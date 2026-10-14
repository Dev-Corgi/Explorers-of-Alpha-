"""Expanded data and permanent profiles in the linked ARM runtime.

Runs phase4 data/runtime and actual native consumer boundaries without
producing NDS/save output. Full gameplay/flash I/O belong to phase8.
"""
from __future__ import annotations
import hashlib
import struct
from .phase4 import load,build,validate,binary
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,MONSTERS,ENTITIES
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.mega_evolve_phase4_data import prepare
from patch_engine.mega_evolve_phase3_data import prepare_data
from ndspy.rom import NintendoDSRom
from skytemple_files.data.md.handler import MdHandler
from true_patches.base_stats_speed.generate_tables import PRIMARY_OFF,RATE_OFF,STATS_OFF
from unicorn.arm_const import *


class FormWorld(World):
    def service(self,u,address,size,data):
        if address==0x0208FEA4:
            a=u.reg_read(UC_ARM_REG_R0);b=u.reg_read(UC_ARM_REG_R1)
            u.reg_write(UC_ARM_REG_R1,a%b);self.ret(a//b);return
        # The phase3 family fixtures model CalcStat. Here the actual patched
        # native entry and original old-species continuation must execute.
        if address==self.calc_stat:return
        if address in [self.loader_info['prior_helpers'][k] for k in ('FORM_STAT_RESUME','FORM_RATE_RESUME')]:return
        if self.body_base<=address<self.body_base+self.loader_info['runtime_size']:return
        super().service(u,address,size,data)


def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    forms=load();assert forms==build()
    assert forms['first_species']==1155 and forms['total_species']==2273
    assert len(forms['rows'])==1118
    rom=NintendoDSRom(SOURCE.read_bytes())
    original=prepare_data(rom)[0]['BALANCE/monster.md']
    manifest=dict(load_module_manifest(MODULE),phase=4)
    record=apply_phase1(rom,MODULE,manifest,None,{'internal_forms':True})
    verify_phase1(rom,MODULE,manifest,record,{'internal_forms':True})
    raw=rom.getFileByName('BALANCE/monster.md');md=MdHandler.deserialize(raw)
    assert len(md.entries)==2273
    assert raw[8:8+1155*68]==original[8:8+1155*68]
    assert raw[8+2273*68:]==binary(forms)
    from .new_species import load as new_species
    extras={species:item for item in new_species() for species in item['species']}
    w=FormWorld(rom,record)
    resident=record.data[0]['form_consumers']['symbols']
    address=0x021A0000
    w.u.mem_write(address,raw)
    w.u.mem_write(0x020B09B4,struct.pack('<I',address+8))
    largest=None
    for row in forms['rows']:
        species=row['species'];entry=md.entries[species];origin=md.entries[row.get('template',row['origin'])]
        assert entry.gender==origin.gender and entry.entid==origin.entid
        assert entry.national_pokedex_number==row.get('dex',origin.national_pokedex_number)
        assert not entry.can_evolve
        assert (entry.pre_evo_index,entry.evo_method)==((row['parent'],1) if not row['stage'] else (0,0))
        expected=row['types'] if row['official'] or 'template' in row else [origin.type_primary,origin.type_secondary]
        assert [entry.type_primary,entry.type_secondary]==expected
        assert w.call('ME_FormStage',species)==row['stage']
        assert w.call('ME_FormOrigin',species)==row['origin']
        assert w.call('ME_FormParent',species)==row['parent']
        assert w.call('',species,start=resident['ME_ResidentOrigin'])==row.get('template',row['origin'])
        assert w.call('',species,start=0x0205476C)==1
        assert w.call('',species,start=resident['ME_ResidentAsset'])==row['asset_source']
        # 80/100 and signed permanent doping exercise the shared base-stat
        # formula, including >255 and zero/clamp edges.
        for stat,base in enumerate(row['stats']):
            for level,doping in ((80,0),(100,17),(1,-400),(100,32767)):
                v=max(0,min(32767,base+doping))
                expected=max(0,min(32767,v*2*level//100+(level+10 if stat==0 else 5)))
                assert w.call('ME_FormCalcStat',species,level,stat,doping)==expected
                if level==80:
                    assert w.call('',species,level,stat,doping,start=w.calc_stat)==expected
            assert w.call('',species,start=w.calc_stat+4)==0
            if largest is None or base>largest[0]:largest=(base,species,stat)
        w.u.mem_write(MONSTERS[0]+2,struct.pack('<HH',species,3))
        w.call('ME_ResetMonster',MONSTERS[0])
        expected=[a|(row['grade']<<16) for a in row['abilities']]
        assert [w.ability(0,i) for i in range(3)]==expected
        # Apparent species and temporary borrowed projections do not alter
        # the original stage or permanent three-ability profile.
        w.u.mem_write(MONSTERS[0]+4,struct.pack('<H',row['origin']))
        w.u.mem_write(MONSTERS[0]+0x60,b'\x20\x21')
        w.call('ME_RestoreAbilities',ENTITIES[0])
        assert [w.ability(0,i) for i in range(3)]==expected
    assert largest[0]==277
    from patch_engine.mega_evolve_phase4_runtime import NAME_SITES,LEARN_SITES
    # Existing names retain their index; newly added ordinary species and
    # their Mega forms use the appended name shared by both genders.
    # Native learnset entry normalizes before its one-time gender subtraction.
    for row in forms['rows'][::2]:
        extra=extras.get(row['origin'])
        for site in NAME_SITES:
            w.u.reg_write(UC_ARM_REG_R0,row['species']);w.u.reg_write(UC_ARM_REG_R1,600)
            w.u.reg_write(UC_ARM_REG_SP,0x023FE000)
            w.u.emu_start(site,site+4,count=2000)
            assert w.u.reg_read(UC_ARM_REG_R1)==(extra['name_index']-8735 if extra else row['origin']%600)
        for site in LEARN_SITES:
            w.u.reg_write(UC_ARM_REG_R0,row['species']);w.u.reg_write(UC_ARM_REG_SP,0x023FE000)
            w.u.emu_start(site,site+4,count=2000)
            assert w.u.reg_read(UC_ARM_REG_R4)==(extra['learnset_index'] if extra else row['origin'])
        # Real portrait load starts with the mapped r7, retaining parameters.
        pointer=0x02280000
        w.u.mem_write(pointer,struct.pack('<H',row['species']))
        w.u.reg_write(UC_ARM_REG_R10,pointer);w.u.reg_write(UC_ARM_REG_SP,0x023FE000)
        w.u.emu_start(0x0204D8CC,0x0204D8D0,count=2000)
        assert w.u.reg_read(UC_ARM_REG_R7)==(extra['portrait_id'] if extra else row['origin'])
        # The real cache getter addresses the existing asset ID, not the new
        # species; the canary beyond the old1155 slots must stay untouched.
        from .verify_phase1 import DUNGEON
        asset=row['asset_source'];cache=DUNGEON+0x19914
        w.u.mem_write(cache+asset*2,struct.pack('<H',123))
        assert w.call('',row['species'],start=0x022F7388)==123
        # Native ground->active and dojo/guest->ground copy fields use whole
        # signed halfwords. The high species bit survives both directions.
        source=0x02281000;target=0x02281200
        w.u.mem_write(source,bytes(0x100));w.u.mem_write(target,bytes(0x100))
        w.u.mem_write(source+4,struct.pack('<H',row['species']))
        w.u.reg_write(UC_ARM_REG_R5,source);w.u.reg_write(UC_ARM_REG_R6,target)
        w.u.emu_start(0x020532B4,0x020532C0,count=100)
        assert struct.unpack('<H',w.u.mem_read(target+12,2))[0]==row['species']
        w.u.mem_write(source+8,struct.pack('<H',row['species']))
        w.u.reg_write(UC_ARM_REG_R3,source);w.u.reg_write(UC_ARM_REG_R12,target)
        w.u.emu_start(0x02055F48,0x02055F50,count=100)
        assert struct.unpack('<H',w.u.mem_read(target+4,2))[0]==row['species']
    # Cache write maps the physical image owner, keeps the MD ID untouched,
    # and never reaches the memory following the old1155-entry table.
    cache=DUNGEON+0x19914
    w.u.mem_write(cache+1155*2,b'CACHE_CANARY')
    for row in (forms['rows'][0],forms['rows'][-2]):
        species=row['species'];asset=row['asset_source']
        w.call('',species,321,start=0x022F740C)
        assert struct.unpack('<H',w.u.mem_read(cache+asset*2,2))[0]==321
        assert bytes(w.u.mem_read(cache+1155*2,12))==b'CACHE_CANARY'
    # A base and mega sharing the same image do not clear their own cache
    # when a temporary appearance swap asks to transfer that image to itself.
    w.call('',forms['rows'][0]['species'],forms['rows'][0]['origin'],start=0x022F75D4)
    assert struct.unpack('<H',w.u.mem_read(cache+3*2,2))[0]==321
    for species in (2273,4095,0xFFFF):assert w.call('',species,start=0x0205476C)==0
    original_ov=rom.loadArm9Overlays()[36].data
    root=w.calc_stat-0x023A7080
    for species in (0,3,603,1137,1154):
        primary=struct.unpack_from('<H',original_ov,root+PRIMARY_OFF+species*2)[0]
        rate=original_ov[root+RATE_OFF+primary]
        assert w.call('',species,start=w.calc_stat+4)==rate
        for stat in range(6):
            base=original_ov[root+STATS_OFF+primary*6+stat]
            effective=min(32767,base+17)*(100,115,138)[rate]//100
            expected=min(32767,effective*160//100+(90 if stat==0 else 5))
            assert w.call('',species,80,stat,17,start=w.calc_stat)==expected
    for species in (0,3,1137,1154,2273,4095):
        assert w.call('ME_FormStage',species)==0
        assert w.call('ME_FormOrigin',species)==species
        assert w.call('ME_FormParent',species)==0
        assert w.call('ME_FormCalcStat',species,80,0,0)==0xFFFFFFFF
    # Missing/truncated MD headers cannot seed expanded permanent profiles.
    w.u.mem_write(address+4,struct.pack('<I',1155))
    assert w.call('ME_FormStage',1155)==0
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase4:1118 additional rows/2273 IDs, unchanged original MD,')
    print('  gender/branch parents, official types, uint16 stat277,24 stat cases per row,')
    print('  three graded permanent traits and temporary appearance/ability restoration.')
    print('  actual native CalcStat/EvoRate roots, including unchanged old-species continuations.')
    print('  real name/learnset/portrait/cache consumers, original/new names and species validity.')
    print('  native team/dojo halfword copies, bounded cache write and shared-image swaps.')
    print('No ROM/save output. Full hardware/dungeon integration remains phase8.')


if __name__=='__main__':main()
