# PS2 battle forecast labels — local 0.4.14

The user reported an overlapping Artificial Intelligence pilot name, incorrect
status icons and damaged AT/CT badges in a PS2 battle forecast screenshot.

## Changes

The PS2 name table's Strg entry 1133 now displays **AI**, the existing approved
glossary abbreviation. Its original slot is rewritten in place and padded
after the terminator. All string offsets, table IDs, pilot records and other
names stay exact. This applies wherever the game resolves that name, including
the forecast; it does not replace words inside translated dialogue.

The PSP-to-PS2 WND mapping shifted several status icons and omitted others:

| PS2 asset | Native meaning | Correct label | Previously drawn |
|---|---|---|---|
| IM_IC07 | Pilot stats down | ST | ST, oversized |
| IM_IC08 | Weapon hit down | WP | MB |
| IM_IC09 | Mobility down | MB | AR |
| IM_IC10 | Armor down | AR | DS |
| IM_IC11 | Cannot act | DS | Untranslated |
| IM_IC12 | HP | Original HP | MV |
| IM_IC13 | Movement down | MV | Untranslated |

The native status tiles occupy 21×21 pixels in padded 32×32 textures. The old
renderer doubled PSP bounds, drawing into padding and erasing the frame. Six
labels now use the native inner rectangle (2,3)..(19,19), with naturally
proportioned letters. The original HP tile is restored exactly. Frames,
padding, palettes, headers, draw coordinates and status activation logic are
preserved. `tools/ps2_graphics_port.py` also applies the correction on full
rebuilds; `tools/ps2_database_port.py` preserves the AI abbreviation on rebuilds.

AT/CT assets IM_IC00S and IM_IC01S already have the verified 24×24 frame fix
in the current 0.4.13 prepared resources and disc hashes. The reported artwork
resembles their pre-0.1.17 payloads. The user was asked which build produced
the screenshot. This candidate preserves the corrected badge pixels exactly,
including complete frames and transparent padding. It does not claim a new
badge-code change or a visually completed forecast walkthrough.

## Validation

`tools/verify_ps2_battle_labels.py` verifies every byte outside the one name
slot and seven status texture payloads against 0.4.13. All executable bytes
and other resources match exactly. Every database section except Strg remains
identical; Strg offsets and all names except 1133 match exactly. Native
forecast execution checks AI, Giganos Sldr. and Hugo at both name draw sites.
AI fits comfortably before the level column.

Pixel checks independently verify status mappings, 21-pixel visible crops,
original frames/padding, HP equality and the exact corrected AT/CT payloads.
Before/after native asset previews were reviewed at
`work/ui/ps2/battle_labels_0.4.14/status_before_after.png`.
The complete graphics-port rebuild matches the incremental WND archive
byte for byte.

All nine suites pass: battle labels, narration, stage-30/campaign, favorites,
prologue, UI, UI details, roster/system and setup/save. Older resource fixtures
reverse only the declared new label edits, verify the exact source hash, then
run their existing preservation assertions. The new label verifier checks the
actual edited bytes and native drawing. This keeps the older fixtures strict
without treating an authorized label edit as gameplay damage.

Evidence:

- `work/output/ps2_battle_labels_0.4.14_verification.json`
- `work/output/ps2_font_0.4.14_verification.json`
- `work/output/ps2_battle_labels_0.4.14_build.log`
- `work/ui/ps2/battle_labels_0.4.14/reported.png`
- `work/ui/ps2/battle_labels_0.4.14/layout.json`
- `work/translation/en/ps2/battle_labels_0.4.14.en.json`

## Local build

```powershell
py -3.8-32 -X utf8 tools/fix_ps2_battle_labels.py --dry-run
py -3.8-32 -X utf8 tools/fix_ps2_battle_labels.py --build
```

The builder preserves existing outputs. `--verify-existing` reruns checks on
the prepared candidate; combine it with `--build` only if the ISO does not
already exist. Output is `work/output/SRWMX_PS2_EN_0.4.14.iso`. Start it from a
fresh boot; old emulator states may retain earlier labels and cached textures.
No public release or Git push is performed. In-game visual forecast and
physical-console testing remain pending.

Final ISO9660 and UDF checks pass for all 37 files. Only FIX00.DAT and WND.BIN
change from 0.4.13; all other files match their prior hashes. Output size:
4,663,275,520 bytes. SHA-256:
`373c8b2cdf62d2c74cb8cbdb7935049204770dd4b801a86c422697e1a98a6228`.
