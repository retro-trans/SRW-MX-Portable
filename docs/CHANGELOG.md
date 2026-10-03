# Changelog

## Translation work — 2026-10-04 (not yet inserted into a build)

- Prepared all remaining routes, final/ending, hidden stage, unused scenes and
  save messages: 16,661 fresh rows across 235 packets using Sol 6.1 Medium.
- Completed and reviewed stages 31–35: 3,548 fresh rows and 4,446 full rows.
  All final lines fit; three stage 33 and two stage 34 drafts required shortening.
  Full initial drafts, decisions and measured widths remain.
- Corrected one demonstrated stage 33 source address typo in English only;
  retained uncertain wordplay, cultural references and incomplete source clauses.
- Extended campaign validation and context-review tools to separate manifests;
  completed stages 1–30 remain intact. Stage 36 translation is ongoing.
- Recorded source-backed speaker aliases and supplemental terminology. Further
  GitHub releases require the user's explicit instruction for that build.

## 0.4.2 — 2026-10-04 (unpublished local build, `work/output/SRWMX_EN_0.4.2.iso`)

- Translated every chapter-card title, covering all 67 scenarios, both starting
  routes, route branches, later stages, the hidden stage and the final stage.
- Enumerated 205 native bitmap copies: translated 160 Japanese copies and
  preserved 45 existing English copies. Two Pursuer placeholders are included.
- Genei LateGo captions fit one or two lines at 20 px, with complete descenders.
  Every palette, non-title pixel, background, chapter number and animation is
  preserved. No emulator texture replacement.
- Added guarded reproduction tool and per-copy source/palette hashes. Checked
  every changed rectangle and visually reviewed all translated title previews.
  Reopened the ISO and verified all 31 other files unchanged from 0.4.1.
- Native PPSSPP checks cover Stage 1 and a two-line renderer probe; full campaign
  and physical PSP playtesting remain pending. Story coverage remains 1–30.
- Full patch from the original Japanese ULJS-00041 ISO uses Retro Trans
  manifests, whole-image round-trip validation and release checksums.
- GitHub release returned to draft and removed from the active catalog at the
  user's request. Further releases require explicit permission.

## 0.4.1 — 2026-10-04 (`work/output/SRWMX_EN_0.4.1.iso`)

- Translated the requested Kaine save-message line in all three identical uses
  (`end_mes:21`, `:26`, `:31`). The English fits two dialogue lines.
- Translated the stage 1 Super chapter card to **Visitors from the Beyond**.
  Its lettering was located in `PACKMAPC2_ADD.BIN` at `0x14e1480` by matching
  the live GPU texture against the archive. Only the title's first 40 bitmap
  rows are edited; Chapter animation, digits, background and geometry remain.
- Native ISO asset patch with Genei LateGo Medium; no emulator texture pack.
- Incremental build from 0.4.0 preserves its stage 1–30 dialogue, battle quotes,
  UI and font fixes. The other 202 script blocks and all other MAP data are
  unchanged; the script area does not grow.
- Reopened the finished ISO and verified every patched file against the prepared
  bytes. Font copyright and SIL OFL notices accompany the build. See
  `docs/chapter_cards.md` and `work/output/screenshot_text_0.4.1_verification.json`.
- Verified the translated title card in isolated PPSSPP with texture replacement
  disabled; the live atlas matches the ISO pixel-for-pixel. Screenshot:
  `work/ui/chapter_card_0.4.1.png`. SHA-256 comparisons confirm the other 30 ISO
  files, including BOOT/EBOOT, fonts and battle data, are unchanged from 0.4.0.
- First GitHub publication packages this exact ISO as a full xdelta patch from
  the original Japanese ULJS-00041 image. README and release notes follow the
  SRW-Z project format. Retro Trans's builder verifies the complete patch round
  trip and supplies the standard manifest, validation report and checksums.
- Added source restoration from scene/string locations, release-building tools,
  translation instructions and font license notices. Only final English dialogue
  copies are committed; Japanese script and game images stay local.
- Published the 1,396,947-byte patch after full ISO round-trip verification and
  verification of downloaded GitHub assets. Registered v0.4.1 in the live
  Retro Trans catalog; the scoped refresh completed successfully.

## 0.4.0 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.4.0.iso`)

- **All story dialogue, stages 1-30, is now in the build.** Earlier builds only had the prologue,
  which is why stage 2 was still Japanese. The source is the reviewed `stageNN_campaign_full_merged.json`
  files plus the prologue. 26,483 script strings were replaced and the script area grew by 649
  sectors.
  - **One scene over the old limit:** s0210 (stage 8 map) is 0x30000 bytes, larger than any original
    block (0x25000). Script blocks are malloc'ed at their exact size from a 1.2 MB heap (heap object
    at 0x2F0E70), so the build now allows up to 0x40000 and prints a NOTE for such scenes.
  - **Watch stage 8** for "Malloc Memory Over".
- **Raise Stats screen:** labels shortened to Mel / Rng / Acc / Eva / Skl / Def. They overlapped the
  values.
- Includes everything from 0.3.3 (battle quotes, font fixes, help width).
- **Checked in game** (portable PPSSPP copy, `work/build/ppsspp_portable/`):
  - hero setup labels, favorite series text;
  - stage 2's opening dialogue (Genzo Umon) is English;
  - text checks and battle-quote verify pass (51,892 entries, 0 mismatches).
- **Not found yet: the chapter title card** ("Chapter.01" over the stage title). It is an image, not
  in TX48 / GIM form in WND, STATIC2, MAP_ADD, IM_ADD, OPWND or D2MAP. IM_ADD sub-file 2 is 146
  raw 8-bit 512x272 backgrounds, and the card is not among them. Still to search: IM_ADD sub-files
  1 and 3-8 (P2IG format), FACEPACK / SFACEPAK.

## 0.3.3 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.3.3.iso`)

- **Screen tabs no longer squeezed** ("Upgrade Unit", "Unit Stats", and so on, drawn 12x16). The
  narrow-font cut-off goes from 0.7 to 10/13, so 12x16 is scaled by the height. 14x18 library text
  and other near-square fonts are unchanged.
  - "Character Library" and "Sortie Preparation" (111 px) are 3 px over their 108 px tab; the
    game's own fit-to-width squeezes them about 3%.
- **Help window rows rewrapped to 416 px** (spirit, skill, ability and help descriptions, 448-464
  before). The help bar at the top of the screen holds about 420 px. The Sure Hit text ran past it
  (reported in game).
  - The Connect ability text (Xabl 34 and its help copy) was shortened to stay within 3 rows.
- Otherwise the same as 0.3.2. Not checked in game.

## 0.3.2 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.3.2.iso`)

- **Battle message text no longer stretched sideways.** The battle box (and some name headers) draw
  with a font wider than it is tall, which made English look squashed vertically (reported in
  battle). Latin glyphs in any font wider than tall are now scaled by the height, like the narrow
  value fonts since 0.2.2. This only makes text narrower, so nothing new can overflow. All 8 font
  sites, `vwf_patch.size_from_height`.
- Otherwise the same as 0.3.1. Not checked in game.

## 0.3.1 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.3.1.iso`)

- **New-game series pick screen:** the series name in the header is centred again. The game centred
  it by counting 16 px per character (Japanese width), so English names started off the left edge.
  The counting loop now calls the real width function, which knows the variable-width font
  (`insert_text.CODE_BLOCKS`, applied by `patch_centering`). The longest name (Machine Robo:
  Revenge of Chronos, 223 px) fits the box (about 265 px). Not checked in game.
- Otherwise the same as 0.3.0 (battle quotes included).

## 0.3.0 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.3.0.iso`)

- **Battle quotes in English.** All 10,227 lines (51,587 strings) from the 27 translated batches
  are in this build, done by `build_patch.py ... --battle` (`tools/battle_quotes.py`).
  - Each pilot's block keeps its records and gets English strings.
  - The rebuilt quote sub-file (3.2 MB) is appended to BATTLE2.BIN and the header points to it.
  - The STATIC2 pilot table is updated.
  - 45 long lines that do not fit their block's fixed 0x4800 read are served from a PRX table
    through three hooked pointer sites.
  - Format and loader: `docs/battle_quotes.md`.
- Verified by reading the ISO back: every quote entry matches its translation (0 mismatches).
  **Not yet tested in game** (the user is testing). Battle box width is an estimate (2 lines x 352 px).
- Everything else as 0.2.3. Still Japanese in battle: the Will (気力) label and the SHIELD-area
  graphics on the battle HUD (images, not yet redrawn).

## 0.2.3 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.2.3.iso`)

- **Battle and status icons redrawn in English** (`tools/redraw_wnd.py`, WND.BIN, 24 textures, done
  by the build with `--text`):
  - Large battle icons: ATK CTR SUP SIM SHP AST EVA DEF.
  - Small battle icons (two sets): AT CT SP SM SH AS EV DF.
  - 16 px status icons: ST WP MB AR DS MV, in the style of the game's own HP icon. Three letters do
    not fit in 14 px.
  - Each icon keeps its frame and palette; the English is drawn in the icon's own colours with a
    dark outline.
  - The two-letter forms are `en_icon` in `work/translation/en/ui/textures.json`; help entries 108
    and 120 explain them.
- Checked in game: the battle setup window (enemy attack, counter choice). Screenshot:
  `work/ui/text_0.2.3_battle_setup.png`.
- Still Japanese: the screen headers (INTERMISSION, SORTIE PREP), the battle and status-effect
  banners in STATIC2 / MAP_ADD, and the title logo.

## 0.2.2 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.2.2.iso`)

- **Squeezed values fixed.** Many screens draw values with a font much narrower than it is tall:
  10x15 for status-screen numbers and rank letters, 10x16 for weapon-list numbers. The Japanese game
  uses this to make full-width digits look half-width, but it squeezed our Latin glyphs to 60-67%
  width. When width/height is under 0.7, Latin glyphs are now scaled by the font height, so they
  keep normal proportions. Squarer fonts (labels, 12x16 tabs, 14x18 library text) are unchanged, so
  text already fitted to them does not move.
  - All 8 VWF sites are covered (`vwf_patch.py`: `hctx`, PRE stubs for W1/W3, and the native 4x
    renderer stubs).
- **Digits:** tabular width 10 (was 12), with no extra stretch. 0.2.1's wider digits were treating
  the same squeeze.
- **Pilot status spirit list:**
  - The cost column moved 14 px right (`insert_text.CODE_PATCHES`).
  - Accelerate / Inspiration / Super Guts / Encourage / Disturbance use the short forms already used
    on the map spirit menu (Accel, Inspire, S. Guts, Encour., Disturb).
  - akurasu's names are kept in the glossary; the short forms are listed in
    `docs/glossary_decisions.md`.
- **Skills:** Support Attack / Support Defend -> Support Atk / Support Def (Lv and +), Enhanced Human
  Lv -> Enh. Human Lv, Clear Mind Still Water -> Clear Mind. Applied in both copies (BOOT pilot screen
  table and STATIC2 names).
- **Hero / partner setup:** labels Name / Nick / Age without colons ("Name:" ran into the name).
- Checked in game: unit status, pilot status, weapon list, hero setup, Robot Library, opening
  narration. Screenshots: `work/ui/text_0.2.2_*.png`.
- Not fixed yet: on the new-game series pick screen, long series names ("Neon Genesis Evangelion",
  "Martian Successor Nadesico: Prince of Darkness") run past the left edge of the header box. That
  box uses a 16x20 font and was already like this before this build. (Fixed in 0.3.1.)

## Unreleased (after 0.2.1)

### 2026-10-03: Battle quotes decoded and sent to translation
- `BATTLE2.BIN` sub-file 5 decoded enough to export the quotes with their speakers: each pilot's
  block is found through a pilot table in STATIC2 (0x17E1C0). Details: `docs/battle_quotes.md`.
- `tools/battle_quotes.py`: export of 10,227 unique lines (51,587 in the game) into 27 batches
  grouped by series and pilot, a 2-line fit check, and batch merge and check commands.
- Translated by 27 Opus 5.5 agents at medium effort, one per batch, following
  `work/translation/en/battle/BRIEF.md`. Output: `work/translation/en/battle/batch_NN.en.json`.
  All 10,227 lines are done and all fit in 2 lines (`battle_quotes.py check`: 0 problems). No
  Japanese sentences are in the notes. 382 translator uncertainties, including 107 about names or
  attacks missing from the glossary, are in `work/translation/en/battle/uncertain.md` for review.
- Not inserted into a build yet; the reinsertion needs the sub-file re-laid out.

## 0.2.1 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.2.1.iso`)

- **Wider, fixed-width digits.** Numbers looked squeezed next to the Japanese original (reported on
  the weapon list). Every digit now has the same advance (12 of 18 px, was 6–10 by ink width), and the
  glyphs are drawn 1.2× wider and centred. Columns of numbers line up again. Changed in
  `make_latin_font.py` (DIGIT_W / DIGIT_STRETCH) and `vwf_patch.width_table`; the 4x atlas follows.
- Checked in game: weapon list and unit status screen fit with the wider digits.
  Screenshots: `work/ui/text_0.2.1_*.png` (before / after: `text_0.2.1_digits_before_after.png`).
- One UI label got wider than its Japanese original: the keyboard page tab "ABC/123" (+5 px). Not
  yet checked in game.
- Otherwise the same as 0.2.0.

## 0.2.0 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.2.0.iso`)

- **All non-dialogue text inserted** (`tools/insert_text.py`, `build_patch.py --text`): BOOT.BIN UI,
  narration, locations and save messages; STATIC2 names, descriptions, help, library, stage
  chapters / locations / titles / summaries, spirit names; PARAM.SFO title. Same dialogue as 0.1.5
  (prologue), same 4x font. Graphics with Japanese text are not redrawn yet; BGM titles stay Japanese.
- BOOT.BIN: 1,076 strings moved to a block appended to the PRX; 1,243 data pointers and 525 code
  references rewritten.
- STATIC2_ADD.BIN keeps its exact size (the game reads a fixed 0x3692C0 bytes into a fixed memory
  map). 3,694 strings that do not fit (364 KB, mostly library text) live in a PRX overflow table;
  the Strg / Sent / summary / spirit-name getters are patched to follow it. Details:
  `docs/text_insertion.md`.
- Tested in an isolated PPSSPP instance: title, OPTION, both libraries, demo select, save dialog,
  hero setup and rename, objectives, map command menu, spirit list, unit status, weapon list and
  details. Fixed in game: labels that ran into fixed-position values (status screen, libraries,
  rename screen, hero setup), weapon-list headers, the hero unit description rows, stage-number
  fragments, five spirit names shortened for the spirit list. Screenshots: `work/ui/text_0.2.0_*.png`.
- Not yet tested: intermission screens, battle screens, stage title cards and summaries, opening
  narration. Not tested on real hardware.
- New tools: `insert_text.py`, `verify_text_build.py`; `textfit.wrap` gained an `indent` option.
  Font licence notice: `work/output/SRWMX_EN_0.2.0_FONT_LICENSE.txt`.

## Unreleased (after 0.1.5)

### 2026-10-03 — All remaining non-dialogue text translated
- Scope: everything in `docs/text_inventory.md` except dialogue, battle quotes, movies and BGM titles.
  Nothing is inserted into a build yet; 0.1.5 is unchanged.
- STATIC2_ADD.BIN: 676 description and help entries (`work/translation/en/static2/descriptions.json`,
  `help.json`; 117 help entries reuse the matching description), all wrapped within their boxes;
  1,500 names (`names.json`: glossary names, 99 romanized voice actors, unit height/weight);
  32 spirit names (`spirits.json`; 15 are longer than the 12-byte inline field and need it moved);
  chapter names, 41 stage locations, 68 stage titles (akurasu wording, shortened to the 27-letter
  field where needed, full title kept) and 69 stage summaries (`scenario.json`).
- BOOT.BIN: opening narration (25 lines) and ending epilogue (31 lines), 34 intermission locations
  and 27 save / Memory Stick messages (`work/translation/en/ui/boot_text.json`); strings shown by the
  PSP system (save list, system dialog) are kept as plain ASCII.
- Graphics: English for the 26 WND.BIN icons and headers, the 58 battle/status banners (both
  copies), the title logo, icons and the PARAM.SFO title (`work/translation/en/ui/textures.json`).
  Icon abbreviations (ATK CTR SUP SIM SHP AST EVA DEF, STA WPN MOB ARM DIS MOV) match the help text.
  Images are not redrawn yet.
- Glossary consistency: "Power Riser (Garudi)" written as "Power Raiser (Garudi)" (akurasu majority
  spelling, 9 of 10). "Operation Bagration" replaces akurasu's misspelling "Baglicion"; chapter 5
  is "Turbulent Continent" (the game says 大陸) instead of akurasu's "Turbulent Earth".
- New checks: `tools/check_static2_text.py`, `tools/check_scenario.py`, `tools/check_boot_text.py`,
  `tools/build_static2_names.py`, `tools/merge_help.py`. `textfit.wrap` takes an `indent` argument
  (default unchanged) so help, summaries and narration wrap without the dialogue indent.
- Kept in Japanese on purpose: debug messages, katakana sort readings, map tile names (internal:
  cut off mid-word in the original records) and possible placeholder keys (see boot_ui.json).

### 2026-10-03 — Weapon names and BOOT.BIN UI translated
- Glossary: 66 weapon names and 2 part names that had no English were added to
  `work/glossary/campaign_terms.json` (source batch: `work/glossary/unused_weapon_additions.json`),
  following existing spellings (FA, FL, IRM Pod, Hand Rail Gun, Gravity Blast). None of the 66
  weapons is used by any unit in MX Portable; 4 are flagged uncertain. Every unit, pilot, weapon,
  skill, ability and part name now has English except the placeholder 無し ("None").
- UI: English for all 1,162 BOOT.BIN UI strings in `work/translation/en/ui/boot_ui.json`
  (959 translated; symbols, digits, debug text and possible placeholder keys kept). Stat and
  system terms follow akurasu (Melee, Ranged, Accuracy, Evasion, Skill, Defense, Will, Mobility,
  Armor, Weak/Normal/Strong/Super Strong); skill, spirit and part names follow the glossary.
  Two-row skill help is written so that shared rows read correctly with every partner row.
- New `tools/check_ui.py`: coverage, format codes, drawable characters and width against the
  Japanese. 68 strings are wider than the widest Japanese entry of their list; they need checking
  in game. 7 open questions are listed in the file's `uncertain` field. Not inserted into a build.

### 2026-10-03 — Non-dialogue text inventory
- New `tools/text_inventory.py`: exports every non-dialogue Japanese string with location, size,
  owner and glossary English to `work/source/text_inventory/` (local only, contains Japanese).
  BOOT.BIN strings are found through relocation targets, so each entry is known to be movable.
- New `docs/text_inventory.md`: 24 text sources. About 32,000 Japanese characters still need
  English outside the dialogue and the (already translated) library; the glossary already covers
  most unit, pilot and weapon names. Fixed-size fields (spirit names, stage titles) are flagged.
- Graphics with Japanese reviewed on contact sheets in `work/ui/textures/`: 26 in WND.BIN, the same
  58 banners in both STATIC2_ADD.BIN and MAP_ADD.BIN, the title logo and three icons.
- Not checked: the 33 videos in MOVIE.BIN and battle animation graphics. No build change.

## 0.1.5 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.1.5.iso`)

- Fixed truncated descenders in the native 4x atlas. The 60 px source glyph
  for g extends to row 75, below the old 72 px temporary canvas. Render into
  a larger temporary canvas before cropping/packing the complete glyph.
- Restored g, j, p, q, y and comma. Every other packaged glyph is byte-identical
  to 0.1.4. Glyph placement, VWF widths, renderer code, memory use, Japanese,
  translation wording and included prologue scenes are unchanged.
- Added a check against the complete FreeType glyph masks to catch source
  clipping. Packaged ISO/font/hooks/relocations and all 21,586 row fit checks
  pass. Comparison: `work/ui/font_descenders_0.1.5.png`; reports in
  `work/output/font_0.1.5_verification.json` and
  `work/output/font_0.1.5_descender_check.json`.
- Verified the updated atlas/code/hooks in an isolated PPSSPP instance, with
  texture replacement disabled. A breakpoint on g confirmed its updated
  atlas row, 72 px texture height and unchanged 8 px advance. In-game capture:
  `work/ui/font_native4x_0.1.5_dialogue.png` (software renderer, PSP resolution).

## 0.1.4 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.1.4.iso`)

- Added a native 4x Latin font atlas inside BOOT/EBOOT, with no emulator
  texture replacement. Genei LateGo is rasterized from the TTF at 60 px in
  72x72 cells; the renderer samples it at the existing on-screen text size.
  VWF widths, line wrapping, translation wording and Japanese cells are unchanged.
- Patched all four renderers, four width functions, four glyph lookups and
  four texture-height instructions. Latin rows upload as 512x128 4bpp textures.
  Extended the original PRX load segment after its original memory allocation;
  zero-initialized BSS is retained. Additional game memory: 256,216 bytes.
- Verified packaged atlas/code/hooks/relocations and matching BOOT/EBOOT.
  All 21,586 checked rows fit. An isolated PPSSPP instance with texture
  replacement disabled reached the prologue and displayed translated dialogue.
  Live checks matched the relocated code and atlas, and confirmed 512x128
  uploads / 72 px texture height / unchanged 14 px W advance.
- Evidence: `work/output/font_0.1.4_verification.json` and
  `work/ui/font_native4x_0.1.4_dialogue.png`. The screenshot uses the software
  renderer at PSP display resolution; a 4x hardware-rendered screenshot and
  physical PSP testing remain unverified. The test ISO contains the prologue;
  campaign insertion remains pending. SIL OFL notices accompany the ISO.

## 0.1.3 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.1.3.iso`)

- Replaced HarmonyOS Sans Condensed with Genei LateGo v2 Medium, from the
  official v2.1 separate-TTF package: https://okoneya.jp/font/genei-latin.html.
  Rendered at 15 px without Latin shadows; original Japanese cells retained.
- Regenerated the atlas and matching VWF table/hooks. Latin advances vary:
  i = 3 px, M = 12 px, W = 14 px at the dialogue font size. Font glyphs do not
  clip their 18x18 atlas cells. The font uses SIL OFL 1.1; source copyrights and
  licence are in `work/output/SRWMX_EN_0.1.3_FONT_LICENSE.txt`.
- Verified the packaged ISO atlas, BOOT/EBOOT equality, VWF table and all eight
  hooks. All 21,586 checked rows (562 prologue plus 21,024 campaign rows) fit.
  Translation wording is unchanged. Test ISO includes the prologue, as in 0.1.2;
  campaign insertion and emulator validation remain pending.
- Added reusable font preview/verification tools and retained the previous
  atlas. Evidence: `work/output/font_0.1.3_verification.json`.

## 0.1.2 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.1.2.iso`)

- Latin glyphs rendered **without the drop shadow** (`SHADOW = False` in `make_latin_font.py`); the
  original Japanese glyphs keep theirs. Each glyph is 1 px narrower; all translated rows still fit.
  Otherwise identical to 0.1.1. Preview: `work/ui/font_harmony_noshadow.png`.

## 0.1.1 — 2026-10-03 (test build, `work/output/SRWMX_EN_0.1.1.iso`)

- **Font switched** from the Arial Narrow Bold prototype to HarmonyOS Sans Condensed (Huawei), Bold
  instance, 15 px. Font file and licence in `incoming/fonts/`; `make_latin_font.py` now reads the font from
  there and supports variable-font instances (`VARIATION`). Licence: free use/redistribution, no
  modification of the font files, and a prominent "uses HarmonyOS Sans" notice is required in the release.
- Lines are ~3% narrower than before with the in-game width table; the prologue (562 rows) and every
  Stage 30 candidate re-checked: 0 overflows. Comparison strip: `work/ui/font_compare_arial_vs_harmony.png`.
- Build content otherwise identical to 0.1.0 (VWF + prologue). Not yet booted in the emulator.

## Unreleased (after 0.1.0)

### 2026-10-03 — Stages 1-30 campaign completed
- Six distinct actual Sol 6.1 Medium translators per stage completed all listed
  numbered routes: 16,092 fresh rows in 241 packets; full assemblies retain
  21,024 stage-local unique rows and every original scene use.
- All coverage, source identity, placeholder, speaker, character, spelling and
  current-font checks pass. Coordinator review fingerprints cover the exact
  final wording and shared contexts; source ambiguities remain documented.
- Stage 30: 680 fresh rows, 839 full rows, 1,116 uses. Only 464/596 shortened
  after initial measured overflow; full drafts and historical fit reports kept.
  Added source-scoped names, Pliny attribution and literal technical labels.
- Saved final completion audit with current font provenance; updated handoff,
  progress and context notes. Integration and in-game testing remain pending.

### 2026-10-03 — Campaign stage29 translated
- Six actual Sol6.1 Medium translators completed363 fresh rows; full530 rows
  and611 scene uses checked. All167 reuse contexts and10 fresh flags reviewed.
- Only58/110 compressed; passive58 preserves the omitted actor after independent
  grammar review. Existing Bright response retained after context review.
- Initial drafts retained; matching fingerprint recorded. Stage30 subsequently completed.

### 2026-10-03 — Preserve immutable speaker labels in checks
- Fixed spelling validation/reconciliation conflicting with source-prefilled
  Galfa Emperor. Prefill equality remains enforced; body spellings still checked.
- Direct complete Stage29 validation passes363 rows after this correction.
- Added source-literal Stage30 field/operation names with provenance flags.

### 2026-10-03 — Campaign stage28 translated
- Six actual Sol6.1 Medium translators completed626 fresh rows in8 packets;
  full802 rows reviewed, including176 reused rows and8 fresh flags.
- Only plain316 overflow compressed. Corrected two exact contextual responses,
  preserving prior owner outputs; clarified activation471 and glossary rank209.
- Initial drafts retained; context fingerprint recorded. Continue stages29–30.

### 2026-10-03 — Stage29 source terminology
- Added three literal terms, retaining source/provenance uncertainty and marking
  the silicone body-coating interpretation as a contextual inference.

### 2026-10-03 — Stage28 activation terminology
- Added source-literal technical command labels and corroborated Incrementum's
  spelling, with explicit limits on English provenance and no added mechanics.

### 2026-10-03 — Campaign stage27 translated
- Six actual Sol6.1 Medium translators completed123 fresh rows in6 packets;
  no compression needed. All146 shared rows and3 fresh flags reviewed.
- Preserved hostile insults/death threats, source allusion and literal radio
  identification provenance; rescue requests and disabled D-1 context checked.
- Initial drafts retained; full checks and matching context fingerprint pass.
  Stage28 underway; continue through30. No new build or sheet posting.

### 2026-10-03 — Stage28 J-Kaiser alias
- Mapped game orthographic variant to existing J-Kaiser glossary spelling,
  corroborated by licensed Good Smile English product text. No mechanics added.

### 2026-10-03 — Campaign completion audit
- Added a read-only audit for six distinct actual translators per stage,
  validated packets, retained drafts/reports/safe copies, unchanged original
  rows/kinds/owners/scene uses, binding-rule hashes and exact review fingerprints.
- Preview and saved audit through26 pass:14,300 fresh rows,18,584 full rows,
  212 packets. Full30 audit will follow completion of remaining stages.

### 2026-10-03 — Campaign stage26 translated
- Six actual Sol6.1 Medium translators completed86 fresh rows in6 packets;
  restored234 original rows. All148 shared rows and3 fresh flags reviewed.
- Only measured dialogue overflow63 compressed; nuclear-threat activation,
  worldwide consequence and timing preserved. Source-short references and
  unfinished plans remain intact; initial drafts retained.
- Context fingerprint recorded; Stage27 underway, continue through30.

### 2026-10-03 — Stage27 radio identification
- Added source-literal Yellow Mountain Squad with explicit unverified English
  provenance; no geographic or formation-history inference.

### 2026-10-03 — Campaign stage25 translated
- Six actual Sol6.1 Medium translators completed199 fresh rows in6 packets;
  restored359 original rows and426 scene uses. All160 shared rows and6 fresh
  uncertainty flags reviewed in original contexts.
- Only measured plain overflow140 compressed; removed added capture sequencing
  and restored contempt91. Alternate capture events and hidden voice preserved.
- Initial drafts retained; full checks and matching context fingerprint pass.
  Stage26 underway, Stage27 started; continue through30. No new build or sheets.

### 2026-10-03 — Stage26 terminology coordination
- Sourced Suruga Bay from Akurasu and official government geography; retained
  source-short Fuji without narrowing the region to city or mountain.
- Preserved broad N2 weapons wording with sourced N2 spelling and explicit
  English compound provenance caveat.

### 2026-10-03 — Campaign stage24 translated
- Six actual Sol6.1 Medium translators completed473 fresh rows in6 packets;
  restored637 original rows. Reviewed164 reused rows in every actual context.
- Compressed only measured overflows33/70/448, preserving ritual astronomy,
  headquarters report and region. Retained cryptic targets and provenance flags.
- Initial drafts preserved; matching context fingerprint recorded. Stage25
  underway; continue through30. No new build or sheet posting.

### 2026-10-03 — Stage25 terminology coordination
- Added official Japanese-backed Data Weapon install commands and source-short
  references, preserving Akurasu full names and English provenance limits.
- Recorded Rom's literal electronic sacred beasts descriptor with official
  Dendoh source; no name expansion or invented mechanics.

### 2026-10-03 — Campaign stage23 translated
- Six Sol6.1 Medium translators completed824 fresh rows in11 packets. Restored
  all1,003 original rows and1,103 scene uses; only overflow666 compressed.
- Reviewed179 reused rows and44 fresh flags, corrected mock-praise titles and
  retained hidden dream voices, symbolic imagery and technical provenance limits.
- Initial drafts preserved; full checks and matching review fingerprint pass.
  Stage24 underway; continue through30. No new game build or sheet posting.

### 2026-10-03 — Stage24 terminology coordination
- Sourced the Zeta recollection's short names/ranks and Earth Sphere to Akurasu;
  retained existing castle-title wording and provisional technique romanization.
  Cryptic Heaven and collective Hakke remain source-dependent.
- Added contextual ki/tanden rendering and Akurasu Gundam Fighter title,
  retaining the explicit GEAR Fighter joke.
- Added Akurasu-backed operation/location/organization wording and literal energy
  compounds. Researched ritual astronomical imagery, preserving source numbers
  and recording contextual inference and licensed-wording limits.

### 2026-10-03 — Stage23 terminology coordination
- Recorded Kaji-scene nickname, departments and First Angel with source-local
  scope; game-specific government affiliation is preserved.
- Excluded source Ryoji from the Ryo nickname scan; no existing translation
  required alteration. Full Ryoji Kaji remains distinct from Ryo/Ryoma.
- Coordinated symbolic/musical wording, literal Contact red alert and unexpanded
  AC recorder with explicit source and provenance limits; preserved hidden labels.
- Added Dead Sea Scrolls, Central Dogma and source technical/musical labels to
  the campaign supplement with references and explicit provenance limits.
- Translation continues; no source identity or mechanism is added by terminology.
- Reused the retained Stage21 worker3 as actual Stage23 worker5 to occupy the
  held concurrency slot; six distinct translators still serve Stage23. Dispatch
  records support explicit actual task names and worker roles.
- Added an exact stage/full-row context override path for reused English replies;
  source/owner/old-English guards preserve earlier drafts and assemblies. No
  override wording is applied until reviewed and saved explicitly.

### 2026-10-03 — Campaign stage22 translated
- Six Sol6.1 Medium translators completed385 new rows in six packets; all552
  original rows and scene uses restored. Only measured overflows69/235 shortened.
- Reviewed167 shared rows and26 fresh flags. Corrected exclusive defense/evasion
  and command-position address; coordinated radio insults and gorilla wordplay.
- Initial drafts retained, checks pass and context review recorded. Stage23 started.
  No new build or sheet posting.

### 2026-10-03 — Stage22 terminology coordination
- Added source-short Gespenst and Zapat, provisional flashback names/callsign,
  official Niigata spelling and coordinated radio-joke/romance wording.
- Recorded the established Zapat exception to Akurasu's alternative spelling;
  independent-name and localization limits remain explicit. Stage22 continues.

### 2026-10-03 — Campaign stage21 translated
- Six Sol6.1 Medium translators completed261 new rows in six smaller packets;
  restored all434 rows and501 original scene uses. No compression needed.
- Reviewed173 shared rows and11 fresh flags, including all scene uses and final
  neighbors. Full checks and matching review fingerprint pass; initial drafts retained.
- Preserved identity ambiguity, source cutoffs, conditional resolve, literal imagery
  and theory provenance. Stage22 underway; no new game build or sheet posting.

### 2026-10-03 — Campaign stage 20 translated; stage21 terminology
- Six Sol6.1 Medium translators completed339 fresh rows in six packets and
  restored all488 stage rows and scene uses. Only measured overflow74 shortened;
  reviewed149 shared rows and18 fresh flags. Full checks and review fingerprint pass.
- Added literal moonlight, source-short Dr. Katsuragi and Super Solenoid/S2 theory
  to the campaign supplement with source and independent-wording limits.
- Stage21 continues with six actual translators. Drafts retained; no new build or posting.

### 2026-10-03 — Campaign stages 18 and 19 translated
- Six Sol Medium translators per stage completed 1,544/532 new rows in20/7
  packets; assembled all1,715/686 rows with original uses restored.
- Stage18 compressed only six measured dialogue overflows; Stage19 required none.
  Reviewed all171/154 shared rows and35/7 fresh flags; final review fingerprints
  match and structural, character, placeholder, spelling and font checks pass.
- Preserved ambiguous labels, slogans, metaphors, hidden identities, battle-event
  alternatives, confessions and paired jokes. Agent meaning/rank corrections
  precede sourced name reconciliation; all complete initial drafts retained.
- Restored approved source-short Dr. Plato in stages2/11/18; full source names
  remain full and earlier review fingerprints renewed. Stage20 underway.
- No new game build or sheet posting.

### 2026-10-03 — Stage 20 terminology additions
- Added descriptive Hyakki mech/soldier and Photon Power reactor/rocket-engine
  compounds using established stems, with explicit independent-label limits.
- Stage 20 translations proceed with six separate worker intervals.

### 2026-10-03 — Stage 19 terminology review started
- Added source-short Beam Searcher, Second Red, bio-pattern, Mishima district,
  Tau and Aen with provenance and scope limits; unsettled English labels remain flagged.
- Stage 19 translators retain full initial drafts and actual-font fit reports.
- Stage 18 rank corrections now preserve the established Ruri and Yurika forms;
  recorded Burr-head's source haircut metaphor and official Zabi family spelling.
- Added source-scoped reversal of earlier Dr. Plato full-name expansion;
  full Japanese names remain full and initial drafts are retained.

### 2026-10-03 — Stage 18 terminology additions
- Added source-derived promotion ranks and Special Duty Second Lieutenant,
  with official Japanese setting references and explicit English mapping limits.
- Recorded Middi's surname address without inventing an academic title, and
  Rom's literal catchphrase with its localization uncertainty retained.
- Added source-short aliases, Little Baam, Iwato, calculation unit, colony names
  and the recurring coup slogan with scope/provenance notes. Approved Dr. Plato
  short body references now pass glossary validation without expanding the source.
- Stage 18 translation packets continue; full drafts and measured fit reports remain available.

### 2026-10-03 — Campaign stage 17 translated
- Six Sol Medium translators completed 788 new rows in ten separate packets;
  assembled all 958 rows with every original use. All initial/final rows fit;
  no compression required. Reviewed all 170 reused rows and 28 fresh flags.
- Preserved hidden identities, branching endings, source poetry, wordplay and
  opaque metaphors; agent review restored a complete Ruri declaration and removed
  added noun epithets/titles. Full initial drafts remain available.
- Added sourced Gundarium alloy, myth reference and transparent Nadesico labels
  with explicit limits. Stage 18 underway; Operation Maelstrom, Salem Medal and
  Folia Esto sourcing added. Approved Dr. Plato short speaker alias retained.
- No new game build or sheet posting.

### 2026-10-03 — Campaign stage 16 translated
- Six Sol Medium translators completed 562 new rows in eight separate packets;
  assembled all 713 rows with every original use. Three measured dialogue overflows
  compressed; all final rows fit and initial drafts remain available.
- Reviewed all 151 reused rows and five fresh flags. Unnamed referents, source
  allusions, literal epithet and affiliation provenance remain explicit.
- Added sourced geography, navigation stars, Minovsky particles and White Devil;
  Federation Space Force remains transparent source wording with licensed-label limit.
- Stage 17 underway; Hangzhou Base and official Gundarium alloy naming added.
  No new game build or sheet posting.

### 2026-10-03 — Campaign stage 15 translated
- Six Sol Medium translators completed 865 new rows in eleven separate packets;
  assembled all 1,039 rows with every original use. Two measured overflows compressed,
  preserving boarding deadline/action and dock-ship intelligence; all final rows fit.
- Reviewed all 174 reused rows and nine fresh flags. Broken radio fragments,
  hidden references, dialect/wordplay and terminology provenance remain explicit.
- Agent meaning review restored deliberate cutoffs and removed added titles/insult.
  Source-scoped name scripts restored Harry, Oyakata-sama and Rom Stol afterward;
  original drafts, full Hari Makibi and speaker Hari retained.
- Stage 16 underway. Added sourced geography and short Gundam aliases, with a
  provisional Heavenly Sword, Peerless Blade epithet. No new build or sheet posting.

### 2026-10-03 — Stage 15 review and terminology
- First 560 fresh lines translated; no measured overflow in those seven packets.
  Review corrected an added insult and is restoring a deliberate cutoff and
  removing decorative honorific titles. Initial drafts remain available.
- Added sourced Scramble Turn, Baam War and Aoi Report entries with explicit
  limits on independently licensed English wording. Extended the preview-first
  nickname tool to preserve spoken Harry versus full Hari Makibi and speaker Hari.
- Remaining stage 15 packets continue with the same six actual translators.
  No new build or sheet publication.

### 2026-10-03 — Campaign stage 14 translated
- Six Sol Medium translators completed 345 new rows in six packets and assembled
  all 502 rows. One measured briefing overflow compressed; all final rows fit.
- Reviewed all 157 reused rows and six fresh uncertainty flags. Preserved hidden
  referents, unfinished defenses, activation labels and distinct Earth/Moon choices.
- Added official-source File Load provenance, distinct from saving and installation.
  Retained menu breaks and every original use. Initial drafts remain available.
- Stage 15's Earth/Space routes underway in eleven packets; King Fleed's source
  designation added with an explicit English-provenance limit. No new game build.

### 2026-10-03 — Campaign stage 13 translated
- Six Sol Medium translators completed 375 new rows in six packets and assembled
  all 536 rows. One measured transmission overflow compressed; all final rows fit.
- Reviewed all 161 reused rows and fourteen fresh uncertainty flags. Preserved
  Quon's cryptic imagery, inferred referents and source-literal terminology.
- Added scoped RahXephon location/nickname/souvenir/system entries with provenance
  limits. Removed one decorative Rikudo honorific after meaning review; fixed the
  name tool's handling of a short canonical name within an old longer form.
- Stage 14 underway; original drafts and scene uses retained. No new game build.

### 2026-10-03 — Campaign stage 12 translated
- Six Sol Medium translators completed 235 new rows in six packets and assembled
  all 383 rows. Every initial and final row fits; no compression required.
- Reviewed all 148 reused rows and eleven fresh uncertainty flags in context.
  Hyakki wordplay, the sisters' incomplete comparison and terminology provenance
  limitations remain explicit. Verified source-short Yousaiki and amplifier aliases.
- Stage 13 underway; initial drafts and source uses retained. No new game build.

### 2026-10-03 — Campaign stage 11 translated
- Six Sol Medium translators completed 545 new rows in seven separate packets;
  assembled all 710 rows. All final rows fit, with one measured overflow compressed.
- Reviewed all 165 reused rows and thirteen fresh uncertainties. Hidden identities,
  unfinished comparisons and context-sensitive actor choices remain source-dependent.
- Added sourced Nadesico aliases, Kyoto ceremony names and provisional fictional
  labels; reconciled canonical Gryps Conflict after meaning review. Source-short
  Medius and Reppu member address are retained without premature identity expansion.
- Stage 12's six workers underway. Added source-equivalent Getter Ray amplifier
  naming and a preview-first fixed-spelling tool; preserved initial drafts. No new build.

### 2026-10-03 — Campaign stage 10 translated; nickname reconciliation
- Six Sol Medium translators completed 337 new rows in six packets and assembled
  all 489 rows. One measured objective overflow compressed; all final rows fit.
- Reviewed 152 reused rows and four fresh uncertainties against original uses.
  Retained interrupted adult-museum allusion and Mazinger wordplay/identity limits.
- Added sourced Ryo nickname and scanned all 30 fresh sources plus prologue.
  Corrected five Stage 2 final lines and two legacy assembly copies, preserving
  drafts and original prologue/build. Rechecked propagated names and renewed
  already completed context-review fingerprints. Added preview-first name tool.
- Stage 11's six workers underway; added sourced geography/event labels and
  explicit uncertainties for fictional temple/plan naming. No new ISO build.

### 2026-10-03 — Campaign stage 9 translated
- Six Sol Medium translators completed 262 new rows in six packets and assembled
  all 413 rows. Every initial/final row fits; no compression required.
- Reviewed all 151 reused rows and eight meaningful fresh uncertainties against
  original uses. Hidden identities, 5A and unfinished comparisons remain unexpanded.
- Added Akurasu-backed Fossil Beast/Reiko Hibiki/Schwarz Bruder mappings, with
  sourced character profiles. Applied existing Star of Ra Mu spelling consistently.
- Stage 10 underway with six workers. No new ISO build.

### 2026-10-03 — Campaign stage 8 translated
- Six Sol Medium translators completed 1,074 new rows in fourteen packets;
  assembled all 1,239 rows. Every final row fits; five measured overflows compressed.
- Reviewed all 165 reused rows and meaningful fresh uncertainties. Agent corrections
  restored instant attack timing and an any-attack loss trigger; initial drafts retained.
- Added sourced Eva equipment, geography, character aliases and literal commands;
  retained wordplay and unestablished English terminology notes. Review aid can now
  display finished raw packets while a stage is pending, excluding safe copies.
- Stage 9 finishing and stage 10 started. No new ISO build.

### 2026-10-03 — Campaign stage 7 translated
- Six Sol Medium translators completed 628 new rows in eight packets and assembled
  all 785 rows. Every final row fits; two measured overflows were compressed.
- Reviewed all 157 reused rows and meaningful fresh uncertainties in original
  contexts. Preserved Gozen alias, concealed relationship self-correction, MA...
  cutoff and exact Star Era 4085 rather than adding unspoken identities/actions.
- Added sourced campaign terms and started stage 8's six workers. No new ISO build.

### 2026-10-03 — Campaign stage 6 translated
- Six Sol Medium translators completed429 new rows in six packets and assembled
  all582 rows. Every final row fits; one measured mission-objective overflow compressed.
- Reviewed153 reused rows and retained three postbattle interpretive notes with
  original context. Added sourced Nasu Highlands/Silver and contextual acronyms/jokes.
- Started stage7 with six workers in waves. No new ISO build.

### 2026-10-03 — Campaign stage 5 translated
- Six Sol Medium translators completed 315 new rows in six packets and assembled
  all 482 stage rows. Every final row fits; one measured overflow was compressed.
- Reviewed all 167 reused rows against original uses, including the shared autograph
  sequence. Retained open-ended protagonist thought and literal radio/minion labels.
- Added Akurasu-backed Raizo Kasshu and location names, and original-context review
  aid. Stage 6 underway. No new ISO build.

### 2026-10-03 — Campaign stage 4 translated
- Six Sol Medium translators completed 618 new rows in eight packets; assembled
  all 765 stage rows. Every final row fits; only one measured overflow compressed.
- Reviewed 147 reused rows against original contexts, retained fixed title and
  two wordplay limitations, and recorded exact review fingerprint. Added source
  nickname and stable literal term conventions. Stage 5's six packets underway.

### 2026-10-03 — Campaign stage 3 translated; six-worker short stages
- Completed stage 3's 787 new rows in ten packets and assembled all 939 rows.
  Every final row fits; two measured overflows were compressed. Source ambiguities
  and technical-name provenance remain explicit in drafts/reports.
- Reviewed reused contexts in stages 1-3 and recorded wording/use fingerprints.
  Retained fixed Oyakata-sama per main glossary; added source-backed cameo names
  and literal technical labels. Stage 4 is underway.
- Split untouched short stages into six smaller nonempty assignments, retaining
  the same source rows and owners. Queue now has 241 packets; interval-aware
  checks preserve exact coverage and the 80-row maximum. No new ISO build.

### 2026-10-03 — Campaign stages 1 and 2 translated
- Six Sol 6.1 Medium translators per stage completed 1,492 new rows in 20 packets.
  Assembled 873/1,068 full stage rows with original scene uses; retained initial
  drafts, decision reports, source uncertainties and pending shared-context review.
- Coverage, placeholders, characters, font fit and fixed spellings pass. Only
  two stage 2 measured overflows required compression; no stage 1 compression.
- Sourced supplemental campaign terms and scoped Fury's Spirit Command alias
  away from the unrelated alien civilization. Started stage 3. No new ISO build.

### 2026-10-03 — Stages 1-30 Sol Medium campaign started
- Prepared all numbered stages 1-30, including route branches, for Sol 6.1 Medium.
  Linked exact-source repeated rows and finished prologue lines while preserving
  full Japanese context, event order, and every scene use for final assembly.
- Saved rule snapshots and a durable six-worker queue: 16,092 new rows in 215
  assignments of at most 80 rows. Started the first stage with three concurrent
  translators; six logical workers run in waves under the session slot limit.
- Added preview-first guarded source preparation and campaign documentation.
  Numbered mission conditions retain plain-row line breaks. No new ISO build.

### 2026-10-03 — Sol 6.1 effort comparison
- Completed fresh translations of all 376 Stage 30 Space rows at Low, Medium, High and
  XHigh effort in 20 independent contexts; recorded model/effort settings were verified.
  Initial full drafts are preserved, with only measured overflow compressed.
- All four candidates pass final fit, placeholder, character, speaker and source-backed
  spelling checks. Reported uncertainties remain available for human wording review.
- Posted four effort columns H:K and 1,044 notes to the user's Translation Test 3 sheet
  `16nyBAPVH1OSQdYo8qMxxqmS5YtceGeK45DZt9prjuWQ`. Original tab id 0 is retained;
  all 1,528 candidate occurrences, notes, reviewer controls and preserved cells were read
  back. Read-only exported layouts, longest dialogue and longest note were inspected.
- Verified row 357 technical identifiers preserve exact source game bytes in ASCII form;
  identical clarification went to each effort level. Low/Medium report-only follow-ups
  left bodies/drafts unchanged and are included in measured usage.
- Saved four-way CSVs, 48 verified safe JSON copies, metrics, shared protocol, input/byte
  audits, token counts and `docs/stage30s_sol_effort_comparison.md`. Standard credit
  estimates: Low 32.82, Medium 36.32, High 46.62, XHigh 70.78, excluding coordination.
- Extended the exporter and added guarded empty-tab posting and session-usage tools.
  Glossary, previous comparison sheets and build 0.1.0 are unchanged; no game insertion.

### 2026-10-03 — Translator usage audit
- Recovered the final cumulative token counts for 40 OpenAI translator contexts across eight
  candidates, including the updated-rules rerun; coordinator usage is excluded.
- Identified the historical Codex-session candidate as Sol 6.1 / High effort. Sol overrides
  used Low; Astra, Luna and Terra used Medium. Corrected earlier effort/identity uncertainty
  in the reports and handoff, with dated clarification on the original protocols.
- Saved `docs/stage30s_translator_usage.md` and local metadata-only audit/summary files with
  Standard credit-equivalent estimates from published rates. Actual billed credits and
  subscription allowance consumption are not established. Sheets, translations and build
  0.1.0 are unchanged.

### 2026-10-03 — OpenAI retranslation under updated rules
- Completed all 376 rows independently with Sol 6.1, Astra 6 and Terra 5.6 under the current
  `BASE_RULES.md` and `TRANSLATOR_BRIEF.md`, tagged `sol61r2`, `astra6r2`, `terra56r2`.
  Luna is excluded at the user's request. Earlier comparison files remain historical records.
- The target is the user's new "Translation Test 2" spreadsheet. Existing Opus/Sonnet/Fable reruns,
  reviewer cells and the Prompt tab were retained and verified unchanged. Luna was already absent
  in that destination and is excluded from the completed six-candidate comparison.
- All rerun translators receive event boundaries/repeat context, matching the new Claude runs.
  Shared instructions are saved in `docs/model_comparison_protocol_r2.md`; input hashes are local.
- All three candidates fit, with intact placeholders, source speakers and row counts. Raw spelling
  findings remain: Sol/Terra row 287 (Jamitov Hymem/Hymen), Terra row 308 (Guiltor/Guiltorre).
  Three source-backed automated notes flag them separately from translator notes; glossary unchanged.
- Posted columns K:M and 719 notes (716 translator notes plus three checks). Verified all 1,146 new
  translation cells and preserved existing values, formatting, validation, notes and unrelated tabs.
  Read-only exported layout previews were inspected, including the longest new dialogue/note.
- Extended the in-place sheet updater for explicit destinations and unrelated-tab preservation, the
  exporter for six updated-rules candidates, and the checker for source-backed review variants.
- Saved six-way CSVs, metrics, input/rule snapshots, summary, 36 verified safe JSON copies and the run
  report `docs/stage30s_updated_rules_openai.md`. Build 0.1.0 remains unchanged.

### 2026-10-02 — Stage 30 re-run under the new rules (Opus 5.5, Sonnet 5.5, Fable 5.1)
- All 376 Stage 30 Space rows translated again by three models (tags `opus2`, `sonnet2`, `fable2`;
  no Haiku) in 15 fresh contexts under the current `BASE_RULES.md` / `TRANSLATOR_BRIEF.md`. New for
  this run: translators were given `stage30s_order.json` (event boundaries, repeated lines) and were
  not allowed to open any earlier Stage 30 translation.
- Checks (`tools/check_translation.py` plus an independent pass): 376/376 rows per model, every row
  fits 3 lines × 352 px, no unsupported characters, placeholders intact, no old spellings.
- Posted to a new review sheet ("Translation Test 2", tabs `Stage 30 Space` and
  `Stage 30 Space notes`): 382 play-order lines, 327 translator notes. The sheet's existing `Prompt`
  tab was not touched. The first sheet and its nine candidates are unchanged.
- Translator working files that had been left in the script folder were moved to the ignored
  `work/build/stage30s_rerun_scratch/`. Commit-safe copies refreshed with `strip_jp.py`.
- Not inserted into a build; 0.1.0 is unchanged.

### 2026-10-02 — New translation rules in BASE_RULES.md
- Added five rules adapted from LinguaGacha's English prompt template (reworded): one row in / one row
  out, spoken register, a two-step context/decisions check per row, translate what the player reads and
  leave what the game reads, no softening. The template's pronoun rule was already covered.
- The "incomplete line stays incomplete" rule is scoped to row boundaries and deliberate fragments, so
  it does not override restoring a subject or verb that Japanese grammar drops.
- `TRANSLATOR_BRIEF.md` points to `BASE_RULES.md` for these rules instead of repeating them.
- The instructions used by all nine existing Stage 30 candidates are kept as `TRANSLATOR_BRIEF_v1.md`
  and `BASE_RULES_v1.md` in `work/translation/en/script/`. No translation was re-run; the review sheet
  is unchanged.

### 2026-10-02 — Sol 6.1, Astra 6, Luna 6 and Terra 5.6 comparison
- Completed independent 376-row translations for each requested model in 20 fresh contexts, with
  full first drafts, final raw slices and context/uncertainty reports preserved.
- All rows fit. Luna and Terra each retain one raw glossary mismatch in row 57 (Galfa/Gulfer),
  recorded in checks and explicitly labelled automated review notes; no cross-model corrections.
- Added four columns M:P to the existing review tab and 222 notes (220 translator entries plus two
  checks). Verified all 1,528 new translation cells and notes, and unchanged existing values,
  formatting, validation and cell notes. Nine candidates are now available for review.
- Added `tools/update_review_sheet.py` (preview and verified in-place posting),
  `tools/export_model_comparison.py` (nine-way exports and safe copies), and a comparison mode in
  `tools/check_translation.py` that retains content errors for review.
- Saved nine-way CSVs, a machine-readable summary and 48 new commit-safe copies. Documented the
  run in `docs/model_comparison_protocol.md` and `docs/stage30s_openai_comparison.md`. Build 0.1.0
  remains unchanged; Stage 30 has not been inserted.

### 2026-10-02 — Published Codex comparison to the review sheet
- Added `Codex (OpenAI session)` to the existing `Stage 30 Space` tab in place: 382 play-order
  occurrences covering all 376 translated rows. Appended 123 Codex notes to the existing notes tab.
- Verified every posted translation and note, and preserved all existing candidate/reviewer cell
  values, formatting, validation, and cell notes. Existing tabs and their IDs were retained.
- Used the handoff's service-account access because the Google Drive connector was signed out;
  credentials remain outside the project. Saved a pre-update snapshot and verification result in
  ignored `work/output/`. No ISO or release version changed.

### 2026-10-02 — Independent Codex Stage 30 translation
- Completed all 376 Stage 30 Space rows in five fresh translation contexts, preserving full drafts
  and final raw slices under the `codex` tag. Two rows required fit compression; 37 rows have flagged
  uncertainties.
- Added `tools/check_translation.py`: read-only preview, exact slice/completeness checks, supported
  characters, placeholders, glossary speaker names, known old spellings, and actual-kind text fit.
  All rows pass; the linked phrasing in rows 190/334 remains a human review item.
- Saved local five-candidate comparison and notes CSVs in `work/output/`, plus merged translation,
  detailed checks and 12 Codex-only commit-safe copies using the `strip_jp.py` cleaner.
- Documented methodology, layout limits and review items in `docs/stage30s_codex_review.md` and
  updated the handoff. Google Sheet and build 0.1.0 were not changed.

### 2026-10-02 — Stage 30 model comparison, handoff
- Stage 30 (Space route, 376 lines) translated independently by Opus 5.5, Sonnet 5.5, Haiku 4.5 and
  Fable 5.1; posted to the review Google Sheet (tab "Stage 30 Space") in play order with model names as
  columns. Not inserted into a build.
- New tools: `play_order.py` (play order and map events from script commands), `post_sheet.py`,
  `strip_jp.py` (commit-safe copies without Japanese script), `extract_iso.py`.
- `.gitignore` added: Japanese script stays local (rule recorded in AGENTS.md).
- `docs/HANDOFF.md` written for the next agent (adding OpenAI models to the comparison).

## 0.1.0 — 2026-10-02 (test build, `work/output/SRWMX_EN_0.1.0.iso`)

- **Variable-width font**: all 8 text sites in BOOT.BIN patched; Latin letters, digits and punctuation
  redrawn in the font atlas (`docs/vwf.md`). Japanese text is unchanged.
- **Prologue translated** (562 lines: opening scene, prologue map and after-scene, both routes) and
  inserted. Lines are wrapped by the build to 3 lines × 352 px.
- New tools: `vwf_patch.py`, `make_latin_font.py`, `textfit.py`, `export_rows.py`, `merge_slices.py`,
  `build_patch.py`, `ppsspp_dbg.py`, `boottest.py`, `post_sheet.py`.
- Verified in PPSSPP 1.20.4: boots, prologue dialogue shows in English (`work/ui/`).
- Known gaps: speaker names that come from name placeholders, the opening narration, menus and every
  other stage are still Japanese. The Latin font is a prototype (not yet an open-licensed font).
  Not tested on real hardware.

## Unreleased (pre-0.1.0)

### 2026-10-02 — Stage map
- Found the script index in BOOT.BIN (name table at 0x27D3A8, sector table at 0x27CA20). All 203 SRWL
  blocks in MAP_ADD.BIN now have their scene name and stage: 70 map scripts and 130 before/after scenes,
  verified against the akurasu MX Portable flow chart's victory conditions.
- New tool `tools/stage_map.py` writes `work/source/stage_map.json`. Documented in `docs/stage_map.md`.
- Found the hidden stage 「心」を蝕むもの (`s0570`) and a probably unused map (`s0760`, scenes `i076a/b`, `i063b`).

### 2026-10-02 — akurasu.net as main term source
- New rule (AGENTS.md): akurasu.net is the main source for terms.
- `tools/akurasu_terms.py` downloads the akurasu SRW MX pages (`work/glossary/akurasu/`) and parses them into
  `work/glossary/akurasu_terms.json` (485 terms). `work/glossary/akurasu_aliases.json` maps akurasu's Japanese typos to game keys.
- `tools/merge_glossary.py`: priority is now decision > akurasu > higher section > owner group. Added suffix
  matching (Lv/+/(n)), single-pass name rewriting, and quote-only rewriting for system terms. Generic characters
  sharing a name (公安 A/B, the ??? entries) are kept apart by their reading.
- Glossary: 564 entries now sourced from akurasu, plus 27 new system terms (parts). Library text rewritten in 240 fields.
  See `docs/glossary_decisions.md`.

### 2026-10-02 — Glossary + Library translation
- Decoded the STATIC2_ADD.BIN database (`docs/static2_format.md`): name table `Strg`, row table `Sent`,
  library indexes `Xunt`/`XPlt`, Unit/Pilot/Weapon records, and the links between them
  (Unit +84 / Pilot +166 = library entry).
- New tools: `tools/static2_extract.py` (exports names and library to `work/source/`),
  `tools/make_batches.py` (splits work by series), `tools/merge_glossary.py` (merges, reconciles names, checks).
- Glossary built by 4 research agents (one per series group A–D), merged into
  `work/glossary/glossary.json`: 22 series, 274 characters, 260 units, 382 weapons, 696 terms.
- Library translated to English: 248/248 robot entries and 264/264 character entries
  (`work/translation/en/library.json`). Not yet inserted into the game; rows still need re-wrapping
  once the font width is decided.
- Name conflicts between groups resolved (`docs/glossary_decisions.md`); 74 fields fixed by script.

### 2026-10-02 — ISO analysis
- Analysed the ISO for Japanese text; report in `docs/japanese_text_report.md`.
- Added tools: `tools/sjis_scan.py`, `tools/srwl_dump.py`, `tools/tx48_dump.py`.
