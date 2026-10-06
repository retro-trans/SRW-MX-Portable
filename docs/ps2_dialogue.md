# PS2 opening and stage 1 — local 0.1.2

0.1.2 corrects the uneven font baseline seen in the user's four 0.1.1 dialogue
captures. It keeps the same opening/stage-1 translations, complete MAP bytes,
glyph advances and renderer hooks. Only Latin atlas pixels differ. See
docs/ps2_vwf.md for the baseline correction. The four captures confirm English
dialogue loads and renders in 0.1.1; corrected 0.1.2 appearance is pending.

PS2 0.1.0 was a font-only build. Its original dialogue was still Japanese.
Local 0.1.1 is the first PS2 dialogue insertion build: the opening (`i001b`)
and both stage-1 routes (`s00r10`, `i00r1a`, `s00s10`, `i00s1a`).
There are 1,321 translated string-table entries across five scenes. Four
technical scene labels remain unchanged. Later scenes, battle captions,
database names, menus and title-card artwork are not translated in this build.
Native Genei LateGo 4x VWF is retained; texture replacement is disabled.

To see the opening English text, start **New Game** in 0.1.2. An old save in a
later scene will continue showing that scene's Japanese text. The first
opening line begins: `Mitar「...I've seen your report. It seems things are...`.
It includes descenders needed for the font check. Dynamic player/unit name
placeholders remain native and use the names stored in the game/save.

## Sources and PS2 differences

The reviewed PSP sources are `prologue_merged.json` and
`stage01_campaign_full_merged.json`, matched by exact original text within
the corresponding PS2 scene. The stage-1 Real route has one line whose exact
source and English occur in the PSP Super route; that reuse was reviewed.

Seven reviewed variants cover 11 differing/missing PS2 slots. Their English,
source hashes, uses and reasons are in
`work/translation/en/ps2/script/stage1_ps2_differences.en.json`. PS2 lines that
name both Medius and AI1 retain both names. Aqua's role wording, Hugo's thought
and an enemy taunt were adapted to the PS2 source rather than copied from
changed PSP wording. The original Japanese script stays in the owned ISO and
ignored working data; it is not added to a tracked translation file.

The build writes an English-only use mapping to
`work/translation/en/ps2/script/opening_stage1_0.1.1.en.json`.

## Reproduce and verify

```powershell
python tools/build_ps2_dialogue.py 'Super Robot Taisen MX (Japan).iso' 0.1.2
```

The supported source is the same original SLPS-25345 ISO as the font build.
Existing output ISOs are preserved. To read back an existing build:

```powershell
python tools/build_ps2_dialogue.py 'Super Robot Taisen MX (Japan).iso' 0.1.2 --verify-existing
```

The builder repacks the original 192 PS2 SRWL blocks, changes only the five
selected text tables and preserves every command and untouched string. It
updates the 193-entry relative script-sector table at ELF file offset
`0x381f40` and archive sections 11–17 in the table at `0x37e438`. Script section
10 starts at MAP offset `0x622a000`. The MAP prefix is unchanged, and its suffix
is moved intact by the script area's growth.

The enlarged MAP and ELF are appended to the original disc; their ISO9660 and
UDF entries are updated. Every unrelated file keeps its original bytes and
sector. UDF is case-sensitive: the original MAP path is `/data/map.bin`, while
ISO9660 uses `/DATA/MAP.BIN;1`.

The native script loader measures block size from adjacent sector-table entries
at `0x339550` and loads the named `\DATA\MAP.BIN;1` resource at `0x339668`.
Its archive offsets are relative to that named file. The translated blocks
remain smaller than the largest original PS2 block; their actual loading and
text appearance still need runtime validation.

Finished-disc verification passed for all 37 files and 192 script blocks in
0.1.2. It boots in a separate PCSX2 profile without interrupting the user's
0.1.1 session. The corrected font segment, all 19 patches and both updated
script/archive tables match RAM; there are no unknown CPU opcode warnings.
85 baseline checks and all existing font execution cases pass. User captures
already confirm English dialogue in 0.1.1. Corrected 0.1.2 visual acceptance,
physical PS2 and extended gameplay tests remain pending.

Outputs: `work/output/SRWMX_PS2_EN_0.1.2.iso`, font license, disc verification
and MIPS reports named `ps2_font_0.1.2_*.json`. Retain the separate original
font-only 0.1.0 build and its unit-stats screenshot. Neither build authorizes
a GitHub push or release. No save conversion or PSP-only content was added.
