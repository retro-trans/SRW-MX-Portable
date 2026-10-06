# Shared public release v0.4.12 — 2026-10-06

The user authorized releasing both platforms under the PSP version number.
Public PS2 v0.4.12 is byte-identical to the final local 0.1.18 image
(`10d491a0ce7331ecaf94270f5112c375276f0a987c1150e104fd22a67833dbdf`).
PSP v0.4.12 retains its existing image and number. Release notes and exact
source/output hashes are in `docs/releases/v0.4.12.md`. PSP uses the existing
Retro Trans Automatic catalog; the PS2 ZIP has separate metadata and is applied
with Apply xdelta. Earlier local-only statements below are historical.

# Handoff — SRW MX Portable English translation

Written 2026-10-02 for whoever continues this work. The original comparison instructions below are
retained; the continuation status describes the latest work on disk.

## PS2 continuation status — 2026-10-06

**Latest local PS2 candidate: 0.1.18 — three favorite series.**
Build with `tools/fix_ps2_favorites.py --build`; see `docs/ps2_favorites.md`,
`work/build/ps2/favorites_0.1.18/` and
`work/output/ps2_favorites_0.1.18_execution.json`. Both balance modes offer
three distinct choices at New Game setup. Confirm toggles, Cancel undoes,
and the third pick opens native Yes/No confirmation. A new top panel displays
all three choices. Native favorite bits at settings +0x5e8 are unioned only
after Yes; all three receive the native EXP/upgrade bonuses and save normally.
Legacy saves keep their choices and NG+ preserves inherited favorites. Save
format and difficulty persistence are unchanged. All 1,632 combination/mode
cases pass, as do native save-field, bonus, UI and prior regression checks.
Output: `work/output/SRWMX_PS2_EN_0.1.18.iso` (4,663,269,376 bytes).
All 37 disc files pass; only the executable changes from 0.1.17. SHA-256:
`10d491a0ce7331ecaf94270f5112c375276f0a987c1150e104fd22a67833dbdf`.
Final fresh-boot PCSX2 readback matches the immutable segment and all 199
references/hooks with zero opcode/TLB warnings. Full menu visual and real card
save/reload checks remain pending: Computer Use failed to activate the test
window, then denied cursor/input access. No release or push is authorized.

**Previous local PS2 candidate: 0.1.17 — CT/AT forecast badge fixes.**
Build with `tools/fix_ps2_forecast_badges.py --build`; see
`docs/ps2_forecast_badges.md` and `work/build/ps2/forecast_badges_0.1.17/`.
AT/CT native WND image payloads now fit the actual 24×24 badge area,
with complete original frames and padding. Only these two payloads change;
the executable and all other resources match 0.1.16. Previous native
execution evidence is carried forward explicitly. Asset previews pass;
in-game visual confirmation remains pending. Output:
`work/output/SRWMX_PS2_EN_0.1.17.iso` (4,663,267,328 bytes).
All 37 disc-file checks pass; only WND.BIN changes compared with 0.1.16.
The shared graphics renderer matches the incremental patch exactly.
SHA-256 `5e181905226266c4ea51f769acf219e24c62ee18e2edf851011a1924cbb3739f`.
No release or push is authorized.

**Previous local PS2 candidate: 0.1.16 — weapon and battle UI fixes.**
Build with `tools/fix_ps2_weapon_battle.py --build`; see
`docs/ps2_weapon_battle.md`, `work/build/ps2/weapon_battle_0.1.16/`, and
`work/output/ps2_weapon_battle_0.1.16_execution.json`.
Attribute text is explicitly terminated, with A/S single-character flags;
long weapon names fit proportionally; Giganos Sldr. is forecast-only.
Weapons and the shared Critical image are translated. CFont wrappers also
map complete cached Will/Critical/Weapons labels to English. All earlier
scenario, balance and UI content is preserved. Battle-animation visual
confirmation of Will/Critical remains pending; do not claim its baked
graphics were identified. Output: `work/output/SRWMX_PS2_EN_0.1.16.iso`.
All 37 disc files pass; fresh 4x PCSX2 boot confirms all 177
hook/reference words and the native segment, with no opcode/TLB warnings.
ISO SHA-256 `d5d904e771e2f72410b757f250d2eca89568cefa547628b5bc0eb75419b4d066`.
No release or push is authorized.

**Previous local PS2 candidate: 0.1.15 — map support captions.**
Build with `tools/fix_ps2_map_support.py --build`; see
`docs/ps2_map_support.md` and `work/build/ps2/map_support_0.1.15/`.
Native MAP section 16 images M_65/M_66/M_67 are English Support Atk,
Support Def and Assist Atk. Only the three 2,048-byte pixel payloads change.
The executable, counters, palettes and all other map content remain identical
to 0.1.14. Decoded previews pass; in-game confirmation remains pending.
Output: `work/output/SRWMX_PS2_EN_0.1.15.iso` (4,663,267,328 bytes).
SHA-256 `ecdaa12f194f5db0a9a6b0abefde5bcec4240047311254332e9f22e1db452360`.
Native campaign checks and all 37 disc resource readbacks pass. No release or push.

**Save converter handoff 0.1.0:** see
`docs/retro_trans_tools_mx_save_handoff.md` and
`work/output/SRWMX_SaveConverter_Handoff_0.1.0.zip`.
The portable bundle is copied to the local Retro Trans checkout at
`E:/Projects/retro-trans-tools/.integration/srw-mx-save-handoff-0.1.0/`.
It specifies PS2 ↔ PSP conversion and the PSP Harder choice for patched
PS2 output, with integrity references and known campaign restrictions.
The converter is not implemented; matched checkpoint field mapping,
destination packaging/crypto and in-game acceptance remain required.
No ROM/save/key bytes are distributed. No release, push or chat dispatch.

**Previous local PS2 candidate: 0.1.14 — save/setup/series UI fixes.**
Build with `tools/fix_ps2_setup_save.py --build`, preserving 0.1.13.
See `docs/ps2_setup_save.md`, `work/build/ps2/setup_save_0.1.14/`, and
`work/output/ps2_setup_save_0.1.14_execution.json`. Checking, saving and
system-data overwrite prompts are English. Yes/No share one left edge;
protagonist values move 32px right, age suffixes are removed, both unit
descriptions are fully English, and final setup buttons are translated.
Series titles use actual VWF centering and uniform fitting inside the
456px padded title area. The baseline uses the native square glyph height.
Native checks cover nine save branches, the actual protagonist header,
both value/age paths, both six-row descriptions, both final button
selections, Yes/No initialization and 40 series title cases. Campaign
.BIN/.DAT resources match 0.1.13 exactly. Disc packaging and fresh-boot
visual validation are recorded in the output reports. No release/push.
Final ISO: `work/output/SRWMX_PS2_EN_0.1.14.iso`, 4,663,267,328 bytes,
SHA-256 `92b871792cbb936d74b72394d9d97cd1e73022bc3574c2d113608e4ee8cde14f`.
All 37 disc resources pass validation. Fresh PCSX2 boot confirms the
777,344-byte native segment and 164 hook/reference words at 4x, with
texture replacements disabled and no opcode/TLB warnings.
PCSX2 visually confirms Protagonist Setup, the separated Name/Nick/Age
value column and the English age values. Evidence is
`work/ui/ps2/setup_save_0.1.14/4_protagonist_setup_after.png`. Save dialogs,
unit descriptions, final confirmation and series-title panels pass
native execution checks; their visual confirmation remains pending.

**Previous local PS2 candidate: 0.1.13 — roster/System UI fixes.**
Build with `tools/fix_ps2_roster_system.py --build`, preserving 0.1.12.
See `docs/ps2_roster_system.md`, prepared files in
`work/build/ps2/roster_system_0.1.13/`, and native execution report in
`work/output/ps2_roster_system_0.1.13_execution.json`.
Roster headings use Wpn/Cost/Und/Rng/P.Rng/Atk to avoid overlap. System
labels and choices are translated at nine local draw sites; two direct
Repair draw sites use Cost. Objectives has a second literal after a
nonzero structure field, referenced in a call delay slot at 0x153b58;
this is now translated too. The map-menu entry was already English.
All 18 legal settings, 14 roster descriptors and the actual Objectives
header pass native text/geometry checks. Option values and all .BIN/.DAT
resources are unchanged from 0.1.12. The roster/footer/header fixes from
0.1.12 remain active. Test with a fresh disc boot; an old save state
restores old executable code. No release or push is authorized.
Final ISO: `work/output/SRWMX_PS2_EN_0.1.13.iso`, 4,663,267,328 bytes,
SHA-256 `31ad4fcdc7effccade0fefc78d100d6f8d33cbb7bc7f4ea1cbac0a0167e9ebd0`.
All 37 disc resources and retained font/campaign/UI checks pass. Fresh
PCSX2 loaded-byte verification passes for the immutable segment and 117
hook/reference words at 4x, with no opcode/TLB warnings. Panel-by-panel
visual confirmation is pending.

**Previous local PS2 candidate: 0.1.12 — detail/search/roster UI fixes.**
Build with `tools/fix_ps2_ui_details.py --build`, using the preserved 0.1.11
resources. See `docs/ps2_ui_details.md` and `work/build/ps2/ui_details_0.1.12/`.
Native header branch paths and GP-relative label draw calls are translated.
Cached weapon flags translate before VWF measurement, so alignment accounts
for their English width. The fixed four-character attribute buffer uses Asst.
The 102 skill/ability descriptions use PS2 advances and at most three lines;
old sentence IDs remain valid, and every numeric database section is unchanged.
All campaign scripts, stage resources and portraits are byte-identical to
0.1.11. PSP opening remains selected. Native checks pass; visual checks must
use a fresh boot of this disc, because older save states restore older code.
No GitHub release or push is requested for this build.
Final ISO: `work/output/SRWMX_PS2_EN_0.1.12.iso`, 4,663,265,280 bytes,
SHA-256 `2e5fd0c260d8f2c827bf2fae4fddf851fb67132f9cd9686ce0f56924a615e6ea`.
All 37 disc resources pass validation. Fresh PCSX2 loaded-byte checks pass
for all recorded hooks and new detail instructions/references. Full visual
checks of the five reported screens remain pending; see the runtime report.

**Previous local PS2 candidate: 0.1.11 — font and battle/status UI fixes.**
User explicitly chose to keep the PSP opening; do not combine the original
PS2 lab opening with it. See `docs/ps2_ui_fixes.md` and
`work/build/ps2/ui_fix_0.1.11/`. Latin uses square dimensions derived from
the smaller native cell dimension, with native half-width numeric contexts
retaining their original height; the native 4x atlas is preserved. The
remaining command, unit/pilot-stat and weapon labels are translated, weapon
labels shortened and Spirit SP costs moved right. Long Spirit names scale
uniformly inside a 76-pixel field. All scenario and portrait resources match
0.1.10 byte-for-byte. Native execution checks pass; build/visual reports
describe the final disc and observed screens. No release or push requested.
Final ISO is `work/output/SRWMX_PS2_EN_0.1.11.iso`, 4,663,255,040 bytes,
SHA-256 `7438b0574cb07c97bd46948b47e0d060fadc269392d90a8fa0a53bc248c7312b`.
Final PCSX2 screenshots confirm the PSP opening, researcher dialogue and
English commands. Unit Stats, Pilot Stats and Weapon Data visual checks
remain pending because isolated emulator controller input was unreliable.
Their native label/name-fit/cost checks pass. See
`work/ui/ps2/ui_fix_0.1.11/layout.json` for exact evidence and native fields.

**Previous local PS2 candidate: 0.1.10 — Prologue corrections built.** See
`docs/ps2_prologue_fixes.md` and `work/build/ps2/prologue_fix_0.1.10/`.
Both PSP pre-battle `0b` events are restored to their exact seven-command,
zero-dialogue source; the old substitution of `i001b` was incorrect.
Native Game Over (0x13d) chapter 0/1 retry gate now includes group 4, with
98 dispatch/parent-retry cases checked. Researcher Pilt433 story face is
2110 (bytes4/5=21,10), separate from its absent battle face at +14. Native
descriptor slot309 and FACEPACK indexes2998/2999 are ported from PSP art.
All other 201 scripts remain byte-identical to 0.1.9. Output is
`work/output/SRWMX_PS2_EN_0.1.10.iso`, 4,663,252,992 bytes, SHA-256
`a48daca844b70653d944f0696d45cabf2b3d1eefab38136a4fc10d2e32afb078`.
All 37 disc resources and replacement ISO9660/UDF entries pass validation;
original ISO and 0.1.9 hashes remain unchanged. Fresh PCSX2 new game on the
Super Robot route visually confirms Hugo's Wolf 1 opening and the correct
researcher radio portrait. Evidence is in `work/ui/ps2/prologue_fix_0.1.10/`
and `work/output/ps2_font_0.1.10_runtime.json`. Full in-game defeat/retry,
clear, memory-card save/load and physical PS2 validation remain pending.
No release requested. Build with `tools/fix_ps2_prologue.py --build`.

**Previous local PS2 candidate: 0.1.9 — both PSP extra scenarios included.**
Output `work/output/SRWMX_PS2_EN_0.1.9.iso`. See `docs/ps2_stage30_port.md`
and `work/output/ps2_font_0.1.9_verification.json` for hashes and evidence.
PSP s0570 is reworked scenario 29 (What Gnaws at the "Heart"); s0560 is
the extra scenario 30 (Zeorymer Sorties at Dawn). Both six-scene event groups
are required. Native chapter 7 locations are `[29,30,31,32,33,68,34]`, with
groups 12 then 10 for those two battles. Tables contain 203 scene blocks.
All reviewed English source slots are covered; nine PSP BFACEPAK cache
commands are adapted to native opcode 178. Original map 90 heights and
native artwork remain. Additional Aqua variants alias native assets 315;
enemy Dragoon 156 reuses native row 69 and has an added PSP-balance entry.
Objective footer titles now correctly map Prologue and chapter-7 groups.

Execution checks pass for native scripts/deployments, seven selectors and
history slots, unlock masks, save fields, card/asset reads and all previous
font/text/balance/Prologue regressions. Stage 29/30 full in-game clear,
memory-card save/load and physical PS2 tests remain pending. Use new games
with a separate card; existing campaign save migration is not implemented.
No release or push requested for 0.1.9. Build with `tools/port_ps2_stage30.py`.
Disc is 4,521,150,464 bytes, SHA-256
`547878052851c158d40154557803c5b647b720ed8ffae12b41ad58acf59c3428`.
Fresh PCSX2 2.8.2 boot/PINE byte checks pass for the full added segment,
all hooks and loader tables, with no unknown opcode/TLB warnings and no
texture replacement. Opening FMV visually observed; stages 29/30 still
need full in-game playthrough. `work/output/ps2_font_0.1.9_runtime.json`.
The following 0.1.8 notes are historical; its ISO remains preserved.

**Latest local PS2 build: 0.1.8 — chapter-number fix.**
`work/output/SRWMX_PS2_EN_0.1.8.iso`, 4,666,597,376 bytes, SHA-256
`0e9f7f4fd61d93c16c7bd6f389b914f6e719af857bbf1dc2b2fb2b3dd079e7b4`.
The user reported the first story card (Visitors from the Beyond) displaying
Chapter 2 after the added Prologue. Hero +0x5f0 counts all cleared battles;
both card-animation paths passed that count plus one. Four display-only
instructions now copy the count without adding one: 0x348634 / 0x3489b4 for
cards and 0x224f08 / 0x2fe7cc for objectives. Prologue displays number zero;
the first story card receives one. No native clear count, save field or
campaign progression changes. Existing 0.1.7 entry fix and resources retained.

`tools/ps2_prologue_numbering.py` is integrated into the clean builder and
incremental verification. 64 native animation cases and 24 native objective
number cases pass across both robot routes. The tests run actual campaign
animation/title lookup, reproduce the original off-by-one and verify counts
remain intact. Report: `work/output/ps2_prologue_0.1.8_numbering_execution.json`.
New Game entry, all eight scene loaders, both deployments, campaign save-field,
font/text and difficulty checks pass. All retained ISO resources were rehashed;
ISO9660 and UDF read the corrected executable. ELF SHA-256
`241497d4d58b7d284a741ba640c38885e5b1b06ef26cd6af58a19f4c90515ef0`;
segment remains 760,436 bytes and InitHeap remains 0x7cea80. Build report:
`work/output/ps2_font_0.1.8_verification.json`. The 0.1.8 title card itself has
not yet been visually checked in PCSX2; retain the 0.1.7 runtime evidence below
as evidence for that previous version only.

Pending footer-title issue: objective call sites pass campaign group / 2 to
0x3473d0, but the added Prologue shifted the first two chapter location lists.
For chapters 0/1, group 4 needs location index 0, group 0 needs index 1, group
2 needs index 2. Remap only the two objective callers; do not change 0x3473d0
globally, because the history title getter already supplies actual list indexes.
0.1.8 corrects displayed numbers, not this title lookup. Full battle clear,
memory-card acceptance, physical console and the added stage 30 remain pending.
No GitHub push/release for 0.1.8. Original discs and earlier builds preserved.

Rebuild with `tools/port_ps2_prologue.py` (0.1.8), or prepare corrected resources
under `work/build/ps2/prologue_0.1.8` and run
`tools/update_ps2_difficulty_build.py --source-version 0.1.7 --version 0.1.8 --feature prologue`.

**Previous local PS2 build: 0.1.7 — Prologue New Game entry fix.**
`work/output/SRWMX_PS2_EN_0.1.7.iso`, 4,661,843,968 bytes, SHA-256
`be484ab778e957cb11bd0950f2fc86e304868693b9dd75d6f40fd0bb582252e8`.
The user confirmed 0.1.6 skips the Prologue and enters original stage 1.
Native New Game completion event 0x2d6 bypasses STAGE selection and passes
deployment group zero at 0x134d88 / 0x134da8. Both now pass group four;
the call at 0x134dc0 wraps native campaign advance to set current group four
without incrementing initial history slot zero. Later chapter advances retain
their original code. Both robot routes and both difficulty modes pass actual
native completion-event execution; tests reproduce the old skip. See
`work/output/ps2_prologue_0.1.7_entry_execution.json`.

All eight native scene loaders, both deployments, campaign save-field checks,
font/text and difficulty regressions pass. All retained disc resources were
rehashed and are identical to 0.1.6; both filesystems read the corrected ELF.
ELF SHA-256 `15699c45e1ab1539550acfd18ddd1d73055b68ab41150933649cdbd7a8ba3232`;
entry routine 0x7cea50, segment 760,436 bytes, InitHeap still 0x7cea80.
Packaged ISO boots in isolated PCSX2, PINE 28018: complete segment, all hooks
and script tables match RAM. No CPU opcode or TLB warnings at initial boot.
Profile: `work/build/ps2_prologue_test_0.1.7/emulator/mx-prologue-fix.exe`.
It has its own copied card; 0.1.6 settings/card and the user's normal profile
are untouched. Test-only direction macros must bind `Down` / `Up` / `Left` /
`Right`, not `DPadDown` etc.; H toggles R1 for dialogue fast-forward.
Both Prologue battles reach their actual mission/objectives screen in PCSX2:
Garmraid with PS2 balance and Cerberus with PSP balance. Live campaign state
is chapter 1/0, group 4, history slot 0; deployments are s00s00/s00r00, map
390, two units. Runtime entry evidence is
`work/output/ps2_prologue_0.1.7_runtime_entry.json`; screenshots are
`work/ui/ps2/prologue_0.1.7_super_objectives.png` and
`work/ui/ps2/prologue_0.1.7_real_objectives.png`.
The UI tests resumed an owned New Game unit-setup checkpoint with only the
three corrected entry words/new routine migrated; fresh ISO boot was checked
separately. The native event tests start from a reset campaign for all four
route/balance combinations. All macros were released at the end of the 0.1.7 test; the emulator was subsequently observed idle.
Known display issue: the objective footer still shows original stage 1's
title; its number is corrected in 0.1.8, but location-title lookup still needs correction. Actual
battle clear/save-load, physical console and stage 30 remain pending.
No GitHub push/release.

Rebuild normally with `tools/port_ps2_prologue.py` (now 0.1.8), or retain the
verified 0.1.6 resources using `tools/update_ps2_difficulty_build.py
--source-version 0.1.6 --version 0.1.7 --feature prologue` with prepared 0.1.7
files. Both builders check the New Game entry before packaging.

**Previous local PS2 build: 0.1.6 — playable PSP Prologue candidate.**
`work/output/SRWMX_PS2_EN_0.1.6.iso`, 4,657,090,560 bytes, SHA-256
`00c9dab486d9fef3dc9657cf10e9273b6b8a76bff2d791e2d80bb3a7ce0276f3`.
Built from verified 0.1.5 with eight extra English scene blocks, native map 390,
two deployments, the faceless Researcher in unused pilot slot 433, and campaign
links before both original stage-1 routes. Original IDs/resources are preserved;
both disc filesystems agree. Total: 200 scene blocks and 68 scenario records.
The other added PSP stage (stage 30 / s0570) is not included yet.

Fixed an earlier campaign corruption: chapter names were written into 64 bytes,
but their actual field is 56 bytes. Restored all fourteen numeric progression
regions from the original STAGE archive, then inserted the two Prologue location
IDs. `tools/ps2_scenario_port.py` now checks that names preserve these regions.
Use a new game on a separate card: existing saves' location-index migration is
not implemented. Do not load a Prologue save with the unpatched game.

Native script/deployment load execution, route selection, six campaign save-field
round trips, database preservation, font/translation and difficulty regressions
pass. These checks do not replace actual battle clear or memory-card saving.
Reports: `work/output/ps2_prologue_0.1.6_execution.json`,
`work/output/ps2_prologue_0.1.6_regression.json`, and
`work/output/ps2_font_0.1.6_verification.json`. ELF SHA-256
`342d14fdc993e2718776184f09602cf9858d045243b7428187e3dcc9c48a099b`;
added segment 760,386 bytes, InitHeap 0x7cea80, balance mode still 0x7cce90.

PCSX2 boots this disc: the complete added segment, all hooks and script/section
tables match RAM; opening FMV and English battle dialogue in the title-screen
demo were observed, with zero opcode/TLB warnings. Runtime evidence:
`work/output/ps2_font_0.1.6_runtime.json`. Both Prologue battles, clearing into
stage 1, and actual memory-card save/load remain pending.

The working isolated emulator is
`work/build/ps2_prologue_test_0.1.6/emulator/mx-prologue-test.exe`, a portable
copy of the already installed PCSX2 2.8.2, PINE 28017. Its separate card is
`work/build/ps2_prologue_test_0.1.6/memcards/mx-test.ps2`. Launching a copy named
pcsx2-qt.exe through Computer Use instead selected the installed emulator;
renaming the test executable made window selection unambiguous. The installed
emulator was opened but no game/card/settings changes were made there.
The test window is usable. Short automated controller taps were missed between
game polls; PCSX2's own toggle macros solve this by holding each button until a
second trigger. New Game opens correctly. In this isolated profile only:
F10 = Circle, F11 = Start, F12 = Down, F7 = Up, V = Left, B = Right, N = Cross.
Press a macro key again to release it. Avoid leaving a direction held through
multiple menus. Normal L/K/Enter/arrows bindings also remain. A fresh New Game
checkpoint is `work/build/ps2_prologue_test_0.1.6/new_game_checkpoint.p2s`;
this is an emulator checkpoint, not proof of memory-card saving. Re-select
current windows by app/path, not stale handles. User's normal cards untouched.

Rebuild through `tools/port_ps2_prologue.py`, optionally `--prepare-only`, then
run `tools/verify_ps2_prologue.py`. The older clean campaign builder still
defaults to 0.1.5 and does not include these new resources. See
`docs/ps2_prologue_port.md`. No commit, push or GitHub release for this build.

**Previous local PS2 build: 0.1.5 — difficulty selection fix.**
`work/output/SRWMX_PS2_EN_0.1.5.iso`, 4,529,623,040 bytes, SHA-256
`fd33956e7fa189a9d759b4bd08ee306545128faa39881f2ab0905c7beed1f72f`.
The user screenshot showed only the balance explanation in 0.1.4. Its choice
window never finished opening: Keystone's MIPS64 `$t0` encoded register 12,
but the native PS2 fifth argument is register 8. Fixed this with numeric `$8`.
The copied vtable was also truncated at 0x90; copied all 0xd8 bytes, including
the four cursor geometry methods used by the opening routine.

Actual five-frame opening, render dispatch for both labels, up/down navigation,
confirmation/cancellation, cleanup, all balance values and save-tail tests pass.
Both deliberately reintroduced bugs are caught by new regression checks.
All other disc resources were independently rehashed and remain byte-identical
to 0.1.4. Appended segment is 757,504 bytes; InitHeap remains 0x7cdf00;
mode remains 0x7cce90. ELF SHA-256
`a4b18b4fcb8111e5125ec714f10002e424b3e842355beea1ab88d812fe1ea228`.
Original source/builds preserved. Clean campaign builder defaults to 0.1.5;
`tools/update_ps2_difficulty_build.py` can preserve a verified previous English
disc while appending the corrected executable to a new version.

Isolated PCSX2 profile `work/build/ps2_difficulty_test_0.1.5/PCSX2`, PINE 28016:
full segment, hooks and script tables match RAM, FMV observed, no opcode/TLB
warnings. Activation denied twice (`GetCursorPos failed: Access is denied
(0x80070005)`); do not claim visual validation. Test PID 13252 stopped after
verification. Original user cards untouched; real gameplay/save-reload and
physical PS2 checks remain pending. No GitHub push/release.

**Previous local PS2 build: 0.1.4 — optional PSP balance prototype.**
`work/output/SRWMX_PS2_EN_0.1.4.iso`, 4,524,873,728 bytes, SHA-256
`2aa59e7dbee57aaa5a971627970c1c4d568d6fd8e9954dea06216449ae50ca4c`.
Retains all 0.1.3 English coverage and native 4x VWF. New Game offers
PS2 - Original / PSP - Harder. Harder mode selects exact original PSP values:
139 shared enemy HP records +50%; 294 nonzero shared reward records -20%.
The empty PS2/PSP Dragoon slot 156 is excluded. Original PS2 campaign, numeric
fields outside HP/rewards and one favorite-series choice remain.

The difficulty mode lives at `0x7cce90`; the final added segment is 757,440
bytes and InitHeap starts at `0x7cdf00`. Native save settings tails stamp
three words at +0x3e0: MXBD, version 1, mode 0/1. Both payload lengths and
native checksums remain. Absent/invalid markers default to PS2; scenario
mode restores before unit decoding. The shared New Game confirmation box
gets an object-specific wide vtable, then restores its normal Yes/No class
and labels after closing. See `docs/ps2_difficulty.md` and
`work/translation/en/ps2/difficulty.en.json` for exact hooks and scope.

3,072 record execution checks, controller-handler callbacks, Cancel, cleanup,
save-marker round trips/native tail checksums, old-save defaults and early
restore pass. Finished ISO boots in an isolated PCSX2 profile on PINE 28015
with copied memory cards; complete code segment/hooks/script tables match
RAM, opening FMV observed, zero unknown opcode/TLB warnings. Visual New Game
acceptance, real gameplay HP/rewards and saving/reloading both modes are still
pending: Windows activation returned Access is denied twice. Test PID 55688
was stopped after checking; user PID 54120 was not touched. Physical PS2
checks are pending. No GitHub push/release. The clean campaign builder now
defaults to 0.1.4; this packaged candidate additionally retains an unused
pre-cleanup ELF extent, so a clean rebuild may have a different disc hash.

**Previous local PS2 build: 0.1.3 — campaign/database port.**
`work/output/SRWMX_PS2_EN_0.1.3.iso`, 4,525,156,352 bytes, SHA-256
`d1a40ec6b726acae6d2b92d4a02a098cf948352480fd40325ab80095a3c7ab8c`.
All 49,659 readable PS2 story slots are English (186 translatable scenes;
192 blocks including six nontext/dummy blocks). All original commands remain.
Also includes all 51,434 battle-caption entries, all non-dummy database
descriptions, 1,499 names, 32 spirit names, all 66 scenario/title-card records
(198 native atlases), narration, terrain and an initial menu/window-art port.
See `docs/ps2_campaign_port.md` for coverage, rebuild steps and remaining work.

The first candidate failed startup because English FIX00 exceeded the native
fixed resource heap's spare capacity. The final build fixes this by removing
unreferenced source sentence storage and moving 320,050 English bytes to a
native pool through the sentence getter at 0x332518. Final FIX00 is 516,744
bytes (original 517,712). Sent IDs and referenced original/dummy rows remain.
All 4,332 translated description-row reads pass execution checks, including
2,171 reads through the external pool. The finished ISO boots in isolated
PCSX2; English FIX00, full font/text segment, hooks and script tables match RAM.
Full campaign/visual validation and physical PS2 checks remain pending.

Remaining artwork is primarily the shared STATIC atlas: logical 1024x256,
palette at 0x134400 (GS CSM1 order), linear indexed pixels at 0x134800,
0x40000 bytes. `work/ui/ps2/static_linear_1024.png` is its correct preview.
The 512-wide and unswizzled probes are wrong interpretations; do not use them.
Port its labels using the existing PSP banner translations while preserving
native UV regions/digits/non-text artwork. Other PS2 menu differences/layouts
and the Sortie Prep header also need a native artwork pass.

The local test profile is `work/build/ps2_campaign_test_0.1.3/PCSX2`, PINE
28014. Do not interrupt the user's emulator (PID 54120 at this check).
Desktop activation failed with `GetCursorPos failed: Access is denied
(0x80070005)`; returned game captures were black, so visual QA is unverified.
No GitHub push/release is authorized. Previous PS2 builds remain preserved.

The following records the earlier baseline-only build.

**Earlier local PS2 build: 0.1.2 — font baseline correction.**
`work/output/SRWMX_PS2_EN_0.1.2.iso`, SHA-256
`24e95df8f22c4711a689461f02849eb1a68cacb9597faf72ea437fc69f18348f`. The user's four 0.1.1 dialogue captures
confirmed English loading/rendering, but showed uneven letter alignment.
0.1.2 preserves the high-resolution font baseline instead of independently
resizing each glyph vertically into its 20px hinted bounds. Ordinary bottoms
vary by one high-res pixel, compared with four before; deep descenders retain
two guard rows. All glyph advances, renderer/heap hooks and the entire MAP
archive are byte-identical to 0.1.1. Coverage remains opening + both stage-1
routes, 1,321 translated slots. No new translation area is added.
85 baseline checks and existing font execution/UV checks pass. Final disc
and boot evidence are under `work/output/ps2_font_0.1.2_*.json`; corrected
in-game visual acceptance and physical PS2 checks remain pending.
User captures and labeled atlas specimen are under `work/ui/ps2/`.
Build with `tools/build_ps2_dialogue.py` and version `0.1.2`.
Do not interrupt the user's current 0.1.1 emulator session for font QA: a
separate test profile is `work/build/ps2_baseline_test_0.1.2/PCSX2`, PINE 28013.
Original test profile remains PINE 28012. No GitHub push/release authorized.

The following records the original 0.1.1 dialogue insertion.

**Local PS2 build 0.1.1 — opening and both stage-1 routes in English.**
`work/output/SRWMX_PS2_EN_0.1.1.iso`, SHA-256
`954f3c069a72e6e8f723190d887e02194073e17736d29615961ddec6a75e71dc`.
Ported 1,321 string-table entries in five scenes: `i001b`, `s00r10`, `i00r1a`,
`s00s10`, `i00s1a`. Four technical labels remain unchanged. Reviewed seven
PS2 wording variants covering 11 slots; English-only overrides and mapping
are under `work/translation/en/ps2/script/`. No later scenes, UI/database,
battle-caption or chapter-artwork insertion is included. Start **New Game**
to see the translated opening; a later-scene save will still show Japanese.

Full disc readback passed: only ELF and MAP change; all 35 unrelated files
retain hashes and LBAs. Both ISO9660 and UDF read the rebuilt files. All 192
PS2 command arrays and every untouched string are preserved, and all 192
finished script blocks match their generated hashes. The MAP script area
grew by 33 sectors; its prefix and moved suffix remain unchanged. Native 4x
font execution checks pass. The finished ISO boots in isolated PCSX2. The font
segment, all 19 font/heap patches, full script-sector table and MAP section
table match RAM, with no unknown CPU opcode warnings. User captures confirmed English dialogue in the opening and stage 1, with
intact portraits/backgrounds. Font baseline alignment failed visual review;
0.1.2 corrects the atlas. Physical PS2 validation remains pending.
Build: `python tools/build_ps2_dialogue.py 'Super Robot Taisen MX (Japan).iso' 0.1.1`.
Use `--verify-existing` for readback of the existing ISO. Reports are
`work/output/ps2_font_0.1.1_verification.json` and
`work/output/ps2_font_0.1.1_mips_verification.json`, with boot/RAM evidence in
`work/output/ps2_font_0.1.1_runtime.json`; details in
`docs/ps2_dialogue.md`. No PS2 push/release is authorized.

The project lead requested a PS2 translation port, starting with the native 4x
VWF. Local PS2 font-only build **0.1.0** is at
`work/output/SRWMX_PS2_EN_0.1.0.iso`, SHA-256
`9c5f40d60a396d991921a1629d2addb1879dd25a997e532b4ee6c5aa41431295`.
It adds Genei LateGo Medium Latin glyphs at 96×96 with variable-width drawing
and measurement. No emulator texture replacement is used. PS2 story, battle,
UI and title-card insertion is still pending; the PSP 0.4.9 release is unchanged.

Full disc verification passed: only the executable changes, all 36 other
files retain hashes and LBAs, and ISO9660/UDF both read the new ELF. Execution
checks passed 1,368 width cases, 20 Japanese fallback cases, 344 renderer cases
and 86 glyph/upload plus 86 atlas UV-bound cases. The finished ISO boots in isolated PCSX2 and its
400,096-byte segment plus all 19 patched locations match RAM.

**Unit-stats visual check passed; remaining contexts are pending.** The user
navigated manually and supplied `work/ui/ps2/unit_stats_font_0.1.0_user.png`.
Latin labels (HP/EN, Lv, SP, PP, NEXT, LL), dynamic numbers and Japanese text
are legible, without visible clipping, overlap or damaged unit/pilot art on
that screen. A fresh read-only RAM check still matches the complete segment
and all 19 patched locations, with no unknown CPU opcode warnings.
The screen contains no lowercase descenders; dialogue, other renderer contexts
and physical PS2 checks remain pending. Windows automated input still returns
`GetCursorPos failed: Access is denied (0x80070005)`, so the screenshot is user
evidence, not an automated capture. Physical PS2 testing is also pending. Use the copied card
and isolated profile under `work/build/ps2_font_test/`, PINE port 28012.

Build tools: `tools/build_ps2_font.py`, `tools/ps2_font4x.py`,
`tools/verify_ps2_font.py`, `tools/verify_ps2_font_runtime.py`,
`tools/pcsx2_pine.py`. Evidence:
`work/output/ps2_font_0.1.0_verification.json`,
`work/output/ps2_font_0.1.0_mips_verification.json`,
`work/output/ps2_font_0.1.0_runtime.json`. Details: `docs/ps2_vwf.md`.
Reject earlier trial ELFs, including the `v2` trial: they contain a generic
MIPS C.LT encoding unsupported by the R5900. The final uses function 0x34.
Save conversion remains deferred. No PS2 GitHub release or push is authorized.

## PSP continuation status — 2026-10-04

**Latest local testing build: 0.4.12 (2026-10-06).** Adds exactly one space
between each thought-dialogue speaker name and its opening parenthesis.
1,173 rows changed; all 1,176 thought rows pass, including the reported
Daisuke line. Commands, wording, line breaks and script allocation sizes are
preserved. Only MAP_ADD.BIN changes from 0.4.11. Shared `textfit.wrap` applies
the rule to future PSP and PS2 builds. Details: `docs/psp_spacing_0.4.12.md`.
ISO: `work/output/SRWMX_EN_0.4.12.iso` (1,317,414,912 bytes), SHA-256
`80f9d24f682884059742c89b0e60ab3a53f611ee384e0cb46b068b4478d9acae`.
Public release remains 0.4.9; no release, push or commit is authorized.

**Previous local testing build: 0.4.11 (2026-10-06).** Fixes Hero/Partner/Unit
rename choice alignment, the Options menu, music/demo row centering and
remaining Japanese music titles. All six screens have native-renderer visual
evidence. Includes the previous Level Up/narration fixes and passing regression
checks. Details: `docs/psp_fixes_0.4.11.md`. Local ISO:
`work/output/SRWMX_EN_0.4.11.iso` (1,317,414,912 bytes), SHA-256
`50e6440438778cc6da32d963c9500e0b4265afb6142bdc360913b55081600f58`.
Public release remains 0.4.9; no release, push or commit is authorized.

**Previous local testing build: 0.4.10 (2026-10-06).** Fixes the user's PSP
0.4.9 Level Up row corruption and opening narration buffer overflow.
The public release remains 0.4.9. No release, push or commit is authorized
for this build. Details and reproducible checks: `docs/psp_fixes_0.4.10.md`.
ISO: `work/output/SRWMX_EN_0.4.10.iso`; SHA-256:
`c4a7eca06a4606426c0f9109c4288ca2db474cb2ac507c7ecb908a0566026444`.

**v0.4.9 upgrade added from published v0.4.1.** Exact upgrade source SHA-256:
`cf4af0243dadd37718866d7ee1a6f1f8d8974d5f55dd827644227f4e58d1c7d5`,
1,313,292,288 bytes. Do not substitute the existing local ISO labeled 0.4.1;
it differs from the published output. The verified source was reconstructed
from the original Japanese ISO and downloaded published 0.4.1 patch into
`work/build/upgrade_041_to_049/SRWMX_EN_0.4.1_published.iso`.
Full and upgrade patches passed standard round trips to the unchanged 0.4.9
target. The upgrade is 853,344 bytes, SHA-256
`d5d8d5bc6f0a9cbc34a739df55631452f7f37a9fc81be896d283cabb6171b2da`.
Extended local assets: `work/output/release-v0.4.9-with-upgrade/`. The original
full patch and release tag/source commit stay unchanged. Current metadata lists
both source paths; the older eight-asset publication record below is historical.
All nine updated published assets were downloaded and verified. Scoped catalog
workflow 37215386850 passed; the live catalog matches the extended manifest and
offers the direct 0.4.1 → 0.4.9 route. Evidence:
`work/output/upgrade_0.4.1_to_0.4.9_local_verification.json` and
`work/output/upgrade_0.4.1_to_0.4.9_upload_verification.json`.

**Latest public release: 0.4.9.** Incremental update of 0.4.8 translating the native
intermission bitmap header in WND.BIN texture #0 to INTERMISSION. All other 31
ISO files are unchanged, preserving the intervening 0.4.4–0.4.8 story/UI fixes
listed in CHANGELOG.md. Verified on the actual intermission screen in isolated
PPSSPP with a copied save and texture replacement disabled; live native texture
bytes match the ISO. Capture: `work/ui/intermission_header_0.4.9_ingame.png`;
report: `work/output/wnd_headers_0.4.9_verification.json`. Reproduce with
`python tools/patch_wnd_headers.py work/output/SRWMX_EN_0.4.8.iso 0.4.9`.
The normal `redraw_wnd.patch_wnd` build path produces the identical WND asset.
The separate sortie-preparation bitmap header (#39) still awaits translation.
The project lead explicitly requested a GitHub release for 0.4.9 on 2026-10-04.
Published at https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.9
from commit `ce426bd4676df5c7ad24ea8d93605368dfed48af`. Full final-ISO readback and
Retro Trans round-trip validation passed. All eight uploaded assets were
downloaded and verified; the 2,391,967-byte patch has SHA-256
`117ffed761b914d675ccd86d27aaa3ef463fd2df3311e80e10f6e4b607079161`.
Local assets: `work/output/release-v0.4.9/`; publication evidence:
`work/output/release-v0.4.9-publication.json`. Scoped catalog workflow
37213984223 passed; the live catalog contains the exact release manifest.
Full-playthrough and physical PSP testing remain pending.
Any future build still requires its own explicit release instruction.
Earlier build evidence follows.

**Complete campaign baseline: 0.4.3.** Rebuilt from the original Japanese ISO with the
prologue and all translated groups through 58, including the ending, hidden
stage, unused scenes and closing/save messages. All 51,366 original readable
script uses and 98,686 unchanged commands passed finished-ISO readback.
Includes the native 4x font, all 67 chapter titles, battle quotes and current UI
work. Output: `work/output/SRWMX_EN_0.4.3.iso`; SHA-256:
`e3d88c4a93c355e2e79ca5a99b45ddabe9957cb3d08397e519b43b4f47c4b352`.
Reports: `work/output/campaign_0.4.3_inputs.json`,
`work/output/campaign_0.4.3_verification.json`, and
`work/output/campaign_0.4.3_runtime.json`.
Boot and copied-save loading passed in isolated PPSSPP with texture replacement
disabled; the live native font and all 18 hooks match. The actual map-script heap
has 262,144 bytes, separate from the 1,200,704-byte resource pool. All five enlarged
map scripts (s0210, s0950, s1040, s1050, s1060) passed native replacement allocation
and complete ISO-read comparison; the test scene's non-script allocations were retained and the
original map script/allocator restored. Native ending/closing loading also passed.
Exact ending text displayed in a temporary renderer probe; the ending scene itself
was not played. Reports: `campaign_0.4.3_scene_loading.json`,
`campaign_0.4.3_extra_scene_loading.json`, and `campaign_0.4.3_ending_renderer.json`
under `work/output/`. The public English exports restore all 59 canonical inputs
and reproduce all review fingerprints and preflight checks; evidence is
`work/output/campaign_0.4.3_restoration_audit.json`. Full playthrough and physical
PSP testing remain pending. The isolated
instance is `work/build/campaign043_test`, debugger port 45379. User emulator
settings and saves were not modified. No GitHub release is authorized.

**Earlier local build: 0.4.2.** Corrects the incomplete chapter-card coverage in 0.4.1:
all 67 scenario titles are now covered across 205 atlases (160 translated,
45 existing English copies preserved). Build is `work/output/SRWMX_EN_0.4.2.iso`.
Only `PACKMAPC2_ADD.BIN` changes; all other 31 ISO files match 0.4.1 exactly.
Reproduce with `tools/patch_chapter_cards.py work/output/SRWMX_EN_0.4.1.iso 0.4.2`.
Metadata: `work/translation/en/ui/all_chapter_cards.json`; report:
`work/output/chapter_cards_0.4.2_verification.json`. English preview sheets and
native test captures are in `work/ui/`. See `docs/chapter_cards.md` for layout,
palette handling and the scope of renderer probes. Story coverage is unchanged.
0.4.2 briefly became public before the user instructed that releases must wait
for explicit permission. It is now an unpublished GitHub draft and withdrawn
from the active Retro Trans catalog; 0.4.1 remains the public release. The tagged
source is `036a619be3c23b3abdfe8ee18182a47523ddeedf`, the verified full patch is
1,574,947 bytes and local assets are `work/output/release-v0.4.2/`. All eight
uploaded assets were downloaded and checked before withdrawal. A future
approved release should use a new version because the catalog withdrawal is
permanent. Do not publish any further release without the user's instruction.

Completed translation task: dialogue after stage 30 through the ending, using
Sol 6.1 Medium sub-agents. Keep source Japanese local and preserve initial
drafts, context decisions, measured fit checks and every route/scene use.
Stages/groups 31–58 are translated and reviewed: 16,661 fresh rows and 21,257
full rows across 235 packets. Coordinator review includes all unused scenes
and all 14 independent closing/save-message sketches. Every final line fits
the actual native font; original drafts, context, measurements and original-use
evidence remain. Legacy unused-scene reachability is unverified. Local insertion
is complete and targeted native loading/rendering checks pass; full playthrough
remains pending. No GitHub release is authorized. Queue:
`work/output/stages31_end_sol_medium_manifest.json`; review notes and tooling:
`docs/stages31_end_sol_medium.md`. These later translations are in local 0.4.3.

**Earlier released build: 0.4.1.** Published at
https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.1 in the now-public
repository. The 1,396,947-byte full xdelta patch is built against the original
Japanese ULJS-00041 ISO and reproduces the complete output SHA-256
`cf4af0243dadd37718866d7ee1a6f1f8d8974d5f55dd827644227f4e58d1c7d5`.
All uploaded assets were downloaded and verified before publication. Retro
Trans's scoped catalog refresh passed and the live catalog includes v0.4.1,
so Automatic mode can discover it. Release source tag pins commit
`db7bde279f8785a04e72bbc9617bd70cb73a1f03`; later documentation commits do not
change that tag. Final assets: `work/output/release-v0.4.1-optimized/`. The older
`release-v0.4.1/` directory contains an unpublished oversized encoder trial;
do not use it. `tools/build_release.py` now uses the whole source image as its
xdelta source window to handle ISO file relocation efficiently.

Incrementally patched the latest 0.4.0 ISO, which
already contains the prologue and stages 1–30 plus the 0.3.3 battle/UI/font work.
Added the requested Kaine closing line in its three `end_mes` uses and the stage
1 Super title-card lettering, **Visitors from the Beyond**. The title-card atlas
is in `PACKMAPC2_ADD.BIN`, pixel offset `0x14e1480`, not STATIC2's title strings.
It was located by matching the live GPU image against the original file. The
native patch edits only its first 40 rows. No emulator texture replacement.
Reproduction: `tools/patch_screenshot_text.py work/output/SRWMX_EN_0.4.0.iso 0.4.1`.
See `docs/chapter_cards.md` and the 0.4.1 verification report in `work/output/`.
The title was verified in-game with texture replacement disabled. Live pixels
match the patched atlas; screenshot: `work/ui/chapter_card_0.4.1.png`. All 30
other ISO files are byte-for-byte unchanged from 0.4.0. The Kaine line's three
ISO records and its two-line fit were checked; random save-message selection
has not been forced to that sketch for an in-game screenshot.

**Earlier font test build: 0.1.5.** The user requested Genei LateGo from
https://okoneya.jp/font/genei-latin.html. Latin glyphs now use the static Medium
font at 15 px without shadows. Japanese atlas cells remain unchanged. The
matching VWF table and all eight hooks are verified in the ISO; all 21,586
prologue/campaign rows pass font-fit checks. This test build contains the
prologue, as in 0.1.2. Build 0.1.4 additionally renders Latin from a native
4x atlas (60 px TTF rasterization / 72 px cells), at the same on-screen size.
The user explicitly rejected texture replacement: this is a native ISO patch,
with no texture pack. All renderer/width/glyph/height hooks and relocated code
were verified in an isolated PPSSPP instance, with texture replacement disabled.
Translated prologue dialogue displayed correctly. Screenshot evidence uses the
software renderer at PSP display resolution; 4x hardware screenshot, physical
PSP testing and campaign insertion remain pending.
Build 0.1.5 fixes cropped bottoms in g/j/p/q/y/comma: draw the complete 60 px
glyph on a 96 px temporary canvas before fitting it into the native atlas.
All other glyphs, widths and renderer code are unchanged. Complete FreeType
mask extents are checked to prevent recurrence. Packaged before/after preview:
`work/ui/font_descenders_0.1.5.png`.
The updated 0.1.5 atlas and relocated code were also matched in live PPSSPP;
a g renderer trace confirmed the larger atlas and unchanged 8 px advance.
Dialogue capture: `work/ui/font_native4x_0.1.5_dialogue.png`.
See `work/output/font_0.1.5_verification.json`, `docs/vwf.md`, and the accompanying
`work/output/SRWMX_EN_0.1.5_FONT_LICENSE.txt` for SIL OFL copyright/licence notices.

**Completed campaign:** numbered stages 1-30, including all listed routes,
translated with Sol 6.1 Medium using six distinct actual workers per stage in
waves. All 16,092 fresh rows across 241 packets validated; full stage assemblies
contain 21,024 stage-local unique rows with every original scene use retained.
Initial drafts, final packets, decision/fit reports and safe English-only copies
are preserved. Original Japanese remains in ignored local working files.

Coordinator reviewed all reused contexts and meaningful fresh flags against
original Japanese and actual scene neighbors. Source ambiguities, wordplay and
unverified licensed-label provenance remain explicit. Exact reviewed wording
is fingerprinted; all full checks pass with the current font width table.
Final audit: work/output/campaign_completion_audit.json.
Workflow and detailed stage reviews: docs/stages01_30_sol_medium.md.
Queue and actual agents: work/output/stages01_30_sol_medium_manifest.json.

Stage 30: 680 fresh rows, 9 packets, 839 full rows, 1,116 uses. Only 464/596 were
shortened after measured initial overflow; all full initial drafts retained.
Context fingerprint:
fbea801962973b4cd17812fd97c6f901e635e1f342aae9691302ff06db792430.
Stage 28 exact copies 502/689 were corrected using guarded contextual overrides;
earlier translation owners remain unchanged. Stage 29 full 487 retained after
independent review. Source-scoped Ryo/Dr. Plato corrections are documented;
original drafts and frozen speaker labels remain intact.

The campaign was subsequently inserted in 0.4.0 and retained in 0.4.1, as
recorded above and in the changelog. Complete gameplay validation remains
pending. Existing build/version records and previous comparison results below
are retained as historical context.

**Previous model-comparison work (2026-10-03):** fresh Sol 6.1 translations at Low, Medium,
High and XHigh are complete and posted to Translation Test 3, spreadsheet
`16nyBAPVH1OSQdYo8qMxxqmS5YtceGeK45DZt9prjuWQ`, original tab id 0 preserved.
Tags: `sol61low3`, `sol61med3`, `sol61high3`, `sol61xhigh3`; each has 376/376 rows,
zero final fit/character/placeholder/name findings. Five fresh contexts per effort;
model/effort verified in all 20 sessions. Header H:K contains candidates, L:M reviewer
fields; companion notes tab id 2000000103 contains 1,044 entries. All 1,528 posted
candidate occurrences and notes were verified, and exported layouts inspected.
Estimated Standard credits: Low 32.82, Medium 36.32, High 46.62, XHigh 70.78;
these exclude coordinator work and do not establish subscription charges.
Row 357 ASCII identifiers were independently checked to preserve exact game bytes;
Low/Medium report-only follow-up costs are included. See
`docs/stage30s_sol_effort_comparison.md` and the shared protocol
`docs/model_comparison_protocol_sol_effort.md`. Inputs/glossary and earlier sheets
are unchanged. Offline CSVs, drafts/reports, 48 safe copies and usage audits are saved.
Build stays 0.1.0; next is human wording selection/reconciliation, then an in-game build.

**Earlier completed work (2026-10-03):** user requested a fresh retranslation under the updated `BASE_RULES.md`, with Luna
excluded, into spreadsheet `18CicqkxXHZezKS8AsOL27dT8CBsfLrHRP8ArL61Fn5k` ("Translation Test 2",
`Stage 30 Space` id `1180054200`, notes id `2028606084`). Sol 6.1, Astra 6 and Terra 5.6 reruns are
complete under tags `sol61r2`, `astra6r2`, `terra56r2` (376/376 rows each, all fit). See
`docs/model_comparison_protocol_r2.md`. The new sheet already has `opus2`, `sonnet2`, `fable2`
translations under the same updated rules; keep these and the Prompt tab unchanged. Event-order
context is provided to every new translator, matching the Claude reruns. Luna is absent in this
destination and is excluded. The completed sheet has six candidates, with OpenAI columns K:M and
reviewer columns N:O. All 1,146 new translation cells and 719 new notes were read back and verified;
existing Claude/reviewer values, formatting and the entire Prompt tab were preserved. Raw spelling
findings are flagged separately: Sol/Terra 287 (Jamitov Hymem vs Akurasu Hymen), Terra 308
(Guiltor vs glossary Guiltorre). Shared glossary unchanged; no raw spelling reconciliation.
See `docs/stage30s_updated_rules_openai.md` for measurements, conditions and verification.
Six-way offline CSV/notes are `work/output/stage30s_comparison_updated_rules*.csv`, with metrics,
summary, preserved full drafts and 36 new safe JSON copies. Exact instructions are saved as
`BASE_RULES_r2.md` / `TRANSLATOR_BRIEF_r2.md` in the script folder. Build 0.1.0 is unchanged.
Token usage and model/effort settings have now been recovered from session metadata; see
`docs/stage30s_translator_usage.md`. These estimates exclude coordinator work and do not establish
actual subscription charges. Next: human wording selection and reconciliation, then a separately
versioned in-game build.
The earlier comparison below is retained as a historical record.

### Earlier comparison under original rules

The requested **Sol 6.1, Astra 6, Luna 6 and Terra 5.6** candidates are complete and posted. Each
translated all 376 rows in five fresh contexts. All rows fit; Luna and Terra each have one raw
Galfa/Gulfer spelling mismatch at id 57, preserved for comparison and flagged separately in the notes
tab. See `docs/stage30s_openai_comparison.md` for requested model ids, metrics and verification.

The live sheet now contains **nine candidates**. New columns M:P hold these four models; reviewer
columns moved to Q:R. All 1,528 new translation cells and 222 new notes were verified, along with
unchanged existing cell values, formats, validation and cell notes. Existing tabs and ids are intact.
Local exports are `work/output/stage30s_comparison_openai_models.csv` and its `_notes.csv` companion.
Each new tag has five full drafts, five raw slices, reports, merged/check files and `.en.json` copies.
Luna/Terra merged files are marked `comparison_only` due to the known spelling error; all raw
candidates need selection and semantic reconciliation before production use.

The preceding single-session candidate remains available as a separate baseline:

The `codex` OpenAI-session candidate is complete: five independently translated slices, 376/376 rows,
no fit/structural errors, 37 uncertainty rows. Full first drafts and final slices are preserved, with
English-only `.en.json` copies. See `docs/stage30s_codex_review.md` for methodology and review details.

New local exports: `work/output/stage30s_comparison_codex.csv` and
`work/output/stage30s_comparison_codex_notes.csv`. They contain all five candidates in play order.
The [online sheet](https://docs.google.com/spreadsheets/d/1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY#gid=886392675)
initially gained the five candidate columns. At the user's request, the Codex column was inserted before the
reviewer columns, and 123 Codex notes were appended to the existing notes tab. All 382 posted
occurrences and the notes were verified, along with unchanged existing cell values, formatting,
validation and cell notes. Reviewer selections/comments were empty at update time. Existing sheet
IDs were retained; a pre-update snapshot and result are in ignored `work/output/`.
Build 0.1.0 is unchanged; Stage 30 remains uninserted.

Next: review the new candidate, reconcile the recalled wording in rows 190/334 and unresolved terms,
then select production text before building. All requested sheet updates are complete. The older
Codex session candidate is identified by the 2026-10-03 session metadata audit as gpt-6.1-sol at
High effort. Sol overrides used Low; Astra, Luna and Terra used Medium. See
`docs/stage30s_translator_usage.md` for all recovered counts and Standard credit estimates. Use the newer `tools/update_review_sheet.py` for in-place additions rather than
recreating existing tabs.

## 1. What this project is

An English fan translation of *Super Robot Taisen MX Portable* (PSP, ULJS00041). The user owns the ISO
(`Super Robot Taisen MX Portable (Japan).iso` in the project root). Project root: `E:\Projects\SRW MX`.

Read these first, in this order. They are binding:

1. `AGENTS.md` — folder layout, versioning (0.x.y), "always write a change log", and the REMEMBER list:
   - releases must work with Retro Trans Tools;
   - akurasu.net is the main source for terms;
   - **Japanese script text must never be committed to git** (local working files are fine).
2. `BASE_RULES.md` — how to translate and proofread (80-row slices, read neighbouring rows, restore
   dropped subjects, never infer gender from a name, report uncertainty, dry-run scripts).
3. `docs/CHANGELOG.md` — what was done, newest first.

## 2. State of the work

| Area | State |
|---|---|
| ISO analysis | Done. `docs/japanese_text_report.md`, `docs/static2_format.md`, `docs/stage_map.md` |
| Glossary | Done, akurasu-first. `work/glossary/glossary.json` (22 series, 279 characters, 260 units, 382 weapons, 723 terms). Rules in `docs/glossary_decisions.md` |
| Library (encyclopedia) | Translated (248 robot + 264 character entries), not yet inserted into the game |
| Variable-width font | Done and working in PPSSPP. `docs/vwf.md` |
| Prologue script | Translated (562 lines) and inserted. Build `work/output/SRWMX_EN_0.1.0.iso` |
| Stage 30, Space route | Original-rules sheet: 9 historical candidates. Updated-rules "Translation Test 2": 6 candidates (Opus, Sonnet, Fable, Sol 6.1, Astra 6, Terra 5.6), Luna excluded. Local comparisons saved. **Not inserted into a build** |
| Everything else | Japanese: other stages, menus, opening narration, battle quotes, default hero names |

Build 0.1.0 was booted in PPSSPP 1.20.4 and played into the prologue map's opening dialogue. Nothing
past that point has been seen on screen. Not tested on real hardware.

## 3. The task being handed over: add OpenAI models to the stage 30 comparison

The human reviewer compares translations side by side in this sheet:
`https://docs.google.com/spreadsheets/d/1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY` (tab "Stage 30 Space").
Columns today: `#`, Part, ID, Kind, Speaker (JP), Japanese, Speaker (EN), Opus 5.5, Sonnet 5.5,
Haiku 4.5, Fable 5.1, Best (model), Reviewer comment.

To add a model, produce its translation files and re-post. Keep the conditions identical to what the
Claude models had, or the comparison is not fair.

### 3.1 Input

`work/translation/en/script/stage30s.json` → `rows` (376 rows, `id` 0–375, in play order).
Fields: `id`, `jp` (raw line), `kind` (`dialogue` / `thought` / `plain`), `speaker_jp`, `speaker_en`
(pre-filled from the glossary), `body_jp` (the text to translate; `@` = line break in the Japanese box),
`uses` (scene:index).

If the file is missing (it is git-ignored), regenerate it — this reproduces it exactly:

```bash
python tools/extract_iso.py "Super Robot Taisen MX Portable (Japan).iso"
```
```bash
python tools/export_rows.py work/build/iso/MAP_ADD.BIN work/translation/en/script/stage30s.json i06s1b s06s10 i06s1a --exclude work/translation/en/script/prologue_merged.json
```

### 3.2 Instructions each translator received

The instructions every comparison candidate so far was given are frozen in
`work/translation/en/script/`: `TRANSLATOR_BRIEF_v1.md` and `BASE_RULES_v1.md`. To add another candidate
to the **existing** comparison, give it those two v1 files unchanged.
The live `BASE_RULES.md` has since gained five rules adapted from LinguaGacha's prompt template (one row
in / one row out, spoken register, a two-step context/decisions check per row, translate what the player
reads and leave what the game reads, no softening). Use the live files for new translation work.
Output produced under the live rules is not comparable with the v1 candidates unless those are re-run.
Each Claude translator got one slice and this task text (only the model tag and slice numbers differ):

> Translate a slice of the Super Robot Wars MX Portable script (stage 30, Space route: "Break through the
> Falcon") into English. Read TRANSLATOR_BRIEF.md and BASE_RULES.md (both binding). Input: stage30s.json.
> YOUR SLICE: rows with `id` X to Y inclusive. Read neighbouring rows for context as the brief requires.
> For every row write the English `en` (and `speaker_en` if empty). Check EVERY row with
> `python tools/textfit.py "<speaker_en>" "<en>"`; it must print FITS (3 lines x 352 px). Glossary:
> work/glossary/glossary.json; fixed spellings: work/glossary/do_not_touch.json. Write the result to
> stage30s_<model>_slice_<N>.json. Do not read any other stage30s_*_slice_*.json file: other translators
> are working on the same rows independently and the results will be compared. Final message: rows examined
> vs rows in slice, rows that needed compression, rows that do not fit, and your uncertainties.

Slices: 0 = ids 0–79, 1 = 80–159, 2 = 160–239, 3 = 240–319, 4 = 320–375. One fresh context per slice.

Conditions to keep equal:
- The translators could run tools (they checked fit themselves and could read the glossary and the
  finished prologue). If the OpenAI models are called through a plain API without tools, say so in the
  results, and run the fit check for them afterwards (§3.4) — expect more overflowing rows.
- They saw only the Japanese of rows outside their slice, never another translator's English.
- The input did **not** mark event boundaries on the battle map. `stage30s_order.json` now has them
  (see §5). Do not give it to the new models for this comparison; do use it for real translation work.

### 3.3 Output format

One file per slice: `work/translation/en/script/stage30s_<model>_slice_<N>.json`, UTF-8:

```json
{"slice": 0, "rows": [{"id": 0, "speaker_en": "Vega", "en": "English body only", "notes": "", "uncertain": ["..."]}]}
```

- `en` is the body only: no speaker name, no brackets. Dialogue/thought rows: one continuous text, no
  `@` (the build wraps). Plain rows: same number of `@`-separated lines as the Japanese.
- ASCII only: letters, digits, space and `, . : ; ? ! / ~ ' " ( ) [ ] + - = $ % & *`. `...` for ellipses.
- Keep placeholders verbatim: `#男愛称` `#女愛称` `#男姓名` `#女姓名` `#部隊名` `#機体名`.
- `<model>` is a short tag without spaces or `=` (e.g. `gpt5`).

### 3.4 Check, then post

Limit of the dialogue box: **3 lines × 352 px**, measured in the game. About 47 characters per line
on average; letters are 4–12 px wide, so use the tool rather than counting:

```bash
python tools/textfit.py "Ruri" "Your English line here."
```
```bash
python tools/textfit.py --check work/translation/en/script/stage30s_gpt5_slice_0.json
```

`--check` measures every row as a dialogue line, so it is right for dialogue and thought rows but not
for the two plain rows (ids 151, 152: check each `@`-separated line against 352 px yourself). A fuller
check is described in §6 "Checks". Then re-post with the new model appended (names after `=` become
the column headers; reviewer input already in the sheet is carried over by line ID):

```bash
python tools/post_sheet.py "C:\Users\Binh\Downloads\windy-renderer-507117-d4-2bb59e962d84.json" 1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY work/translation/en/script/stage30s "Stage 30 Space" "opus=Opus 5.5" "sonnet=Sonnet 5.5" "haiku=Haiku 4.5" "fable=Fable 5.1" "gpt5=GPT-5"
```

The sheet is shared with the service account `claude@windy-renderer-507117-d4.iam.gserviceaccount.com`
(Editor). The key file stays in the user's Downloads folder; do not copy it into the project.
Posting replaces the tabs "Stage 30 Space" and "Stage 30 Space notes" and touches nothing else.
Offline alternative: replace the first two arguments with `csv work/output/stage30s_comparison.csv`.

Post each model's **raw** output. Do not fix its spelling errors first; the reviewer should see them.

### 3.5 What the Claude runs showed (baseline for comparison)

All four translated 376/376 rows and no dialogue line overflowed (measured independently).

| | Opus 5.5 | Sonnet 5.5 | Haiku 4.5 | Fable 5.1 |
|---|---|---|---|---|
| Wrong glossary spellings | 0 | 0 | 9 ("Lagou" ×8, "Galfa" ×1) | 0 |
| Problems in the 2 condition rows (ids 151, 152) | 0 | 0 | 3 | 0 |
| Rows with a flagged uncertainty | 68 | 54 | 0 | 75 |
| Messages using all 3 lines | 47 | 35 | 26 | 70 |
| Total English characters | 21,757 | 20,615 | 19,138 | 22,716 |

The Claude runs used the Claude Code default effort for each model; effort was not varied.
The reviewer's picks ("Best" column) were not in yet at handoff.

## 4. How the game stores what we translate

- **Scripts**: `MAP_ADD.BIN`, 203 `SRWL` blocks from sector 0x579C. Each = header, commands (0x30 bytes
  each), then a pointer table and Shift-JIS strings. Names like `s06s10` (map) / `i06s1b` (scene before) /
  `i06s1a` (scene after) come from tables in `BOOT.BIN`. Full mapping: `docs/stage_map.md`.
- **Play order**: opcode 0x0B shows a message (arg 2 = string index), 0x0C shows two at once, 0x58 shows a
  victory/defeat condition, 0x6D plays a scene, 0x7E/0x7F delimit map events. `tools/play_order.py`.
- **Font and text drawing**: `docs/vwf.md`. English is stored as full-width Shift-JIS (2 bytes per
  letter); the patch gives those glyphs their own widths.
- **Names, library, help text**: `STATIC2_ADD.BIN`, `docs/static2_format.md`.

## 5. Tools (all in `tools/`, Python 3.8)

| Tool | Purpose |
|---|---|
| `extract_iso.py` | Pull BOOT / MAP_ADD / STATIC2_ADD out of the ISO into `work/build/iso/` |
| `static2_extract.py`, `stage_map.py`, `make_batches.py` | Rebuild `work/source/` (names, library, stage map) |
| `akurasu_terms.py`, `merge_glossary.py` | Refresh akurasu terms; merge glossaries and fix names (`--apply`) |
| `export_rows.py` | Export a scene's lines for translation (`--exclude` skips lines already done) |
| `play_order.py` | Play order + event boundaries of a stage → `<scene>_order.json` |
| `textfit.py` | Encode English and measure it against the dialogue box |
| `merge_slices.py` | Merge slice files into `<scene>_merged.json` and check them |
| `post_sheet.py` | Post a multi-model comparison to the Google Sheet (or CSV) |
| `update_review_sheet.py` | Preview and append new candidates in place; preserve and verify existing reviewer/candidate cells |
| `check_translation.py`, `export_model_comparison.py` | Check candidate slices and preserve raw review errors; export nine-way comparison and safe copies |
| `build_patch.py` | Build the patched ISO (`work/output/SRWMX_EN_<version>.iso`) |
| `vwf_patch.py`, `make_latin_font.py`, `native_font4x.py` | VWF, original-size Latin atlas and native 4x font patch |
| `ppsspp_dbg.py`, `nav.py`, `boottest.py` | Drive PPSSPP through its debugger; boot-test an ISO |
| `strip_jp.py` | Write `*.en.json` copies without Japanese script — run before any git commit |

Build command used for 0.1.0:

```bash
python tools/build_patch.py "Super Robot Taisen MX Portable (Japan).iso" 0.1.0 --scenes-file work/translation/en/script/prologue_merged.json
```

## 6. Things that will bite you

- **Environment**: Windows, Git Bash, Python 3.8 **32-bit**. Set `PYTHONIOENCODING=utf-8` or printing
  Japanese crashes. In bash heredocs, backslashes inside Python source get mangled (`'\n'`, `'\\'`,
  `'\0'`); write scripts to files or avoid backslash literals. Google libraries print version
  warnings on every run; they are harmless.
- **`textfit.py` needs `work/build/STATIC2_ADD.BIN`** (the atlas with Latin glyphs). If it is missing,
  run `extract_iso.py`, then
  `python tools/make_latin_font.py work/build/iso/STATIC2_ADD.BIN work/build/STATIC2_ADD.BIN`.
- **Do not put code at 0xE4EAC in BOOT.BIN.** It looks unused but is called once at boot from code in
  `.data`. The patch lives at 0x250944. BOOT.BIN is relocatable: any patched instruction that holds an
  address needs a relocation entry (`vwf_patch.patch_boot` handles this).
- **Script size and shared memory.** The build ceiling is 0x40000, while the actual map loader
  uses a 0x40000-byte heap shared with other allocations. Local 0.4.3's five enlarged scripts
  (largest 0x32000) passed native replacement allocation and ISO reads with existing non-script
  allocations retained. This does not prove peak memory use throughout every map event.
- **The build only rewrites scenes listed in the rows' `uses`.** Shared defeat lines are therefore
  translated only inside the scenes that have been built, not game-wide.
- **PPSSPP**: the debugger needs `RemoteDebuggerOnStartup = True`, `RemoteDebuggerLocal = True`,
  `RemoteISOPort = 45373` in the user's `ppsspp.ini`. The user approved this once; a backup is at
  `work/ppsspp.ini.backup` and the settings were restored afterwards. Ask before changing them again.
  The debugger's screenshot call fails on this machine; `ppsspp_dbg.Dbg.grab_window()` captures the
  window instead. Use `Dbg.tap()` for input; on the favourite-series screen Circle selects and the
  carousel then rotates by itself.
- **Checks**: the per-model check used for the table in §3.5 was a one-off script (completeness, fit,
  allowed characters, placeholder counts, old spellings from `work/glossary/name_fixes.json`). Its
  result is in `work/translation/en/script/stage30s_checks.json`. `merge_slices.py` has the same logic
  for a single set of slices.
- **Not a git repository yet.** `.gitignore` is in place. Run `tools/strip_jp.py` before the first commit.

## 7. Open items

Translation quality:
- Glossary gaps hit by several translators: Operation Moonraker, "junior science trainee" (Hokuto's
  and Ginga's cover story), Zeon Zum Deikun, Jamitov Hymem, Core 258, Little Baam, Ereism.
- Glossary inconsistencies: the short form of the Gulfer Emperor still says "Galfa Emperor"; one
  character entry says "Omzack of the Thunder" (the unit is "Omzack of the Lightning").
- Row 334 quotes row 190; the two must match in the final text.
- Spirit Command names: akurasu's literal names are in use (Hot Blood, Sure Hit…); the user has not
  yet said whether to switch to the official English names (Valor, Strike…).
- "Shuffle Alliance" is used (akurasu); the official SRW T English says "Shuffle Union".

Technical:
- Measure the victory/defeat condition window; the Japanese there is wider than 352 px.
- Default hero names shown through placeholders, the opening narration and all menus are still
  Japanese (they live in BOOT.BIN / STATIC2_ADD.BIN).
- The current Latin font is Genei LateGo v2 Medium (SIL OFL 1.1). Keep the
  complete source copyright/licence notice alongside redistribution. See `docs/vwf.md`.
- Insert the library translation (needs re-wrapping to its own window, not yet measured).
- Scenes `s0760`, `i076a/b`, `i063b` look unused; confirm in the emulator before skipping them.
- Check Retro Trans Tools' patch format before the first release.
- Battle quotes (`BATTLE2.BIN`) record layout is not decoded.

Waiting on the user:
- Reviewer's picks in the sheet, then tally per model and per kind of line.
- Whether to read the script pool capacity with the debugger now.
