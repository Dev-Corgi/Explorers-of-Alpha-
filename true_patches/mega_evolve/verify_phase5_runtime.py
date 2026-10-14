"""Native chunk decoding, resource allocation and new cache slots; no ROM outputs."""
import hashlib,json,struct
from unittest.mock import patch
from ndspy.rom import NintendoDSRom
from .verify_phase4_forms import FormWorld
from .verify_phase1 import SOURCE,MODULE,BUFFER,DUNGEON
from unicorn.arm_const import *
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.mega_evolve_phase5_data import prepare,chunks

class SpriteWorld(FormWorld):
    service_addresses=(0x02001170,0x02001188,0x0200C33C,0x0200C35C,
                       0x0201D334,0x0201D244,0x0201D72C)
    def __init__(self,rom,record,blobs):
        self.blobs=blobs;self.unloaded=[];super().__init__(rom,record)
        self.u.mem_map(0x02400000,0x800000);self.heap=0x02401000
    def service(self,u,address,size,data):
        args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        a,b,c,d=args
        if address==0x0200C33C:self.ret(len(self.blobs[(a,b)]));return
        if address==0x0200C35C:u.mem_write(c,self.blobs[(a,b)]);self.ret();return
        if address==0x0201D334:
            for i in range(1,20):
                row=bytes(u.mem_read(a+i*56,56))
                if row[0x21]==2 and struct.unpack_from('<2H',row,0x22)==(b,c):self.ret(i);return
            self.ret(0xffffffff);return
        if address==0x0201D244:
            self.ret(next(i for i in range(1,20) if u.mem_read(a+i*56+0x21,1)[0]!=2));return
        if address==0x0201D72C:self.unloaded.append(b);self.ret();return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    inventory=json.loads((MODULE/'data/phase5_assets.json').read_text(encoding='utf-8'))
    asset=inventory['assets'][0];directory=MODULE/'.cache/phase5'/asset['sha256']
    conversion=json.loads((directory/'conversion.json').read_text(encoding='utf-8'))
    fixture=dict(assets=[asset],mapping=[dict(species=1155,asset=0),dict(species=1157,asset=0)],missing=[])
    report=dict(converted=1,total=1,assets=[conversion])
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=5)
    def fixture_prepare(r,m):return prepare(r,m,fixture,report)
    with patch('patch_engine.mega_evolve_phase5_data.prepare',fixture_prepare):
        record=apply_phase1(rom,MODULE,manifest,None,{'phase5_fixture':True})
    verify_phase1(rom,MODULE,manifest,record,{'phase5_fixture':True})
    # Native pack-name table020AF6A0: monster, m_attack, m_ground.
    blobs={(0,819):(directory/'monster.wan').read_bytes(),(1,819):(directory/'attack.wan').read_bytes(),
           (2,819):chunks((directory/'ground.wan').read_bytes())}
    w=SpriteWorld(rom,record,blobs);raw=rom.getFileByName('BALANCE/monster.md')
    w.u.mem_write(0x021A0000,raw);w.u.mem_write(0x020B09B4,struct.pack('<I',0x021A0008))
    resident=record.data[0]['form_consumers']['symbols']
    assert w.call('',1155,start=0x0205281C)==conversion['raw_sizes']['monster']
    assert w.call('',1157,start=resident['ME_ResidentAsset'])==1155
    canary=DUNGEON+0x19914+1155*2;w.u.mem_write(canary,b'CANARY!!')
    w.call('',1155,23,start=0x022F740C)
    assert w.call('',1155,start=0x022F7388)==23 and w.call('',1157,start=0x022F7388)==23
    w.call('',1157,start=0x022F7768);assert w.unloaded==[23]
    assert w.call('',1155,start=0x022F7388)==0 and bytes(w.u.mem_read(canary,8))==b'CANARY!!'
    for key,blob in blobs.items():
        pointer=0x02410000;out=0x02600000
        w.u.mem_write(pointer,blob);length=struct.unpack_from('<I',blob,4)[0]
        assert w.call('',pointer,start=0x020204EC)==length
        w.u.mem_write(out+length,b'SAFE')
        assert w.call('',out,length,pointer,start=0x0201F5C0,limit=100000000)==length
        original=(directory/({0:'monster',1:'attack',2:'ground'}[key[0]]+'.wan')).read_bytes()
        if key[0]!=2:
            from skytemple_rust.st_pkdpx import Pkdpx
            parts=[];p=12
            for i in range(struct.unpack_from('<I',original,8)[0]):
                n=struct.unpack_from('<I',original,p)[0];p+=4;parts.append(Pkdpx(original[p:p+n]).decompress());p+=(n+3)&~3
            original=b''.join(parts)
        assert bytes(w.u.mem_read(out,length))==original and bytes(w.u.mem_read(out+length,4))==b'SAFE'
    manager=BUFFER;w.u.mem_write(manager,bytes(0x1600));w.heap=0x02401000
    for pack in (0,1,2):
        # Actual patched global resource entry, including its5th stack argument.
        w.u.mem_write(0x023FE000,struct.pack('<I',int(pack!=2)))
        slot=w.call('',manager,pack,819,0,start=0x0201D484,limit=100000000)
        assert slot==pack+1
        pointer=struct.unpack('<I',bytes(w.u.mem_read(manager+slot*56+0x34,4)))[0]
        assert bytes(w.u.mem_read(pointer,4))==b'SIRO' # Native relocation marks the loaded SIR0.
    assert len(w.freed)==3 # Each owned compressed buffer was released.
    w.fail_alloc=True
    assert w.call('',manager,0,819,0,start=0x0201D484)==1 # Cache hit needs no allocation.
    # Allocation failure leaves the existing buffer and cache identity intact.
    saved=bytes(w.u.mem_read(manager+56,56))
    assert w.call('',manager,1,0,819,start=0x0201D684)==0
    assert bytes(w.u.mem_read(manager+56,56))==saved
    w.fail_alloc=False
    assert w.call('',manager,1,0,819,start=0x0201D684,limit=100000000)==1
    assert len(w.freed)==5 # Replacement scratch and old raw buffer were released.
    w.u.mem_write(0x023FE000,struct.pack('<I',1))
    # New resources ignore the old-size borrowed buffer instead of overflowing it.
    w.u.mem_write(BUFFER+0x1800,b'BORROWED')
    other_manager=BUFFER+0x2000;w.u.mem_write(other_manager,bytes(0x1600))
    assert w.call('',other_manager,0,819,BUFFER+0x1800,start=0x0201D590,limit=100000000)==1
    assert bytes(w.u.mem_read(BUFFER+0x1800,8))==b'BORROWED'
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase5: native chunk decoder/size lookup, resource loading and buffer release,')
    print('  separate cache slots, shared images, deletion and legacy-array canaries.')
    print('Pack I/O/allocator/manager slots modeled; native decoder and SIR0 initialization executed. No ROM/save output.')
if __name__=='__main__':main()
