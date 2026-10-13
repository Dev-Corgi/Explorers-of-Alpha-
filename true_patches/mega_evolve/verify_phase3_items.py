"""ARM berry retention and floor Pickup, plus live item/legacy-block guards."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,BUFFER,STACK
from .phase3 import load
from .phase3_items import load as items,build,validate_rom
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1,OV29,word
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):
        self.rolls=[];self.results=[];self.removed=[];self.generated=[];self.added=[]
        self.bag_full=0;self.add_success=1
        super().reset()
    def service(self,u,address,size,data):
        a,b,c,d=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if address==0x022eab20:
            self.rolls.append(a);self.ret(self.results.pop(0) if self.results else self.probability)
        elif address==0x022eb60c:self.removed.append((a,b,c,d));self.ret()
        elif address==0x0200edc0:self.ret(self.bag_full)
        elif address==0x023443b4:
            self.generated.append((b,c,d));u.mem_write(a,struct.pack('<BBHH',1,0,c,b));self.ret()
        elif address==0x0200f874:self.added.append(bytes(u.mem_read(a,6)));self.ret(self.add_success)
        else:super().service(u,address,size,data)
    def item(self,id_,pointer=BUFFER,flags=1):
        self.u.mem_write(pointer,struct.pack('<BBHH',flags,0,1,id_));return pointer

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    catalogue=items();assert catalogue==build()
    assert len(catalogue['berries'])==8
    assert all(r['id'] not in (73,89,93) for r in catalogue['pickup'])
    assert all(r['id'] not in (88,98,99,100,101,102,103,108,113,116,324,339,345,349,361) for r in catalogue['pickup'])
    rom=NintendoDSRom(SOURCE.read_bytes());validate_rom(rom)
    from skytemple_files.data.item_p.handler import ItemPHandler
    changed=NintendoDSRom(SOURCE.read_bytes())
    item_table=ItemPHandler.deserialize(changed.getFileByName('BALANCE/item_p.bin'))
    item_table.item_list[70].category=1
    changed.setFileByName('BALANCE/item_p.bin',ItemPHandler.serialize(item_table))
    try:validate_rom(changed)
    except RuntimeError as error:assert 'item identities changed' in str(error)
    else:raise AssertionError('changed berry classification accepted')
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'items_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'items_test':True})
    legacy=catalogue['legacy_pickup_block']
    assert word(rom.loadArm9Overlays()[29].data,legacy['start'],OV29)>>24==0xea
    ids={r['key']:r['id'] for r in load()['abilities']};w=World(rom,record)
    consumer=ENTITIES[1];user=ENTITIES[0]
    w.profile(1,(ids['수확'],0));w.weather(0)
    for row in catalogue['berries']:
        w.rolls.clear();assert w.call('ME_KeepBerry',consumer,w.item(row['id']))==1
        assert w.rolls==[12]
    w.weather(1);w.rolls.clear();assert w.call('ME_KeepBerry',consumer,w.item(70))==1
    assert w.rolls==[25]
    w.profile(1,(ids['되새김질'],0));w.rolls.clear()
    assert w.call('ME_KeepBerry',consumer,w.item(70))==1 and w.rolls==[20]
    # Both ordinary traits work once each; success short-circuits additional
    # retention rolls. Duplicate slots never multiply their probability.
    w.profile(1,(ids['되새김질'],0),(ids['수확'],0),(ids['수확'],0));w.rolls.clear();w.results=[0,1]
    assert w.call('ME_KeepBerry',consumer,w.item(70))==1 and w.rolls==[20,25]
    w.rolls.clear();w.results=[1]
    assert w.call('ME_KeepBerry',consumer,w.item(70))==1 and w.rolls==[20]
    for id_ in (69,73,88,89,93,99,100,361):
        count=len(w.rolls);assert w.call('ME_KeepBerry',consumer,w.item(id_))==0 and len(w.rolls)==count
    count=len(w.rolls);assert w.call('ME_KeepBerry',consumer,w.item(70,flags=0))==0 and len(w.rolls)==count
    w.suppressed.add(consumer)
    assert w.call('ME_KeepBerry',consumer,w.item(70))==0 and len(w.rolls)==count
    w.suppressed.clear()
    # Real removal-call wrapper uses r8 (consumer) and original stack+8 item,
    # leaves the original user/parameter arguments untouched on normal removal.
    w.item(70,STACK+8);w.probability=1
    w.call('ME_BerryConsumeHook',user,0,0x66,17,registers={UC_ARM_REG_R8:consumer})
    assert not w.removed and w.u.reg_read(UC_ARM_REG_SP)==STACK
    w.probability=0;w.item(70,STACK+8)
    w.call('ME_BerryConsumeHook',user,0,0x66,17,registers={UC_ARM_REG_R8:consumer})
    assert w.removed==[(user,0,0x66,17)] and w.u.reg_read(UC_ARM_REG_SP)==STACK
    w.item(73,STACK+8);w.probability=1
    w.call('ME_BerryConsumeHook',user,0,0x66,17,registers={UC_ARM_REG_R8:consumer})
    assert len(w.removed)==2
    # Every candidate index creates exactly its audited seed/berry in the bag.
    w.reset();w.profile(0,(ids['픽업'],0));w.probability=1
    for index,row in enumerate(catalogue['pickup']):
        w.choice=index;assert w.call('ME_PickupItem',user)==1
        assert w.generated[-1]==(row['id'],1,0)
        assert struct.unpack('<BBHH',w.added[-1])==(1,0,1,row['id'])
    count=len(w.generated);w.bag_full=1;rolls=len(w.rolls)
    assert w.call('ME_PickupItem',user)==0 and len(w.generated)==count and len(w.rolls)==rolls
    w.bag_full=0;w.probability=0
    assert w.call('ME_PickupItem',user)==0 and w.rolls[-1]==50 and len(w.generated)==count
    w.probability=1;w.u.mem_write(MONSTERS[0]+6,b'\x01');rolls=len(w.rolls)
    assert w.call('ME_PickupItem',user)==0 and len(w.rolls)==rolls
    w.u.mem_write(MONSTERS[0]+6,b'\0');w.suppressed.add(user)
    assert w.call('ME_PickupItem',user)==0 and len(w.rolls)==rolls
    w.suppressed.clear();w.choice=0
    # Entry service is once per floor, even after a native restore or copied
    # ability. A fresh floor can perform one more attempt.
    count=len(w.generated);w.call('ME_FloorEntry',user);w.call('ME_FloorEntry',user)
    w.call('ME_RestoreAbilities',user);w.call('ME_FloorEntry',user)
    assert len(w.generated)==count+1
    w.u.mem_write(0x02100749,b'\x02');w.profile(0,(ids['픽업'],0));w.call('ME_FloorEntry',user)
    assert len(w.generated)==count+2
    # A changed old Pickup block must fail before producing applied ROM files.
    broken=NintendoDSRom(SOURCE.read_bytes());table=broken.loadArm9Overlays()[29];raw=bytearray(table.data)
    raw[legacy['start']-OV29+8]^=1;broken.files[table.fileID]=bytes(raw)
    try:apply_phase1(broken,MODULE,manifest,None,{})
    except RuntimeError as error:assert 'legacy Pickup block' in str(error)
    else:raise AssertionError('unguarded old Pickup body accepted')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 items ARM: eight berry identities, Harvest 12/25%, Cud Chew 20%,')
    print('  stacking/duplicates/suppression, real removal-call ABI; audited Pickup pool, exclusions,')
    print('  bag capacity/team/floor-once and legacy-body guard. Other consumption paths remain under audit.')
    print('No ROM/save/item assets written.')

if __name__=='__main__':main()
