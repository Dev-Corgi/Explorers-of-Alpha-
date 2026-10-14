"""Native level gate/conversion and ordinary evolution resources; no ROM output."""
import hashlib,struct
from .verify_phase1 import SOURCE,MODULE,BUFFER
from .verify_phase4_forms import FormWorld
from .phase4 import load as forms
from .new_species import load
from .phase5_routes import build as routes
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.korean_codec import parse_str_file,decode_english
from patch_engine.mega_evolve_phase3_data import installed_translations
from skytemple_files.common.types.file_types import FileType
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP

class EvolutionWorld(FormWorld):
    def service(self,u,address,size,data):
        if address==0x020555A8:
            self.ret(BUFFER);return
        if address==0x02055D7C:
            pointer=u.reg_read(UC_ARM_REG_R1)
            u.mem_write(BUFFER,bytes(u.mem_read(pointer,68)))
            self.ret();return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    contract=routes()
    assert contract['compatibility_only_mega_ids']==[1917,1923,2179,2185,2193]
    assert not any(r['target'] in contract['compatibility_only_mega_ids'] for r in contract['routes'])
    for source,target in ((555,1918),(556,1924)):
        route=next(r for r in contract['routes'] if r['source']==source)
        assert route['target']==target and route['level'] is None and route['source_stage']==1
    rom=NintendoDSRom(SOURCE.read_bytes())
    original_waza=FileType.WAZA_P.deserialize(rom.getFileByName('BALANCE/waza_p.bin'))
    original_kao=FileType.KAO.deserialize(rom.getFileByName('FONT/kaomado.kao'))
    manifest=dict(load_module_manifest(MODULE),phase=4)
    record=apply_phase1(rom,MODULE,manifest,None,{'new_species_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'new_species_test':True})
    text=[decode_english(s) for s in parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))]
    translations=installed_translations(text)
    waza=FileType.WAZA_P.deserialize(rom.getFileByName('BALANCE/waza_p.bin'))
    kao=FileType.KAO.deserialize(rom.getFileByName('FONT/kaomado.kao'))
    assert waza.learnsets[:553]==original_waza.learnsets and waza.moves==original_waza.moves
    assert len(waza.learnsets)==555 and kao.n_entries()==2049
    # KAO expansion relocates offsets, so compare every old portrait's bytes.
    for i in range(2047):
        for j in range(40):
            a,b=original_kao.get(i,j),kao.get(i,j)
            assert (a is None)==(b is None)
            if a:assert a.raw()==b.raw()
    world=EvolutionWorld(rom,record)
    raw=rom.getFileByName('BALANCE/monster.md')
    world.u.mem_write(0x021A0000,raw);world.u.mem_write(0x020B09B4,struct.pack('<I',0x021A0008))
    out=BUFFER+0x100;index=BUFFER+0x200
    for item in load():
        assert text[item['name_index']]==item['en']
        assert translations[str(item['name_index'])]['ko']==item['ko']
        learned=waza.learnsets[item['learnset_index']]
        assert [(int(m.move_id),int(m.level_id)) for m in learned.level_up_moves]==[
            (m['rom_id'],m['level']) for m in item['moves'] if m['method']==1]
        assert all(m['rom_id'] is not None for m in item['moves'])
        assert kao.get(item['portrait_id']-1,0) is not None
        for gender,target in enumerate(item['species']):
            parent=item['parent']+gender*600
            for level in (19,20,80,100):
                member=bytearray(68);member[1]=level
                struct.pack_into('<H',member,4,parent)
                member[8:68]=bytes(range(60))
                world.u.mem_write(BUFFER,bytes(member));world.u.mem_write(out,b'\xA5'*64)
                world.call('',BUFFER,out,start=0x02059B18)
                flag,candidate=struct.unpack('<2H',world.u.mem_read(out+6,4))
                assert (flag,candidate)==((1,target) if level>=20 else (2,0))
                assert bytes(world.u.mem_read(out+58,6))==b'\xA5'*6
                if level>=20:
                    world.u.mem_write(index,struct.pack('<h',0))
                    assert world.call('',index,target,start=0x0205A288)==1
                    converted=bytes(world.u.mem_read(BUFFER,68))
                    assert struct.unpack_from('<H',converted,4)[0]==target
                    assert converted[1]==level and converted[6]==level
                    assert converted[8:]==member[8:]
            # The saved normal species, mega, and shiny all share new resources.
            pair=[r for r in forms()['rows'] if r['origin']==target]
            assert {r['stage'] for r in pair}=={0,1,2}
            for row in pair:
                assert world.call('ME_LearnSpecies',row['species'])==item['learnset_index']
                assert world.call('ME_PortraitSpecies',row['species'])==item['portrait_id']
    # Unrelated species keep the exact native prologue and continuation.
    world.u.mem_write(BUFFER+4,struct.pack('<H',3))
    world.u.reg_write(UC_ARM_REG_R0,BUFFER);world.u.reg_write(UC_ARM_REG_R1,out)
    world.u.reg_write(UC_ARM_REG_SP,0x023FE000)
    world.u.emu_start(0x02059B18,0x02059B1C,count=3000)
    assert world.u.reg_read(UC_ARM_REG_SP)==0x023FE000-40
    for path in ('BALANCE/waza_p.bin','FONT/kaomado.kao'):
        old=rom.getFileByName(path);altered=bytearray(old);altered[-1]^=1
        rom.setFileByName(path,altered)
        try:verify_phase1(rom,MODULE,manifest,record,{'new_species_test':True})
        except AssertionError:pass
        else:raise AssertionError('New species resource corruption accepted')
        rom.setFileByName(path,old)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS new species: level19/20/80/100, both genders, native conversion/history/XP bytes,')
    print('  supported SV learnsets, new English/Korean names, shared form portraits and old portrait/move preservation.')
    print('  explicit phase6 Primal routes have no additional Mega choice.')
    print('Roster read/write modeled; native level hook and conversion body execute. No ROM/save output.')

if __name__=='__main__':main()
