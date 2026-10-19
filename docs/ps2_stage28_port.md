# PSP stage 28 port to PS2

The local PS2 v0.4.37 candidate replaces all three Chapter 28 scenes,
**Tragedy Beneath the Moon**, with their reviewed PSP counterparts:

| Scene | Purpose | PSP commands | Translated strings |
| --- | --- | ---: | ---: |
| `i055b` | Opening | 231 | 168 |
| `s0550` | Battle events | 1,502 | 731 |
| `i055a` | Aftermath | 161 | 108 |

This completes the previously missing stage-28 portion before the imported
PSP stages 29 and 30. The earlier port replaced the Prologue and those later
stages while retaining PS2's original stage-28 events and aftermath.

All PSP event commands, operands and branch indexes are retained exactly.
These three scenes do not use PSP-only portrait-cache opcode 179, so no
opcode substitution is needed. English comes from the shared, reviewed
Chapter 28 source, including both Ritsu revisions approved on 2026-10-18.
Native PS2 wrapping fits all translated lines within 528 pixels and three
lines. All blocks remain below the native `0x25000` script-buffer limit.

The 34-unit deployment at index 148 (chapter 7, group 8) differs from PSP by
one byte: deployment-record 1, field +24, changes from 0 to 1. The port uses
the exact PSP deployment. It preserves unit/pilot IDs, database stats, the
selected balance mode and every other deployment. Map 460 remains the
original PS2 24-by-30 map; all 720 terrain IDs match PSP, while native heights
and all map bytes are retained.

`tools/ps2_stage28.py` performs the guarded conversion. The regular PS2
story builder now applies it and selects PSP source mappings for these
three scenes, preventing later rebuilds from restoring PS2 stage 28.
`tools/build_ps2_stage28.py` creates the local test image over verified
v0.4.36 and regenerates its native title footer as **v0.4.37** with
**github.com/retro-trans**. PSP is unchanged by this PS2-only build.

Verification covers exact command and English readback for all 1,007
translated strings, the two approved Ritsu lines, idempotence, all 200 other
script blocks, other map sections and unrelated disc bytes. Native loader
execution includes the three added scenes, their deployment, retained
stage-29/30 scenes and campaign location progression. Native Chapter 28
numbering is compared with the baseline. Regression tests reject missing
translations and unsupported PSP opcodes, and check the approved dialogue's
PS2 reflow. ISO9660 and UDF must read identical updated resources.

The output is `work/output/SRWMX_PS2_EN_0.4.37.iso`; evidence is
`work/output/ps2_stage28_0.4.37_verification.json`. A complete in-game stage
28 clear and transition into stage 29 remain pending. No release is published.
