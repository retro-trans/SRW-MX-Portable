# STATIC2_ADD.BIN — game database format

Tagged sections start at 0x17EF00. Every section: `tag[4]`, `u32 size` (incl. 12-byte header),
`u32 count`, then data. The next section starts at `(offset + size + 3) & ~3`.
`Fixh` lists section offsets relative to `Vers` (0x17EF00).

| Offset | Tag | Count | Content |
|---|---|---|---|
| 0x17EF00 | `Vers` | — | version |
| 0x17EF10 | `Fixh` | — | section directory |
| 0x17EF64 | `Unit` | 512 × 124 B | units. u16 name (Strg) @0, u16 reading (Strg) @2, u8 series @10, u16 weapon ids @32 (16 slots, 0xFFFF end), u16 library entry @84 |
| 0x18E770 | `Weap` | 1024 × 48 B | weapons. u16 name (Strg) @0 |
| 0x19A77C | `Pilt` | 512 × 184 B | pilots. u16 full name @0, u16 short name @2, u8 series @4, u16 reading @16, u16 library entry @166 |
| 0x1B1788 | `DTS ` / 0x1B25D8 `DT  ` | | unknown |
| 0x1B2C4C | `Sprt` | 32 × 16 B | spirit commands, SJIS name inline |
| 0x1B2E58 | `Skil` | 50 | pilot skills |
| 0x1B3184 | `Abil` | 54 | unit abilities |
| 0x1B3268 | `Part` | 38 | parts |
| 0x1B330C | `Bgm ` | 86 | BGM list |
| 0x1B3878 | `Strg` | 1839 | **name strings**: u32 offsets (relative to section start) + SJIS strings |
| 0x1BBE18 | `Xunt` | 294 | **robot library index**: u32 offsets → `u16 n, u16 Sent_row[n]` |
| 0x1BD3E0 | `XPlt` | 431 | **character library index**, same layout |
| 0x1BF070 | `XSpr` / `XSkl` / `Xabl` / `XPrt` / `XHlp` | 32/50/54/38/509 | description indexes (spirits, skills, abilities, parts, help) |
| 0x1C08C4 | `Sent` | 5288 | **sentence rows**: u32 offsets + SJIS strings, one string = one display row |
| 0x20EB64 | `Ddfd` | | unknown |

- Library link: `Unit` u16 @84 = `Xunt` entry, `Pilt` u16 @166 = `XPlt` entry (0xFFFF = none).
  Several records (enemy copies, forms) can share one entry. Entry index ≠ record index after ~133.
- Entries whose rows are only `☆ダミー…` are unused (46 robot, 167 character entries).
- Series ids index the 22 titles at BOOT.BIN 0x28FDB8.
- Rows are reached only through the index tables, so translations can be re-wrapped to any
  number of rows by rebuilding `Sent` + the `X…` indexes (no byte budget). The section offsets
  in `Fixh` must be updated if `Sent` changes size.

Extract with `tools/static2_extract.py`.
