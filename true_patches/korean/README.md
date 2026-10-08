# korean

Korean text for Explorers of Alpha, ported from the unofficial Explorers of Sky (US) Korean patch (하늘의 탐험대 1-101b).

Build, only when requested: `.venv\Scripts\python.exe patch_engine\build_korean.py --rebuild-full` rebuilds the English full_stack from `PatchTesting/Explorers of Alpha/Explorers of Alpha.nds`, then writes `PatchTesting/Export Rom/Explorers of Alpha+_kor.nds`. Apply Korean last. The build keeps its state in a temporary directory.

String matching (EoS English is the text the Korean patch translated):

- text_e.str: same id with equal English, else equal English at the nearest id (Alpha inserted entries), else equal English after an `[M:I..]` icon prefix (the Alpha prefix stays, the body becomes Korean).
- Scripts: same file and index with equal English, else equal English in the same file, else equal English in another EoS script.
- Everything else stays English. The Excel report lists those strings with a similar EoS line and its Korean as a reference, plus review sheets for id-shifted and cross-script matches.

Engine: the Korean patch's arm9 text hooks, with its code moved into an ov36 cave. Glyph bitmaps for the characters in use are built from the patch font `TOP/ziti` and loaded with ov36 at `0x023E0000` (the leftover main RAM past ExtraSpace). ARM9 PU region 2 is moved from `0x023E0000-0x023FFFFF` to `0x023F0000-0x023FFFFF` so melonDS allows those data reads. `FONT/ko_glyph.bin` keeps the same table. Drawing a character is a pointer into that table. The name keyboard is in the same module. Game codes are dense: lead `0x88 + i / 127`, trail `0x80 + i % 127`. English cp1252 characters in 0x88..0x9F (for example ’) become ASCII, and SJIS ♪ and arrows use the Korean glyphs. The ov11/ov14 window constants and the kanji_rd/markfont glyph edits are applied only over vanilla bytes.

Data: `tools/extract_source.py <eos_us.nds> <eos_kor.nds>` regenerates `data/` (EoS English/Korean pairs as Unicode, `ziti.bin`).


JIT compatibility candidate (v5): glyph rendering keeps its pointer in the existing
stack frame at sp+0x4D0 instead of writing ARM9 code at 0x020254C4. Character
measurement loads Ko_SkipTrail through a saved register; only its immutable address
is a PC-relative literal. This avoids folding changing values into JIT constants
in both melonDS x64 and ARM64 backends. It does not claim to fix every JIT issue.

The historical v4-to-v5 updater described below does not include the v6 text-safety fixes.
To update an existing v4 Korean ROM while retaining every translation and other
game edit, run `python -B tools/build_korean_jit_compat.py input.nds output.nds`.
The updater checks the saved v4 assembly against the input, retains the existing
cave allocation, and changes only ARM9 hook words and the Korean engine cave.
The original ROM and extracted files are retained. Android melonDS with JIT ON
still requires an on-device gameplay test.

## Text safety (v6)

The second PreprocessString character copier now recognizes dense Korean pairs,
while preserving legacy symbols. Previously a Korean trail such as `0x87` could
consume the NUL after Crystal Crossing and continue into a stale weather message.
The number tag in that stale message was evaluated without caller arguments,
causing an ARM9 data abort. Width/draw/read hooks also reject malformed trails;
`%c` now takes an integer character code in lead/trail order.

Seventeen general-message translations have corrected runtime tags in
`data/translations.json.gz`. Numbered lowercase tags keep their original type and
slot; order and repetitions may change. Empty indices mean zero. Uppercase layout
tags are not required to match. Unmatched brackets and NULs are rejected as well.
Whitespace-only source strings stay blank. The importer rejects invalid new
translations, and application refuses unsafe translations until they are repaired.

The audit's 259 script entries are repaired in `data/translations.json.gz`.
Most fixes restore `[team:]` in place of `[team]`: the former selects the caller's
team slot, while the latter reads the current player's team. The remaining fixes
restore damaged placeholder/greeting prefixes and the received-item slot.
`audit/translation_repairs.json` retains each before/after pair and its reason;
`audit/translation_issues.json` contains the remaining validation failures.
The repairs do not join or split dialogue entries. These are structural checks,
not a certification of all translation meaning or layout.
Adjacent entries in the same Shaymin Village script also contained four empty
translations, incorrect Yes/No labels and unrelated/truncated text. Another 52
entries were restored against their own English and surrounding dialogue, for
311 script corrections in total. The original dialogue indices are retained.

Run these read-only checks from the repository root:

```powershell
.venv\Scripts\python.exe -B true_patches\korean\tools\verify_text_safety.py
.venv\Scripts\python.exe -B true_patches\korean\tools\audit_translations.py
```

The ARM execution check uses Unicorn (also available in
`tools/.korean_jit_test_deps`), assembles only temporary binary fixtures, verifies
manifest hooks, reproduces the original crash, and exercises all 2,921 dense
character combinations. It does not write a ROM or replace an Android gameplay test.
