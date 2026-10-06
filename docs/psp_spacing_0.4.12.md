# PSP 0.4.12: thought dialogue spacing

The reported Daisuke line now separates the name from its parenthesis:
`Daisuke (He's being a fool...!)`. The rule is recorded in AGENTS.md and in
the shared dialogue formatter, `tools/textfit.py`, for future builds.

`tools/fix_psp_thought_spacing.py --build` incrementally updates 0.4.11.
It recognizes the thought prefix before any dialogue quote or row separator,
adds one encoded space, and rebuilds the affected SRWL string tables. It
distinguishes the row control from the same byte inside Shift-JIS glyphs.
The formatter accepts both ASCII and native opening parentheses, normalizes
an existing separator, and leaves anonymous parentheses and quoted speech alone.

Verification found 1,173 exact space insertions across 153 script blocks.
All 1,176 thought rows have exactly one separator; three were already correct.
No lines need rewrapping, no blocks grow, and the largest affected row is
345 px against the 352 px limit. Independent ISO readback through
`play_order.load` compares all 203 command streams and string counts,
confirms each changed string is exactly the previous string plus one space,
and checks the reported Daisuke line (block 127, slot 267).

Only MAP_ADD.BIN changes; all 31 other disc files match 0.4.11, including the
executable, fonts, menus and previous crash fixes. The renderer is unchanged;
this build was checked by complete script/disc readback, without a new gameplay
visual test.

Output: `work/output/SRWMX_EN_0.4.12.iso`, 1,317,414,912 bytes. SHA-256:
`80f9d24f682884059742c89b0e60ab3a53f611ee384e0cb46b068b4478d9acae`.
Reports: `work/output/psp_spacing_0.4.12_verification.json` and
`work/output/psp_spacing_0.4.12_readback.json`. Local testing build only.
