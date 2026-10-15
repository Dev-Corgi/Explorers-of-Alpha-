"""Allocate/link mega_evolve runtime phases and guard replaced instructions."""
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


def build_runtime(module_dir,work,cave,entity_speed,from_monster,phase=1,skill_swap_message=0,additional_defines=None,emit_relocations=False):
    compiler=shutil.which("arm-none-eabi-gcc")
    if not compiler:
        raise RuntimeError("mega_evolve needs arm-none-eabi-gcc")
    prefix=str(Path(compiler).with_name("arm-none-eabi-"))
    suffix=".exe" if compiler.lower().endswith(".exe") else ""
    defines={"DUNGEON_PTR":0x02353538,"ABILITY_ACTIVE":0x02301D78,
             "SIGNED_DIVIDE":0x0208FEA4,"LEGACY_STRONG_WEATHER":0x022AB46A,
             "ENTITY_SPEED":entity_speed,"FROM_MONSTER_FN":from_monster,"FROM_MONSTER_RESUME":from_monster+4}
    if phase>=2:
        from true_patches.mega_evolve.phase2 import load,header
        (work/"abilities_generated.h").write_text(header(load()),encoding="ascii")
        defines.update(ME_PHASE2=1,SKILL_SWAP_MESSAGE=skill_swap_message)
    if phase>=3:
        from true_patches.mega_evolve.phase3 import load,header
        (work/"phase3_generated.h").write_text(header(load()),encoding="ascii")
        from true_patches.mega_evolve.phase3_items import load as items,header as item_header
        (work/"phase3_items_generated.h").write_text(item_header(items()),encoding="ascii")
        from true_patches.mega_evolve.phase3_moves import header as move_header
        (work/'phase3_moves_generated.h').write_text(move_header(),encoding='ascii')
        defines.update(ME_PHASE3=1)
    if phase>=4:
        from true_patches.mega_evolve.phase4 import load as forms,header as form_header
        data=forms()
        (work/'phase4_generated.h').write_text(form_header(data),encoding='ascii')
        from true_patches.mega_evolve.new_species import header as new_header
        (work/'new_species_generated.h').write_text(new_header(),encoding='ascii')
        defines['ME_PHASE4']=1
    if phase>=5:defines.update(ME_PHASE5=1,ME_FORM_FIRST_ASM=data['first_species'])
    if phase>=6:
        from true_patches.mega_evolve.trial_tower import header as tower_header
        (work/'trial_tower_generated.h').write_text(tower_header(),encoding='ascii')
        defines['ME_TRIAL_TOWER']=1
    defines.update(additional_defines or {})
    if phase>=3:
        from true_patches.mega_evolve.status_hooks import assembly
        (work/"phase3_status_generated.S").write_text(assembly(defines),encoding="ascii")
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
    if emit_relocations:command.insert(-2,'-Wl,--emit-relocs')
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
    if phase<3 and symbols["MERuntimeEnd"]>cave+(0x4000 if phase>=2 else SIZE):
        raise RuntimeError("mega_evolve runtime bytes="+str(symbols["MERuntimeEnd"]-cave))
    return output.read_bytes(),symbols


def allocate_runtime(data,state,size=SIZE):
    reserved=reserved_file_ranges(state,"ov36")
    runs=find_zero_run(bytes(data),size,16,forbidden=ov36_forbidden_ranges())
    refs=scan_overlay_xrefs(bytes(data),OV36)
    failures=[]
    for start,length in runs:
        candidates={start}
        candidates.update((r.end+15)&~15 for r in reserved if start<=r.end<start+length)
        candidates.update((x.target_file_offset_for(OV36)+16)&~15 for x in refs
                          if start<=x.target_file_offset_for(OV36)<start+length)
        for candidate in sorted(candidates):
            if candidate+size>start+length: continue
            try:
                return allocate_ov36_cave(data,OV36,size,alignment=16,
                    preferred_file_offset=candidate,reserved_file_offsets=reserved)
            except RuntimeError as error:
                failures.append(str(error))
    raise RuntimeError("mega_evolve has no reserved/xref-safe runtime slot: "+"; ".join(failures[-2:]))


def apply_phase1(rom,module_dir,manifest,state,metadata):
    if manifest['phase']>=3:
        # Bootstrap depends on the observed native ROM-file API, not only the
        # vanilla symbol's address. Fail before mutating the in-memory ROM.
        if word(rom.arm9,0x02008c3c,0x02000000)!=0xe92d4008 or word(rom.arm9,0x02008c5c,0x02000000)!=branch(0x02008c5c,0x02008d60,True):
            raise RuntimeError('mega_evolve native file loader guard changed')
        if word(rom.arm9,0x020528fc,0x02000000)!=0xe59f2010 or word(rom.arm9,0x0205290c,0x02000000)!=0xe1d002b8:
            raise RuntimeError('mega_evolve native weight lookup guard changed')
        if rom.filenames.subfolder('MEGA') is not None:
            raise RuntimeError('mega_evolve runtime namespace already occupied')
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
    if manifest["phase"]>=2:
        block_guards=json.loads((module_dir/"data/phase2_hooks.json").read_text(encoding="utf-8"))
        for block in block_guards["blocks"]:
            observed=hashlib.sha256(ov29[block["start"]-OV29:block["end"]-OV29]).hexdigest()
            if observed!=block["sha256"]:
                raise RuntimeError(f"mega_evolve {block['owner']} skipped-block guard failed")
        guards2=[(0x02301d10,0xEA000000),(0x022f9538,0xEA000000),
                 (0x02328714,0xE5D58060),(0x0232a1c8,0xE5D72060),
                 (0x0233493c,0xE5D41060),(0x022f9220,0xE59F0010)]
        for site,expected in guards2:
            actual=word(ov29,site,OV29)
            if (actual&0xff000000 if expected==0xEA000000 else actual)!=expected:
                raise RuntimeError(f"mega_evolve ability hook guard failed at {site:#x}")
        # Preserve the installed balance item predicate and bug_fixes Trace owner.
        target=branch_target(0x02301d10,word(ov29,0x02301d10,OV29))
        if bytes(ov36[target-OV36:target-OV36+8])!=struct.pack("<II",0xE92D401F,0xE1A04000):
            raise RuntimeError("unexpected native ability predicate owner")
        trace_target=branch_target(0x022f9538,word(ov29,0x022f9538,OV29))
        if bytes(ov36[trace_target-OV36:trace_target-OV36+12])!=struct.pack("<III",0xE92D500F,0xE1A00008,0xE3A01028):
            raise RuntimeError("unexpected native Trace predicate owner")
    runtime_size=0x4000 if manifest["phase"]>=2 else SIZE
    scatter_info={}
    if manifest["phase"]>=3:
        from true_patches.mega_evolve.phase3_items import validate_rom as validate_items
        validate_items(rom)
        from true_patches.mega_evolve.phase3_moves import validate_rom as validate_moves
        validate_moves(rom)
        from .mega_evolve_loader import link_runtime
        caves,ov36,symbols,scatter_info,runtime_payload=link_runtime(module_dir,ov29,ov36,state,entity_speed,from_monster,manifest['phase'])
    else:
        slot,ov36=allocate_runtime(ov36,state,runtime_size)
        with tempfile.TemporaryDirectory(prefix="mega_evolve_phase1_") as temporary:
            blob,symbols=build_runtime(module_dir,Path(temporary),slot.load_address,entity_speed,from_monster,manifest["phase"],word(ov29,0x02328790,OV29))
        ov36[slot.file_offset:slot.file_offset+runtime_size]=bytes(runtime_size)
        ov36[slot.file_offset:slot.file_offset+len(blob)]=blob
        caves=[CaveAllocation("ov36",slot.file_offset,runtime_size,slot.load_address)]
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
    if manifest["phase"]>=2:
        for site,target in [(0x02301d10,"ME_AbilityActiveHook"),(0x022f9538,"ME_TraceHook"),
                            (0x02328714,"ME_SkillSwapHook"),(0x0232a1c8,"ME_RolePlayHook"),
                            (0x0233493c,"ME_AbilitiesEqualHook"),(0x022f9220,"ME_RestoreAbilitiesHook")]:
            if manifest["phase"]>=3 and site==0x02301d10:target="ME_NativeAbilityHook"
            patch(29,site,branch(site,symbols[target]),target,target)
    if manifest["phase"]>=3:
        from .mega_evolve_phase3_runtime import install_hooks
        install_hooks(ov29,ov36,symbols,patch)
    if manifest['phase']>=4:
        from true_patches.base_stats_speed.generate_tables import COMBAT_OFF
        root=from_monster-COMBAT_OFF
        for offset,target in ((0,'ME_FormStatHook'),(4,'ME_FormRateHook')):
            if word(ov36,root+offset,OV36)>>24!=0xea:
                raise RuntimeError('phase4 base-stat entry guard changed')
            patch(36,root+offset,branch(root+offset,symbols[target]),target,target)
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
    prepared_files={"MESSAGE/text_e.str":build_str_file(strings)}
    profile_edits=[]
    if manifest["phase"]>=3:
        from .mega_evolve_phase3_data import prepare_data
        files,profile_edits=prepare_data(rom,strings)
        prepared_files.update(files)
    for path,content in prepared_files.items():rom.setFileByName(path,content)
    if manifest['phase']>=4:
        from .mega_evolve_phase4_data import prepare_files
        prepared_files.update(prepare_files(rom))
        for path,content in prepared_files.items():rom.setFileByName(path,content)
    sprite_details=None
    if manifest['phase']>=5:
        from .mega_evolve_phase5_data import prepare as prepare_sprites
        sprite_files,sprite_details=prepare_sprites(rom,module_dir)
        prepared_files.update(sprite_files)
        for path,content in sprite_files.items():rom.setFileByName(path,content)
    if manifest['phase']>=3:
        from .mega_evolve_loader import install_file
        install_file(rom,runtime_payload)
    rom.files[tables[29].fileID]=bytes(ov29)
    write_ov36_to_rom(rom,None,bytes(ov36))
    record=AppliedModule("mega_evolve",manifest.get("version",1),
        caves,hooks,
        [{"mega_evolve":metadata,"phase":manifest["phase"],"symbols":symbols,"edits":edits,
          **scatter_info,
          **({"cave_sha256":hashlib.sha256(ov36[caves[0].file_offset:caves[0].file_offset+caves[0].size]).hexdigest()} if len(caves)==1 else {}),
          "cave_hashes":[hashlib.sha256(ov36[c.file_offset:c.file_offset+c.size]).hexdigest() for c in caves],
          "base_profile_edits":profile_edits,
          **({"phase3_md_sha256":hashlib.sha256(prepared_files["BALANCE/monster.md"]).hexdigest()} if manifest["phase"]>=3 else {}),
          "base_stats_helpers":{"entity_speed":entity_speed,"from_monster":from_monster},
          "save_component_schema":2 if manifest["phase"]>=2 else 1,"automatic_save_codec_integration_phase":4}])
    if manifest['phase']>=4:
        record.data[0]['new_species_resources_sha256']={path:hashlib.sha256(prepared_files[path]).hexdigest()
            for path in ('BALANCE/waza_p.bin','FONT/kaomado.kao')}
    if manifest['phase']>=3 and manifest.get('species_save_bits',11)==12:
        from .mega_evolve_save12 import install
        info=install(rom,module_dir,state)
        record.caves.append(info['cave']);record.hooks.extend(info['hooks'])
        record.data[0]['species_save_codec']={k:v for k,v in info.items() if k not in ('cave','hooks')}
        record.data[0]['species_save_codec']['cave']=info['cave'].to_dict()
    if manifest['phase']>=4:
        arm9=bytearray(rom.arm9)
        quick_edits=[]
        for site,target,prior in ((0x02049264,'ME_QuickWrite',0x02048E74),
                                  (0x02049644,'ME_QuickRead',0x02048ED0)):
            before=word(arm9,site,0x02000000)
            if before!=branch(site,prior,True):raise RuntimeError('phase4 quicksave codec call changed')
            value=branch(site,symbols[target],True)
            struct.pack_into('<I',arm9,site-0x02000000,value)
            quick_edits.append(dict(site=site,after=value))
            record.hooks.append(HookRecord(target,site,'bl',target,'quicksave_sidecar'))
        rom.arm9=bytes(arm9)
        record.data[0]['quick_edits']=quick_edits
        from .mega_evolve_phase4_runtime import install
        from .state import BuildState
        combined=BuildState('us_vanilla',OV29,list(state.applied) if state else [])
        combined.applied.append(record)
        info=install(rom,module_dir,combined,phase=manifest['phase'],runtime_symbols=symbols)
        record.caves.append(info['cave']);record.hooks.extend(info['hooks'])
        record.data[0]['form_consumers']={k:v for k,v in info.items() if k not in ('cave','hooks')}
        record.data[0]['form_consumers']['cave']=info['cave'].to_dict()
        if manifest['phase']>=5:
            from .mega_evolve_phase5_runtime import install as install_cache
            from true_patches.mega_evolve.phase4 import load as forms
            record.data[0]['sprite_cache_edits']=install_cache(rom,symbols,info['symbols'],record,forms()['total_species'])
            record.data[0]['sprites']=sprite_details
            revised={e['site']:e['after'] for e in record.data[0]['sprite_cache_edits']}
            for e in record.data[0]['form_consumers']['edits']:
                if e['binary']==29 and e['site'] in revised:e['after']=revised[e['site']]
    if manifest['phase']>=6:
        from .mega_evolve_phase6 import install
        record.data[0]['spring']=install(rom,module_dir,state,record)
        from .mega_evolve_trial_tower import install as install_tower
        record.data[0]['trial_tower']=install_tower(rom,module_dir,state,record)
    if manifest['phase']>=4:
        from .mega_evolve_native_data import install
        record.data[0]['native_data']=install(rom,record.data[0]['species_save_codec'])
    return record


def verify_phase1(rom,module_dir,manifest,record,metadata):
    if record is None or not record.caves or record.data[0].get("mega_evolve")!=metadata:
        raise AssertionError("mega_evolve phase1 linker record missing/stale")
    if record.id!="mega_evolve" or record.version!=manifest["version"] or record.data[0].get("phase")!=manifest["phase"]:
        raise AssertionError("mega_evolve phase1 record version/phase mismatch")
    if not isinstance(rom,NintendoDSRom):
        rom=NintendoDSRom(Path(rom).read_bytes())
    if manifest['phase']>=4:
        from .mega_evolve_native_data import verify
        verify(rom,record.data[0]['native_data'])
    tables=rom.loadArm9Overlays()
    if manifest['phase']>=3:
        if hashlib.sha256(rom.getFileByName(record.data[0]['runtime_file'])).hexdigest()!=record.data[0]['runtime_sha256']:
            raise AssertionError('mega_evolve execution payload hash mismatch')
    if manifest['phase']>=3 and hashlib.sha256(rom.getFileByName('BALANCE/monster.md')).hexdigest()!=record.data[0].get('phase3_md_sha256'):
        raise AssertionError('mega_evolve phase3 MD hash mismatch')
    caves=[c for c in record.caves if c.overlay=='ov36']
    hashes=record.data[0].get('cave_hashes') or [record.data[0].get('cave_sha256')]
    if len(caves)==1 and record.data[0].get('cave_sha256',hashes[0])!=hashes[0]:
        raise AssertionError('mega_evolve conflicting single-cave hashes')
    if len(hashes)!=len(caves):raise AssertionError('mega_evolve cave record mismatch')
    for cave,expected in zip(caves,hashes):
        blob=bytes(tables[36].data[cave.file_offset:cave.file_offset+cave.size])
        if hashlib.sha256(blob).hexdigest()!=expected:
            raise AssertionError("mega_evolve phase1 cave hash mismatch")
    for edit in record.data[0]["edits"]:
        base=OV29 if edit["overlay"]==29 else OV36
        if word(tables[edit["overlay"]].data,edit["site"],base)!=edit["after"]:
            raise AssertionError(f"mega_evolve instruction changed at {edit['site']:#x}")
    if manifest['phase']>=3 and manifest.get('species_save_bits',11)==12:
        from .mega_evolve_save12 import verify
        info=dict(record.data[0]['species_save_codec'])
        c=info['cave'];info['cave']=CaveAllocation(c['overlay'],c['file_offset'],c['size'],c['load_address'])
        if info['cave'] not in record.caves:raise AssertionError('missing resident species codec reservation')
        verify(rom,info)
    if manifest['phase']>=4:
        for path,digest in record.data[0]['new_species_resources_sha256'].items():
            if hashlib.sha256(rom.getFileByName(path)).hexdigest()!=digest:
                raise AssertionError('new species resource drift: '+path)
        for edit in record.data[0]['quick_edits']:
            if word(rom.arm9,edit['site'],0x02000000)!=edit['after']:
                raise AssertionError('phase4 quicksave hook changed')
        from .mega_evolve_phase4_runtime import verify
        info=dict(record.data[0]['form_consumers']);c=info['cave']
        info['cave']=CaveAllocation(c['overlay'],c['file_offset'],c['size'],c['load_address'])
        if info['cave'] not in record.caves:raise AssertionError('missing form consumer reservation')
        verify(rom,info)
    if manifest['phase']>=5:
        from .mega_evolve_phase5_runtime import verify as verify_cache
        from .mega_evolve_phase5_data import verify as verify_sprites
        verify_cache(rom,record.data[0]['sprite_cache_edits']);verify_sprites(rom,record.data[0]['sprites'])
    if manifest['phase']>=6:
        from .mega_evolve_phase6 import verify
        verify(rom,record.data[0]['spring'])
        from .mega_evolve_trial_tower import verify as verify_tower
        verify_tower(rom,record.data[0]['trial_tower'])
