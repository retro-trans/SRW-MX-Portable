# Battle-animation caption correction — 2026-10-14

The screenshot labels translate as **Assist Attack** and **Simultaneous Attack**.
Assist Attack follows the refreshed Akurasu MX Pilot Abilities terminology and
matches the existing menus. Simultaneous Attack retains the existing project
translation; its native banner displays **Simul. Attack** for readable lettering.

These white/blue labels are part of the untagged native battle HUD atlas. The
previously translated TX48/P2IG banners serve a separate map interface and did
not replace these animation captions. Both PSP and PS2 contain the same Japanese
captions at the same atlas coordinates, despite different atlas dimensions.

`tools/patch_battle_banners.py` changes only the indexed pixels in two 84x24
rectangles: Assist Attack at `(0,152)-(84,176)` and Simultaneous Attack at
`(84,128)-(168,152)`. It retains the palette, dimensions, adjacent Counter,
Jammer, Support Attack and Defend labels, and every other resource byte.
The rendered English uses a 13px cap height without horizontal distortion;
the unabbreviated second label would fit only at an 8px cap height.

The PSP full builder and both PS2 build paths apply the correction. Historical
PS2 regression normalization reverses only the recorded banner rectangles and
checks that reapplying the guarded patch reproduces their exact bytes.

`tools/build_battle_banners.py` creates local v0.4.34 candidates from the exact
published v0.4.33 images. The complete source SHA256 must match the downloaded
release manifest. The streamed transform changes only these rectangles and
the regenerated native title version. A complete output hash, native asset
readback, preserved file extents and sizes, and PS2 ISO9660/UDF agreement verify
the final disc. The actual output images must display v0.4.34 and the credit.

Translation: `work/translation/en/ui/battle_banners.en.json`.
Evidence: `work/output/{psp,ps2}_battle_banners_0.4.34_verification.json`.
Actual ISO previews: `work/ui/{psp,ps2}/battle_banners_0.4.34/iso_readback/`.
Fresh in-game visual validation remains pending; no GitHub release was requested.
