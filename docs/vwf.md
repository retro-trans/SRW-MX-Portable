# Variable-width font (VWF)

Implemented by `tools/vwf_patch.py` (code) and `tools/make_latin_font.py` (glyphs).
Build with `tools/build_patch.py`. First shipped in build 0.1.0.

## Native 4x font (0.1.4)

Since 0.1.5, the temporary raster canvas is 96x96: g/j/p/q/y/comma extend
below row 72 at the 60 px font size. The entire source glyph is cropped and
then packed into the existing 72x72 cell. A complete FreeType mask comparison
checks for source clipping; placement, VWF widths and renderer code are unchanged.
`tools/check_font_descenders.py` compares the actual 0.1.4/0.1.5 packaged atlases
and saves `work/ui/font_descenders_0.1.5.png`.

The user requested higher font resolution and explicitly rejected emulator
texture replacement. `tools/native_font4x.py` supplies a second, native Latin
atlas in the game's PRX module. It rasterizes the unmodified Genei LateGo TTF
at 60 px into 72x72 cells, seven per row, on a 512 px wide 4bpp bitmap.
The larger ink fits the original glyph placement multiplied by four. Latin
glyph lookup returns the appropriate row; uploads use 512x128 textures, and
the four renderers use fourfold texture coordinates/width/height while keeping
their original VWF on-screen advances. Japanese uses the original atlas path.

The 384-byte VWF table, index map, 253,952-byte bitmap and renderer code are
appended after the original PRX memory allocation. The load segment grows by
256,216 bytes; the original BSS remains zero. New address instructions have
PRX relocations. This mode does not use the old dead-library code cave.

Build and check explicitly (the ISO contains only the listed prologue scenes):

```powershell
py -3 -X utf8 tools/build_patch.py 'Super Robot Taisen MX Portable (Japan).iso' 0.1.4 --scenes-file work/translation/en/script/prologue_merged.json --native-font4x
py -3 -X utf8 tools/verify_font_build.py 0.1.4 --native-font4x
```

An isolated PPSSPP instance booted and displayed translated prologue dialogue,
with `ReplaceTextures=False`. `verify_native_font_live.py` matched every new
atlas/table/code byte and all 16 patched instructions after relocation, ignoring
PPSSPP's JIT substitutions. A renderer breakpoint confirmed Latin upload
width=512 / height=128, sampled glyph height=72, and W advance=14 at size16.
Evidence: `work/output/font_0.1.4_verification.json` and
`work/ui/font_native4x_0.1.4_dialogue.png` (software renderer, 480x272 framebuffer).
Physical PSP testing and a 4x hardware-rendered screenshot are not verified.
Higher emulator internal resolution can display the extra glyph detail; no
texture replacement is needed. The source font licence notice is
`work/output/SRWMX_EN_0.1.4_FONT_LICENSE.txt`.

The sections below describe the original-size atlas and 0.1.0–0.1.3 VWF patch.

## How the game draws text

- **Font atlas**: `STATIC2_ADD.BIN` + 0x40000. 4 bits per pixel, 256 px wide, 18×18 cells, 14 per row,
  about 4,480 glyphs. Pixel values: 0 = empty, 5 = drop shadow, 6–0xE = anti-aliased body.
- **Glyph slot**: for lead bytes 0x81–0x98, `slot = (sjis − 0x8140) − ((sjis − 0x8140) >> 8) × 64`
  (function 0xB07E8). Kanji above 0x989F go through a second lookup (0xB090C).
- **Text context** (first argument of every text function): floats at +0 / +4 (cell size),
  +8 / +0xC (font width / height), +0x24 atlas pointer, +0x2C "proportional" flag.
- **Renderers**: 0xAEB08 (main `drawString`, used by dialogue), 0xAEFF4, 0xAF548, 0xAFA24.
- **Width functions**: 0xB03E4, 0xB04D8, 0xB061C, 0xB06E0.
- The original game only knows three width classes (kanji, digits/Latin, kana), and only when the
  proportional flag is set. The dialogue box does not set it: every glyph advances 16 px.

## The patch

Each of the 8 sites computes a glyph's advance. At each one, the instruction that tests the proportional
flag is replaced by a jump to a stub. The stub looks the glyph up in a 384-byte width table (slots of lead
bytes 0x81 and 0x82: punctuation, digits, A–Z, a–z). An entry is `W | L << 5`:

- `W` = columns of the cell to show (ink width + 1 px), `L` = left bearing.
- If `W ≠ 0`: texture u += L, texture width = W, on-screen width and advance = `W × size / 18`.
  The glyph is cropped, not squashed.
- If `W = 0` the original code runs unchanged, so Japanese text is unaffected.
- Digits 0–9 are tabular: every digit has `W = 10, L = 1` (0.2.2; 12 with a 1.2× stretch in 0.2.1).
- **Narrow fonts (0.2.2):** many screens draw values with a font much narrower than it is tall. The
  Japanese game uses this to make full-width digits look half-width; status values are 10x15 and
  weapon-list values 10x16 (font width x height, from the text context at ctx+8 / ctx+0xC).
  - **The rule:** when width/height < 0.7, the stubs scale Latin glyphs by the height instead of the
    width, so a digit advances 10*16/18 = 9 px with normal proportions instead of 10*10/18 = 6 px
    squeezed. Squarer fonts keep the width. Since 0.3.2, fonts wider than tall (the battle message
    box) are scaled by the height as well.
  - **Where it applies:** all 8 sites. Each site's `hctx` names the register holding the context. W1
    and W3 overwrite `$a0` before their loop, so a PRE stub at 0xB0400 / 0xB063C saves the height
    in `$f8` first. `$f8`–`$f11` are free in all eight functions.
  - **Finding the contexts:** `ctxlog.py`-style logging: execution breakpoints on the renderer entries
    0xAEB08 / 0xAEFF4 / 0xAF548 / 0xAFA24 (+0x08804000) while switching a tab to force a redraw.
    They work under the JIT; static screens only draw when they change.

`$ra` is parked in `LO` around the shared lookup routine because two of the width functions are leaf
functions.

### Where the code lives

`BOOT.BIN` is a relocatable module. The stubs and table sit in dead library code at 0x250944 (0x848 bytes):
no relocation entry in any section targets it, no branch reaches it and no call word in the file points
into it. The 28 relocation entries that belonged to that dead code are replaced by the 26 the patch needs
(8 hook jumps, 16 stub exits, 1 HI16/LO16 pair for the table), and `.rel.text` shrinks by two entries.

**Do not use 0xE4EAC.** It looks unreferenced from `.text`, but a `jal` to it sits in `.data` (static
initialiser code) and runs once at boot.

`EBOOT.BIN` in the built ISO is the patched `BOOT.BIN` (plain ELF).

## Latin glyphs

`make_latin_font.py` redraws A–Z, a–z, 0–9 and the punctuation `, . : ; ? ! / ~ ' " ( ) [ ] + - = $ % # & *`
left-aligned in their full-width cells, with anti-aliased bodies. Latin shadows
are disabled; original Japanese glyphs retain their original rendering.
English uses codes that Japanese text rarely needs (， ． － ’ “ ”), so remaining Japanese keeps 、 。 ー.
The full-width space is 5 px wide for the dialogue font size.

**Font**: since 0.1.3, Genei LateGo v2 Medium from the official v2.1 separate-TTF
package (https://okoneya.jp/font/genei-latin.html), rendered at 15 px without shadows.
Source: incoming/fonts/GenEiLatin_v2.1/GenEiLatin-Separate_v2.1/GenEiLateGoN_v2.ttf.
The normal N edition already has proportional Latin letters/digits; the P edition
also changes Japanese kana spacing, which is outside this Latin replacement.
The game still requires the VWF patch: installing a proportional TTF alone does
not change the original game's fixed dialogue advance.

Current dialogue advances include i=3px, M=12px, W=14px. Japanese atlas cells
are unchanged. Source font, SIL OFL 1.1 licence and acknowledgments are retained;
the derived bitmap is called the SRW MX Latin atlas. Accompany redistribution
with the copyright/licence notice in work/output/SRWMX_EN_0.1.3_FONT_LICENSE.txt.
Previous fonts were HarmonyOS Sans Condensed Bold (0.1.1/0.1.2) and Arial Narrow
Bold (0.1.0); historical font files/builds remain available.

Verification: tools/verify_font_build.py 0.1.3 checks unchanged non-Latin atlas
bits, unclipped glyphs, packaged ISO atlas, matching BOOT/EBOOT, VWF table and
eight hooks, and fits all 562 prologue/21,024 campaign rows. Results are in
work/output/font_0.1.3_verification.json. Emulator validation is still pending.

## Text limits

`tools/textfit.py` encodes English and measures it with the same width table.
Dialogue box: 3 lines × 352 px (measured in-game, see `work/ui/dialogue_box.json`).

## Script rebuild

`build_patch.py` rebuilds the `SRWL` blocks of the translated scenes (pointer tables are rewritten, so
there is no byte budget per line), repacks the script area of `MAP_ADD.BIN`, and updates the block table
(BOOT 0x27CA20) and the `MAP_ADD` section table (BOOT 0x2791F0). Only blocks of the scenes being
translated are touched. A script is loaded into a memory pool whose capacity is not confirmed yet, so no
block may exceed the largest original block (0x25000 bytes).

## Testing

`tools/ppsspp_dbg.py` drives PPSSPP through its remote debugger (memory read/write, breakpoints, button
input, window capture). `tools/boottest.py` launches an ISO and reports whether the game threads started.
