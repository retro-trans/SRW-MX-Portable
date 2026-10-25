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

## God Shadow — 2026-10-15, local v0.4.36

The additional screenshot identifies God Shadow, matching Akurasu's MX Mech
Abilities entry and the existing map-banner term. Both native battle HUD atlases
store this label at `(240,48)-(348,72)`. The English uses an 18px cap height,
retaining the original white, blue and black palette without horizontal scaling.
The right boundary excludes the adjacent red EN label; a palette-content guard
rejects a rectangle that includes red lettering. The first wider crop was
discarded before delivery, and its incomplete images and records remain under
`work/build/god_shadow_0.4.36_crop_attempt/`.

Local candidates use verified v0.4.35 images, preserving the Parts alignment,
earlier crash fix and existing Assist/Simultaneous Attack artwork. Actual ISO
readback checks all three captions and exact v0.4.36 native title footers.
Recorded historical caption subsets are reapplied by ID so older preservation
fixtures do not acquire newer artwork during their normalization.

## Critical and Shield Defense — 2026-10-19, local v0.4.39

The reported stacked battle labels are **Critical** and **Shield Defense**.
The second term matches a fresh Akurasu MX Pilot Abilities refresh, cached
under `work/source/battle_banner_terms_0.4.39/`; Critical matches the existing
menu/map terminology. Both editions retain these untranslated native captions
in the shared atlas even though their other UI text uses English.

Critical occupies `(240,120)-(336,144)` and Shield Defense occupies
`(240,144)-(348,168)`. The full English labels fit at 18px and 16px cap heights
without horizontal scaling. Region guards reject overlap and red lettering
inside the Shield Defense rectangle. Support Defend to the right of Critical
and the red Insufficient Will label to the right of Shield Defense remain exact.

The regular builders already call `patch_battle_banners.py`, so extending its
registered terms covers subsequent full builds as well as the local incremental
v0.4.39 candidates. Those candidates use the exact public v0.4.38 sources and
change only the registered caption pixels and regenerated native title version.
All previous caption translations are retained. Fresh in-game display remains
pending; the screenshot does not authorize another GitHub release.

Screenshot and annotated native regions:
`work/ui/battle_banner_2026_10_19/`. Prepared and actual ISO previews:
`work/ui/{psp,ps2}/battle_banners_0.4.39/`.

## Distortion Field and TE Sphere — 2026-10-21, local v0.4.40

The reported labels match Akurasu's MX Mech Abilities names **Distortion Field**
and **TE Sphere**, refreshed into `work/source/battle_banner_terms_0.4.40/`.
Both terms were already translated in the menus/map banners; their native
battle-animation artwork was separate. Critical was corrected in local
v0.4.39 and remains included in this build.

Unlike the earlier registered captions, these use different atlas coordinates:

| Label | PSP rectangle | PS2 rectangle |
|---|---|---|
| Distortion Field | `(0,280)-(192,304)` | `(416,24)-(608,48)` |
| TE Sphere | `(8,376)-(104,400)` | `(424,120)-(520,144)` |

The registry now resolves platform-specific rectangles before rendering,
overlap checks, preservation checks and native ISO readback. Both full English
labels use an 18px cap height with the existing outlined white/blue style.
The first exploratory Distortion Field crop was too wide and was corrected
before any ISO was built. A regression check verifies that the neighboring
pilot-SP and electric-attack captions remain byte-for-byte identical on both
editions. All four caption regressions pass, including historical subsets,
red-letter boundaries and rejection of unrecognized source artwork.

Local v0.4.40 candidates inherit the exact verified v0.4.39 images and regenerate
the native title version and credit. No release is authorized for this build;
the current public release remains v0.4.38. Fresh in-game display is pending.
Reported and annotated screenshots are in `work/ui/battle_banner_2026_10_21/`;
prepared and actual ISO previews are in
`work/ui/{psp,ps2}/battle_banners_0.4.40/`.
