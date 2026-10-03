# Battle quotes (`BATTLE2.BIN`)

Tool: `tools/battle_quotes.py` (export, fit, check, merge, status). Translator brief:
`work/translation/en/battle/BRIEF.md`.

## Where they are
- **Sub-file 5:** `BATTLE2.BIN` (526 MB) starts with a u32 table of sub-file offsets (11 entries,
  ended by `0xFFFFFFFF`). Sub-file 5 (`0x75800`–`0x31C000`, 2.6 MB) holds every battle quote. The
  sub-files after it are battle animation data.
- **Pilot table:** `STATIC2_ADD.BIN` `0x17E1C0`, just before the `Vers` section, has `u32[512]`, one
  per pilot id. The ids are the same as `work/source/pilots.json`. Each entry is the offset of that
  pilot's quote block inside sub-file 5, or `0xFFFFFFFF` if the pilot has none. 372 pilots have a
  block, each its own.
- **Unnamed slots:** pilots 450–509 are named 無し ("none") in the pilot list. They hold the
  original characters' voice sets: Hugo, Aqua, their partner lines, and per-unit and story
  variants. Several speakers share one block.

## Block layout
- **Alignment:** each block starts on a 0x800 boundary and is padded with zeros to the next.
- **Header:** `+0x00` 8 bytes (zero except in block 0), then `+0x08` `u16[10]` section offsets
  relative to the block (`0xFFFF` = absent). The last offset is where the strings start.
- **Records:** `+0x1C` onwards holds the situation records. They have a variable shape that is not
  decoded yet. Many are 24 bytes (`count, 0, first string, condition, parameter, 0`), but some
  blocks mix in other sizes.
- **Section 6:** one u32 of flags per string.
- **Section 7:** u16 offset of each string, relative to the string area. This limits a block's
  strings to 64 KB.
- **Section 8:** u32 text id of each string. A line repeated inside a block keeps the same id.
- **Strings:** Shift-JIS, NUL-terminated. A quote is `「...」`; `/` (ASCII) is the line break, at
  most 2 lines.

## Counts and size limits
- **Counts:** 51,587 strings and 10,227 unique (the unique key is the exact string).
  - 30 strings are the second half of a line (no opening `「`).
  - A few end in full-width space padding.
- **Box:** the longest Japanese line is 22 cells, the same 352 px as the dialogue box at 16 px per
  cell. `battle_quotes.py fit` wraps English into at most 2 lines of 352 px, with `「` on line 1, a
  full-width space indent on line 2 and `」` at the end. This has not been measured on a battle
  screen yet.

## How the game loads a block
- **The loader (0x495F4):** reads a fixed `0x4800` bytes:
  - sector = BATTLE2 start + (BATTLE2 header[5] >> 11) + (pilot table entry >> 11);
  - destination: one of 16 buffers of 0x4800 at UseArea + 0x7E6640 (set up at 0x4AAD4), so the
    buffers cannot grow.
- **The parser (0x49630):** stores section pointers in the slot object. Section 7 (string offsets)
  goes to +0x38 and section 9 (string base) to +0x40.
- **String pointers:** built in three places, 0x49C08, 0x4A22C and 0x4A578, each
  `addu v1, base, offset` followed by `sw v1, 0x34(v0)`.
- **Shared entries:** some offset-table entries point to the same string (for example offset 0), and
  the last entry can be padding.

## Insertion (`build_patch.py ... --battle`, since 0.3.0)
- **Rebuilt blocks:** every block keeps its records, flags and text ids. Its strings are replaced by
  the English (wrapped by `fit`, lines joined by ASCII `/`, identical lines stored once) and section
  7 is rewritten.
- **Overflow:** lines that would push a block past 0x4800, longest first, go to an overflow table in
  the PRX (45 lines, 5.5 KB in 0.3.0). Their offset entry is `0x8000 | index`. The three pointer
  sites `jal` a stub that reads the table for such entries.
- **Placement:** the new sub-file 5 (0x339000 bytes, 0x4800 of padding at the end) is appended to
  BATTLE2.BIN, and header[5] points to it. The STATIC2 pilot table gets the new block offsets.
- **Check:** `python tools/battle_quotes.py verify <iso>` reads every entry back the way the game
  does. In 0.3.0: 51,892 entries, 0 mismatches.
- **Untested:** the box width (352 px, 2 lines) is not measured on a battle screen yet, and the
  build has not been played in battle.
