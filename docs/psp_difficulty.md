# PSP New Game balance selector — local v0.4.61

Start New Game, complete the hero and robot setup, and choose Finish Settings.
The confirmation offers **PS2 - Original** and **PSP - Harder**, with PSP
selected initially. Cancel returns to setup. Both choices proceed to the
normal three favorite-series selections and the opening sequence.

PS2 mode uses the original PS2 base HP and funds rewards for units whose IDs
and Japanese names match across the two original databases. This changes 139
HP records and 294 reward records. Other records use the PSP values, including
the PSP-only Dragoon in slot 156. PSP mode uses the native PSP getters. The
selector controls these two balance fields within the PSP campaign.

The choice is stored in the common save settings tail using the same MXBD,
format 1, mode 0/1 extension as the PS2 patch. The original serializer uses
the first 164 bytes of that 1024-byte tail. The extension occupies twelve
bytes at offset 0x3e0. Existing native fields and payload lengths are retained.
Missing, unsupported or invalid extensions select PSP balance. Loading a
scenario restores the mode before unit deserialization.

`tools/psp_difficulty.py` appends a small table, menu strings and native wrappers
to the loaded PRX segment. It registers the new code, data and string
relocations. An object-specific copy of the Yes/No vtable supplies a wider
opening and cursor. Cleanup restores the shared window's normal class and
labels before later confirmations.

`tools/verify_psp_difficulty.py` executes the native getters for all 512 records
in both modes and two invalid modes, plus out-of-range fallback, menu setup,
five-frame opening, up/down wrapping, both confirmations and Cancel. It also
checks the complete native serializer, scenario/system save tails, legacy
defaults, and restoration before loading unit data.

The actual ISO was cold-booted in an isolated PPSSPP v1.20.4 profile. Both
robot setup routes displayed the selector, cancellation returned to setup,
and both balance choices reached the opening after three favorite-series
selections. The loaded feature bytes and relocations match the ISO. Live
gameplay save/reload and physical PSP testing remain pending.

Build from the verified local v0.4.60 image with
`tools/build_psp_s1050.py --base 0.4.60 --version 0.4.61 --feature difficulty`.
The normal full PSP builder includes the feature from v0.4.61 onward. The
local output is `work/output/SRWMX_EN_0.4.61.iso`. Native and runtime evidence
are recorded in `work/output/psp_difficulty_0.4.61_verification.json` and
`work/output/psp_difficulty_0.4.61_runtime.json`. Screenshots are under
`work/ui/psp/difficulty_0.4.61/`.
