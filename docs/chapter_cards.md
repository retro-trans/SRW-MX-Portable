# Native chapter-card lettering

Chapter titles are pre-rendered bitmaps in `PACKMAPC2_ADD.BIN`, separate from
STATIC2's scenario strings. They appear after a stage's opening dialogue.
Build 0.4.2 covers all 67 scenario titles, including both starting routes,
route branches, later stages, the hidden stage and the final stage.

## Coverage and archive layout

There are 205 title atlases: 69 primary packages containing two copies each,
and 67 additional matching copies. Two primary packages are Pursuer
placeholders; their artwork is translated too. Of the 205 copies, 160 contain
Japanese lettering and are translated, while 45 already have English lettering
and remain byte-for-byte unchanged.

Primary pixels begin at `0x145c480`, with package stride `0x42800`. The second
copy is at primary + `0x30c00`. Each package also contains two background/logo
textures, which are preserved. The additional series starts at `0x2647c00`,
stride `0x10800`. Its first atlas is another Pursuer placeholder; subsequent
atlases correspond to primary indices 0–65. Primary index 68 is the hidden
stage, corresponding to scenario record 66. It has two copies.

Each atlas is 256×256, linear 8-bit indexed pixels. The preceding 1,024 bytes
are its RGBA palette. Palette indices differ between titles and cannot be
interpreted directly as gray levels. English masks are mapped to the nearest
original opaque palette color; every palette byte remains unchanged.

Only the first 52 rows of translated atlases are edited. All other pixels,
Chapter lettering, digits, animation, background, geometry and UV coordinates
are retained. The displayed chapter number is assembled separately from the
atlas's sample number. No emulator texture replacement is used.

## Translation and reproduction

`work/translation/en/ui/all_chapter_cards.json` records every copy, title,
scenario association, palette hash and accepted source-title hash. Wording
follows existing scenario translations and Akurasu's MX Portable flow chart.
Three source-faithful clarifications are recorded in `docs/glossary_decisions.md`
and `work/glossary/decisions.json`. Existing English artwork is preserved.

Genei LateGo Medium is rasterized at 4× and filtered into the native title slot.
Every translated title fits at 20 px, using one or two balanced lines. Proper
phrases such as La Mu and Getter Robo stay together. All ink fits within
248×48 pixels inside the 256×52 rectangle, preserving complete descenders.
English preview sheets are `work/ui/chapter_cards_0.4.2_00.png` through `_02.png`.

```sh
python tools/patch_chapter_cards.py work/output/SRWMX_EN_0.4.1.iso 0.4.2
```

The guarded patch accepts original title art and the exact released 0.4.1
Super card. It refuses an existing output and verifies every unchanged archive
range. After writing, it reopens the ISO and hashes the other 31 ISO files;
all are unchanged from 0.4.1, including dialogue, fonts, battle data and code.
Verification: `work/output/chapter_cards_0.4.2_verification.json`.

The native Stage 1 card is checked in isolated PPSSPP with texture replacement
disabled. A separate two-line caption probe checks the native renderer's title
bounds; it is not a playthrough of that later stage. Full campaign playthrough
and physical PSP testing remain pending.

## Earlier 0.4.1 work

Build 0.4.1 translated only Stage 1 Super, at pixel offset `0x14e1480`, editing
its first 40 rows. The original atlas was matched against the live GPU image.
`tools/patch_screenshot_text.py` also translated Kaine's three closing-message
records. These changes are retained in 0.4.2. The original 0.4.1 screenshot and
verification report remain available as historical evidence.
