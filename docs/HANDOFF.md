# Handoff — SRW MX Portable English translation

Written 2026-10-02 for whoever continues this work. The original comparison instructions below are
retained; the continuation status describes the latest work on disk.

## Continuation status — 2026-10-04

**Current build: 0.4.2.** Corrects the incomplete chapter-card coverage in 0.4.1:
all 67 scenario titles are now covered across 205 atlases (160 translated,
45 existing English copies preserved). Build is `work/output/SRWMX_EN_0.4.2.iso`.
Only `PACKMAPC2_ADD.BIN` changes; all other 31 ISO files match 0.4.1 exactly.
Reproduce with `tools/patch_chapter_cards.py work/output/SRWMX_EN_0.4.1.iso 0.4.2`.
Metadata: `work/translation/en/ui/all_chapter_cards.json`; report:
`work/output/chapter_cards_0.4.2_verification.json`. English preview sheets and
native test captures are in `work/ui/`. See `docs/chapter_cards.md` for layout,
palette handling and the scope of renderer probes. Story coverage is unchanged.
0.4.2 briefly became public before the user instructed that releases must wait
for explicit permission. It is now an unpublished GitHub draft and withdrawn
from the active Retro Trans catalog; 0.4.1 remains the public release. The tagged
source is `036a619be3c23b3abdfe8ee18182a47523ddeedf`, the verified full patch is
1,574,947 bytes and local assets are `work/output/release-v0.4.2/`. All eight
uploaded assets were downloaded and checked before withdrawal. A future
approved release should use a new version because the catalog withdrawal is
permanent. Do not publish any further release without the user's instruction.

Active task: translate dialogue after stage 30 through the ending, using
Sol 6.1 Medium sub-agents. Keep source Japanese local and preserve initial
drafts, context decisions, measured fit checks and every route/scene use.
Stages 31–35 are translated and reviewed: 3,548 fresh rows and 4,446 full rows.
Stage 36 translation is in progress. Queue:
`work/output/stages31_end_sol_medium_manifest.json`; review notes and tooling:
`docs/stages31_end_sol_medium.md`. These later translations are not yet in an ISO.

**Earlier released build: 0.4.1.** Published at
https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.1 in the now-public
repository. The 1,396,947-byte full xdelta patch is built against the original
Japanese ULJS-00041 ISO and reproduces the complete output SHA-256
`cf4af0243dadd37718866d7ee1a6f1f8d8974d5f55dd827644227f4e58d1c7d5`.
All uploaded assets were downloaded and verified before publication. Retro
Trans's scoped catalog refresh passed and the live catalog includes v0.4.1,
so Automatic mode can discover it. Release source tag pins commit
`db7bde279f8785a04e72bbc9617bd70cb73a1f03`; later documentation commits do not
change that tag. Final assets: `work/output/release-v0.4.1-optimized/`. The older
`release-v0.4.1/` directory contains an unpublished oversized encoder trial;
do not use it. `tools/build_release.py` now uses the whole source image as its
xdelta source window to handle ISO file relocation efficiently.

Incrementally patched the latest 0.4.0 ISO, which
already contains the prologue and stages 1–30 plus the 0.3.3 battle/UI/font work.
Added the requested Kaine closing line in its three `end_mes` uses and the stage
1 Super title-card lettering, **Visitors from the Beyond**. The title-card atlas
is in `PACKMAPC2_ADD.BIN`, pixel offset `0x14e1480`, not STATIC2's title strings.
It was located by matching the live GPU image against the original file. The
native patch edits only its first 40 rows. No emulator texture replacement.
Reproduction: `tools/patch_screenshot_text.py work/output/SRWMX_EN_0.4.0.iso 0.4.1`.
See `docs/chapter_cards.md` and the 0.4.1 verification report in `work/output/`.
The title was verified in-game with texture replacement disabled. Live pixels
match the patched atlas; screenshot: `work/ui/chapter_card_0.4.1.png`. All 30
other ISO files are byte-for-byte unchanged from 0.4.0. The Kaine line's three
ISO records and its two-line fit were checked; random save-message selection
has not been forced to that sketch for an in-game screenshot.

**Earlier font test build: 0.1.5.** The user requested Genei LateGo from
https://okoneya.jp/font/genei-latin.html. Latin glyphs now use the static Medium
font at 15 px without shadows. Japanese atlas cells remain unchanged. The
matching VWF table and all eight hooks are verified in the ISO; all 21,586
prologue/campaign rows pass font-fit checks. This test build contains the
prologue, as in 0.1.2. Build 0.1.4 additionally renders Latin from a native
4x atlas (60 px TTF rasterization / 72 px cells), at the same on-screen size.
The user explicitly rejected texture replacement: this is a native ISO patch,
with no texture pack. All renderer/width/glyph/height hooks and relocated code
were verified in an isolated PPSSPP instance, with texture replacement disabled.
Translated prologue dialogue displayed correctly. Screenshot evidence uses the
software renderer at PSP display resolution; 4x hardware screenshot, physical
PSP testing and campaign insertion remain pending.
Build 0.1.5 fixes cropped bottoms in g/j/p/q/y/comma: draw the complete 60 px
glyph on a 96 px temporary canvas before fitting it into the native atlas.
All other glyphs, widths and renderer code are unchanged. Complete FreeType
mask extents are checked to prevent recurrence. Packaged before/after preview:
`work/ui/font_descenders_0.1.5.png`.
The updated 0.1.5 atlas and relocated code were also matched in live PPSSPP;
a g renderer trace confirmed the larger atlas and unchanged 8 px advance.
Dialogue capture: `work/ui/font_native4x_0.1.5_dialogue.png`.
See `work/output/font_0.1.5_verification.json`, `docs/vwf.md`, and the accompanying
`work/output/SRWMX_EN_0.1.5_FONT_LICENSE.txt` for SIL OFL copyright/licence notices.

**Completed campaign:** numbered stages 1-30, including all listed routes,
translated with Sol 6.1 Medium using six distinct actual workers per stage in
waves. All 16,092 fresh rows across 241 packets validated; full stage assemblies
contain 21,024 stage-local unique rows with every original scene use retained.
Initial drafts, final packets, decision/fit reports and safe English-only copies
are preserved. Original Japanese remains in ignored local working files.

Coordinator reviewed all reused contexts and meaningful fresh flags against
original Japanese and actual scene neighbors. Source ambiguities, wordplay and
unverified licensed-label provenance remain explicit. Exact reviewed wording
is fingerprinted; all full checks pass with the current font width table.
Final audit: work/output/campaign_completion_audit.json.
Workflow and detailed stage reviews: docs/stages01_30_sol_medium.md.
Queue and actual agents: work/output/stages01_30_sol_medium_manifest.json.

Stage 30: 680 fresh rows, 9 packets, 839 full rows, 1,116 uses. Only 464/596 were
shortened after measured initial overflow; all full initial drafts retained.
Context fingerprint:
fbea801962973b4cd17812fd97c6f901e635e1f342aae9691302ff06db792430.
Stage 28 exact copies 502/689 were corrected using guarded contextual overrides;
earlier translation owners remain unchanged. Stage 29 full 487 retained after
independent review. Source-scoped Ryo/Dr. Plato corrections are documented;
original drafts and frozen speaker labels remain intact.

The campaign was subsequently inserted in 0.4.0 and retained in 0.4.1, as
recorded above and in the changelog. Complete gameplay validation remains
pending. Existing build/version records and previous comparison results below
are retained as historical context.

**Previous model-comparison work (2026-10-03):** fresh Sol 6.1 translations at Low, Medium,
High and XHigh are complete and posted to Translation Test 3, spreadsheet
`16nyBAPVH1OSQdYo8qMxxqmS5YtceGeK45DZt9prjuWQ`, original tab id 0 preserved.
Tags: `sol61low3`, `sol61med3`, `sol61high3`, `sol61xhigh3`; each has 376/376 rows,
zero final fit/character/placeholder/name findings. Five fresh contexts per effort;
model/effort verified in all 20 sessions. Header H:K contains candidates, L:M reviewer
fields; companion notes tab id 2000000103 contains 1,044 entries. All 1,528 posted
candidate occurrences and notes were verified, and exported layouts inspected.
Estimated Standard credits: Low 32.82, Medium 36.32, High 46.62, XHigh 70.78;
these exclude coordinator work and do not establish subscription charges.
Row 357 ASCII identifiers were independently checked to preserve exact game bytes;
Low/Medium report-only follow-up costs are included. See
`docs/stage30s_sol_effort_comparison.md` and the shared protocol
`docs/model_comparison_protocol_sol_effort.md`. Inputs/glossary and earlier sheets
are unchanged. Offline CSVs, drafts/reports, 48 safe copies and usage audits are saved.
Build stays 0.1.0; next is human wording selection/reconciliation, then an in-game build.

**Earlier completed work (2026-10-03):** user requested a fresh retranslation under the updated `BASE_RULES.md`, with Luna
excluded, into spreadsheet `18CicqkxXHZezKS8AsOL27dT8CBsfLrHRP8ArL61Fn5k` ("Translation Test 2",
`Stage 30 Space` id `1180054200`, notes id `2028606084`). Sol 6.1, Astra 6 and Terra 5.6 reruns are
complete under tags `sol61r2`, `astra6r2`, `terra56r2` (376/376 rows each, all fit). See
`docs/model_comparison_protocol_r2.md`. The new sheet already has `opus2`, `sonnet2`, `fable2`
translations under the same updated rules; keep these and the Prompt tab unchanged. Event-order
context is provided to every new translator, matching the Claude reruns. Luna is absent in this
destination and is excluded. The completed sheet has six candidates, with OpenAI columns K:M and
reviewer columns N:O. All 1,146 new translation cells and 719 new notes were read back and verified;
existing Claude/reviewer values, formatting and the entire Prompt tab were preserved. Raw spelling
findings are flagged separately: Sol/Terra 287 (Jamitov Hymem vs Akurasu Hymen), Terra 308
(Guiltor vs glossary Guiltorre). Shared glossary unchanged; no raw spelling reconciliation.
See `docs/stage30s_updated_rules_openai.md` for measurements, conditions and verification.
Six-way offline CSV/notes are `work/output/stage30s_comparison_updated_rules*.csv`, with metrics,
summary, preserved full drafts and 36 new safe JSON copies. Exact instructions are saved as
`BASE_RULES_r2.md` / `TRANSLATOR_BRIEF_r2.md` in the script folder. Build 0.1.0 is unchanged.
Token usage and model/effort settings have now been recovered from session metadata; see
`docs/stage30s_translator_usage.md`. These estimates exclude coordinator work and do not establish
actual subscription charges. Next: human wording selection and reconciliation, then a separately
versioned in-game build.
The earlier comparison below is retained as a historical record.

### Earlier comparison under original rules

The requested **Sol 6.1, Astra 6, Luna 6 and Terra 5.6** candidates are complete and posted. Each
translated all 376 rows in five fresh contexts. All rows fit; Luna and Terra each have one raw
Galfa/Gulfer spelling mismatch at id 57, preserved for comparison and flagged separately in the notes
tab. See `docs/stage30s_openai_comparison.md` for requested model ids, metrics and verification.

The live sheet now contains **nine candidates**. New columns M:P hold these four models; reviewer
columns moved to Q:R. All 1,528 new translation cells and 222 new notes were verified, along with
unchanged existing cell values, formats, validation and cell notes. Existing tabs and ids are intact.
Local exports are `work/output/stage30s_comparison_openai_models.csv` and its `_notes.csv` companion.
Each new tag has five full drafts, five raw slices, reports, merged/check files and `.en.json` copies.
Luna/Terra merged files are marked `comparison_only` due to the known spelling error; all raw
candidates need selection and semantic reconciliation before production use.

The preceding single-session candidate remains available as a separate baseline:

The `codex` OpenAI-session candidate is complete: five independently translated slices, 376/376 rows,
no fit/structural errors, 37 uncertainty rows. Full first drafts and final slices are preserved, with
English-only `.en.json` copies. See `docs/stage30s_codex_review.md` for methodology and review details.

New local exports: `work/output/stage30s_comparison_codex.csv` and
`work/output/stage30s_comparison_codex_notes.csv`. They contain all five candidates in play order.
The [online sheet](https://docs.google.com/spreadsheets/d/1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY#gid=886392675)
initially gained the five candidate columns. At the user's request, the Codex column was inserted before the
reviewer columns, and 123 Codex notes were appended to the existing notes tab. All 382 posted
occurrences and the notes were verified, along with unchanged existing cell values, formatting,
validation and cell notes. Reviewer selections/comments were empty at update time. Existing sheet
IDs were retained; a pre-update snapshot and result are in ignored `work/output/`.
Build 0.1.0 is unchanged; Stage 30 remains uninserted.

Next: review the new candidate, reconcile the recalled wording in rows 190/334 and unresolved terms,
then select production text before building. All requested sheet updates are complete. The older
Codex session candidate is identified by the 2026-10-03 session metadata audit as gpt-6.1-sol at
High effort. Sol overrides used Low; Astra, Luna and Terra used Medium. See
`docs/stage30s_translator_usage.md` for all recovered counts and Standard credit estimates. Use the newer `tools/update_review_sheet.py` for in-place additions rather than
recreating existing tabs.

## 1. What this project is

An English fan translation of *Super Robot Taisen MX Portable* (PSP, ULJS00041). The user owns the ISO
(`Super Robot Taisen MX Portable (Japan).iso` in the project root). Project root: `E:\Projects\SRW MX`.

Read these first, in this order. They are binding:

1. `AGENTS.md` — folder layout, versioning (0.x.y), "always write a change log", and the REMEMBER list:
   - releases must work with Retro Trans Tools;
   - akurasu.net is the main source for terms;
   - **Japanese script text must never be committed to git** (local working files are fine).
2. `BASE_RULES.md` — how to translate and proofread (80-row slices, read neighbouring rows, restore
   dropped subjects, never infer gender from a name, report uncertainty, dry-run scripts).
3. `docs/CHANGELOG.md` — what was done, newest first.

## 2. State of the work

| Area | State |
|---|---|
| ISO analysis | Done. `docs/japanese_text_report.md`, `docs/static2_format.md`, `docs/stage_map.md` |
| Glossary | Done, akurasu-first. `work/glossary/glossary.json` (22 series, 279 characters, 260 units, 382 weapons, 723 terms). Rules in `docs/glossary_decisions.md` |
| Library (encyclopedia) | Translated (248 robot + 264 character entries), not yet inserted into the game |
| Variable-width font | Done and working in PPSSPP. `docs/vwf.md` |
| Prologue script | Translated (562 lines) and inserted. Build `work/output/SRWMX_EN_0.1.0.iso` |
| Stage 30, Space route | Original-rules sheet: 9 historical candidates. Updated-rules "Translation Test 2": 6 candidates (Opus, Sonnet, Fable, Sol 6.1, Astra 6, Terra 5.6), Luna excluded. Local comparisons saved. **Not inserted into a build** |
| Everything else | Japanese: other stages, menus, opening narration, battle quotes, default hero names |

Build 0.1.0 was booted in PPSSPP 1.20.4 and played into the prologue map's opening dialogue. Nothing
past that point has been seen on screen. Not tested on real hardware.

## 3. The task being handed over: add OpenAI models to the stage 30 comparison

The human reviewer compares translations side by side in this sheet:
`https://docs.google.com/spreadsheets/d/1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY` (tab "Stage 30 Space").
Columns today: `#`, Part, ID, Kind, Speaker (JP), Japanese, Speaker (EN), Opus 5.5, Sonnet 5.5,
Haiku 4.5, Fable 5.1, Best (model), Reviewer comment.

To add a model, produce its translation files and re-post. Keep the conditions identical to what the
Claude models had, or the comparison is not fair.

### 3.1 Input

`work/translation/en/script/stage30s.json` → `rows` (376 rows, `id` 0–375, in play order).
Fields: `id`, `jp` (raw line), `kind` (`dialogue` / `thought` / `plain`), `speaker_jp`, `speaker_en`
(pre-filled from the glossary), `body_jp` (the text to translate; `@` = line break in the Japanese box),
`uses` (scene:index).

If the file is missing (it is git-ignored), regenerate it — this reproduces it exactly:

```bash
python tools/extract_iso.py "Super Robot Taisen MX Portable (Japan).iso"
```
```bash
python tools/export_rows.py work/build/iso/MAP_ADD.BIN work/translation/en/script/stage30s.json i06s1b s06s10 i06s1a --exclude work/translation/en/script/prologue_merged.json
```

### 3.2 Instructions each translator received

The instructions every comparison candidate so far was given are frozen in
`work/translation/en/script/`: `TRANSLATOR_BRIEF_v1.md` and `BASE_RULES_v1.md`. To add another candidate
to the **existing** comparison, give it those two v1 files unchanged.
The live `BASE_RULES.md` has since gained five rules adapted from LinguaGacha's prompt template (one row
in / one row out, spoken register, a two-step context/decisions check per row, translate what the player
reads and leave what the game reads, no softening). Use the live files for new translation work.
Output produced under the live rules is not comparable with the v1 candidates unless those are re-run.
Each Claude translator got one slice and this task text (only the model tag and slice numbers differ):

> Translate a slice of the Super Robot Wars MX Portable script (stage 30, Space route: "Break through the
> Falcon") into English. Read TRANSLATOR_BRIEF.md and BASE_RULES.md (both binding). Input: stage30s.json.
> YOUR SLICE: rows with `id` X to Y inclusive. Read neighbouring rows for context as the brief requires.
> For every row write the English `en` (and `speaker_en` if empty). Check EVERY row with
> `python tools/textfit.py "<speaker_en>" "<en>"`; it must print FITS (3 lines x 352 px). Glossary:
> work/glossary/glossary.json; fixed spellings: work/glossary/do_not_touch.json. Write the result to
> stage30s_<model>_slice_<N>.json. Do not read any other stage30s_*_slice_*.json file: other translators
> are working on the same rows independently and the results will be compared. Final message: rows examined
> vs rows in slice, rows that needed compression, rows that do not fit, and your uncertainties.

Slices: 0 = ids 0–79, 1 = 80–159, 2 = 160–239, 3 = 240–319, 4 = 320–375. One fresh context per slice.

Conditions to keep equal:
- The translators could run tools (they checked fit themselves and could read the glossary and the
  finished prologue). If the OpenAI models are called through a plain API without tools, say so in the
  results, and run the fit check for them afterwards (§3.4) — expect more overflowing rows.
- They saw only the Japanese of rows outside their slice, never another translator's English.
- The input did **not** mark event boundaries on the battle map. `stage30s_order.json` now has them
  (see §5). Do not give it to the new models for this comparison; do use it for real translation work.

### 3.3 Output format

One file per slice: `work/translation/en/script/stage30s_<model>_slice_<N>.json`, UTF-8:

```json
{"slice": 0, "rows": [{"id": 0, "speaker_en": "Vega", "en": "English body only", "notes": "", "uncertain": ["..."]}]}
```

- `en` is the body only: no speaker name, no brackets. Dialogue/thought rows: one continuous text, no
  `@` (the build wraps). Plain rows: same number of `@`-separated lines as the Japanese.
- ASCII only: letters, digits, space and `, . : ; ? ! / ~ ' " ( ) [ ] + - = $ % & *`. `...` for ellipses.
- Keep placeholders verbatim: `#男愛称` `#女愛称` `#男姓名` `#女姓名` `#部隊名` `#機体名`.
- `<model>` is a short tag without spaces or `=` (e.g. `gpt5`).

### 3.4 Check, then post

Limit of the dialogue box: **3 lines × 352 px**, measured in the game. About 47 characters per line
on average; letters are 4–12 px wide, so use the tool rather than counting:

```bash
python tools/textfit.py "Ruri" "Your English line here."
```
```bash
python tools/textfit.py --check work/translation/en/script/stage30s_gpt5_slice_0.json
```

`--check` measures every row as a dialogue line, so it is right for dialogue and thought rows but not
for the two plain rows (ids 151, 152: check each `@`-separated line against 352 px yourself). A fuller
check is described in §6 "Checks". Then re-post with the new model appended (names after `=` become
the column headers; reviewer input already in the sheet is carried over by line ID):

```bash
python tools/post_sheet.py "C:\Users\Binh\Downloads\windy-renderer-507117-d4-2bb59e962d84.json" 1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY work/translation/en/script/stage30s "Stage 30 Space" "opus=Opus 5.5" "sonnet=Sonnet 5.5" "haiku=Haiku 4.5" "fable=Fable 5.1" "gpt5=GPT-5"
```

The sheet is shared with the service account `claude@windy-renderer-507117-d4.iam.gserviceaccount.com`
(Editor). The key file stays in the user's Downloads folder; do not copy it into the project.
Posting replaces the tabs "Stage 30 Space" and "Stage 30 Space notes" and touches nothing else.
Offline alternative: replace the first two arguments with `csv work/output/stage30s_comparison.csv`.

Post each model's **raw** output. Do not fix its spelling errors first; the reviewer should see them.

### 3.5 What the Claude runs showed (baseline for comparison)

All four translated 376/376 rows and no dialogue line overflowed (measured independently).

| | Opus 5.5 | Sonnet 5.5 | Haiku 4.5 | Fable 5.1 |
|---|---|---|---|---|
| Wrong glossary spellings | 0 | 0 | 9 ("Lagou" ×8, "Galfa" ×1) | 0 |
| Problems in the 2 condition rows (ids 151, 152) | 0 | 0 | 3 | 0 |
| Rows with a flagged uncertainty | 68 | 54 | 0 | 75 |
| Messages using all 3 lines | 47 | 35 | 26 | 70 |
| Total English characters | 21,757 | 20,615 | 19,138 | 22,716 |

The Claude runs used the Claude Code default effort for each model; effort was not varied.
The reviewer's picks ("Best" column) were not in yet at handoff.

## 4. How the game stores what we translate

- **Scripts**: `MAP_ADD.BIN`, 203 `SRWL` blocks from sector 0x579C. Each = header, commands (0x30 bytes
  each), then a pointer table and Shift-JIS strings. Names like `s06s10` (map) / `i06s1b` (scene before) /
  `i06s1a` (scene after) come from tables in `BOOT.BIN`. Full mapping: `docs/stage_map.md`.
- **Play order**: opcode 0x0B shows a message (arg 2 = string index), 0x0C shows two at once, 0x58 shows a
  victory/defeat condition, 0x6D plays a scene, 0x7E/0x7F delimit map events. `tools/play_order.py`.
- **Font and text drawing**: `docs/vwf.md`. English is stored as full-width Shift-JIS (2 bytes per
  letter); the patch gives those glyphs their own widths.
- **Names, library, help text**: `STATIC2_ADD.BIN`, `docs/static2_format.md`.

## 5. Tools (all in `tools/`, Python 3.8)

| Tool | Purpose |
|---|---|
| `extract_iso.py` | Pull BOOT / MAP_ADD / STATIC2_ADD out of the ISO into `work/build/iso/` |
| `static2_extract.py`, `stage_map.py`, `make_batches.py` | Rebuild `work/source/` (names, library, stage map) |
| `akurasu_terms.py`, `merge_glossary.py` | Refresh akurasu terms; merge glossaries and fix names (`--apply`) |
| `export_rows.py` | Export a scene's lines for translation (`--exclude` skips lines already done) |
| `play_order.py` | Play order + event boundaries of a stage → `<scene>_order.json` |
| `textfit.py` | Encode English and measure it against the dialogue box |
| `merge_slices.py` | Merge slice files into `<scene>_merged.json` and check them |
| `post_sheet.py` | Post a multi-model comparison to the Google Sheet (or CSV) |
| `update_review_sheet.py` | Preview and append new candidates in place; preserve and verify existing reviewer/candidate cells |
| `check_translation.py`, `export_model_comparison.py` | Check candidate slices and preserve raw review errors; export nine-way comparison and safe copies |
| `build_patch.py` | Build the patched ISO (`work/output/SRWMX_EN_<version>.iso`) |
| `vwf_patch.py`, `make_latin_font.py`, `native_font4x.py` | VWF, original-size Latin atlas and native 4x font patch |
| `ppsspp_dbg.py`, `nav.py`, `boottest.py` | Drive PPSSPP through its debugger; boot-test an ISO |
| `strip_jp.py` | Write `*.en.json` copies without Japanese script — run before any git commit |

Build command used for 0.1.0:

```bash
python tools/build_patch.py "Super Robot Taisen MX Portable (Japan).iso" 0.1.0 --scenes-file work/translation/en/script/prologue_merged.json
```

## 6. Things that will bite you

- **Environment**: Windows, Git Bash, Python 3.8 **32-bit**. Set `PYTHONIOENCODING=utf-8` or printing
  Japanese crashes. In bash heredocs, backslashes inside Python source get mangled (`'\n'`, `'\\'`,
  `'\0'`); write scripts to files or avoid backslash literals. Google libraries print version
  warnings on every run; they are harmless.
- **`textfit.py` needs `work/build/STATIC2_ADD.BIN`** (the atlas with Latin glyphs). If it is missing,
  run `extract_iso.py`, then
  `python tools/make_latin_font.py work/build/iso/STATIC2_ADD.BIN work/build/STATIC2_ADD.BIN`.
- **Do not put code at 0xE4EAC in BOOT.BIN.** It looks unused but is called once at boot from code in
  `.data`. The patch lives at 0x250944. BOOT.BIN is relocatable: any patched instruction that holds an
  address needs a relocation entry (`vwf_patch.patch_boot` handles this).
- **Script size cap is ours, not the game's.** `build_patch.py` refuses a scene script above 0x25000
  bytes (151,552), the largest original. The game loads scripts into a memory pool of unknown size.
  The maps of stages 8, 49 and 54 will exceed the cap once translated. Either read the pool's capacity
  with the debugger and raise the cap, or add a 1-byte encoding for Latin text.
- **The build only rewrites scenes listed in the rows' `uses`.** Shared defeat lines are therefore
  translated only inside the scenes that have been built, not game-wide.
- **PPSSPP**: the debugger needs `RemoteDebuggerOnStartup = True`, `RemoteDebuggerLocal = True`,
  `RemoteISOPort = 45373` in the user's `ppsspp.ini`. The user approved this once; a backup is at
  `work/ppsspp.ini.backup` and the settings were restored afterwards. Ask before changing them again.
  The debugger's screenshot call fails on this machine; `ppsspp_dbg.Dbg.grab_window()` captures the
  window instead. Use `Dbg.tap()` for input; on the favourite-series screen Circle selects and the
  carousel then rotates by itself.
- **Checks**: the per-model check used for the table in §3.5 was a one-off script (completeness, fit,
  allowed characters, placeholder counts, old spellings from `work/glossary/name_fixes.json`). Its
  result is in `work/translation/en/script/stage30s_checks.json`. `merge_slices.py` has the same logic
  for a single set of slices.
- **Not a git repository yet.** `.gitignore` is in place. Run `tools/strip_jp.py` before the first commit.

## 7. Open items

Translation quality:
- Glossary gaps hit by several translators: Operation Moonraker, "junior science trainee" (Hokuto's
  and Ginga's cover story), Zeon Zum Deikun, Jamitov Hymem, Core 258, Little Baam, Ereism.
- Glossary inconsistencies: the short form of the Gulfer Emperor still says "Galfa Emperor"; one
  character entry says "Omzack of the Thunder" (the unit is "Omzack of the Lightning").
- Row 334 quotes row 190; the two must match in the final text.
- Spirit Command names: akurasu's literal names are in use (Hot Blood, Sure Hit…); the user has not
  yet said whether to switch to the official English names (Valor, Strike…).
- "Shuffle Alliance" is used (akurasu); the official SRW T English says "Shuffle Union".

Technical:
- Measure the victory/defeat condition window; the Japanese there is wider than 352 px.
- Default hero names shown through placeholders, the opening narration and all menus are still
  Japanese (they live in BOOT.BIN / STATIC2_ADD.BIN).
- The current Latin font is Genei LateGo v2 Medium (SIL OFL 1.1). Keep the
  complete source copyright/licence notice alongside redistribution. See `docs/vwf.md`.
- Insert the library translation (needs re-wrapping to its own window, not yet measured).
- Scenes `s0760`, `i076a/b`, `i063b` look unused; confirm in the emulator before skipping them.
- Check Retro Trans Tools' patch format before the first release.
- Battle quotes (`BATTLE2.BIN`) record layout is not decoded.

Waiting on the user:
- Reviewer's picks in the sheet, then tally per model and per kind of line.
- Whether to read the script pool capacity with the debugger now.
