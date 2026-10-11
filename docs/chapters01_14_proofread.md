# Chapters 1–14 proofreading — 2026-10-09

Reviewed all 9,766 assembled entries across every applicable route against the
Japanese source and surrounding dialogue. Identical source/speaker/English
combinations were reviewed once: 7,745 distinct entries. Applied 91 distinct
corrections to 130 chapter-entry occurrences.

The standalone report is
[`chapters01_14_proofread.html`](../work/output/chapters01_14_proofread.html).
Every correction includes the previous English, replacement, speaker,
chapter/entry locations and an explanation. Search, chapter filters,
highlighted word differences and printing are available. The original
Japanese script is omitted. Customizable names are displayed in square
brackets while their runtime placeholders remain in the game inputs.

## Changes

- Corrected meaning where English confused the inventor with a material,
  alien acceptance with alien existence, internal batteries with an external
  supply, or an administrative deployment hold with physical freezing.
- Clarified ambiguous subjects and references; corrected awkward idioms,
  possessives and recurring insults while retaining character tone.
- Standardized the protagonists' established Ensign rank, Bright's Captain
  rank and Albero's squad-leader title, Commander. Albero's former military
  rank remains Major.
- Restored Dr. Umon where dialogue uses his title and surname; his full
  character name remains Genzo Umon. The existing contextual-name checker now
  permits this source-backed spoken form.
- Used Shorinji Kempo in Dendoh passages explicitly naming that martial art,
  consistent with the existing glossary distinction from G Gundam's Shaolin
  references.

## Source handling and checks

Corrections are stored in current Chapter 1–14 `*_full_merged.json` sources
and exact stage/entry context overrides. Original source, speaker, kind,
owner, uses and uncertainty fields are preserved. Context review fingerprints
and commit-safe `.en.json` copies are current. No historical draft or source
extraction was edited.

All 9,766 entries pass current full-source checks: dialogue wrapping, font
widths, allowed characters, placeholder counts, names and plain-text line
breaks. These use the project's current PSP font and conservative text limits;
they do not establish actual PS2 rendering.

All 109 final packets for Chapters 1–14 validate. Reassembling all 14 chapters
through the existing campaign assembler reproduces the reviewed English and
current context-review fingerprints exactly. The HTML report was inspected
at desktop and mobile widths; search, chapter filtering, empty states and
all 14 coverage rows work without JavaScript errors or mobile page overflow.

Reassembly validation also synchronized six final-packet rows with earlier
approved name, dialogue and objective corrections already present in the
reviewed full sources. These include George De Sand, Albero Est, Rockfell's
Taiha remark and the Zeorymer defeat condition. They retain prior fixes,
not additional proofreading changes. Older packet spelling failures outside
Chapters 1–14 are outside this review.

English decisions and checks:
`work/translation/en/script/chapters01_14_proofread.en.json` and
`work/output/chapters01_14_proofread_verification.json`. Local baselines and
original script stay under ignored `work/source/proofread_chapters01_14/`.

Source-only work. Existing PSP/PS2 ISO images have not been rebuilt; no release
or commit was created. In-game display and playthrough checks require a
subsequent build.
