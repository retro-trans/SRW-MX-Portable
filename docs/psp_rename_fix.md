# PSP unit rename corruption — local v0.4.38

The reported public v0.4.33 screen is reproduced by executing the original
native initializer. It copies the 16-character translated upgrade name into
an editor field spaced only 23 bytes from Reading. Loading Reading then
overwrites the tail of Name, producing mixed glyphs. The old 11-character
Name and six-character Reading limits also truncate the English defaults.

The unit editor already has 48 usable bytes at object offsets `0x614–0x643`,
before its control words at `0x644`. The fix packs a 31-byte Name field and a
17-byte Reading field into that space: 15 and eight full-width characters,
respectively. It updates initialization, rendering, cursor limits, insertion,
deletion, reset, validation and export consistently. Object allocation and
all save-record offsets remain unchanged. The native saved names already
have 32-byte slots.

The editable default is now **Cerberus Ignite**, a 15-character spelling used
by Akurasu's MX Pilot Database. The old **Cerberus Ignited** default requires
33 bytes including NUL, which exceeds the save slot. The separate Mech List
database G/S terms are retained. The source-backed exception is recorded in
`docs/glossary_decisions.md` and `work/glossary/decisions.json`.

A small relocated native guard terminates loaded fields before the original
strlen/padding logic. This also handles the old 16-character saved default
without changing the save format. The initializer fills any remaining cells
with its original full-width spaces; normal export trims those spaces.

`tools/fix_psp_rename.py` applies exact original-instruction guards and is
included in the regular PSP builder. Native tests in
`tools/verify_psp_rename.py` reproduce the old corruption and cover all four
robot defaults in reset and saved-name modes, maximum-length custom names,
the legacy overlong default, both fields' first/middle/last deletion and space
actions, control-word guards, underline coordinates, idempotence and PRX
relocations. The last underline positions remain within both visible fields.

`tools/build_psp_rename.py` preserves the v0.4.36 disc and appends one corrected
PRX shared by BOOT/EBOOT. The native footer is regenerated as **v0.4.38** at
the bottom right, with **github.com/retro-trans**, outlined text and no panel.
Both approved Ritsu revisions are inserted into their existing stage-28
allocation; only slots 400 and 427 change. All other dialogue, script commands,
battle captions, Parts fixes and original disc bytes remain exact, apart from
the required executable directory/volume metadata and new title footer.

Test ISO: `work/output/SRWMX_EN_0.4.38.iso`.
SHA256: `9adb8ad55560d6bd2380247d0f0394fd52a03d28982e8e081d40201e2ce04798`.
Evidence: `work/output/psp_rename_0.4.38_verification.json`.
The complete expected image hash and actual ISO resources agree. Fresh
PPSSPP visual acceptance remains pending; the user-stopped GUI was not
resumed. This is a local PSP test build. PS2's editor was not changed and no
release was published.
