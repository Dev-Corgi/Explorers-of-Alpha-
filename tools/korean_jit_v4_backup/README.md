# korean

Korean text for Explorers of Alpha, ported from the unofficial Explorers of Sky (US) Korean patch (하늘의 탐험대 1-101b).

Build: `python true_patches/build_korean.py` applies this module on top of `Export Rom/Explorers of Alpha_Vanilla+full_stack.nds` and writes `...+full_stack+korean.nds` plus `...+full_stack+korean_untranslated.xlsx`. `--rebuild-full` rebuilds full_stack first. Apply it last; the canonical full_stack stays English.

String matching (EoS English is the text the Korean patch translated):

- text_e.str: same id with equal English, else equal English at the nearest id (Alpha inserted entries), else equal English after an `[M:I..]` icon prefix (the Alpha prefix stays, the body becomes Korean).
- Scripts: same file and index with equal English, else equal English in the same file, else equal English in another EoS script.
- Everything else stays English. The Excel report lists those strings with a similar EoS line and its Korean as a reference, plus review sheets for id-shifted and cross-script matches.

Engine: the Korean patch's arm9 text hooks, with its code moved into an ov36 cave. Glyph bitmaps for the characters in use are built from the patch font `TOP/ziti` and loaded with ov36 at `0x023E0000` (the leftover main RAM past ExtraSpace). ARM9 PU region 2 is moved from `0x023E0000-0x023FFFFF` to `0x023F0000-0x023FFFFF` so melonDS allows those data reads. `FONT/ko_glyph.bin` keeps the same table. Drawing a character is a pointer into that table. The name keyboard is in the same module. Game codes are dense: lead `0x88 + i / 127`, trail `0x80 + i % 127`. English cp1252 characters in 0x88..0x9F (for example ’) become ASCII, and SJIS ♪ and arrows use the Korean glyphs. The ov11/ov14 window constants and the kanji_rd/markfont glyph edits are applied only over vanilla bytes.

Data: `tools/extract_source.py <eos_us.nds> <eos_kor.nds>` regenerates `data/` (EoS English/Korean pairs as Unicode, `ziti.bin`).
