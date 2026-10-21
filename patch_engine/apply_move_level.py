"""Apply the per-Pokemon move mastery module."""
from __future__ import annotations

import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom

from .apply_asm import _binary_load
from .apply_spinda_ev import _get_binary_bytes, _set_binary_bytes
from .armips_runner import run_armips_bundle, write_generated_inc_text
from .cave_allocator import allocate_cave
from .cave_manifest import parse_forbidden_ranges, parse_max_file_offset
from .hook_registry import assert_hooks_on_binary, collect_hook_records, resolve_prior_target
from .overlay_caves import allocate_overlay_cave
from .cave_reservations import FileRange, reserved_file_ranges
from .state import AppliedModule, CaveAllocation, HookRecord
from .manifest import resolve_symbol


def _compiler() -> str:
    value = os.environ.get("ARM_GCC") or shutil.which("arm-none-eabi-gcc")
    if not value:
        candidate = Path("C:/msys64/mingw64/bin/arm-none-eabi-gcc.exe")
        if candidate.is_file():
            value = str(candidate)
    if not value:
        raise RuntimeError("move_level requires arm-none-eabi-gcc")
    return value


def _build_runtime(module_dir: Path, work: Path, runtime_address: int, state_address: int, symbols: dict[str, int]) -> tuple[Path, list[str]]:
    compiler = _compiler()
    prefix = str(Path(compiler).with_name("arm-none-eabi-"))
    suffix = ".exe" if compiler.lower().endswith(".exe") else ""
    defines = {
        "STATE_ADDRESS": state_address,
        "TM_PENDING": symbols["tm_pending"],
        "Z_PENDING": symbols["z_pending"],
        "Z_SELECTED_SLOT": symbols["z_selected_slot"],
        "PRIOR_SAVE_READ": symbols["prior_save_read"],
        "PRIOR_SAVE_WRITE": symbols["prior_save_write"],
        "PRIOR_NEW_GAME": symbols["prior_new_game"],
    }
    (work / "generated.h").write_text(
        "".join(f"#define {key} 0x{value:X}\n" for key, value in defines.items()),
        encoding="ascii",
    )
    linker = work / "move_level.ld"
    linker.write_text(
        f"SECTIONS {{ . = 0x{runtime_address:X}; .text : {{ *(.text*) *(.rodata*) }} "
        "/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }",
        encoding="ascii",
    )
    elf = work / "move_level.elf"
    command = [
        compiler, "-mcpu=arm946e-s", "-marm", "-Os", "-ffreestanding",
        "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
        "-nostdlib", "-Wall", "-Wextra", "-Werror", "-I", str(work),
        str(module_dir / "runtime/save.c"), "-Wl,-T," + str(linker), "-o", str(elf),
    ]
    compiled = subprocess.run(command, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError("move_level runtime compile failed:\n" + compiled.stderr + "\nLINKER=" + linker.read_text())
    output = work / "move_level.bin"
    subprocess.run([prefix + "objcopy" + suffix, "-O", "binary", str(elf), str(output)], check=True)
    if output.stat().st_size > 0x1400:
        raise RuntimeError("move_level runtime exceeds the ARM9 code area")
    nm = subprocess.check_output([prefix + "nm" + suffix, "--defined-only", str(elf)], text=True)
    labels = []
    for line in nm.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == "T" and parts[2].startswith("MoveLevel_"):
            labels.append(f".definelabel {parts[2]}, 0x{int(parts[0], 16):X}")
    return output, labels


def _prior_lines(hooks: list[dict[str, Any]], profile: dict[str, Any], blobs: dict[str, bytearray]) -> dict[str, int]:
    result: dict[str, int] = {}
    for hook in hooks:
        label = hook.get("prior_label")
        if not label:
            continue
        binary = hook.get("binary", "ov29")
        site = resolve_symbol(profile, hook["symbol"])
        load = _binary_load(profile, binary)
        word = struct.unpack_from("<I", blobs[binary], site - load)[0]
        result[label] = resolve_prior_target(site, word, hook)
    return result


def apply_move_level_module(*, module_id: str, module_dir: Path, manifest: dict[str, Any],
                            profile: dict[str, Any], rom: NintendoDSRom, armips, state,
                            prior_hook_sites: set[int]) -> AppliedModule:
    from skytemple_files.common.util import get_ppmdu_config_for_rom
    config = get_ppmdu_config_for_rom(rom)
    arm9 = bytearray(rom.arm9)
    ov29 = bytearray(_get_binary_bytes(rom, config, "ov29"))
    hooks = manifest.get("hooks") or []
    for hook in hooks:
        hook.setdefault("binary", "ov29")
    blobs = {"arm9": arm9, "ov29": ov29}
    for binary, blob in blobs.items():
        load = _binary_load(profile, binary)
        assert_hooks_on_binary(bytes(blob), load, [h for h in hooks if h.get("binary") == binary], profile, prior_hook_sites)

    arm_cfg = manifest["caves"]["arm9"]
    reserved = reserved_file_ranges(state, "arm9", exclude_module=module_id)
    arm_slot = allocate_cave(
        bytes(arm9), _binary_load(profile, "arm9"), int(arm_cfg["estimated_bytes"], 0) if isinstance(arm_cfg["estimated_bytes"], str) else int(arm_cfg["estimated_bytes"]),
        alignment=4, reserved_file_offsets=reserved,
        forbidden_file_offsets=parse_forbidden_ranges(arm_cfg),
        max_file_offset=parse_max_file_offset(arm_cfg), check_vanilla_xrefs=False,
    )
    ov_cfg = dict(manifest["caves"]["ov29"])
    ov_cfg["binary"] = "ov29"
    ov_slot, ov29 = allocate_overlay_cave(
        binary="ov29", overlay_data=ov29, profile=profile, state=state,
        cave_cfg=ov_cfg, module_id=module_id,
    )
    tail_size = 0x5000
    tail_off = (len(arm9) + 3) & ~3
    if tail_off + tail_size > len(arm9):
        arm9.extend(bytes(tail_off + tail_size - len(arm9)))
    tail_address = _binary_load(profile, "arm9") + tail_off
    arm9[arm_slot.file_offset:arm_slot.file_offset + arm_slot.size] = bytes(arm_slot.size)

    prior = _prior_lines(hooks, profile, blobs)
    with tempfile.TemporaryDirectory(prefix="true_patches_move_level_") as temp:
        work = Path(temp)
        runtime, runtime_labels = _build_runtime(
            module_dir, work, tail_address + 0x400, tail_address + 0x3000,
            {
                "tm_pending": 0x023C2C10,
                "z_pending": 0x023C3718,
                "z_selected_slot": 0x023C3714,
                "prior_save_read": prior["MoveLevel_PriorSaveRead"],
                "prior_save_write": prior["MoveLevel_PriorSaveWrite"],
                "prior_new_game": prior["MoveLevel_PriorNewGame"],
            },
        )
        arm9[tail_off + 0x400:tail_off + 0x400 + runtime.stat().st_size] = runtime.read_bytes()
        generated = [
            f".definelabel MoveLevelArm9Code, 0x{arm_slot.load_address:X}",
            f".definelabel MoveLevelOv29Code, 0x{ov_slot.load_address:X}",
        ]
        generated.extend(f".definelabel {name}, 0x{value:X}" for name, value in prior.items())
        generated.extend(runtime_labels)
        paths = {"arm9.bin": work / "arm9.bin", "overlay_0029.bin": work / "overlay_0029.bin"}
        paths["arm9.bin"].write_bytes(bytes(arm9))
        paths["overlay_0029.bin"].write_bytes(bytes(ov29))
        inc = work / "generated.inc"
        write_generated_inc_text(inc, "\n".join(generated) + "\n")
        asm_dir = work / "asm"
        shutil.copytree(module_dir / "asm", asm_dir)
        run_armips_bundle(armips=armips, asm_dir=asm_dir, asm_entry="main.asm",
                          binaries=paths, generated_inc=inc)
        arm9 = bytearray(paths["arm9.bin"].read_bytes())
        ov29 = bytearray(paths["overlay_0029.bin"].read_bytes())
        if len(arm9) < tail_off + tail_size:
            arm9.extend(bytes(tail_off + tail_size - len(arm9)))
        arm9[tail_off + 0x400:tail_off + 0x400 + runtime.stat().st_size] = runtime.read_bytes()

    rom.arm9 = bytes(arm9)
    _set_binary_bytes(rom, config, "ov29", bytes(ov29))
    records = collect_hook_records(hooks, profile, ov_slot.load_address)
    return AppliedModule(
        id=module_id, version=int(manifest.get("version", 1)),
        caves=[
            CaveAllocation("arm9", arm_slot.file_offset, arm_slot.size, arm_slot.load_address),
            CaveAllocation("ov29", ov_slot.file_offset, ov_slot.size, ov_slot.load_address),
            CaveAllocation("arm9", tail_off, tail_size, tail_address),
        ],
        hooks=[HookRecord(h["name"], h["site"], h["kind"], h["target_symbol"], h["chain"]) for h in records],
        data=[{"MoveLevelArm9Code": f"0x{arm_slot.load_address:X}",
               "MoveLevelOv29Code": f"0x{ov_slot.load_address:X}",
               "save_block_bytes": 0x2300, "save_pages": [400, 440]}],
    )


def verify_move_level_module(rom_path: Path, module_dir: Path, manifest: dict[str, Any], state_mod) -> None:
    if not state_mod or len(state_mod.caves) != 3:
        raise AssertionError("move_level state must contain ARM9 code, ov29 code, and ARM9 state tail")
    rom = NintendoDSRom(rom_path.read_bytes())
    arm = bytes(rom.arm9)
    tail = state_mod.caves[2]
    if arm[tail.file_offset + 0x400:tail.file_offset + 0x404] == b"\0\0\0\0":
        raise AssertionError("move_level ARM9 runtime tail is empty")
