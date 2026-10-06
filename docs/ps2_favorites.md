# Three favorite series — PS2 0.1.18

Both **PS2 – Original** and **PSP – Harder** now offer three distinct
favorite-series choices during New Game setup.

Use Left/Right to browse. Confirm picks or removes the displayed series.
The third pick opens **Use these 3 favorites?**. Yes accepts all three;
No returns to the carousel with the choices intact for editing. Cancel
removes the most recent pick; at zero picks it uses the existing setup
cancellation. The top panel shows the count, three chosen titles and controls.

This is available when starting a game. Existing saves retain their saved
favorites; loading a save does not open a new selector or grant extra choices.
New Game Plus retains the native union of inherited favorites and the three
choices made in this setup. Choosing an inherited favorite again does not
stack its bonus. Each setup prevents duplicate entries among its three slots.

## Native implementation and persistence

`tools/ps2_favorites.py` appends native MIPS routines and text to the existing
English executable segment. `tools/fix_ps2_favorites.py --build` prepares
resources, runs verification and packages `work/output/SRWMX_PS2_EN_0.1.18.iso`.
Input is the preserved 0.1.17 candidate. No patch or cheat files are required.

The original game already uses a 32-bit favorite mask at settings object
offset `0x5e8`. The native setter at `0x337270` unions a bit into this mask;
the getter at `0x336970` checks one series bit. Its 18 carousel entries map
to series IDs `[0,1,3,5,6,7,8,9,10,11,12,14,15,17,18,19,20,21]` through
the original `0x1661e0` getter.

Temporary choice state contains a mask, count and three ordered carousel
indexes. It resets at the native selector initialization and is never written
to a save. Confirm toggles an entry; removing it compacts the ordered slots.
Only the third distinct pick sends the original confirmation event. The final
Yes acceptance unions the temporary mask into the game's existing favorite
mask. The native No and cancel/fade paths remain in use.

The native EXP path at `0x25bf68` and upgrade limit routines read this same
mask. All three selected series receive the original 1.5× EXP and +2 upgrade
limits, subject to the game's existing caps. No additional funds bonus or
replacement stat calculations are introduced.

Native serialization at `0x335808` stores the mask in scenario payload offset
`0x1008`; deserialization at `0x335ca8` restores it without reducing it to one
bit. Existing checksums, sizes and balance-marker data are unchanged. No new
save extension or cross-platform converter is needed for this feature.

The existing carousel title centering hook remains intact. The new panel uses
native VWF measurement and scales width and height together only if a row
exceeds 536px. Its 608×124 panel begins at (16,12); chosen titles start at
(58,48), (58,68), (58,88). Font dimensions restore after each draw and frame.

## Verification and remaining checks

`tools/verify_ps2_favorites.py` executes actual native instructions with only
input, drawing and database fixture services supplied:

- 816 triples in each of two balance modes: 1,632 cases, 29,376 membership
  checks and 1,632 native save-field round trips.
- Remove/compact each of the three positions, repeat picks, undo at counts
  0–3, reject a fourth pick, reset setup, preserve inherited and legacy bits.
- Actual final Yes commit and No reopen paths; no manager bits change while
  choices are only temporary.
- 18 native EXP cases and 270 upgrade-limit cases across five getters and
  three base limits, including cap behavior.
- All 18 series in every selected row, real VWF widths, panel bounds, restored
  font dimensions, and both stationary/scrolling render-hook paths.
- Declared executable changes only; all other prepared disc assets identical
  to 0.1.17. Previous campaign, balance, font and UI regression suites pass.

The local candidate boots in isolated PCSX2 2.8.2 at 4×. Desktop input testing
was blocked by Computer Use errors: `failed to activate captured window`,
then `GetCursorPos failed: Access is denied. (0x80070005)`. A full visual menu
walkthrough, actual memory-card save/reload and physical PS2 testing remain
pending. Native execution and save-field tests do not replace those checks.

Fresh boot is required to load the new executable; older emulator save states
contain old code. No GitHub release or push is authorized or created.

Final ISO: 4,663,269,376 bytes. All 37 disc-file checks pass, including ISO9660
and UDF readback. Only SLPS_253.45 changes from 0.1.17. SHA-256:
`10d491a0ce7331ecaf94270f5112c375276f0a987c1150e104fd22a67833dbdf`.

Final fresh-boot PCSX2 readback matches the immutable native segment and
all 199 hook/reference checks, with zero unknown-opcode or TLB warnings.
This is loaded-byte confirmation, not a visual gameplay walkthrough.
