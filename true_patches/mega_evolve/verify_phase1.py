"""Execute the linked phase-1 ARM runtime and real weather-selection path.

Input ROMs are only read; no full-stack, NDS, save or state files are written.
UI/weather animations, ability predicates, base-stat calculation and division
are supplied by the harness. Native weather counters and patched hooks execute.
"""
from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
sys.path.insert(0,str(REPO/"tools/.korean_jit_test_deps"))
from ndspy.rom import NintendoDSRom
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R10,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from patch_engine.apply_mega_evolve import apply_mega_evolve_module,verify_mega_evolve_module
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import OV29,OV36,word,allocate_runtime
from patch_engine.state import BuildState,AppliedModule,CaveAllocation
from patch_engine.cave_reservations import reserved_file_ranges
from true_patches.base_stats_speed.generate_tables import SENTINEL_OFF
from patch_engine.korean_codec import parse_str_file,decode_english,translation_issues
from patch_engine.apply_korean import load_source,plan_translation

MODULE=REPO/"true_patches/mega_evolve"
SOURCE=REPO/"PatchTesting/Export Rom/Explorers of Alpha+.nds"
DUNGEON=0x02100000
ENTITIES=[0x02250000+i*0x200 for i in range(20)]
MONSTERS=[0x02260000+i*0x400 for i in range(20)]
STACK=0x023FE000
STOP=0x023FF000
BUFFER=0x02280000


class World:
    def __init__(self,rom,record):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        self.u.mem_map(0x02000000,0x400000)
        self.u.mem_write(0x02000000,bytes(rom.arm9))
        overlays=rom.loadArm9Overlays()
        self.u.mem_write(OV29,bytes(overlays[29].data))
        self.u.mem_write(OV36,bytes(overlays[36].data))
        self.record=record
        self.symbols=record.data[0]["symbols"]
        self.entity_speed=record.data[0]["base_stats_helpers"]["entity_speed"]
        sentinel=bytes(overlays[36].data).index(struct.pack("<I",0xB5A7E001))
        self.calc_stat=OV36+sentinel-SENTINEL_OFF
        self.abilities={}
        self.suppressed=set()
        self.weather_immune=set()
        self.base_speed=100
        self.base_stat=101
        self.divisions=[]
        if getattr(self,'service_addresses',None):
            for address in self.service_addresses:
                self.u.hook_add(UC_HOOK_CODE,self.service,begin=address,end=address)
        else:self.u.hook_add(UC_HOOK_CODE,self.service)
        self.reset()

    def reset(self):
        self.abilities.clear(); self.suppressed.clear(); self.weather_immune.clear(); self.divisions.clear()
        self.u.mem_write(self.symbols["state"],bytes(self.symbols["MERuntimeEnd"]-self.symbols["state"]))
        self.u.mem_write(DUNGEON,bytes(0x2f000))
        self.u.mem_write(0x02353538,struct.pack("<I",DUNGEON))
        self.u.mem_write(0x022AB46A,b"\0")
        self.u.mem_write(DUNGEON+0x748,bytes([1,1]))
        for i,(e,m) in enumerate(zip(ENTITIES,MONSTERS)):
            self.u.mem_write(e,bytes(0x200)); self.u.mem_write(m,bytes(0x400))
            self.u.mem_write(e,struct.pack("<I",1))
            self.u.mem_write(e+0xb4,struct.pack("<I",m))
            self.u.mem_write(m+2,struct.pack("<HH",6+i,6+i))
            self.u.mem_write(m+0xa,b"\x50")
            self.u.mem_write(m+0xc,struct.pack("<h",-1))
            self.u.mem_write(m+0x10,struct.pack("<hhh",100,100,0))
            self.u.mem_write(m+0x5e,bytes([1,0]))
            self.u.mem_write(DUNGEON+0x12b78+i*4,struct.pack("<I",e))

    def ret(self,result=0):
        self.u.reg_write(UC_ARM_REG_R0,result&0xFFFFFFFF)
        self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))

    def service(self,u,address,size,_):
        a,b,c=(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))
        if address==0x02301D78:
            self.ret(b in self.abilities.get(a,set()) and a not in self.suppressed)
        elif address==0x0208FEA4:
            self.divisions.append((a,b)); self.ret(a//b)
        elif address==0x023467E4: self.ret(a in self.weather_immune and b==0x34)
        elif address in (0x022E95F4,0x022F7364): self.ret(a in ENTITIES)
        elif address==0x0230175C: self.ret(1) # unrelated Cloud Nine holder
        elif address==0x022E9A6C:
            count=struct.unpack("<H",bytes(u.mem_read(a,2)))[0]
            u.mem_write(a,struct.pack("<H",max(0,count-1))); self.ret()
        elif address==0x022E9A44:
            count=bytes(u.mem_read(a,1))[0]
            u.mem_write(a,bytes([max(0,count-1)])); self.ret()
        elif address in (0x02334E70,0x0234B2A4,0x0234B350,0x022E9580): self.ret()
        elif address==self.entity_speed: self.ret(self.base_speed)
        elif address==self.calc_stat: self.ret(self.base_stat)

    def call(self,name,*args,start=None,registers=None,limit=200000):
        self.u.reg_write(UC_ARM_REG_SP,STACK)
        self.u.reg_write(UC_ARM_REG_LR,STOP)
        for r,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):
            self.u.reg_write(r,v&0xFFFFFFFF)
        if registers:
            for r,v in registers.items(): self.u.reg_write(r,v)
        self.u.emu_start(start if start is not None else self.symbols[name],STOP,count=limit)
        if self.u.reg_read(UC_ARM_REG_PC)!=STOP:
            raise AssertionError(f"{name}: did not return ({self.u.reg_read(UC_ARM_REG_PC):#x})")
        return self.u.reg_read(UC_ARM_REG_R0)

    def weather(self,value):
        self.u.mem_write(DUNGEON+0xcd38,bytes([value]))
        self.u.mem_write(DUNGEON+0xcd39,bytes([value]))


def main():
    manifest=dict(load_module_manifest(MODULE),phase=1)
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes())
    fixture_data=bytes(rom.loadArm9Overlays()[36].data)
    first,_=allocate_runtime(fixture_data,None)
    reserved=BuildState("us_vanilla",OV29,[AppliedModule("prior_fixture",1,
        caves=[CaveAllocation("ov36",first.file_offset,0x400,first.load_address)])])
    relocated,_=allocate_runtime(fixture_data,reserved)
    assert all(not r.overlaps(relocated.file_offset,relocated.size) for r in reserved_file_ranges(reserved,"ov36"))
    old_md=rom.getFileByName("BALANCE/monster.md")
    record=apply_mega_evolve_module("mega_evolve",MODULE,manifest,rom)
    verify_mega_evolve_module(rom,MODULE,manifest,record)
    assert old_md==rom.getFileByName("BALANCE/monster.md")
    w=World(rom,record); e=ENTITIES[0]; other=ENTITIES[1]; m=MONSTERS[0]
    assert w.call("ME_GetStoredSpeed",e)==10
    for value,expected in [(-99,4),(99,16),(10,10)]:
        w.call("ME_SetStoredSpeed",e,value)
        assert w.call("ME_GetStoredSpeed",e)==expected
    w.call("ME_ChangeSpeed",e,e,2,0)
    assert w.call("ME_GetStoredSpeed",e)==12
    assert w.call("ME_GetSpeed",e,100,0,0)==200
    assert w.call("ME_GetStoredSpeed",e)==12 # calculation must not mutate rank
    w.call("ME_SetStoredSpeed",e,8)
    assert w.call("ME_GetSpeed",e,100,0,0)==50
    for stage in range(4,17):
        w.call("ME_SetStoredSpeed",e,stage)
        d=stage-10; expected=100*(2+d)//2 if d>=0 else 200//(2-d)
        assert w.call("ME_GetSpeed",e,100,0,0)==expected
    w.abilities[e]={15}
    assert w.call("ME_ChangeSpeed",other,e,-1,0)==0
    assert w.call("ME_ChangeSpeed",e,e,-1,0)==1
    w.call("ME_SetStoredSpeed",e,10); w.abilities[e]={97}
    w.call("ME_ChangeSpeed",e,e,1,0)
    assert w.call("ME_GetStoredSpeed",e)==12
    w.abilities[e]=set(); w.abilities[other]={103}
    assert w.call("ME_GetSpeed",e,100,other,3)==100
    w.abilities[other]=set()
    assert w.call("ME_HitAttackerSpeedHook",e,registers={UC_ARM_REG_R6:other,UC_ARM_REG_R7:e})==200
    w.abilities[e]={142}; w.call("ME_SetStoredSpeed",e,10)
    assert w.call("ME_GetSpeed",e,100,0,0)==200
    assert struct.unpack("<I",bytes(w.u.mem_read(m+0x110,4)))[0]==0
    w.abilities[e]=set(); w.call("ME_SetStoredSpeed",e,13)
    w.u.mem_write(DUNGEON+0x749,b"\x02")
    assert w.call("ME_GetStoredSpeed",e)==10
    w.call("ME_SetStoredSpeed",e,13); w.call("ME_ResetMonster",m)
    assert w.call("ME_GetStoredSpeed",e)==10
    w.reset()
    # Native apparent-weather hook normalizes snow without changing buff counters.
    for raw,expected in [(1,1),(2,2),(4,4),(5,5),(7,5)]:
        w.weather(raw)
        assert w.call("ME_ApparentWeather",e,start=0x02334D08)==expected
    w.weather_immune.add(e) # existing apparent-weather exclusive protection
    assert w.call("ME_ApparentWeather",e)==0
    w.weather_immune.clear()
    # Defense applies once to both damage categories and all eligible type pairs.
    for weather,types,expected in [(2,(13,9),121),(2,(17,0),121),(2,(1,0),101),(5,(6,0),121),(5,(1,0),101)]:
        w.weather(weather); w.u.mem_write(m+0x5e,bytes(types))
        assert w.call("ME_WeatherDefense",m,101,1)==expected
        assert w.call("ME_WeatherDefense",m,101,0)==101
        assert w.call("ME_FromMonsterHook",m,0,1)==expected
        assert w.call("ME_FromMonsterHook",m,1,1)==expected
        assert w.call("ME_FromMonsterHook",m,0,0)==101
    w.reset(); w.abilities[e]={28}; w.abilities[other]={120}
    assert w.call("ME_SetWeatherSource",e,2,1,28)==1
    assert w.call("ME_ForcedWeather") == 2
    assert w.u.mem_read(DUNGEON+0xcd38,1)==b"\x02"
    w.u.mem_write(m+0x5e,bytes([13,17]))
    assert w.call("ME_WeatherDefense",m,101,1)==151
    assert w.call("ME_WeatherMessage",2,start=0x023BF96C)+0xa00==19751
    w.call("ME_WeatherFailureHook",registers={UC_ARM_REG_R0:e,UC_ARM_REG_R1:other})
    assert w.u.reg_read(UC_ARM_REG_R2)==19753
    assert w.u.reg_read(UC_ARM_REG_R0)==e and w.u.reg_read(UC_ARM_REG_R1)==other
    # Native Hail move counter write must not override strong Sandstorm.
    w.u.mem_write(0x022C4754,struct.pack("<H",3000))
    w.call("native_Hail",e,other,0,0,start=0x0232612C)
    assert w.u.mem_read(DUNGEON+0xcd38,1)==b"\x02"
    assert w.call("ME_SetWeatherSource",other,5,0,120)==0 # strong resists normal
    assert w.call("ME_SetWeatherSource",other,5,1,120)==1 # strong replaces strong
    assert w.call("ME_ForcedWeather")==5
    assert w.call("ME_WeatherMessage",5,start=0x023BF96C)+0xa00==19752
    w.suppressed.add(other)
    assert w.call("ME_ForcedWeather")==2 # earlier valid source resumes
    w.suppressed.remove(other)
    assert w.call("ME_ForcedWeather")==5
    w.u.mem_write(MONSTERS[1]+0x10,b"\0\0")
    assert w.call("ME_ForcedWeather")==2
    w.call("ME_ClearWeatherSource",e)
    assert w.call("ME_ForcedWeather")==0xFFFFFFFF
    w.reset(); w.weather(1)
    p=w.call("ME_WeatherPower",e)
    factor=struct.unpack("<II",bytes(w.u.mem_read(p,8)))
    assert tuple(factor)==(0x33333334,0x13333)
    encoded_factor=(factor[1]<<32)|factor[0]
    assert all((value*encoded_factor)>>48==value*6//5 for value in range(1,1024))
    w.abilities[e]={253}
    assert w.call("ME_ForcedWeather")==1
    p=w.call("ME_WeatherPower",e)
    assert tuple(struct.unpack("<II",bytes(w.u.mem_read(p,8))))==(0,0x18000)
    # Actual factor-load wrapper preserves CalcTypeBasedDamageEffects registers.
    regs={UC_ARM_REG_R0:0x1234,UC_ARM_REG_R1:0x1238,UC_ARM_REG_R3:0x5678,UC_ARM_REG_R10:e}
    w.call("ME_SunPowerHook",registers=regs)
    assert w.u.reg_read(UC_ARM_REG_R0)==0x1234 and w.u.reg_read(UC_ARM_REG_R1)==0x1238
    assert w.u.reg_read(UC_ARM_REG_R3)==0x5678
    assert tuple(struct.unpack("<II",bytes(w.u.mem_read(w.u.reg_read(UC_ARM_REG_R2),8))))==(0,0x18000)
    w.reset(); w.call("ME_SetStoredSpeed",e,14)
    assert w.call("ME_ExportState",BUFFER,1024)==1024
    payload=bytes(w.u.mem_read(BUFFER,1024)); w.call("ME_SetStoredSpeed",e,4)
    assert w.call("ME_ImportState",BUFFER,1024)==1
    assert w.call("ME_GetStoredSpeed",e)==14
    corrupted=bytearray(payload); corrupted[18]=1; w.u.mem_write(BUFFER,bytes(corrupted))
    assert w.call("ME_ImportState",BUFFER,1024)==0
    assert w.call("ME_GetStoredSpeed",e)==14
    check=2166136261
    for i,value in enumerate(corrupted):
        if i<12 or i>=16: check=((check^value)*16777619)&0xFFFFFFFF
    struct.pack_into("<I",corrupted,12,check)
    w.u.mem_write(BUFFER,bytes(corrupted))
    assert w.call("ME_ImportState",BUFFER,1024)==0 # valid checksum, invalid rank
    assert w.call("ME_GetStoredSpeed",e)==14
    w.u.mem_write(BUFFER,payload); w.u.mem_write(DUNGEON+0x749,b"\x03")
    assert w.call("ME_ImportState",BUFFER,1024)==0
    w.reset(); w.abilities[e]={4}
    assert w.call("ME_SetWeatherSource",e,4,0,4)==1
    assert w.u.mem_read(DUNGEON+0xcd38,1)==b"\x04"
    assert w.call("ME_ForcedWeather")==0xFFFFFFFF
    w.abilities[e]={28}
    assert w.call("ME_SetWeatherSource",e,2,1,28)==1
    w.u.mem_write(DUNGEON+0x749,b"\x02")
    assert w.call("ME_ForcedWeather")==0xFFFFFFFF
    assert w.u.mem_read(0x022AB46A,1)==b"\0"
    w.reset(); w.abilities[e]={28}; w.abilities[other]={120}
    w.call("ME_SetWeatherSource",e,2,1,28); w.call("ME_SetWeatherSource",other,5,1,120)
    assert w.call("ME_ExportState",BUFFER,1024)==1024
    saved_weather=bytes(w.u.mem_read(BUFFER,1024))
    w.reset(); w.abilities[e]={28}; w.abilities[other]={120}
    moved_monster=0x02270000
    w.u.mem_write(moved_monster,bytes(w.u.mem_read(MONSTERS[1],0x400)))
    w.u.mem_write(other+0xb4,struct.pack("<I",moved_monster))
    w.u.mem_write(BUFFER,saved_weather)
    assert w.call("ME_ImportState",BUFFER,1024)==1
    assert w.call("ME_ForcedWeather")==5
    w.suppressed.add(other)
    assert w.call("ME_ForcedWeather")==2
    w.reset(); w.weather(5)
    w.u.reg_write(UC_ARM_REG_R5,e); w.u.reg_write(UC_ARM_REG_SP,STACK)
    w.u.emu_start(0x02310170,0x02310360,count=10000)
    assert w.u.reg_read(UC_ARM_REG_PC)==0x02310360
    assert w.u.mem_read(m+0x10,2)==struct.pack("<H",100) # real hail chip dispatch skips damage
    # Native freeze/clear/reset and old chip-stage paths are explicitly patched.
    native_overlays=rom.loadArm9Overlays()
    assert word(native_overlays[29].data,0x02310180,OV29)>>24==0xEA
    assert word(native_overlays[29].data,0x0230C03C,OV29)==0xE1A00000
    text= [decode_english(t) for t in parse_str_file(rom.getFileByName("MESSAGE/text_e.str"))]
    entries=json.loads((MODULE/"data/phase1_strings.json").read_text(encoding="utf-8"))["entries"]
    for entry in entries:
        assert text[entry["index"]]==entry["en"]
        assert not translation_issues(entry["en"],entry["ko"])
    korean=REPO/"true_patches/korean"
    plan=plan_translation(rom,load_source(korean,load_module_manifest(korean)))
    for entry in entries:
        assert plan.text_dec[entry["index"]].ko==entry["ko"]
    # Every patched instruction and allocated cave is verified; tampering fails.
    broken=copy.deepcopy(record); broken.data[0]["cave_sha256"]="invalid"
    try: verify_mega_evolve_module(rom,MODULE,manifest,broken)
    except AssertionError: pass
    else: raise AssertionError("cave tampering accepted")
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print("PASS ARM: Speed caps/multipliers/Simple/Clear Body/Unaware/Gale Wings, hit consumers,")
    print("          native weather selection, family mapping, defense/power, suppression/source order,")
    print("          component codec corruption/floor checks and instruction/cave guards.")
    print("No ROM/save/state files were written; automatic save-codec wiring belongs to phase 4.")


if __name__=="__main__": main()
