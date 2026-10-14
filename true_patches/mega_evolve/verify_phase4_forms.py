"""Expanded data and permanent profiles in the linked ARM runtime.

This is an internal phase4 fixture. Public activation remains phase3 until
all native species consumers are connected. No NDS/save output is produced.
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
from ndspy.rom import NintendoDSRom
from skytemple_files.data.md.handler import MdHandler
from true_patches.base_stats_speed.generate_tables import PRIMARY_OFF,RATE_OFF,STATS_OFF


class FormWorld(World):
    def service(self,u,address,size,data):
        # The phase3 family fixtures model CalcStat. Here the actual patched
        # native entry and original old-species continuation must execute.
        if address==self.calc_stat:return
        if address in [self.loader_info['prior_helpers'][k] for k in ('FORM_STAT_RESUME','FORM_RATE_RESUME')]:return
        if self.body_base<=address<self.body_base+self.loader_info['runtime_size']:return
        super().service(u,address,size,data)


def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    forms=load();assert forms==build()
    assert forms['first_species']==1155 and forms['total_species']==2269
    assert len(forms['rows'])==1114
    rom=NintendoDSRom(SOURCE.read_bytes())
    manifest=dict(load_module_manifest(MODULE),phase=4)
    record=apply_phase1(rom,MODULE,manifest,None,{'internal_forms':True})
    verify_phase1(rom,MODULE,manifest,record,{'internal_forms':True})
    original=rom.getFileByName('BALANCE/monster.md')
    raw=prepare(rom);md=MdHandler.deserialize(raw)
    assert len(md.entries)==2269
    assert raw[8:8+1155*68]==original[8:8+1155*68]
    assert raw[8+2269*68:]==binary(forms)
    w=FormWorld(rom,record)
    address=0x021A0000
    w.u.mem_write(address,raw)
    w.u.mem_write(0x020B09B4,struct.pack('<I',address+8))
    largest=None
    for row in forms['rows']:
        species=row['species'];entry=md.entries[species];origin=md.entries[row['origin']]
        assert entry.gender==origin.gender and entry.entid==origin.entid
        assert entry.national_pokedex_number==origin.national_pokedex_number
        assert entry.pre_evo_index==0 and entry.evo_method==0 and not entry.can_evolve
        expected=row['types'] if row['official'] else [origin.type_primary,origin.type_secondary]
        assert [entry.type_primary,entry.type_secondary]==expected
        assert w.call('ME_FormStage',species)==row['stage']
        assert w.call('ME_FormOrigin',species)==row['origin']
        assert w.call('ME_FormParent',species)==row['parent']
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
    for species in (0,3,1137,1154,2269,4095):
        assert w.call('ME_FormStage',species)==0
        assert w.call('ME_FormOrigin',species)==species
        assert w.call('ME_FormParent',species)==0
        assert w.call('ME_FormCalcStat',species,80,0,0)==0xFFFFFFFF
    # Missing/truncated MD headers cannot seed expanded permanent profiles.
    w.u.mem_write(address+4,struct.pack('<I',1155))
    assert w.call('ME_FormStage',1155)==0
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS internal phase4:1114 new forms/2269 IDs, unchanged original MD,')
    print('  gender/branch parents, official types, uint16 stat277,24 stat cases per row,')
    print('  three graded permanent traits and temporary appearance/ability restoration.')
    print('  actual native CalcStat/EvoRate roots, including unchanged old-species continuations.')
    print('Town/stat-copy, name/learnset/portrait consumers still pending; no public phase4 or ROM/save output.')


if __name__=='__main__':main()
