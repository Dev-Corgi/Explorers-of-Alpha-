"""ARM reward tests with native MD, item metadata and leader lookup services."""
import itertools
import struct
from collections import Counter

from unicorn.arm_const import UC_ARM_REG_R7,UC_ARM_REG_LR,UC_ARM_REG_SP
from skytemple_files.common.types.file_types import FileType
from skytemple_files.dungeon_data.fixed_bin.model import EntityRule,TileRule


def check_rewards(m,rom,info):
    d=0x02100000;entity=0x02250000;mon=0x02260000
    buffer=0x02280100;stack=0x023fe000;ret=0x023ff000
    expected=[[115,115,99,99],[73]*2,[103]*4,[93],[77]*8,[136],[0],[89]*7]
    fixed=FileType.FIXED_BIN.deserialize(rom.getFileByName('BALANCE/fixed.bin'))
    # All other fixed rooms, including inherited key rooms, remain byte-identical.
    from ndspy.rom import NintendoDSRom
    from .verify_trial_tower import ROOT
    original=NintendoDSRom.fromFile(str(ROOT/'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'))
    old=FileType.FIXED_BIN.deserialize(original.getFileByName('BALANCE/fixed.bin'))
    for n in range(256):
        if not 230<=n<=239:assert fixed.fixed_floors[n].to_bytes()==old.fixed_floors[n].to_bytes()
    generated=[]
    def generate():
        sp=m.u.reg_read(UC_ARM_REG_SP)
        generated.append(([m.reg(i) for i in range(4)],bytes(m.u.mem_read(sp,8))))
        return 1
    m.stubs[0x02344430]=generate
    for room,rewards in enumerate(expected):
        m.u.mem_write(d+0x748,bytes([234,45]));m.u.mem_write(d+0x40da,bytes([249]))
        m.stubs[0x022eaa98]=lambda:room
        assert m.run('ME_TowerChooseKey')==249
        layout=fixed.fixed_floors[256+room]
        assert layout.width==layout.height==7
        assert sum(isinstance(a,TileRule) and a.tr_type.value==12 for a in layout.actions)==1
        rows=[a for a in layout.actions if isinstance(a,EntityRule)]
        assert len(rows)==len(rewards)
        actual=[]
        for a in rows:
            item=115 if a.entity_rule_id==198 else 136
            m.u.mem_write(stack,struct.pack('<II',1,1))
            m.run('ME_TowerItemHook',item,4,5,0)
            args,flags=generated[-1]
            assert args[1:]==[4,5,0] and flags==bytes(8)
            actual.append(0 if room==6 else args[0])
        assert actual==rewards
    # Shared fixed rooms, ordinary dungeon IDs and their duplicate-item rule.
    for dungeon,room in [(102,231),(234,170),(234,230),(234,239)]:
        m.u.mem_write(d+0x748,bytes([dungeon,45]));m.u.mem_write(d+0x40da,bytes([room]))
        m.u.mem_write(stack,struct.pack('<II',1,1));m.run('ME_TowerItemHook',136,4,5,0)
        assert generated[-1]==([136,4,5,0],struct.pack('<II',1,1))
    m.stubs.pop(0x02344430)

    # Run the native file loader's SIR0 relocation and its real patched epilogue.
    # All native consumers subsequently index the same rebound pointer table.
    from patch_engine.mega_evolve_runtime import branch
    raw=0x020c0000;context=0x02270000
    fixed_blob=bytearray(rom.getFileByName('UTILITY/fixed.bin'))
    for i in range(8):struct.pack_into('<I',fixed_blob,32+i*12,100+i)
    fixed_blob=bytes(fixed_blob)
    assert len(fixed_blob)<0x40000
    m.write32(0x02353794,context)
    def file_load():
        m.u.mem_write(raw,fixed_blob);m.write32(context,raw);m.write32(context+8,0)
        return 0
    m.stubs[0x02008c3c]=file_load
    m.stubs[0x02343dd8]=lambda:0
    m.write32(0x02343db8,branch(0x02343db8,m.symbols['ME_TowerFixedLoadedHook']))
    for value in range(8):
        m.u.mem_write(d+0x748,bytes([234,45]));m.u.mem_write(d+0x40da,bytes([249]))
        m.stubs[0x022eaa98]=lambda:value;m.run('ME_TowerChooseKey')
        m.run(0x02343d90)
        table=struct.unpack('<I',m.u.mem_read(context+8,4))[0]
        at=lambda n:struct.unpack('<I',m.u.mem_read(table+n*4,4))[0]
        assert at(249)==at(256+value)
        assert m.read16(at(249))==m.read16(at(249)+2)==7
        props=fixed_blob[32+value*12:44+value*12]
        assert bytes(m.u.mem_read(0x022c6c70+249*12,12))==props
        assert m.run(0x0233c310,249)==1 and m.run(0x023361d4)==0
        # Preload scans the physical selected layout using the original decoder.
        m.stubs[0x02001170]=lambda:buffer+0x1000
        m.stubs[0x02001188]=lambda:0
        m.run(0x02343e20,buffer+0x800,0,249,0)
        decoded=struct.unpack('<49H',m.u.mem_read(buffer+0x1000,98))
        assert sum(16<=(action&0xfff)<512 for action in decoded)==len(expected[value])
    for address in [0x02008c3c,0x02001170,0x02001188,0x02343dd8]:m.stubs.pop(address)
    print('PASS native fixed.bin file loading, SIR0 relocation, extended pointer binding, properties, partial-room flags and original preload/decoder for all8 new IDs',flush=True)

    # Execute native item-SP accessors against actual ROM tables, avoiding mocks
    # that could silently confuse a species ID with a dex ID or star rarity.
    md_raw=bytes(rom.getFileByName('BALANCE/monster.md'))
    md=FileType.MD.deserialize(md_raw)
    sp=FileType.ITEM_SP.deserialize(rom.getFileByName('BALANCE/item_s_p.bin'))
    item_p=rom.getFileByName('BALANCE/item_p.bin')
    valid=lambda item:bool(item_p[16+item*16+14]&1)
    m.u.mem_write(0x02080000,bytes(rom.getFileByName('BALANCE/item_s_p.bin')[16:16+956*4]))
    m.u.mem_write(0x02081000,bytes(rom.getFileByName('BALANCE/item_p.bin')[16:16+1400*16]))
    m.u.mem_write(0x02090000,md_raw);m.write32(0x020b09b4,0x02090008)
    table=struct.unpack_from('<I',rom.arm9,0xe778)[0]
    m.write32(table,0x02080000);m.write32(table+4,0x02081000)
    overlay=rom.loadArm9Overlays()[29]
    leader_cache=struct.unpack_from('<I',overlay.data,0x022e95ec-overlay.ramAddress)[0]
    m.write32(leader_cache,0)
    for i in range(4):m.write32(d+0x12b28+i*4,0)
    m.write32(entity,1);m.write32(entity+0xb4,mon);m.write32(d+0x12b28,entity)
    m.u.mem_write(mon,bytes(0x200));m.u.mem_write(mon+7,b'\1')
    bag=set();m.stubs[0x0200eee0]=lambda:int(m.reg(0) in bag)
    rng=m.stubs[0x022eaa98]
    calls=[]
    def choose_last():calls.append(m.reg(0));return 0
    m.stubs[0x022eaa98]=choose_last
    def leader(species):
        m.u.mem_write(mon+2,struct.pack('<H',species))
        e=md.entries[species]
        m.u.mem_write(mon+0x5e,bytes([int(e.type_primary),int(e.type_secondary)]))
    def family_items(species):
        root=md.entries[species].base_form_index
        return [444+i for i,r in enumerate(sp.item_list) if valid(444+i) and r.type.value in (8,9,10)
                and md.entries[r.parameter].base_form_index==root]
    def type_items(species):
        e=md.entries[species];types={int(e.type_primary),int(e.type_secondary)}
        return [444+i for i,r in enumerate(sp.item_list) if valid(444+i) and r.type.value==4 and r.parameter in types]
    # Branch families, hatch rewards, female rows and cyclic alternate forms.
    for species in [3,25,26,133,134,135,136,196,197,172,263,264,276,418,419,529,536,601,625,733]:
        leader(species);bag.clear();calls.clear()
        candidates=family_items(species)
        actual=m.run('ME_TowerExclusive')
        assert actual==candidates[-1],(species,actual,candidates)
        assert calls==list(range(1,len(candidates)+1)),(species,candidates,calls)
        for missing in candidates:
            bag.clear();bag.update(set(candidates)-{missing})
            assert m.run('ME_TowerExclusive')==missing
        bag.clear();bag.update(candidates)
        types=type_items(species)
        assert m.run('ME_TowerExclusive')==(types[-1] if types else 136)
        for missing in types:
            bag.clear();bag.update(candidates);bag.update(set(types)-{missing})
            assert m.run('ME_TowerExclusive')==missing
        bag.update(types);assert m.run('ME_TowerExclusive')==136
    # Actual equipped item on a second team member excludes that candidate too.
    leader(3);candidates=family_items(3);bag.clear();bag.update(candidates[:-1])
    teammate=entity+0x800;tm=mon+0x2000
    m.write32(teammate,1);m.write32(teammate+0xb4,tm);m.write32(d+0x12b2c,teammate)
    m.u.mem_write(tm,bytes(0x200));m.u.mem_write(tm+0x62,b'\1');m.u.mem_write(tm+0x66,struct.pack('<H',candidates[-1]))
    assert m.run('ME_TowerExclusive') in type_items(3)
    m.u.mem_write(tm+0x62,b'\0');assert m.run('ME_TowerExclusive')==candidates[-1]
    # Exhaust every RNG outcome for a small real family: equal reservoir mass.
    leader(3);bag.clear();candidates=family_items(3);outcomes=Counter()
    for choices in itertools.product(*[range(i+1) for i in range(len(candidates))]):
        stream=iter(choices);m.stubs[0x022eaa98]=lambda:next(stream)
        outcomes[m.run('ME_TowerExclusive')]+=1
    assert set(outcomes)==set(candidates) and len(set(outcomes.values()))==1
    m.stubs[0x022eaa98]=choose_last

    # The exclusive item is deferred until native SpawnTeam has established
    # the current leader. Then mutate just that ground item's saved item struct.
    m.u.mem_write(d+0x748,bytes([234,45]));m.u.mem_write(d+0x40da,bytes([249]))
    m.u.mem_write(buffer,struct.pack('<II',1,1))
    m.stubs[0x022eaa98]=lambda:6
    m.run('ME_TowerChooseKey')
    m.stubs[0x022eaa98]=choose_last
    assert m.run('ME_TowerItem',136,4,5,buffer)==136
    tile=buffer+0x100;item_entity=buffer+0x200;item_info=buffer+0x300
    m.write32(tile+0x10,item_entity);m.write32(item_entity,3);m.write32(item_entity+0xb4,item_info)
    m.u.mem_write(item_info,struct.pack('<BBHH',1,0,0,136))
    m.stubs[0x023360fc]=lambda:tile if [m.reg(0),m.reg(1)]==[4,5] else 0
    m.write32(leader_cache,0);m.write32(d+0x12b28,0)
    def spawn_team():m.write32(d+0x12b28,entity);return 17
    m.stubs[0x022fc50c]=spawn_team
    assert m.run('ME_TowerTeamHook',0)==17
    assert m.read16(item_info+4)==candidates[-1]
    m.u.mem_write(item_info+4,struct.pack('<H',136));m.run('ME_TowerResolveReward')
    assert m.read16(item_info+4)==136  # consumed once
    for address in [0x022fc50c,0x023360fc,0x0200eee0]:m.stubs.pop(address)

    # Selector returns a native bridge ID, while the saved logical ID is16-bit.
    # Original twelve-way selection resumes for every other dungeon.
    def finish():m.u.reg_write(UC_ARM_REG_LR,ret);return 0
    m.stubs[0x023dbbf8]=finish
    m.u.reg_write(UC_ARM_REG_R7,buffer)
    logical=[]
    for value in range(8):
        def draw(v=value):assert m.reg(0)==8;return v
        m.stubs[0x022eaa98]=draw
        m.run('ME_TowerSelectHook')
        assert m.u.mem_read(buffer+0x12,1)==bytes([249])
        m.run('ME_TowerFixedLoaded')
        m.run('ME_TowerSave',buffer+0x400)
        saved=bytes(m.u.mem_read(buffer+0x400,27))
        logical.append(saved[13]|saved[14]<<8)
        assert saved[15:27]==fixed_blob[32+value*12:44+value*12]
        m.run('ME_TowerReset');m.u.mem_write(0x022c6c70+249*12,bytes(12))
        assert m.run('ME_TowerLoad',buffer+0x400)==1
        assert bytes(m.u.mem_read(0x022c6c70+249*12,12))==saved[15:27]
        m.run('ME_TowerSave',buffer+0x500)
        assert bytes(m.u.mem_read(buffer+0x500,27))==saved
        m.run('ME_TestResume',buffer+0x400)
        m.run('ME_TowerSave',buffer+0x500)
        assert bytes(m.u.mem_read(buffer+0x500,27))==saved
    assert logical==list(range(256,264))
    invalid=bytearray(saved);invalid[13:15]=struct.pack('<H',264)
    m.u.mem_write(buffer+0x400,bytes(invalid));assert m.run('ME_TowerLoad',buffer+0x400)==0
    m.run('ME_TowerFloorReset');m.run('ME_TowerSave',buffer+0x400)
    assert bytes(m.u.mem_read(buffer+0x40d,14))==bytes(14)
    m.u.mem_write(d+0x748,b'\x66');seen=[]
    def native_choice():seen.append(m.reg(0));return finish()
    m.stubs[0x023dbbd8]=native_choice;m.run('ME_TowerSelectHook');assert seen==[12]
    m.stubs.pop(0x023dbbd8);m.stubs.pop(0x023dbbf8);m.stubs[0x022eaa98]=rng
    print('PASS eight physical extended rooms256-263, exact rewards, native metadata/leader, family/type/held-item fallbacks, uniform selection, post-team resolution and16-bit save/load',flush=True)
