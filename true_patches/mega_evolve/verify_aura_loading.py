"""Run actual whole-WAN loading with the regenerated aura and bounded allocation."""
import json,struct,xml.etree.ElementTree as ET
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from .verify_actor_sprite_cache import CacheWorld
from .verify_phase1 import REPO
from unicorn.arm_const import *


class AuraWorld(CacheWorld):
    def __init__(self,rom):
        self.rom=rom;self.opened=[];self.live={};self.peak=0
        self.packs=[FileType.BIN_PACK.deserialize(rom.getFileByName(p)) for p in
                    ('MONSTER/monster.bin','MONSTER/m_attack.bin','MONSTER/m_ground.bin')]
        super().__init__(rom)
        self.u.mem_map(0x02400000,0x100000)
        self.manager=0x02200000
        self.u.mem_write(0x020AFC68,struct.pack('<I',self.manager))
        self.u.mem_write(self.manager+0x1508,struct.pack('<HH',96,1))
        ov=rom.loadArm9Overlays()[36];self.u.mem_write(ov.ramAddress,bytes(ov.data))

    def ret(self,value=0):
        self.u.reg_write(UC_ARM_REG_R0,value&0xffffffff)
        self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))

    def service(self,u,address,size,data):
        a,b,c=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
        if address==0x02001170:
            if a>102256 or sum(self.live.values())+a>408324:self.ret(0);return
            pointer=0x02401000
            for start,length in sorted(self.live.items()):
                if pointer+a<=start:break
                pointer=max(pointer,(start+length+31)&~31)
            self.live[pointer]=a;self.peak=max(self.peak,sum(self.live.values()))
            self.ret(pointer);return
        if address==0x02001188:
            assert a in self.live,hex(a)
            del self.live[a];self.ret();return
        if address==0x0200C33C:self.ret(len(self.packs[a][b]));return
        if address==0x0200C35C:
            blob=bytes(self.packs[a][b]);assert self.live.get(c,0)>=len(blob)
            u.mem_write(c,blob);self.ret();return
        return super().service(u,address,size,data)

    def invoke(self,address,*args):
        stack=0x023FE000;end=0x023FF000;self.u.mem_write(stack,bytes(64))
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):
            self.u.reg_write(register,value)
        for i,value in enumerate(args[4:]):self.u.mem_write(stack+i*4,struct.pack('<I',value))
        self.u.reg_write(UC_ARM_REG_SP,stack);self.u.reg_write(UC_ARM_REG_LR,end)
        self.u.emu_start(address,end,count=10000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==end
        assert self.u.reg_read(UC_ARM_REG_SP)==stack
        return self.u.reg_read(UC_ARM_REG_R0)


def audit_packages():
    module=REPO/'true_patches/mega_evolve'
    data=json.loads((module/'data/phase5_aura_pose.json').read_text('utf-8'))
    inventory=json.loads((module/'data/phase5_assets.json').read_text('utf-8'))
    def signature(node):
        return (node.tag,(node.text or '').strip(),node.attrib,
                [signature(n) for n in node if n.tag not in ('FrameWidth','FrameHeight')])
    for package in data['packages']:
        job=package['job'];asset=package['asset'];output=REPO/asset['path']
        assert inventory['assets'][job['index']]==asset
        source=ET.parse(REPO/job['source']/'AnimData.xml').getroot()
        result=ET.parse(output/'AnimData.xml').getroot()
        assert signature(source)==signature(result),'Animation IDs/timing/aliases changed'
        report=json.loads((output/'aura-report.json').read_text('utf-8'))
        assert report['aura_pipeline']==2
        assert report['unique_source_poses']==report['unique_aura_poses']
        assert report['source_unchanged']
        for row in report['animations'].values():
            assert row['clipping_pixels']==0 and row['original_foreground_pixels_preserved']
    assert len(data['packages'])==584
    assert not any(a['policy']=='official_sprite' for a in inventory['assets'])
    print('PASS all584 aura packages: canonical poses, source preservation and XML timing/aliases')


def main():
    audit_packages()
    rom=NintendoDSRom((REPO/'PatchTesting/Export Rom/Explorers of Alpha+.nds').read_bytes())
    world=AuraWorld(rom);slots=[]
    rows=json.loads((REPO/'true_patches/mega_evolve/data/phase5_conversion.json').read_text('utf-8'))['assets']
    assert all(len(pack)==1405 for pack in world.packs),'No per-action pack entries allowed'
    for asset in (140,250,470):
        for pack,kind in enumerate(('monster','attack','ground')):
            slot=world.invoke(0x0201D484,world.manager,pack,819+asset,15,1)
            assert 0<slot<96,(asset,kind,slot)
            row=world.manager+slot*56
            size=struct.unpack('<I',world.u.mem_read(row+0x28,4))[0]
            assert size==rows[asset]['raw_sizes'][kind]
            assert world.invoke(0x0201D484,world.manager,pack,819+asset,15,1)==slot
            world.invoke(0x0201D72C,world.manager,slot)
            slots.append(slot)
            print('Native whole-WAN load:',asset,kind,size,flush=True)
    for slot in slots:world.invoke(0x0201D72C,world.manager,slot)
    assert not world.live,'Sprite buffer leak'
    assert world.invoke(0x02001170,331376,0)==0
    print('PASS actual native whole-WAN decoder/manager, sharing and cleanup; peak modeled sprite bytes:',world.peak)
    print('Pack IO/allocator modeled; no DraStic gameplay or FPS claim.')


if __name__=='__main__':main()
