#!/usr/bin/env python3
"""Generate PATCHNOTES.md section for damage_formula."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load_move_names():
    from ndspy.rom import NintendoDSRom
    from skytemple_files.common.util import get_ppmdu_config_for_rom
    from skytemple_files.data.str.handler import StrHandler

    rom = NintendoDSRom.fromFile(str(REPO / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"))
    config = get_ppmdu_config_for_rom(rom)
    block = config.string_index_data.string_blocks["Move Names"]
    strs = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=config.string_encoding
    )
    return {
        mid: strs.strings[block.begin + mid].strip()
        for mid in range(block.end - block.begin + 1)
        if strs.strings[block.begin + mid].strip()
    }


def load_power_rows():
    from ndspy.rom import NintendoDSRom
    from skytemple_files.data.waza_p.handler import WazaPHandler

    names = load_move_names()
    rom = NintendoDSRom.fromFile(str(REPO / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"))
    wp = WazaPHandler.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    new = {
        int(k): int(v)
        for k, v in json.loads(
            (REPO / "true_patches/damage_formula/data/gen9_powers_by_move_id.json").read_text()
        ).items()
    }
    rows = []
    for mid, powv in sorted(new.items()):
        if mid >= len(wp.moves):
            continue
        vanilla = int(wp.moves[mid].base_power)
        if vanilla != powv:
            rows.append((names.get(mid, f"기술#{mid}"), vanilla, powv))
    return rows


def throwable_rows():
    import struct

    from ndspy.rom import NintendoDSRom
    from skytemple_files.common.util import get_binary_from_rom, get_ppmdu_config_for_rom

    labels = {
        "STICK_POWER": "나뭇가지",
        "IRON_THORN_POWER": "철 가시",
        "SILVER_SPIKE_POWER": "은 가시",
        "CACNEA_SPIKE_POWER": "선인장 가시",
        "CORSOLA_TWIG_POWER": "코산호 가지",
        "GOLD_FANG_POWER": "금니",
        "GOLD_THORN_POWER": "금 가시",
        "GEO_PEBBLE_POWER": "돌멩이",
        "GRAVELEROCK_POWER": "자갈",
        "RARE_FOSSIL_POWER": "희귀한 화석",
        "BLAST_SEED_DAMAGE_A": "폭탄땅콩",
        "BLAST_SEED_DAMAGE_B": "폭탄땅콩(보조)",
    }
    rom = NintendoDSRom.fromFile(str(REPO / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"))
    config = get_ppmdu_config_for_rom(rom)
    ov10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
    entries = json.loads(
        (REPO / "true_patches/damage_formula/data/throwable_ov10.json").read_text()
    )
    rows = []
    seen = set()
    for ent in entries:
        key = ent["name"]
        if key.endswith("_B"):
            continue
        label = labels.get(key, key)
        fo = int(ent["file_offset"], 16)
        old = struct.unpack_from("<H", ov10, fo)[0]
        new = int(ent["value"])
        if label in seen:
            continue
        seen.add(label)
        rows.append((label, old, new))
    return rows


def exclusive_rows():
    data = json.loads(
        (REPO / "true_patches/damage_formula/data/exclusive_rebalance.json").read_text()
    )
    label = {
        "regular attack": "일반 공격(기본 타격)",
        "projectile": "투사체(던지기 껍데기)",
    }
    return [
        (label.get(e["name"], e["name"]), e["old"], e["new"])
        for e in data
        if e["old"] != e["new"]
    ]


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def main():
    power_rows = load_power_rows()
    throw_rows = throwable_rows()

    lines = [
        "# 패치노트",
        "",
        "## damage_formula v5",
        "",
        "탐험대 데미지·기술 위력·던지기 아이템을 9세대 본편 기준에 맞춘 통합 패치입니다.",
        "",
        "### 시스템 변경",
        "",
        "- 데미지 기본 공식 | 탐험대 전용 공식 → 본편식 `((2×레벨/5+2)×위력×공격÷방어÷50)+2` 후, 타입·STAB·급소·랜덤(±12.5%)은 기존과 동일하게 적용",
        "- 적 포켓몬 공격 | 추가 보정 없음 → 아군이 아닌 공격자는 ×64/85 패널티",
        "- 특성 **기술자** | 위력 4 이하 기술만 1.5배 → **위력 60 이하** 기술까지 1.5배",
        "- **일반 공격** | 고정 데미지 처리 → 해당 포켓몬 기본 공격 위력의 **25%**로 계산",
        "- **투사체** 데미지 | 계산 후 ×0.5 → ×1.0",
        "- **급소·날씨 보정** | 일반 급소, 맑음+불꽃, 비+물 타입 | ×1.25 → ×1.5",
        "- 기술 설명 **위력 별표** | 구간별 별 개수 → **20 위력당 ★1**, **10 위력당 ★½** (IQ와 같은 반별 표시)",
        "- **돌멩이·자갈·희귀한 화석** | 고정 데미지 → 본편 데미지 공식을 거치는 투사체로 변경",
        "",
        "### v5 추가 조정 (v4 대비)",
        "",
        "- **Thrash** | 위력 120 → 50",
        "- **Outrage** | 위력 120 → 50",
        "- **Petal Dance** | 위력 120 → 50",
        "- **Raging Fury** | 위력 120 → 50",
        "- **Self-Destruct** | (고정 데미지) → 위력 **120**",
        "- **Explosion** | 위력 250 → **150**",
        "",
        "### 던지기·폭탄땅콩",
        "",
        md_table(["아이템", "변경 전", "변경 후"], throw_rows),
        "",
        "- **폭탄땅콩** | 고정 25 데미지 → 위력 80 투사체(본편 공식 적용)",
        "",
    ]

    out = REPO / "PATCHNOTES.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(power_rows)} move rows)")


if __name__ == "__main__":
    main()
