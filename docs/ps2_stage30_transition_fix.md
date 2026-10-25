# PS2 chapter-30 lockout — local v0.4.45

User acceptance, 2026-10-26: the user confirms working and supplies an Earth
Chapter 31 Objectives screenshot, **Shine of the Red Dragon**. Saved as
`work/ui/ps2/chapter30_lockout_2026_10_26/confirmed_chapter31.png`; the build
reports include a separate `user_validation` record. The image does not show
the exact version footer and does not verify the live Space route or a full
mission playthrough. Native fixture limitations below remain historical.

Reporter: PCSX2, English v0.4.38, Earth choice. The Stage Select screenshot
shows all seven Hades Project locations cleared, including Tekkoryu Fortress,
with no next stage available.

The imported PSP chapter-29 closing scene, `i057a`, calls opcode 112 to check
chapter completion. On PS2 the current seven-location chapter is not complete
at that point, so this check leaves it active for the added chapter 30.
Chapter 30's closing `i056a` ends with **108, 93, 127**, returning to intermission
without another opcode-112 check. The native PS2 chapter advance routine is
only called from opcode 112. Once chapter 30 is cleared, its selection screen
therefore can show seven Clear entries in the still-active old chapter.

Native execution reproduces that exact campaign/selection state for Earth
and Space: chapter index 7, scene index 5, mask 0x7f, seven cleared rows.
The earlier route tests directly invoked opcode 112 after setting all seven
bits. They proved the destination lookup, but missed that the actual final
scene never invokes the check. Those prior tests were insufficient to cover
the ending's command flow.

`tools/fix_ps2_stage30_transition.py` adds one guarded native helper and two
entry wrappers:

- Before opcode 108 returns to intermission, check this completed chapter
  in normal script mode and use native `0x346f38` to advance it.
- Before `0x1c4ba8` populates Stage Select's rows, run the same guarded check.
  This recovers a save already in the reported state and builds the next
  chapter's rows immediately, without replaying or clearing a stage again.

All guards must match: chapter index 7, scene index 5, current deployment
group 10, clear mask exactly 0x7f, route byte 6 equal to 0 or 1, and the
native location count equal to seven. An uninitialized campaign/STAGE pointer,
other chapters, incomplete clears, invalid routes and the old six-location
layout do not advance. The opcode-108 wrapper preserves special/replay mode.
The helper becomes inert after the first advancement, so repeated openings
do not skip another chapter.

Both existing regular PS2 builders include the patch. No dialogue, script
commands, deployment records or save-layout bytes change. Existing completion
counters, route choice and battle history stay intact. The normal native
advance increments the scene index and resets the current chapter's clear mask.

`tools/verify_ps2_stage30_transition.py` runs the actual ending opcode 108,
chapter advance, Stage Select population, title lookup and next-stage selection
on the packaged executable. It checks both routes, previously stuck state,
late clear-bit commitment, repeat entry, history preservation and the next
history append, all 127 incomplete masks, seven other-state guards, the old
six-location layout, null pointers, and special mode. Earth unlocks **Shine of
the Red Dragon**; Space unlocks **Break through the Falcon**. The fixture only
supplies delivery of the intermission event; it does not stand in for the
campaign/selector routines. A full battle-clear playthrough and the reporter's
actual memory card remain untested.

`tools/build_ps2_stage30_transition.py` builds over local PS2 v0.4.44 using the
shared incremental executable writer. Complete source and expected/actual
output hashes protect all bytes outside registered executable/metadata changes.
Both filesystem views agree on the new executable. All other 36 resources and
locations are preserved, including the entire MAP archive. The native footer
is regenerated and read back as **v0.4.45 / github.com/retro-trans**; 42 native
title-state cases pass.

Local test ISO: `work/output/SRWMX_PS2_EN_0.4.45.iso`.
SHA256: `26d3b9e81bf92d4e96658a067316663aaf493176d96c132b8bb293db797810b8`.
Evidence: `work/output/ps2_stage30_transition_0.4.45_verification.json`.
Public remains v0.4.38; local PSP remains v0.4.42. No release requested.

For an already-stuck game: boot this ISO, load a normal in-game save, then open
Stage Select. The native recovery uses the existing route and completed-stage
state. An old emulator save state can restore the old executable, so use an
in-game save for confirmation. The user's emulator and memory cards were not
operated or modified during this work. The subsequent user confirmation of
reaching Earth Chapter 31 is recorded above.
