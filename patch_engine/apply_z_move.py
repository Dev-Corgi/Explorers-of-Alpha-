from __future__ import annotations

import struct
import tempfile
from pathlib import Path
from typing import Any

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
    set_binary_in_rom,
)
from skytemple_files.data.str.handler import StrHandler

from .apply_asm import _export_cave_symbols
from .armips_runner import run_armips_bundle, write_generated_inc_text
from .cave_allocator import allocate_cave
from .cave_manifest import parse_forbidden_ranges, parse_max_file_offset
from .overlay_caves import (
    allocate_overlay_cave,
    binary_load,
    get_rom_binary,
    normalize_cave_binary,
    overlay_filename,
    write_rom_binary,
)
from .arm9_layout import spinda_arm9_legacy_range
from .cave_reservations import reserved_file_ranges
from true_patches.z_move_v2.patch_shell_move import patch_shell_move_data, verify_shell_move_data
from .hook_registry import (
    branch_target,
    collect_hook_records,
    hook_word_kind,
    resolve_prior_target,
)
from .manifest import load_yaml, resolve_symbol
from .state import AppliedModule, BuildState, CaveAllocation, HookRecord

OV29_LOAD = 0x022DC240
OV31_LOAD = 0x02382820
OV11_LOAD = 0x022DC240
ARM9_LOAD = 0x02000000
ZGAUGE_WRAM = 0x022B6A00
EXECUTE_MOVE_EFFECT = 0x0232E864
EXECUTE_MOVE_EFFECT_HOOK1 = 0x02322B50
ROOM_CHARGE_WRAPPER_OFFSET = 0x298
TM_READ_FALLBACK_SUB_OFF = 0x0
TM_READ_FALLBACK_CLEANUP_OFF = 0x8
ROOM_CHARGE_MOVE_STUB_OFF = 0xC
ROOM_CHARGE_STATE_STUB_OFF = 0x14
# After RoomChargeStateNoOp (+0x14, 8 bytes) → PriorLevelUpFallback @ +0x1C
ZMOVE_PRIOR_LEVEL_UP_FALLBACK_OFF = 0x1C
ZMOVE_PRIOR_RESTORE_PP_FALLBACK_OFF = 0x24


def _parse_fixed(value: Any) -> int | None:
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def _binary_load(profile: dict[str, Any], name: str) -> int:
    return binary_load(profile, name)


def _get_binary_bytes(rom: NintendoDSRom, config, name: str) -> bytes:
    return bytes(get_rom_binary(rom, name))


def _set_binary_bytes(rom: NintendoDSRom, config, name: str, data: bytes) -> None:
    write_rom_binary(rom, config, name, data)


_ROOM_CHARGE_IDS = frozenset({"room_charge", "room_charge_pending"})
# ov36 legacy/pending cave: RoomChargeExecuteMoveEffectWrapper relative to cave base.
ROOM_CHARGE_OV36_WRAPPER_OFFSET = 0x2B4


def _prior_execute_move_effect_call(
    state: BuildState | None,
    profile: dict[str, Any],
    *,
    ov29_data: bytes | bytearray | None = None,
    ov29_load: int | None = None,
) -> int:
    """Resolve prior ExecuteMoveEffect callee for Z-Move chain=append.

    Prefer room_charge / room_charge_pending exports (or ov36 cave+wrapper).
    Live hook BL is a fallback for first-time append; on z_move re-apply the site
    already points at ZMove itself, so state/cave must win.
    """
    if state:
        for mod in state.applied:
            if mod.id not in _ROOM_CHARGE_IDS:
                continue
            data = (mod.data or [{}])[0]
            sym = data.get("RoomChargeExecuteMoveEffectWrapper")
            if sym:
                return int(sym, 16)
            for cave in mod.caves:
                if cave.overlay in ("ov36", "overlay36", "overlay_0036"):
                    return cave.load_address + ROOM_CHARGE_OV36_WRAPPER_OFFSET
                if cave.overlay in ("ov29", "overlay29", "overlay_0029"):
                    return cave.load_address + ROOM_CHARGE_WRAPPER_OFFSET

    hook1 = int(
        profile.get("symbols", {}).get("ExecuteMoveEffectHook1", EXECUTE_MOVE_EFFECT_HOOK1)
    )
    if ov29_data is not None and ov29_load is not None:
        off = hook1 - ov29_load
        if 0 <= off + 4 <= len(ov29_data):
            word = struct.unpack_from("<I", ov29_data, off)[0]
            if hook_word_kind(word) in ("b", "bl"):
                return branch_target(hook1, word)

    return int(profile.get("symbols", {}).get("ExecuteMoveEffect", EXECUTE_MOVE_EFFECT))


def _prior_is_room_charge_move(state: BuildState | None, profile: dict[str, Any]) -> tuple[int, str]:
    """Full-function fallback for IsRoomChargeMove when Z-Move is not pending.

    room_charge / room_charge_pending export a real helper. room_charge_v3/v4 do not —
    Alpha's profile address 0x231C3D0 is empty padding, so prefer tm_read's return-0
    stub (or z_move local stub via generated.inc fallback address 0).
    """
    del profile
    if state:
        for mod in state.applied:
            if mod.id not in _ROOM_CHARGE_IDS:
                continue
            data = (mod.data or [{}])[0]
            sym = data.get("IsRoomChargeMove")
            if sym:
                # Full function entry (has its own push/pop); do not use +4 body.
                return int(sym, 16), mod.id
        for mod in state.applied:
            if mod.id != "tm_read":
                continue
            data = (mod.data or [{}])[0]
            sym = data.get("TmReadIsRoomChargeMove")
            if sym:
                return int(sym, 16), "tm_read"
    return 0, "stub"


def _prior_get_room_charge_state(state: BuildState | None, profile: dict[str, Any]) -> tuple[int, str]:
    """GetRoomChargeState for Z-Move slot-restore gating.

    Never fall back to Alpha padding @ 0x231C47C (zeros) — that executes as
    garbage after Z-Move pending cleanup and corrupts menus/actions.
    """
    del profile
    if state:
        for mod in state.applied:
            if mod.id not in _ROOM_CHARGE_IDS:
                continue
            data = (mod.data or [{}])[0]
            sym = data.get("GetRoomChargeState")
            if sym:
                return int(sym, 16), mod.id
        for mod in state.applied:
            if mod.id != "tm_read":
                continue
            data = (mod.data or [{}])[0]
            sym = data.get("TmReadGetRoomChargeState")
            if sym:
                return int(sym, 16), "tm_read"
    return 0, "stub"


def _resolve_tm_read_integration(
    state: BuildState | None,
    ov29_base: int,
) -> tuple[int, int, int, int, str]:
    """Return (PriorSubMenu, PriorCleanup/ForceRestore, PriorLevelUp, PriorRestorePp, source)."""
    if state:
        for mod in state.applied:
            if mod.id != "tm_read":
                continue
            data = (mod.data or [{}])[0]
            prior_sub = data.get("TmRead_CheckReadString")
            prior_cleanup = data.get("TmRead_ForceRestorePending") or data.get(
                "TmRead_TryRestoreSlot"
            )
            prior_level = data.get("TmRead_LevelUpForceRestore")
            prior_pp = data.get("TmRead_RestorePpForceRestore")
            if prior_sub and prior_cleanup and prior_level and prior_pp:
                return (
                    int(prior_sub, 16),
                    int(prior_cleanup, 16),
                    int(prior_level, 16),
                    int(prior_pp, 16),
                    "tm_read",
                )
    return (
        ov29_base + TM_READ_FALLBACK_SUB_OFF,
        ov29_base + TM_READ_FALLBACK_CLEANUP_OFF,
        ov29_base + ZMOVE_PRIOR_LEVEL_UP_FALLBACK_OFF,
        ov29_base + ZMOVE_PRIOR_RESTORE_PP_FALLBACK_OFF,
        "fallback",
    )


def _assert_code_entry(overlay: bytes, overlay_load: int, addr: int, label: str) -> None:
    """Reject exports that land on BSS zeros (would execute SlotBackup as code)."""
    off = addr - overlay_load
    if off < 0 or off + 4 > len(overlay):
        raise RuntimeError(f"{label} {addr:#x} outside overlay")
    word = struct.unpack_from("<I", overlay, off)[0]
    if word == 0:
        raise RuntimeError(
            f"{label} {addr:#x} points at zero word (BSS/padding) - "
            "check tm_read export_symbols offsets"
        )


def _resolve_zmove_try_restore_slot(
    overlay: bytes,
    overlay_load: int,
    cave_load: int,
    cave_size: int,
) -> int:
    """Find ZMove_TryRestoreSlotForEntity after armips (push {r4-r8,lr}; mov r8,r0).

    Hardcoded manifest offsets go stale whenever TryAppend/HUD code above it grows.
    """
    push = 0xE92D41F0  # push {r4,r5,r6,r7,r8,lr}
    mov_r8_r0 = 0xE1A08000
    start = cave_load - overlay_load
    end = start + cave_size
    hits: list[int] = []
    for off in range(start, max(start, end - 8), 4):
        w0 = struct.unpack_from("<I", overlay, off)[0]
        w1 = struct.unpack_from("<I", overlay, off + 4)[0]
        if w0 == push and w1 == mov_r8_r0:
            hits.append(overlay_load + off)
    if len(hits) != 1:
        raise RuntimeError(
            f"ZMove_TryRestoreSlotForEntity: expected 1 match in cave, found {len(hits)} "
            f"({[hex(h) for h in hits]})"
        )
    return hits[0]


def _encode_bl(from_addr: int, to_addr: int) -> int:
    offset = (to_addr - from_addr - 8) >> 2
    if offset < -0x800000 or offset > 0x7FFFFF:
        raise RuntimeError(f"BL out of range: {from_addr:#x} -> {to_addr:#x}")
    return 0xEB000000 | (offset & 0xFFFFFF)


def _resolve_tm_read_cave(state: BuildState | None) -> tuple[int, int] | None:
    """Return (cave_load_address, cave_size) for tm_read ov29 cave."""
    if not state:
        return None
    for mod in state.applied:
        if mod.id != "tm_read":
            continue
        for cave in mod.caves:
            if cave.overlay in ("ov29", "ov36"):
                return cave.load_address, cave.size
    return None


def _patch_tm_read_zmove_restore_calls(
    overlay: bytearray,
    overlay_load: int,
    *,
    tm_read_base: int,
    tm_read_size: int,
    target: int,
) -> list[int]:
    """Retarget tm_read `bl PriorPostValidateRestore` (no-op @ +0x10) to Z-Move restore."""
    prior_noop = tm_read_base + 0x10
    cave_start = tm_read_base - overlay_load
    cave_end = cave_start + tm_read_size
    patched: list[int] = []
    for off in range(cave_start, min(cave_end, len(overlay) - 3), 4):
        w = struct.unpack_from("<I", overlay, off)[0]
        if (w >> 24) != 0xEB:
            continue
        site = overlay_load + off
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        dest = site + 8 + (imm * 4)
        if dest != prior_noop:
            continue
        struct.pack_into("<I", overlay, off, _encode_bl(site, target))
        patched.append(site)
    return patched


def _preferred_arm9_cave(state: BuildState | None) -> int | None:
    # Z gauge trampoline pinned @ file 0xAF2C0 (near GetDungeonResultMsg); not spinda legacy.
    return _parse_fixed("0xAF2C0")


def _assert_z_move_hooks(
    *,
    hooks: list[dict[str, Any]],
    profile: dict[str, Any],
    binaries: dict[str, tuple[bytes, int]],
    prior_hook_sites: set[int],
) -> None:
    for hook in hooks:
        chain = hook.get("chain", "first")
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        blob, load = binaries[bname]
        off = site - load
        if off < 0 or off + 4 > len(blob):
            raise RuntimeError(f"hook {hook['name']} @ {site:#x} out of range")
        if site in prior_hook_sites and chain == "first":
            raise RuntimeError(
                f"hook {hook['name']} @ {site:#x} already used; use chain=append or apply order"
            )
        if chain == "append" and site in prior_hook_sites:
            continue
        word = struct.unpack_from("<I", blob, off)[0]
        if "vanilla_word" in hook:
            expected = hook["vanilla_word"]
            if isinstance(expected, str):
                expected = int(expected, 16)
            if word != expected:
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: expected {expected:#010x}, found {word:#010x}"
                )
            continue
        expected = hook.get("replace")
        if expected:
            kind = hook_word_kind(word)
            if kind != expected:
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: expected {expected}, found {kind or word:#010x}"
                )


def _build_generated_inc(
    *,
    module_id: str,
    ov29_base: int,
    arm9_cave: int,
    prior_execute_move_effect: int,
    prior_is_room_charge_move: int,
    prior_get_room_charge_state: int,
    prior_sub_menu_check: int,
    prior_cleanup_try_restore: int,
    prior_level_up: int,
    prior_restore_pp: int,
    tm_read_integration_source: str,
    room_charge_integration_source: str,
) -> str:
    lines = [
        f"; Auto-generated by true_patches for {module_id}",
        f"; tm_read integration: {tm_read_integration_source}",
        f"; room_charge integration: {room_charge_integration_source}",
        f".definelabel ZMoveOv29CodeAddress, 0x{ov29_base:X}",
        f".definelabel ZMoveArm9GaugeCave, 0x{arm9_cave:X}",
        f"ZGaugeRamAddress equ 0x{ZGAUGE_WRAM:X}",
        f".definelabel ZGauge, ZGaugeRamAddress",
        f".definelabel PriorExecuteMoveEffectCall, 0x{prior_execute_move_effect:X}",
        f".definelabel PriorIsRoomChargeMove, 0x{prior_is_room_charge_move:X}",
        f".definelabel PriorGetRoomChargeState, 0x{prior_get_room_charge_state:X}",
        f".definelabel PriorSubMenuStringCheck, 0x{prior_sub_menu_check:X}",
        f".definelabel PriorCleanupTryRestore, 0x{prior_cleanup_try_restore:X}",
        f".definelabel PriorLevelUp, 0x{prior_level_up:X}",
        f".definelabel PriorRestorePp, 0x{prior_restore_pp:X}",
    ]
    return "\n".join(lines) + "\n"


def patch_strings(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> None:
    strings_cfg = manifest.get("strings") or {}
    doc = load_yaml(module_dir / strings_cfg.get("yaml", "strings.yaml"))
    config = get_ppmdu_config_for_rom(rom)
    for item in doc.get("entries") or []:
        string_id = int(item["id"])
        text = str(item["text"])
        for filename in get_files_from_rom_with_extension(rom, "str"):
            if not filename.endswith("text_e.str"):
                continue
            strings = StrHandler.deserialize(
                rom.getFileByName(filename), string_encoding=config.string_encoding
            )
            strings.strings[string_id] = text
            rom.setFileByName(filename, StrHandler.serialize(strings))


def apply_z_move_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
    state: BuildState | None,
    prior_hook_sites: set[int],
    force_reapply: bool = False,
) -> AppliedModule:
    config = get_ppmdu_config_for_rom(rom)
    hooks_cfg: list[dict[str, Any]] = manifest.get("hooks") or []

    ov29_data = bytearray(_get_binary_bytes(rom, config, "ov29"))
    ov31_data = bytearray(_get_binary_bytes(rom, config, "ov31"))
    ov11_data = bytearray(_get_binary_bytes(rom, config, "ov11"))
    arm9_data = bytearray(_get_binary_bytes(rom, config, "arm9"))

    binaries = {
        "ov29": (bytes(ov29_data), _binary_load(profile, "ov29")),
        "ov31": (bytes(ov31_data), _binary_load(profile, "ov31")),
        "ov11": (bytes(ov11_data), _binary_load(profile, "ov11")),
        "arm9": (bytes(arm9_data), _binary_load(profile, "arm9")),
    }
    if not force_reapply:
        _assert_z_move_hooks(
            hooks=hooks_cfg,
            profile=profile,
            binaries=binaries,
            prior_hook_sites=prior_hook_sites,
        )

    ov29_cave_cfg = manifest.get("ov29_cave") or {}
    arm9_cave_cfg = manifest.get("arm9_cave") or {}

    def _reuse_cave(overlay: str) -> CaveAllocation | None:
        if not force_reapply or state is None:
            return None
        mod = state.get_module(module_id)
        if not mod:
            return None
        for cave in mod.caves:
            if cave.overlay == overlay:
                return cave
        return None

    cave_binary = normalize_cave_binary(ov29_cave_cfg)
    ov36_data = bytearray(get_rom_binary(rom, cave_binary))
    need_bytes = int(ov29_cave_cfg.get("estimated_bytes", 2048))
    ov36_reuse = _reuse_cave(cave_binary)
    if ov36_reuse is not None and ov36_reuse.size >= need_bytes:
        ov29_slot = ov36_reuse
    else:
        ov29_slot, ov36_data = allocate_overlay_cave(
            binary=cave_binary,
            overlay_data=ov36_data,
            profile=profile,
            state=state,
            cave_cfg=ov29_cave_cfg,
            module_id=module_id,
        )
    slot_start = ov29_slot.file_offset
    slot_end = slot_start + ov29_slot.size
    ov36_data[slot_start:slot_end] = bytes(ov29_slot.size)

    arm9_reuse = _reuse_cave("arm9")
    if arm9_reuse is not None:
        arm9_slot = arm9_reuse
    else:
        arm9_slot = allocate_cave(
            bytes(arm9_data),
            _binary_load(profile, "arm9"),
            int(arm9_cave_cfg.get("estimated_bytes", 64)),
            alignment=int(arm9_cave_cfg.get("alignment", 4)),
            preferred_file_offset=_preferred_arm9_cave(state),
            reserved_file_offsets=reserved_file_ranges(state, "arm9"),
            forbidden_file_offsets=parse_forbidden_ranges(arm9_cave_cfg),
            max_file_offset=parse_max_file_offset(arm9_cave_cfg),
            check_vanilla_xrefs=False,
        )

    prior_em = _prior_execute_move_effect_call(
        state,
        profile,
        ov29_data=ov29_data,
        ov29_load=_binary_load(profile, "ov29"),
    )
    prior_irc, irc_src = _prior_is_room_charge_move(state, profile)
    prior_grcs, grcs_src = _prior_get_room_charge_state(state, profile)
    if prior_irc == 0:
        prior_irc = ov29_slot.load_address + ROOM_CHARGE_MOVE_STUB_OFF
        irc_src = "stub"
    if prior_grcs == 0:
        prior_grcs = ov29_slot.load_address + ROOM_CHARGE_STATE_STUB_OFF
        grcs_src = "stub"
    room_charge_src = f"irc={irc_src},grcs={grcs_src}"
    prior_sub, prior_cleanup, prior_level_up, prior_restore_pp, tm_read_src = (
        _resolve_tm_read_integration(state, ov29_slot.load_address)
    )
    # Only validate when chaining to an already-applied tm_read cave (not our own
    # still-empty fallback stubs, which are filled by armips after this point).
    if tm_read_src == "tm_read":
        _assert_code_entry(
            bytes(ov36_data), _binary_load(profile, "ov36"), prior_sub, "PriorSubMenuStringCheck"
        )
        _assert_code_entry(
            bytes(ov36_data),
            _binary_load(profile, "ov36"),
            prior_cleanup,
            "PriorCleanupTryRestore",
        )
        _assert_code_entry(
            bytes(ov36_data),
            _binary_load(profile, "ov36"),
            prior_level_up,
            "PriorLevelUp",
        )
        _assert_code_entry(
            bytes(ov36_data),
            _binary_load(profile, "ov36"),
            prior_restore_pp,
            "PriorRestorePp",
        )
    prior_lines: list[str] = []
    for hook in hooks_cfg:
        prior_label = hook.get("prior_label")
        if not prior_label:
            continue
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        blob, load = binaries[bname]
        off = site - load
        word = struct.unpack_from("<I", blob, off)[0]
        prior = resolve_prior_target(site, word, hook)
        prior_lines.append(f".definelabel {prior_label}, 0x{prior:X}")

    gen_text = _build_generated_inc(
        module_id=module_id,
        ov29_base=ov29_slot.load_address,
        arm9_cave=arm9_slot.load_address,
        prior_execute_move_effect=prior_em,
        prior_is_room_charge_move=prior_irc,
        prior_get_room_charge_state=prior_grcs,
        prior_sub_menu_check=prior_sub,
        prior_cleanup_try_restore=prior_cleanup,
        prior_level_up=prior_level_up,
        prior_restore_pp=prior_restore_pp,
        tm_read_integration_source=tm_read_src,
        room_charge_integration_source=room_charge_src,
    )
    if prior_lines:
        gen_text = gen_text.rstrip("\n") + "\n" + "\n".join(prior_lines) + "\n"

    asm_dir = module_dir / (manifest.get("asm") or {}).get("dir", "asm")
    asm_entry = (manifest.get("asm") or {}).get("entry", "main.asm")

    exports: dict[str, str] = {}
    tm_read_restore_patched: list[int] = []
    restore_sym: str | None = None

    with tempfile.TemporaryDirectory(prefix="true_patches_zmove_") as tmp:
        tmp_path = Path(tmp)
        ov29_path = tmp_path / "overlay_0029.bin"
        ov31_path = tmp_path / "overlay_0031.bin"
        ov11_path = tmp_path / "overlay_0011.bin"
        ov36_path = tmp_path / overlay_filename(cave_binary)
        arm9_path = tmp_path / "arm9.bin"
        ov29_path.write_bytes(bytes(ov29_data))
        ov31_path.write_bytes(bytes(ov31_data))
        ov11_path.write_bytes(bytes(ov11_data))
        ov36_path.write_bytes(bytes(ov36_data))
        arm9_path.write_bytes(bytes(arm9_data))

        gen_inc = tmp_path / "generated.inc"
        write_generated_inc_text(gen_inc, gen_text)

        run_armips_bundle(
            armips=armips,
            asm_dir=asm_dir,
            asm_entry=asm_entry,
            binaries={
                "overlay_0029.bin": ov29_path,
                "overlay_0031.bin": ov31_path,
                "overlay_0011.bin": ov11_path,
                overlay_filename(cave_binary): ov36_path,
                "arm9.bin": arm9_path,
            },
            generated_inc=gen_inc,
        )

        ov29_patched = bytearray(ov29_path.read_bytes())
        ov36_patched = bytearray(ov36_path.read_bytes())
        ov36_load = _binary_load(profile, cave_binary)
        exports = _export_cave_symbols(ov29_cave_cfg, ov29_slot)
        # Re-resolve after assemble — manifest offset drifts when cave code grows.
        restore_addr = _resolve_zmove_try_restore_slot(
            bytes(ov36_patched),
            ov36_load,
            ov29_slot.load_address,
            ov29_slot.size,
        )
        exports["ZMove_TryRestoreSlotForEntity"] = f"0x{restore_addr:X}"
        restore_sym = exports["ZMove_TryRestoreSlotForEntity"]
        tm_read_cave = _resolve_tm_read_cave(state)
        if tm_read_cave and restore_sym:
            tm_base, tm_size = tm_read_cave
            tm_read_restore_patched = _patch_tm_read_zmove_restore_calls(
                ov36_patched,
                ov36_load,
                tm_read_base=tm_base,
                tm_read_size=tm_size,
                target=restore_addr,
            )
            if not tm_read_restore_patched and not force_reapply:
                raise RuntimeError(
                    "tm_read PriorPostValidateRestore BL not found in tm_read cave; "
                    "apply tm_read before z_move_v2"
                )

        _set_binary_bytes(rom, config, "ov29", bytes(ov29_patched))
        _set_binary_bytes(rom, config, "ov31", ov31_path.read_bytes())
        _set_binary_bytes(rom, config, "ov11", ov11_path.read_bytes())
        _set_binary_bytes(rom, config, cave_binary, bytes(ov36_patched))
        _set_binary_bytes(rom, config, "arm9", arm9_path.read_bytes())

    patch_strings(rom, module_dir, manifest)
    ov29_for_shell = bytearray(get_rom_binary(rom, "ov29"))
    shell_meta = patch_shell_move_data(rom, ov29_for_shell, module_dir, manifest)
    write_rom_binary(rom, config, "ov29", bytes(ov29_for_shell))

    hook_records: list[dict[str, Any]] = []
    for hook in hooks_cfg:
        load = _binary_load(profile, hook.get("binary", "ov29"))
        hook_records.extend(collect_hook_records([hook], profile, load))

    zm_data: dict[str, Any] = {
        "cave_base_ov29": f"0x{ov29_slot.load_address:X}",
        "arm9_gauge_cave": f"0x{arm9_slot.load_address:X}",
        "prior_execute_move_effect": f"0x{prior_em:X}",
        "prior_is_room_charge_move": f"0x{prior_irc:X}",
        "prior_get_room_charge_state": f"0x{prior_grcs:X}",
        "room_charge_integration": room_charge_src,
        "tm_read_integration": tm_read_src,
        "shell_move": shell_meta,
        "PriorSubMenuStringCheck": f"0x{prior_sub:X}",
        "PriorCleanupTryRestore": f"0x{prior_cleanup:X}",
    }
    if exports:
        zm_data.update(exports)
    if tm_read_restore_patched and restore_sym:
        zm_data["post_validate_restore_patched_sites"] = [
            f"0x{site:X}" for site in tm_read_restore_patched
        ]
        zm_data["post_validate_restore_patch"] = restore_sym

    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[
            CaveAllocation(
                overlay=cave_binary,
                file_offset=ov29_slot.file_offset,
                size=ov29_slot.size,
                load_address=ov29_slot.load_address,
            ),
            CaveAllocation(
                overlay="arm9",
                file_offset=arm9_slot.file_offset,
                size=arm9_slot.size,
                load_address=arm9_slot.load_address,
            ),
        ],
        hooks=[
            HookRecord(
                name=h["name"],
                site=h["site"],
                kind=h.get("kind", "overwrite"),
                target_symbol=h.get("target_symbol", h["name"]),
                chain=h.get("chain", "first"),
            )
            for h in hook_records
        ],
        data=[zm_data],
    )


def verify_z_move_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    state_mod: AppliedModule | None,
) -> None:
    if not state_mod or len(state_mod.caves) < 2:
        raise AssertionError("z_move state missing combat/arm9 cave allocations")

    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    ov36 = bytes(rom.files[table[36].fileID])
    ov31 = bytes(rom.files[table[31].fileID])
    ov11 = bytes(rom.files[table[11].fileID])
    arm9 = bytes(rom.arm9)

    combat_cave = next(c for c in state_mod.caves if c.overlay in ("ov29", "ov36"))
    arm9_cave = next(c for c in state_mod.caves if c.overlay == "arm9")

    if not any(ov36[combat_cave.file_offset : combat_cave.file_offset + 64]):
        raise AssertionError("z_move ov36 cave empty")
    if not any(arm9[arm9_cave.file_offset : arm9_cave.file_offset + 32]):
        raise AssertionError("z_move arm9 gauge cave empty")

    loads = {
        "ov29": int(profile.get("overlay29_load", OV29_LOAD)),
        "ov31": int(profile.get("overlay31_load", OV31_LOAD)),
        "ov11": int(profile.get("overlay11_load", OV11_LOAD)),
        "arm9": int(profile.get("arm9_load", ARM9_LOAD)),
    }
    blobs = {"ov29": ov29, "ov31": ov31, "ov11": ov11, "arm9": arm9}

    skip_branch_check = {"CalcDamageJudgmentTypeHook"}
    for hook in manifest.get("hooks") or []:
        if hook["name"] in skip_branch_check or not hook.get("target_symbol"):
            continue
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        blob, load = blobs[bname], loads[bname]
        off = site - load
        word = struct.unpack_from("<I", blob, off)[0]
        top = word >> 24
        if top not in (0xEA, 0xEB):
            raise AssertionError(f"hook {hook['name']} @ {site:#x} not branch/bl: {word:#010x}")

    strings_cfg = manifest.get("strings") or {}
    doc = load_yaml(module_dir / strings_cfg.get("yaml", "strings.yaml"))
    for item in doc.get("entries") or []:
        string_id = int(item["id"])
        expected = str(item["text"])
        for filename in get_files_from_rom_with_extension(rom, "str"):
            if filename.endswith("text_e.str"):
                strings = StrHandler.deserialize(rom.getFileByName(filename))
                if strings.strings[string_id] != expected:
                    raise AssertionError(
                        f"string {string_id}: {strings.strings[string_id]!r} != {expected!r}"
                    )
                break

    verify_shell_move_data(rom, ov29, module_dir, manifest)

    load_waza_close_off = 0x020A5F10 - ARM9_LOAD
    load_waza_close_word = struct.unpack_from("<I", arm9, load_waza_close_off)[0]
    if load_waza_close_word != 0xEBFD889F:
        raise AssertionError(
            f"LoadWazaMain close @ 0x020A5F10 should be vanilla CloseBalanceFile BL, "
            f"found {load_waza_close_word:#010x}"
        )
