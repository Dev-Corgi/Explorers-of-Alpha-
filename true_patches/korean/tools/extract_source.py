#!/usr/bin/env python3
"""Extract EoS English/Korean string pairs and the ziti font into korean/data.

Korean ROM: apply the unofficial patch to Explorers of Sky (US) first, e.g.
  xdelta3 -d -s "EoS (US).nds" "하늘의 탐험대 1-101b.xdelta" eos_kor.nds

Usage: python extract_source.py <eos_us.nds> <eos_kor.nds>
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

from ndspy.rom import NintendoDSRom

MODULE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MODULE_DIR.parent.parent))

from patch_engine.korean_codec import (  # noqa: E402
    decode_english,
    decode_korean,
    parse_ssb_strings,
    parse_str_file,
    rom_paths,
)


def _dump(path: Path, obj) -> None:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.GzipFile(path, "wb", mtime=0) as fh:
        fh.write(raw)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    eos = NintendoDSRom.fromFile(sys.argv[1])
    kor = NintendoDSRom.fromFile(sys.argv[2])
    out = MODULE_DIR / "data"
    out.mkdir(parents=True, exist_ok=True)

    en = parse_str_file(eos.getFileByName("MESSAGE/text_e.str"))
    ko = parse_str_file(kor.getFileByName("MESSAGE/text_e.str"))
    if len(en) != len(ko):
        raise RuntimeError(f"text_e count {len(en)} != {len(ko)}")
    _dump(out / "text_e.json.gz", {
        "en": [decode_english(s) for s in en],
        "ko": [decode_korean(s) for s in ko],
    })

    scripts: dict[str, dict[str, list[str]]] = {}
    skipped: list[str] = []
    for path in rom_paths(eos, "SCRIPT/", ".ssb"):
        e = parse_ssb_strings(eos.getFileByName(path)).strings
        try:
            k = parse_ssb_strings(kor.getFileByName(path), strict=False).strings
        except (KeyError, ValueError):
            skipped.append(path)
            continue
        if len(e) != len(k):
            skipped.append(path)
            continue
        if e:
            scripts[path] = {
                "en": [decode_english(s) for s in e],
                "ko": [decode_korean(s) for s in k],
            }
    _dump(out / "scripts.json.gz", scripts)
    (out / "ziti.bin").write_bytes(bytes(kor.getFileByName("TOP/ziti")))

    unknown = set()
    for s in ko:
        unknown.update(t for t in decode_korean(s).split("{")[1:])
    print(f"text_e {len(en)} strings, scripts {len(scripts)} files, skipped {skipped}")
    print(f"unknown escapes in text_e: {len(unknown)}")


if __name__ == "__main__":
    main()
