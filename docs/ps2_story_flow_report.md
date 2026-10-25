# PS2 early route choice / repeated dialogue report — 2026-10-25

## Chapter-30 lockout reproduced — 2026-10-26

Reporter confirms **v0.4.38, Earth**. New screenshot shows all seven Hades
Project stages marked Clear with no next stage. Found a separate, real
transition bug: opcode 112 checks completion at the end of chapter 29, when
the added chapter 30 remains uncleared, but chapter 30's closing `i056a`
returns to intermission without that command. Prior tests manually called
112 after marking all seven clear, missing its absence from the actual ending.

Native tests reproduce the locked seven-Clear-row state for both routes.
Local PS2 v0.4.45 adds a narrowly guarded completion check before returning
to intermission and before Stage Select populates its rows. The latter also
recovers an already-stuck campaign state. Both routes advance correctly,
preserving the chosen route, clear counters and history. Incomplete/other
states are guarded. This fixes chapter transition; it does not diagnose the
separate repeated-dialogue report below.

Details: `docs/ps2_stage30_transition_fix.md`; evidence:
`work/output/ps2_stage30_transition_0.4.45_verification.json`. The user has
since confirmed working and supplied an Earth Chapter 31 screenshot, Shine
of the Red Dragon. Reaching the next Earth mission is confirmed by that
report; a live Space-route transition and full playthrough remain unverified.

## Identified dialogue anchor — 2026-10-26

The new screenshot identifies **“Have you finished adjusting the new model's
DFC system?”** The actual public v0.4.38 disc contains this line in `s0570`,
string slot 336, message command 692, within handler 631–1019. It begins
Hugo's discussion of his artificial body, medication, and the upgraded unit.
The original Japanese PSP script has this exact source line at the same
slot/command, once across its full script inventory. All six chapter-28/29
scene command arrays match the intended PSP source, allowing the existing
portrait-cache opcode adaptations.

The original PS2 chapter-28 aftermath, `i055a`, shares 61 longer string slots
with this part of PSP's chapter-29 battle script, including consecutive
dialogue runs. Thus much of the conversation was moved from the PS2 chapter-28
aftermath into PSP chapter 29. Recognizing it as a PS2 chapter-28 conversation
is understandable. Translation working filenames are extraction groups:
`stage56_campaign_full_merged.json` owns this line, but it is **not chapter 56**.

Checked the actual older PS2 v0.4.33 and v0.4.36 ISOs as well, with verified
native version footers. Both retain original PS2 `i055a` commands after
chapter 28 and PSP `s0570` commands in chapter 29. Their two conversations
share **50 identical longer English strings**, confirming that the old build
scripts could present substantial repeated dialogue across those stages.
The chapter-28 port first included in public v0.4.38 removes that old PS2
aftermath. This establishes the historical overlap, not which build the
reporter used for chapter 28.

The active v0.4.38 chapter-28 aftermath uses the PSP version: Hugo is missing,
and Aqua mourns/blames herself in the medical room. It does not contain the
pictured DFC/body-reveal conversation. Comparing chapter 28's three PSP scene
message streams against the chapter-29 battle gives no three-message exact
matching run; the anchor is absent from all three. This distinguishes the
scripted scenes, but does not prove that a handler cannot retrigger at runtime.

The reporter's **first occurrence** is still not identified. If they saw the
body-reveal conversation at both points, an older PS2 chapter-28 playthrough,
an older cached script/save state, an incorrectly applied image or a runtime
event problem remain possibilities, not established causes. Do not blame a
save or remove chapter-29 dialogue without a concrete checkpoint. Asked whether
the exact conversation repeats or Aqua cries again; the user replied
**“exact I think”**, so treat it as a tentative exact-repeat report. Need to
establish which build ran chapter 28 and the earlier occurrence/checkpoint.
The prior instruction to leave their emulator alone
remains in effect.

Evidence: `work/output/ps2_repeated_dfc_dialogue_0.4.38_audit.json`;
reproducible audit: `tools/audit_ps2_repeated_dialogue.py`. Screenshot:
`work/ui/ps2/stage29_route_report_2026_10_25/dfc_conversation_reported.png`.
The latest local v0.4.44 retains the exact same MAP resource hash as v0.4.38.
This was an audit only; no script edits, new game build or release.

## Objectives-footer report closed by user correction

On 2026-10-25 the user clarified that the pictured battle actually was
chapter 28. Its **28 / Tragedy Beneath the Moon** footer is therefore correct.
No objectives or campaign patch is needed for that screenshot. The earlier
repeated-dialogue report remains separate and unresolved. The investigation
below records the evidence gathered before the correction.

After the chapter-30 card, the user supplied an Objectives screenshot whose
footer reads **28 — Tragedy Beneath the Moon**. This was initially treated as
a suspected inconsistency, separate from the expected route-choice order. The image
is saved as `work/ui/ps2/stage29_route_report_2026_10_25/objectives_reports_28.png`.
Do not treat the earlier correct route-order check as resolving this report.

Executed both actual objectives preparation paths in the v0.4.38 executable,
including the existing title wrapper, using its actual STAGE resource:

- chapter index 7/group 8, hero count 28 -> 28 / Tragedy Beneath the Moon;
- chapter index 7/group 12, hero count 29 -> 29 / What Gnaws at the Heart;
- chapter index 7/group 10, hero count 30 -> 30 / Zeorymer Sorties at Dawn.

Evidence: `work/output/ps2_objective_footer_0.4.38_audit.json`. These supplied
state fixtures show that the lookup/preparation code can display the right
values, not that the live game had those values when the screenshot was taken.
The number comes from Hero +0x5f0 and the title is looked up through campaign
chapter/group. Need to inspect the reported frame's source values, current
script/deployment and window fields before deciding whether the cause is stale
UI, incorrect live campaign state, or a different battle being loaded.

A read-only connection to local PCSX2 v2.8.2 confirmed MX and matching sampled
port instructions, but found count 29/group 12 at a different checkpoint. The
user confirmed they had moved away from the screenshot and were checking
something else. That capture is **not** a reproduction or evidence that the
reported frame was correct. Live reading stopped; do not resume it until the
user returns to this investigation. No memory writes, UI controls or emulator
resumption were performed. No code/ISO change or fix is claimed.

## Initial report

The user forwarded a report that the PS2 patch shows PSP scenario content,
asks for a route choice before a mission ends, and repeats dialogue scenes.
The reporter suspects that both PS2 and PSP scenarios are running.
The reporter confirmed PCSX2 v2.6.3, English v0.4.38, stage 29. Exact repeated
dialogue and save origin are still unknown. The problem is not reproduced or
fixed.

PSP scenario content is intentional in this project: the PS2 port includes the
PSP Prologue, reworked Chapter 28 and 29, and added Chapter 30. Chapter 28 was
explicitly requested and first included in local PS2 v0.4.37 / public v0.4.38.
This does not establish whether the reported route timing or repetition is
correct. Those symptoms need investigation against a concrete checkpoint.

Read-only audit of the actual public v0.4.38 PS2 ISO:

- The executable matches the recorded v0.4.38 executable hash.
- The active loader table has 203 entries and 203 distinct scene names.
- 186 command arrays match their original PS2 source hashes exactly.
- The other 17 match the intended PSP source commands exactly, after the
  previously documented portrait-cache opcode adaptation (179 to native 178).
- Every opcode-109 scene call refers to an existing active scene name.
- Each ported battle script has one before-scene call and one after-scene call.
  The commands are replacements of the intended source, not concatenations of
  the PS2 and PSP command arrays.

Evidence: `work/output/ps2_story_flow_0.4.38_audit.json`, including per-scene
command hashes, provenance and scene-call indexes. This is a static active-table
and command-provenance audit, not a full runtime event trace. Unique scene
entries do not prevent a scene from being triggered twice by campaign state,
event conditions, retry/load behavior or platform-specific command semantics.

Earlier native checks established loader/table, selector, save-field and
numbering behavior. The complete ported mission-clear/transition playthroughs
were still pending, so those checks could miss the reported behavior. Do not
close this report based on command equality or suggest the reporter's save is
the cause without evidence. Save migration was historically not implemented,
so save origin is relevant information to collect, not an established cause.

## Stage 29 follow-up

The actual v0.4.38 battle script `s0570` calls opening `i057b` at command 324
and closing `i057a` at command 1502. The route choice is command 254 in the
closing scene: **Send them into space / Keep them on Earth**. It exists in
the original PSP source and precedes the added stage 30 (`s0560`). Thus a route
choice before that extra battle, by itself, is part of the imported story.
This does not establish whether the reporter saw it at the proper time.

The closing handler starts at command 1451. Its condition commands at 1452
and 1453 retain the original PS2 stage-29 guard operands: local variables
150 and 12, with different jump indexes appropriate to the new script. There
is no unconditional direct closing-scene call inserted into the opening.
This remains a static inspection, not proof that runtime state satisfies
those guards only when intended. No speculative script edits were made.

## Observed Earth choice followed by Chapter 30

The user supplied screenshots of the route prompt and the following Chapter 30
card, **Zeorymer Sorties at Dawn**. That sequence agrees with the intentional
PSP campaign port. Both choices retain this shared battle before the split.
Screenshots are saved in `work/ui/ps2/stage29_route_report_2026_10_25/`.

Follow-up native execution on the actual v0.4.38 executable and STAGE resource
checks opcode 111 (`0x300710`) storing route byte 6 and opcode 112 (`0x3007b8`)
handling chapter advancement. With six of seven chapter locations cleared,
both choices leave chapter index 7 active. Selecting its last location calls
the native group/title lookup and yields group 10, Zeorymer Sorties at Dawn.
With all seven marked clear in the fixture, native advancement follows the
saved choice: Space -> chapter index 8, **Break through the Falcon**;
Earth -> chapter index 9, **Shine of the Red Dragon**.

Evidence: `work/output/ps2_stage29_route_choice_0.4.38_verification.json`.
This checks route storage and campaign routines with explicit clear-state
fixtures, not a full battle-clear simulation. The two screenshots by themselves
do not demonstrate premature route timing or duplicated scenes. The earlier
reported repetition remains unresolved pending its exact dialogue/checkpoint.

Next reproduction needs a checkpoint before the problem, the exact repeated
lines and whether the run started fresh or used an existing save/save state.
Trace the actual battle-clear event, after-scene call and campaign advance at
that checkpoint, comparing the corresponding original-platform behavior.
No ISO, published patch or release was changed during this audit.

## Akurasu MXP chart discrepancy

The user linked [MXPFlow Chart](https://akurasu.net/wiki/MXPFlow_Chart), which
lists Hades Sorties at Dawn at 29 and the route branches at 30. This section
retains PS2 ordering/numbering despite the Portable page title and added PSP
notes. It omits Portable's reworked stage 29, What Gnaws at the "Heart".

Checked the **original Japanese PSP ISO**, not only the patched PS2 tables.
Its `/PSP_GAME/USRDIR/STATIC2_ADD.BIN` matches the local original resource
exactly (SHA256 is in the evidence). Native chapter index 7 has count 7 and
location order `[29,30,31,32,33,66,34]`. The final three locations resolve to
Tragedy Beneath the Moon (33/group 8), What Gnaws at the "Heart" (66/group 12),
and Zeorymer Sorties at Dawn (34/group 10). The next chapter is the branch.
The PS2 port remaps added ID 66 to 68 because its added Prologue already uses
66/67; it retains the same story order.

The [Japanese PSP scenario list](https://srw.wiki.cre.jp/wiki/全話一覧/MX_PORTABLE)
independently lists these as stages 28, 29 and 30, with the route branches at
31. The [PS2 list](https://srw.wiki.cre.jp/wiki/全話一覧/MX) puts Hades at 29
and the branch at 30, explaining the chart's conflicting numbering.

Evidence: `work/output/psp_original_stage29_30_order_2026_10_25_verification.json`.
The screenshot is preserved with the route report's UI evidence. No campaign
order change is warranted by this chart. The repeated-dialogue report is still
separate and unresolved. Source exception recorded in `docs/glossary_decisions.md`.
