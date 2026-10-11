# Campaign proofreading through the end — 2026-10-09

Completed the continuation from Chapter 31 through the end, including both
routes, alternate battles, the final battle and epilogue, hidden-stage text,
unused scenes and closing/save messages. Internal source groups 55–58 are
labelled Finale, Hidden stage, Unused scenes and Closing/save messages in
the report, rather than presented as four more numbered chapters.

Compared **17,135 distinct entries** with the original Japanese in scene
context, covering **21,257 assembled entries** in the remaining 28 source
groups. Exact repeated occurrences share a review; previously reviewed
generic defeat lines retain their approved wording.

Applied **633 new corrections at 658 entry occurrences**. These include
meaning and subject corrections, tactical conditions, idioms, rank/title
consistency, removal of unspoken explanations, thought formatting, natural
English and spacing after ellipses. Deliberate interruptions, dialect, jokes
and plot-specific claims remain intact. The established naval Captain rank
for Bright and Yurika is retained.

The cumulative report explains **804 corrections at 869 occurrences**:
[`chapters01_end_proofread.html`](../work/output/chapters01_end_proofread.html).
Coverage from Chapter 1 through the end is **42,281 assembled entries** and
**33,070 distinct entries**. Every correction has before/after wording,
an explanation and exact locations, with highlighted differences, search,
chapter/scene filters and printing. Earlier reports remain available.

## Examples of corrections

- Clarified that Vector Zero and the Gulfer Emperor must both be defeated
  during the same turn, without suggesting that the entire battle must be
  completed in one turn. Preserved the original objective line counts and
  measured the shortened wording against the font limit.
- Corrected tactical subjects, who protects whom, and statements about
  memory, identity and the TE/AI1 systems where the English changed the
  source meaning.
- Distinguished taking responsibility for defeat from literal ritual
  sacrifice; translated idiomatic threats in their scene context.
- Removed explanatory Iron Dragon and UESF glosses that were inserted into
  spoken dialogue. Retained the explicitly stated Tekkoryu/Hau Dragon
  correction where the characters make it themselves.
- Repaired an intentionally mangled proverb as “moths to a frame” followed
  by “moths to a flame,” retaining the forced joke and the responding criticism.
- Corrected Boson terminology and formatted thought dialogue with one
  space before the opening parenthesis. Unused plain-text thought blocks
  retain their original number of lines.

## Validation and limitations

All **21,257 remaining assembled entries** pass the existing checks for
font width, dialogue length, supported characters, runtime placeholders,
names and plain-text line counts. The measurements use the current PSP
font and conservative limits; they do not establish native PS2 rendering.

Original Japanese text, IDs, speakers, scene uses, kinds, translation
owners and uncertainty fields are preserved. Current full campaign merges,
scoped context overrides, review fingerprints and commit-safe English
copies contain the corrections. Historical drafts remain unchanged.

All **235 final packets** covering **16,661 fresh rows** validate. Twelve
older final-packet rows were synchronized with previously approved George
De Sand, Albero Est and Black Selena spellings. These retain earlier fixes
and are listed separately from the new proofreading corrections.

A read-only reassembly of all 28 remaining source groups reproduces every
reviewed English entry and all context-review fingerprints exactly. The
remaining-campaign manifest's separate review registry is also updated;
future assembly must apply the scoped context overrides.

The HTML passes desktop/mobile checks for search, all 58 chapter/scene
filters, reset, empty states and printing. It has no JavaScript errors or
horizontal overflow at 390px width. Desktop and mobile views were inspected.

Existing source uncertainty annotations are retained. For example, the
original source labels one Chapter 50 line as Michiru despite its Urube-like
revival narrative; this attribution anomaly remains explicitly flagged.
The review does not invent a replacement speaker.

## Records and reproduction

- New decisions: `work/translation/en/script/chapters31_58_proofread.en.json`.
- Cumulative decisions: `work/translation/en/script/chapters01_end_proofread.en.json`.
- Checks: `work/output/chapters31_58_proofread_verification.json`.
- Regenerate the cumulative HTML with
  `py -3.8-32 tools/report_cumulative_proofread.py --through-end`.
- Original-script baselines, review checkpoints, read-only reassembly
  records and report screenshots are kept in the ignored local directory
  `work/source/proofread_chapters31_58/`.

Source-only work. Existing PSP/PS2 ISOs do not contain these new corrections.
No ISO, patch, build version, commit or release was created. A subsequent
build is required for native rendering and playthrough verification.
