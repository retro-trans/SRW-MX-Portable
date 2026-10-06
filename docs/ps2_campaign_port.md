# PSP to PS2 translation port — local 0.1.3

The local ISO is `work/output/SRWMX_PS2_EN_0.1.3.iso`. It retains the PS2 game
commands, routes, mechanics and numeric database records. PSP translations
are matched against PS2 source strings instead of copying PSP table IDs.
Source script remains in ignored local files; public mappings contain English
and source hashes. Original discs and earlier builds are preserved.

| Area | Inserted coverage |
| --- | --- |
| Story | 49,659 readable slots, 186 scenes; all 192 command arrays preserved |
| Battle captions | 51,434 entries, 370 pilot blocks |
| Database names | 1,499 translated names/terms/credits |
| Database descriptions | 248 unit and 264 pilot profiles; 32 spirits, 49 skills, 53 abilities, 37 parts, 507 help entries; remaining entries are dummy |
| Scenario text | 14 chapter names, 66 scenario records, 132 title fields, 66 summaries |
| Native title artwork | All 198 atlases representing 66 scenario records |
| Terrain | 404 nonempty names among 630 records; numeric attributes preserved |
| Executable/window UI | 776 translated string locations, 32 spirit names, 23 icons, intermission header |
| Narration | Opening and ending, with PS2 timing and final player-name line preserved |
| Font | Native 4x Genei LateGo VWF, corrected shared baseline |

The port is not a complete visual acceptance pass. Shared battle/status atlas
artwork, the Sortie Prep header and other PS2-only menu/layout differences
remain. PSP-only UI/content has no automatic PS2 destination. Full campaign
gameplay, line fit in every menu and physical PS2 operation remain unverified.

## Memory and native loading

The PS2 allocates FIX00 by file length inside a fixed 0x3e4000 resource heap.
Simply appending all English sentences caused a startup allocation failure.
The final resource retains sentence IDs and referenced dummy/source rows,
releases unreferenced source text, deduplicates rows, and resolves 2,054 long
English rows through the native sentence getter. The external pool contains
320,050 bytes; FIX00 is 516,744 bytes, below its original 517,712-byte size.
Normal offsets and the original negative sentinel behavior remain supported.
The native font/text segment ends at 0x7ccf00, before STATIC at 0x800000.

Battle captions retain the 0x4800 native read size. Four checked pointer hooks
resolve the high-bit long-line offsets. Every quote was matched to existing
PSP English. Native STAGE fields and terrain records retain numeric data.

The largest English story block is 0x32000 bytes, compared with 0x24800 in the
original. Script-sector tables follow the rebuilt blocks. Commands and string
counts are checked per block. The boot check does not establish worst-case
allocation or gameplay safety for every later scene; those need campaign QA.

## Verification and reproduction

The final disc's 37 files pass readback. Eight files change; the other 29 retain
their hashes and locations. Both ISO9660 and UDF resolve all replacements.
Font arithmetic/baseline/UV checks, 45 caption/spirit cases and 4,332 description
row reads pass. PCSX2 v2.8.2 loads the English database and complete appended
segment/hooks/tables correctly; its log reaches the opening FMV without
unknown CPU opcode warnings. Windows desktop activation denied access and
captures were black, so visual acceptance remains pending.

Reports: `work/output/ps2_font_0.1.3_verification.json`,
`ps2_font_0.1.3_mips_verification.json`, and `ps2_font_0.1.3_runtime.json`.
English mappings are under `work/translation/en/ps2/`.

Prepare battle, scenario and artwork inputs, then build from the original disc:

```powershell
python tools/ps2_battle_port.py
python tools/ps2_scenario_port.py
python tools/ps2_graphics_port.py
python tools/build_ps2_campaign.py 'Super Robot Taisen MX (Japan).iso'
```

The builder regenerates story and database inputs, applies the native hooks,
and verifies the resulting resources/disc. It refuses to overwrite an existing
version. It now defaults to 0.1.5 with the corrected New Game balance choice;
see `docs/ps2_difficulty.md`. Change the version for a new local build and
write its changelog.
The existing 0.1.3 was repaired during boot testing and retains an unused old
executable extent; a clean rebuild can have a different disc hash with the same
final resources. The 0.1.3 build has no gameplay rebalance. The 0.1.5 builder
includes optional PSP HP/reward balance; no release, upload or save conversion
is performed.

The final runtime resource heap retains 137,996 free bytes. FIX00, STAGE and
STATIC match their complete built resources in RAM. This does not substitute
for later-scene allocation checks or a full playthrough.
