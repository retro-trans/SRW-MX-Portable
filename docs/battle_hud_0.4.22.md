# Battle HUD translations 0.4.22

The reported Japanese labels are pre-rendered in the untagged battle HUD atlas,
separate from the translated WND and map-banner assets. This correction updates
the matching copies on both editions.

| Original | English | Meaning |
| --- | --- | --- |
| 気力 | Will | Pilot morale, displayed beside the value on both sides. |
| 武 | WP | Weapon accuracy reduced, matching the existing menu/help abbreviation. |
| 能 | ST | Pilot stats reduced. |
| 動 | MB | Mobility reduced. |
| 装 | AR | Armor reduced. |
| 行 | DS | Cannot act. |
| 移 | MV | Movement reduced. |
| 防御 | Defend | The battle-animation defensive action caption. |

The translations follow the current glossary and UI terminology. The Akurasu
MX term reference was refreshed on 2026-10-10 during the preceding review.
Tapp's already translated battle dialogue remains unchanged.

## Asset layout and reproduction

PSP uses the 512×512 indexed HUD image at STATIC2_ADD.BIN pixel offset
`0xF4400`, with its palette at `0xF4000`. PS2 uses the 1024×256 indexed image
at STATIC.BIN pixel offset `0x134800`, palette `0x134400`, with CSM1 palette
addressing. The coordinate and row stride differences are handled explicitly.

Only nine rectangles are changed on each platform. Will is centered inside
its existing badge interior. The six tiny status tiles use legible two-letter
bitmap glyphs; their frames remain intact. Defend uses natural-width lettering
with the original white body, black outline and blue shadow. No text is squeezed
horizontally. HP/EN bars, shields, numbers, other captions, palettes and atlas
dimensions are preserved, including the earlier AT Field translation.

`tools/patch_battle_hud.py` guards each rectangle against the original artwork
or the exact new English artwork. It preserves every byte outside those
rectangles and is idempotent. Both full-build paths invoke it after AT Field.
`tools/build_battle_hud_0422.py` creates the local 0.4.22 candidates over 0.4.21
by editing the existing file extents. It refuses to overwrite a versioned ISO.

## Verification

Before/after images and exact rectangle bounds are in
`work/ui/{psp,ps2}/battle_hud_0.4.22/`. The reported screenshots are preserved
in the PSP subfolder's `reported/` directory. Both platform previews were
inspected for legible lettering and clipping.

Reports are `work/output/psp_battle_hud_0.4.22_verification.json` and
`work/output/ps2_battle_hud_0.4.22_verification.json`, with English source records
under `work/translation/en/{psp,ps2}/battle_hud_0.4.22.en.json`.
Checks read back every ISO file and independently compare the entire disc
outside the permitted pixel spans. PS2 also reads STATIC through UDF.
All executable, dialogue, script and other resource bytes are unchanged;
no gameplay logic or pointers are edited. The earlier corrections are retained.

These are local incremental candidates. They do not include the broader
source-only campaign proofreading. In-game visual confirmation and physical
hardware testing remain pending. No commit or GitHub release requested.
