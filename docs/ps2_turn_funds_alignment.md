# PS2 map-menu Turns / Funds alignment — local v0.4.44

The reported `CWndTurnMoney` panel uses `%4d` at x122 for Turns and `%8d`
at x58 for Funds. Those offsets share a right edge with the original fixed
16-pixel ASCII cells. The English proportional font makes spaces narrower
than digits, so the padded strings end at different positions. Executing
the existing panel reproduces the 1 / 367040 mismatch in the screenshot.

Both numeric rows now use the same window-relative right edge, x188, inside
the original 200-pixel panel. A small private native wrapper measures the
actual formatted ASCII string through the installed width function, subtracts
that width from the anchor and calls the original renderer. Labels remain
at x12; row positions y6/y32, numeric font 16x24, formats, values, panel size,
visibility and slide animation stay unchanged. Shared formatter strings and
other windows are untouched.

`tools/fix_ps2_turn_funds.py` checks four original instructions, appends the
wrapper to the registered font segment and updates its heap start. Repeating
the patch checks the existing code and hooks without allocating another copy.
Both regular PS2 builders apply it after the unit rename correction.

`tools/verify_ps2_turn_funds.py` executes the actual native panel initializer,
label drawing, numeric call sites, wrapper and width function. It reproduces
the old mismatch and checks 27 combinations of values, window origins and
animation offsets, from zero through 2,147,483,647. Both values share the
same right edge, clear their labels and stay within the panel. A separate
check runs the actual ASCII renderer's conversion and glyph advances for
18 numeric rows, capturing the final pen position immediately before GS
drawing. Both rows end at native screen x628 when the panel starts at x440.
Stack, callee-saved registers, hidden-panel behavior and idempotence pass.
Fixtures supply standard sprintf and the EE packed strlen service; graphics
calls are captured. Fresh PCSX2 visual acceptance remains pending.

`tools/build_ps2_turn_funds.py` builds over verified local PS2 v0.4.43.
Only the registered instructions, appended wrapper, executable sizing/heap,
required disc metadata and regenerated native v0.4.44 footer may change.
It hashes the complete source while copying the allowlisted transform,
then checks the entire output against its independently computed expected
hash. Existing resource extents are protected from all metadata writes;
all 37 directory entries and both ISO9660/UDF executable views are checked.
The prior rename, translation, artwork and story fixes are retained.

Test ISO: `work/output/SRWMX_PS2_EN_0.4.44.iso`.
SHA256: `a108a7bb88819469bea2afa9b4072773ee302ba1f5f11d325ad30491f0d528f4`.
Evidence: `work/output/ps2_turn_funds_0.4.44_verification.json`.
Reported screenshot and native coordinates:
`work/ui/ps2/turn_funds_2026_10_26/`.
No emulator/memory-card changes and no GitHub release. Public remains
v0.4.38; latest local PSP remains v0.4.42.
