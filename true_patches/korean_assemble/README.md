# korean_assemble

Name-input symbol pairs use the Hangul glyphs present in the Korean dialogue
font. Cave placement remains dynamic and inside the protected ov36 linker hole.

Version 2 reserves a 1024-byte instruction/literal-pool budget plus the actual
generated index, sanitize, glyph-bit and syllable-code tables, aligned to four
bytes. The assembler's `.area` checks that the complete payload fits. The
previous fixed 6144-byte reservation could fail on the current full stack even
though the payload was only about 4 KiB. The Korean build reads this module's
manifest instead of duplicating its configuration.

After building the Korean full stack, run:

```powershell
.venv\Scripts\python.exe -B true_patches\korean_assemble\verify.py
```

The verifier executes both installed ARM9 hooks and the relocated ov36 code for
every generated Hangul pair. It checks the encoded character, cursor and stack,
then deletes the entire two-byte character. Sound and redraw calls use fixtures.
It reads the built ROM without modifying it; it is not a screen-layout test.
