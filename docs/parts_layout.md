# Parts window alignment — local v0.4.35

The supplied PSP screenshots show the equipped-part value touching the panel
divider and descriptions running past the right edge. The old value origin was
110px from the panel origin. Description insertion used a 272px wrapping budget
that exceeded the actual native text area.

The equipped-name origin is now 80px. Names keep their full wording. Only names
that exceed the remaining 162px receive a temporary proportional font reduction;
the draw wrapper restores both display dimensions afterwards. It preserves the
previous 256-byte unit-name scratch buffer fix, selection logic and row spacing.

All 37 PSP descriptions are wrapped at a 224px source-font budget. Executing the
native 14px font-width routine confirms their actual widths are at most 196px,
inside the 200px text area. Each description has at most four rows, fitting the
existing 19px row spacing. Haro and High Performance Radar retain their wording
and every numeric effect.

PS2 already places equipped names on separate rows below the label, so that
name origin is retained. Its descriptions are wrapped using the actual native
font advances, rather than the PSP proxy. Native execution confirms every row
is at most 257px within the 258px budget. At most five rows fit the native panel.

The correction preserves numeric gameplay sections, names, unrelated description
indexes and protected sentence content. PSP retains all earlier sentence IDs;
PS2 reuses only unshared part rows and unused blank IDs within the fixed database
heap. PSP's enlarged PRX is appended once, with both executable directory names
pointing to its identical bytes. All remaining resources keep their allocations.
Both exact native title footers are regenerated with v0.4.35 and the credit.

Tools: `parts_layout.py`, `verify_parts_layout.py`, `build_parts_layout.py`.
Records: `work/output/{psp,ps2}_parts_layout_0.4.35_verification.json` and
`work/output/parts_layout_0.4.35_native_verification.json`.
Fresh in-game visual and live equip/exit checks remain pending; no GitHub release
has been requested for this build.
