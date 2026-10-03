# Native chapter-card lettering

The stage 1 Super title is a pre-rendered bitmap in `PACKMAPC2_ADD.BIN`, not the
scenario title string in `STATIC2_ADD.BIN`. It appears after the introduction's
dialogue and before the battle-map dialogue. Its texture bypasses the small
texture-upload wrapper used by the normal interface.

The stage 1 Super atlas starts at pixel offset `0x14e1480`. It is a linear
256×256 image with one byte per palette index. The preceding 1,024-byte RGBA
palette starts at `0x14e1080`; index 0 is transparent, and indices 1–255 are
gray levels with PSP alpha 128. The first 40 rows hold the stage title.
Other rows contain animated Chapter lettering, digits and effect artwork.
The displayed Chapter number is assembled separately; the atlas's baked
`Chapter.03` sample does not determine the stage number.

The original first 65,536 pixels have SHA-256
`3210d1e3571d759e7935ef33590c3e76e330177796b4acd0feb74fc8ecaaee19`.
They were matched byte-for-byte against the image used in the live chapter-card
display list. The comparable stage 1 Real atlas starts at `0x145c480`.
Its title is outside this screenshot request's scope.

Build 0.4.1 replaces only the Super title rectangle with **Visitors from the
Beyond**, using the existing glossary/scenario wording from Akurasu. Genei
LateGo Medium is rasterized at 4× and filtered to the original bitmap's slot.
The original atlas dimensions, palette, UV coordinates, card background and
animation are retained. This is an ISO asset patch; it requires no emulator
texture replacement.

Run `tools/patch_screenshot_text.py <0.4.0 ISO> 0.4.1` to reproduce the build.
It also replaces the identical Kaine save-message line at `end_mes:21`, `:26`
and `:31`. English is read from the safe `.en.json` translation; Japanese source
is read from the user's ISO in memory. It checks all other 202 script blocks,
the unchanged atlas regions and the finished ISO's patched files.

Coordinates and translation data are in `work/ui/chapter_card.json` and
`work/translation/en/ui/chapter_cards.json`. The original and translated atlas
previews are `work/ui/chapter_card_atlas_before.png` and
`work/ui/chapter_card_atlas_after.png`.

The finished 0.4.1 ISO was tested in an isolated PPSSPP profile with texture
replacement disabled. The translated atlas was found at live address
`0x09720c80` and matched the patched file pixel-for-pixel. The in-game screenshot
is `work/ui/chapter_card_0.4.1.png`. SHA-256 comparisons confirmed that only
MAP_ADD and PACKMAPC2 file contents differ from 0.4.0; the other 30 ISO files
are unchanged.
