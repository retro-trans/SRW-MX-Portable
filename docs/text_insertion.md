# Inserting the non-dialogue text (builds 0.2.0–0.2.2)

`tools/insert_text.py`, called by `tools/build_patch.py ... --text`. Sources are the English files
listed in `docs/text_inventory.md`; checks are `tools/check_*.py` and `tools/verify_text_build.py`.

```bash
python tools/build_patch.py "Super Robot Taisen MX Portable (Japan).iso" 0.2.2 --scenes-file work/translation/en/script/prologue_merged.json --native-font4x --text
```

```bash
python tools/verify_text_build.py 0.2.2
```

## Engine facts this relies on

- **English must be full-width.** The main renderer computes the character count as
  `strlen / 2` (0xAEB60: `jal strlen; srl $fp, $v0, 1`), so single-byte ASCII cannot be mixed in.
  Every English letter takes 2 bytes. Format codes (`%d`, `%s` …) stay ASCII because `sprintf`
  reads them. Text shown by the PSP system (the save list, the "Memory Stick not found"
  dialog) is plain ASCII.
- **BOOT.BIN strings are movable.** Every UI string is reached through a relocation: a 32-bit data
  pointer (`.rel.data`) or a `lui`/`addiu` pair (`.rel.text` HI16 followed by its LO16s). All 813
  `lui` groups that touch translated strings serve only translated strings, so each group gets a new
  upper half. The translated strings go to a block appended to the PRX load segment, after
  `native_font4x.py`'s atlas.
- **STATIC2_ADD.BIN cannot grow.**
  - **Fixed read size:** the game reads exactly `0x3692C0` bytes into the start of a fixed 16 MB
    area. The size is a constant, not the file size.
  - **Hard-coded region boundaries:** the regions after it are set by 176 identical static
    initializers (one per source file; 0x29A808–0x2B79D4). Each writes 14 boundaries:
    `0x3692C0, 0x369300, 0x40E680, … 0xEE9B00`.
  - **The heap sits in the gap:** the malloc heap is `0xEE9B00–0xF00000`, and code adds fixed area
    offsets directly in many places (`0x7E6640`, `0x966640`, `0xF00000`, `0xF80000` …).
  - **Tested:** shifting the boundaries starves the heap and the game stops with "Malloc Memory
    Over".
- **Database sections are reached through tiny getters.** The database object builds one
  section object per tag (`Vers Fixh Unit … Strg … Sent`) at 0x5CEB0. String sections are read by
  getters of this exact shape:
  `lw a0,(a0); sll v0,a1,2; addiu v1,a0,0xc; addu; lw v0,(v0); bgezl v0,…; addu v0,a0,v0; move v0,zero; jr ra`.
  A negative table entry used to mean "no string".

## Overflow table

The English library, help and summaries need about 364 KB more than STATIC2 holds. Strings that
don't fit in their old section go to an overflow table in the PRX:

| Text | Getter | Patch |
|---|---|---|
| Names (`Strg`, object +0xEC) | 0x5BF24 | negative entry → `j stub1`, which returns `overflow[n]` |
| Rows (`Sent`, object +0x18C) | 0x5BDDC | same |
| Stage summaries | tail of 0x1A4160 (0x1A41D4) | `j stub2`: negative offset → `overflow[n]`, else `base + offset` |
| Spirit names (`Sprt`, 12-byte inline field) | 0x5BEC8 (`j 0x5BF10`) | `j stub3`: field starting `FF FF` → `overflow[u16 at +2]`, else the record |

- **Entry encoding:** overflow entries are `0x80000000 + n` in the offset tables, or the marker
  `FF FF` + u16 n in a spirit-name field.
- **Relocations:** the stubs and the pointer table carry their own relocations: HI16/LO16 for the
  table address, R_MIPS_26 for the new jumps, and R_MIPS_32 for each table entry. The spirit getter
  keeps its existing R_MIPS_26.
- **Memory cost:** the PRX grows by about 380 KB, on top of 0.1.5's 256 KB font atlas.
  Free memory at start-up stays above the 16 MB the game reserves (`FreeSzie: 0x111C500`, needed
  `0x1000000`).
- **Expect the same for dialogue:** any other text that outgrows STATIC2 or MAP_ADD can use the
  same mechanism. The script pool for dialogue likely has the same kind of fixed limit.

## Checked in PPSSPP (isolated instance, `work/build/text_test/`)

This instance uses the software renderer at 1x (480×272) so screenshots can be read straight from
PSP VRAM. Its screenshots therefore never show the 4x font. To look at the 4x font, use
`work/build/hw4x/ppsspp.ini` (same settings, hardware renderer, internal resolution 4).

| Screen | Result |
|---|---|
| Title, OPTION menu, Demo Select | English |
| Robot Library, Character Library | English names, height/weight, voice actor, scrolling English text (overflow rows) |
| PSP save dialog | " SRW MX System Data" (plain ASCII title) |
| Hero / partner setup, rename screen, Latin keyboard page | English; labels shortened where values sit at fixed positions |
| Hero unit setup | English description (rows re-split to the box) |
| Objectives window | English; stage number fragments blanked (they sit in one-kanji slots) |
| Map: command menu, Spirit list, spirit help | English; spirit names via the overflow hook |
| Unit status, weapon list, weapon details | English; labels abbreviated where they ran into values |

Not checked yet:
- **Intermission screens:** upgrades, parts, pilot training, sortie preparation, saving.
- **Battle screens:** the response menu and battle-setup window; the battle banners are still
  Japanese images.
- **Stage title cards and summaries:** these appear between stages.
- **The opening narration:** it plays over a movie in a way the framebuffer capture doesn't show.

Screenshots: `work/ui/text_0.2.0_*.png`.

## Layout lessons (fixed in `boot_ui.json`, list in its `in_game_fixes`)

Many labels are drawn with the value at a fixed x position sized for 1–2 kanji (32 px). On such
screens the English must stay within the Japanese width:
- **Pilot stats on the status screen:** Mel / Rng / Acc / Eva / Skl / Def.
- **Library labels:** Ht. / Wt. / Nick.
- **Terrain letters:** Ai / Ld / Sp / Se / Ug.
- **Weapon attribute headers:** single letters A T S F H B.

Long lists (menus, the option help) have room. The pilot status spirit and skill lists do not: spirit
names have 63 px before the cost column (moved right in 0.2.2, `CODE_PATCHES`), and skill names plus
the level digit have 121 px.
