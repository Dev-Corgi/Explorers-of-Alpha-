#!/usr/bin/env python3
"""Conservative ARM cave audit; does not execute or certify melonDS JIT."""
import sys,json,struct,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.venv/Lib/site-packages'))
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from capstone.arm_const import ARM_OP_MEM,ARM_REG_PC
P=ROOT/'Export Rom/Explorers of Alpha_Vanilla+full_stack+korean+jit_compat.nds'
rom=NintendoDSRom(P.read_bytes());state=json.loads(P.with_suffix('.state.json').read_text())
t=loadOverlayTable(rom.arm9OverlayTable,lambda i,n:rom.files[n])
images={'arm9':(0x02000000,bytes(rom.arm9))}
images.update({f'ov{i}':(o.ramAddress,bytes(o.data)) for i,o in t.items()})
caves=[]
for m in state['applied']:
 for c in m.get('caves',[]):
  if m['id']=='korean' and c['load_address']==0x023E0000:continue
  caves.append((c['load_address'],c['load_address']+c['size'],m['id'],c['overlay']))
def owner(a):return next((x for x in caves if x[0]<=a<x[1]),None)
def word(a):
 c=owner(a)
 if not c:return None
 base,b=images[c[3]];off=a-base
 return struct.unpack_from('<I',b,off)[0] if 0<=off<=len(b)-4 else None
def target(w,a):
 imm=w&0xFFFFFF
 if imm&0x800000:imm-=0x1000000
 return a+8+4*imm
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM);cs.detail=True
roots=set();root_provenance=collections.defaultdict(list)
hooksites={h['site'] for m in state['applied'] for h in m.get('hooks',[])}
for name,(base,b) in images.items():
 for off in range(0,len(b)-3,4):
  a=base+off;w=struct.unpack_from('<I',b,off)[0]
  if w&0x0E000000==0x0A000000 and w>>28<15:
   dest=target(w,a)
   if owner(dest) and (a in hooksites or owner(a) or name in ('ov29','ov36')):
    roots.add(dest);root_provenance[dest].append([name,hex(a)])
visited={};pending=list(roots);bad=[];pc_literals=[];pc_stores=[];alignment=[];special=[];base_list=[];stores=[]
while pending:
 a=pending.pop()
 if a in visited or not owner(a):continue
 w=word(a)
 if w is None:continue
 instructions=list(cs.disasm(struct.pack('<I',w),a))
 if not instructions:
  bad.append([owner(a)[2],hex(a),hex(w)]);continue
 i=instructions[0];visited[a]=(i.mnemonic,i.op_str)
 module=owner(a)[2]
 if w&0x0E000000==0x0A000000 and w>>28<15:
  dest=target(w,a)
  if owner(dest):pending.append(dest)
  if w&(1<<24) or w>>28!=14:pending.append(a+4)
  continue
 if i.mnemonic in ('udf','svc','mcr','mrc','ldrd','strd','swp','swpb'):
  special.append([module,hex(a),i.mnemonic,i.op_str])
 if w&0x0E000000==0x08000000:
  rn=(w>>16)&15;regs=w&0xFFFF
  if not regs or (w&(1<<21) and regs&(1<<rn) and rn!=13):base_list.append([module,hex(a),i.mnemonic,i.op_str])
 for op in i.operands:
  if op.type!=ARM_OP_MEM:continue
  if op.mem.base==ARM_REG_PC and not op.mem.index:
   dest=a+8+op.mem.disp
   if i.mnemonic.startswith('ldr'):
    pc_literals.append([module,hex(a),hex(dest),i.mnemonic])
    if i.mnemonic in ('ldr','ldrh','ldrsh') and dest%(2 if i.mnemonic!='ldr' else 4):alignment.append([module,hex(a),i.mnemonic,hex(dest)])
   elif i.mnemonic.startswith('str'):pc_stores.append([module,hex(a),hex(dest),i.mnemonic])
 if i.mnemonic.startswith('str'):stores.append([module,hex(a),i.mnemonic,i.op_str])
 # ARM data processing/load/ldm that writes pc exits; conditional exit has a fallthrough.
 exits=(w&0x0FFFFFF0 in (0x012FFF10,0x012FFF30) or
  (w&0x0E000000==0x08000000 and w&(1<<20) and w&(1<<15)) or
  (w&0x0C100000==0x04100000 and ((w>>12)&15)==15) or
  (w&0x0C000000==0 and ((w>>12)&15)==15 and ((w>>21)&15) not in (8,9,10,11)))
 if not exits or w>>28!=14:pending.append(a+4)
# Linear constant-address tracing inside each basic block. Registers from callers
# are unknown; BL invalidates caller-saved registers. These are sufficient patterns
# only, not a whole-program alias or lifetime proof.
const_writes=[];unaligned_static=[]
for root in sorted(roots):
 regs={};a=root
 for _ in range(128):
  if a not in visited:break
  w=word(a);mn,op=visited[a]
  rn=(w>>16)&15;rd=(w>>12)&15
  if w&0x0E000000==0x0A000000:break
  if w&0x0E000000==0x04000000 and w>>28==14 and w&(1<<24) and not w&(1<<21):
   base=a+8 if rn==15 else regs.get(rn)
   addr=(base+((w&0xFFF) if w&(1<<23) else -(w&0xFFF))) if base is not None else None
   if w&(1<<20):
    if addr is not None and not w&(1<<22) and addr%4:unaligned_static.append([owner(a)[2],hex(a),hex(addr)])
    if rn==15 and addr is not None and not w&(1<<22):
     c=owner(a);bbase,b=images[c[3]];off=addr-bbase
     regs[rd]=struct.unpack_from('<I',b,off)[0] if 0<=off<=len(b)-4 else None
    else:regs.pop(rd,None)
   elif addr is not None:const_writes.append([owner(a)[2],hex(a),hex(addr),1 if w&(1<<22) else 4])
  elif w&0x0E000000==0x02000000 and w>>28==14:
   shift=((w>>8)&15)*2;imm=w&255;imm=((imm>>shift)|(imm<<(32-shift)))&0xFFFFFFFF if shift else imm
   opcode=(w>>21)&15
   if opcode==13:regs[rd]=imm
   elif opcode in (2,4) and rn in regs and regs[rn] is not None:regs[rd]=(regs[rn]+(imm if opcode==4 else -imm))&0xFFFFFFFF
   elif opcode not in (8,9,10,11):regs.pop(rd,None)
  elif mn.startswith(('pop','ldm','bx')):break
  elif w&0x0C000000==0 and ((w>>21)&15) not in (8,9,10,11):regs.pop(rd,None)
  a+=4
const_writes=sorted(set(tuple(x) for x in const_writes))
write_pc_read_overlap=[]
for m,pc,dest,width in const_writes:
 dest=int(dest,16)
 for lm,lpc,lit,mn in pc_literals:
  if dest<=int(lit,16)<dest+width:write_pc_read_overlap.append([m,pc,hex(dest),lm,lpc])
counts=collections.Counter(owner(a)[2] for a in visited)
report={'rom':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),
 'applied_modules':len(state['applied']),'code_caves':len(caves),'roots':len(roots),'conservatively_reachable_arm_words':len(visited),
 'words_by_module':dict(sorted(counts.items())),
 'undecodable_words':bad,'special_instructions':special,'pc_relative_unaligned_reads':alignment,
 'pc_relative_stores':pc_stores,'block_transfer_base_in_list_or_empty':base_list,
 'constant_address_writes':const_writes,'static_unaligned_word_reads':unaligned_static,
 'constant_write_vs_pc_literal_read_overlap':write_pc_read_overlap,
 'limitations':['Branch roots in overlay data can be false positives.',
 'Indirect calls, heap pointers, runtime-generated item/waza code, IRQ timing and emulator JIT behavior are not fully analyzed.',
 'A clean static audit does not prove crash-free JIT execution.']}
out=ROOT/'tools/true_patches_jit_audit.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('constant_address_writes','limitations')},indent=2))
