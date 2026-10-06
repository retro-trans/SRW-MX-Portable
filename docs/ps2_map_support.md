# PS2 0.1.15 map support captions

Build with `python tools/fix_ps2_map_support.py --build`. Input is the
preserved 0.1.14 setup/save candidate; output is
`work/output/SRWMX_PS2_EN_0.1.15.iso`.

The user's map screenshot contains yellow Assist Attack and red Support
Attack labels. The same bank also contains blue Support Defend. Terms
follow the refreshed [Akurasu MX Pilot Abilities](https://akurasu.net/wiki/Super_Robot_Wars/MX/Pilot_Abilities)
and the existing PSP UI abbreviation policy:

| Native map image | English caption | Color |
|---|---|---|
| M_65 | Support Atk | Red |
| M_66 | Support Def | Blue |
| M_67 | Assist Atk | Yellow |

These are images in MAP section 16, separate from the menu string pool.
The three 128×32 PSMT4 images have 2,048-byte payloads. The native upload
interprets the bytes as a 16×32 PSMCT32 transfer, so treating them as
linear nibble rows scrambles the letters. `tools/ps2_map_label_pixels.py`
expresses the GS address permutation as bit arithmetic. All 4,096 pixel
positions match an independent check against [PCSX2 GS address tables](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSTables.cpp).
The reference C++ file remains in ignored research files and is not bundled.

English captions use the original palette, natural Bahnschrift Bold
Condensed proportions, a shared 26px font size and baseline 24. Text is
centered on the original image's center, with an outline and antialiasing.
No horizontal rescaling is used. Existing UV/image dimensions and counters
remain intact. All headers, palettes, padding, script commands, maps,
deployment tables and all other resources are preserved. The executable
is byte-identical to 0.1.14, retaining its native 4x dialogue/UI VWF.

The pixel verifier checks exact changed ranges, source and output hashes,
native image-bank offsets, decode/encode round trips, preserved palette
headers and every other prepared resource. Existing UI execution evidence
is carried forward explicitly because its executable/data inputs are
unchanged. The campaign/font/difficulty native verifier also runs against
the prepared build, and disc packaging checks all 37 files through both
ISO9660 and UDF.

Actual user capture and decoded asset previews are in
`work/ui/ps2/map_support_0.1.15/`. `support_before_after.png` is an asset
comparison, not an emulator screenshot. In-game confirmation of the new
captions remains pending. Start the new ISO with a fresh disc boot; an old
emulator save state can retain old map textures. Memory-card saves remain
compatible. No GitHub release or push is authorized.

Final ISO: 4,663,267,328 bytes. SHA-256:
`ecdaa12f194f5db0a9a6b0abefde5bcec4240047311254332e9f22e1db452360`.
All 37 disc resource readbacks pass, including the three English map
captions in both ISO9660 and UDF MAP archive reads.
