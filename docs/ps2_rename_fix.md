# PS2 unit rename corruption — local v0.4.43

The reported Garmraid Blaze screen has the same underlying editor-capacity
problem fixed on PSP in v0.4.38. That correction was platform-specific; PS2
still placed Reading only 23 bytes after Name and allowed 11/six characters.
The 14-character English upgrade name crosses that boundary, so loading
Reading overwrites the name's tail and the editor interprets the remaining
bytes as unrelated glyphs. Native initialization reproduces the corruption.

The PS2 fix repacks the existing 48-byte editor area into Name at `+0x634`
(31 bytes, 15 characters) and Reading at `+0x653` (17 bytes, eight characters).
Controls still start at `+0x664`. Initialization, reset, rendering, limits,
typing, deletion, spaces, cursor arithmetic, validation and export use the
same new layout. The object allocation and existing 32-byte save slots do
not change. A native termination guard caps legacy loaded defaults before
the original length/padding logic. The editable Cerberus default becomes
**Cerberus Ignite**, matching the existing PSP fix and documented Akurasu
Pilot Database spelling; other database names remain as recorded.

Name's value moves from x92 to x116, Reading's from x456 to x476. Labels stay
at x44/x372. The native width measurement with a 28-pixel font gives Name
64.17 pixels and Reading 87.5 pixels, leaving gaps before both values.
The enlarged fields also need tighter underline spacing. A private scalar
helper uses 14/16/20-pixel Latin/digit/kanji cells, following the native logical
width budgets without modifying shared spacing constants or other screens.
The 15/eight Latin underlines end at x326/x588. Actual native window draws
and VWF widths for both upgraded defaults clear the adjacent boundaries.

`tools/fix_ps2_rename.py` guards the original instruction/data words, updates
the font segment and heap metadata, and checks idempotence. Both regular PS2
build paths apply it after text refresh and before the title footer.
`tools/verify_ps2_rename.py` executes the actual native initializer, string
copy/length, padding loop, window/underline drawing, editing and export:

- all four robot defaults, reset and saved-name modes;
- maximum-length names and the legacy Cerberus default;
- typing, deletion and spaces at the first/middle/last position of both fields;
- unchanged adjacent fields, control guards and save-slot boundaries;
- actual font widths, value origins, underline positions and repeat patching.

The fixture supplies the standard byte-concatenation service for the game's
EE packed-instruction libc `strcat`; the editor's calling loop runs normally.
Graphics services capture native draw arguments instead of rendering GS pixels.
These checks do not replace fresh PCSX2 visual acceptance, which remains pending.
The user's running emulator and memory cards were left untouched.

`tools/build_ps2_rename.py` uses local PS2 v0.4.41 as the verified baseline,
appends the corrected executable, and keeps ISO9660/UDF directory views and
volume sizes in agreement. It verifies every other disc byte outside the
required filesystem metadata, all 37 resources, exact executable readback,
registered executable changes, native font regressions and 42 title-state
cases. The actual ISO footer is regenerated and checked as **v0.4.43** with
**github.com/retro-trans**. Existing caption/header/story fixes are preserved.

Test ISO: `work/output/SRWMX_PS2_EN_0.4.43.iso`.
SHA256: `36e73a20b15af2b80f74f057f57bcfe03cc2e5e17a4dddd49fb3050f4697865f`.
Evidence: `work/output/ps2_rename_0.4.43_verification.json`.
This is a local PS2 test build; public release remains v0.4.38 and the latest
local PSP remains v0.4.42. No GitHub release was requested or created.
If a name was already confirmed in its damaged form, use the fixed editor's
**Reset** action and confirm again. Load a normal in-game save after booting
the new ISO; an old emulator save state can retain the previous executable.
