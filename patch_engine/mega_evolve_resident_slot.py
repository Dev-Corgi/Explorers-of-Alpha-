"""Use only the audited unoccupied EVS1 trampoline padding in ARM9.

The prerequisite reserves its whole cave, including padding. Its assembly
ends the last trampoline at +0x888 and starts the codec at +0x1000. Both
mega resident components explicitly subreserve this unused range; live EVS1
code, state, caches and buffers stay excluded. Placement follows the actual
native trampoline, never a fixed cave address.
"""
import struct
from .cave_allocator import allocate_cave
from .cave_reservations import FileRange,reserved_file_ranges
from .mega_evolve_runtime import branch
BASE=0x02000000


def allocate(data,state,size):
    candidates=[]
    for off in range(0,len(data)-8,4):
        if struct.unpack_from('<I',data,off)[0]!=0xE92D41F0:continue
        if struct.unpack_from('<I',data,off+4)[0]==branch(BASE+off+4,0x02059228):
            candidates.append(off-0x830)
    if len(candidates)!=1:raise RuntimeError('mega resident EVS1 trampoline guard changed')
    root=candidates[0]
    # The last HP trampoline is push{r3-r11,lr}; b original. No data follows it.
    if struct.unpack_from('<2I',data,root+0x880)!=(0xE92D4FF8,branch(BASE+root+0x884,0x023152E8)):
        raise RuntimeError('mega resident EVS1 padding boundary changed')
    lo=(root+0x888+15)&~15;hi=root+0x1000
    reserved=reserved_file_ranges(state,'arm9',exclude_module='spinda_ev_speed')
    return allocate_cave(bytes(data),BASE,size,alignment=16,reserved_file_offsets=reserved,
                         forbidden_file_offsets=[FileRange(0,lo),FileRange(hi,len(data))])
