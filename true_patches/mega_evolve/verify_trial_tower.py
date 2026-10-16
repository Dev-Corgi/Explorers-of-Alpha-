"""Read-only ROM fixture and compiled ARM tests; never writes a ROM or save."""
from __future__ import annotations
import copy
import gzip
import hashlib
import itertools
import json
import random
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/.korean_jit_test_deps'))
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from ndspy.rom import NintendoDSRom
from patch_engine.state import AppliedModule
from patch_engine.mega_evolve_trial_tower import install,verify
from patch_engine.mega_evolve_runtime import build_runtime,OV29,OV36,word
from patch_engine.korean_codec import parse_str_file,decode_english
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from true_patches.base_stats_speed.generate_tables import GEN,calc_stat_from_tables
from .trial_tower import load,header

MODULE=Path(__file__).resolve().parent
BASE=0x02180000
DUNGEON=0x02100000
ENTITY=0x02250000
MONSTER=0x02260000
SPAWN=0x02280000
BUFFER=0x02280100
RETURN=0x023ff000
STACK=0x023fe000


def compile_code(work,source,extra=()):
    compiler=shutil.which('arm-none-eabi-gcc');assert compiler
    prefix=str(Path(compiler).with_name('arm-none-eabi-'));suffix='.exe' if compiler.endswith('.exe') else ''
    (work/'test.ld').write_text(f'SECTIONS {{ . = {BASE}; .text : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) }} /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.attributes) *(.comment) }} }}')
    elf=work/'test.elf'
    p=subprocess.run([compiler,'-mcpu=arm946e-s','-marm','-Os','-ffreestanding','-fno-builtin','-nostdlib',
        '-Wall','-Wextra','-Werror','-I',str(work),'-I',str(MODULE/'runtime'),str(source),*map(str,extra),
        '-Wl,-T,'+str(work/'test.ld'),'-o',str(elf)],capture_output=True,text=True)
    assert p.returncode==0,p.stdout+p.stderr
    symbols={}
    for line in subprocess.check_output([prefix+'nm'+suffix,'--defined-only',str(elf)],text=True).splitlines():
        a,k,n=line.split();symbols[n]=int(a,16)
    binary=work/'test.bin';subprocess.run([prefix+'objcopy'+suffix,'-O','binary',str(elf),str(binary)],check=True,capture_output=True)
    return binary.read_bytes(),symbols


class Machine:
    def __init__(self,rom,blob,symbols):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM);self.u.mem_map(0x02000000,0x400000)
        self.u.mem_write(0x02000000,bytes(rom.arm9))
        for n in (10,11,29,36):
            o=rom.loadArm9Overlays()[n];self.u.mem_write(o.ramAddress,bytes(o.data))
        self.u.mem_write(BASE,blob);self.symbols=symbols;self.stubs={};self.random=random.Random(0)
        self.write32(0x02353538,DUNGEON);self.write32(ENTITY,1);self.write32(ENTITY+0xb4,MONSTER)
        self.u.hook_add(UC_HOOK_CODE,self.hook)
        self.base=(GEN/'base_stats.bin').read_bytes();self.rates=(GEN/'evo_rate.bin').read_bytes();self.primary=(GEN/'primary.bin').read_bytes()
        self.stubs[0x022eaa98]=lambda:self.random.randrange(self.reg(0))
        self.stubs[0x02001000]=self.calc
        self.stubs[0x02301fbc]=lambda:0
    def reg(self,i):return self.u.reg_read([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3][i])
    def write32(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def read16(self,p):return struct.unpack('<H',self.u.mem_read(p,2))[0]
    def hook(self,u,a,size,_):
        if a in self.stubs:
            result=self.stubs[a]() or 0;u.reg_write(UC_ARM_REG_R0,result&0xffffffff);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
    def run(self,name,*args):
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,RETURN)
        for reg,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):self.u.reg_write(reg,v)
        a=self.symbols[name] if isinstance(name,str) else name
        self.u.emu_start(a,RETURN,count=500000)
        assert self.u.reg_read(UC_ARM_REG_PC)==RETURN,hex(self.u.reg_read(UC_ARM_REG_PC))
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK
        return self.reg(0)
    def calc(self):
        p=struct.unpack_from('<H',self.primary,self.reg(0)*2)[0]
        return calc_stat_from_tables(p,self.reg(1),self.reg(2),self.reg(3),self.base,self.rates)
    def floor(self,room):self.u.mem_write(DUNGEON+0x748,bytes([234,10]));self.u.mem_write(DUNGEON+0x40da,bytes([room]))


def main():
    source=ROOT/'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
    before=hashlib.sha256(source.read_bytes()).hexdigest();rom=NintendoDSRom(source.read_bytes());d=load()
    record=AppliedModule('mega_evolve',21,data=[{'symbols':{name:0x023b8000+i*16 for i,name in enumerate([
        'ME_TowerSpawnHook','ME_TowerStatsHook','ME_TowerSpeciesHook','ME_TowerItemHook','ME_TowerTeamHook',
        'ME_TowerSelectHook','ME_TowerFloorHook','ME_TowerFixedLoadedHook'])},'cave_hashes':[]}])
    info=install(rom,MODULE,None,record);verify(rom,info)
    from .fixed_extension_plugin.verify import check_plugin
    check_plugin(rom)
    # Independent screenshot transcription; check displayed deltas AFTER the
    # MAPPA serialize/deserialize round-trip on every floor, not raw thresholds.
    expected_food={109:2055,110:2055,119:342,120:343,121:342,122:342,
                   123:343,124:342,125:343,126:342,127:343,128:342,129:343,
                   130:342,131:343,132:342,133:343,134:342,135:343,137:68}
    fixture=FileType.MAPPA_BIN.deserialize(rom.getFileByName('BALANCE/mappa_s.bin'))
    for floor in fixture.floor_lists[info['group']]:
        assert floor.layout.item_density==4
        last=0;actual={}
        for item in [109,110,111,112,113,114,115,*range(119,139),353]:
            value=floor.floor_items.items.get(item)
            if value is not None:
                actual[item]=value-last;last=value
        assert actual==expected_food and last==10000
    print('PASS all 99 floor-food pools match screenshot weights after MAPPA round-trip; other pools/categories retain source values',flush=True)
    assert rom.getFileByName('BALANCE/fixed.bin')==rom.getFileByName('UTILITY/fixed.bin')
    text=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    translations=json.loads(gzip.decompress((ROOT/'true_patches/korean/data/translations.json.gz').read_bytes()))
    assert translations['text_e'][str(d['name_index'])]==dict(en='Trial Tower',ko='시련의 탑')
    assert decode_english(text[d['name_index']])=='Trial Tower'
    print('PASS dungeon clone, 10 new layouts, native data banks, restrictions, victory flags, name/translation and corruption guards',flush=True)
    broken=copy.deepcopy(rom);blob=bytearray(broken.getFileByName('UTILITY/fixed.bin'));blob[-1]^=1;broken.setFileByName('UTILITY/fixed.bin',blob)
    try:verify(broken,info)
    except AssertionError:pass
    else:raise AssertionError('corrupt native fixed rooms accepted')
    with tempfile.TemporaryDirectory(prefix='tower_test_') as temp:
        work=Path(temp);(work/'trial_tower_generated.h').write_text(header())
        (work/'test.c').write_text('''typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
#define BYTE(p,o) (*((u8*)(p)+(o)))
#define U16(p,o) (*(u16*)((u8*)(p)+(o)))
#define U32(p,o) (*(u32*)((u8*)(p)+(o)))
#define FN(a,t) ((t)(a))
#define FORM_STAT_RESUME 0x02001000
static u8 *dungeon(void){return *(u8**)0x02353538;}
static u8 *monster(u8 *e){return e&&U32(e,0)==1?(u8*)U32(e,0xb4):0;}
static int clamp(int x,int lo,int hi){return x<lo?lo:x>hi?hi:x;}
#include "trial_tower.c"
''')
        # Exercise the actual first-turn restore callback after a native floor
        # reset, with unrelated actor/state restoration services isolated.
        ready=(MODULE/'runtime/phase4_quick.c').read_text().split('void ME_QuickReady(void)',1)[1]
        with (work/'test.c').open('a') as out:
            out.write('''
#define ME_TRIAL_TOWER 1
enum {COUNT=0,SNAPSHOT=1024};
static u8 quick_pending[0x1400];static int quick_loaded;
static u32 sunlight_serial,movement_serial;
static u8 *entity(int i){(void)i;return 0;}
static void ME_QuickActor(u8 *e){(void)e;}
static void ME_ImportState(u8 *p,int size){(void)p;(void)size;}
void ME_QuickReady(void)'''+ready+'''
void ME_TestResume(u8 *saved){
    for(int i=0;i<27;i++)quick_pending[4888+i]=saved[i];
    quick_loaded=1;ME_TowerFloorReset();ME_QuickReady();
}
''')
        (work/'hooks.S').write_text('.syntax unified\n.arm\n.text\n.macro entry name\n.global \\name\n\\name:\n.endm\n#include "trial_tower_hooks.S"\n')
        blob,symbols=compile_code(work,work/'test.c',[work/'hooks.S']);m=Machine(rom,blob,symbols)
        from .verify_trial_tower_rewards import check_rewards
        check_rewards(Machine(rom,blob,symbols),rom,info)
        m.stubs[0x020137b8]=lambda: m.u.mem_write(m.reg(0),struct.pack('<BBHHBB',9,0,0,m.reg(1),10,0)) or 0
        permutations=set();cases=0;covered=set()
        # Every Fisher-Yates decision sequence is a bijection onto all 9! orders.
        for choices in itertools.product(*[range(i+1) for i in range(8,0,-1)]):
            a=list(range(9))
            for i,j in zip(range(8,0,-1),choices):a[i],a[j]=a[j],a[i]
            permutations.add(tuple(a))
        assert len(permutations)==362880
        for seed in range(80):
            m.random.seed(seed);m.run('ME_TowerReset');seen=[]
            for i,level in enumerate(d['levels']):
                m.floor(230+i);m.u.mem_write(SPAWN,struct.pack('<HBBIHH',415,6,0,0,1,0))
                m.run('ME_TowerSpawn',SPAWN);species=m.read16(SPAWN);seen.append(species)
                covered.add((species,level))
                assert m.run('ME_TowerSpecies',415)==species
                assert m.read16(SPAWN+8)==level
                m.u.mem_write(MONSTER,bytes(0x200));m.u.mem_write(MONSTER+2,struct.pack('<H',species))
                m.run('ME_TowerStats',ENTITY)
                p=struct.unpack_from('<H',m.primary,species*2)[0]
                hp=calc_stat_from_tables(p,level,0,0,m.base,m.rates)*4
                assert m.read16(MONSTER+0x10)==m.read16(MONSTER+0x12)==hp
                assert m.read16(MONSTER+0xe)==999
                assert m.u.mem_read(MONSTER+0xa,1)==bytes([level])
                row=next(b for b in d['bosses'] if b['species']==species)
                assert [m.read16(MONSTER+0x128+j*8) for j in range(4)]==row['moves']
                m.run('ME_TowerSave',BUFFER);saved=bytes(m.u.mem_read(BUFFER,13))
                m.run('ME_TowerReset');assert m.run('ME_TowerLoad',BUFFER)==1
                m.run('ME_TowerSave',BUFFER);assert bytes(m.u.mem_read(BUFFER,13))==saved
                cases+=1
            assert len(set(seen))==9
        assert len(covered)==81
        m.floor(239)
        for boss in d['final']:
            m.u.mem_write(SPAWN,struct.pack('<HBBIHH',boss['source_species'],6,0,0,1,0));m.run('ME_TowerSpawn',SPAWN)
            assert m.read16(SPAWN)==boss['species'] and m.read16(SPAWN+8)==60
            m.u.mem_write(MONSTER,bytes(0x200));m.u.mem_write(MONSTER+2,struct.pack('<H',boss['species']));m.run('ME_TowerStats',ENTITY)
            p=struct.unpack_from('<H',m.primary,boss['species']*2)[0]
            assert m.read16(MONSTER+0x10)==m.read16(MONSTER+0x12)==calc_stat_from_tables(p,60,0,0,m.base,m.rates)*2
            assert [m.read16(MONSTER+0x128+j*8) for j in range(4)]==boss['moves']
        for bad in (b'BAD!'+bytes(9),struct.pack('<I',0x3154544d)+bytes(9),struct.pack('<I',0x3154544d)+bytes(range(1,10))):
            m.u.mem_write(BUFFER,bad);assert m.run('ME_TowerLoad',BUFFER)==0
        # Original rooms and unrelated dungeons must not be touched.
        for dungeon,room in ((102,21),(234,21),(102,230)):
            m.floor(room);m.u.mem_write(DUNGEON+0x748,bytes([dungeon,10]));m.u.mem_write(SPAWN,b'\x9f\x01\x06'+bytes(9));old=bytes(m.u.mem_read(SPAWN,12))
            m.run('ME_TowerSpawn',SPAWN);assert bytes(m.u.mem_read(SPAWN,12))==old
        print(f'PASS compiled ARM: {cases} boss/level/HP/moves/IQ cases, final trio, shuffle bijection (9!), saved permutations and scope guards',flush=True)
        # Resident getter hooks execute native fallbacks for existing dungeons.
        m.symbols.update(info['symbols'])
        for name,expected in (('ME_TowerFloors',99),('ME_TowerGroup',113),('ME_TowerPreceding',0),('ME_TowerGroupFloors',99),('ME_TowerSwapId',234),('ME_TowerSwapIndex',234),('ME_TowerMap',235)):
            assert m.run(name,234)==expected
        assert m.run('ME_TowerFloors',102)==99 and m.run('ME_TowerGroup',102)==68
        assert m.run('ME_TowerFloors',180)==5 and m.run('ME_TowerSwapIndex',102)==102
        print('PASS resident dungeon queries and original Zero Isle South/dojo fallbacks',flush=True)
        requests=[]
        def string_resume():
            requests.append(m.reg(1));m.u.reg_write(UC_ARM_REG_SP,m.u.reg_read(UC_ARM_REG_SP)+16)
            return m.reg(0)
        m.stubs[0x0202578c]=string_resume
        for old in (16799,17058,17317,17574,1087):
            m.run('ME_TowerName',BUFFER,old)
            assert requests[-1]==(1087 if old==1087 else 19781)
        m.stubs.pop(0x0202578c)
        # Execute the original victory objective code against the cloned
        # properties, including the three-enemy case that can otherwise trap a team.
        m.stubs[0x0234ba54]=lambda:0
        for room,total in ((230,1),(239,3)):
            m.floor(room);m.run(0x022ef738)
            assert m.u.mem_read(DUNGEON+0x40ca,1)==b'\x02'
            m.u.mem_write(DUNGEON+6,b'\0')
            for i in range(16):m.write32(DUNGEON+0x12b38+i*4,0)
            for i in range(total):
                e=ENTITY+i*0x200;mon=MONSTER+i*0x400
                m.write32(e,1);m.write32(e+0xb4,mon);m.u.mem_write(mon+8,b'\0')
                m.write32(DUNGEON+0x12b38+i*4,e)
            for i in range(total):
                e=ENTITY+i*0x200;m.run(0x022ef7c4,e,6,1)
                assert m.u.mem_read(DUNGEON+6,1)==(b'\x01' if i==total-1 else b'\0')
                m.write32(e,0)
        print('PASS all four native name aliases and native single/triple-enemy victory objective/advance paths',flush=True)
        # Execute the ORIGINAL constructor and its epilogue, not a fabricated
        # pointer plus a stubbed continuation. That old test duplicated the
        # installer's wrong adjacent literal and hid a broken menu return.
        ground=rom.loadArm9Overlays()[11]
        m.u.mem_write(ground.ramAddress,bytes(ground.data))
        menu=BUFFER+0x1000;allocations=[];dungeon_modes={}
        def allocate_menu():
            allocations.append(m.reg(0));return menu
        m.stubs[0x02001170]=allocate_menu
        m.stubs[0x0204cf9c]=lambda:dungeon_modes.get(m.reg(0),0)
        # Reproduce v16: using the adjacent selector literal must fail this
        # native-constructor test, even when Trial Tower is still locked.
        cave=record.caves[-1]
        resident=bytes(m.u.mem_read(cave.load_address,cave.size))
        assert resident.count(struct.pack('<I',0x02324d1c))==1
        wrong=resident.replace(struct.pack('<I',0x02324d1c),struct.pack('<I',0x0238a080))
        m.u.mem_write(cave.load_address,wrong)
        dungeon_modes.update({1:1,102:3})
        m.write32(0x0238a080,0);m.write32(0x0238a084,0xdeadbeef)
        try:m.run(0x022ffaf0)
        except UcError:pass
        else:raise AssertionError('v16 wrong menu pointer was not detected')
        m.u.mem_write(cave.load_address,resident)
        for kind,states,expected in (
            (0,{1:1,102:3},[1,102]),
            (0,{1:1,102:3,234:1},[1,102,234]),
            (0,{1:1,102:3,234:3},[1,102,234]),
            (0,{},[]),
            (0,{234:1},[234]),
            (2,{180:1,234:1},[180]),
            (3,{191:1,234:1},[191]),
        ):
            dungeon_modes.clear();dungeon_modes.update(states)
            # This selector and the allocated-menu owner are independent native
            # globals. Keep a sentinel after the selector to catch wrong reads.
            m.write32(0x0238a080,kind);m.write32(0x0238a084,0xdeadbeef)
            m.u.mem_write(menu,bytes(0x518)+b'GUARD')
            result=m.run(0x022ffaf0)
            assert allocations[-1]==0x518
            assert struct.unpack('<I',m.u.mem_read(0x02324d20,4))[0]==menu
            assert struct.unpack('<I',m.u.mem_read(menu+0x14,4))[0]==len(expected)
            assert [m.read16(menu+0x18+i*2) for i in range(len(expected))]==expected
            assert result==int(bool(expected))
            assert bytes(m.u.mem_read(menu+0x518,5))==b'GUARD'
            assert struct.unpack('<I',m.u.mem_read(0x0238a084,4))[0]==0xdeadbeef
        print('PASS v16 failure reproduction and native departure constructor through menu return: locked/unlocked/cleared, existing/empty lists and dojo exclusions',flush=True)
        # The native selector must reach the existing Zero Isle South warning
        # Cases, while SetEnterDungeon and script variables keep the new ID.
        script=FileType.SSB.deserialize(rom.getFileByName('SCRIPT/D46P21A/enter04.ssb'),
                                       static_data=get_ppmdu_config_for_rom(rom))
        ops={op.offset:op for routine in script.routine_ops for op in routine}
        code=BUFFER+0x2000;frame=BUFFER+0x4000
        for offset,op in ops.items():
            m.u.mem_write(code+offset*2,struct.pack('<'+'H'*(len(op.params)+1),op.op_code.id,*op.params))
        variables={}
        m.stubs[0x0204b820]=lambda:variables.update({m.reg(1):m.reg(2)})
        m.stubs[0x0204afc0]=lambda:2
        m.stubs[0x0204ca94]=lambda:0
        m.stubs[0x0200c240]=lambda:0  # debug logging only
        m.stubs[0x0205ee40]=lambda:0  # no mission override
        init=word(rom.arm9,0x0204e96c,0x02000000)
        ready=word(rom.arm9,0x0204e970,0x02000000)
        scene=word(ground.data,0x022e9588,ground.ramAddress)
        def read32(p):return struct.unpack('<I',m.u.mem_read(p,4))[0]
        def select(dungeon):
            m.u.mem_write(frame,bytes(0x80));m.u.mem_write(frame+0xe,struct.pack('<H',5))
            m.write32(frame+0x14,code);m.write32(frame+0x1c,code+918*2)
            m.write32(frame+0x34,code+915*2)
            m.u.mem_write(0x02324d1c,struct.pack('<h',dungeon))
            m.run(0x022dd2c0,frame)
        for dungeon in (102,234):
            select(dungeon)
            assert read32(frame+0x1c)==code+1154*2  # real Case 26
            assert variables[38]==variables[39]==variables[41]==dungeon
            assert m.u.mem_read(init,1)==bytes([dungeon]) and m.read16(init+2)==dungeon
            assert m.u.mem_read(ready,1)==b'\x01'
            # Follow the ROM's actual mail/Jump/menu operations. Model the UI
            # answer only; the ARM selector, Case dispatch and entry are native.
            for yes in (False,True):
                pc=1154;messages=[]
                while ops[pc].op_code.name!='main_EnterAdventure':
                    op=ops[pc];name=op.op_code.name;args=op.params
                    if name=='message_Mail':messages.append(script.strings['english'][args[0]])
                    elif name=='Jump':pc=args[0];continue
                    elif name=='message_SwitchMenu':
                        choices=[ops[pc+3],ops[pc+6]]
                        assert all(x.op_code.name=='CaseMenu' for x in choices)
                        pc=choices[0 if yes else 1].params[1]
                        if not yes:
                            assert ops[pc+5].op_code.name=='supervision_Suspend'
                            break
                        continue
                    pc+=1+len(args)
                assert len(messages)==4
                if yes:
                    assert ops[pc].params==[251,30]
                    m.write32(scene+0x1c,0)
                    m.u.mem_write(frame+0xe,struct.pack('<H',5))
                    m.u.mem_write(frame+0x44,struct.pack('<H',1))
                    m.write32(frame+0x34,code+pc*2);m.write32(frame+0x1c,code+(pc+3)*2)
                    m.run(0x022dd2c0,frame)
                    assert read32(scene+0x1c)==3 and read32(scene+0x18)==30
                    assert m.u.mem_read(init,1)==bytes([dungeon]) and m.read16(init+2)==dungeon
        # Second admission query preserves Trial Tower's own open/progress bits.
        m.stubs[0x0204d2f8]=lambda:1
        m.stubs[0x0204cee0]=lambda:1
        for mode,expected in ((1,17),(3,0x4001)):
            dungeon_modes.clear();dungeon_modes[234]=mode
            assert m.run(0x0204f488,234,0,0)==expected
        select(-1)
        assert m.read16(frame+0x44)==0xffff
        print('PASS native selection/Case 26 warnings, ROM Yes/No routes, native entry with ID234, cancellation and own unlock checks',flush=True)
        # Compile the complete production payload to catch integration and
        # relocation failures without rebuilding or saving the full stack.
        from patch_engine.mega_evolve_phase3_runtime import native_defines
        from patch_engine.mega_evolve_loader import relocation_offsets
        from true_patches.mega_evolve.status_hooks import ENTRIES
        installed=NintendoDSRom.fromFile(str(ROOT/'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds'))
        ov29=bytearray(installed.loadArm9Overlays()[29].data)
        for _,site,expected in ENTRIES:
            if expected!=0xea000000:struct.pack_into('<I',ov29,site-OV29,expected)
        defines=native_defines(ov29)
        defines.update(FORM_STAT_RESUME=0x023b0008,FORM_RATE_RESUME=0x023b0100)
        _,body=build_runtime(MODULE,work,0x01000000,0x023b1000,0x023b1800,6,0,defines,emit_relocations=True)
        assert body['MERuntimeEnd']-0x01000000<0x40000
        assert 'ME_TowerSpawnHook' in body and 'ME_TowerStatsHook' in body
        relocation_offsets(work/'phase1.elf')
        print('PASS complete phase6 payload compilation, exports, relocation validation and RAM budget',flush=True)
        from patch_engine.mega_evolve_phase6 import header as spring_header
        from true_patches.mega_evolve.phase6 import load as spring_data
        from true_patches.luminous_evolution.verify import Machine as SpringMachine,ROSTER,INDEX
        spring=spring_data()
        (work/'phase6_generated.h').write_text(spring_header(installed,installed.loadArm9Overlays()[16].data,spring))
        (work/'phase6_generated_asm.h').write_text('')
        blob,syms=compile_code(work,MODULE/'runtime/phase6_spring.c',[MODULE/'runtime/phase6_spring.S'])
        sm=SpringMachine(installed,syms);sm.u.mem_write(BASE,blob)
        sm.stub(0x020555a8,lambda:ROSTER+sm.reg(0)*0x44)
        opened={};writes=[];convert_ok=[True]
        sm.stub(0x0204cf9c,lambda:opened.get(sm.reg(0),0))
        def open_dungeon():opened[sm.reg(0)]=sm.reg(1)
        sm.stub(0x0204d018,open_dungeon)
        sm.stub(0x0204b988,lambda:writes.append((sm.reg(1),sm.reg(2),sm.reg(3))))
        def convert():
            if convert_ok[0]:sm.u.mem_write(ROSTER+4,struct.pack('<H',sm.reg(2)))
            return 1
        sm.stub(0x0205a340,convert);sm.stub(0x0205a288,lambda:1)
        mega=next(r for r in spring['routes'] if r['target_stage']==1)
        sm.run('ME_Spring_Prepare');sm.record(0,mega['source'],80);sm.select(0);sm.run('ME_Spring_Submenu')
        assert not opened and not writes  # selecting or cancelling never unlocks
        convert_ok[0]=False;sm.run('ME_Spring_Convert',INDEX,mega['target']);assert not opened
        convert_ok[0]=True;sm.run('ME_Spring_Convert',INDEX,mega['target'])
        assert opened=={234:1} and (0x53,234,1) in writes and (0x55,235,1) in writes
        opened.clear();writes.clear()
        shiny=next(r for r in spring['routes'] if r['target_stage']==2)
        sm.run('ME_Spring_Prepare');sm.record(0,shiny['source'],1);sm.select(0);sm.run('ME_Spring_Submenu')
        sm.run('ME_Spring_Convert',INDEX,shiny['target']);assert not opened and not writes
        sm.run('ME_Spring_Prepare');sm.record(0,1,80);sm.select(0)
        sm.run('ME_Spring_Convert',INDEX,2);assert not opened and not writes
        print('PASS compiled Spring success-only unlock; menu/cancel, failed conversion, ordinary evolution and Shiny exclusions',flush=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before


if __name__=='__main__':main()
