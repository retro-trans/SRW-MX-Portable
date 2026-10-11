# Chapters 15–30 proofreading — 2026-10-09

Completed all applicable routes through Chapter 30. This continuation covers
11,258 assembled entries: 8,140 newly reviewed distinct source/speaker/English
combinations, 70 repeated occurrences of those entries, and 3,048 occurrences
whose exact source, speaker and English already matched completed reviews.
Every new entry was compared with the Japanese source in scene context.

Applied **58 new distinct corrections at 59 entry occurrences**. The earlier
22 corrections to Chapter 15's Super route are retained and included in the
cumulative report, rather than counted again as new edits.

The cumulative report is
[`chapters01_30_proofread.html`](../work/output/chapters01_30_proofread.html).
It explains **171 distinct corrections at 211 occurrences** across Chapters
1–30, with before/after wording, reasons, speakers, locations, highlighted
differences, search, chapter filters and printing. Coverage totals are
21,024 assembled entries and 16,403 distinct entries across the full range.
The original Chapters 1–14 report remains available.

## Main corrections

- Corrected negative-question replies that incorrectly affirmed the question,
  mistaken agents or subjects in tactical dialogue, and idioms translated too
  literally.
- Clarified the TE system, AI1's compatibility, Miku's restoration of the
  Dimensional Coupler System, and Saiga's claim that an alliance would be
  unbeatable.
- Corrected a destination objective from all allied units to an allied unit.
  Checked the changing victory and defeat conditions against each source phase.
- Retained Captain Bright, Lieutenant Commander Ruri and Commander Albero
  where their established project titles apply. Used Folia Est consistently
  with his father's user-approved surname; documented the spelling decision.
- Removed unspoken parenthetical explanations for Tekkoryu, restored the
  Tekkoryu/Hau Dragon connection where explicitly stated, and used Jovian
  Federation instead of the untranslated Mokuren label.
- Used Shorinji Kempo for Ginga's martial art and improved awkward English
  while preserving interruptions, jokes, dialect and deliberate malapropisms.

## Validation

All 11,258 Chapter 15–30 entries pass the existing checks for dialogue fit,
font widths, supported characters, runtime placeholders, names and plain-text
line breaks. These checks use the current PSP font and conservative limits;
they do not establish native PS2 rendering.

Original Japanese text, IDs, scene uses, translation owners, speakers, kinds
and uncertainty fields are unchanged. Only recorded English corrections and
their explanatory notes changed. Current full merges, scoped context
overrides, review fingerprints and commit-safe English copies are updated.
Unreviewed historical drafts were preserved.

All **241 current final packets** for Chapters 1–30 validate. A read-only
reassembly of all 30 chapters reproduces their reviewed English and review
fingerprints exactly. Reassembly also required synchronizing 12 older packet
rows with earlier approved George De Sand and Albero Est spellings. These
retain previous corrections, rather than add 12 new proofreading edits.

The cumulative HTML was visually inspected at desktop and mobile sizes.
Search, all 30 chapter filters, reset, empty states and coverage rows pass;
there are no JavaScript errors or horizontal overflow at 390px width.

## Records

- New corrections: `work/translation/en/script/chapters15_30_proofread.en.json`.
- Cumulative corrections: `work/translation/en/script/chapters01_30_proofread.en.json`.
- Validation: `work/output/chapters15_30_proofread_verification.json`.
- Cumulative report generator: `tools/report_cumulative_proofread.py`.
- Original-script baselines and review checkpoints: ignored local directory
  `work/source/proofread_chapters15_30/`.

Source-only work. Existing PSP/PS2 ISO images do not contain these new changes.
No ISO, patch, build version, commit or release was created. A subsequent build
is required for native rendering and playthrough verification.
