"""Regression: real control-mode assembly precedes Trial Tower's spawn hook."""
import copy
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

import yaml
from ndspy.code import saveOverlayTable
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import UC_ARM_REG_LR

from patch_engine.mega_evolve_runtime import OV29,OV36,branch,word
from patch_engine.trial_tower import team_spawn_prior
from patch_engine.state import AppliedModule,BuildState,CaveAllocation


def check_spawn_chain(source,module):
    from .verify import ROOT,Machine,compile_code,ENTITY,RETURN
    rom=NintendoDSRom.fromFile(str(source));tables=rom.loadArm9Overlays()
    cme=ROOT/'true_patches/control_mode_enhance'
    cfg=yaml.safe_load((cme/'manifest.yaml').read_text(encoding='utf8'))
    offset=(len(tables[36].data)+3)&~3;size=cfg['cave']['estimated_bytes']
    with tempfile.TemporaryDirectory(prefix='tower_spawn_chain_') as tmp:
        work=Path(tmp);shutil.copytree(cme/'asm',work/'asm');asm=work/'asm'
        for n in [17,29,36]:
            data=bytes(tables[n].data)
            if n==36:data=data.ljust(offset+size,b'\0')
            (asm/f'overlay_{n:04d}.bin').write_bytes(data)
        (asm/'arm9.bin').write_bytes(bytes(rom.arm9))
        (asm/'generated.inc').write_text(f'ControlModeEnhanceCodeAddress equ 0x{offset:X}\n')
        result=subprocess.run([str(ROOT/'tools/armips.exe'),'-sym','cme.sym','main.asm'],cwd=asm,capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
        symbols={}
        for line in (asm/'cme.sym').read_text().splitlines():
            parts=line.split()
            if len(parts)==2:
                try:symbols[parts[1].lower()]=int(parts[0],16)
                except ValueError:pass
        for n in [17,29,36]:
            ov=tables[n];ov.data=bytearray((asm/f'overlay_{n:04d}.bin').read_bytes())
            ov.compressed=False;ov.ramSize=len(ov.data);rom.files[ov.fileID]=ov.save(compress=False)
        rom.arm9OverlayTable=saveOverlayTable(tables)
        prior=team_spawn_prior(tables[29].data,tables[36].data)
        assert prior==symbols['controlmodeenhance_spawnteam'] and prior!=0x022fc50c
        # Unexpected calls remain rejected; the fix does not relax the guard
        # into accepting arbitrary branches or bypass the earlier wrapper.
        bad=bytearray(tables[29].data)
        for instruction in [0xe1a00000,branch(0x022df6a4,prior+8,True)]:
            struct.pack_into('<I',bad,0x022df6a4-OV29,instruction)
            try:team_spawn_prior(bad,tables[36].data)
            except RuntimeError:pass
            else:raise AssertionError('unknown SpawnTeam predecessor accepted')
        assert bytes(tables[36].data[offset:offset+size])==(asm/'overlay_0036.bin').read_bytes()[offset:offset+size]
        # Compile the production wrapper verbatim with the preceding module's
        # discovered address. Downstream native services are modeled below.
        body=(module/'runtime/tower_hooks.S').read_text().split('entry ME_TowerTeamHook',1)[1].split('.ltorg',1)[0]
        (work/'hook.S').write_text(f'.syntax unified\n.arm\n.text\n#define TT_PRIOR_TEAM {prior}\n.global ME_TowerTeamHook\nME_TowerTeamHook:\n'+body+'\n.ltorg\n')
        (work/'test.c').write_text('void ME_TowerResolveReward(void){((void(*)(void))0x02001004)();}\n')
        blob,syms=compile_code(work,work/'test.c',[work/'hook.S'])
        m=Machine(rom,blob,syms);calls=[]
        leader=symbols['leaderptraddr']
        def spawn():calls.append('native spawn');m.write32(leader,ENTITY);return 17
        def alive():calls.append('control alive');assert m.reg(0)==ENTITY;return 1
        def set_leader():calls.append('control leader');assert m.reg(0)==ENTITY;return 0
        def reward():
            calls.append('tower reward')
            read=lambda p:struct.unpack('<I',m.u.mem_read(p,4))[0]
            assert read(symbols['cehome'])==ENTITY and read(symbols['ceroundpending'])==1
            return 0
        m.stubs[0x022fc50c]=spawn
        m.stubs[symbols['controlmodeenhance_regularalive']]=alive
        m.stubs[symbols['controlmodeenhance_setleader']]=set_leader
        m.stubs[0x02001004]=reward
        m.write32(0x022df6a4,branch(0x022df6a4,syms['ME_TowerTeamHook'],True))
        def resume():m.u.reg_write(UC_ARM_REG_LR,RETURN);return m.reg(0)
        m.stubs[0x022df6a8]=resume
        assert m.run(0x022df6a4,123)==17
        assert calls==['native spawn','control alive','control leader','tower reward']
    print('PASS control_mode_enhance -> Trial Tower wrapper, prior-target guards, native spawn/control leader/reward order with original return',flush=True)
