# PS2 native 4x VWF — local 0.1.0

## Baseline correction in 0.1.2

Four actual 0.1.1 dialogue screenshots are saved as
`work/ui/ps2/dialogue_font_0.1.1_user_1.png` through `_4.png`, with a JSON
sidecar recording panel bounds, hashes and the user's report of uneven letter
alignment. Opening and stage-1 English text is visible; portraits and
backgrounds remain intact in these captures.

The original high-resolution rasterizer fit each glyph vertically into its
20px hinted bounding box. Those boxes end at different pixel rows even when
the 80px font has a shared baseline. Scaling them up introduced four high-res
pixels of baseline variation. 0.1.2 retains the 80px outline's vertical bounds
and uses baseline row 74 throughout, leaving two rows below the deepest
descender. Natural rounded-letter overshoot is retained; ordinary bottoms vary
by at most one high-res pixel. No letter is independently stretched vertically.

All 86 width-table entries and all renderer/heap patches are unchanged. The
complete MAP archive is byte-identical to 0.1.1, so English coverage and line
breaks are unchanged. No PSP font change or texture replacement is involved.
The builder keeps a legacy atlas option to reproduce 0.1.0 and 0.1.1.
`work/ui/ps2/font_baseline_0.1.2_comparison.png` is a labeled atlas specimen,
not a rendered gameplay screenshot. 85 baseline/guard checks pass alongside
the existing width, fallback, renderer, UV and upload checks. Corrected
0.1.2 in-game dialogue appearance remains pending.

The following sections record the original font-only 0.1.0 build.

The PS2 port starts with the font. This build adds Genei LateGo Medium Latin
glyphs at four times the original raster resolution and proportional spacing.
Original cells are 24×24; the new Latin cells are 96×96. Text keeps its original
on-screen height. The glyphs are part of the executable and use the game's own
GS upload path. Emulator texture replacement is disabled.

This is a font-only development build. PSP story, battle, UI and chapter-card
translations have not yet been inserted into the PS2 disc. The PSP 0.4.9 release
and the original PS2 ISO remain unchanged. No PS2 release is authorized.

## Reproduce

Use the original Japanese SLPS-25345 disc, SHA-256
`bcc9a6c5e20ffe4afc02aae482819de7b18c8bb1437a6d7a0feff096801934ce`.
The executable's original SHA-256 is
`1a7d24a5482979dda218d8be7d8721c9438ef21ed598f8ff8abdbd71e02f7141`.

```powershell
python tools/build_ps2_font.py 'Super Robot Taisen MX (Japan).iso' 0.1.0
```

Dependencies: Pillow, Keystone, Unicorn and PyCdlib. The font and license are
under `incoming/fonts/`. The build tool refuses to overwrite an existing ISO.
To verify an existing output without modifying its disc bytes:

```powershell
python tools/build_ps2_font.py 'Super Robot Taisen MX (Japan).iso' 0.1.0 --verify-existing
```

Outputs:

- `work/output/SRWMX_PS2_EN_0.1.0.iso` — local test disc.
- `work/output/SRWMX_PS2_EN_0.1.0_FONT_LICENSE.txt`.
- `work/output/ps2_font_0.1.0_verification.json` — disc readback and file hashes.
- `work/output/ps2_font_0.1.0_mips_verification.json` — execution checks.
- `work/output/ps2_font_0.1.0_runtime.json` — isolated PCSX2 boot/RAM evidence.
- `work/build/ps2/font_0.1.0/` — patched ELF, assembly, glyph metadata and atlas.
- `work/ui/ps2/font_atlas_0.1.0.png` — raster preview, not an in-game screenshot.

## Implementation

An additional ELF LOAD segment begins at `0x715000`, after the original BSS
boundary `0x7141fc`. It contains a Latin width/bearing table, glyph state,
86 glyphs and native hooks. The heap starts at `0x776b00`; the original BSS
clear boundary is retained. The segment ends below the original font/STATIC
region at `0x800000`.

The whitelist matches the PSP Latin font. All other Japanese glyphs retain
their original bitmap and spacing path. Digits use a common advance for numeric
tables. Latin ink is packed into the actual sampled UV interval, preventing
narrow letters such as `I` and `i` from losing their right edge. Raster
generation compares complete font masks before fitting them into
the cell, including the descenders in `g`, `j`, `p`, `q` and `y`.

| Native function | Address | Change |
|---|---|---|
| Full-width integer renderer | `0x130610` | Latin advance and 4x UV crop |
| Full-width float renderer | `0x1309b0` | Latin advance and 4x UV crop |
| ASCII integer renderer | `0x130d78` | Latin advance and 4x UV crop |
| ASCII float renderer | `0x131120` | Latin advance and 4x UV crop |
| Full-width integer measure | `0x1319c0` | Matching Latin advance |
| ASCII integer measure | `0x131a88` | Matching Latin advance |
| Full-width float measure | `0x131ba0` | Matching Latin advance |
| ASCII float measure | `0x131c60` | Matching Latin advance |
| Glyph pointer | `0x131d78` | New bitmap for whitelisted Latin |
| GS upload | `0x12f718` | 96×96 transfer for the new atlas |
| GS quad | `0x12f8b8` | 96px cell and 128×128 texture bounds for Latin |

There are 17 hook sites and two heap-address patches. MIPS64 assembler register
aliases are normalized to the game's EE/EABI register numbers. R5900 floating
comparison uses function `0x34`, encoded by Keystone as `c.olt.s`, rather than
generic MIPS `c.lt.s` (`0x3c`). A static COP1 check prevents that unsupported
encoding from passing the broader Unicorn instruction set. Reference:
[PCSX2 R5900 opcode table](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/R5900OpcodeTables.cpp).

## Disc layout and validation

The enlarged ELF is appended to the disc. Both ISO9660 and UDF entries point to
it, both UDF partition descriptors and the integrity size are updated, and a
valid final UDF anchor is added. Original asset sectors stay fixed: the game
addresses its archives directly. UDF descriptor checksums retain the mastered
disc's full-sector CRC coverage.

The build checks every one of the 37 files. Only the executable changes; the
other 36 files must retain both their hashes and disc sectors. It independently
reads the new executable through ISO9660 and UDF, checks the original source
hash again and records the final ISO hash.

Execution checks cover 1,368 width cases across four text paths and four sizes,
20 Japanese fallback cases, 344 renderer cases, all 86 atlas UV bounds, and all 86 glyph pointers and
96×96 upload arguments. PCSX2 testing uses a separate profile at
`work/build/ps2_font_test/PCSX2/` and a copied card at
`work/build/ps2_font_test/memcards/mx-test.ps2`. Its PINE port is 28012;
do not use the user's normal emulator connection or modify the original saves.

After booting the finished disc in that profile, repeat the read-only RAM check:

```powershell
python tools/verify_ps2_font_runtime.py 0.1.0 --port 28012 --profile work/build/ps2_font_test/PCSX2
```

Booting the finished ISO and checking the loaded segment and all 19 patched
locations are separate from visual acceptance. The user supplied an actual
unit-stats capture after navigating manually:
`work/ui/ps2/unit_stats_font_0.1.0_user.png`, with scope/observations in its JSON
sidecar. HP/EN, Lv, SP, PP, NEXT, LL, dynamic numbers and Japanese text are
legible. There is no visible clipping, overlap or damaged unit/pilot art on
this screen. A fresh RAM check still matches the font segment and all patches,
with no unknown CPU opcode warnings. This is a partial visual pass.

The capture contains no lowercase descenders, so `g`, `j`, `p`, `q`, `y`,
dialogue and other renderer contexts remain pending. Windows automated input
still returns `GetCursorPos failed: Access is denied (0x80070005)`; the capture
is user-supplied. Physical PS2 and extended gameplay testing are also pending.
Do not treat the atlas preview or MIPS tests as an in-game rendering pass.
