# PS2 font and battle UI fixes — 0.1.11

The PSP opening remains the selected opening. This build changes only native
font drawing, UI text references and Pilot Stats layout in the executable.
The seven scenario/portrait resources are byte-identical to 0.1.10. It uses
the existing native 4x font atlas; emulator texture replacement is disabled.

## Font proportions

The previous width policy enlarged a 20-by-30 dialogue cell to 30 pixels
wide. The game's line fitting could then compress that enlarged text back
into the dialogue box while retaining its 30-pixel height. Latin now uses
the smaller native cell dimension in both axes. Menu cells that were already
square retain their size. The native 12-by-24 numeric style denotes half-width
ASCII spacing, rather than a smaller font. It retains its 24-pixel height and
uses the Latin atlas's own digit advances. Glyph baseline, descender guards and source shapes
are unchanged. Non-Latin glyphs retain the original native cell geometry.

## Labels and spacing

The remaining short UI labels were skipped by the earlier general port where
the PSP used different long and abbreviated translations of the same term.
This patch selects the existing compact terms for these narrow PS2 fields.

| Field | English label |
| --- | --- |
| Unit commands | Move, Status |
| Unit repair cost / pilot personality | Repair, Type |
| Combat stats | Mel, Rng, Acc, Eva, Skl, Def |
| Spirit Commands heading | Spirits |
| Terrain heading | Ter |
| Terrain movement-mode heading | Mv |
| Air / Land / Space / Water / Underground | A / L / Sp / W / U |
| Weapon power / accuracy | Power / Hit |
| Weapon support marker | As |
| Weapon footer | Will, EN Cost, Critical, Skill |

The Pilot Stats name field starts at native X=212 and allows 76 pixels.
The opening parenthesis moves from X=268 to 292, the cost starts at 306,
and the closing parenthesis moves from 318 to 346. All six rows use these
positions. Names wider than 76 pixels scale uniformly in both axes; their
Y position compensates for the atlas baseline. The temporary font size is
restored after drawing, so other labels are unaffected.

## Reproduction and evidence

Build with `python tools/fix_ps2_ui.py --build`. The build preserves earlier
ISOs. `tools/verify_ps2_ui.py` executes the real native measurement and fit
wrapper and checks the cost columns; `tools/verify_ps2_font.py` checks sprite
geometry, widths, atlas guards and Japanese fallback paths. The existing
campaign, balance, portrait and Prologue regression checks also run.

Prepared resources: `work/build/ps2/ui_fix_0.1.11/`.
ISO and reports: `work/output/`.
In-game screenshots and layout details: `work/ui/ps2/ui_fix_0.1.11/`.
No GitHub release is authorized for this build.

Final candidate: `work/output/SRWMX_PS2_EN_0.1.11.iso`, 4,663,255,040 bytes.
SHA-256: `7438b0574cb07c97bd46948b47e0d060fadc269392d90a8fa0a53bc248c7312b`.
PCSX2 2.8.2 visually confirms the PSP Wolf 1 opening, researcher radio
dialogue with corrected proportions, and English Move/Spirit/Status commands.
Native screenshots are in the evidence folder, with their hashes and layout
fields in `layout.json`. The final Unit Stats, Pilot Stats and Weapon Data
pages still need visual confirmation: controller input in the isolated test
profile was unreliable. Their patched labels and Spirit name/cost geometry
pass native execution checks; these checks do not substitute for screenshots.
