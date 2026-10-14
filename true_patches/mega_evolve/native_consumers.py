"""Persist existing native consumers, separate from effect execution coverage.
Unchanged ordinary behavior is inherited from the prerequisite full stack.
This inventory checks code provenance and lookup routing, not whole battles.
"""
import hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from .phase3 import load
from .phase3_worklist import classify
MODULE=Path(__file__).resolve().parent
SOURCE=MODULE.parents[1]/'PatchTesting/Export Rom/Explorers of Alpha+.nds'

def build():
    raw=SOURCE.read_bytes();rom=NintendoDSRom(raw);overlays=rom.loadArm9Overlays()
    decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM);decoder.skipdata=True
    # Wrappers preserve the extended three-slot query entry contract.
    targets={0x02301d10:1,0x02301d78:1,0x02301d84:1,0x0230a940:2,0x02311b94:2,
             0x02332a0c:2,0x02311bf8:1,0x022f96cc:2,0x02301a0c:2,
             0x02322d64:2,0x02328634:2,0x02329f14:2,0x0232bdd0:2,0x0232de20:2,
             0x023bf080:1,0x023d5880:1}
    rows={}
    binaries=[(29,0x022dc240,bytes(overlays[29].data)),(36,0x023a7080,bytes(overlays[36].data)),
              ('itcm',0x01ff8000,bytes(rom.arm9[0xb3380:0xbb380]))]
    for overlay,base,binary in binaries:
        window=[]
        for i in decoder.disasm(binary,base):
            window.append(i);window=window[-24:]
            if i.mnemonic!='bl' or not i.op_str.startswith('#'):continue
            address=int(i.op_str[1:],16)
            if address not in targets:continue
            register=f'r{targets[address]}, '
            writes=[j for j in window[:-1] if j.op_str.startswith(register) and j.mnemonic.startswith(('mov','ldr','add','sub'))]
            if not writes:continue
            owner=writes[-1]
            if not owner.mnemonic.startswith('mov') or not owner.op_str.startswith(register+'#'):continue
            id_=int(owner.op_str.split('#')[1],0)
            code=b''.join(bytes(j.bytes) for j in window)
            rows.setdefault(id_,[]).append({'overlay':overlay,'site':i.address,'query':address,
                'window_start':window[0].address,'window_sha256':hashlib.sha256(code).hexdigest(),
                'disconnected_copy':0x023d9480<=i.address<0x023d9b00})
    abilities=[]
    for a in load()['abilities']:
        sites=[r for r in rows.get(a['legacy_effect_id'],[]) if not r['disconnected_copy']]
        abilities.append({'key':a['key'],'legacy_effect_id':a['legacy_effect_id'],
            'candidate':classify(a),'consumers':sites})
    return {'schema':1,'source_sha256':hashlib.sha256(raw).hexdigest(),
            'scope':'Native instruction provenance and extended lookup routing; dynamic effect tests are listed separately.',
            'abilities':abilities}

def load_inventory():return json.loads((MODULE/'data/phase3_native_consumers.json').read_text(encoding='utf-8'))
if __name__=='__main__':
    data=build();(MODULE/'data/phase3_native_consumers.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Reuse candidates without immediate-query evidence:',[a['key'] for a in data['abilities'] if a['candidate']=='reuse_candidate' and not a['consumers']])
