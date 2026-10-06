# PSP 0.4.10 local fixes

The user confirmed both screenshots came from PSP 0.4.9. This build preserves
the PSP opening, campaign translation, font, portraits and native headers.

## Level Up

The post-battle formatter at module-relative `0xCE26C` writes six skill rows
starting at `0x2C63DC`, originally spaced 32 bytes apart. Full English names
can already exceed that capacity before a level is appended. For example,
“Shield Defense Lv” needs 34 bytes plus its NUL. Subsequent row writes remove
its terminator and join the next name onto it.

`tools/fix_psp_levelup.py` appends a zeroed 1,536-byte array to the PRX load
segment, updates the existing relocated address pair at `0xCE364/0xCE378`,
and changes the stride at `0xCE604` to 256. The other native Level Up path
already has 256-byte rows. Skill learning, numeric levels, flags, formatting
and drawing instructions retain their previous behavior. Full builds apply
this fix through `tools/build_patch.py`.

## Narration

The native scrolling-text routine at `0x171110` copies two-byte glyphs and
their NUL to a 128-byte buffer. It has no bounds check. The prior pixel-only
wrap produced twelve oversized opening/ending lines, which overwrite the
next slot's active flag and metadata. Skipping the narration avoids copying
these lines and explains the user's Start-button workaround.

`tools/insert_text.py::wrap_narration` now requires both an encoded length
of at most 128 bytes, including the terminator, and a width of at most
416 pixels. The longest actual line occupies 127 bytes. Paragraph wording
is unchanged. Opening uses 26 of 32 string slots; ending uses 21 of 24.
The original record delays and end-marker locations are preserved;
spare blank records are redistributed by the existing timing algorithm.

## Verification and reproduction

Reproduce the incremental ISO with `python tools/fix_psp_0410.py` when its
versioned output does not already exist. Source is the verified 0.4.9 ISO.
Run `python tools/verify_psp_0410.py` and
`python tools/verify_text_build.py 0.4.10`.

- All 32 ISO file hashes checked. BOOT.BIN and EBOOT.BIN are identical
  replacements; the other 30 files are byte-identical to 0.4.9.
- All 1,763 translated executable text references and 1,500 English names
  read back correctly.
- Unicorn executes the game's narration copier for all 47 corrected lines.
  Neighboring buffer guards survive; all twelve old oversized lines damage
  the guards. All 124 narration records preserve their native timing.
- A controlled six-skill fixture executes the post-battle row builder,
  native string copies, numeric glyph conversion and stored row pointers.
  Window callbacks and skill getters are supplied by the fixture, and printf
  is simulated. The old rows reproduce joined names; the new rows preserve
  all names, suffixes, NULs and unused bytes. This is not a battle playthrough.
- Fresh boot of the actual 0.4.10 ISO in an isolated PPSSPP instance completed
  the entire opening without Start or a save state, passed the South Pole
  paragraph, and entered Hugo's first prologue dialogue. Captures:
  `work/ui/psp/fixes_0.4.10/opening_2.png`, `opening_after.png`, `prologue.png`.
  The loaded Level Up address relocates to its new array and the runtime
  stride is 256. A full Judau Level Up battle playthrough and hardware PSP
  test have not been performed. The user's emulator was left untouched.

Reports: `work/output/psp_fixes_0.4.10_verification.json` and
`work/output/psp_fixes_0.4.10_native_tests.json`.

ISO: `work/output/SRWMX_EN_0.4.10.iso`, SHA-256
`c4a7eca06a4606426c0f9109c4288ca2db474cb2ac507c7ecb908a0566026444`.
Local testing build only; no release authorization.
