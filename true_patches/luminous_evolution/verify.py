"""Assemble temporary fixtures, execute ARM code, and round-trip EN/KO scripts.

No .nds or state file is written; this is not a full-stack build.
"""
from __future__ import annotations

import gzip
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.md.handler import MdHandler
from skytemple_files.data.md_evo.handler import MdEvoHandler
from skytemple_files.script.ssb.handler import SsbHandler
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)
from patch_engine.apply_luminous_evolution import (
    apply_luminous_evolution_module, verify_luminous_evolution_module, _word,
)
from patch_engine.state import BuildState
from patch_engine.apply_korean import load_source, plan_translation, _write_strings
from patch_engine.korean_codec import translation_issues, parse_ssb_strings, DenseEncoder
from true_patches.luminous_evolution.policy import relationship_tables
import yaml

MODULE = Path(__file__).resolve().parent
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12]
ROSTER, MD, STATE, OUT, INDEX = 0x02200000, 0x02220000, 0x02250000, 0x02251000, 0x02252000
RETURN, STACK, NAME = 0x021FF000, 0x027E3000, 0x02253000


class Machine:
    def __init__(self, rom, symbols):
        self.u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.u.mem_map(0x02000000, 0x400000)
        self.u.mem_map(0x027E0000, 0x4000)
        self.u.mem_write(0x02000000, bytes(rom.arm9))
        ov = loadOverlayTable(rom.arm9OverlayTable, lambda i, f: rom.files[f])[16]
        self.u.mem_write(ov.ramAddress, bytes(ov.data))
        self.symbols = symbols
        self.flags = {5: 1, 10: 0}
        self.calls = []
        self.menus = []
        self.messages = []
        self.string_requests = []
        self.evolution_count = 0
        self.spawned = []
        self.stops = {RETURN: self.stop}
        self.stubs = {}
        self.write32(_word(rom.arm9, 0x020555CC, 0x02000000), ROSTER)
        self.write32(_word(rom.arm9, 0x02052ADC, 0x02000000), MD)
        self.write32(0x0238CE40, STATE)
        self.u.mem_write(MD, bytes(rom.getFileByName("BALANCE/monster.md"))[8:])
        self.evos = MdEvoHandler.deserialize(rom.getFileByName("UTILITY/md_evo.bin")).evo_entries
        self.stub(0x02059F24, self.evolutions)
        self.stub(0x0204CA94, lambda: self.flags.get(self.reg(0), 0))
        self.stub(0x0204CB2C, self.set_flag)
        self.stub(0x0204AFC0, lambda: 1)
        self.stub(0x0200D278, lambda: -1)  # no item, including no Ascend Stones
        self.stub(0x0204FDFC, lambda: 0)
        self.stub(0x0204FCDC, self.count_evolution)
        self.stub(0x02055CCC, self.spawn)
        self.stub(0x020526C8, lambda: NAME)
        self.u.mem_write(NAME, b"Shedinja\0")
        self.stub(0x0202B0EC, self.menu)
        self.stub(0x0202F1B4, self.message)
        self.stub(0x020258C4, self.string)
        for a in [0x0238CAE8, 0x0203A51C, 0x0203C874]:
            self.stub(a, lambda: 0)
        self.stub(0x0238A140, self.set_state)
        self.u.hook_add(UC_HOOK_CODE, self.hook)

    def write32(self, address, value):
        self.u.mem_write(address, struct.pack("<I", value))

    def read16(self, address):
        return struct.unpack("<H", self.u.mem_read(address, 2))[0]

    def reg(self, index):
        return self.u.reg_read(REGS[index])

    def stub(self, address, fn):
        self.stubs[address] = fn

    def stop(self):
        self.u.emu_stop()

    def hook(self, _, address, size, __):
        if address in self.stops:
            self.stops[address]()
        elif address in self.stubs:
            result = self.stubs[address]()
            self.u.reg_write(UC_ARM_REG_R0, (result or 0) & 0xFFFFFFFF)
            self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def run(self, address, *args):
        if isinstance(address, str):
            address = self.symbols[address]
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, RETURN)
        for i, value in enumerate(args):
            self.u.reg_write(REGS[i], value)
        try:
            self.u.emu_start(address, RETURN, count=300000)
        except Exception as error:
            raise AssertionError(f"ARM failed at PC={self.u.reg_read(UC_ARM_REG_PC):#x}, "
                                 f"LR={self.u.reg_read(UC_ARM_REG_LR):#x}, "
                                 f"SP={self.u.reg_read(UC_ARM_REG_SP):#x} from {address:#x}") from error
        if self.u.reg_read(UC_ARM_REG_PC) != RETURN:
            raise AssertionError(f"ARM execution did not return from {address:#x}")
        assert self.u.reg_read(UC_ARM_REG_SP) == STACK
        return self.reg(0)

    def evolutions(self):
        ids = list(self.evos[self.reg(1)].evos)
        self.u.mem_write(self.reg(0), struct.pack("<8H", *(ids + [0] * (8-len(ids)))))
        return len(ids)

    def set_flag(self):
        self.flags[self.reg(0)] = self.reg(1)

    def set_state(self):
        self.calls.append(self.reg(0))
        self.write32(STATE+0x70, self.reg(0))

    def menu(self):
        count = struct.unpack("<I", self.u.mem_read(self.u.reg_read(UC_ARM_REG_SP), 4))[0]
        pairs = [struct.unpack("<II", self.u.mem_read(self.reg(3)+i*8, 8)) for i in range(count+1)]
        assert pairs[-1] == (0, 1)
        self.menus.append(pairs[:-1])
        return 4

    def message(self):
        self.messages.append(self.reg(2))

    def string(self):
        self.string_requests.append(self.reg(0))
        return NAME

    def count_evolution(self):
        self.evolution_count += 1

    def spawn(self):
        self.spawned.append(bytes(self.u.mem_read(self.reg(0), 0x44)))
        self.u.mem_write(ROSTER+5*0x44, self.spawned[-1])
        return 5

    def record(self, index, species, level=50, joined=0xD6):
        data = bytearray((i*7+3)%256 for i in range(0x44))
        data[0]=1; data[1]=level; data[2]=joined
        struct.pack_into("<H", data, 4, species)
        data[6:8]=b"\0\0"
        struct.pack_into("<I", data, 0x10, 0x123456)
        data[0x3A:0x44]=b"MyBuddy\0\0\0"
        self.u.mem_write(ROSTER+index*0x44, bytes(data))
        return bytes(data)

    def select(self, index):
        self.u.mem_write(STATE, bytes(0x150))
        self.write32(STATE+0x3C, ROSTER+index*0x44)
        self.u.mem_write(STATE+0x44, struct.pack("<h", index))
        self.u.mem_write(INDEX, struct.pack("<h", index))


def check_scripts(before, after):
    config=get_ppmdu_config_for_rom(after)
    texts=json.loads((MODULE/"data/texts.json").read_text(encoding="utf-8"))
    paths=set(texts["scripts"])|{"SCRIPT/COMMON/unionall.ssb","SCRIPT/D01P11A/us2306.ssb"}
    for path in paths:
        old=SsbHandler.deserialize(before.getFileByName(path), static_data=config)
        new=SsbHandler.deserialize(after.getFileByName(path), static_data=config)
        offsets={o.offset for ops in new.routine_ops for o in ops}
        for ops in new.routine_ops:
            for op in ops:
                for arg in op.op_code.arguments:
                    if arg.name=="jump_address":
                        assert op.params[arg.id] in offsets, (path,op.offset)
        assert SsbHandler.serialize(new,static_data=config)==after.getFileByName(path)
        def progress(s):
            return [(o.op_code.name,o.params) for ops in s.routine_ops for o in ops
                    if o.op_code.name.startswith("flag_")]
        assert progress(old)==progress(new), path
        if path.endswith("s01p1005.ssb"):
            prefix=[(o.op_code.name,o.params) for o in old.routine_ops[0] if o.offset<0x1A4]
            assert prefix==[(o.op_code.name,o.params) for o in new.routine_ops[0]][:len(prefix)]
            operations=[o for ops in new.routine_ops for o in ops]
            menus=[i for i,o in enumerate(operations) if o.op_code.name=="message_Menu" and o.params==[21]]
            warning=[i for i,o in enumerate(operations) if o.op_code.name=="message_Talk" and o.params==[85]]
            assert len(menus)==1 and menus[0]<warning[0]
            assert not any(o.op_code.name=="message_Talk" and o.params==[63] for o in operations)
        if path in ("SCRIPT/COMMON/unionall.ssb","SCRIPT/D01P11A/us2306.ssb"):
            assert not any(o.op_code.name=="item_Set" and o.params[1] in (427,428)
                           for ops in new.routine_ops for o in ops)
    # All newly authored entries must have a safe, exact-match Korean override.
    translation=json.loads(gzip.decompress((ROOT/"true_patches/korean/data/translations.json.gz").read_bytes()))
    for where, es in [("text_e",{str(e["index"]):e for e in texts["text_e"]}),*texts["scripts"].items()]:
        override=translation["text_e"] if where=="text_e" else translation["scripts"][where]
        for key,e in es.items():
            assert override[key]=={"en":e["en"],"ko":e["ko"]}
            assert not translation_issues(e["en"],e["ko"]), (where,key)
    korean=ROOT/"true_patches/korean"
    manifest=yaml.safe_load((korean/"manifest.yaml").read_text(encoding="utf-8"))
    source=load_source(korean,manifest)
    plan=plan_translation(after,source)
    for e in texts["text_e"]:
        assert plan.text_dec[e["index"]].ko==e["ko"]
    for path,entries in texts["scripts"].items():
        for index,e in entries.items():
            assert plan.script_dec[path][int(index)].ko==e["ko"]
    authored=[e["ko"] for e in texts["text_e"]]
    authored.extend(e["ko"] for entries in texts["scripts"].values() for e in entries.values())
    encoder=DenseEncoder(source.ziti)
    for text in authored:
        encoder.collect(text)
    encoder.finalize()
    for text in authored:
        assert b"\0" not in encoder.encode(text)
    assert not encoder.stats.unmapped, encoder.stats.unmapped
    # Exercise the actual Korean string importer, including the newly migrated
    # constant-table mail. This serializes strings in memory, not a ROM build.
    translated=NintendoDSRom(bytes(after.save()))
    encoder=DenseEncoder(source.ziti)
    _write_strings(translated,plan,encoder)
    for path,entries in texts["scripts"].items():
        raw=parse_ssb_strings(translated.getFileByName(path)).strings
        for index,e in entries.items():
            assert raw[int(index)]==encoder.encode(e["ko"])


def check_arm(rom, record):
    m=Machine(rom,record.data[0]["symbols"])
    # Execute the real ARM9 MD condition copier and candidate checker, with only
    # file/bag/UI services supplied by the harness. No stones are in the bag.
    m.record(0,1,16)
    m.run("Spring_Prepare")
    assert m.run(0x0205A210,ROSTER)==1
    m.record(0,1,15)
    assert m.run(0x0205A210,ROSTER)==0
    m.record(0,2,32,0xD7)
    assert m.run(0x0205A210,ROSTER)==1
    for species,level in [(438,15),(439,30),(1038,15),(1039,30)]:
        m.record(0,species,level)
        assert m.run(0x0205A210,ROSTER)==1, (species,level)
        m.record(0,species,level-1)
        assert m.run(0x0205A210,ROSTER)==0, (species,level)
    m.record(0,2,32,0xD7)
    m.flags[5]=0
    assert m.run(0x0205A210,ROSTER)==0
    # First visit enables ordinary evolution, but offers neither regression nor
    # form changing, and only the hero/partner are eligible in the story menu.
    m.run("Spring_Prepare")
    assert m.flags[5]==1 and m.flags[10]==0
    m.record(0,3)
    m.record(1,6,joined=0xD7)
    m.record(5,1,16,joined=0xA0)
    assert m.run("Spring_Count")==0
    m.record(1,4,16,0xD7)
    assert m.run("Spring_Count")==1
    m.select(0); m.run("Spring_Submenu")
    assert [a for _,a in m.menus[-1]]==[3,8,1]
    # Reopening the unlocked Spring exposes regression even to final forms.
    m.run("Spring_Prepare")
    m.select(0);m.run("Spring_Submenu")
    assert [a for _,a in m.menus[-1]]==[3,10,8,1]
    old=m.record(0,3)
    m.select(0)
    assert m.run("Spring_Action",10)==1 and m.calls[-1]==22
    assert m.read16(STATE+0xC)==2
    m.run("Spring_RecordEvolution")
    assert m.evolution_count==0
    m.run("Spring_Convert",INDEX,2)
    changed=bytes(m.u.mem_read(ROSTER,0x44))
    expected=bytearray(old);struct.pack_into("<H",expected,4,2)
    assert changed==bytes(expected)
    assert not m.spawned
    m.run("Spring_Message",1,8,1087,OUT)
    assert m.messages[-1]==19705
    # Normal evolution preserves every byte except species and still follows
    # the original Ninjask branch. A Shedinja is created only for that evolution.
    m.run("Spring_Submenu")
    m.run("Spring_RecordEvolution")
    assert m.evolution_count==1
    m.run("Spring_Convert",INDEX,3)
    now=bytes(m.u.mem_read(ROSTER,0x44))
    assert now[:6]+now[8:]==old[:6]+old[8:]
    assert now[6]==old[1] and now[7]==0
    old=m.record(0,318,20)
    m.select(0);m.run("Spring_Submenu")
    m.run("Spring_Convert",INDEX,319)
    actual=bytearray(m.u.mem_read(ROSTER,0x44));struct.pack_into("<H",actual,4,318)
    assert actual[:6]+actual[8:]==old[:6]+old[8:]
    assert actual[6]==20
    assert len(m.spawned)==1 and struct.unpack_from("<H",m.spawned[0],4)[0]==320
    assert m.spawned[0][1]==20 and m.spawned[0][0xA:0x16]==old[0xA:0x16]
    assert m.spawned[0][6]==20
    # Cyclic Giratina relationships are form changes, never regression/evolution.
    old=m.record(0,529)
    m.select(0);m.run("Spring_Submenu")
    assert [a for _,a in m.menus[-1]]==[3,11,8,1]
    assert m.run("Spring_Action",11)==1
    assert m.read16(STATE+0xC)==536
    m.run("Spring_Convert",INDEX,536)
    expected=bytearray(old);struct.pack_into("<H",expected,4,536)
    assert bytes(m.u.mem_read(ROSTER,0x44))==bytes(expected)
    assert len(m.spawned)==1
    m.run("Spring_Message",1,8,1087,OUT)
    assert m.messages[-1]==19706
    m.run("Spring_TargetLabel",OUT,0)
    assert m.string_requests[-1]==19730  # Origin Forme has its own EN/KO label
    m.run("Spring_RecordEvolution")
    assert m.evolution_count==1
    # The actual native single-target selector must reach the rewritten prompt.
    m.record(0,3);m.select(0);m.run("Spring_Submenu")
    m.run("Spring_Action",10)
    del m.stubs[0x0238A140]
    m.stub(0x0202F0B0,lambda: 3)
    m.stub(0x0202F3A4,lambda: 0)
    m.run(0x0238A140,22)
    assert m.messages[-1]==19703
    m.stub(0x0238A140,m.set_state)
    # Native No/cancel dispatch goes back to member selection, not conversion.
    cancelled_record=bytes(m.u.mem_read(ROSTER,0x44))
    m.write32(STATE+0x70,19);m.write32(STATE+0xD8,1)
    m.write32(STATE+0x74,23);m.write32(STATE+0x78,6)
    m.u.mem_write(STATE+0xC2,b"\xFE")
    for address in (0x0202B4F0,0x0202F2C4,0x0203C9E4):
        m.stub(address,lambda: 0)
    m.stub(0x0202B57C,lambda: 7)
    m.run(0x0238C1F8)
    assert struct.unpack("<I",m.u.mem_read(STATE+0x70,4))[0]==28
    assert struct.unpack("<I",m.u.mem_read(STATE+0x74,4))[0]==6
    assert bytes(m.u.mem_read(ROSTER,0x44))==cancelled_record
    m.record(0,418);m.select(0);m.run("Spring_Submenu")
    assert m.run("Spring_Action",11)==1
    assert [m.read16(STATE+0xC+2*i) for i in range(3)]==[419,420,421]
    del m.stubs[0x0238A140]
    m.run(0x0238A140,22)
    assert m.messages[-1]==19707  # selection question, not uninitialized target
    m.stub(0x0202BA20,lambda: 4)
    m.run(0x0238A140,39)
    for i,expected_label in enumerate([19716,19717,19718]):
        m.run("Spring_TargetLabel",OUT,i)
        assert m.string_requests[-1]==expected_label
    m.stub(0x0238A140,m.set_state)
    m.record(0,1);m.select(0);m.run("Spring_Submenu")
    assert [a for _,a in m.menus[-1]]==[3,8,1]
    for species,parent in [(320,318),(920,918),(461,459),(451,1048),(1051,1048)]:
        m.record(0,species);m.select(0);m.run("Spring_Submenu")
        assert 10 in [a for _,a in m.menus[-1]], species
        m.run("Spring_Action",10)
        assert m.read16(STATE+0xC)==parent, (species,parent)
    m.record(0,1047);m.select(0);m.run("Spring_Submenu")
    m.run("Spring_Action",11)
    assert [m.read16(STATE+0xC+2*i) for i in range(2)]==[1048,1049]
    m.record(0,1129);m.select(0);m.run("Spring_Submenu")
    m.run("Spring_Action",11)
    assert [m.read16(STATE+0xC+2*i) for i in range(2)]==[536,0]
    # Repeated regression/evolution cannot farm permanent boosts or XP.
    original=m.record(0,3)
    for _ in range(12):
        m.select(0);m.run("Spring_Submenu");m.run("Spring_Action",10)
        m.run("Spring_Convert",INDEX,2)
        m.run("Spring_Submenu");m.run("Spring_Convert",INDEX,3)
        now=bytes(m.u.mem_read(ROSTER,0x44))
        assert now[:6]+now[8:]==original[:6]+original[8:]
        assert now[6]==original[1] and now[7]==0


def main():
    source=(ROOT/"PatchTesting/Export Rom/Explorers of Alpha+.nds" if "--integration" in sys.argv
            else ROOT/"PatchTesting/Explorers of Alpha/Explorers of Alpha.nds")
    before=NintendoDSRom.fromFile(str(source))
    after=NintendoDSRom(bytes(before.save()))
    record=apply_luminous_evolution_module("luminous_evolution",MODULE,{"version":1},after,
                                          ROOT/"tools/armips.exe",BuildState("us_vanilla",0x022DC240))
    verify_luminous_evolution_module(after,MODULE,{"version":1},record)
    check_scripts(before,after)
    check_arm(after,record)
    print("OK: ARM evolution gates, final-form access, conditional menus, record/XP/doping preservation,")
    print("    Shedinja only on normal evolution, form cycles, repeated changes, SSB relocation and EN/KO exact matches.")
    print("No ROM or full-stack build was written.")


if __name__=="__main__":
    main()
