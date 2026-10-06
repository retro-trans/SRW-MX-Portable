# PS2 roster and System fixes — 0.1.13

This local candidate extends 0.1.12 with native executable text and layout
corrections. It retains the PSP opening, both extra scenarios, selectable
balance and the native 4x VWF. No emulator texture replacement is used.

| Screen | English changes |
| --- | --- |
| Roster upgrade/terrain view | Wpn and Cost fit the narrow scrolling columns; existing Air/Lnd/Sea/Spc labels retained |
| Roster weapon/range view | Und, Rng, P.Rng and Atk headings fit their columns |
| Roster footer | Allied Units, Status/Edit/Info and Will from 0.1.12 retained |
| Objectives | Actual screen-header reference translated to Objectives |
| System | Grid, Sound, BGM Source, BGM Switch, Rumble, Unit Display, Cursor and Rotation |

System choices read ON/OFF; Stereo/Mono; Each/Unit/Pilot; Fixed/Switch;
Std/Type/Blink; Screen/Map; and 90 deg/Free. Each denotes an individual
unit/pilot BGM setting. The native controls and stored option values remain
unchanged. Std abbreviates the standard unit display mode.

The Objectives screen uses a separate literal from the translated map-menu
entry. It follows a nonzero structure field, and its pointer is loaded in
the title call's delay slot. The ordinary source-boundary scan missed it.
Both instructions forming this screen's pointer now address the English pool.

The System screen also forms several labels in branch delay slots and shares
high address halves with unchanged ON/OFF strings. Nine local draw hooks
translate the selected literal before calling the native VWF renderer. Two
roster Repair draw paths use the same lookup, showing Cost in that context.
Unknown pointers pass through unchanged. The preceding header/footer fixes
remain active; no campaign or database resource changes are introduced.

The native tests execute all 18 legal setting selections, all 26 labels and
choices per selection, 14 roster descriptor draws, both direct Cost draws,
the actual Objectives header call and unknown-pointer fallback. They check
label/choice separation using the game's coordinates and glyph advances,
and confirm every option value and all prior resource files are unchanged.
The test backend supports the original EE MOVN/MOVZ instructions in delay
slots. Only palette and final graphics services are intercepted.

Roster headings use at most 52 pixels at the 24-pixel font, leaving at least
8 pixels in a 60-pixel column interval. The original horizontal scrolling
behavior, partial adjacent columns, row values and series names are retained.
These checks establish native text routing and geometry; complete in-game
visual confirmation and physical PS2 checks remain separate.

Build: `python tools/fix_ps2_roster_system.py --build`.
Checks: `python tools/verify_ps2_roster_system.py`.
Evidence: `work/ui/ps2/roster_system_0.1.13/`.
Outputs: `work/output/`. No GitHub release is authorized for this build.

Final ISO: `work/output/SRWMX_PS2_EN_0.1.13.iso`, 4,663,267,328 bytes.
SHA-256: `31ad4fcdc7effccade0fefc78d100d6f8d33cbb7bc7f4ea1cbac0a0167e9ebd0`.
All 37 disc resources and ISO9660/UDF records pass verification. A fresh
PCSX2 2.8.2 boot loads the complete new executable segment and all 117
recorded hook/reference words correctly at 4x rendering, with no CPU-opcode
or TLB warnings. Visual confirmation of the four reported panels is pending.

Boot the new ISO fresh when testing. An older emulator save state restores
the old executable and cached labels; memory-card loads use the new disc code.
