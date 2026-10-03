# Remaining dialogue campaign

Started 2026-10-04. The user requested dialogue through the ending using
Sol 6.1 Medium sub-agents. No GitHub release is authorized by this task.

Sources and route context are extracted from the original Japanese ISO into
ignored local working files. Stages 1–30 retain their completed translations.
The queue is `work/output/stages31_end_sol_medium_manifest.json` and uses
235 separate packets, at most 80 rows each, for 16,661 fresh rows. Six actual
workers share each group in waves of at most three simultaneous translators.
These are initial preparation counts, not completed translation counts.

Source-queue coverage audit: all 203 original scene blocks and 51,366 readable
scene/string uses are represented by the prologue and all stage/group sources;
no readable use is omitted. Local report:
`work/output/full_dialogue_queue_coverage.json`. This checks queue coverage,
not completed translation or insertion into the game.

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
Compression is allowed only after measured overflow. Dialogue and thoughts allow
three actual wrapped lines regardless of the source Japanese line count; only
plain text preserves the original fixed line count. Nonobvious referents,
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
`06b43971793b807040780329c4c1fe5c0fff8b4b995d1faece37c6bb2743a486`.

Stage 33 is complete: 1,070 fresh rows in fourteen packets, 1,264 full rows and
1,593 original scene uses. All 26 fresh flagged rows and all 194 reused rows
were reviewed in their route contexts. The 143 generic defeat rows have 410
registered uses plus one ordinary Koji silence, checked separately. The other
51 reused rows include repeated family scenes and Data Weapon silences.
Three measured draft overflows were shortened without losing meaning. One
proven source address typo is corrected in final only, as documented in
`docs/glossary_decisions.md`; deliberate contract and mask fragments remain.
Exact review fingerprint:
`6983857f91839c2af139cdb0cee98b114453f7996e9b692b40551fa1c336a077`.

Stage 34 is complete: 552 fresh rows in seven packets and 729 full rows. All
11 fresh flags and every use of the 34 non-template reused rows were reviewed.
The remaining 143 defeat-template rows have 410 registered uses. Two condition
lines required measured shortening; both retain all defeat alternatives. Asona
Island remains a provisional reading, and source jokes keep their documented
provenance limits. Buddhist cultural terms are sourced without adding a sect.
Exact review fingerprint:
`3822fb8b42430653a043d3ae382ef485c20370c58fa0a40509eae8dcb5414755`.

Stage 35 is complete: 622 fresh rows in eight packets, 801 full rows and 921
original uses. All initial and final rows fit without compression. All 25 fresh
flags and the 36 non-template reused rows were reviewed in every scene context.
The 143 defeat-template rows have 205 registered uses and no ordinary uses.
RahXephon technical compounds and alien utterances retain provisional licensed
wording; the scientific stem stochastic resonance follows primary academic
sources. Unfinished actions, poetic fragments and the address contrast remain
explicitly documented. Exact review fingerprint:
`cd858f826660230cfa5dcd91b1dabcfc92fed7e807f6723ee1fd797122031cb1`.

Stage 36 is complete: 547 fresh rows in seven packets, 723 full rows and 825
original uses. All 15 fresh flags and all 33 non-template reused rows were
reviewed in every scene context. The 143 defeat-template rows have 205 registered
uses and no ordinary uses. One real four-line draft overflow was shortened to
three lines without losing branch/workplace details. Four fitting drafts were
restored after correcting an artificial source dialogue-line ceiling; explicit
hospital context survives. Bright's naval rank follows Akurasu Captain;
the earlier generic Colonel interpretation is corrected in final only.
Provisional NERV compounds, Toji's confession referent and intentional fragments
remain documented. Exact review fingerprint:
`eb83c024508af3a8880df1b4c7bdbd6654570d68f15d7f4e34ce5621a0d2e439`.

Stage 37 is complete: 727 fresh rows in ten packets, 916 full rows and 1,043
original uses. All initial and final rows fit without compression. All 21 fresh
flags and every use of the 46 non-template reused rows were reviewed. The 143
defeat-template rows have 205 registered uses and no ordinary uses. Hidden
identities, unfinished refusal/confession and technical wording remain explicit.
Geographical names and pond smelt are sourced; provisional EVA compounds retain
licensed-provenance limits. Exact review fingerprint:
`d3b7cf31bc87fdd627fef921029e2d15bd76a1132a9e702b46ccd6e4bdbcff0b`.

Stages 31–37 now total 4,822 fresh and 6,085 full rows, with 64 validated packets.
Stage 38 is underway. Full-game local insertion and playtesting remain pending.
No further GitHub release is authorized.
