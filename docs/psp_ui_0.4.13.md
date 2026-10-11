# PSP screenshot corrections — local 0.4.13

The user compiled a list of screenshots and clarified that some may come
from older builds. PSP 0.4.12 is the baseline, rather than an assumption that
all four screenshots reproduce on that version.

| Report | Result |
| --- | --- |
| Chapter 11 `do justice to` | Replaced the native mixed-size English lettering with uniformly sized, centered lettering in all three title atlases. |
| Spirit Search result costs | Separated the name, opening bracket, numeric/unknown cost and closing bracket in all six footer cells. Corrected the unavailable-command branch's inconsistent column and row strides too. |
| Judau Level Up skill corruption | Already fixed since PSP 0.4.10. Both 0.4.12 and 0.4.13 pass the formatter and native window drawing fixture. No new Level Up code change. |
| Chapter 7 objectives | Changed the imperative to `1. Zeorymer of the Heavens is shot down.` in both s0150:207 and s0430:207. Losing this allied unit triggers defeat; the wording must describe that event. |
| Chapter 7 title | Retained `King of Hades: "Heaven"`, the short form of `The King of Hades, His Name Is "Heaven"`. Both 56-byte scenario title fields read back correctly. The earlier source-based title decision is in `docs/glossary_decisions.md`. |

## Reproduction and verification

Run with Python 3.8 32-bit and UTF-8 output:

```text
py -3.8-32 tools/record_psp_0413_sources.py
py -3.8-32 tools/fix_psp_0413.py
py -3.8-32 tools/verify_psp_0413.py
py -3.8-32 tools/verify_text_build.py 0.4.13
```

The builder preserves existing versioned images. `psp_spirit_footer.py`
supplies the same 21 instruction changes to incremental and clean builds.
The objective working files and commit-safe English copies are updated;
their review fingerprints include the narrowly reviewed wording correction.
Chapter-card metadata schedules the three redraws in future builds.

Native MIPS verification reproduces the old Spirit Search collision and
checks 99 corrected cases: all 32 Spirit Command names at costs 1, 70 and
150, plus unlearned, unknown and unavailable commands. Every case executes
the real six-cell drawing routine and native font width functions. Names,
brackets and costs do not overlap or spill into the next cell.

The Level Up check executes the native six-row formatter, verifies separate
256-byte buffers, then passes its actual row pointers to the native drawing
routine. All six skill rows, arrows and upgraded levels fit without overlap.
This is a controlled fixture with supplied skill data and intercepted GPU
draw calls, not a battle playthrough. The narration buffer/timing regression
also passes. The native text readback resolves 1,763 BOOT references and all
1,580 English names correctly.

All 32 disc files pass byte-for-byte ISO readback. Only BOOT, EBOOT, MAP and
PACKMAPC2 differ from 0.4.12. The two changed script blocks retain their
original sector budgets, command bytes and every other string. Title atlas
palettes, non-title pixels and all unlisted archive regions remain exact.
The new defeat sentence measures 263 pixels against the 352-pixel limit.

An isolated emulator profile at `work/build/psp_0413_test` fresh-boots the
candidate. `verify_psp_0413_runtime.py` checks all 21 loaded footer words and
the relocated Level Up buffer/stride. The supplied reports and extracted
title preview are in `work/ui/psp/0.4.13`; fresh-boot capture comes directly
from PSP VRAM. Actual battle-screen visual acceptance and physical PSP
validation remain pending. The user's normal emulator profile was untouched.

Local image: `work/output/SRWMX_EN_0.4.13.iso` (1,317,414,912 bytes).
SHA-256: `e30101fef36588b70f0142345677382bb9238300e23aca16324d2080d4022d19`.
Evidence: `work/output/psp_ui_0.4.13_{verification,execution,runtime}.json`.
This build has no GitHub release authorization; public releases remain 0.4.12.
