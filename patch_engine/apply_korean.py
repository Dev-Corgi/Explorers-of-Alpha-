"""Apply korean: EoS Korean patch strings matched by English text + ov36 glyph engine.

Glyph bitmaps load with ov36 at 0x023E0000. Drawing is a pointer into that table.
ARM9 PU region 2 is moved to 0x023F0000-0x023FFFFF so those reads are allowed.
"""

from __future__ import annotations

import gzip
import json
import re
import struct
import tempfile
from bisect import bisect, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ndspy.code import loadOverlayTable, saveOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom

from .armips_runner import run_armips_bundle, write_generated_inc_text
from .korean_codec import (
    DenseEncoder,
    build_str_file,
    decode_english,
    parse_ssb_strings,
    parse_str_file,
    rebuild_ssb_strings,
    rom_paths,
)
from .cave_reservations import FileRange
from .overlay_caves import allocate_overlay_cave, get_rom_binary, write_rom_binary
from .state import AppliedModule, BuildState, CaveAllocation, HookRecord

TEXT_E = "MESSAGE/text_e.str"
GLYPH_FILE = "FONT/ko_glyph.bin"
ARM9_LOAD = 0x02000000
OV36_LOAD = 0x023A7080
KO_GLYPH_RAM = 0x023E0000
KO_GLYPH_FILE_OFF = KO_GLYPH_RAM - OV36_LOAD
_TAG_RE = re.compile(r"\[[^\]]*\]")
_LETTER_RE = re.compile(r"[A-Za-z]")
_ICON_PREFIX_RE = re.compile(r"^(?:\[M:[A-Z]+\d+\])+ ?")

# Decision kinds
SAME_ID = "same_id"
MOVED = "moved"
ICON_PREFIX = "icon_prefix"
SAME_FILE = "same_file"
GLOBAL = "global"
SOURCE_ENGLISH = "source_english"
UNMATCHED = "unmatched"
NO_TEXT = "no_text"
USER = "user"
TRANSLATED_KINDS = frozenset({SAME_ID, MOVED, ICON_PREFIX, SAME_FILE, GLOBAL, USER})


def has_text(s: str) -> bool:
    return _LETTER_RE.search(_TAG_RE.sub("", s)) is not None


def split_icon_prefix(s: str) -> tuple[str, str]:
    m = _ICON_PREFIX_RE.match(s)
    return (m.group(0), s[m.end() :]) if m else ("", s)


@dataclass
class Decision:
    kind: str
    ko: str | None = None
    ref: int | str | None = None


@dataclass
class KoreanSource:
    text_en: list[str]
    text_ko: list[str]
    scripts: dict[str, dict[str, list[str]]]
    ziti: bytes
    # Translated report: {"text_e": {id: {en, ko}}, "scripts": {path: {index: {en, ko}}}}
    user: dict[str, Any] = field(default_factory=dict)


@dataclass
class KoreanPlan:
    text_e: list[str]
    text_dec: list[Decision]
    scripts: dict[str, list[str]]
    script_dec: dict[str, list[Decision]]
    expected_eos_id: list[int] = field(default_factory=list)
    # Translations whose English no longer matches the ROM: (path or "text_e", index, en, ko).
    user_stale: list[tuple[str, int, str, str]] = field(default_factory=list)

    def final_text_e(self) -> list[str]:
        return [d.ko if d.ko is not None else s for s, d in zip(self.text_e, self.text_dec)]

    def final_script(self, path: str) -> list[str]:
        return [
            d.ko if d.ko is not None else s
            for s, d in zip(self.scripts[path], self.script_dec[path])
        ]


def _load_gz(path: Path) -> Any:
    with gzip.open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def load_source(module_dir: Path, manifest: dict[str, Any]) -> KoreanSource:
    cfg = manifest.get("data") or {}
    text = _load_gz(module_dir / cfg.get("text_e", "data/text_e.json.gz"))
    scripts = _load_gz(module_dir / cfg.get("scripts", "data/scripts.json.gz"))
    ziti = (module_dir / cfg.get("ziti", "data/ziti.bin")).read_bytes()
    user_path = module_dir / cfg.get("translations", "data/translations.json.gz")
    user = _load_gz(user_path) if user_path.is_file() else {}
    return KoreanSource(text["en"], text["ko"], scripts, ziti, user)


def match_text_e(alpha: list[str], en: list[str], ko: list[str]) -> tuple[list[Decision], list[int]]:
    index: dict[str, list[int]] = defaultdict(list)
    body_index: dict[str, list[int]] = defaultdict(list)
    for i, e in enumerate(en):
        index[e].append(i)
        body = split_icon_prefix(e)[1]
        if has_text(body) and ko[i] != e:
            body_index[body].append(i)
    acount = Counter(alpha)
    anchor_j: list[int] = []
    anchor_d: list[int] = []
    for j, t in enumerate(alpha):
        cands = index.get(t)
        if cands and len(cands) == 1 and acount[t] == 1 and has_text(t):
            anchor_j.append(j)
            anchor_d.append(cands[0] - j)

    def expected(j: int) -> int:
        k = bisect_right(anchor_j, j) - 1
        return j + (anchor_d[k] if k >= 0 else 0)

    out: list[Decision] = []
    exp_ids: list[int] = []
    for j, t in enumerate(alpha):
        exp = expected(j)
        exp_ids.append(exp)
        if not t:
            out.append(Decision(NO_TEXT))
            continue
        texty = has_text(t)
        if j < len(en) and en[j] == t:
            i, kind = j, SAME_ID
        elif texty and t in index:
            i = min(index[t], key=lambda c: (abs(c - exp), c))
            kind = MOVED
        else:
            prefix, body = split_icon_prefix(t)
            if texty and body in body_index:
                i = min(body_index[body], key=lambda c: (abs(c - exp), c))
                out.append(Decision(ICON_PREFIX, prefix + split_icon_prefix(ko[i])[1], i))
            else:
                out.append(Decision(UNMATCHED if texty else NO_TEXT))
            continue
        if ko[i] == en[i]:
            out.append(Decision(SOURCE_ENGLISH if texty else NO_TEXT, None, i))
        else:
            out.append(Decision(kind, ko[i], i))
    return out, exp_ids


def match_scripts(
    alpha: dict[str, list[str]],
    src_scripts: dict[str, dict[str, list[str]]],
) -> dict[str, list[Decision]]:
    glob: dict[str, Counter] = defaultdict(Counter)
    glob_ref: dict[tuple[str, str], str] = {}
    for path, d in src_scripts.items():
        for k, (e, t) in enumerate(zip(d["en"], d["ko"])):
            if e != t:
                glob[e][t] += 1
                glob_ref.setdefault((e, t), f"{path}#{k}")

    out: dict[str, list[Decision]] = {}
    for path, strings in alpha.items():
        d = src_scripts.get(path)
        en = d["en"] if d else []
        ko = d["ko"] if d else []
        idx: dict[str, list[int]] = defaultdict(list)
        for k, e in enumerate(en):
            idx[e].append(k)
        decs: list[Decision] = []
        for k, t in enumerate(strings):
            texty = has_text(t)
            if not t:
                decs.append(Decision(NO_TEXT))
                continue
            if k < len(en) and en[k] == t:
                i, kind = k, SAME_ID
            elif t in idx and texty:
                i = min(idx[t], key=lambda c: (abs(c - k), c))
                kind = SAME_FILE
            elif texty and t in glob:
                best = glob[t].most_common(1)[0][0]
                decs.append(Decision(GLOBAL, best, glob_ref[(t, best)]))
                continue
            else:
                decs.append(Decision(UNMATCHED if texty else NO_TEXT))
                continue
            if ko[i] == en[i]:
                decs.append(Decision(SOURCE_ENGLISH if texty else NO_TEXT, None, f"{path}#{i}"))
            else:
                decs.append(Decision(kind, ko[i], f"{path}#{i}"))
        out[path] = decs
    return out


def read_rom_texts(rom: NintendoDSRom) -> tuple[list[str], dict[str, list[str]]]:
    text = [decode_english(s) for s in parse_str_file(rom.getFileByName(TEXT_E))]
    scripts: dict[str, list[str]] = {}
    for path in rom_paths(rom, "SCRIPT/", ".ssb"):
        strings = parse_ssb_strings(rom.getFileByName(path)).strings
        if strings:
            scripts[path] = [decode_english(s) for s in strings]
    return text, scripts


def _apply_user(
    where: str,
    strings: list[str],
    decs: list[Decision],
    entries: dict[str, dict[str, str]],
    stale: list[tuple[str, int, str, str]],
) -> None:
    for key, ent in entries.items():
        i = int(key)
        if i < len(strings) and strings[i] == ent["en"]:
            decs[i] = Decision(USER, ent["ko"], "translations")
        else:
            stale.append((where, i, ent["en"], ent["ko"]))


def plan_translation(rom: NintendoDSRom, src: KoreanSource) -> KoreanPlan:
    text, scripts = read_rom_texts(rom)
    text_dec, exp_ids = match_text_e(text, src.text_en, src.text_ko)
    script_dec = match_scripts(scripts, src.scripts)
    plan = KoreanPlan(text, text_dec, scripts, script_dec, exp_ids)
    _apply_user("text_e", text, text_dec, src.user.get("text_e") or {}, plan.user_stale)
    for path, entries in (src.user.get("scripts") or {}).items():
        if path in scripts:
            _apply_user(path, scripts[path], script_dec[path], entries, plan.user_stale)
        else:
            plan.user_stale.extend((path, int(k), e["en"], e["ko"]) for k, e in entries.items())
    return plan


def plan_stats(plan: KoreanPlan) -> dict[str, dict[str, int]]:
    text = Counter(d.kind for d in plan.text_dec)
    scr = Counter(d.kind for decs in plan.script_dec.values() for d in decs)
    return {"text_e": dict(text), "scripts": dict(scr)}


# ---------------------------------------------------------------- binaries


def _u32(value: Any) -> int:
    return int(value, 16) if isinstance(value, str) else int(value)


def _branch_target(word: int, pc: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    return pc + 8 + imm * 4


def _is_branch(word: int) -> bool:
    return (word >> 25) & 0x7 == 0b101 and (word >> 28) != 0xF


def _check_arm9_vanilla(arm9: bytes, sites: list[dict[str, Any]], prior: set[int]) -> None:
    for site in sites:
        addr = _u32(site["address"])
        if addr in prior:
            raise RuntimeError(f"korean arm9 site {addr:#x} already hooked by another module")
        word = struct.unpack_from("<I", arm9, addr - ARM9_LOAD)[0]
        if word != _u32(site["vanilla"]):
            raise RuntimeError(
                f"korean arm9 site {addr:#x}: expected vanilla {_u32(site['vanilla']):#010x}, found {word:#010x}"
            )


def check_arm9_patched(arm9: bytes, sites: list[dict[str, Any]], cave_lo: int, cave_hi: int) -> None:
    for site in sites:
        addr = _u32(site["address"])
        word = struct.unpack_from("<I", arm9, addr - ARM9_LOAD)[0]
        if site.get("branch_to_cave"):
            korean = _u32(site["korean"])
            if not _is_branch(word) or (word & 0xFF000000) != (korean & 0xFF000000):
                raise RuntimeError(f"korean arm9 {addr:#x}: {word:#010x} is not the expected branch")
            tgt = _branch_target(word, addr)
            if not cave_lo <= tgt < cave_hi:
                raise RuntimeError(f"korean arm9 {addr:#x}: branch target {tgt:#x} outside cave")
        elif word != _u32(site["korean"]):
            raise RuntimeError(
                f"korean arm9 {addr:#x}: {word:#010x} != Korean patch word {_u32(site['korean']):#010x}"
            )


def _patch_overlay_words(rom: NintendoDSRom, config, words: list[dict[str, Any]]) -> None:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    by_ov: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for w in words:
        by_ov[int(w["overlay"])].append(w)
    for ov_id, items in by_ov.items():
        entry = table[ov_id]
        if entry.compressed:
            raise RuntimeError(f"overlay {ov_id} is compressed")
        data = bytearray(rom.files[entry.fileID])
        for w in items:
            off = _u32(w["address"]) - entry.ramAddress
            cur = struct.unpack_from("<I", data, off)[0]
            if cur != _u32(w["vanilla"]):
                raise RuntimeError(
                    f"korean ov{ov_id} {_u32(w['address']):#x}: expected {_u32(w['vanilla']):#010x}, found {cur:#010x}"
                )
            struct.pack_into("<I", data, off, _u32(w["korean"]))
        if ov_id == 11:
            write_rom_binary(rom, config, "ov11", bytes(data))
        else:
            rom.files[entry.fileID] = bytes(data)


def _patch_files(rom: NintendoDSRom, patches: list[dict[str, Any]]) -> None:
    for p in patches:
        data = bytearray(rom.getFileByName(p["file"]))
        off = _u32(p["offset"])
        old = bytes.fromhex(p["vanilla"])
        new = bytes.fromhex(p["korean"])
        if bytes(data[off : off + len(old)]) != old:
            raise RuntimeError(f"korean {p['file']} @ {off:#x}: bytes differ from vanilla")
        data[off : off + len(new)] = new
        rom.setFileByName(p["file"], bytes(data))


def _write_strings(rom: NintendoDSRom, plan: KoreanPlan, enc: DenseEncoder) -> dict[str, int]:
    finals_text = plan.final_text_e()
    finals_scripts = {p: plan.final_script(p) for p in plan.scripts}
    for s in finals_text:
        enc.collect(s)
    for strings in finals_scripts.values():
        for s in strings:
            enc.collect(s)
    enc.finalize()

    rom.setFileByName(TEXT_E, build_str_file([enc.encode(s) for s in finals_text]))
    changed = 0
    for path, strings in finals_scripts.items():
        data = bytes(rom.getFileByName(path))
        old = parse_ssb_strings(data).strings
        new = [enc.encode(s) for s in strings]
        if new != old:
            rom.setFileByName(path, rebuild_ssb_strings(data, new))
            changed += 1
    return {"scripts_rewritten": changed}


def _embed_ov36_glyphs(rom: NintendoDSRom, config, glyphs: bytes) -> None:
    """Place the glyph table at ExtraSpace end so ov36 load maps it to 0x023E0000.

    PU region 2 is patched to 0x023F0000-0x023FFFFF so melonDS allows those reads.
    """
    ov36 = bytearray(get_rom_binary(rom, "ov36"))
    if len(ov36) > KO_GLYPH_FILE_OFF:
        raise RuntimeError(
            f"ov36 file {len(ov36):#x} already past glyph slot {KO_GLYPH_FILE_OFF:#x}"
        )
    ov36.extend(b"\x00" * (KO_GLYPH_FILE_OFF - len(ov36)))
    ov36.extend(glyphs)
    write_rom_binary(rom, config, "ov36", bytes(ov36))


def _add_glyph_file(rom: NintendoDSRom, data: bytes) -> None:
    """Add FONT/ko_glyph.bin and keep overlay file IDs pointed at the same bytes."""
    folder = rom.filenames.subfolder("FONT")
    if folder is None:
        raise RuntimeError("ROM has no FONT folder")
    name = GLYPH_FILE.split("/")[-1]
    if name in folder.files:
        raise RuntimeError(f"{GLYPH_FILE} already exists")
    insert_at = folder.firstID + bisect(folder.files, name)
    from skytemple_files.common.util import create_file_in_rom

    create_file_in_rom(rom, GLYPH_FILE, data)
    for table_bytes, setter in (
        (rom.arm9OverlayTable, "arm9OverlayTable"),
        (rom.arm7OverlayTable, "arm7OverlayTable"),
    ):
        if not table_bytes:
            continue
        table = loadOverlayTable(table_bytes, lambda _i, _n: b"")
        for entry in table.values():
            if entry.fileID >= insert_at:
                entry.fileID += 1
        setattr(rom, setter, saveOverlayTable(table))


def apply_korean_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
    state: BuildState | None,
    prior_hook_sites: set[int],
) -> AppliedModule:
    config = get_ppmdu_config_for_rom(rom)
    sites: list[dict[str, Any]] = manifest.get("arm9_sites") or []
    arm9 = bytearray(get_rom_binary(rom, "arm9"))
    _check_arm9_vanilla(bytes(arm9), sites, prior_hook_sites)

    src = load_source(module_dir, manifest)
    plan = plan_translation(rom, src)
    enc = DenseEncoder(src.ziti)
    write_info = _write_strings(rom, plan, enc)
    glyphs = enc.glyph_table()

    cave_cfg = dict(manifest.get("cave") or {})
    code_bytes = int(cave_cfg.get("code_bytes", 1280))
    cave_cfg["estimated_bytes"] = code_bytes
    ov36 = get_rom_binary(rom, "ov36")
    slot, ov36 = allocate_overlay_cave(
        binary="ov36",
        overlay_data=ov36,
        profile=profile,
        state=state,
        cave_cfg=cave_cfg,
        module_id=module_id,
    )

    asm_cfg = manifest.get("asm") or {}
    asm_path = module_dir / asm_cfg.get("entry", "asm/main.asm")
    with tempfile.TemporaryDirectory(prefix="true_patches_korean_") as tmp:
        tmp_path = Path(tmp)
        arm9_path = tmp_path / "arm9.bin"
        ov36_path = tmp_path / "overlay_0036.bin"
        arm9_path.write_bytes(bytes(arm9))
        ov36_path.write_bytes(bytes(ov36))
        gen_inc = tmp_path / "generated.inc"
        write_generated_inc_text(
            gen_inc,
            f"; Auto-generated by true_patches for {module_id}\n"
            f".definelabel KoreanCaveAddress, 0x{slot.load_address:X}\n"
            f"KoreanCaveSize equ 0x{slot.size:X}\n"
            f".definelabel KoGlyphTable, 0x{KO_GLYPH_RAM:X}\n"
            f"KoGlyphCount equ {enc.glyph_count}\n",
        )
        run_armips_bundle(
            armips=armips,
            asm_dir=asm_path.parent,
            asm_entry=asm_path.name,
            binaries={
                "arm9.bin": arm9_path,
                "overlay_0036.bin": ov36_path,
            },
            generated_inc=gen_inc,
        )
        arm9_out = arm9_path.read_bytes()
        ov36_out = ov36_path.read_bytes()

    cave_hi = slot.load_address + slot.size
    check_arm9_patched(arm9_out, sites, slot.load_address, cave_hi)
    if len(glyphs) != enc.glyph_count * 0x1C:
        raise RuntimeError(f"korean glyph file is {len(glyphs)} bytes for {enc.glyph_count} glyphs")

    write_rom_binary(rom, config, "arm9", arm9_out)
    write_rom_binary(rom, config, "ov36", ov36_out)
    _add_glyph_file(rom, glyphs)
    _patch_overlay_words(rom, config, manifest.get("overlay_words") or [])
    _patch_files(rom, manifest.get("file_patches") or [])

    from .apply_korean_assemble import apply_korean_assemble_module

    assemble = apply_korean_assemble_module(
        module_id=module_id,
        module_dir=module_dir.parent / "korean_assemble",
        manifest={"cave": {"estimated_bytes": 6144, "alignment": 4}, "asm": {"entry": "asm/main.asm"}},
        profile=profile,
        rom=rom,
        armips=armips,
        state=state,
        prior_hook_sites=prior_hook_sites,
        glyph_count=enc.glyph_count,
        extra_reserved=[FileRange(slot.file_offset, slot.file_offset + slot.size)],
    )
    _embed_ov36_glyphs(rom, config, glyphs)

    hooks = [
        HookRecord(
            name=str(s.get("name") or f"KoArm9_{_u32(s['address']):08X}"),
            site=_u32(s["address"]),
            kind="branch" if s.get("branch_to_cave") else "overwrite",
            target_symbol=str(s.get("name") or "korean"),
            chain="first",
        )
        for s in sites
        if s.get("name")
    ]
    stats = plan_stats(plan)
    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[
            CaveAllocation(
                overlay="ov36",
                file_offset=slot.file_offset,
                size=slot.size,
                load_address=slot.load_address,
            ),
            *assemble.caves,
            CaveAllocation(
                overlay="ov36",
                file_offset=KO_GLYPH_FILE_OFF,
                size=len(glyphs),
                load_address=KO_GLYPH_RAM,
            ),
        ],
        hooks=[*hooks, *assemble.hooks],
        data=[
            {
                "glyph_count": enc.glyph_count,
                "glyph_file": GLYPH_FILE,
                "glyph_bytes": len(glyphs),
                "glyph_ram": f"0x{KO_GLYPH_RAM:X}",
                "glyph_file_offset": f"0x{KO_GLYPH_FILE_OFF:X}",
                "text_e": stats["text_e"],
                "scripts": stats["scripts"],
                "translations_stale": len(plan.user_stale),
                "sanitized": enc.stats.sanitized,
                "unmapped": enc.stats.unmapped,
                **write_info,
                **assemble.data[0],
            }
        ],
    )


def verify_korean_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any],
    mod_state: AppliedModule | None,
) -> None:
    if not mod_state or not mod_state.caves:
        raise AssertionError("korean state missing ov36 cave")
    cave = mod_state.caves[0]
    rom = NintendoDSRom(rom_path.read_bytes())
    check_arm9_patched(
        bytes(rom.arm9),
        manifest.get("arm9_sites") or [],
        cave.load_address,
        cave.load_address + cave.size,
    )
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov36 = bytes(rom.files[table[36].fileID])
    if not any(ov36[cave.file_offset : cave.file_offset + 0x40]):
        raise AssertionError("korean ov36 cave empty")
    blob = rom.getFileByName(GLYPH_FILE)
    count = int(mod_state.data[0]["glyph_count"])
    want = count * 0x1C
    if len(blob) != want:
        raise AssertionError(f"korean glyph file is {len(blob)} bytes, expected {want}")
    if len(ov36) < KO_GLYPH_FILE_OFF + want:
        raise AssertionError(
            f"ov36 file {len(ov36):#x} missing glyph table at {KO_GLYPH_FILE_OFF:#x}"
        )
    if ov36[KO_GLYPH_FILE_OFF : KO_GLYPH_FILE_OFF + want] != blob:
        raise AssertionError("ov36 glyph table does not match FONT/ko_glyph.bin")
    if table[36].ramSize < KO_GLYPH_FILE_OFF + want:
        raise AssertionError(
            f"ov36 ramSize {table[36].ramSize:#x} does not cover the glyph table"
        )
    from .apply_korean_assemble import verify_korean_assemble_module

    verify_korean_assemble_module(rom_path, module_dir.parent / "korean_assemble", manifest, mod_state)
    for w in manifest.get("overlay_words") or []:
        entry = table[int(w["overlay"])]
        data = bytes(rom.files[entry.fileID])
        cur = struct.unpack_from("<I", data, _u32(w["address"]) - entry.ramAddress)[0]
        if cur != _u32(w["korean"]):
            raise AssertionError(f"korean ov{w['overlay']} {_u32(w['address']):#x} = {cur:#010x}")
    text = parse_str_file(rom.getFileByName(TEXT_E))
    lead = sum(1 for s in text if any(0x88 <= b <= 0x9E for b in s))
    if lead < len(text) // 4:
        raise AssertionError(f"korean text_e has only {lead} Korean strings")
