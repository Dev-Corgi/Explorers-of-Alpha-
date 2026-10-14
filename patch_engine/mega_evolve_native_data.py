"""Connect the actual Alpha resource paths and its existing save updater."""
import hashlib,struct
from skytemple_files.data.data_cd.handler import DataCDHandler
from range_typed_integers import u16
from .mega_evolve_runtime import branch

PROCESS_BASE=0x022E7A48
PROCESS_RETURN=0x022E82C0


def updater_codes(state,version_address):
    # Native ProcessSpecial 77: keep the original Alpha version gate, but a
    # successfully decoded 11-bit roster must also enter that same updater.
    gate=[0xE59F3018,0xE5930008,0xE3500000,0x13A00000,
          0x1A000000,0xE59F3008,0xE5D30000,0, state,version_address]
    gate[4]=(branch(PROCESS_BASE+16,PROCESS_BASE+28)&0x0FFFFFFF)|0x10000000
    gate[7]=branch(PROCESS_BASE+28,PROCESS_RETURN)
    # Native ProcessSpecial 76: complete the original update, then acknowledge
    # the in-memory mega schema. Persisted ME12 is written by the normal save
    # codec; it is never faked on an undecoded or failed save load.
    complete=[0xE59F3024,0xE5D30000,0xE3500000,0x03A010FF,0x05C31000,
              0xE59F3014,0xE3A01000,0xE5831008,0xE3A01001,0xE583100C,
              0,version_address,state]
    complete[10]=branch(PROCESS_BASE+40,PROCESS_RETURN)
    return {77:struct.pack('<10I',*gate),76:struct.pack('<13I',*complete)}


def install(rom,codec):
    hashes={}
    # The canonical Alpha copies are equal before our stack. Its native ARM9
    # literals select UTILITY, whereas data authoring modules select BALANCE.
    for name in ('monster.md','waza_p.bin'):
        source='BALANCE/'+name;target='UTILITY/'+name
        content=rom.getFileByName(source)
        rom.setFileByName(target,content)
        hashes[target]=hashlib.sha256(content).hexdigest()
    codes=None
    for path in ('BALANCE/process.bin','UTILITY/process.bin'):
        cd=DataCDHandler.deserialize(rom.getFileByName(path))
        old={n:bytes(cd.get_effect_code(cd.items_effects[n])) for n in (76,77)}
        if len(old[77])!=16 or len(old[76])!=28 or old[77][:8]!=struct.pack('<2I',0xE59F3004,0xE5D30000):
            raise RuntimeError('mega save updater process guard changed')
        version=struct.unpack_from('<I',old[77],12)[0]
        if struct.unpack_from('<I',old[76],24)[0]!=version:
            raise RuntimeError('Alpha save updater version addresses disagree')
        generated=updater_codes(codec['state'],version)
        if codes is not None and generated!=codes:
            raise RuntimeError('Alpha process banks disagree')
        codes=generated
        # Append distinct effect records; do not replace shared code records.
        for n,content in generated.items():
            cd.items_effects[n]=u16(len(cd.effects_code));cd.effects_code.append(content)
        blob=bytes(DataCDHandler.serialize(cd));rom.setFileByName(path,blob)
        hashes[path]=hashlib.sha256(blob).hexdigest()
    return {'files':hashes,'save_updater_processes':[76,77],'schema':1}


def verify(rom,info):
    for path,digest in info['files'].items():
        if hashlib.sha256(rom.getFileByName(path)).hexdigest()!=digest:
            raise AssertionError('mega native resource/updater changed: '+path)
    for name in ('monster.md','waza_p.bin'):
        if rom.getFileByName('BALANCE/'+name)!=rom.getFileByName('UTILITY/'+name):
            raise AssertionError('mega native resource bank mismatch')
    # Inspect the ARM9 literals actually passed to LoadFile. A future input
    # changing the native paths must not silently invalidate this integration.
    for address,name in ((0x0205238C,'monster.md'),):
        pointer=struct.unpack_from('<I',rom.arm9,address-0x02000000)[0]
        expected=('rom0:/UTILITY/'+name).encode()+b'\0'
        if rom.arm9[pointer-0x02000000:pointer-0x02000000+len(expected)]!=expected:
            raise AssertionError('mega native MD loader path changed')
