"""Map name-keyboard symbol pairs onto Hangul that already has a glyph."""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom

from .apply_korean import load_source, plan_translation
from .armips_runner import run_armips_bundle, write_generated_inc_text
from .korean_codec import DENSE_PER_LEAD, LEAD_MIN, ZITI_TO_CHAR, DenseEncoder
from .manifest import load_module_manifest
from .overlay_caves import allocate_overlay_cave, get_rom_binary, write_rom_binary
from .state import AppliedModule, BuildState, CaveAllocation, HookRecord

ARM9_LOAD = 0x02000000
PAGE0 = 0x0209BF18
PAGE1 = 0x0209BBC4
ONKEY_SITE = 0x020384D8
ONKEY_VANILLA = 0xE2440F41
DEL_SITE = 0x02038904
DEL_VANILLA = 0xE92D4008
SYM_COUNT = 78

# Lead-byte keys swallow the next byte. Left alone next to a normal
# character, they become a single ASCII stand-in instead.
SANITIZE = {
    0x8A: ord("S"),
    0x8C: ord("O"),
    0x8E: ord("Z"),
    0x91: ord("'"),
    0x92: ord("'"),
    0x93: ord('"'),
    0x94: ord('"'),
    0x9A: ord("s"),
    0x9C: ord("o"),
    0x9E: ord("z"),
    0x9F: ord("Y"),
}


def _u32(buf: bytes, addr: int) -> int:
    return struct.unpack_from("<I", buf, addr - ARM9_LOAD)[0]


def _branch_target(word: int, addr: int) -> int:
    imm = word & 0x00FFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def _full_stack_rom(repo: Path) -> Path:
    return repo / "PatchTesting" / "Export Rom" / "Explorers of Alpha+.nds"


def _dialogue_syllables(repo: Path, glyph_count: int) -> list[tuple[str, int]]:
    korean_dir = repo / "true_patches" / "korean"
    src = load_source(korean_dir, load_module_manifest(korean_dir))
    plan = plan_translation(NintendoDSRom.fromFile(str(_full_stack_rom(repo))), src)
    enc = DenseEncoder(src.ziti)
    for text in plan.final_text_e():
        enc.collect(text)
    for path in plan.scripts:
        for text in plan.final_script(path):
            enc.collect(text)
    enc.finalize()
    if enc.glyph_count != glyph_count:
        raise RuntimeError(
            f"dialogue glyph count {enc.glyph_count} != korean module {glyph_count}"
        )
    chosen: dict[str, int] = {}
    for code in enc._order:
        ch = ZITI_TO_CHAR.get(code)
        if ch is None or len(ch) != 1 or not ("\uac00" <= ch <= "\ud7a3"):
            continue
        dense = enc._dense[code]
        if ch not in chosen or dense < chosen[ch]:
            chosen[ch] = dense
    return sorted(chosen.items(), key=lambda item: ord(item[0]))


def _symbol_keys(arm9: bytes) -> list[int]:
    found: list[tuple[int, int, int, int]] = []
    for page_i, page in enumerate((PAGE0, PAGE1)):
        for key in range(84):
            off = page - ARM9_LOAD + key * 10
            code = struct.unpack_from("<H", arm9, off + 8)[0]
            if code < 0x80 or code > 0xFF:
                continue
            found.append((page_i, arm9[off + 5], arm9[off + 4], code))
    found.sort()
    codes = [code for _page, _y, _x, code in found]
    if len(codes) != SYM_COUNT or len(set(codes)) != SYM_COUNT:
        raise RuntimeError(f"expected {SYM_COUNT} distinct symbol keys, found {codes}")
    missing = [code for code in codes if 0x88 <= code <= 0x9F and code not in SANITIZE]
    if missing:
        raise RuntimeError(f"lead-byte keys without a stand-in: {missing}")
    return codes


def _tables(symbols: list[int], syllables: list[tuple[str, int]], glyph_count: int) -> dict[str, bytes]:
    index = bytearray([0xFF]) * 256
    for i, code in enumerate(symbols):
        index[code] = i
    sanitize = bytearray(256)
    for code, repl in SANITIZE.items():
        sanitize[code] = repl
    bits = bytearray((glyph_count + 7) // 8)
    for _ch, dense in syllables:
        lead = dense >> 8
        trail = dense & 0xFF
        idx = (lead - LEAD_MIN) * DENSE_PER_LEAD + (trail - 0x80)
        if not 0 <= idx < glyph_count:
            raise RuntimeError(f"dense code {dense:#x} is outside the glyph table")
        bits[idx >> 3] |= 1 << (idx & 7)
    codes = bytearray()
    for _ch, dense in syllables:
        codes += struct.pack("<H", dense)
    return {"index": bytes(index), "sanitize": bytes(sanitize), "bits": bytes(bits), "codes": bytes(codes)}


def _write_pairs_md(path: Path, symbols: list[int], syllables: list[tuple[str, int]]) -> None:
    chars = [bytes([code]).decode("cp1252") for code in symbols]
    lines = [
        "# 이름 입력의 기호 조합",
        "",
        "한글 빌드의 이름 키보드에서, 기호나 악센트 키 두 개를 누르면 대화에 그림이 있는 한글 한 글자가 된다. 새 그림은 없다.",
        "",
        "키 순서는 기본 문자판 맨 아래 기호, 그다음 악센트 문자판을 왼쪽 위부터이다. 앞 글자 번호에 78을 곱하고 뒤 글자 번호를 더한 값이 아래 표의 순서다. 그 값이 음절 수를 넘으면 한글이 되지 않고, 두 기호가 그대로 남는다.",
        "",
        "영문, 숫자, 쉼표, 마침표, `!`, `?`는 그대로다. 기호 다음에 그런 글자를 누르면, 앞 글자가 다음 바이트를 삼키는 코드면 비슷한 영문으로 바뀐다. `Š→S`, `Œ→O`, `Ž→Z`, `š→s`, `œ→o`, `ž→z`, `Ÿ→Y`, 따옴표는 `'` 또는 `\"`이다.",
        "",
        "한글 한 글자는 두 바이트다. 커서가 그 글자 바로 뒤에 있을 때 지우면 두 바이트가 함께 지워진다.",
        "",
        "기호 번호:",
        "",
    ]
    for i, ch in enumerate(chars):
        lines.append(f"{i}. `{ch}`")
    lines.append("")
    pair_i = 0
    current = None
    for first_i, first in enumerate(chars):
        for second_i, second in enumerate(chars):
            if pair_i >= len(syllables):
                break
            if first != current:
                lines.append(f"## 앞 글자 `{first}`")
                lines.append("")
                lines.append("| 뒤 글자 | 한글 |")
                lines.append("| --- | --- |")
                current = first
            lines.append(f"| `{second}` | {syllables[pair_i][0]} |")
            pair_i += 1
        if pair_i >= len(syllables):
            break
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _data_asm(tables: dict[str, bytes]) -> str:
    def blob(name: str, data: bytes) -> str:
        rows = []
        for i in range(0, len(data), 16):
            chunk = ", ".join(str(b) for b in data[i : i + 16])
            rows.append(f".byte {chunk}")
        return f"{name}:\n" + "\n".join(rows)

    return (
        ".align 4\n"
        + blob("Ka_SymIndex", tables["index"])
        + "\n.align 4\n"
        + blob("Ka_Sanitize", tables["sanitize"])
        + "\n.align 4\n"
        + blob("Ka_Bits", tables["bits"])
        + "\n.align 4\n"
        + "Ka_Codes:\n"
        + "\n".join(
            ".dh " + ", ".join(str(struct.unpack_from("<H", tables["codes"], i)[0]) for i in range(off, min(off + 16, len(tables["codes"])), 2))
            for off in range(0, len(tables["codes"]), 16)
        )
        + "\n"
    )


def apply_korean_assemble_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
    state: BuildState | None,
    prior_hook_sites: set[int],
    glyph_count: int | None = None,
    extra_reserved: list | None = None,
) -> AppliedModule:
    for site in (ONKEY_SITE, DEL_SITE):
        if site in prior_hook_sites:
            raise RuntimeError(f"korean_assemble site {site:#x} is already hooked")
    if glyph_count is None:
        if state is None or state.get_module("korean") is None:
            raise RuntimeError("korean_assemble requires the korean glyph count")
        glyph_count = int(state.get_module("korean").data[0]["glyph_count"])
    repo = module_dir.parent.parent
    syllables = _dialogue_syllables(repo, glyph_count)
    if not syllables:
        raise RuntimeError("no dialogue syllables to assemble")
    arm9 = bytearray(get_rom_binary(rom, "arm9"))
    if _u32(arm9, ONKEY_SITE) != ONKEY_VANILLA or _u32(arm9, DEL_SITE) != DEL_VANILLA:
        raise RuntimeError("korean_assemble sites are not vanilla")
    symbols = _symbol_keys(bytes(arm9))
    tables = _tables(symbols, syllables, glyph_count)
    _write_pairs_md(module_dir / "pairs.md", symbols, syllables)

    cave_cfg = dict(manifest.get("cave") or {})
    ov36 = get_rom_binary(rom, "ov36")
    slot, ov36 = allocate_overlay_cave(
        binary="ov36",
        overlay_data=ov36,
        profile=profile,
        state=state,
        cave_cfg=cave_cfg,
        module_id=module_id,
        extra_reserved=extra_reserved,
    )
    asm_cfg = manifest.get("asm") or {}
    asm_path = module_dir / asm_cfg.get("entry", "asm/main.asm")
    data_path = asm_path.parent / "ka_data.asm"
    try:
        data_path.write_text(_data_asm(tables), encoding="ascii")
        with tempfile.TemporaryDirectory(prefix="true_patches_korean_assemble_") as tmp:
            tmp_path = Path(tmp)
            arm9_path = tmp_path / "arm9.bin"
            ov36_path = tmp_path / "overlay_0036.bin"
            arm9_path.write_bytes(bytes(arm9))
            ov36_path.write_bytes(bytes(ov36))
            gen = tmp_path / "generated.inc"
            write_generated_inc_text(
                gen,
                f"; Auto-generated by true_patches for {module_id}\n"
                f".definelabel KaCaveAddress, 0x{slot.load_address:X}\n"
                f"KaCaveSize equ 0x{slot.size:X}\n"
                f"KaGlyphMax equ {glyph_count}\n"
                f"KaPairCount equ {len(syllables)}\n",
            )
            run_armips_bundle(
                armips=armips,
                asm_dir=asm_path.parent,
                asm_entry=asm_path.name,
                binaries={"arm9.bin": arm9_path, "overlay_0036.bin": ov36_path},
                generated_inc=gen,
            )
            arm9_out = arm9_path.read_bytes()
            ov36_out = ov36_path.read_bytes()
    finally:
        data_path.unlink(missing_ok=True)

    config = get_ppmdu_config_for_rom(rom)
    write_rom_binary(rom, config, "arm9", arm9_out)
    write_rom_binary(rom, config, "ov36", ov36_out)
    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[
            CaveAllocation(
                overlay="ov36",
                file_offset=slot.file_offset,
                size=slot.size,
                load_address=slot.load_address,
            )
        ],
        hooks=[
            HookRecord("Ka_OnKey", ONKEY_SITE, "branch", "Ka_OnKey", "first"),
            HookRecord("Ka_Del", DEL_SITE, "branch", "Ka_Del", "first"),
        ],
        data=[
            {
                "pair_count": len(syllables),
                "symbol_count": len(symbols),
                "glyph_count": glyph_count,
                "first_keys": f"{symbols[0]:02X}+{symbols[0]:02X}",
                "first_dense": f"0x{syllables[0][1]:04X}",
            }
        ],
    )


def verify_korean_assemble_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any],
    mod_state,
) -> None:
    if mod_state is None or not mod_state.caves:
        raise AssertionError("korean_assemble state missing")
    rom = NintendoDSRom.fromFile(str(rom_path))
    arm9 = bytes(rom.arm9)
    caves = list(mod_state.caves)
    for addr in (ONKEY_SITE, DEL_SITE):
        word = _u32(arm9, addr)
        if (word >> 24) != 0xEA:
            raise AssertionError(f"korean_assemble hook {addr:#x} is not a branch")
        target = _branch_target(word, addr)
        if not any(c.load_address <= target < c.load_address + c.size for c in caves):
            raise AssertionError(f"korean_assemble hook {addr:#x} misses the cave")
    info = next((item for item in mod_state.data if "pair_count" in item), mod_state.data[0])
    if info["symbol_count"] != SYM_COUNT or info["pair_count"] <= 0:
        raise AssertionError(f"korean_assemble table is empty: {info}")
