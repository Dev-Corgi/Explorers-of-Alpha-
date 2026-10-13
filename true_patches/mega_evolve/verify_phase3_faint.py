"""Deferred one-slot faint copying through the real ARM action ledger."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS
from .phase3 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'faint_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'faint_test':True})
    ids={r['key']:r['id'] for r in load()['abilities']};w=World(rom,record)
    receiver=ids['화학의힘'];holder=ENTITIES[0]
    def reset():
        w.reset()
        for i in range(20):w.profile(i,(0,0))
        w.profile(0,(ids['클리어바디'],0),(receiver,0),(ids['단순'],1))
        for i in range(3):w.u.mem_write(ENTITIES[i]+0x25,b'\x01')
        w.position(0,10,10);w.position(1,15,10);w.position(2,11,10)
        w.profile(1,(ids['부유'],0));w.profile(2,(ids['내열'],1))
    def faint(i):
        w.u.mem_write(MONSTERS[i]+0x10,struct.pack('<H',0))
        w.call('ME_FaintEvent',ENTITIES[i],20,ENTITIES[3])
    reset();original=[w.ability(0,j) for j in range(3)]
    token=w.call('ME_BeginAction',ENTITIES[3],20)
    faint(1);faint(2)
    assert [w.ability(0,j) for j in range(3)]==original # Selection waits for all targets.
    w.call('ME_EndAction',token)
    assert [w.ability(0,j) for j in range(3)]==[original[0],ids['내열']|65536,original[2]]
    w.call('ME_RestoreAbilities',holder)
    assert [w.ability(0,j) for j in range(3)]==original
    # Reverse callback order cannot change nearest selection. Ties use team slot.
    reset();token=w.call('ME_BeginAction',ENTITIES[3],20);faint(2);faint(1);w.call('ME_EndAction',token)
    assert w.ability(0,1)==ids['내열']|65536
    reset();w.position(1,11,11);token=w.call('ME_BeginAction',ENTITIES[3],20)
    faint(2);faint(1);w.call('ME_EndAction',token)
    assert w.ability(0,1)==ids['부유']
    # Different room, opponents, suppressed owner and protected-only source.
    for mode in ('room','opponent','suppressed','protected','receiver'):
        reset()
        if mode=='room':w.u.mem_write(ENTITIES[1]+0x25,b'\x02')
        if mode=='opponent':w.u.mem_write(MONSTERS[1]+6,b'\x01')
        if mode=='suppressed':w.suppressed.add(holder)
        if mode=='protected':w.profile(1,(ids['Omniscience'],0),(206,0))
        if mode=='receiver':w.profile(1,(receiver,0))
        token=w.call('ME_BeginAction',ENTITIES[3],20);faint(1);w.call('ME_EndAction',token)
        assert w.ability(0,1)==receiver
    # A protected slot does not discard another copyable slot of the source.
    reset();w.profile(1,(ids['Omniscience'],0),(ids['부유'],0),(ids['부유'],1))
    token=w.call('ME_BeginAction',ENTITIES[3],20);faint(1);w.call('ME_EndAction',token)
    assert w.ability(0,1)==ids['부유']|65536
    # Nested action snapshots cannot overwrite a pending parent selection.
    reset();token=w.call('ME_BeginAction',ENTITIES[3],20);faint(1)
    nested=w.call('ME_BeginAction',ENTITIES[4],21);faint(2);w.call('ME_EndAction',nested)
    assert w.ability(0,1)==ids['내열']|65536
    w.call('ME_RestoreAbilities',holder);w.call('ME_EndAction',token)
    assert w.ability(0,1)==ids['부유']
    # Reset/reused monster and holder death cancel pending inheritance.
    reset();token=w.call('ME_BeginAction',ENTITIES[3],20);faint(1)
    w.call('ME_ResetMonster',MONSTERS[0]);w.profile(0,(receiver,0));w.call('ME_EndAction',token)
    assert w.ability(0,0)==receiver
    reset();token=w.call('ME_BeginAction',ENTITIES[3],20);faint(1)
    w.u.mem_write(MONSTERS[0]+0x10,struct.pack('<H',0));w.call('ME_EndAction',token)
    assert w.ability(0,1)==receiver
    # Environmental faint gets its own temporary action bracket and flushes.
    reset();w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',0))
    w.call('ME_FaintBoundary',ENTITIES[1],563,0)
    assert w.ability(0,1)==ids['부유']
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 faint ARM: nearest/tie-slot/order-independent pending copy, grade/unique candidates,')
    print('  room/team/suppression/protected source, one temporary slot/restoration, nested actions,')
    print('  reset/death cancellation and environmental faint brackets. No ROM/save output.')

if __name__=='__main__':main()
