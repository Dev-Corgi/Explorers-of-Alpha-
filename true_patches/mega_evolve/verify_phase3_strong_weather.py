"""Native harsh sun/heavy rain type immunity respects local weather suppression."""
import hashlib,struct
from .verify_phase3_native_coefficients import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER
from .phase3 import load
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address==0x0230175c:
            a,b=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
            ma=struct.unpack('<I',bytes(u.mem_read(a+0xb4,4)))[0];mb=struct.unpack('<I',bytes(u.mem_read(b+0xb4,4)))[0]
            self.ret(bytes(u.mem_read(ma+6,1))!=bytes(u.mem_read(mb+6,1)));return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rom=NintendoDSRom(SOURCE.read_bytes())
    manifest=dict(load_module_manifest(MODULE),phase=3);record=apply_phase1(rom,MODULE,manifest,None,{'strong_weather_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'strong_weather_test':True})
    w=World(rom,record);ids={a['key']:a['id'] for a in load()['abilities']};cases=0
    for name,weather,blocked_type in (('시작의바다',4,2),('끝의대지',1,3)):
        for suppressed in (False,True):
            for type_ in (blocked_type,1):
                w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4));w.profile(0,(ids[name],0));w.profile(1,(0,0))
                w.weather(weather);assert w.call('ME_ForcedWeather')==weather
                if suppressed:
                    w.profile(1,(ids['날씨부정'],0))
                    w.u.mem_write(DUNGEON+0x12b28,struct.pack('<I',ENTITIES[1]))
                packet=bytearray(20);struct.pack_into('<I',packet,0,100);packet[12]=type_;w.u.mem_write(BUFFER+0x400,bytes(packet))
                reached=w.segment(0x023c0468,{0x023093d8,0x0230a918},{UC_ARM_REG_R8:ENTITIES[0],UC_ARM_REG_R7:ENTITIES[1],UC_ARM_REG_R6:BUFFER+0x400})
                blocked=not suppressed and type_==blocked_type
                assert reached==(0x0230a918 if blocked else 0x023093d8),(name,suppressed,type_,hex(reached))
                if blocked:assert bytes(w.u.mem_read(BUFFER+0x410,1))==b'\x01'
                # Local immunity suppression must not erase the active source.
                assert w.call('ME_ForcedWeather')==weather;cases+=3
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native strong-weather cases: harsh sun Water and heavy rain Fire immunity, matching types only, Air Lock protected target passes damage, source retained, harsh-sun miss marker prevents additional effects. Native UI/team-relation eligibility modeled; no ROM/save output.')
if __name__=='__main__':main()
