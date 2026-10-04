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

Stages 31–54 now total 14,007 reviewed fresh rows, 18,200 full rows and 196 packets.
Stage 55 is in progress. No later dialogue has yet been inserted into an ISO.

Stage 31 is complete: 726 fresh rows in ten packets, 899 full rows and 1,225
original scene uses. Six distinct Sol 6.1 Medium translators produced preserved
drafts and measured final translations. All initial drafts fit without shortening.
Coordinator reviewed all 45 fresh uncertainty rows, all reused scene contexts,
both route orders and defeat-line registrations. Predict uses its canonical
skill name, and the recurring improvised operation title is consistent.
Original wordplay, deliberate omissions and uncertain licensed provenance remain
documented. Exact review fingerprint:
`a0db5292defccffd883cc8d1448647947b68a20b5018c5ee0b9741b40c08a1c7`.

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
`1c85a7f7bc81c8ffb998ae04c721053111162e15d420d3ef2f67d1d9c5f64f86`.

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
`05255e98114ac2354a1c9017aae6d8349fb125a42c4a106a2a9a45a2944bdb55`.

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

Stage 38 is complete: 529 fresh rows in seven packets, 691 full rows and 774
original uses. All 45 fresh flags and every use of the 19 non-template reused
rows were reviewed. The 143 defeat-template rows have 205 registered uses and
no ordinary uses. Only one fixed condition line required measured shortening,
retaining all four defeat triggers. Haiku, nickname and proverb imagery remain;
provisional fictional labels and separate alternate battle outcomes are explicit.
Exact review fingerprint:
`14179ba9ab943ff94ede9a7934e6cd73efbe145c55e48220042b07dfffd765a6`.

Stage 39 is complete: 204 fresh rows in six packets, 359 full rows and 432
original uses. All 30 fresh flags and every use of the 12 non-template reused
rows were reviewed. The 143 defeat-template rows have 205 registered uses and
no ordinary uses. Two actual overflows required shortening: one dialogue row
and one fixed defeat-condition row. Every question and defeat alternative remains.
The allied/enemy actors in an omitted-subject report are clarified from the
adjacent question and pincer inference in final only. Countdown order, interrupted
clauses and separate timeout/victory branches remain; licensed wording and
soundplay limits are documented. Exact review fingerprint:
`919414be784527b79a98d0aaa933fe8eb8460075510b8a8571e4dffd56e45747`.

Stage 40 is complete: 494 fresh rows in seven packets, 676 full rows and 765
original uses. All 65 fresh flags and every use of the 39 non-template reused
rows were reviewed. The 143 defeat-template rows have 205 registered uses and
no ordinary uses. Only one actual four-line draft overflow required shortening;
the fortress, institute, amplifier and action order remain. Cultural names and
geography are sourced, while fictional physics and poetic compounds retain
provenance limits. Far East Command follows the existing glossary; hidden labels,
source-short acronyms, unfinished commands and barrier-restoration doubts remain.
Exact review fingerprint:
`1691ed3cfc9c2435a2ead350c51457329a7ac966fc383d67cae35397f8c8d303`.

Stage 41 is complete: 454 fresh rows in six packets, 628 full rows and 709
original uses. All 56 fresh flags and every use of the 31 non-template reused
rows were reviewed, including repeated silences in separate scenes. The 143
defeat-template rows have 205 registered uses and no ordinary uses. All full
initial drafts and finals fit without compression. Three final ranked Bright
addresses follow the established Captain rule; Amuro's destruction question
retains the achieved result rather than becoming a purpose clause. Historical
Kunugi/Kuki ranks retain fictional-branch uncertainty. Source-short acronyms,
unfinished clauses, the unnamed medicine recipient, singing syllable counts
and Eldy's reveal order remain. Mutiara follows the actual source spelling,
distinct from the unsupported old Mutiana entry. Exact review fingerprint:
`b1911bb7b01cd324f8c40720aee8189165289ca8cd5c70940793603c9256ec52`.

Stage 42 is complete: 373 fresh rows in six packets, 531 full rows and 596
original uses. All 33 fresh flags and every use of the 15 non-template reused
rows were reviewed. The 143 defeat-template rows have 205 registered uses and
no ordinary uses. All full initial drafts and finals fit without compression.
Conditional defeat storage stays distinct from later event order. The clone
and difficulty pun uses documented clone/groan wordplay; the fortress accusation
keeps its omitted predicate. Unknown Zero labels and the later unnamed escort
retain source reveal order and gender neutrality. Fortress Island, Ogre Island,
gravity control device and Red Arrow Squadron retain licensed-provenance limits;
short Pikadron follows exact Akurasu evidence. Exact review fingerprint:
`7058ea9c465c0dbfb1f774f90b984622e857aa0dc8bf333b3289dd915c4c4143`.

Stage 43 is complete: 514 fresh rows in seven separate packets, 682 full rows
and 756 original uses. Six actual translators preserved full immutable drafts.
All 67 fresh flags and every occurrence of the 25 non-template reused rows were
reviewed; 143 defeat-template rows have 205 registrations and no ordinary uses.
Every initial and final row fits the current font without compression. Conditional
encounters and defeat storage stay separate from rescue and infiltration events.
Zero’s false Altair-death claims, Meteo’s false security report, implanted battle
history and Hokuto’s Ginga/Subaru confusion remain. Brother-role attribution,
Alktos-survivor conjecture, unknown infant origin and cross-row fragments stay
explicit. Final-only corrections follow fixed names, rank and honorific rules
and preserve Machine General comic suffixes. Guard Captain Altair and Gades’s
cosmological labels retain licensed-provenance flags without added identities.
Exact review fingerprint:
`dad10192e59bdb00a036a38e4e802c38684247cbbbe8b25e1175bdd0a4409847`.

Stage 44 is complete: 456 fresh rows in six packets, 621 full rows and 693
original uses. Six actual Sol 6.1 Medium translators preserved immutable full
drafts. All 58 fresh flags and every occurrence of 22 non-template reused rows
were reviewed. The remaining 143 defeat-template rows have 205 registrations
and no ordinary uses. One initial plain list measured 439 px; reflow across its
original three lines preserves all five units and both defeat conditions at
293/305/226 px. Every final row fits; no dialogue compression. Both Hokuto
recovery branches retain their second/third insult counts and false memories.
Unknown child references, alternate-world Gades claims, unfinished sentences
and hidden speaker labels remain faithful to their source contexts. Fixed
Commander Ranking and Leina Power Raiser labels follow scoped glossary rules.
Rosammy follows Akurasu; Nagase's special reading has primary manufacturer
confirmation. Descriptive dimensional terms and the literal softshell-turtle
epithet retain licensed-provenance limits; Altair's human-fear clause retains
its bounded grammatical ambiguity. Exact review fingerprint:
`f98b15cd5bcfee3ea8dac49998fbb988dc9915c32fa4d89dd8d3a00fe62a0eef`.

Stage 50 is underway. Full-game local insertion and playtesting remain pending.
No further GitHub release is authorized.

Stage 45, **Dearest**, is complete: 834 fresh rows, 1,019 full rows and 1,130
original uses in eleven packets from six actual Sol 6.1 Medium translators.
Coordinator reviewed all fresh rows, all 101 fresh flags and all 42 non-template
reused rows at every occurrence. The 143 generic defeat rows have 205 original
registrations and no ordinary uses. Three initial overflows (136, 440, 642)
were shortened only after measuring; full drafts and every change remain local.
All final rows fit the actual font. An independent translator checked the
explicit enemy scope in objective 440; both exclusions and the 30% threshold
remain, with the first line measuring 347 px.

Review preserves the hidden voice until Aoi Wakaba is named, Inez’s false death
report and second-anniversary memorial, Akito’s sensory injury, Subaru’s lifelong
indoctrination distinct from Altair’s mind control, and the concert deception.
Ululun and Nadesico Q&A follow Akurasu; source-short Pros and Hari remain
consistent. Source-specific naval titles, uncertain licensed compounds and
literary allusions have explicit provenance notes. Exact review fingerprint:
`0fb81712779ca3981bc94356d27104b3ffc39215de4f53e8822089bb66ed8e3e`.
Completion audit through 45 has no problems. No later dialogue is inserted into
an ISO, and no GitHub release was created.

Stage 46, **Starlight Serenade**, is complete: 677 fresh rows, 841 full rows
and 934 original uses in nine packets from six actual Sol 6.1 Medium translators.
Coordinator reviewed every fresh row, all 60 fresh flags and all 21 non-template
reused rows at every occurrence. The 143 defeat-template rows retain 205
registrations and no ordinary uses. Initial row 60 required measured shortening;
canonical-name expansion in row 523 caused a separate measured overflow,
resolved with a translator-reviewed minimal change. All final rows fit. Full
initial drafts remain unchanged.

Review preserves concealed pilot identity, compulsory hostage rescue and its
cover story, firing-squad threats, explicit enemy scope and AND/OR objectives,
82% confidence, Dorchenov’s false accusation and later confession, deliberate
microphone broadcast, reduction to 15%, the Mrs/Miss gag and the future
brother-in-law joke. United Lunar Empire Giganos follows Akurasu; prior full-name
occurrences in stages 6 and 30 were corrected and re-reviewed with passing
font and completion checks. SP, PD and SFF remain unexpanded. Exact review
fingerprint: `ea50ed27f558bf1c5c8388115d2d94cda0692f709391b622a00104cbb2783173`.
Completion audit through 46 has no problems. Stage 50 is underway. Full-game
local insertion and playtesting remain pending; no release is authorized.

Stage 47, **Farewell to your Memories**, is complete: 210 fresh rows, 363 full
rows and 439 original uses in six packets from six actual Sol 6.1 Medium
translators. All immutable drafts and final rows fit without compression.
Coordinator reviewed every fresh row, all 22 fresh flags and every occurrence
of ten non-template reused rows. Generic defeat registrations remain 143 rows
with 205 uses and no ordinary uses. Two independently checked final corrections
restore the horse roll-call subject and explicit butt setup for the next joke.

Review preserves system entrustment, source-ranked arrests, concealed referents,
all Lapis possessives, rescue actors, Borne’s four-part metaphor, connected
footwear wordplay, unfinished convictions and both surrender paths. Ruri’s
I/we scope remains explicitly flagged without asserting mutual romance. Ending
is inside the MAP handler; later-stored Hokushin quotes remain conditional
battle encounters. Exact review fingerprint:
`a02a9f494ea9fc8977650e8284ffad567d49611f6204109c17fffd4b4def7f12`.
Completion audit through 47 has no problems. Stage 50 is underway. Local
insertion and playtesting remain pending; no release is authorized.

Stage 48, **A Single Flower and the Green Planet**, is complete: 534 fresh
rows, 688 full rows and 841 original uses in seven packets from six actual
Sol 6.1 Medium translators. Coordinator reviewed every fresh row, all 38 fresh
flags and every occurrence of 11 non-template reused rows. Generic defeat
registrations remain 143 rows with 205 uses and no ordinary uses. One measured
initial overflow was shortened with the complete draft and both measurements
retained; all final rows fit.

Review preserves three painted-label branches, Kyral’s crimes and blindness,
Rubina’s unspoken marriage assumption and shooting reveal, Duke’s subjective
guilt, every family possessive, conditional shootdowns, ranked AND objectives,
map-edge OR defeat, the radioactive crash deadline and delayed homecoming.
Two independently checked meaning corrections align the True painted-label
joke and restore Hikaru’s future-action predicate. Canonical Medifo spelling
and source-short Black Great are reconciled with existing glossary evidence.
Exact review fingerprint:
`3a9a395473dc12b89cd7b6d9b5316345b1396e40e611cb99ef3a1d25a1fcb195`.
Completion audit through 48 has no problems. Stage 50 is underway. Later
dialogue insertion and playtesting remain pending; no release is authorized.

Stage 49, **Death and Rebirth**, is complete: 992 fresh rows, 1,190 full
rows and 1,346 original uses in thirteen packets from six actual Sol 6.1
Medium translators. Coordinator reviewed every fresh source/final pair, all
176 fresh flags and every occurrence of 55 non-template reused rows. Generic
defeat registrations remain 143 rows with 205 uses and no ordinary uses.
Only initial draft54 required measured compression; every final row fits.
Full drafts and semantic before/after measurements are preserved.

Review preserves four Kaworu capture branches, conditional mental attacks,
source soul and song referents, character claims, Adam’s mother description,
Lilith recognition, Human-to-Multiverse correction, both self-destruct
conditions and closing departures. Independent checks correct Kaworu’s
omitted subject and sound-quality wording. A guarded stage-local override
restores Rei’s reused question about Shinji’s thanks without changing its
earlier owner. Akurasu names and provisional technical labels retain
explicit provenance limits. Exact review fingerprint:
`105e6ec5badb9a00c363dcbf396dcf2a55e174f2b73ae72e16a8e17050396e92`.
Completion audit through 49 has no problems. Stage 50 is underway. Later
dialogue insertion and playtesting remain pending; no release is authorized.

Stage 50, **Anthem for the Victors**, is complete: 377 fresh rows, 541 full
rows and 612 original uses in six packets from six actual Sol 6.1 Medium
translators. Coordinator compared every fresh source/final pair, all 58
fresh flags and every occurrence of 21 non-template reused rows. The 143
generic defeat rows have 205 registered uses and no ordinary uses. Three
measured draft overflows (56, 175, 274) required shortening; all final rows
fit. Full drafts and semantic before/after measurements remain preserved.

Review retains the temporary truce, clone recovery and Bahbem reveal,
living-core claims, maternal list, Grand Master defeat before the Devil
Gundam, soul attack, DG-erasure duty and the subsequent fleet briefing.
Independent neighboring translators restored Hari’s stutter and reconciled
Albero’s Commander address. The original Michiru attribution anomaly,
Eldy’s ambiguous singular addressee and conditional event order remain
explicit. Exact review fingerprint:
`6b7ddc2532e871cc660861b254a7f7254685e4f5d63f15d89e4c345932fae425`.
Completion audit through 50 has no problems. Stage 51 is underway. Later
dialogue insertion and playtesting remain pending; no release is authorized.

Stage 51, **Hope, Which is the Final GEAR**, is complete: 390 fresh rows,
556 full rows and 626 original uses in six packets from six actual Sol 6.1
Medium translators. Coordinator reviewed every fresh source/final pair,
all 71 fresh flags and every occurrence of 23 non-template reused rows
(31 uses). The 143 generic defeat rows have 205 registered uses and no
ordinary uses. Only fixed defeat condition 217 required measured shortening;
every final row fits, and full initial drafts remain unchanged.

Review preserves the flashback and AI reveal order, uncertain project ties,
medication shortage and fatal stakes, Altair/Vega/Subaru family relations,
atonement contrast, both-ship escort and eight-turn versus eight-minute
wording. Conditional encounters, ship arrivals and countdowns stay separate.
Independent actual translators restored the technical question, reconciled
Middi’s address and corrected the shared inside joke. Ryoko’s final conditional
actor remains explicitly ambiguous; legacy referents remain gender-neutral.
Exact review fingerprint:
`405d943b45495e807c579217857a9dd80886a2232c3a56ed3ee8ab0b3d85cbb0`.
Completion audit through 51 has no problems. Stage 52 is underway. Later
dialogue insertion and playtesting remain pending; no release is authorized.

Stage 52 is complete: 392 fresh rows, 580 full rows and 647 original uses
in six packets from six actual Sol 6.1 Medium translators. Coordinator reviewed
every fresh source/final pair, all 107 fresh flags and every occurrence of
45 non-template reused rows (49 uses). The 143 generic defeat templates have
205 registrations and no ordinary uses. Only fixed UI conditions 264, 349 and
350 required measured shortening; every final fits and full drafts remain.

Independent review corrected negation scope, the seal-chamber copula, the
quoted legend’s pronoun shift and the guardians’ identity. Phoenix’s reveal
in event 13, the failed synchronization in event 36 and success in event 38
remain separate. Family relations, planetary ecology, the seven-god count
and source hypotheses remain; spirit-vessel identity and the strike object
are explicitly unresolved. Hyribead follows the existing main glossary, with
persistent spelling guards. Exact review fingerprint:
`e0a4bda020a1ac872e426df109a4f1a3f60ec824ef3ab3bb8a8d5f051ebfef01`.
Completion audit through 52 has no problems. Stage 53 is next. Later
dialogue insertion and playtesting remain pending; no release is authorized.

Stage 53, **Soul's Refrain**, is complete: 836 fresh rows, 1,023 full
rows and 1,139 original uses in eleven packets from six actual Sol 6.1
Medium translators. Coordinator reviewed every fresh source/final pair,
all 142 fresh flags and every occurrence of 44 non-template reused rows
(92 uses). The 143 generic defeat templates have 205 registrations and no
ordinary uses. Only dialogue 417 required measured shortening; all final
rows fit and immutable full drafts remain.

Review preserves separate conditional handlers, twin and maternal identities,
the theater metaphor and its two gods, retrospective hypotheses, symbolic
Eva spelling, exact repeated kill counts and German ordinal stems, interrupted
clauses and unknown rescue voices until the Tsukiomi reveal. Meaning corrections
and canonical spelling corrections remain separately measured and documented.
SEELE and Far East Command enforce existing glossary entries. Licensed names
and fictional technical labels without primary corroboration stay flagged.
Exact review fingerprint: `77a08be91b55ff4538bd692f13fcfd64e199eba923121e46f56625914ec19f5b`.
Completion audit through 53 has no problems. Stage 54 is next. Later dialogue
insertion and playtesting remain pending; no release is authorized.

Stage 54, **Across Infinite Time**, is complete: 919 fresh rows, 1,126 full
rows and 1,246 original uses in twelve packets from six actual Sol 6.1
Medium translators. Coordinator reviewed every fresh source/final pair,
all 329 flagged fresh rows and every occurrence of 64 non-template reused rows
(109 uses). The 143 generic defeat templates have 205 registrations and no
ordinary uses. Only dialogue 305, 313 and 616 required measured shortening;
plain 87 required reflow with full canonical names and two original segments.
Every final row fits; full immutable drafts and original uses remain.

Review preserves separate conditional handlers, two/three divine counts,
qualified cosmology and theater claims, the D wordplay, source dates and
family or bodily identity reveals. Interrupted ritual, farewell and final
replies remain unfinished. Unresolved audience and encounter objects remain
explicitly qualified. Meaning repairs and canonical spelling scripts are
measured separately. Boson Out, Gilgazamune and the source-bound deity address
follow established entries and Akurasu. The reused FULL 797 agreement was
independently corrected only for this stage; its earlier owner is unchanged.
Exact review fingerprint: `2b54dd70a0030b812cc3d8589041a9548ec3ffa1fc14e4ebc8fcc9661e62dfed`.
Completion audit through 54 has no problems. Stage 55 is next. Later dialogue
insertion and playtesting remain pending; no release is authorized.

Stage 55, **The Promised Land**, is complete: 1,000 fresh rows, 1,210 full
rows and 1,289 original uses in thirteen packets from six actual Sol 6.1
Medium translators. Coordinator paired-reviewed every fresh source/final,
all 396 fresh flags and every occurrence of 67 non-template reused rows
(80 uses) with final neighbors. The 143 generic defeat templates have 205
registrations and no ordinary uses. Only initial dialogue 9 and 27 required
measured shortening; all final rows fit, and original drafts remain unchanged.

Review preserves the ending, conditional encounters, the Eldy/Akito reveals,
qualified cosmology, personal relationships and unfinished replies. Meaning
repairs remain separate from canonical spelling/rank corrections. The reused
FULL755 question now identifies one approaching object; the earlier stage29
owner is unchanged. Scripted Raideen, source-spoken Harry, Captain Bright and
the locally identified Yurika's Captain Misumaru addresses are measured and
documented after meaning review. Twenty-two earlier owned Harry corrections
and one derived reuse have exact old/new, source-unchanged review proof;
their completed-stage fingerprints above are refreshed.
Exact review fingerprint: `03702c80b850e4275103f731cc145257be4efe06565437120b881f07ffd99016`.
Completion audit through 55 has no problems. Stage 56, the hidden stage, is
underway; unused scenes/save messages follow. Later dialogue insertion and
playtesting remain pending. No GitHub release is authorized.

A full final-corpus scan found five source-owned unit-spelling instances in
stages 2, 35, 54 and 55 using Reideen against Akurasu/main Raideen. A script
corrected these after meaning review, preserved full drafts, remeasured every
changed line and added the persistent spelling guard. Completed stages 2, 35
and 54 have refreshed exact review records; no meaning or game-build change.
