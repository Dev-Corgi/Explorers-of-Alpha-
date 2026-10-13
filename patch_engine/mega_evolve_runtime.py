"""Allocate/link mega_evolve phase-1 runtime and guard every patched instruction."""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

from .cave_reservations import reserved_file_ranges
from .cave_allocator import find_zero_run
from .cave_xref import scan_overlay_xrefs
from .hook_registry import branch_target
from .ov36_layout import allocate_ov36_cave, write_ov36_to_rom, ov36_forbidden_ranges
from .state import AppliedModule, CaveAllocation, HookRecord
from .korean_codec import parse_str_file, build_str_file, decode_english

OV29=0x022DC240
OV36=0x023A7080
SIZE=0x2000


def word(data,address,base):
    return struct.unpack_from("<I",data,address-base)[0]


def branch(site,target,link=False):
    delta=target-site-8
    if delta%4 or not -0x2000000<=delta<0x2000000:
        raise ValueError("mega_evolve ARM branch out of range")
    return (0xEB000000 if link else 0xEA000000)|((delta>>2)&0xFFFFFF)


def locate_base_stats(ov36):
    from true_patches.base_stats_speed.generate_tables import SENTINEL_OFF,SPEED_OFF,EVO_OFF,COMBAT_OFF
    sentinel=struct.pack("<I",0xB5A7E001)
    positions=[i for i in range(len(ov36)-3) if ov36[i:i+4]==sentinel]
    if len(positions)!=1:
        raise RuntimeError("mega_evolve requires exactly one installed base_stats_speed runtime")
    base=positions[0]-SENTINEL_OFF
    signature=struct.pack("<II",0xE92D4030,0xE59040B4)
    region=ov36[base+SPEED_OFF:base+EVO_OFF]
    positions=[i for i in range(len(region)-7) if region[i:i+8]==signature]
    if len(positions)!=1:
        raise RuntimeError("BaseStats_EntitySpe signature changed")
    entity_speed=OV36+base+SPEED_OFF+positions[0]
    calls=[]
    for off in range(base+SPEED_OFF,entity_speed-OV36,4):
        instruction=word(ov36,OV36+off,OV36)
        if instruction>>24==0xEB and branch_target(OV36+off,instruction)==entity_speed:
            calls.append(OV36+off)
    if len(calls)!=2:
        raise RuntimeError("BaseStats hit Speed consumer calls changed")
    from_monster=OV36+base+COMBAT_OFF
    if word(ov36,from_monster,OV36)!=0xE92D4070:
        raise RuntimeError("BaseStats_FromMonster prologue changed")
    return entity_speed,from_monster,calls


def build_runtime(module_dir,work,cave,entity_speed,from_monster):
    compiler=shutil.which("arm-none-eabi-gcc")
    if not compiler:
        raise RuntimeError("mega_evolve needs arm-none-eabi-gcc")
    prefix=str(Path(compiler).with_name("arm-none-eabi-"))
    suffix=".exe" if compiler.lower().endswith(".exe") else ""
    defines={"DUNGEON_PTR":0x02353538,"ABILITY_ACTIVE":0x02301D78,
             "SIGNED_DIVIDE":0x0208FEA4,"LEGACY_STRONG_WEATHER":0x022AB46A,
             "ENTITY_SPEED":entity_speed,"FROM_MONSTER_RESUME":from_monster+4}
    (work/"generated.h").write_text("".join(f"#define {k} 0x{v:X}\n" for k,v in defines.items()),encoding="ascii")
    linker=work/"phase1.ld"
    linker.write_text(f"SECTIONS {{ . = 0x{cave:X}; .text : {{ *(.text*) *(.rodata*) }} "
                      ".data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } MERuntimeEnd = .; "
                      "/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }",encoding="ascii")
    elf=work/"phase1.elf"
    command=[compiler,"-mcpu=arm946e-s","-marm","-Os","-ffreestanding","-fno-builtin",
             "-fno-unwind-tables","-fno-asynchronous-unwind-tables","-nostdlib","-Wall","-Wextra","-Werror",
             "-I",str(work),str(module_dir/"runtime/phase1.c"),str(module_dir/"runtime/phase1_hooks.S"),
             "-Wl,-T,"+str(linker),"-o",str(elf)]
    result=subprocess.run(command,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stdout+result.stderr)
    output=work/"phase1.bin"
    subprocess.run([prefix+"objcopy"+suffix,"-O","binary",str(elf),str(output)],check=True,capture_output=True)
    symbols={}
    for line in subprocess.check_output([prefix+"nm"+suffix,"--defined-only",str(elf)],text=True).splitlines():
        address,kind,name=line.split()
        if name.startswith("ME_") or name in ("state","MERuntimeEnd"):
            symbols[name]=int(address,16)
    if symbols["MERuntimeEnd"]>cave+SIZE:
        raise RuntimeError("mega_evolve phase1 exceeds allocated runtime/BSS size")
    return output.read_bytes(),symbols


def allocate_runtime(data,state):
    reserved=reserved_file_ranges(state,"ov36")
    runs=find_zero_run(bytes(data),SIZE,16,forbidden=ov36_forbidden_ranges())
    refs=scan_overlay_xrefs(bytes(data),OV36)
    failures=[]
    for start,length in runs:
        candidates={start}
        candidates.update((r.end+15)&~15 for r in reserved if start<=r.end<start+length)
        candidates.update((x.target_file_offset_for(OV36)+16)&~15 for x in refs
                          if start<=x.target_file_offset_for(OV36)<start+length)
        for candidate in sorted(candidates):
            if candidate+SIZE>start+length: continue
            try:
                return allocate_ov36_cave(data,OV36,SIZE,alignment=16,
                    preferred_file_offset=candidate,reserved_file_offsets=reserved)
            except RuntimeError as error:
                failures.append(str(error))
    raise RuntimeError("mega_evolve has no reserved/xref-safe runtime slot: "+"; ".join(failures[-2:]))


def apply_phase1(rom,module_dir,manifest,state,metadata):
    tables=loadOverlayTable(rom.arm9OverlayTable,lambda i,f:rom.files[f])
    ov29=bytearray(tables[29].data)
    ov36=bytearray(tables[36].data)
    entity_speed,from_monster,calls=locate_base_stats(ov36)
    # Existing instruction sites are fixed; new code placement is not.
    guards=[(29,0x02334D08,0xE92D4010),(29,0x0233554C,0xE3550000),
            (29,0x022FDDC0,0xE92D4FF8),(29,0x023196D8,0xE3540000),
            (29,0x0230C03C,0x028BB002),(36,0x023DB104,0xE1A00009),
            (36,0x023BF96C,0xE92D4002),(36,0x023BF950,0xE92D4001)]
    for ov,site,expected in guards:
        if word(ov29 if ov==29 else ov36,site,OV29 if ov==29 else OV36)!=expected:
            raise RuntimeError(f"mega_evolve hook guard failed at {site:#x}")
    hail_word=word(ov29,0x02310180,OV29)
    if hail_word>>24!=0x1A or branch_target(0x02310180,hail_word)!=0x023101FC:
        raise RuntimeError("hail periodic-damage guard changed")
    sun_site,rain_site=0x0230B5EC,0x0230B674
    # Preserve type-multiplier diagnostics and the opposite-type weather nerfs.
    if word(ov29,sun_site,OV29)!=0xE59F21BC or word(ov29,rain_site,OV29)!=0xE59F2134:
        raise RuntimeError("weather power multiplier load guard changed")
    gale_word=word(ov29,0x022FFEFC,OV29)
    if gale_word>>24!=0xEA:
        raise RuntimeError("balance_change Gale Wings speed hook missing")
    gale_target=branch_target(0x022FFEFC,gale_word)
    if ov36[gale_target-OV36:gale_target-OV36+12]!=struct.pack("<III",0xE92D400F,0xE1A00008,0xE3A0108E):
        raise RuntimeError("unexpected movement-speed hook owner")
    slot,ov36=allocate_runtime(ov36,state)
    with tempfile.TemporaryDirectory(prefix="mega_evolve_phase1_") as temporary:
        blob,symbols=build_runtime(module_dir,Path(temporary),slot.load_address,entity_speed,from_monster)
    ov36[slot.file_offset:slot.file_offset+SIZE]=bytes(SIZE)
    ov36[slot.file_offset:slot.file_offset+len(blob)]=blob
    edits=[]
    hooks=[]
    def patch(ov,site,value,name,target=None):
        data,base=(ov29,OV29) if ov==29 else (ov36,OV36)
        old=word(data,site,base)
        struct.pack_into("<I",data,site-base,value)
        edits.append({"overlay":ov,"site":site,"before":old,"after":value,"name":name})
        if target:
            hooks.append(HookRecord(name,site,"bl" if value>>24==0xEB else "b",target,"guarded_replacement"))
    for site,target in [(0x02334D08,"ME_ApparentWeatherHook"),(0x0233554C,"ME_WeatherSelectHook"),
                        (0x022FDDC0,"ME_SubInitMonsterHook"),(0x023196D8,"ME_ResetSpeedHook")]:
        patch(29,site,branch(site,symbols[target]),target,target)
    patch(36,from_monster,branch(from_monster,symbols["ME_FromMonsterHook"]),"WeatherDefense","ME_FromMonsterHook")
    for site,target in zip(calls,["ME_HitAttackerSpeedHook","ME_HitDefenderSpeedHook"]):
        patch(36,site,branch(site,symbols[target],True),target,target)
    for site,target in [(sun_site,"ME_SunPowerHook"),(rain_site,"ME_RainPowerHook")]:
        patch(29,site,branch(site,symbols[target],True),target,target)
    patch(29,0x02310180,(hail_word&0x0FFFFFFF)|0xE0000000,"RemoveHailChip")
    patch(29,0x0230C03C,0xE1A00000,"RemoveLegacySandSpDefStages")
    patch(36,0x023DB104,branch(0x023DB104,0x023DB134),"RemoveLegacyHailDefStages")
    patch(29,0x022FFEFC,0xE3540000,"GaleWingsIsNumericSpeed")
    for site,target in [(0x023BF96C,"ME_WeatherMessageHook"),(0x023BF950,"ME_WeatherFailureHook")]:
        patch(36,site,branch(site,symbols[target]),target,target)
    strings=parse_str_file(rom.getFileByName("MESSAGE/text_e.str"))
    text_data=json.loads((module_dir/"data/phase1_strings.json").read_text(encoding="utf-8"))
    for entry in text_data["entries"]:
        index=entry["index"]
        if index>=len(strings): strings.extend([b""]*(index+1-len(strings)))
        previous=decode_english(strings[index])
        if "before" in entry:
            if previous!=entry["before"]:
                raise RuntimeError(f"mega_evolve weather string guard failed at {index}")
        elif previous.strip() not in ("","[M:D1]"):
            raise RuntimeError(f"mega_evolve new string index {index} is occupied")
        strings[index]=entry["en"].encode("cp1252")
    rom.setFileByName("MESSAGE/text_e.str",build_str_file(strings))
    rom.files[tables[29].fileID]=bytes(ov29)
    write_ov36_to_rom(rom,None,bytes(ov36))
    return AppliedModule("mega_evolve",manifest.get("version",1),
        [CaveAllocation("ov36",slot.file_offset,SIZE,slot.load_address)],hooks,
        [{"mega_evolve":metadata,"phase":1,"symbols":symbols,"edits":edits,
          "cave_sha256":hashlib.sha256(ov36[slot.file_offset:slot.file_offset+SIZE]).hexdigest(),
          "base_stats_helpers":{"entity_speed":entity_speed,"from_monster":from_monster},
          "save_component_schema":1,"automatic_save_codec_integration_phase":4}])


def verify_phase1(rom,module_dir,manifest,record,metadata):
    if record is None or len(record.caves)!=1 or record.data[0].get("mega_evolve")!=metadata:
        raise AssertionError("mega_evolve phase1 linker record missing/stale")
    if record.id!="mega_evolve" or record.version!=manifest["version"] or record.data[0].get("phase")!=1:
        raise AssertionError("mega_evolve phase1 record version/phase mismatch")
    if not isinstance(rom,NintendoDSRom):
        rom=NintendoDSRom(Path(rom).read_bytes())
    tables=rom.loadArm9Overlays()
    cave=record.caves[0]
    blob=bytes(tables[36].data[cave.file_offset:cave.file_offset+cave.size])
    if hashlib.sha256(blob).hexdigest()!=record.data[0]["cave_sha256"]:
        raise AssertionError("mega_evolve phase1 cave hash mismatch")
    for edit in record.data[0]["edits"]:
        base=OV29 if edit["overlay"]==29 else OV36
        if word(tables[edit["overlay"]].data,edit["site"],base)!=edit["after"]:
            raise AssertionError(f"mega_evolve instruction changed at {edit['site']:#x}")
