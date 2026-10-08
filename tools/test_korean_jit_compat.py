#!/usr/bin/env python3
"""Execute original and candidate Korean routines with Unicorn ARM.

This checks instruction-level equivalence and a frozen-mutable-literal fault
model. It does NOT execute melonDS JIT or certify Android gameplay.
"""
from __future__ import annotations
import json
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.venv/Lib/site-packages'))
sys.path.insert(0,str(ROOT/'tools/.korean_jit_test_deps'))
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
REGS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,
 UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
 UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR]
SP=0x027E1000
KEYBOARD=0x02200000
RETURN=0x021FF000
DRAW_CONTINUE=0x02015BC4
MEASURE_RESUME=0x02038080

def u32(data,offset=0):return struct.unpack_from('<I',data,offset)[0]
def branch(data,site):
 w=u32(data,site-0x02000000);imm=w&0xFFFFFF
 if imm&0x800000:imm-=0x1000000
 return site+8+imm*4

class Machine:
 def __init__(self,path,freeze=False):
  rom=NintendoDSRom(path.read_bytes())
  t=loadOverlayTable(rom.arm9OverlayTable,lambda i,n:rom.files[n])
  self.arm9=bytes(rom.arm9);self.ov36=bytes(t[36].data)
  self.uc=Uc(UC_ARCH_ARM,UC_MODE_ARM)
  self.uc.mem_map(0x02000000,0x400000)
  self.uc.mem_map(0x027E0000,0x4000)
  self.uc.mem_write(0x02000000,self.arm9)
  self.uc.mem_write(t[36].ramAddress,self.ov36)
  self.uc.mem_write(0x020AF710,struct.pack('<I',0x02210000))
  self.uc.mem_write(0x02210000,struct.pack('<I',0x02211000))
  self.measure=branch(self.arm9,0x0203807C)
  # Ko_SkipTrail is the word immediately preceding the measurement entry.
  self.flag=self.measure-4
  self.freeze=freeze
  self.frozen={0x020254C4:u32(self.arm9,0x254C4),self.flag:0}
  self.code_writes=[]
  self.stopped=False
  self.uc.hook_add(UC_HOOK_CODE,self.on_code)
  self.uc.hook_add(UC_HOOK_MEM_WRITE,self.on_write)
 def on_write(self,uc,access,addr,size,value,user):
  if 0x02000000<=addr<0x02000000+len(self.arm9):
   self.code_writes.append((addr,size))
 def on_code(self,uc,addr,size,user):
  if addr in (RETURN,DRAW_CONTINUE,MEASURE_RESUME):
   self.stopped=True;uc.emu_stop();return
  if not self.freeze:return
  w=u32(uc.mem_read(addr,4))
  # Model constant-folding only PC-relative immediate LDR/LDRB of changing slots.
  if (w&0x0E100000)==0x04100000 and ((w>>16)&15)==15:
   target=addr+8+((w&0xFFF) if w&(1<<23) else -(w&0xFFF))
   if target in self.frozen:
    rd=(w>>12)&15
    assert rd<15 and (w>>28)==14
    value=self.frozen[target]
    if w&(1<<22):value&=255
    uc.reg_write(REGS[rd],value)
    uc.reg_write(UC_ARM_REG_PC,addr+4)
 def init_regs(self):
  for i,r in enumerate(REGS):self.uc.reg_write(r,0x11220000+i*0x101)
  self.uc.reg_write(UC_ARM_REG_CPSR,0x13)
  self.uc.reg_write(UC_ARM_REG_SP,SP)
  self.uc.reg_write(UC_ARM_REG_LR,RETURN)
 def run(self,addr):
  self.stopped=False
  self.uc.emu_start(addr,0,count=20000)
  assert self.stopped,'Routine failed to return within the instruction limit'
 def regs(self):
  return tuple(self.uc.reg_read(r) for r in REGS)+(self.uc.reg_read(UC_ARM_REG_CPSR)&0xF0000000,)
 def draw(self,code):
  self.init_regs();self.code_writes=[]
  self.uc.mem_write(SP,b'\xA5'*0x700)
  self.uc.reg_write(UC_ARM_REG_R0,code)
  self.run(0x02025484)
  return self.regs(),bytes(self.uc.mem_read(SP,0x700))
 def measure_once(self,index):
  self.init_regs()
  self.uc.reg_write(UC_ARM_REG_R0,KEYBOARD+index)
  self.uc.reg_write(UC_ARM_REG_R1,KEYBOARD)
  self.uc.reg_write(UC_ARM_REG_R6,index)
  self.run(self.measure)
  return self.regs(),bytes(self.uc.mem_read(self.flag,1))
 def sequence(self,text,initial=0):
  self.uc.mem_write(KEYBOARD,b'\x00'*0x400)
  self.uc.mem_write(KEYBOARD+0xFC,text)
  self.uc.mem_write(self.flag,bytes([initial]))
  states=[];index=0
  for _ in range(128):
   regs,flag=self.measure_once(index);states.append((regs,flag))
   index=regs[6]+1
   if index>=len(text):break
  else:raise AssertionError('Measurement sequence did not terminate')
  return states

def main():
 source=ROOT/'Export Rom/Explorers of Alpha_Vanilla+full_stack+korean.nds'
 output=ROOT/'Export Rom/Explorers of Alpha_Vanilla+full_stack+korean+jit_compat.nds'
 old,new=Machine(source),Machine(output)
 # Real glyphs, fallback glyph, malformed boundary codes and English early returns.
 codes=[0x0041,0x007F,0x87FF,0x8800,0x887F,0x8880,0x8890,0x88A7,
  0x88FE,0x8980,0x89FE,0x8AFF,0x9280,0x9E80,0x9EFF,0x9F00,0x9F01]
 glyph_count=0
 for code in codes:
  ro,bo=old.draw(code);rn,bn=new.draw(code)
  assert ro==rn,f'Register/flags mismatch drawing {code:#x}: {ro} != {rn}'
  # sp+0x4D0 is now the saved pointer; compare all pixel output and remaining frame.
  assert bo[:0x4D0]==bn[:0x4D0] and bo[0x4D4:]==bn[0x4D4:],f'Pixel/frame mismatch {code:#x}'
  assert not new.code_writes,f'Candidate wrote ARM9 code: {new.code_writes}'
  glyph_count+=1
 texts=[b'\0',b'ASCII\0',b'\x88\x80\0',b'\x88\xA7\x89\xFE\0',
  b'A\x88\xA7B\x89\xFEZ\0',b'\x88\0',b'\x9F\0',b'\x9F\x80\0',
  b'\x87\x80\0',b'\xA0\x80\0',b'\x88\x5BZ\0',b'\x88\x88\x89\x89\0']
 measure_count=0
 for text in texts:
  for initial in (0,1,2):
   a,b=old.sequence(text,initial),new.sequence(text,initial)
   assert a==b,f'Measurement ABI/state mismatch {text!r}, flag={initial}'
   measure_count+=len(a)
 # Inject the suspected stale-constant behavior. The old code is affected;
 # the candidate contains no PC-relative read of either changing value.
 frozen_old,frozen_new=Machine(source,True),Machine(output,True)
 expected=Machine(source).draw(0x88A7)[0]
 assert frozen_old.draw(0x88A7)[0]!=expected,'Glyph fault model did not distinguish the old code'
 assert frozen_new.draw(0x88A7)[0]==expected,'Candidate retained the mutable glyph literal dependency'
 text=b'A\x88\xA7B\x89\xFEZ\0'
 expected=Machine(source).sequence(text)
 assert frozen_old.sequence(text)!=expected,'Flag fault model did not distinguish the old code'
 assert frozen_new.sequence(text)==expected,'Candidate retained the mutable flag literal dependency'
 result={'glyph_execution_cases':glyph_count,'measurement_execution_steps':measure_count,
  'registers_flags_stack_and_pixel_parity':'passed','candidate_ARM9_code_writes_during_render':0,
  'frozen_mutable_literal_fault_model':'old routines diverge; candidate matches reference',
  'actual_melonDS_JIT_execution':False,'android_device_test':'pending'}
 print(json.dumps(result,indent=2))
 if '--write-report' in sys.argv:
  report=output.with_suffix('.jit-report.json');data=json.loads(report.read_text(encoding='utf-8'))
  data['ARM_behavioral_regression']=result
  report.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
