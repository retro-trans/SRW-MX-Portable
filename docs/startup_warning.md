# Native startup warning — local 0.4.20

The user requested translation of the first PS2 screenshot on 2026-10-10,
with the equivalent PSP screen translated too. This supersedes the earlier
decision to leave the warning Japanese. Option and save/load changes belong
to separate work; this build changes only warning pixels.

Both editions retain all five paragraphs: viewing distance, flashing effects,
rare muscle spasms/loss of consciousness and other symptoms, consulting a
doctor after previous symptoms, and reading the manual before play.
The PS2 original also says to keep the room well lit and refers to a TV.
The PSP original omits room lighting and refers to the LCD screen.
The English preserves these differences.

## Asset locations

| Platform | Archive | Palette offset | Pixels | Stored / displayed dimensions |
|---|---|---|---|---|
| PS2 | IM.BIN | 0x27e8000 | 0x27e8400 | 640 x 448 |
| PSP | IM_ADD.BIN | 0x14ea000 | 0x14ea400 | 512 x 272 / 480 x 272 |

PS2 opening state code at 0x2c1f64 requests background 202 through
0x1b3068. Its STATIC.BIN table at 0x1a6a90 contains relative offset
0x252d800; IM.BIN subarchive 2 begins at 0x2ba800, giving 0x27e8000.
The decoded image matches the supplied screenshot. Both images are linear
8-bit palette indexes. PS2 uses the original CSM1 palette address swap;
PSP uses direct palette order. The next PSP image is copyright artwork and
is preserved.

The renderer uses Genei LateGo v2 Medium, matching the project's font,
with supersampling and explicit centered line breaks. PS2 is 18px and PSP
12px. Letters are not stretched horizontally. The existing palettes,
dimensions, image loading code, resource tables, timing and unrelated bytes
are preserved. Font license sidecars accompany the local ISO builds.

## Build and checks

Run `py -3.8-32 -X utf8 tools/fix_startup_warning.py --preview` for asset
previews, or omit `--preview` to build both platforms. Existing versioned
ISOs are never overwritten. PS2 uses local 0.4.19; PSP uses local 0.4.18.

Outputs:

- `work/output/SRWMX_PS2_EN_0.4.20.iso`
- `work/output/SRWMX_EN_0.4.20.iso`
- `work/output/ps2_startup_warning_0.4.20_verification.json`
- `work/output/psp_startup_warning_0.4.20_verification.json`
- `work/ui/ps2/startup_warning_0.4.20/english.png`
- `work/ui/psp/startup_warning_0.4.20/english.png`

Checks compare every ISO file and every disc byte outside the declared
warning-pixel span. PS2 also reads the changed archive through UDF.
Readback reproduces the inspected previews exactly. Both palettes and all
other image/archive bytes are retained. No executable changes are required.

Verified ISO SHA-256:

- PS2: `d07092b924824051882d0d7a6f40d146ee27372f16b0bf093b9cfe0cecd452fc`
- PSP: `ddcc194c36660ea6d443a04fab906888036a4edd906781fca78951b034a941b0`

In-game visual confirmation and physical-console testing remain pending.
Earlier emulator checks retain their historical build attribution.
These incremental builds do not include the subsequent campaign proofreading.
No GitHub release or commit was requested or created.
