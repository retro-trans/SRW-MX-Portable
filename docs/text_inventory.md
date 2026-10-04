# Non-dialogue text inventory

All Japanese text in the ISO **except the scenario script** (`MAP_ADD.BIN` SRWL blocks, handled by
the dialogue work). Produced by `tools/text_inventory.py`; the per-string exports (with offsets, byte
lengths and owners) are in `work/source/text_inventory/` and stay local, because they contain Japanese.
Textures were checked by eye on contact sheets in `work/ui/textures/`.

Date: 2026-10-03. Counts are exact (parsed tables or relocation targets) unless marked.

## Summary

"Chars" = Japanese characters in the unique strings. Status: **done** = English exists (not yet
inserted), **partial** = glossary covers most of it, **todo** = nothing translated yet, **skip** = not
shown to the player.

| # | Text | File / location | Count / unique | Chars | Status | Storage (what limits the English) |
|---|---|---|---|---|---|---|
| 1 | Menus, labels, messages, option help, upgrade/skill screens | BOOT.BIN `.data` | 1,162 / 831 | 5,721 | **done** `ui/boot_ui.json` | pointer (relocations) |
| 2 | Opening narration + ending epilogue | BOOT.BIN 0x285E4C | 56 lines | 1,102 | **done** `ui/boot_text.json` | line tables: 25 + 31 line pointers |
| 3 | Intermission location list | BOOT.BIN 0x28C620 | 34 | 214 | **done** `ui/boot_text.json` | pointer |
| 4 | Save / Memory Stick messages, save-data titles | BOOT.BIN 0x282BB8, 0x299260 | 27 | 487 | **done** `ui/boot_text.json` | pointer; save-list strings are plain ASCII |
| 5 | Unit names | STATIC2 `Strg` | 262 | 1,910 | **done** `static2/names.json` | pointer table |
| 6 | Weapon names | STATIC2 `Strg` | 456 | 3,671 | **done** `static2/names.json` | pointer table |
| 7 | Pilot full / short names | STATIC2 `Strg` | 271 / 270 | 2,519 | **done** `static2/names.json` | pointer table |
| 8 | Skills / unit abilities / parts | STATIC2 `Strg` | 50 / 54 / 38 | 856 | **done** `static2/names.json` | pointer table |
| 9 | BGM titles (sound test, BGM settings) | STATIC2 `Strg` | 85 | 1,017 | out of scope (kept) | pointer table |
| 10 | Voice actor names (library) | STATIC2 `Strg` | 99 | 499 | **done** `static2/voice_actors.json` | pointer table |
| 11 | Unit height / weight (`５７．９ｍ`) | STATIC2 `Strg` | 150 | 772 | **done** `static2/names.json` | pointer table |
| 12 | Spirit command names | STATIC2 `Sprt` | 32 | 70 | **done** `static2/spirits.json`; 15 too long for the field | **inline 12-byte field** |
| 13 | Descriptions: spirits, skills, abilities, parts | STATIC2 `Sent` via XSpr/XSkl/Xabl/XPrt | 287 rows / 211 | 3,935 | **done** `static2/descriptions.json` | rows; index rebuild (no byte budget) |
| 14 | Help text (509 help entries) | STATIC2 `Sent` via XHlp | 745 rows / 632 | 13,436 | **done** `static2/descriptions.json` (+ `help.json`) | rows; index rebuild |
| 15 | Robot + character library | STATIC2 `Sent` via Xunt/XPlt | 4,256 rows | ~82k | **done** `library.json` | rows; needs re-wrap + insertion |
| 16 | Chapter names | STATIC2 0x1FCF20 | 14 / 13 | 77 | **done** `static2/scenario.json` | inline field, 0x58 stride |
| 17 | Stage location names (stage select / intro) | STATIC2 0x1FD3F0 | 138 / 41 | 203 | **done** `static2/scenario.json` | inline 0x40-byte field |
| 18 | Stage titles (two copies per stage) | STATIC2 0x1FF898 | 138 / 68 | 630 | **done** `static2/scenario.json` (27-letter limit) | **inline 0x38-byte field** |
| 19 | Stage summaries (`＠` = new line) | STATIC2 0x201B18 | 69 / 68 | 4,546 | **done** `static2/scenario.json` | pointer table; 4 lines x 448 px |
| 20 | Graphics: window headers, battle command / status icons | WND.BIN | 26 images | — | **done** (text) `ui/textures.json`; icons redrawn in 0.2.3; intermission header native English in 0.4.9 (`tools/redraw_wnd.py`), sortie-preparation header pending | redraw TX48 |
| 21 | Graphics: battle and status-effect banners | STATIC2 + MAP_ADD (same set twice) | 58 + 58 images | — | **done** (text) `ui/textures.json` | redraw TX48, both copies |
| 22 | Title logo | OPWND.BIN #44 | 1 | — | **done** (text) `ui/textures.json` | redraw TX48 (512x256) |
| 23 | XMB / save icons with the logo | ICON0.PNG, SAVE.BIN (2 PNG) | 3 | — | **done** (text) `ui/textures.json` | PNG |
| 24 | Game title | PARAM.SFO `TITLE` | 1 | 17 | **done** `ui/textures.json` | UTF-8, max 128 bytes |
| — | Debug messages | BOOT.BIN | 25 | 533 | skip (developer only) | |
| — | Font glyph-order table, name-entry kana tables | BOOT.BIN | 221 | — | skip (not text) | |
| — | Sort readings (katakana) for units / pilots | STATIC2 `Strg` | 262 / 266 | 3,223 | kept (sort keys, not displayed) | pointer table |
| — | Map tile names (`ロボット博物館@上`) | MAP_ADD.BIN `MPTI` 0x2AA8000 | 404 / 399 | 3,730 | skip (internal, see notes) | inline, 52-byte record |
| — | Effect asset names (`木星消去1`) | MAP_ADD.BIN 0x3340000 | ~74 | — | skip | internal |

Not part of this inventory:
- **Battle quotes**: `BATTLE2.BIN` sub-file 5, 51,587 strings / 10,227 unique. Decoded and exported
  by `tools/battle_quotes.py` (format in `docs/battle_quotes.md`); translated in
  `work/translation/en/battle/` and inserted since 0.3.0 (`--battle`).
- **Movies**: `MOVIE.BIN` holds 33 PSMF videos (opening, event demos, staff roll). Not checked for
  burned-in text, because there is no video decoder on this machine.
- **Battle animation graphics**: `BATTLE2.BIN` has no TX48 textures; its graphics use an undecoded
  format, so cut-in text (if any) is unchecked.

All non-dialogue text now has English (2026-10-03), except the BGM titles (out of scope by request)
and the rows marked skip. Nothing is inserted into a build yet. Checks: `tools/check_ui.py`,
`tools/check_boot_text.py`, `tools/check_static2_text.py`, `tools/check_scenario.py`,
`tools/build_static2_names.py`.

Why the map tile names are skipped: the names are cut off mid-word in their 30-byte record fields in
the original (for example ＤＧマスドライバー@ギガノス本), which text shown to the player would not be,
and they carry developer notes such as （穴） and （空中のみ）. Sort readings are only used to order
lists. If either turns out to be displayed, it can be added later.

## Notes by source

### BOOT.BIN (items 1-4)
- Every listed string is the target of at least one relocation (a code HI16/LO16 pair or a 32-bit
  data pointer), so any of them can be moved to new space by rewriting its relocations: **no byte
  budget**. 674 strings are referenced from more than one place. `room` in the export is the space
  before the next string, for strings that fit in place.
- Several descriptions are stored as two separate row strings (e.g. skill training: 格闘武器の攻撃力と移動力 /
  が上昇する。). The row count is fixed by code, so English has to be split at the same number of rows,
  each within the window width.
- Series titles exist in BOOT twice (two lists) and in the glossary; spirit command names exist in
  BOOT (spirit list, one-kanji abbreviations 精 加 手 …) and in STATIC2 `Sprt`.
- Name entry (`名前変更` screen): the input pages are hiragana / katakana / 英数 (alphanumeric) /
  記号 / 漢字, plus a Western / Japanese name-order toggle (欧米読み / 日本読み). The kana tables
  themselves are not translated, but the screen's labels are (item 1), and English players will use
  the 英数 page.
- 9 Japanese strings are not relocation targets: they are tails of longer strings that something
  points into the middle of, not separate text.

### STATIC2_ADD.BIN (items 5-19)
- `Strg` (names) and `Sent` (rows) are offset tables, so they can be rebuilt with any length;
  `Sent` rows can also change count by rebuilding the X… indexes (`docs/static2_format.md`).
- Description rows are at most 29 full-width characters wide, which is the width of the help box;
  English needs re-wrapping to the measured pixel width, as the dialogue does.
- Untagged scenario block at 0x1FCD80: five u32 offsets → chapter table, chapter names (0x58-byte
  records), stage locations (variable records, some stages list two places), stage titles (each title
  is stored twice, 0x38 bytes per copy) and the summary offset table (69 entries).
- Sort readings: libraries and unit lists probably sort by the katakana reading. Leaving them in
  Japanese keeps the Japanese order; replacing them with English sorts alphabetically, but only if
  the sort compares SJIS codes in a way that works for full-width Latin. Needs a test.

### Fixed-size fields (items 12, 16, 17, 18)
English is stored as full-width SJIS, **2 bytes per letter**, so inline fields hold half as many
letters as bytes: spirit names 5 letters (12 bytes with NUL), stage titles 27 letters (0x38). Titles
such as "The Immortal Machine, Getter Robo" are too long. Options: shorter English, single-byte
ASCII if the renderer accepts it (not tested), or moving the strings and patching the code that
reads them.

### Graphics (items 20-23)
- WND.BIN: headers インターミッション (#0) and 出撃準備 (#39); battle-command icons 攻 反 援 同 戦 支 避 防,
  each in a large and a small version; unit-status tabs 能 武 動 装 行 移 (HP is already Latin).
  These are 1-kanji icons in square boxes, so English needs abbreviations (ATK, CTR, …).
- STATIC2 #15-64 and MAP_ADD #23-72 are the same 50 banners (カウンター, 同時攻撃, 援護攻撃, barrier
  names, status-effect names …), plus 8 more each (重力波ビーム, 出入口, EWAC(強/弱), シールド防御,
  援護攻撃/援護防御/支援攻撃 in other colours). Both copies have to be replaced.
- Already English: START / LOAD / CONTINUE / OPTION, PRESS ANY BUTTON, NOW LOADING, HIT!! / MISS!!,
  Attack / Guard / Support, PLAYER / ENEMY PHASE, Connect, UNKNOWN (intermission map).

## Suggested order
1. Names that the glossary does not cover yet: 66 weapons and 2 parts (the other gaps are only the
   placeholder 無し "None"), then BGM titles (official English titles where they exist) and voice
   actors.
2. BOOT UI (item 1), measuring each window as it is translated (menus are narrow).
3. Descriptions and help (13, 14) with a row-wrap checker like `textfit.py`.
4. Scenario block (16-19), after deciding how to handle the fixed-size title fields.
5. Graphics (20-23).
6. Narration (2), save messages (4), PARAM.SFO (24).
