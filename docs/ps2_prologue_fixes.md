# PS2 Prologue corrections — 0.1.10

The user reported Game Over followed by an unusable Intermission, the wrong
researcher bust-up and the original PS2 lab opening appearing before the added
PSP training battle. These are three separate porting defects.

The PSP pre-battle events `i00r0b` and `i00s0b` contain seven commands and no
dialogue. The earlier port substituted the original PS2 `i001b` opening there.
0.1.10 restores the exact empty PSP events. Both routes now begin their spoken
dialogue on the battlefield with Hugo's Wolf 1 radio call. The PSP's reviewed
post-battle lab scene remains in `i00r0a` / `i00s0a`; it is not moved or removed.
All other 201 script blocks are byte-identical to 0.1.9, including the second
PSP extra scenario and the revised preceding scenario.

Native Game Over event 0x13d restores the campaign/roster snapshots and retries
chapter 0/1 only when the battle group is zero. The added Prologue is group four.
The old gate therefore closed the battle and fell back into Intermission before
the player had a permanent roster. A small EE hook at 0x1f5e28 includes group four
in that retry rule. The existing parent retry event (6,1) restarts the campaign's
current chapter/group without changing history or marking a battle cleared.
Other chapter/group combinations retain their original defeat behavior.

The researcher's Pilt row 433 has story group 21, face 10: story asset ID 2110.
Pilt +14 is the separate battle face, intentionally absent. Native PS2 story
metadata lacks ID 2110 and falls back to its first face. PSP portrait data is
ported into two previously unused native face indexes, 2998/2999, with a native
60-byte descriptor in unused slot 309. The original native face archive is
preserved byte-for-byte; the two 256px assets are appended. Source 128px indexed
art is doubled with nearest-neighbor sampling, preserving colours/transparency
and using native CSM1 palette layout. No emulator texture replacement is used.

`tools/fix_ps2_prologue.py --build` prepares and packages this correction from
0.1.9. It preserves old outputs. `tools/verify_ps2_prologue_fix.py` executes 98
native Game Over route cases, reproduces the old Prologue fallthrough, exercises
the real parent retry handler, checks the native Pilt story mapping and reads
both researcher expressions through the native FACEPACK archive loader.
Snapshot services are recorded in those synthetic defeat fixtures; live roster
rollback is not simulated. The stage-30, font, translation, balance, Prologue
entry/numbering and campaign save-field regression checks also pass.

Fresh PCSX2 new game on the Super Robot route, PS2 Original balance, visually
confirms Hugo's Wolf 1 opening and the correct researcher radio portrait.
Screenshots are in `work/ui/ps2/prologue_fix_0.1.10/`. The loaded added segment,
hooks and loader tables match the packaged ELF. All 37 resources validate;
the original ISO and 0.1.9 build remain unchanged. The ISO is
`work/output/SRWMX_PS2_EN_0.1.10.iso` (4,663,252,992 bytes), SHA-256
`a48daca844b70653d944f0696d45cabf2b3d1eefab38136a4fc10d2e32afb078`.

Full in-game defeat/retry, campaign playthrough, memory-card save/load and physical PS2 tests
remain pending. No GitHub release is requested for this build.
