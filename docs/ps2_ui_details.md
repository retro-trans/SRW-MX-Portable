# PS2 detail, search and roster fixes — 0.1.12

This incremental build retains the PSP opening, both extra scenarios and the
native 4x VWF from 0.1.11. It changes English UI paths in the executable and
skill/ability description indexes in FIX00. No texture replacement is used.

| Reported screen | Changes |
| --- | --- |
| Weapon Details | Attr., None/Yes/Pierce/Spread/Null/Weaken flags, four-character Asst label, compact Will/Critical/Skill labels, Ammo value spacing |
| Skill search | Skill Search header; descriptions wrap with native PS2 glyph advances |
| Ability search | Ability Search header; descriptions wrap with native PS2 glyph advances |
| Unit roster | Allied Units header, plus Enemy Units/Neutral Units/Unit Info variants; Status/Edit/Info and Will labels |
| Movement field | English Move in the remaining GP-relative draw paths |

Some labels are loaded relative to the global pointer, so the earlier
translator's ordinary pointer and LUI scans did not find them. Five local
draw stubs supply the English pointer and tail-call the native renderer,
retaining coordinates and caller state. The search/roster headers have
branch-delay references; both high-word paths now use the English pool.

Weapon flags were copied as two Japanese characters before drawing.
Translation now expands those cached flags inside the existing 256-byte
stack buffer before measuring them. The calculation uses the same VWF
context as their final draw. The Assist source is shortened to Asst because
its attribute formatter copies exactly four characters. The Ammo value
starts at native X=112 instead of 80; its label starts at X=32.

Descriptions retain their English meaning and wrap at 512 native pixels,
using the 24-pixel font's advances. Each uses at most three rows. Two ability
descriptions were shortened to fit while retaining their details: the
5+ EN/4000-damage barrier and its bypass/break conditions; and Connect's
player-phase EN recovery and 10-square movement limit. New sentence IDs
are appended; every old sentence and every numeric gameplay record remain
intact. Other description tables and campaign assets remain unchanged.

Build: `python tools/fix_ps2_ui_details.py --build`.
Dedicated checks: `python tools/verify_ps2_ui_details.py`.
Evidence and layout: `work/ui/ps2/ui_details_0.1.12/`.
Execution reports and ISO: `work/output/`.
The reports distinguish native checks from in-game visual confirmation.
No GitHub release is authorized for this build.

Final disc: `work/output/SRWMX_PS2_EN_0.1.12.iso`, 4,663,265,280 bytes.
SHA-256: `2e5fd0c260d8f2c827bf2fae4fddf851fb67132f9cd9686ce0f56924a615e6ea`.
All 37 disc resources and ISO9660/UDF replacement records pass validation.
Fresh PCSX2 2.8.2 boot confirms the loaded executable segment, all recorded
hooks and the new detail instruction/reference words. No CPU-opcode or TLB
warnings were reported. Screen-by-screen visual confirmation remains pending.
Boot the new disc fresh when testing; older emulator save states restore
the old executable and cached labels. A memory-card save uses the new code.
