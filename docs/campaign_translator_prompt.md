# Sol 6.1 Medium campaign translator instructions

Work in `E:/Projects/SRW MX`. Your task message supplies stage, slice, and exact
source ID interval (at most 80 consecutive rows). Translate only that interval.

Read `AGENTS.md`, `work/translation/en/script/BASE_RULES_campaign.md`, and
`TRANSLATOR_BRIEF_campaign.md` in the same folder. They are binding. Read
`work/glossary/glossary.json`, `campaign_terms.json`, `do_not_touch.json` and
`name_fixes.json`. Report missing terminology to root for centralized sourcing;
continue other rows. Never guess gender from a name.

Source nicknames remain distinct from full names: リョウ is Ryo; 竜馬 is Ryoma.
Body ハーリー is Harry, while the prefilled speaker stays Hari and the full
マキビ・ハリ remains Hari Makibi. Both nicknames follow sourced glossary entries.

The source is `work/translation/en/script/stageNN_campaign.json`. Full original
Japanese context is `stageNN_campaign_all_source.json`. To locate your rows,
match BOTH `translation_owner.source` to your source path and `translation_owner.id`
to your assigned ID; owner IDs repeat across files. Read original neighbors and
route `stageNN_campaign_*_order.json` files to settle speaker/listener, tone,
callbacks, event boundaries and referents before wording. Deduplication removes
previously translated lines from the fresh source, never from full context.
Do not copy previous English candidates. Keep hidden speaker labels hidden.

One source row becomes one output row, body only, without speaker or Japanese
wrappers. Preserve prefilled speakers. Use natural spoken character voice,
restore context-settled subject/action, and preserve request direction. Keep
ASCII punctuation and exact runtime placeholders. Dialogue/thought text has no
manual `@`; plain rows keep the same `@` count as source. Preserve actual kind:
thought fitting uses `thought=True`.

First save a complete full initial draft, before measuring or shortening.
Filename: `stageNN_campaign_sol61medium_draft_S.json` in the source folder.
Then measure EVERY row with `tools/textfit.py` API:
`fit_dialogue(speaker, en, kind == 'thought')`; plain rows use `px` on each
`@` segment, with provisional 352 px limit. Only measured overflow may be
compressed. Keep subject, verb and ending; flag any unresolved overflow.
Fix meaning yourself before applying source-backed name corrections. Retain
initial drafts even when final meaning corrections are necessary.

Final: `stageNN_campaign_sol61medium_slice_S.json`, schema
`{"slice": S, "rows": [{"id": ID, "speaker_en": "...", "en": "...", "notes": "...", "uncertain": []}]}`.
Every row must have all five fields. Report:
`stageNN_campaign_sol61medium_report_S.md`, with assigned and examined IDs/count,
context decisions, uncertainty, per-row fit widths and every compression or
retained omission/fragment. Do not claim a new build version for a translation
packet. Explain meaningful draft-to-final changes.

Do not edit source/rules/glossary, another worker's outputs, ISO files or Sheets.
No commit or publication. Save the three assigned outputs and report completion
to root. A later assignment is separate and must preserve earlier outputs.
