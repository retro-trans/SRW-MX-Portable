# Remaining dialogue campaign

Started 2026-10-04. The user requested dialogue through the ending using
Sol 6.1 Medium sub-agents. No GitHub release is authorized by this task.

Sources and route context are extracted from the original Japanese ISO into
ignored local working files. Stages 1–30 retain their completed translations.
The queue is `work/output/stages31_end_sol_medium_manifest.json` and uses
235 separate packets, at most 80 rows each, for 16,661 fresh rows. Six actual
workers share each group in waves of at most three simultaneous translators.
These are initial preparation counts, not completed translation counts.

Stages 31–54 include every mapped route. Internal group 55 is the final stage
with its before/map/after scenes (including the ending); group 56 is the hidden
stage. Group 57 covers unreferenced old scenes and group 58 covers save/closing
messages. These internal group numbers are not new playable stage numbers.

Completed prologue and stages 1–30 assemblies seed exact-source reuse. Reused
English must be reviewed in every new scene context; an exact Japanese match
does not by itself establish that the referent or English subject still fits.
Every original scene/string use is retained in final assemblies.

The current rules and translator brief are frozen as `BASE_RULES_remaining.md`
and `TRANSLATOR_BRIEF_remaining.md`. Each packet retains a full initial draft,
final translation, context/decision report and actual font measurements.
Compression is allowed only after measured overflow. Nonobvious referents,
retained omissions, terminology gaps and uncertain provenance remain explicit.

Preparation preview: `python tools/prepare_remaining_campaign.py`.
Writing requires `--write` and refuses existing campaign source/context files.
Validation: `python tools/campaign_status.py --manifest
work/output/stages31_end_sol_medium_manifest.json`; add `--write` only after
inspecting the preview. This does not insert translations into the game.

## Progress

Stage 31 is complete: 726 fresh rows in ten packets, 899 full rows and 1,225
original scene uses. Six distinct Sol 6.1 Medium translators produced preserved
drafts and measured final translations. All initial drafts fit without shortening.
Coordinator reviewed all 45 fresh uncertainty rows, all reused scene contexts,
both route orders and defeat-line registrations. Predict uses its canonical
skill name, and the recurring improvised operation title is consistent.
Original wordplay, deliberate omissions and uncertain licensed provenance remain
documented. Exact review fingerprint:
`a18375284394721c0556e44bf2b936e0beffb477c6738fdd336c35a69fe44e8a`.

Stage 32 is complete: 578 fresh rows in eight packets and 753 full rows. All
initial drafts fit without compression. Coordinator reviewed all 26 fresh flags,
all 32 non-template reused rows in every scene and 143 defeat-template rows
across 410 registered uses. Symbolic bird-man references, unfinished warnings,
Buddhist invocations and provisional boundary-quake/calendar terminology retain
their documented uncertainty. Chicken and Mandala puns are localized with notes.
Exact review fingerprint:
`7bce06e4d52b61270584d0da13bb0f050f44446488cf1b9a3ddf7f77410b8755`.

Stage 33 has begun. Full-game local insertion and playtesting remain pending.
No further GitHub release is authorized.
