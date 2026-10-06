# PSP second extra scenario — local PS2 0.1.9 candidate

0.1.9 adds PSP scenario 30, **Zeorymer Sorties at Dawn**, together with its
reworked scenario 29, **What Gnaws at the "Heart"**. PSP s0570 is scenario 29,
and s0560 is scenario 30. Earlier preliminary notes calling s0570 the extra
scenario 30 were inaccurate. See the [PSP scenario list](https://srw.wiki.cre.jp/wiki/全話一覧/MX_PORTABLE)
and [original PS2 list](https://srw.wiki.cre.jp/wiki/全話一覧/MX).

The existing first five locations in chapter index 7 retain their IDs. New
location/scenario 68 uses deployment group 12 before existing location 34,
group 10. The native seven-slot list is now `[29,30,31,32,33,68,34]`.
No campaign save structure grows. Existing save migration is not implemented:
test with a new game and a separate card. Stage 29's closing scene retains
the PSP route-choice events before the new stage 30.

Six reviewed English scenes replace the three original s0560 scenes and add
the three s0570 scenes. The executable's scene name/sector tables now have
203 entries. Every readable source string has a translation, scene-name
references resolve, and all event operands and jump indexes retain their PSP
positions. The native PS2 script buffer limit is checked for every block.

Nine PSP command-179 entries switch/wait for the BFACEPAK portrait cache.
PSP ELF pointers are virtual addresses, with file offset VA + 0x60. The
actual handler is 0xae3b8, calling cache setup 0x5890c and readiness 0x58ab0;
it is not itself a no-op. PS2 uses native portrait assets. The new Aqua
variants reuse native portrait and translated battle-caption bank 315.
Those nine cache commands become native PS2 no-op 178, whose real handler
0x306a20 returns completion value 2 with no object side effects. Opcode 0
is a window wait and must not be used as a no-op. Native execution checks
exercise both cache mode operands and preserve stack/object data.

Both battles use native PS2 map 90 (24x32). All 768 terrain IDs match the PSP
map; corner-height values differ by platform. The whole original PS2 map,
mesh and selection image remain. Deployments contain 132 and 46 records.
The missing enemy Dragoon row 156 reuses native PS2 enemy Dragoon 69 and
weapons 301–304, avoiding PSP attack-animation selector IDs. Optional PSP
balance gives the added row its source HP/reward (3900/2000); original PS2
balance uses native values (3900/2500). Existing rows remain unchanged.
Pilot rows 431/432 retain the PSP variant stats with native Aqua name,
portrait, library, voice and caption references. Researcher 433 is retained
from the Prologue port.

Animation 166 clones the original native chapter-card animation and supplies
the English stage-29 title. The existing stage-30 card and its selection
title are renamed to **Zeorymer Sorties at Dawn**. Native indexed palettes
and animation commands remain. There are no emulator texture replacements.
The two objective-title callers remap deployment groups to location indexes;
the shared history getter remains unchanged. This also repairs the Prologue
objective footer to show the correct title.

`tools/verify_ps2_stage30.py` executes all six native scene name/size/read
paths, both deployment loaders, all seven location selectors/history entries,
eight branch-unlock masks, three campaign save-field round trips, eight
objective title cases, both native card paths for stages 29/30 and the new
card player's actual archive reads. It models only five original EE
conditional-move instructions unsupported by Unicorn and supplies file/draw
services. Font, English text hooks, both balances, Prologue loaders, New Game
entry and chapter-number regressions also pass.

These execution fixtures do not constitute a full battle clear. Stage 29/30
playthrough, in-game memory-card save/load and physical-console validation
remain pending. No GitHub release is authorized for this build.

Rebuild with `python tools/port_ps2_stage30.py`. `--prepare-only` prepares
resources without packaging. Run `python tools/verify_ps2_stage30.py` to
repeat execution checks and `python tools/package_ps2_stage30.py` to package.
Existing output ISOs are protected from overwrite. Packaging starts from the
original Japanese ISO and appends only current translated resources, avoiding
accumulated superseded resources. All 37 files are verified, both ISO9660 and
UDF read identical replacements, and the disc fits single-layer DVD capacity.

Evidence: `work/output/ps2_stage30_0.1.9_execution.json`,
`work/output/ps2_font_0.1.9_verification.json`.

The packaged 4,521,150,464-byte ISO boots fresh in isolated PCSX2 2.8.2.
Read-only PINE checks confirm the full 763,516-byte added segment, every
patch hook and the script/map tables match disc bytes. The opening FMV is
visible, with no unknown CPU-opcode or TLB warnings and texture replacement
disabled. English Shinji dialogue in the title-screen battle demo was also
observed at 4x rendering. This is a boot check, not a stage-29/30 gameplay clear. Report:
`work/output/ps2_font_0.1.9_runtime.json`. ISO SHA-256:
`547878052851c158d40154557803c5b647b720ed8ffae12b41ad58acf59c3428`.
