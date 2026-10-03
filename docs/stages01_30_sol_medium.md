# Stages 1-30 translation campaign

Started 2026-10-03 at the user's request. Model: Sol 6.1 (`gpt-6.1-sol`),
reasoning effort Medium. Cover all routes listed for numbered stages 1-30 in
`docs/stage_map.md`, including both protagonist routes and Earth/Space branches.
The unnumbered secret stage is outside this numbered scope.

The local queue is `work/output/stages01_30_sol_medium_manifest.json`.
There are 21,024 stage-local unique rows, including shared lines, and 16,092 new
rows in 241 assignments of at most 80 consecutive rows. Already translated
prologue lines are linked by exact Japanese source text. Other repeated source
lines have one translation owner; final stage files must retain every original
`uses` location. Reuse needs context review whenever an English subject/referent
could change between occurrences.

Six actual Sol Medium translator workers share each stage. The session permits only three
child agents simultaneously, so they run in waves. Each assignment respects the
80-row Base_rules limit; workers may receive further separate assignments.
Short stages are split into six smaller nonempty packets. Longer stages keep
80-row packets; the six workers can receive later separate assignments. The
manifest's explicit start/stop intervals are authoritative for coverage checks.

Sources are `work/translation/en/script/stageNN_campaign.json`. Full original
context is in `stageNN_campaign_all_source.json`, including translation-owner
references. Route-specific `stageNN_campaign_sXXXX_order.json` files preserve
script event order. Battle event order is approximate and defeat messages may
not appear in the linear order. Sources are local ignored files.

Current rules were copied byte-for-byte into `BASE_RULES_campaign.md` and
`TRANSLATOR_BRIEF_campaign.md`. Translators read original context, glossary and
fixed spellings; keep full initial drafts; measure every row with the actual VWF
font; compress only measured overflow; and report uncertainties and omissions.
Names and runtime placeholders retain their prescribed spelling.

`tools/prepare_stage_campaign.py` previews first and refuses overwrite when
writing. It corrects numbered mission conditions mistakenly recognized as
speaker dialogue by the older generic classifier. This preserves their explicit
line breaks and leaves the Japanese source unchanged.

Outputs use tag `sol61medium`: draft, final slice and decision/fit report per
assignment. A stage is complete only after coverage, structural, placeholder,
character, font-fit and spelling checks, plus review of meaningful uncertainties
and shared-context reuse. Safe `*.en.json` copies are generated for eligible
outputs. No game insertion is implied by a completed translation file.

## Progress

Stages 1-30 are translated: 16,092 new rows in 241 packets, using six distinct
actual Sol 6.1 Medium translators per stage. Full assemblies contain 21,024
stage-local unique rows across every numbered route, retaining all original
scene uses. Initial drafts and reports are preserved. Coverage, font,
character, placeholder and spelling checks pass. Coordinator context review
covers all reused lines and meaningful fresh flags; source ambiguities and
provenance limits remain explicit. Fingerprints identify the exact reviewed
wording and scene uses. Game insertion and in-game testing are still pending.

The final completion audit is `work/output/campaign_completion_audit.json`.
Per-stage review details below record the completed campaign.

Following the requested font replacement in build 0.1.3, all campaign outputs
were revalidated with Genei LateGo at 15 px: no fit findings, identical review
fingerprints and translation wording. The audit now records the new atlas hash;
historical draft measurements remain in the original translator reports.

Stage23 added824 fresh rows in11 packets from six actual translators. Only
measured overflow666 was compressed. All179 reused rows and44 fresh flags
were reviewed with every scene use and final neighbors. Hidden voices, symbolic
imagery and source uncertainties remain intact; mock-praise titles were corrected.
Full1,003-row/1,103-use checks and matching context fingerprint pass.

Stage22 added385 fresh rows in six packets. Only measured overflows69/235
were compressed; exclusive defense/evasion, command position and radio-joke
callbacks were corrected in source context. All167 shared rows and26 fresh
flags were reviewed. Six actual translators completed the stage; full552-row,
629-use checks and review fingerprint pass, with source ambiguities and initial
drafts retained.

Stage21 added261 fresh rows in six packets without compression. All173 shared
rows and11 fresh flags were reviewed, with every original use restored in the
434-row assembly. Source-short units, bait assignment, identity crisis, conditional
resolve, theory provenance and eyes/shadow imagery remain source-dependent.
Six actual translators completed the stage; full checks and review fingerprint pass.

Stage 20 added 339 fresh rows in six packets, with only measured dialogue
overflow74 compressed. All149 shared rows and18 fresh flags were reviewed,
including every actual use and final neighbors. Six actual translators completed
the stage; full488-row assembly has a matching review fingerprint and no findings.
Source technical compounds and jokes retain their provenance limits.

Stage 18 added 1,544 fresh rows in twenty packets. Six measured dialogue
overflows were compressed; all 171 shared rows and 35 fresh flags were reviewed.
Rank, geographical scope, probable-action and explicit-death corrections precede
the sourced name pass. Stage 19 added 532 fresh rows in seven packets, with no
compression; all 154 shared rows and seven fresh flags were reviewed. Hidden
identities, battle-event alternatives, paired jokes, confessions and literal
imagery remain source-dependent. Both full assemblies have matching review
fingerprints and zero structural/font findings. Source-short Dr. Plato was restored
in stages2/11/18 after meaning review, with renewed earlier fingerprints and
initial drafts preserved. The generic 143-row battle template has been compared
through stage30; each remaining stage still needs its other shared-context review.
Six actual translators shared each completed stage, handling later packets as
separate assignments. No compression occurred in stage 1; stage 2 compressed
only two measured overflows, retaining their timing and ship details. Stage 3
also compressed only two measured overflows; stages 4, 5 and 6 compressed one each.
Stage 7 compressed two measured overflows and retained source-cutoff references.
Stage 8 compressed five measured overflows, with agent review restoring immediate
attack timing and the mission condition's any-attack trigger.
Stage 9 required no compression; its six smaller packets retain hidden references
and partial comparisons without adding identity revelations.
Stage 10 compressed one measured objective overflow, preserving the inclusive
HP threshold and persuasion order. Its four source/wordplay uncertainties remain explicit.
Stage 11 compressed one measured dialogue overflow. Its thirteen fresh uncertainties
retain hidden/unnamed references, uncertain temple spelling and literal technical
labels. All 165 shared rows were reviewed in their original contexts.
Stage 12 required no compression. All 148 shared rows and eleven fresh uncertainty
flags were reviewed, retaining the sisters' fragmentary comparison, wordplay and
unestablished terminology provenance.
Stage 13 compressed one measured transmission overflow and retained fourteen
fresh uncertainty flags, including cryptic Quon imagery and literal labels.
All 161 shared rows were reviewed in every original use; initial drafts retained.
Stage 14 compressed one measured briefing overflow and retained six fresh
uncertainty flags. All 157 shared rows were reviewed; Earth/Moon choice directions
and explicit menu breaks are preserved.
Stage 15 compressed one measured boarding objective and one intelligence briefing.
All 174 shared rows and nine fresh flags were reviewed, preserving broken radio
fragments, dialect/wordplay and terminology provenance. Six actual workers handled
eleven separate packets. Spoken Harry, fixed Oyakata-sama and Rom Stol were
reconciled after meaning review; full Hari Makibi and speaker Hari are retained.
Stage 16 compressed three measured dialogue overflows, preserving the route briefing
and Federation offensive. All 151 shared rows and five fresh flags were reviewed;
source allusions and English terminology provenance limits remain explicit.
Eight separate packets were handled by six actual translators.
Stage 17 required no compression. All 170 shared rows and 28 fresh flags were
reviewed; hidden identities, route alternatives, deliberate cutoffs, wordplay and
opaque metaphors remain visible. Six actual translators handled ten packets.
The Ryo nickname was checked across all campaign sources: five earlier Stage 2
lines and two prologue assembly copies were corrected. Full Ryoma stays unchanged
where the source uses it; original drafts and prologue/build files are retained.
The queue is the authoritative detailed progress record; this document explains
the workflow. Build 0.1.0 and prior comparison sheets remain available.

Stage24 completed473 fresh rows in6 packets; full637 rows/716 scene uses pass.
All164 shared rows and15 fresh flags reviewed. Only measured overflows33/70/448
compressed; ritual astronomy and cryptic references retained. Review fingerprint
2f4f19b41449e3e6ad705bf37a7a38a6dc28f68f5be50e3a351f796f090f72dc matches.
Stages25 and26 subsequently completed; see the records below.

Stage25 completed199 fresh rows in6 packets; full359 rows/426 uses pass,
all160 shared rows and6 fresh flags reviewed. Only plain140 overflow compressed,
with added sequencing removed. Contempt91 restored; draft retained. Fingerprint
53604bdfdbbb62b5710de2c8fb88c7b39735fe4b0c1aa8ac31de215da93fcf4e matches.

Stage26 completed86 fresh rows in6 packets; full234 rows/296 uses pass.
All148 reused rows and3 fresh flags reviewed; only dialogue63 overflow compressed.
Fingerprint6197288e0dbeec7d56349242c348dfe32e79813bc75e087462ab8eca57d0aa79
matches the reviewed assembly.

Stage27 completed123 fresh rows in6 packets; full269 rows/331 uses pass.
No compression; all146 shared rows and3 fresh flags reviewed. Fingerprint
e97d5b9c5c6188ff37a4c0f55c44a8edd75ba8c76633889fda345cb42024a1bc matches.

Stage28 completed626 fresh rows in8 packets with6 actual translators; full802 rows pass source context review. Only plain316 needed measured compression. All176 reused rows and8 fresh flags reviewed; exact copies502/689 corrected without changing prior owners. Activation471 preserves separate commands and singular limiter release; male lead rank follows glossary Ensign. Fingerprint302a93803a9cabe5fc103639e3553d9866972f3c9a70d9965ab64bfdf1b63b8d. Stage29 subsequently completed.

Stage29 completed363 fresh rows in6 packets; full530 rows/611 uses pass, all167 reused rows and10 fresh flags reviewed. Only58/110 overflow compressed. Passive58 retains the omitted actor, independently reviewed; full487 remains valid acknowledgment. Fingerprintd02ea384ad19dc4ca40311b15dfe079deb1256d1264ce14d476b66b42ec0868c. Stage30 subsequently completed.


Stage30 completed680 fresh rows in9 packets with6 actual translators; full839
rows and1,116 scene uses pass. All159 reused rows and6 fresh provenance/wordplay
flags reviewed at every actual use. Only464/596 needed shortening under the
initial font measurements; current font checks pass, and historical measurements
and full drafts remain retained. Getter activation/timings, political arguments,
threats, and closing virus scenes preserve source meaning. Names and technical
labels are centrally sourced with explicit provenance limits. Fingerprint
47834df1a02439dd971ee5db22e62c1bdc09798e5c94688dd73b276e0c896507 matches.
