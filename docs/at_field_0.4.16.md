# Native battle caption: PSP and PS2 0.4.16

The reported `A.T.フィールド` battle-animation caption now reads **AT Field**
on both platforms, matching Akurasu's MX Mech Abilities entry. The glossary
was refreshed with `tools/akurasu_terms.py` on 2026-10-07. The translated
yellow map banner was a separate copy; editing it did not affect this white
caption.

The missing copy is in the shared, untagged battle HUD atlas inside STATIC,
not in the animation archive or the game dialogue. PSP stores a linear
512×512 indexed image at STATIC2_ADD offset `0xF4400`, with a 256-colour
palette at `0xF4000`. PS2 stores a linear 1024×256 indexed image at STATIC
offset `0x134800`, with a native CSM1 palette at `0x134400`. PS2's wider
row stride must be used when editing these pixels.

The caption rectangles are `[8,304,120,328]` on PSP and
`[424,48,536,72]` on PS2. The immediate adjacent Virus caption is outside
these rectangles. Each edit spans 24 rows of 112 bytes. The English uses
an 18px cap height, natural width, white body, black outline and blue
shadow, centred within the same caption area. Both palettes, coordinates,
other captions, fonts, database records and animation files are preserved.

`tools/patch_at_field.py` applies and verifies the same edit for future full
PSP and PS2 builds. `tools/build_at_field_0416.py` builds the local candidates
from PSP 0.4.14 and PS2 0.4.15 without relocating any disc resources. Both
use 0.4.16; the existing PS2 0.4.15 test image is preserved.

Validation compares every disc resource and every byte outside the 24
declared pixel spans. The PS2 resource also passes independent UDF readback.
Before/after decoded previews are saved under `work/ui/<platform>/at_field_0.4.16`.
An isolated PSP fresh boot finds the entire modified HUD atlas, including
the unchanged palette, byte-identical to the candidate ISO in native game
RAM. This proves that the candidate actually loads the translated asset.
Actual A.T. Field activation during battle and physical console checks
remain pending. No GitHub release was requested or created.

Local images:

| Platform | Image | SHA-256 |
|---|---|---|
| PSP | `work/output/SRWMX_EN_0.4.16.iso` | `6cf33af6f0a77342e22e53130d9186fb428548808ff980156602fae83edb3867` |
| PS2 | `work/output/SRWMX_PS2_EN_0.4.16.iso` | `7cce7bc0c5787218a9b3ff008918295e7618035500bd9f1cfc3b22a2fa44ba08` |

The earlier glossary and gameplay corrections remain intact. The historical
PS2 checks can normalize only this independently verified caption edit when
comparing against older portrait or asset fixtures; undeclared changes fail.
