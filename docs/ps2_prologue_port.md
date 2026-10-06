# Native PS2 Prologue port — local 0.1.8 candidate

0.1.8 fixes chapter numbering after the added Prologue. Native Hero +0x5f0
counts every cleared battle; the original title animation adds one, producing
Chapter 2 for the first story card. `tools/ps2_prologue_numbering.py` changes
only the four display copies at 0x348634, 0x3489b4, 0x224f08 and 0x2fe7cc.
The first story card receives Chapter 1, objectives use the same convention,
and native clear counts, campaign/save state and the 0.1.7 entry fix remain.
`tools/verify_ps2_prologue_numbering.py` passes 64 actual native card-animation
cases and 24 native objective-number cases for both robot routes, reproducing
the old display behavior from restored original instructions. This avoids a
dependency on an archived 0.1.7 executable. 0.1.8 card visual acceptance remains
pending; these checks validate native animation arguments and window numbers.

0.1.6 skips the Prologue on New Game: completion event 0x2d6 hard-codes
deployment group zero in both branches (0x134d88 / 0x134da8). Updating STAGE
alone did not change this path. 0.1.7 changes both arguments to group four
and wraps the initial campaign advance at 0x134dc0 to set the matching
campaign group. Initial history remains slot zero; ordinary map selection's
history increment is deliberately not used for the initial battle.

`tools/verify_ps2_prologue_entry.py` executes native event dispatch, battle
argument storage and campaign advance for both robots and balance modes,
intercepting only window/animation services. It reproduces group zero on
the old executable and requires group four on the corrected executable.
The previous scene/deployment tests did not execute this New Game event.

The playable PSP Prologue is inserted before the original first two maps on
both the Cerberus and Garmraid routes. This candidate retains the English
PS2 campaign, native Genei 4x VWF and selectable enemy HP/funds balance.
The other added PSP stage is outside this historical 0.1.8 build. Local
0.1.9 adds it; see `docs/ps2_stage30_port.md`. No release is authorized.

The 40x40 battlefield is native map 390. Its original PS2 layout is identical
to the PSP layout, as is the original terrain table. Its existing 640x640
selection image is reused from PS2 scenario s03s40. No PSP mesh conversion,
emulator texture replacement or substitute battlefield is required.

Eight scene blocks are added, with 200 total script blocks. Native script
name/sector lookups use extended tables in the added executable segment.
Two UNTD version-910 deployments occupy previously empty chapter/group
slots (0,4) and (1,4). Both use the original two-unit placements. The PSP
Researcher record fills unused PS2 pilot slot 433 with a new English name;
its source portrait ID is already the no-face sentinel. Other pilot and
gameplay records retain their original IDs and values.

The original English opening runs before each Prologue battle. Original
stage-1 maps call the corresponding PSP stage-1 introduction afterward,
so the opening is not repeated. Battle and intermission event commands
retain their original order and jump indexes. All used opcodes have native
PS2 dispatch entries.

STAGE gains location/scenario records 66 and 67. Existing scenario IDs,
chapters and later route choices are retained. The first two chapter lists
now contain Prologue followed by their original maps. A separate repair
restores all fourteen chapters' numeric progression fields: earlier builds
wrote chapter names into 64 bytes, although the actual name field is only
56 bytes. The clean scenario builder now uses the correct boundary.

Execution checks run the actual PS2 script name, size and read routines for
all eight scenes, both unit-deployment readers, both route selectors and
six native campaign save-field round trips. File reads are supplied by the
test harness; these are not full battle-clear or memory-card gameplay tests.
The FIX directory and all existing gameplay rows are also checked.

Rebuild with `python tools/port_ps2_prologue.py`; use `--prepare-only` to
prepare resources before execution checks. Run
`python tools/verify_ps2_prologue.py`. The builder preserves 0.1.5 and the
original discs, checks the source hash, retains unrelated file extents,
updates both disc filesystems and stays within single-layer DVD capacity.

To retain an already packaged 0.1.7 disc, prepare the corrected ELF/resources
under `work/build/ps2/prologue_0.1.8`, then use
`python tools/update_ps2_difficulty_build.py --source-version 0.1.7 --version 0.1.8 --feature prologue`.
This verifies New Game entry, chapter numbering, existing Prologue loaders, font, translations
and difficulty, then appends only the corrected executable and rehashes all
preserved disc resources. Both disc filesystems must read the same ELF.

Both Prologue battles now reach their mission/objectives screen in isolated
PCSX2 on 0.1.7: Garmraid with PS2 balance, Cerberus with PSP balance. Live
deployment headers and campaign state agree on map 390, group 4 and initial
history slot zero. The UI test used an owned New Game unit-setup checkpoint
with only three corrected entry words and the added entry routine migrated;
the packaged ISO's fresh boot and loaded executable were checked separately.
Evidence: `work/output/ps2_prologue_0.1.7_runtime_entry.json` and the two
`work/ui/ps2/prologue_0.1.7_*_objectives.png` screenshots. The objective
footer still used original stage 1's number/title in 0.1.7. 0.1.8 fixes its
number; the title remains a follow-up issue. Its two callers need to map group
4 to location index 0 and groups 0/2 to indexes 1/2 in chapters 0/1. Keep the
shared title getter unchanged because history already supplies location indexes. The native event tests cover both robots in both balances.

Acceptance still requires clearing both battles and saving/loading
in PCSX2, then physical-console testing. Use a new game and a separate test
memory card: migration of existing saves' first-chapter location indexes is
not implemented in this candidate. Do not overwrite an existing campaign
save or load a Prologue save in an unpatched PS2 game.

The packaged disc boots in isolated PCSX2 2.8.2. All added code, hooks and
loader tables match live memory; the opening movie and English dialogue in
the title-screen battle demo were observed, with no opcode/TLB warnings.
See `work/output/ps2_font_0.1.6_runtime.json`. Short automated controller taps
were missed between game polls; isolated PCSX2 toggle macros now hold buttons
long enough to enter New Game. See the handoff for controls. Its profile is
`work/build/ps2_prologue_test_0.1.6/emulator`, PINE 28017.

Preliminary analysis of the other PSP-only stage identifies native PS2 map
90 (24x32). Its layout header exists on both platforms, but its binary map
records differ. Do not copy that PSP map or claim its battle validated from
this comparison alone. Analysis is recorded locally in
`work/output/ps2_stage30_map_analysis.json`; stage 30 remains outside 0.1.8.
