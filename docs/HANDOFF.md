# Local PSP v0.4.38 — unit rename fields

Completed 2026-10-19 for the user's latest-public PSP screenshot. Native
initialization reproduces the garbled upgraded Cerberus name in public
v0.4.33: Name and Reading were packed at a 23-byte stride, while the translated
default was 16 full-width characters. The editor now uses 31 bytes for Name
and the remaining 17 for Reading within its existing 48-byte area. All cursor,
reset, edit and export paths use the new bounds. Controls at +0x644 and the
32-byte save fields retain their original layout. Both PRX jump relocations
for the new post-load terminator guard are checked.

The editable default becomes **Cerberus Ignite**, using Akurasu's Pilot
Database spelling to fit 15 glyphs plus NUL within 32 bytes. The separate
Mech List database terms are unchanged; the UI-only exception is documented.
The old overlong saved default loads safely into the corrected editor.

PSP: `work/output/SRWMX_EN_0.4.38.iso`, SHA256
`9adb8ad55560d6bd2380247d0f0394fd52a03d28982e8e081d40201e2ce04798`.
Contains both approved Ritsu corrections. Only their two existing dialogue
slots, the corrected BOOT/EBOOT, native v0.4.38 footer and required ISO metadata
change over v0.4.36. Expected streaming image hash and actual complete ISO
hash agree; both executable aliases and actual story/footer read back exactly.
Native tests cover all defaults and saved names, maximum-size custom names,
legacy names, editing both ends/middle, control guards, underline bounds and
relocations. A first validator compared the map block with a reused footer
variable; it was corrected and the same candidate passed full read-only
verification. No image bytes were altered for that validator repair.

Tools: `tools/fix_psp_rename.py`, `tools/verify_psp_rename.py`,
`tools/build_psp_rename.py`; the regular PSP builder includes the correction.
Details: `docs/psp_rename_fix.md`. Evidence:
`work/output/psp_rename_0.4.38_verification.json`.
Fresh in-game visual acceptance remains pending. No GUI resumed and no
release published. Latest PS2 remains local v0.4.37; its editor is unchanged.

# Local PS2 v0.4.37 — complete PSP stage 28 port

Ported PSP Chapter 28, **Tragedy Beneath the Moon**, to PS2: opening `i055b`,
battle `s0550`, and aftermath `i055a`. All 1,894 PSP commands and their operands
are retained exactly. All 1,007 translated string slots read back in English,
including the two approved Ritsu revisions. No portrait-cache adaptation is
needed. The exact 34-unit PSP deployment replaces one changed flag at offset
260 of native deployment 148 (chapter 7, group 8). PS2 map 460, terrain/heights,
unit stats, balance options, the other 200 scenes and prior fixes are preserved.

PS2 test image: `work/output/SRWMX_PS2_EN_0.4.37.iso`, SHA256
`4d0a6a8446812b5fa99dae5853316d9199b962969e4e4401aca5e9fe830439c1`.
Both filesystems read identical changed assets. Complete disc comparison permits
only the map/executable and registered map-length metadata changes. Native tests
load all nine stage-28/29/30 scenes, verify the three deployments, retain campaign
progression and stage-28 numbering, and pass all 42 v0.4.37 title-footer cases.
Three regression tests pass. A regular full-story rebuild reproduces the image's
203 scene blocks and executable exactly (51,146 translated slots, zero changes).

`tools/ps2_stage28.py` is called by the normal PS2 story builder; its three
scenes use PSP translations and source ordering on future builds. The PS2
source loader falls back to the exact 59 reviewed inputs if the old transient
`campaign_0.4.9_inputs.json` report was cleaned. The incremental builder is
`tools/build_ps2_stage28.py`; details are in `docs/ps2_stage28_port.md`.
Evidence: `work/output/ps2_stage28_0.4.37_verification.json` and
`work/output/ps2_stage28_0.4.37_full_builder_check.json`.

The first prepared readback attempt was archived before any ISO was created:
its validator compared decoded game punctuation with unencoded ASCII. The
corrected validator encodes expected text first; no translation was altered.
Full in-game stage-28 clear/transition remains pending. No GUI resumed and no
release requested or published. PSP's latest local ISO remains v0.4.36; its two
approved Ritsu corrections are in shared sources awaiting a PSP rebuild.

# Local shared v0.4.36 — God Shadow banner

Completed 2026-10-15. Translated the separate native God Shadow animation
caption on PSP and PS2, following Akurasu's MX Mech Abilities term. The HUD
rectangle is `(240,48)-(348,72)`, with 18px white/blue outlined lettering.
The right boundary preserves the adjacent red EN label. A first wider crop
was discarded before delivery; its incomplete images/reports are retained
under `work/build/god_shadow_0.4.36_crop_attempt/`.

PSP: `work/output/SRWMX_EN_0.4.36.iso`, SHA256
`30491e650639d576397202cf8ef459dbdb9625d3dd5d5eb7c2c507979c5be7a1`.
PS2: `work/output/SRWMX_PS2_EN_0.4.36.iso`, SHA256
`3637bebd8c378035d83b618986fdde1d58dc48504b4d1eacecf26554978f5ca8`.
Verified exact v0.4.35 baseline hashes, complete output hashes, unchanged file
extents/sizes, native caption pixels, actual v0.4.36 footers and PS2 ISO9660/UDF
readback. Existing Assist/Simultaneous Attack pixels and Parts fixes remain
exact. Three regression tests cover both platforms' EN boundary, unknown
artwork rejection and historical caption subsets; 42 PS2 title-state cases pass.
Evidence: `work/output/{psp,ps2}_battle_banners_0.4.36_verification.json`,
`work/output/god_shadow_0.4.36_regression_tests.log`, and
`work/ui/{psp,ps2}/battle_banners_0.4.36/iso_readback/`.
Fresh in-game display remains pending. No v0.4.36 release was requested.
The source commit is local: GitHub denied the push with HTTP 403 for the
currently authenticated account. Local ISOs and verification records are ready.

# Local shared v0.4.35 — Parts window alignment

Completed 2026-10-15. PSP equipped-name origin moves from panel.x+110 to
panel.x+80. Names keep full wording; a guarded native draw wrapper temporarily
fits only names wider than 162px and restores the display font dimensions.
All 37 descriptions are rewrapped. Native execution measures at most 196px
within the PSP 200px area, with four rows maximum. PS2's equipped names already
use separate rows; native font advances rewrap its descriptions to at most
257px within the 258px budget, with five rows maximum.

PSP: `work/output/SRWMX_EN_0.4.35.iso`, SHA256
`c65aadbbba1f85256e5d6b1fb9dc5a8d59e7cee10f4629616f5a02b95bc7ffd9`.
PS2: `work/output/SRWMX_PS2_EN_0.4.35.iso`, SHA256
`8001af3ec9cd9140ef36bfca57efae5ef086234c4d13b6162358e41d9d4c968c`.
Complete ISO hashes and changed-resource readback pass. Both native v0.4.35
footers and v0.4.34 battle-banner artwork pass. PSP BOOT/EBOOT resolve to the
same appended, independently checked PRX. All other resource allocations and
bytes remain exact. PSP retains all 4,550 earlier sentence IDs; PS2 preserves
every protected sentence and numeric gameplay section within its fixed heap.
PSP full non-story readback and retained native Parts pointer regression pass;
all 42 PS2 title-state cases pass. Records are in
`work/output/{psp,ps2}_parts_layout_0.4.35_verification.json` and
`work/output/parts_layout_0.4.35_native_verification.json`.
Source/tool details: `docs/parts_layout.md`.
Fresh in-game display and live equip/exit checks remain pending. No release
requested for v0.4.35. Previous user-stopped GUI checks were not resumed.

# Local shared v0.4.34 — battle-animation banners

Completed 2026-10-15 for screenshots supplied 2026-10-14. The separate blue/white
native HUD captions now display Assist Attack and Simul. Attack (full term:
Simultaneous Attack). Both platforms use the same two 84x24 atlas rectangles.
The existing translated map banners did not cover these animation assets.
Complete streaming source/output hash verification, exact ISO caption readback,
unchanged file extents and sizes, retained palettes, idempotence and exact new
native title footers pass. PS2 reads both changed assets through ISO9660 and UDF.
Everything outside the caption pixels and new version footer remains exact.

PSP: `work/output/SRWMX_EN_0.4.34.iso`, SHA256
`d1d7805027d9532d9083aa46aa720b2647ece97cd94264e26706f444a3571f9e`.
PS2: `work/output/SRWMX_PS2_EN_0.4.34.iso`, SHA256
`50b9c7e2750b11d503ea32fe41f447e8185b024784b9c3d8f75c5472c4d7c3dd`.
Evidence: `work/output/{psp,ps2}_battle_banners_0.4.34_verification.json`.
Previews: `work/ui/{psp,ps2}/battle_banners_0.4.34/` and `iso_readback/`.
Source/tool details: `docs/battle_banners.md`.
PSP/PS2 full builders now include the guarded correction; release verification
rejects untranslated caption artwork. No release requested for v0.4.34.
Fresh in-game visual checks remain pending. Output reports for older releases
were cleaned before this task; public v0.4.33 manifest/tests were recovered to
`work/build/battle_banners_baseline_0.4.33/` and their exact ISO hashes verified.
The historical prepared v0.4.33 PS2 assets and font metadata remain available.

# Published shared v0.4.33 — 2026-10-13

Published: https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.33.
Source/tag snapshot: `b21d96037f9bb01c7afc994782d6628bb3a242d5`.
Restored 1,705 English battle quotes lost during v0.4.29 source preparation;
PSP v0.4.32 had retained Japanese for these rows. PS2 retained those English
quotes but needed remaining terminology refreshed. All 10,227 source rows
are complete; builds reject missing translations and export rejects erasure.
Historical audit found no further English loss in the 38 changed English
JSON files shared with the v0.4.1 snapshot.

Final PSP SHA256:
`e4f5d968b3a3af9e1aef44fdb828b2bdadb745828de1714f4a21fd4990f144be`.
Final PS2 SHA256:
`192ee9cd9e6d59e9b3d34e0715ebe0b6acb3d72ceccffe1ffadff27f9f5a92e2`.
The first PS2 candidate was superseded before publication: native battle
captions use slash line breaks, not the story marker. Its image and package
are archived under `work/build/ps2/battle_marker_attempt_0.4.33/`.
Only the final corrected image and four verified patches were published.

All 103,600 battle-caption references pass exact source readback and marker
checks (PSP 51,892; PS2 51,708), with zero Japanese fallbacks or mismatches.
Complete story, PSP UI/database/library, chapter cards, native Parts-menu
regression, PS2 file preservation and 42 title-state checks pass. Both actual
native footers identify v0.4.33. Nine new regression tests and 32 Retro Trans
Tools release/catalog tests pass. All four full and exact v0.4.32 upgrade
patches pass complete decode/hash round trips.

All 14 uploaded asset sizes and GitHub SHA256 digests match local artifacts.
Retro Trans Tools catalog workflow 38384738042 succeeded. The live catalog
manifest matches the release; both originals and v0.4.32 have direct routes,
and v0.4.29 / v0.4.12 upgrade chains reach v0.4.33.
Evidence: `work/output/release_0.4.33_build_tests.json`,
`work/output/release_0.4.33_publication_verification.json`, and
`work/output/release_0.4.33_catalog_verification.json`.
Publication summary: `docs/releases/v0.4.33_validation.json`.
Fresh emulator playthrough, physical-console and live PSP Parts equip/exit
checks remain pending. Previously stopped GUI checks were not resumed.

# Published shared v0.4.32 — 2026-10-13

PSP v0.4.32 is rebuilt and verified with
all reviewed story text and the Parts-name buffer fix. Exact SHA256:
`866a11ba283c3e239fb135d365a9e55cf3b1461861d40659166d852d6becad87`.
PS2 refresh preserves v0.4.30's native fixes and extra scenarios, replaces 2,091
story slots, and reflows 362 changed lines. Three source-checked shorter PS2
phrasings are guarded by source hashes in `ps2/script/reviewed_layout.en.json`.
Library refresh independently checks gameplay/ELF preservation and native widths;
26 description entries and 277 newly written rows pass. Shared Quattro quote
uses 3 stored strings with 11 verified native references. Native scenario,
deployment, campaign/save, font and database getter checks pass on prepared data.
Disc rebuild reuses original allocations where resources fit and appends enlarged
resources to remain below single-layer capacity. The PS2 image is now verified across all 37 files and both ISO9660/UDF
directory views: 4,659,449,856 bytes; SHA256
`983f6b30f73f03fc16b143a8bf576b306d73e6cb36f552a6868dc81fc2bc7833`.
All 42 PS2 title-state cases and both exact v0.4.32 native footers pass.
Current evidence: `work/output/release_0.4.32_build_tests.json`. All four full
and v0.4.29 upgrade patches pass complete Retro Trans Tools round trips.
Both upgrade source hashes match the downloaded public v0.4.29 manifest.
Published: https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.32.
All 14 uploaded asset sizes and GitHub SHA256 digests match local artifacts;
evidence: `work/output/release_0.4.32_publication_verification.json`.
Retro Trans Tools catalog workflow 38295376828 succeeded. Live remote catalog
manifest matches the published release. Direct routes from both Japanese
originals and both v0.4.29 images, plus v0.4.12 upgrade chains, reach v0.4.32.
Evidence: `work/output/release_0.4.32_catalog_verification.json`.
Game-source and final tool snapshot: `22cf2ede2d09bd37440695446a64a52699e27ccb`.

The release includes bare full and v0.4.29 upgrade xdelta patches for both
platforms, Retro Trans Tools metadata, checksums and proofreading HTML reports.
Thirty-two Retro Trans Tools release/catalog tests pass. Current fresh emulator
boot/playthrough, physical-console, and PSP live Parts equip/exit checks remain
pending. The earlier user-stopped GUI checks have not been resumed.

# Screenshot dialogue review — 2026-10-12

Updated Saiga (19:681), Ritsu (21:269), and battle quote q04997. Burai's
20:74 / 21:11 wording was already corrected; Leina 20:326 was retained.
Guarded contributor reassembly, unchanged non-editorial metadata, both font
limits, both affected chapters and all 407 affected-batch battle quotes pass.
Sources feed both platforms; existing ISOs are unchanged. English-only evidence:
`work/translation/en/ui/dialogue_review_2026_10_12.en.json`.
Reports: `work/output/dialogue_review_2026_10_12.html` and updated cumulative
`work/output/chapters01_end_proofread.html`.

# Local PSP v0.4.31 — Parts-menu crash fix

Candidate: `work/output/SRWMX_EN_0.4.31.iso`.
SHA256: 2d30c71d5314a7933624428d0e29765ec4f42c02971c3ee19a92e643a3798eaa.
The 53-byte FA Hyaku Shiki Kai name overflows a 52-byte menu field and changes
the adjacent pointer from 0x8bbf480 to 0x8bbf400. Six name-path references now
use the existing 256-byte temporary row; full name and pointer are preserved
in the native original/fixed regression. Full builder applies fix_psp_parts.
ISO preservation and exact title footer pass; fresh boot observes loaded patch
and version. The user stopped ComputerUse before final equip/exit validation;
do not mark that check complete or resume GUI without permission. Supplied save
is unchanged. No release requested. Later source proofreading remains excluded.
Evidence: `work/output/psp_parts_0.4.31_verification.json` and
`work/output/psp_parts_native_regression_0.4.31.json`.

# Local shared v0.4.30 — 2026-10-12

Both candidates are complete, with all native English chapter cards redrawn.
PSP SHA256: a962bd92f6a5b0a496f1d8b4aa716e8ce1b98d76a33eceb24f003ffcb2cd05b8.
PS2 SHA256: 2f5c0cc6f920ce0fc15de4cca111ad72c0088d8d530b167ff769161aec1d558b.
Actual ISO audits cover 205 PSP and 200 PS2 atlases. Source hashes, duplicate
copies, all other disc bytes, exact native footers and 42 PS2 footer cases pass.
Full builders no longer skip native English titles. See `docs/chapter_cards.md`
and `work/output/{psp,ps2}_chapter_cards_0.4.30_verification.json`.

The user stopped the isolated PSP Chapter 20 live check with Escape; it remains
unfinished. New incoming savedata later replaces the 19-clear fixture with a
21-clear fixture for the FA Hyaku Shiki Kai parts crash investigation. Preserve
historical fixture hashes when comparing tests. No v0.4.30 release is authorized.
Later proofreading/Hau Dragon changes remain source-only.

# Published shared v0.4.29 — 2026-10-11

Published https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.29
at 2026-10-11 12:18:44 UTC. The 12 assets were downloaded and matched byte for
byte, including GitHub SHA-256 metadata. Four full/upgrade patch round trips
passed; exact published v0.4.12 inputs were cross-checked. Release tag points
to 9dc4cb0d6ceea8561f453b41464374adc12b3ecb; built source snapshot remains
8714e03980396e4b5ef07214d3e8fa1d7a4c7782.

Live catalog refresh 38138893977 passed. Automatic routes from both originals
and v0.4.12 reach v0.4.29; PSP v0.4.1 and v0.4.9 reach it through existing
upgrades. Evidence: `docs/releases/v0.4.29_validation.json`. Thirty-two Retro
Trans release/catalog tests pass. The initial refresh exposed that canonical
SHA256SUMS.txt must contain only catalog-required files; its corrected version
and the complete versioned checksum file were reuploaded and verified. Patch
and manifest identities did not change. The package helper now follows this rule.

Later campaign proofreading, Saburota and Hau Dragon changes remain source-only.
Full playthrough and physical-console tests remain pending. Owned emulator tests
are stopped; normal emulator configurations are untouched. No GitHub release is
authorized for a future build without another explicit request.

# Shared v0.4.29 release preparation — 2026-10-11

The user explicitly requested a release. PSP 0.4.29 and PS2 0.4.29 are complete;
PS2 applies the Name caption and exact footer over its historical 0.4.26 image.
The PS2 fresh boot visibly verifies both footer lines at native resolution;
loaded immutable renderer bytes and all hooks match the candidate. Forty-two
title state/phase execution cases pass. Both platforms' title evidence is in
`work/ui/{psp,ps2}/title_footer_0.4.29/title_menu.png`.

Release packaging creates full original-image and exact published 0.4.12
upgrade patches for each edition, with full decoded-output hashes and the
shared Retro Trans Tools manifest. Source snapshot: 8714e03980396e4b5ef07214d3e8fa1d7a4c7782.
Later campaign proofreading/Hau Dragon remain source-only and are explicitly
excluded in the release notes. Publication/catalog verification will be recorded
in `docs/releases/v0.4.29_validation.json`.

# PSP footer placement, local 0.4.29 — 2026-10-11

`work/output/SRWMX_EN_0.4.29.iso` is complete, SHA256
`6e795ed2579cba86f896f819cfe7bb64384557dc4950bfae226225a2ce9b8b5e`.
User requested bottom-right credit/version with no dark panel and accepts a
little logo overlap. The footer uses 14px white outlined text, native screen
box (298,138)-(472,178); the upper-left panel is restored to original pixels.
`tools/title_footer.py` preserves historical layouts, guards the entire title
texture against unknown edits and regenerates this layout for future versions.
The preference is recorded in AGENTS.md.

Fresh-boot native title-menu verification passes and the full loaded title
texture matches the candidate ISO. See
`work/ui/psp/title_footer_0.4.29/title_menu.png` and the footer runtime/build
records in `work/output`. Owned profile
`work/build/psp_title_footer_test_0.4.29`, debugger 45399, is stopped after
verification. User emulator/configuration untouched. This footer-only build
inherits 0.4.28's Name caption. No release requested; later proofreading/Hau
Dragon remain source-only. PS2 live footer placement is still pending below.

# Rename-screen caption, local PSP 0.4.28 — 2026-10-11

`work/output/SRWMX_EN_0.4.28.iso` is complete, SHA256
`5a3697130967dfb1579b5d3446df89b27a6d1055ddccecab37b3f9827b50767d`.
`tools/fix_squad_name_label.py` shortens Squad Name to Name in the shared UI
override 28F910 and both existing PSP executable allocations over 0.4.27,
regenerating the exact footer. Saved names remain unchanged. File/scene and
whole-disc preservation checks pass.

The isolated profile `work/build/squad_name_test_0.4.28` loaded a separate copy
of the incoming save. Native `work/ui/psp/squad_name_0.4.28/rename_name.png`
shows Name with a clear gap before Magnet X. All four save files still match
the incoming fixture. Runtime and build records are
`work/output/psp_squad_name_label_0.4.28_runtime.json` and
`work/output/psp_squad_name_label_0.4.28_verification.json`. The owned test
process is stopped; normal emulator/configuration untouched. No release
requested. Shared source is ready for PS2; no new PS2 build created here.
Later campaign proofreading/Hau Dragon remain source-only.

# PSP title footer readability, local 0.4.27 — 2026-10-11

`work/output/SRWMX_EN_0.4.27.iso` is complete: SHA256
`c3db02c4f8bd84cd8bc39e271112532044843025d02a3a6ec3044df0104734a4`.
It inherits 0.4.25, changing only the title-footer pixels and restoring the old
footer area. `tools/title_footer.py` uses a 14px white two-line dark panel for
PSP versions >=0.4.27, native screen box (55,5)-(229,45). Future builds retain
this layout and regenerate their exact version. Historical checks keep their
original layout.

Native PPSSPP title-menu screenshot and full loaded-texture comparison pass.
See `work/ui/psp/title_footer_0.4.27/title_menu.png` and the platform footer
verification/runtime JSON records in `work/output`. The isolated profile is
`work/build/psp_title_footer_test_0.4.27`, debugger 45397. The owned process is
stopped after verification; the user emulator/configuration is untouched.
No release requested. Later proofreading/Hau Dragon remain source-only.

# PS2 title footer correction, live verification pending — 2026-10-11

The missing footer was reproduced in live 0.4.25. The old PS2 IM #141 target
does not reach the animated title renderer. `tools/ps2_title_footer.py` now
adds a guarded native draw callback at 0x2c1e28, preserves the original call,
and draws two right-aligned lines through a private native font context.
`tools/build_ps2_title_fix.py` completed local 0.4.26 over 0.4.25, restoring
only the registered old static-background footer. Disc readback passes and
`tools/verify_ps2_title_footer.py` passes 42 title-state/phase execution cases.
ISO SHA256:
`9509598ff1efb3b450c5c3e84282c5ed48e5dd29b63b38defbc886ad9f0d5e97`.

The isolated profile is `work/build/ps2_title_footer_test_0.4.26`, PINE 28036.
Computer use was stopped with the user's physical Escape key before the new
candidate could be visually verified. The owned emulator is stopped. Do not
claim title visibility yet. Fresh-boot the actual finished ISO, verify runtime bytes
and capture the title and open menu with texture replacement disabled.
Update `docs/title_footer.md` after confirming layout. Earlier PS2 title
bitmap checks remain historical records; they did not prove live visibility.
No release requested. Later proofreading/Hau Dragon remain source-only.

# Magnet X default, local 0.4.25 — 2026-10-11

The native squad default now uses the user's requested Magnet X. Current
`work/translation/en/ui/boot_ui.json` supplies it to both platform builders;
the glossary decision explains the override and eight-character limit.
`tools/fix_magnet_x.py` records the source correction and creates incremental
0.4.25 candidates over 0.4.24 through the shared in-place text builder.

Both ISOs pass terminated-allocation readback, exact footer, all-file spelling,
whole-disc preservation, scene command/pointer and file-size/position checks.
PS2 ISO9660/UDF views agree. The PS2 aggregate and executable metadata carry
the current hashes. Later campaign proofreading and Hau Dragon terminology
still require a full story rebuild; these are default-name-only candidates.
No release was requested.

User fixture `incoming/ULJS000410002` was copied unchanged to
`C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/ULJS000410002`. No matching save
folder existed, so no existing slot was replaced. The four copied file hashes
are in `work/output/magnet_x_save_import.json`.

An owned isolated profile at `work/build/magnet_x_test_0.4.25` loaded a separate
copy of that fixture successfully and reached the Chapter 19 naming scene.
Default and Reset both display Magnet X; accepting it produces Ruri's
"Let's call it Magnet X." with X intact. Native default bytes also match the
candidate at the loaded module address. Runtime evidence and screenshots are
in `work/output/psp_magnet_x_0.4.25_runtime.json` and
`work/ui/psp/magnet_x_0.4.25`. The test process is stopped after verification;
other emulators and the user's configuration are untouched. The squad-caption
overlap shown in the reported image remains a separate UI-layout issue.

# Est surname, local 0.4.24 — 2026-10-11

Both reported Chapter 18 lines already use Est in the completed proofreading
sources: Hugo entry 462 and Aqua entry 906. Sixteen active input files still
contained Esto in older contributor text, term additions or a generated PS2
projection. `tools/fix_est_surname.py --inputs` corrected those and synchronized
the affected exact context guard. The source verification record confirms all
22 current Albero/Folia dialogue rows reproduce correctly, with every chapter
fingerprint unchanged. Name validation now rejects both full Esto variants.

The same tool creates local 0.4.24 candidates over 0.4.23 with `--build PSP`
or `--build PS2`: every whole-word native/ASCII Esto is shortened in its current
terminated allocation, and the footer is regenerated before final hashes.
This changes two surname occurrences in each disc. See the platform
`est_0.4.24_verification.json` records in `work/output` for actual disc checks.
The PS2 aggregate and font metadata are carried forward with current resource
and changed script-block hashes. No release was requested. Story playthrough
remains pending; this is a surname-only candidate, so later proofreading and
the Hau Dragon source follow-up still require a full campaign rebuild.

# Hau Dragon follow-up — 2026-10-11

The latest screenshot correction is applied to current sources, not local
0.4.23 ISOs. Ordinary mentions use Hau Dragon. There are 54 edited dialogue
entries across 16 chapters and seven edited library entries. The three
explicit dual-name source lines retain the literal Iron Dragon alias.

Chapter 18 entry 1201 (Prospector, i03s4b:82) now reads:
"Giganos, Gulfer, the Mu... The Hyakki Empire and Hau Dragon... Plus the Vegan
Empire, and the Angels on top of that."
This preserves the cumulative enemy list and removes the unspoken gloss.

`tools/record_hau_dragon_followup.py` records the guarded source changes;
`--library-only` records the encyclopedia inputs. Both are one-shot tools.
`tools/campaign_dialogue_layout.py` applies exact reviewed English breaks
from `work/translation/en/ui/campaign_dialogue_layout.en.json` in the shared
PSP/PS2 loader. Re-run `tools/verify_hau_dragon_sources.py` after related
changes. The verification record is `work/output/hau_dragon_followup_validation.json`:
54 dialogue entries fit both fonts; 53 have matching PS2 sources; Chapter 56
entry 218 has no PS2 counterpart. Current reports include this follow-up.

# Title-screen credit/version, local 0.4.23 — 2026-10-10

Both platforms now have local 0.4.23 footer-only candidates over 0.4.22:
`v0.4.23` / `github.com/retro-trans`, matching SRW Z3's two-line treatment.
The persistent rule is in AGENTS.md. Every new build must regenerate and
read back the exact footer, including incremental builds. Main PSP/PS2 build
paths and the compact PS2 packager stamp it automatically; new incremental
builders must use `build_title_footer.stamp_existing` before final hashes.
Release packaging gates 0.4.23+ on actual native footer pixels.

See `docs/title_footer.md` for offsets, bounds, build integration and checks.
The PSP live title uses OPWND TX48 #44; IM background #141 was a separate
story image and was rejected as the PSP target during native boot testing.
PS2 uses IM background #141. These ISOs add only title-footer pixels over
0.4.22, so later source-only proofreading still needs a story rebuild.
PSP fresh-boot verification matches the entire native title texture and confirms
the visible footer clears the menu rows, with texture replacement disabled.
No release requested. PS2 live title placement remains pending.

# Chapter 17 proofreading follow-up — 2026-10-10

Saburota's reported line was missed by the earlier proofreading pass. It now
reads "Sometimes we get a raw deal behind Commander Misumaru's back." The
source describes unfair treatment outside Misumaru's oversight. The current
full chapter source and guarded context override are updated; the original
contributor packet remains the exact baseline for reproducible reassembly.
The explanation is in `screenshot_proofread_followups.en.json` and both
cumulative HTML reports. Entire-chapter checks, independent row reassembly
and PSP/PS2 font widths pass. This is source-only: 0.4.22 ISOs still contain
the old line. Helper: `tools/record_saburota_proofread.py`.

# Local battle HUD candidates 0.4.22 — 2026-10-10

The reported Will labels, weapon accuracy debuff badge and Defend caption
belong to the shared untagged battle HUD atlas. Both editions now have English
in all nine selected rectangles: Will twice, Defend, and the six status tiles
ST/WP/MB/AR/DS/MV. The previous AT Field caption and all other atlas pixels
remain intact. HP, EN, shield art, numbers and frames are preserved.

Builds use local 0.4.21 as their base. Only one STATIC resource per edition
changes; the executable and all dialogue files remain byte-identical.
Tools: `tools/patch_battle_hud.py`, `tools/build_battle_hud_0422.py`.
Full-build integration is in `tools/build_patch.py` and
`tools/build_ps2_campaign.py`. Verification reports:
`work/output/{psp,ps2}_battle_hud_0.4.22_verification.json`.
Details: `docs/battle_hud_0.4.22.md`. Local builds only; no release requested.
In-game visual confirmation is pending. Broader campaign proofreading is
still source-only, as described below.

# Local screenshot corrections 0.4.21 — 2026-10-10

Both editions now have Bryst, Mu and the reviewed Bahbem decoy wording.
Rom's refusal to give his name was checked and remains unchanged. All three
Chapter 16 title atlases per platform now read "Blue Meets White" in uniform
lettering. Current sources, terminology decisions and review fingerprints
are updated; the cumulative end-of-campaign HTML report is regenerated.

Build helper: `tools/fix_reviewed_text_0421.py`; verification reports:
`work/output/{psp,ps2}_screenshot_review_0.4.21_verification.json`.
Details: `docs/screenshot_review_0.4.21.md`. These are incremental local
builds from 0.4.20. The earlier startup-warning translation is retained.
Full campaign proofreading is still source-only. In-game visual confirmation
remains pending; no commit or release requested.

# Local startup-warning candidates 0.4.20 — 2026-10-10

The user now requests English startup warning artwork, superseding the earlier
decision to keep it Japanese. Both native images are translated, preserving
all five paragraphs and their edition-specific wording. The PS2 warning is
IM.BIN at 0x27e8000; PSP is IM_ADD.BIN at 0x14ea000. Only pixel bytes change;
palettes, loading code, copyright artwork and other assets are preserved.
Option/save screens belong to separate work and are outside this correction.

Build helper: `tools/fix_startup_warning.py`; details: `docs/startup_warning.md`.
Both local ISO candidates use 0.4.20 (PS2 base 0.4.19, PSP base 0.4.18).
Verification reports: `work/output/ps2_startup_warning_0.4.20_verification.json`
and `work/output/psp_startup_warning_0.4.20_verification.json`. The PS2 font
chain retains its unchanged executable. Native asset previews are in
`work/ui/{ps2,psp}/startup_warning_0.4.20/english.png`.
In-game visual confirmation remains pending. No commit or release requested.
The completed campaign proofreading below is not included in these ISOs.

# Proofreading completed through the end — 2026-10-09

All campaign routes through the finale and epilogue are reviewed, along with
hidden-stage text, unused scenes and closing/save messages. This continuation
adds 633 corrections at 658 occurrences across 21,257 assembled entries.
The cumulative report explains 804 corrections at 869 occurrences:
`work/output/chapters01_end_proofread.html`. See
`docs/chapters31_end_proofread.md` for scope, checks and limitations.

Current full merges, scoped context overrides and safe English copies are
updated. The remaining-campaign manifest points to
`work/output/stages31_end_context_reviews.json`; its review records and the
common context registry are current. Do not assemble without scoped overrides.
All 235 remaining final packets validate, retaining 12 earlier approved name
fixes. Original source metadata and uncertainty annotations are preserved.
Read-only reassembly reproduces all 28 remaining groups and review fingerprints
exactly. Verification: `work/output/chapters31_58_proofread_verification.json`.

The report labels groups 55–58 as Finale, Hidden stage, Unused scenes and
Closing/save messages. They are internal source groups, not four additional
numbered chapters. Regenerate the cumulative report with
`py -3.8-32 tools/report_cumulative_proofread.py --through-end`.

Existing PSP/PS2 ISOs do not include this review. No build, commit or release
was made; native rendering and playthrough verification need a subsequent build.

# Previous proofreading through Chapter 30 — 2026-10-09

All routes through Chapter 30 are reviewed. Chapters 15–30 add 58 new
corrections at 59 occurrences; prior Chapter 15 Super edits are retained.
The cumulative report explains 171 distinct corrections at 211 occurrences:
`work/output/chapters01_30_proofread.html`. See
`docs/chapters15_30_proofread.md`; new decisions and checks:
`work/translation/en/script/chapters15_30_proofread.en.json` and
`work/output/chapters15_30_proofread_verification.json`.

All 241 current final packets validate, and all 30 chapter assemblies reproduce
the reviewed text and fingerprints exactly. Current full merges and scoped
context overrides are authoritative; do not assemble without those overrides.
Twelve older final-packet rows retain earlier George De Sand / Albero Est fixes.
Folia Est follows the documented family spelling. Historical drafts remain
unchanged. Existing ISOs do not include this source review; no build or release
was made. The cumulative report can be regenerated with
`tools/report_cumulative_proofread.py`.

# Chapters 1–14 proofreading inputs — 2026-10-09

All routes reviewed: 9,766 assembled entries / 7,745 distinct entries.
91 distinct corrections applied at 130 occurrences. Current full merges,
scoped context overrides and review fingerprints are updated; source metadata
and uncertainty flags are preserved. All full-source formatting checks pass.
Final packets also retain six older approved text fixes needed for
reassembly. Historical drafts are unchanged. Existing ISOs do not include
this review: no build or release was made.

Report: `work/output/chapters01_14_proofread.html`; helper:
`tools/proofread_chapters.py`; decisions:
`work/translation/en/script/chapters01_14_proofread.en.json`. See
`docs/chapters01_14_proofread.md`. Do not overwrite the full merges with an
assembly that ignores `campaign_context_overrides.json`.

# Chapter 15 Super proofreading inputs — 2026-10-09

All 677 Super-route rows compared with Japanese; 22 dialogue corrections saved
in the seven final packets and fresh/full Chapter 15 merges. All translation
checks pass and the context review fingerprint is current. Earth-route rows,
source metadata and uncertainty flags are unchanged. The current inputs have
these edits, but existing PSP/PS2 images do not: no new ISO or release was made.
Details: `docs/chapter15_proofread.md`; English edit/validation record:
`work/translation/en/script/chapter15_super_proofread.en.json`.

# Latest local PS2 candidate 0.4.19 — 2026-10-08

User-reported PS2 screens: Option menu library entries, save/load list and
memory-card dialogs (79 strings, Continue/New Game checks included).
Build: `python tools/fix_ps2_system_text.py --build` (base: local PS2 0.4.18,
`work/build/ps2/black_selena_0.4.18`). Details: `docs/ps2_system_text.md`.
Output `work/output/SRWMX_PS2_EN_0.4.19.iso`; report
`work/output/ps2_system_text_0.4.19_verification.json`; chain file
`ps2_font_0.4.19_verification.json` updated for later incremental tools.
160 static/native checks pass. The older verify_ps2_* checkers are pinned to
the 0.4.15 Library ELF hash and fail on 0.4.18 as well, so they were not usable.
The boot warning screen stays Japanese (user decision). PSP has no 0.4.19.
In-game check pending; no release requested.

# Previous local PSP and PS2 candidates 0.4.18 — 2026-10-07

User-requested **Black Selena** replaces Sarana/Sarena in standard and
high-maneuver unit names, Robot Library text, related story dialogue and
the associated music title. Current inputs, protected names and aliases
agree; the Akurasu override is recorded. Both native fonts render Selena
narrower, so existing line breaks and storage are preserved. Based on the
local 0.4.17 images, retaining Albero Est and all previous changes.
Reproduce with `tools/fix_black_selena.py --inputs --build`; existing images
use `--verify-existing`. Details: `docs/black_selena_0.4.18.md`.
All 32 PSP / 37 PS2 files pass readback, including both PS2 filesystem views.
All 203 story blocks per platform preserve commands and pointers. Whole-disc
comparison permits only declared text changes. PSP fresh boot verifies both
unit names and changed library/music text; actual screen playthrough and
PS2 live checks remain pending.
Public releases remain 0.4.12; no release requested or created.

# Previous local PSP and PS2 candidates 0.4.17 — 2026-10-07

User-requested **Albero Est** replaces Albero Esto in both platforms' full-name
tables, story and battle dialogue. Based on the local 0.4.16 images; the AT Field
caption and all previous fixes are preserved. Current inputs and the glossary
decision are updated; historical records retain their labels. Reproduce with
`tools/fix_albero_est.py --inputs --build`; existing images are audited using
`--verify-existing`. Details: `docs/albero_est_0.4.17.md`.
All 32 PSP and 37 PS2 disc files pass readback; both PS2 filesystem views
agree. All 203 story blocks per platform preserve commands and pointers.
Whole-disc comparison permits only the declared terminated text changes.
PSP fresh boot confirms Albero Est and all 3,837 text-pointer relocations.
Affected story playthrough and PS2 live checks remain pending.
Public releases remain 0.4.12; no release requested or created.

# Latest local PSP and PS2 candidates 0.4.16 — 2026-10-07

The reported white A.T. Field battle caption now reads `AT Field` on both
platforms. It was a separate, untagged shared HUD atlas, rather than the
already translated yellow map banner. See `docs/at_field_0.4.16.md`.
Only 24×112 caption bytes change in each native STATIC resource; palettes,
coordinates, scripts, executables and animation resources are preserved.
Local bases are PSP 0.4.14 and PS2 0.4.15. Both new images use 0.4.16;
older versioned files remain intact. Public releases remain 0.4.12.
Resource/whole-disc checks and decoded previews cover both platforms.
Isolated PSP fresh boot verifies the entire modified atlas in game RAM.
Actual field activation, PS2 live capture and physical console tests remain
pending. No GitHub release was requested or created.

# Previous local PSP candidate 0.4.14 — 2026-10-07

Built on local PSP 0.4.13. User-requested George De Sand spelling changes the
name table and five story lines; current glossary/library/battle metadata is
consistent. Karl's corruption line was source-checked and is accurate.
Rockfell's favor/arrogance line now reads idiomatically; see
`docs/psp_text_0.4.14.md` for the original meaning. All 80 music titles already
translated in 0.4.11 are verified; two formerly romanized long G Gundam titles
now use compact English. Actual Sound Select shows the serene-mind title
without overflow in an isolated fresh-boot profile.

Native menu, text, Spirit Cost, Level Up and narration regressions pass.
Independent preservation verifies all 203 script tables, only six story
slots changed, only three STATIC pointers changed and all prior 3,834 text
pointers remain exact. Fresh boot checks all 3,837 relocated pointers and
all three native getter pairs. All 32 ISO files pass readback. Only BOOT,
EBOOT, MAP and STATIC change; earlier Chapter 11 artwork remains exact.
Affected story playthrough and physical PSP checks remain pending.

Local ISO: `work/output/SRWMX_EN_0.4.14.iso`. SHA-256:
`15f32a409041b218068b0b026d32212a286eeb184e5e948b82d2070e979d9826`.
Tools: `record_psp_0414_sources.py`, `fix_psp_0414.py`, `verify_psp_0414.py`,
`verify_psp_0414_runtime.py`, `verify_psp_0411.py 0.4.14`.
Public PSP/PS2 remain 0.4.12. No new release authorization.

# Previous local PSP candidate 0.4.13 — 2026-10-07

Based on public PSP 0.4.12. Fixed six-cell Spirit Search cost/bracket spacing
in learned, unlearned, unknown and unavailable branches; all 99 native cases
pass. Redrew three Chapter 11 `do justice to` title atlases uniformly.
Corrected allied Zeorymer defeat wording in s0150:207 and s0430:207; commands,
other strings and script budgets remain exact. Chapter 7's shortened title
is correct and retained. The user clarified the screenshot list can include
old builds: Level Up was already fixed since 0.4.10, and the actual formatter
row pointers pass the native drawing fixture on both 0.4.12 and 0.4.13.

All 32 ISO files pass readback. Only BOOT/EBOOT, MAP and PACKMAPC2 change.
Native text and narration regressions pass. Isolated fresh boot checks all
21 new instruction words and relocated Level Up buffer/stride. Battle-screen
visual acceptance and physical PSP testing remain pending. Evidence and
reproduction: `docs/psp_ui_0.4.13.md`; tools `fix_psp_0413.py`,
`verify_psp_0413.py`, `verify_psp_0413_runtime.py`. Local ISO:
`work/output/SRWMX_EN_0.4.13.iso`. SHA-256:
`e30101fef36588b70f0142345677382bb9238300e23aca16324d2080d4022d19`.
Public PSP/PS2 versions remain 0.4.12. No new release authorization.

# Latest local PS2 candidate 0.4.15 — 2026-10-07

Translated both library headings and repaired all 512 library descriptions.
PSP wrapping had produced 3,059 overwide lines and 3,020 rows over the native
copy-buffer limit. All 4,708 current lines execute within 560 pixels and 128
expanded bytes, including editable nicknames. Character nickname/actor/series
values now share x=104 and long metadata fits the area before the portrait.
Twelve header paths, 103 value draws and eight earlier regression suites pass.
FIX00 is smaller than 0.4.14; the text segment ends at 0x7d8980. Unrelated
database sections, nonlibrary sentences, campaign assets, AI/status/badges,
favorites and balance are preserved by an independent structural proof.

Build: `tools/fix_ps2_library.py --verify-existing --build` after preparation.
Prepared files: `work/build/ps2/library_0.4.15/`. Evidence:
`work/output/ps2_library_0.4.15_execution.json`; reproduction and limitations:
`docs/ps2_library.md`. Local image:
`work/output/SRWMX_PS2_EN_0.4.15.iso`. Visual acceptance in the actual library
and physical console tests remain pending. No release is authorized.
All 37 disc-file ISO9660/UDF checks pass; only FIX00 and the executable change.
Isolated fresh boot verifies the entire new text segment and database plus
all 28 library code/data words, with no opcode/TLB warnings. Runtime evidence:
`work/output/ps2_library_0.4.15_runtime.json`. Image size: 4,663,291,904 bytes;
SHA-256: `c4fbc932b67a04088c6bbd6213c9aa008bea42fef733b56b39b4ff388aa82676`.

# Previous local PS2 candidate 0.4.14 — 2026-10-07

Shortened the generic pilot name to AI in Strg 1133. Corrected the native
status mapping/bounds and restored the original HP icon. AT/CT assets retain
the exact verified 0.1.17 frame fix; the reported screenshot appears to show
the older badge artwork, so its originating build was queried. All nine
regression suites pass; the executable is identical to 0.4.13. Only FIX00.DAT
(one name slot) and WND.BIN (seven status tiles) change. Narration, campaign,
three favorites, balance and saved numeric fields remain intact.

Build/evidence: `tools/fix_ps2_battle_labels.py`,
`work/build/ps2/battle_labels_0.4.14/`,
`work/output/ps2_battle_labels_0.4.14_verification.json` and
`docs/ps2_battle_labels.md`. Local output is
`work/output/SRWMX_PS2_EN_0.4.14.iso`. Public releases remain 0.4.12; no
GitHub release is authorized for this candidate. Fresh boot is required to
load the new name and icon resources; older save states can retain old data.
All 37 disc-file checks pass in ISO9660 and UDF. Image size: 4,663,275,520 bytes.
SHA-256: `373c8b2cdf62d2c74cb8cbdb7935049204770dd4b801a86c422697e1a98a6228`.

# Previous local PS2 candidate 0.4.13 — 2026-10-07

Fixed right-edge clipping in both narration crawls using native PS2 glyph
advances. The existing 24-pixel font is preserved; each line fits 560 pixels.
All 56 lines execute within the limit, with wording, placeholders and timed
record commands unchanged. All eight regression suites and 37 disc-file
checks pass. Three favorites and both balance modes remain intact.

Image: `work/output/SRWMX_PS2_EN_0.4.13.iso` (4,663,275,520 bytes).
SHA-256: `28dd376b20d54381a85c0b1073191212f66a07fead5fe71603d7fdaba0995e0c`.
See `docs/ps2_narration.md` and `work/build/ps2/narration_0.4.13/`.
Build with `tools/fix_ps2_narration.py --build` in a fresh candidate directory;
`--dry-run` previews the change without writes. The existing candidate is
protected from overwrite. Public PSP/PS2 releases remain 0.4.12; this local
PS2 fix is unpublished and PSP needs no corresponding narration change.

# Shared public release v0.4.12 — 2026-10-06

Published: https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.12
All 11 current release assets were downloaded and verified. PS2 is now a bare
`.xdelta` at the user's request; the ZIP has been removed. Its bytes match the
previously verified Apply xdelta patch. The shared manifest covers both platforms.
The catalog refresh and Retro Trans checks passed, with accurate platform
metadata, all previous PSP routes retained and the PS2 original-to-0.4.12 route.
Publication evidence: `docs/releases/v0.4.12_validation.json`; initial ZIP
publication evidence is preserved in `docs/releases/v0.4.12_zip_validation.json`.
Public local images are `work/output/SRWMX_EN_0.4.12.iso` and
`work/output/SRWMX_PS2_EN_0.4.12.iso` (hard link to the preserved 0.1.18 image).

The user authorized releasing both platforms under the PSP version number.
Public PS2 v0.4.12 is byte-identical to the final local 0.1.18 image
(`10d491a0ce7331ecaf94270f5112c375276f0a987c1150e104fd22a67833dbdf`).
PSP v0.4.12 retains its existing image and number. Release notes and exact
source/output hashes are in `docs/releases/v0.4.12.md`. PSP uses the existing
Retro Trans Automatic catalog; the bare PS2 patch is applied directly with
Apply xdelta and has its own entry in the shared manifest. Earlier local-only statements below are historical.

# Handoff — SRW MX Portable English translation

Written 2026-10-02 for whoever continues this work. The original comparison instructions below are
retained; the continuation status describes the latest work on disk.

## PS2 continuation status — 2026-10-06

**Latest local PS2 candidate: 0.1.18 — three favorite series.**
Build with `tools/fix_ps2_favorites.py --build`; see `docs/ps2_favorites.md`,
`work/build/ps2/favorites_0.1.18/` and
`work/output/ps2_favorites_0.1.18_execution.json`. Both balance modes offer
three distinct choices at New Game setup. Confirm toggles, Cancel undoes,
and the third pick opens native Yes/No confirmation. A new top panel displays
all three choices. Native favorite bits at settings +0x5e8 are unioned only
after Yes; all three receive the native EXP/upgrade bonuses and save normally.
Legacy saves keep their choices and NG+ preserves inherited favorites. Save
format and difficulty persistence are unchanged. All 1,632 combination/mode
cases pass, as do native save-field, bonus, UI and prior regression checks.
Output: `work/output/SRWMX_PS2_EN_0.1.18.iso` (4,663,269,376 bytes).
All 37 disc files pass; only the executable changes from 0.1.17. SHA-256:
`10d491a0ce7331ecaf94270f5112c375276f0a987c1150e104fd22a67833dbdf`.
Final fresh-boot PCSX2 readback matches the immutable segment and all 199
references/hooks with zero opcode/TLB warnings. Full menu visual and real card
save/reload checks remain pending: Computer Use failed to activate the test
window, then denied cursor/input access. No release or push is authorized.

**Previous local PS2 candidate: 0.1.17 — CT/AT forecast badge fixes.**
Build with `tools/fix_ps2_forecast_badges.py --build`; see
`docs/ps2_forecast_badges.md` and `work/build/ps2/forecast_badges_0.1.17/`.
AT/CT native WND image payloads now fit the actual 24×24 badge area,
with complete original frames and padding. Only these two payloads change;
the executable and all other resources match 0.1.16. Previous native
execution evidence is carried forward explicitly. Asset previews pass;
in-game visual confirmation remains pending. Output:
`work/output/SRWMX_PS2_EN_0.1.17.iso` (4,663,267,328 bytes).
All 37 disc-file checks pass; only WND.BIN changes compared with 0.1.16.
The shared graphics renderer matches the incremental patch exactly.
SHA-256 `5e181905226266c4ea51f769acf219e24c62ee18e2edf851011a1924cbb3739f`.
No release or push is authorized.

**Previous local PS2 candidate: 0.1.16 — weapon and battle UI fixes.**
Build with `tools/fix_ps2_weapon_battle.py --build`; see
`docs/ps2_weapon_battle.md`, `work/build/ps2/weapon_battle_0.1.16/`, and
`work/output/ps2_weapon_battle_0.1.16_execution.json`.
Attribute text is explicitly terminated, with A/S single-character flags;
long weapon names fit proportionally; Giganos Sldr. is forecast-only.
Weapons and the shared Critical image are translated. CFont wrappers also
map complete cached Will/Critical/Weapons labels to English. All earlier
scenario, balance and UI content is preserved. Battle-animation visual
confirmation of Will/Critical remains pending; do not claim its baked
graphics were identified. Output: `work/output/SRWMX_PS2_EN_0.1.16.iso`.
All 37 disc files pass; fresh 4x PCSX2 boot confirms all 177
hook/reference words and the native segment, with no opcode/TLB warnings.
ISO SHA-256 `d5d904e771e2f72410b757f250d2eca89568cefa547628b5bc0eb75419b4d066`.
No release or push is authorized.

**Previous local PS2 candidate: 0.1.15 — map support captions.**
Build with `tools/fix_ps2_map_support.py --build`; see
`docs/ps2_map_support.md` and `work/build/ps2/map_support_0.1.15/`.
Native MAP section 16 images M_65/M_66/M_67 are English Support Atk,
Support Def and Assist Atk. Only the three 2,048-byte pixel payloads change.
The executable, counters, palettes and all other map content remain identical
to 0.1.14. Decoded previews pass; in-game confirmation remains pending.
Output: `work/output/SRWMX_PS2_EN_0.1.15.iso` (4,663,267,328 bytes).
SHA-256 `ecdaa12f194f5db0a9a6b0abefde5bcec4240047311254332e9f22e1db452360`.
Native campaign checks and all 37 disc resource readbacks pass. No release or push.

**Save converter handoff 0.1.0:** see
`docs/retro_trans_tools_mx_save_handoff.md` and
`work/output/SRWMX_SaveConverter_Handoff_0.1.0.zip`.
The portable bundle is copied to the local Retro Trans checkout at
`E:/Projects/retro-trans-tools/.integration/srw-mx-save-handoff-0.1.0/`.
It specifies PS2 ↔ PSP conversion and the PSP Harder choice for patched
PS2 output, with integrity references and known campaign restrictions.
The converter is not implemented; matched checkpoint field mapping,
destination packaging/crypto and in-game acceptance remain required.
No ROM/save/key bytes are distributed. No release, push or chat dispatch.

**Previous local PS2 candidate: 0.1.14 — save/setup/series UI fixes.**
Build with `tools/fix_ps2_setup_save.py --build`, preserving 0.1.13.
See `docs/ps2_setup_save.md`, `work/build/ps2/setup_save_0.1.14/`, and
`work/output/ps2_setup_save_0.1.14_execution.json`. Checking, saving and
system-data overwrite prompts are English. Yes/No share one left edge;
protagonist values move 32px right, age suffixes are removed, both unit
descriptions are fully English, and final setup buttons are translated.
Series titles use actual VWF centering and uniform fitting inside the
456px padded title area. The baseline uses the native square glyph height.
Native checks cover nine save branches, the actual protagonist header,
both value/age paths, both six-row descriptions, both final button
selections, Yes/No initialization and 40 series title cases. Campaign
.BIN/.DAT resources match 0.1.13 exactly. Disc packaging and fresh-boot
visual validation are recorded in the output reports. No release/push.
Final ISO: `work/output/SRWMX_PS2_EN_0.1.14.iso`, 4,663,267,328 bytes,
SHA-256 `92b871792cbb936d74b72394d9d97cd1e73022bc3574c2d113608e4ee8cde14f`.
All 37 disc resources pass validation. Fresh PCSX2 boot confirms the
777,344-byte native segment and 164 hook/reference words at 4x, with
texture replacements disabled and no opcode/TLB warnings.
PCSX2 visually confirms Protagonist Setup, the separated Name/Nick/Age
value column and the English age values. Evidence is
`work/ui/ps2/setup_save_0.1.14/4_protagonist_setup_after.png`. Save dialogs,
unit descriptions, final confirmation and series-title panels pass
native execution checks; their visual confirmation remains pending.

**Previous local PS2 candidate: 0.1.13 — roster/System UI fixes.**
Build with `tools/fix_ps2_roster_system.py --build`, preserving 0.1.12.
See `docs/ps2_roster_system.md`, prepared files in
`work/build/ps2/roster_system_0.1.13/`, and native execution report in
`work/output/ps2_roster_system_0.1.13_execution.json`.
Roster headings use Wpn/Cost/Und/Rng/P.Rng/Atk to avoid overlap. System
labels and choices are translated at nine local draw sites; two direct
Repair draw sites use Cost. Objectives has a second literal after a
nonzero structure field, referenced in a call delay slot at 0x153b58;
this is now translated too. The map-menu entry was already English.
All 18 legal settings, 14 roster descriptors and the actual Objectives
header pass native text/geometry checks. Option values and all .BIN/.DAT
resources are unchanged from 0.1.12. The roster/footer/header fixes from
0.1.12 remain active. Test with a fresh disc boot; an old save state
restores old executable code. No release or push is authorized.
Final ISO: `work/output/SRWMX_PS2_EN_0.1.13.iso`, 4,663,267,328 bytes,
SHA-256 `31ad4fcdc7effccade0fefc78d100d6f8d33cbb7bc7f4ea1cbac0a0167e9ebd0`.
All 37 disc resources and retained font/campaign/UI checks pass. Fresh
PCSX2 loaded-byte verification passes for the immutable segment and 117
hook/reference words at 4x, with no opcode/TLB warnings. Panel-by-panel
visual confirmation is pending.

**Previous local PS2 candidate: 0.1.12 — detail/search/roster UI fixes.**
Build with `tools/fix_ps2_ui_details.py --build`, using the preserved 0.1.11
resources. See `docs/ps2_ui_details.md` and `work/build/ps2/ui_details_0.1.12/`.
Native header branch paths and GP-relative label draw calls are translated.
Cached weapon flags translate before VWF measurement, so alignment accounts
for their English width. The fixed four-character attribute buffer uses Asst.
The 102 skill/ability descriptions use PS2 advances and at most three lines;
old sentence IDs remain valid, and every numeric database section is unchanged.
All campaign scripts, stage resources and portraits are byte-identical to
0.1.11. PSP opening remains selected. Native checks pass; visual checks must
use a fresh boot of this disc, because older save states restore older code.
No GitHub release or push is requested for this build.
Final ISO: `work/output/SRWMX_PS2_EN_0.1.12.iso`, 4,663,265,280 bytes,
SHA-256 `2e5fd0c260d8f2c827bf2fae4fddf851fb67132f9cd9686ce0f56924a615e6ea`.
All 37 disc resources pass validation. Fresh PCSX2 loaded-byte checks pass
for all recorded hooks and new detail instructions/references. Full visual
checks of the five reported screens remain pending; see the runtime report.

**Previous local PS2 candidate: 0.1.11 — font and battle/status UI fixes.**
User explicitly chose to keep the PSP opening; do not combine the original
PS2 lab opening with it. See `docs/ps2_ui_fixes.md` and
`work/build/ps2/ui_fix_0.1.11/`. Latin uses square dimensions derived from
the smaller native cell dimension, with native half-width numeric contexts
retaining their original height; the native 4x atlas is preserved. The
remaining command, unit/pilot-stat and weapon labels are translated, weapon
labels shortened and Spirit SP costs moved right. Long Spirit names scale
uniformly inside a 76-pixel field. All scenario and portrait resources match
0.1.10 byte-for-byte. Native execution checks pass; build/visual reports
describe the final disc and observed screens. No release or push requested.
Final ISO is `work/output/SRWMX_PS2_EN_0.1.11.iso`, 4,663,255,040 bytes,
SHA-256 `7438b0574cb07c97bd46948b47e0d060fadc269392d90a8fa0a53bc248c7312b`.
Final PCSX2 screenshots confirm the PSP opening, researcher dialogue and
English commands. Unit Stats, Pilot Stats and Weapon Data visual checks
remain pending because isolated emulator controller input was unreliable.
Their native label/name-fit/cost checks pass. See
`work/ui/ps2/ui_fix_0.1.11/layout.json` for exact evidence and native fields.

**Previous local PS2 candidate: 0.1.10 — Prologue corrections built.** See
`docs/ps2_prologue_fixes.md` and `work/build/ps2/prologue_fix_0.1.10/`.
Both PSP pre-battle `0b` events are restored to their exact seven-command,
zero-dialogue source; the old substitution of `i001b` was incorrect.
Native Game Over (0x13d) chapter 0/1 retry gate now includes group 4, with
98 dispatch/parent-retry cases checked. Researcher Pilt433 story face is
2110 (bytes4/5=21,10), separate from its absent battle face at +14. Native
descriptor slot309 and FACEPACK indexes2998/2999 are ported from PSP art.
All other 201 scripts remain byte-identical to 0.1.9. Output is
`work/output/SRWMX_PS2_EN_0.1.10.iso`, 4,663,252,992 bytes, SHA-256
`a48daca844b70653d944f0696d45cabf2b3d1eefab38136a4fc10d2e32afb078`.
All 37 disc resources and replacement ISO9660/UDF entries pass validation;
original ISO and 0.1.9 hashes remain unchanged. Fresh PCSX2 new game on the
Super Robot route visually confirms Hugo's Wolf 1 opening and the correct
researcher radio portrait. Evidence is in `work/ui/ps2/prologue_fix_0.1.10/`
and `work/output/ps2_font_0.1.10_runtime.json`. Full in-game defeat/retry,
clear, memory-card save/load and physical PS2 validation remain pending.
No release requested. Build with `tools/fix_ps2_prologue.py --build`.

**Previous local PS2 candidate: 0.1.9 — both PSP extra scenarios included.**
Output `work/output/SRWMX_PS2_EN_0.1.9.iso`. See `docs/ps2_stage30_port.md`
and `work/output/ps2_font_0.1.9_verification.json` for hashes and evidence.
PSP s0570 is reworked scenario 29 (What Gnaws at the "Heart"); s0560 is
the extra scenario 30 (Zeorymer Sorties at Dawn). Both six-scene event groups
are required. Native chapter 7 locations are `[29,30,31,32,33,68,34]`, with
groups 12 then 10 for those two battles. Tables contain 203 scene blocks.
All reviewed English source slots are covered; nine PSP BFACEPAK cache
commands are adapted to native opcode 178. Original map 90 heights and
native artwork remain. Additional Aqua variants alias native assets 315;
enemy Dragoon 156 reuses native row 69 and has an added PSP-balance entry.
Objective footer titles now correctly map Prologue and chapter-7 groups.

Execution checks pass for native scripts/deployments, seven selectors and
history slots, unlock masks, save fields, card/asset reads and all previous
font/text/balance/Prologue regressions. Stage 29/30 full in-game clear,
memory-card save/load and physical PS2 tests remain pending. Use new games
with a separate card; existing campaign save migration is not implemented.
No release or push requested for 0.1.9. Build with `tools/port_ps2_stage30.py`.
Disc is 4,521,150,464 bytes, SHA-256
`547878052851c158d40154557803c5b647b720ed8ffae12b41ad58acf59c3428`.
Fresh PCSX2 2.8.2 boot/PINE byte checks pass for the full added segment,
all hooks and loader tables, with no unknown opcode/TLB warnings and no
texture replacement. Opening FMV visually observed; stages 29/30 still
need full in-game playthrough. `work/output/ps2_font_0.1.9_runtime.json`.
The following 0.1.8 notes are historical; its ISO remains preserved.

**Latest local PS2 build: 0.1.8 — chapter-number fix.**
`work/output/SRWMX_PS2_EN_0.1.8.iso`, 4,666,597,376 bytes, SHA-256
`0e9f7f4fd61d93c16c7bd6f389b914f6e719af857bbf1dc2b2fb2b3dd079e7b4`.
The user reported the first story card (Visitors from the Beyond) displaying
Chapter 2 after the added Prologue. Hero +0x5f0 counts all cleared battles;
both card-animation paths passed that count plus one. Four display-only
instructions now copy the count without adding one: 0x348634 / 0x3489b4 for
cards and 0x224f08 / 0x2fe7cc for objectives. Prologue displays number zero;
the first story card receives one. No native clear count, save field or
campaign progression changes. Existing 0.1.7 entry fix and resources retained.

`tools/ps2_prologue_numbering.py` is integrated into the clean builder and
incremental verification. 64 native animation cases and 24 native objective
number cases pass across both robot routes. The tests run actual campaign
animation/title lookup, reproduce the original off-by-one and verify counts
remain intact. Report: `work/output/ps2_prologue_0.1.8_numbering_execution.json`.
New Game entry, all eight scene loaders, both deployments, campaign save-field,
font/text and difficulty checks pass. All retained ISO resources were rehashed;
ISO9660 and UDF read the corrected executable. ELF SHA-256
`241497d4d58b7d284a741ba640c38885e5b1b06ef26cd6af58a19f4c90515ef0`;
segment remains 760,436 bytes and InitHeap remains 0x7cea80. Build report:
`work/output/ps2_font_0.1.8_verification.json`. The 0.1.8 title card itself has
not yet been visually checked in PCSX2; retain the 0.1.7 runtime evidence below
as evidence for that previous version only.

Pending footer-title issue: objective call sites pass campaign group / 2 to
0x3473d0, but the added Prologue shifted the first two chapter location lists.
For chapters 0/1, group 4 needs location index 0, group 0 needs index 1, group
2 needs index 2. Remap only the two objective callers; do not change 0x3473d0
globally, because the history title getter already supplies actual list indexes.
0.1.8 corrects displayed numbers, not this title lookup. Full battle clear,
memory-card acceptance, physical console and the added stage 30 remain pending.
No GitHub push/release for 0.1.8. Original discs and earlier builds preserved.

Rebuild with `tools/port_ps2_prologue.py` (0.1.8), or prepare corrected resources
under `work/build/ps2/prologue_0.1.8` and run
`tools/update_ps2_difficulty_build.py --source-version 0.1.7 --version 0.1.8 --feature prologue`.

**Previous local PS2 build: 0.1.7 — Prologue New Game entry fix.**
`work/output/SRWMX_PS2_EN_0.1.7.iso`, 4,661,843,968 bytes, SHA-256
`be484ab778e957cb11bd0950f2fc86e304868693b9dd75d6f40fd0bb582252e8`.
The user confirmed 0.1.6 skips the Prologue and enters original stage 1.
Native New Game completion event 0x2d6 bypasses STAGE selection and passes
deployment group zero at 0x134d88 / 0x134da8. Both now pass group four;
the call at 0x134dc0 wraps native campaign advance to set current group four
without incrementing initial history slot zero. Later chapter advances retain
their original code. Both robot routes and both difficulty modes pass actual
native completion-event execution; tests reproduce the old skip. See
`work/output/ps2_prologue_0.1.7_entry_execution.json`.

All eight native scene loaders, both deployments, campaign save-field checks,
font/text and difficulty regressions pass. All retained disc resources were
rehashed and are identical to 0.1.6; both filesystems read the corrected ELF.
ELF SHA-256 `15699c45e1ab1539550acfd18ddd1d73055b68ab41150933649cdbd7a8ba3232`;
entry routine 0x7cea50, segment 760,436 bytes, InitHeap still 0x7cea80.
Packaged ISO boots in isolated PCSX2, PINE 28018: complete segment, all hooks
and script tables match RAM. No CPU opcode or TLB warnings at initial boot.
Profile: `work/build/ps2_prologue_test_0.1.7/emulator/mx-prologue-fix.exe`.
It has its own copied card; 0.1.6 settings/card and the user's normal profile
are untouched. Test-only direction macros must bind `Down` / `Up` / `Left` /
`Right`, not `DPadDown` etc.; H toggles R1 for dialogue fast-forward.
Both Prologue battles reach their actual mission/objectives screen in PCSX2:
Garmraid with PS2 balance and Cerberus with PSP balance. Live campaign state
is chapter 1/0, group 4, history slot 0; deployments are s00s00/s00r00, map
390, two units. Runtime entry evidence is
`work/output/ps2_prologue_0.1.7_runtime_entry.json`; screenshots are
`work/ui/ps2/prologue_0.1.7_super_objectives.png` and
`work/ui/ps2/prologue_0.1.7_real_objectives.png`.
The UI tests resumed an owned New Game unit-setup checkpoint with only the
three corrected entry words/new routine migrated; fresh ISO boot was checked
separately. The native event tests start from a reset campaign for all four
route/balance combinations. All macros were released at the end of the 0.1.7 test; the emulator was subsequently observed idle.
Known display issue: the objective footer still shows original stage 1's
title; its number is corrected in 0.1.8, but location-title lookup still needs correction. Actual
battle clear/save-load, physical console and stage 30 remain pending.
No GitHub push/release.

Rebuild normally with `tools/port_ps2_prologue.py` (now 0.1.8), or retain the
verified 0.1.6 resources using `tools/update_ps2_difficulty_build.py
--source-version 0.1.6 --version 0.1.7 --feature prologue` with prepared 0.1.7
files. Both builders check the New Game entry before packaging.

**Previous local PS2 build: 0.1.6 — playable PSP Prologue candidate.**
`work/output/SRWMX_PS2_EN_0.1.6.iso`, 4,657,090,560 bytes, SHA-256
`00c9dab486d9fef3dc9657cf10e9273b6b8a76bff2d791e2d80bb3a7ce0276f3`.
Built from verified 0.1.5 with eight extra English scene blocks, native map 390,
two deployments, the faceless Researcher in unused pilot slot 433, and campaign
links before both original stage-1 routes. Original IDs/resources are preserved;
both disc filesystems agree. Total: 200 scene blocks and 68 scenario records.
The other added PSP stage (stage 30 / s0570) is not included yet.

Fixed an earlier campaign corruption: chapter names were written into 64 bytes,
but their actual field is 56 bytes. Restored all fourteen numeric progression
regions from the original STAGE archive, then inserted the two Prologue location
IDs. `tools/ps2_scenario_port.py` now checks that names preserve these regions.
Use a new game on a separate card: existing saves' location-index migration is
not implemented. Do not load a Prologue save with the unpatched game.

Native script/deployment load execution, route selection, six campaign save-field
round trips, database preservation, font/translation and difficulty regressions
pass. These checks do not replace actual battle clear or memory-card saving.
Reports: `work/output/ps2_prologue_0.1.6_execution.json`,
`work/output/ps2_prologue_0.1.6_regression.json`, and
`work/output/ps2_font_0.1.6_verification.json`. ELF SHA-256
`342d14fdc993e2718776184f09602cf9858d045243b7428187e3dcc9c48a099b`;
added segment 760,386 bytes, InitHeap 0x7cea80, balance mode still 0x7cce90.

PCSX2 boots this disc: the complete added segment, all hooks and script/section
tables match RAM; opening FMV and English battle dialogue in the title-screen
demo were observed, with zero opcode/TLB warnings. Runtime evidence:
`work/output/ps2_font_0.1.6_runtime.json`. Both Prologue battles, clearing into
stage 1, and actual memory-card save/load remain pending.

The working isolated emulator is
`work/build/ps2_prologue_test_0.1.6/emulator/mx-prologue-test.exe`, a portable
copy of the already installed PCSX2 2.8.2, PINE 28017. Its separate card is
`work/build/ps2_prologue_test_0.1.6/memcards/mx-test.ps2`. Launching a copy named
pcsx2-qt.exe through Computer Use instead selected the installed emulator;
renaming the test executable made window selection unambiguous. The installed
emulator was opened but no game/card/settings changes were made there.
The test window is usable. Short automated controller taps were missed between
game polls; PCSX2's own toggle macros solve this by holding each button until a
second trigger. New Game opens correctly. In this isolated profile only:
F10 = Circle, F11 = Start, F12 = Down, F7 = Up, V = Left, B = Right, N = Cross.
Press a macro key again to release it. Avoid leaving a direction held through
multiple menus. Normal L/K/Enter/arrows bindings also remain. A fresh New Game
checkpoint is `work/build/ps2_prologue_test_0.1.6/new_game_checkpoint.p2s`;
this is an emulator checkpoint, not proof of memory-card saving. Re-select
current windows by app/path, not stale handles. User's normal cards untouched.

Rebuild through `tools/port_ps2_prologue.py`, optionally `--prepare-only`, then
run `tools/verify_ps2_prologue.py`. The older clean campaign builder still
defaults to 0.1.5 and does not include these new resources. See
`docs/ps2_prologue_port.md`. No commit, push or GitHub release for this build.

**Previous local PS2 build: 0.1.5 — difficulty selection fix.**
`work/output/SRWMX_PS2_EN_0.1.5.iso`, 4,529,623,040 bytes, SHA-256
`fd33956e7fa189a9d759b4bd08ee306545128faa39881f2ab0905c7beed1f72f`.
The user screenshot showed only the balance explanation in 0.1.4. Its choice
window never finished opening: Keystone's MIPS64 `$t0` encoded register 12,
but the native PS2 fifth argument is register 8. Fixed this with numeric `$8`.
The copied vtable was also truncated at 0x90; copied all 0xd8 bytes, including
the four cursor geometry methods used by the opening routine.

Actual five-frame opening, render dispatch for both labels, up/down navigation,
confirmation/cancellation, cleanup, all balance values and save-tail tests pass.
Both deliberately reintroduced bugs are caught by new regression checks.
All other disc resources were independently rehashed and remain byte-identical
to 0.1.4. Appended segment is 757,504 bytes; InitHeap remains 0x7cdf00;
mode remains 0x7cce90. ELF SHA-256
`a4b18b4fcb8111e5125ec714f10002e424b3e842355beea1ab88d812fe1ea228`.
Original source/builds preserved. Clean campaign builder defaults to 0.1.5;
`tools/update_ps2_difficulty_build.py` can preserve a verified previous English
disc while appending the corrected executable to a new version.

Isolated PCSX2 profile `work/build/ps2_difficulty_test_0.1.5/PCSX2`, PINE 28016:
full segment, hooks and script tables match RAM, FMV observed, no opcode/TLB
warnings. Activation denied twice (`GetCursorPos failed: Access is denied
(0x80070005)`); do not claim visual validation. Test PID 13252 stopped after
verification. Original user cards untouched; real gameplay/save-reload and
physical PS2 checks remain pending. No GitHub push/release.

**Previous local PS2 build: 0.1.4 — optional PSP balance prototype.**
`work/output/SRWMX_PS2_EN_0.1.4.iso`, 4,524,873,728 bytes, SHA-256
`2aa59e7dbee57aaa5a971627970c1c4d568d6fd8e9954dea06216449ae50ca4c`.
Retains all 0.1.3 English coverage and native 4x VWF. New Game offers
PS2 - Original / PSP - Harder. Harder mode selects exact original PSP values:
139 shared enemy HP records +50%; 294 nonzero shared reward records -20%.
The empty PS2/PSP Dragoon slot 156 is excluded. Original PS2 campaign, numeric
fields outside HP/rewards and one favorite-series choice remain.

The difficulty mode lives at `0x7cce90`; the final added segment is 757,440
bytes and InitHeap starts at `0x7cdf00`. Native save settings tails stamp
three words at +0x3e0: MXBD, version 1, mode 0/1. Both payload lengths and
native checksums remain. Absent/invalid markers default to PS2; scenario
mode restores before unit decoding. The shared New Game confirmation box
gets an object-specific wide vtable, then restores its normal Yes/No class
and labels after closing. See `docs/ps2_difficulty.md` and
`work/translation/en/ps2/difficulty.en.json` for exact hooks and scope.

3,072 record execution checks, controller-handler callbacks, Cancel, cleanup,
save-marker round trips/native tail checksums, old-save defaults and early
restore pass. Finished ISO boots in an isolated PCSX2 profile on PINE 28015
with copied memory cards; complete code segment/hooks/script tables match
RAM, opening FMV observed, zero unknown opcode/TLB warnings. Visual New Game
acceptance, real gameplay HP/rewards and saving/reloading both modes are still
pending: Windows activation returned Access is denied twice. Test PID 55688
was stopped after checking; user PID 54120 was not touched. Physical PS2
checks are pending. No GitHub push/release. The clean campaign builder now
defaults to 0.1.4; this packaged candidate additionally retains an unused
pre-cleanup ELF extent, so a clean rebuild may have a different disc hash.

**Previous local PS2 build: 0.1.3 — campaign/database port.**
`work/output/SRWMX_PS2_EN_0.1.3.iso`, 4,525,156,352 bytes, SHA-256
`d1a40ec6b726acae6d2b92d4a02a098cf948352480fd40325ab80095a3c7ab8c`.
All 49,659 readable PS2 story slots are English (186 translatable scenes;
192 blocks including six nontext/dummy blocks). All original commands remain.
Also includes all 51,434 battle-caption entries, all non-dummy database
descriptions, 1,499 names, 32 spirit names, all 66 scenario/title-card records
(198 native atlases), narration, terrain and an initial menu/window-art port.
See `docs/ps2_campaign_port.md` for coverage, rebuild steps and remaining work.

The first candidate failed startup because English FIX00 exceeded the native
fixed resource heap's spare capacity. The final build fixes this by removing
unreferenced source sentence storage and moving 320,050 English bytes to a
native pool through the sentence getter at 0x332518. Final FIX00 is 516,744
bytes (original 517,712). Sent IDs and referenced original/dummy rows remain.
All 4,332 translated description-row reads pass execution checks, including
2,171 reads through the external pool. The finished ISO boots in isolated
PCSX2; English FIX00, full font/text segment, hooks and script tables match RAM.
Full campaign/visual validation and physical PS2 checks remain pending.

Remaining artwork is primarily the shared STATIC atlas: logical 1024x256,
palette at 0x134400 (GS CSM1 order), linear indexed pixels at 0x134800,
0x40000 bytes. `work/ui/ps2/static_linear_1024.png` is its correct preview.
The 512-wide and unswizzled probes are wrong interpretations; do not use them.
Port its labels using the existing PSP banner translations while preserving
native UV regions/digits/non-text artwork. Other PS2 menu differences/layouts
and the Sortie Prep header also need a native artwork pass.

The local test profile is `work/build/ps2_campaign_test_0.1.3/PCSX2`, PINE
28014. Do not interrupt the user's emulator (PID 54120 at this check).
Desktop activation failed with `GetCursorPos failed: Access is denied
(0x80070005)`; returned game captures were black, so visual QA is unverified.
No GitHub push/release is authorized. Previous PS2 builds remain preserved.

The following records the earlier baseline-only build.

**Earlier local PS2 build: 0.1.2 — font baseline correction.**
`work/output/SRWMX_PS2_EN_0.1.2.iso`, SHA-256
`24e95df8f22c4711a689461f02849eb1a68cacb9597faf72ea437fc69f18348f`. The user's four 0.1.1 dialogue captures
confirmed English loading/rendering, but showed uneven letter alignment.
0.1.2 preserves the high-resolution font baseline instead of independently
resizing each glyph vertically into its 20px hinted bounds. Ordinary bottoms
vary by one high-res pixel, compared with four before; deep descenders retain
two guard rows. All glyph advances, renderer/heap hooks and the entire MAP
archive are byte-identical to 0.1.1. Coverage remains opening + both stage-1
routes, 1,321 translated slots. No new translation area is added.
85 baseline checks and existing font execution/UV checks pass. Final disc
and boot evidence are under `work/output/ps2_font_0.1.2_*.json`; corrected
in-game visual acceptance and physical PS2 checks remain pending.
User captures and labeled atlas specimen are under `work/ui/ps2/`.
Build with `tools/build_ps2_dialogue.py` and version `0.1.2`.
Do not interrupt the user's current 0.1.1 emulator session for font QA: a
separate test profile is `work/build/ps2_baseline_test_0.1.2/PCSX2`, PINE 28013.
Original test profile remains PINE 28012. No GitHub push/release authorized.

The following records the original 0.1.1 dialogue insertion.

**Local PS2 build 0.1.1 — opening and both stage-1 routes in English.**
`work/output/SRWMX_PS2_EN_0.1.1.iso`, SHA-256
`954f3c069a72e6e8f723190d887e02194073e17736d29615961ddec6a75e71dc`.
Ported 1,321 string-table entries in five scenes: `i001b`, `s00r10`, `i00r1a`,
`s00s10`, `i00s1a`. Four technical labels remain unchanged. Reviewed seven
PS2 wording variants covering 11 slots; English-only overrides and mapping
are under `work/translation/en/ps2/script/`. No later scenes, UI/database,
battle-caption or chapter-artwork insertion is included. Start **New Game**
to see the translated opening; a later-scene save will still show Japanese.

Full disc readback passed: only ELF and MAP change; all 35 unrelated files
retain hashes and LBAs. Both ISO9660 and UDF read the rebuilt files. All 192
PS2 command arrays and every untouched string are preserved, and all 192
finished script blocks match their generated hashes. The MAP script area
grew by 33 sectors; its prefix and moved suffix remain unchanged. Native 4x
font execution checks pass. The finished ISO boots in isolated PCSX2. The font
segment, all 19 font/heap patches, full script-sector table and MAP section
table match RAM, with no unknown CPU opcode warnings. User captures confirmed English dialogue in the opening and stage 1, with
intact portraits/backgrounds. Font baseline alignment failed visual review;
0.1.2 corrects the atlas. Physical PS2 validation remains pending.
Build: `python tools/build_ps2_dialogue.py 'Super Robot Taisen MX (Japan).iso' 0.1.1`.
Use `--verify-existing` for readback of the existing ISO. Reports are
`work/output/ps2_font_0.1.1_verification.json` and
`work/output/ps2_font_0.1.1_mips_verification.json`, with boot/RAM evidence in
`work/output/ps2_font_0.1.1_runtime.json`; details in
`docs/ps2_dialogue.md`. No PS2 push/release is authorized.

The project lead requested a PS2 translation port, starting with the native 4x
VWF. Local PS2 font-only build **0.1.0** is at
`work/output/SRWMX_PS2_EN_0.1.0.iso`, SHA-256
`9c5f40d60a396d991921a1629d2addb1879dd25a997e532b4ee6c5aa41431295`.
It adds Genei LateGo Medium Latin glyphs at 96×96 with variable-width drawing
and measurement. No emulator texture replacement is used. PS2 story, battle,
UI and title-card insertion is still pending; the PSP 0.4.9 release is unchanged.

Full disc verification passed: only the executable changes, all 36 other
files retain hashes and LBAs, and ISO9660/UDF both read the new ELF. Execution
checks passed 1,368 width cases, 20 Japanese fallback cases, 344 renderer cases
and 86 glyph/upload plus 86 atlas UV-bound cases. The finished ISO boots in isolated PCSX2 and its
400,096-byte segment plus all 19 patched locations match RAM.

**Unit-stats visual check passed; remaining contexts are pending.** The user
navigated manually and supplied `work/ui/ps2/unit_stats_font_0.1.0_user.png`.
Latin labels (HP/EN, Lv, SP, PP, NEXT, LL), dynamic numbers and Japanese text
are legible, without visible clipping, overlap or damaged unit/pilot art on
that screen. A fresh read-only RAM check still matches the complete segment
and all 19 patched locations, with no unknown CPU opcode warnings.
The screen contains no lowercase descenders; dialogue, other renderer contexts
and physical PS2 checks remain pending. Windows automated input still returns
`GetCursorPos failed: Access is denied (0x80070005)`, so the screenshot is user
evidence, not an automated capture. Physical PS2 testing is also pending. Use the copied card
and isolated profile under `work/build/ps2_font_test/`, PINE port 28012.

Build tools: `tools/build_ps2_font.py`, `tools/ps2_font4x.py`,
`tools/verify_ps2_font.py`, `tools/verify_ps2_font_runtime.py`,
`tools/pcsx2_pine.py`. Evidence:
`work/output/ps2_font_0.1.0_verification.json`,
`work/output/ps2_font_0.1.0_mips_verification.json`,
`work/output/ps2_font_0.1.0_runtime.json`. Details: `docs/ps2_vwf.md`.
Reject earlier trial ELFs, including the `v2` trial: they contain a generic
MIPS C.LT encoding unsupported by the R5900. The final uses function 0x34.
Save conversion remains deferred. No PS2 GitHub release or push is authorized.

## PSP continuation status — 2026-10-04

**Latest local testing build: 0.4.12 (2026-10-06).** Adds exactly one space
between each thought-dialogue speaker name and its opening parenthesis.
1,173 rows changed; all 1,176 thought rows pass, including the reported
Daisuke line. Commands, wording, line breaks and script allocation sizes are
preserved. Only MAP_ADD.BIN changes from 0.4.11. Shared `textfit.wrap` applies
the rule to future PSP and PS2 builds. Details: `docs/psp_spacing_0.4.12.md`.
ISO: `work/output/SRWMX_EN_0.4.12.iso` (1,317,414,912 bytes), SHA-256
`80f9d24f682884059742c89b0e60ab3a53f611ee384e0cb46b068b4478d9acae`.
Public release remains 0.4.9; no release, push or commit is authorized.

**Previous local testing build: 0.4.11 (2026-10-06).** Fixes Hero/Partner/Unit
rename choice alignment, the Options menu, music/demo row centering and
remaining Japanese music titles. All six screens have native-renderer visual
evidence. Includes the previous Level Up/narration fixes and passing regression
checks. Details: `docs/psp_fixes_0.4.11.md`. Local ISO:
`work/output/SRWMX_EN_0.4.11.iso` (1,317,414,912 bytes), SHA-256
`50e6440438778cc6da32d963c9500e0b4265afb6142bdc360913b55081600f58`.
Public release remains 0.4.9; no release, push or commit is authorized.

**Previous local testing build: 0.4.10 (2026-10-06).** Fixes the user's PSP
0.4.9 Level Up row corruption and opening narration buffer overflow.
The public release remains 0.4.9. No release, push or commit is authorized
for this build. Details and reproducible checks: `docs/psp_fixes_0.4.10.md`.
ISO: `work/output/SRWMX_EN_0.4.10.iso`; SHA-256:
`c4a7eca06a4606426c0f9109c4288ca2db474cb2ac507c7ecb908a0566026444`.

**v0.4.9 upgrade added from published v0.4.1.** Exact upgrade source SHA-256:
`cf4af0243dadd37718866d7ee1a6f1f8d8974d5f55dd827644227f4e58d1c7d5`,
1,313,292,288 bytes. Do not substitute the existing local ISO labeled 0.4.1;
it differs from the published output. The verified source was reconstructed
from the original Japanese ISO and downloaded published 0.4.1 patch into
`work/build/upgrade_041_to_049/SRWMX_EN_0.4.1_published.iso`.
Full and upgrade patches passed standard round trips to the unchanged 0.4.9
target. The upgrade is 853,344 bytes, SHA-256
`d5d8d5bc6f0a9cbc34a739df55631452f7f37a9fc81be896d283cabb6171b2da`.
Extended local assets: `work/output/release-v0.4.9-with-upgrade/`. The original
full patch and release tag/source commit stay unchanged. Current metadata lists
both source paths; the older eight-asset publication record below is historical.
All nine updated published assets were downloaded and verified. Scoped catalog
workflow 37215386850 passed; the live catalog matches the extended manifest and
offers the direct 0.4.1 → 0.4.9 route. Evidence:
`work/output/upgrade_0.4.1_to_0.4.9_local_verification.json` and
`work/output/upgrade_0.4.1_to_0.4.9_upload_verification.json`.

**Latest public release: 0.4.9.** Incremental update of 0.4.8 translating the native
intermission bitmap header in WND.BIN texture #0 to INTERMISSION. All other 31
ISO files are unchanged, preserving the intervening 0.4.4–0.4.8 story/UI fixes
listed in CHANGELOG.md. Verified on the actual intermission screen in isolated
PPSSPP with a copied save and texture replacement disabled; live native texture
bytes match the ISO. Capture: `work/ui/intermission_header_0.4.9_ingame.png`;
report: `work/output/wnd_headers_0.4.9_verification.json`. Reproduce with
`python tools/patch_wnd_headers.py work/output/SRWMX_EN_0.4.8.iso 0.4.9`.
The normal `redraw_wnd.patch_wnd` build path produces the identical WND asset.
The separate sortie-preparation bitmap header (#39) still awaits translation.
The project lead explicitly requested a GitHub release for 0.4.9 on 2026-10-04.
Published at https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.9
from commit `ce426bd4676df5c7ad24ea8d93605368dfed48af`. Full final-ISO readback and
Retro Trans round-trip validation passed. All eight uploaded assets were
downloaded and verified; the 2,391,967-byte patch has SHA-256
`117ffed761b914d675ccd86d27aaa3ef463fd2df3311e80e10f6e4b607079161`.
Local assets: `work/output/release-v0.4.9/`; publication evidence:
`work/output/release-v0.4.9-publication.json`. Scoped catalog workflow
37213984223 passed; the live catalog contains the exact release manifest.
Full-playthrough and physical PSP testing remain pending.
Any future build still requires its own explicit release instruction.
Earlier build evidence follows.

**Complete campaign baseline: 0.4.3.** Rebuilt from the original Japanese ISO with the
prologue and all translated groups through 58, including the ending, hidden
stage, unused scenes and closing/save messages. All 51,366 original readable
script uses and 98,686 unchanged commands passed finished-ISO readback.
Includes the native 4x font, all 67 chapter titles, battle quotes and current UI
work. Output: `work/output/SRWMX_EN_0.4.3.iso`; SHA-256:
`e3d88c4a93c355e2e79ca5a99b45ddabe9957cb3d08397e519b43b4f47c4b352`.
Reports: `work/output/campaign_0.4.3_inputs.json`,
`work/output/campaign_0.4.3_verification.json`, and
`work/output/campaign_0.4.3_runtime.json`.
Boot and copied-save loading passed in isolated PPSSPP with texture replacement
disabled; the live native font and all 18 hooks match. The actual map-script heap
has 262,144 bytes, separate from the 1,200,704-byte resource pool. All five enlarged
map scripts (s0210, s0950, s1040, s1050, s1060) passed native replacement allocation
and complete ISO-read comparison; the test scene's non-script allocations were retained and the
original map script/allocator restored. Native ending/closing loading also passed.
Exact ending text displayed in a temporary renderer probe; the ending scene itself
was not played. Reports: `campaign_0.4.3_scene_loading.json`,
`campaign_0.4.3_extra_scene_loading.json`, and `campaign_0.4.3_ending_renderer.json`
under `work/output/`. The public English exports restore all 59 canonical inputs
and reproduce all review fingerprints and preflight checks; evidence is
`work/output/campaign_0.4.3_restoration_audit.json`. Full playthrough and physical
PSP testing remain pending. The isolated
instance is `work/build/campaign043_test`, debugger port 45379. User emulator
settings and saves were not modified. No GitHub release is authorized.

**Earlier local build: 0.4.2.** Corrects the incomplete chapter-card coverage in 0.4.1:
all 67 scenario titles are now covered across 205 atlases (160 translated,
45 existing English copies preserved). Build is `work/output/SRWMX_EN_0.4.2.iso`.
Only `PACKMAPC2_ADD.BIN` changes; all other 31 ISO files match 0.4.1 exactly.
Reproduce with `tools/patch_chapter_cards.py work/output/SRWMX_EN_0.4.1.iso 0.4.2`.
Metadata: `work/translation/en/ui/all_chapter_cards.json`; report:
`work/output/chapter_cards_0.4.2_verification.json`. English preview sheets and
native test captures are in `work/ui/`. See `docs/chapter_cards.md` for layout,
palette handling and the scope of renderer probes. Story coverage is unchanged.
0.4.2 briefly became public before the user instructed that releases must wait
for explicit permission. It is now an unpublished GitHub draft and withdrawn
from the active Retro Trans catalog; 0.4.1 remains the public release. The tagged
source is `036a619be3c23b3abdfe8ee18182a47523ddeedf`, the verified full patch is
1,574,947 bytes and local assets are `work/output/release-v0.4.2/`. All eight
uploaded assets were downloaded and checked before withdrawal. A future
approved release should use a new version because the catalog withdrawal is
permanent. Do not publish any further release without the user's instruction.

Completed translation task: dialogue after stage 30 through the ending, using
Sol 6.1 Medium sub-agents. Keep source Japanese local and preserve initial
drafts, context decisions, measured fit checks and every route/scene use.
Stages/groups 31–58 are translated and reviewed: 16,661 fresh rows and 21,257
full rows across 235 packets. Coordinator review includes all unused scenes
and all 14 independent closing/save-message sketches. Every final line fits
the actual native font; original drafts, context, measurements and original-use
evidence remain. Legacy unused-scene reachability is unverified. Local insertion
is complete and targeted native loading/rendering checks pass; full playthrough
remains pending. No GitHub release is authorized. Queue:
`work/output/stages31_end_sol_medium_manifest.json`; review notes and tooling:
`docs/stages31_end_sol_medium.md`. These later translations are in local 0.4.3.

**Earlier released build: 0.4.1.** Published at
https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.1 in the now-public
repository. The 1,396,947-byte full xdelta patch is built against the original
Japanese ULJS-00041 ISO and reproduces the complete output SHA-256
`cf4af0243dadd37718866d7ee1a6f1f8d8974d5f55dd827644227f4e58d1c7d5`.
All uploaded assets were downloaded and verified before publication. Retro
Trans's scoped catalog refresh passed and the live catalog includes v0.4.1,
so Automatic mode can discover it. Release source tag pins commit
`db7bde279f8785a04e72bbc9617bd70cb73a1f03`; later documentation commits do not
change that tag. Final assets: `work/output/release-v0.4.1-optimized/`. The older
`release-v0.4.1/` directory contains an unpublished oversized encoder trial;
do not use it. `tools/build_release.py` now uses the whole source image as its
xdelta source window to handle ISO file relocation efficiently.

Incrementally patched the latest 0.4.0 ISO, which
already contains the prologue and stages 1–30 plus the 0.3.3 battle/UI/font work.
Added the requested Kaine closing line in its three `end_mes` uses and the stage
1 Super title-card lettering, **Visitors from the Beyond**. The title-card atlas
is in `PACKMAPC2_ADD.BIN`, pixel offset `0x14e1480`, not STATIC2's title strings.
It was located by matching the live GPU image against the original file. The
native patch edits only its first 40 rows. No emulator texture replacement.
Reproduction: `tools/patch_screenshot_text.py work/output/SRWMX_EN_0.4.0.iso 0.4.1`.
See `docs/chapter_cards.md` and the 0.4.1 verification report in `work/output/`.
The title was verified in-game with texture replacement disabled. Live pixels
match the patched atlas; screenshot: `work/ui/chapter_card_0.4.1.png`. All 30
other ISO files are byte-for-byte unchanged from 0.4.0. The Kaine line's three
ISO records and its two-line fit were checked; random save-message selection
has not been forced to that sketch for an in-game screenshot.

**Earlier font test build: 0.1.5.** The user requested Genei LateGo from
https://okoneya.jp/font/genei-latin.html. Latin glyphs now use the static Medium
font at 15 px without shadows. Japanese atlas cells remain unchanged. The
matching VWF table and all eight hooks are verified in the ISO; all 21,586
prologue/campaign rows pass font-fit checks. This test build contains the
prologue, as in 0.1.2. Build 0.1.4 additionally renders Latin from a native
4x atlas (60 px TTF rasterization / 72 px cells), at the same on-screen size.
The user explicitly rejected texture replacement: this is a native ISO patch,
with no texture pack. All renderer/width/glyph/height hooks and relocated code
were verified in an isolated PPSSPP instance, with texture replacement disabled.
Translated prologue dialogue displayed correctly. Screenshot evidence uses the
software renderer at PSP display resolution; 4x hardware screenshot, physical
PSP testing and campaign insertion remain pending.
Build 0.1.5 fixes cropped bottoms in g/j/p/q/y/comma: draw the complete 60 px
glyph on a 96 px temporary canvas before fitting it into the native atlas.
All other glyphs, widths and renderer code are unchanged. Complete FreeType
mask extents are checked to prevent recurrence. Packaged before/after preview:
`work/ui/font_descenders_0.1.5.png`.
The updated 0.1.5 atlas and relocated code were also matched in live PPSSPP;
a g renderer trace confirmed the larger atlas and unchanged 8 px advance.
Dialogue capture: `work/ui/font_native4x_0.1.5_dialogue.png`.
See `work/output/font_0.1.5_verification.json`, `docs/vwf.md`, and the accompanying
`work/output/SRWMX_EN_0.1.5_FONT_LICENSE.txt` for SIL OFL copyright/licence notices.

**Completed campaign:** numbered stages 1-30, including all listed routes,
translated with Sol 6.1 Medium using six distinct actual workers per stage in
waves. All 16,092 fresh rows across 241 packets validated; full stage assemblies
contain 21,024 stage-local unique rows with every original scene use retained.
Initial drafts, final packets, decision/fit reports and safe English-only copies
are preserved. Original Japanese remains in ignored local working files.

Coordinator reviewed all reused contexts and meaningful fresh flags against
original Japanese and actual scene neighbors. Source ambiguities, wordplay and
unverified licensed-label provenance remain explicit. Exact reviewed wording
is fingerprinted; all full checks pass with the current font width table.
Final audit: work/output/campaign_completion_audit.json.
Workflow and detailed stage reviews: docs/stages01_30_sol_medium.md.
Queue and actual agents: work/output/stages01_30_sol_medium_manifest.json.

Stage 30: 680 fresh rows, 9 packets, 839 full rows, 1,116 uses. Only 464/596 were
shortened after measured initial overflow; all full initial drafts retained.
Context fingerprint:
fbea801962973b4cd17812fd97c6f901e635e1f342aae9691302ff06db792430.
Stage 28 exact copies 502/689 were corrected using guarded contextual overrides;
earlier translation owners remain unchanged. Stage 29 full 487 retained after
independent review. Source-scoped Ryo/Dr. Plato corrections are documented;
original drafts and frozen speaker labels remain intact.

The campaign was subsequently inserted in 0.4.0 and retained in 0.4.1, as
recorded above and in the changelog. Complete gameplay validation remains
pending. Existing build/version records and previous comparison results below
are retained as historical context.

**Previous model-comparison work (2026-10-03):** fresh Sol 6.1 translations at Low, Medium,
High and XHigh are complete and posted to Translation Test 3, spreadsheet
`16nyBAPVH1OSQdYo8qMxxqmS5YtceGeK45DZt9prjuWQ`, original tab id 0 preserved.
Tags: `sol61low3`, `sol61med3`, `sol61high3`, `sol61xhigh3`; each has 376/376 rows,
zero final fit/character/placeholder/name findings. Five fresh contexts per effort;
model/effort verified in all 20 sessions. Header H:K contains candidates, L:M reviewer
fields; companion notes tab id 2000000103 contains 1,044 entries. All 1,528 posted
candidate occurrences and notes were verified, and exported layouts inspected.
Estimated Standard credits: Low 32.82, Medium 36.32, High 46.62, XHigh 70.78;
these exclude coordinator work and do not establish subscription charges.
Row 357 ASCII identifiers were independently checked to preserve exact game bytes;
Low/Medium report-only follow-up costs are included. See
`docs/stage30s_sol_effort_comparison.md` and the shared protocol
`docs/model_comparison_protocol_sol_effort.md`. Inputs/glossary and earlier sheets
are unchanged. Offline CSVs, drafts/reports, 48 safe copies and usage audits are saved.
Build stays 0.1.0; next is human wording selection/reconciliation, then an in-game build.

**Earlier completed work (2026-10-03):** user requested a fresh retranslation under the updated `BASE_RULES.md`, with Luna
excluded, into spreadsheet `18CicqkxXHZezKS8AsOL27dT8CBsfLrHRP8ArL61Fn5k` ("Translation Test 2",
`Stage 30 Space` id `1180054200`, notes id `2028606084`). Sol 6.1, Astra 6 and Terra 5.6 reruns are
complete under tags `sol61r2`, `astra6r2`, `terra56r2` (376/376 rows each, all fit). See
`docs/model_comparison_protocol_r2.md`. The new sheet already has `opus2`, `sonnet2`, `fable2`
translations under the same updated rules; keep these and the Prompt tab unchanged. Event-order
context is provided to every new translator, matching the Claude reruns. Luna is absent in this
destination and is excluded. The completed sheet has six candidates, with OpenAI columns K:M and
reviewer columns N:O. All 1,146 new translation cells and 719 new notes were read back and verified;
existing Claude/reviewer values, formatting and the entire Prompt tab were preserved. Raw spelling
findings are flagged separately: Sol/Terra 287 (Jamitov Hymem vs Akurasu Hymen), Terra 308
(Guiltor vs glossary Guiltorre). Shared glossary unchanged; no raw spelling reconciliation.
See `docs/stage30s_updated_rules_openai.md` for measurements, conditions and verification.
Six-way offline CSV/notes are `work/output/stage30s_comparison_updated_rules*.csv`, with metrics,
summary, preserved full drafts and 36 new safe JSON copies. Exact instructions are saved as
`BASE_RULES_r2.md` / `TRANSLATOR_BRIEF_r2.md` in the script folder. Build 0.1.0 is unchanged.
Token usage and model/effort settings have now been recovered from session metadata; see
`docs/stage30s_translator_usage.md`. These estimates exclude coordinator work and do not establish
actual subscription charges. Next: human wording selection and reconciliation, then a separately
versioned in-game build.
The earlier comparison below is retained as a historical record.

### Earlier comparison under original rules

The requested **Sol 6.1, Astra 6, Luna 6 and Terra 5.6** candidates are complete and posted. Each
translated all 376 rows in five fresh contexts. All rows fit; Luna and Terra each have one raw
Galfa/Gulfer spelling mismatch at id 57, preserved for comparison and flagged separately in the notes
tab. See `docs/stage30s_openai_comparison.md` for requested model ids, metrics and verification.

The live sheet now contains **nine candidates**. New columns M:P hold these four models; reviewer
columns moved to Q:R. All 1,528 new translation cells and 222 new notes were verified, along with
unchanged existing cell values, formats, validation and cell notes. Existing tabs and ids are intact.
Local exports are `work/output/stage30s_comparison_openai_models.csv` and its `_notes.csv` companion.
Each new tag has five full drafts, five raw slices, reports, merged/check files and `.en.json` copies.
Luna/Terra merged files are marked `comparison_only` due to the known spelling error; all raw
candidates need selection and semantic reconciliation before production use.

The preceding single-session candidate remains available as a separate baseline:

The `codex` OpenAI-session candidate is complete: five independently translated slices, 376/376 rows,
no fit/structural errors, 37 uncertainty rows. Full first drafts and final slices are preserved, with
English-only `.en.json` copies. See `docs/stage30s_codex_review.md` for methodology and review details.

New local exports: `work/output/stage30s_comparison_codex.csv` and
`work/output/stage30s_comparison_codex_notes.csv`. They contain all five candidates in play order.
The [online sheet](https://docs.google.com/spreadsheets/d/1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY#gid=886392675)
initially gained the five candidate columns. At the user's request, the Codex column was inserted before the
reviewer columns, and 123 Codex notes were appended to the existing notes tab. All 382 posted
occurrences and the notes were verified, along with unchanged existing cell values, formatting,
validation and cell notes. Reviewer selections/comments were empty at update time. Existing sheet
IDs were retained; a pre-update snapshot and result are in ignored `work/output/`.
Build 0.1.0 is unchanged; Stage 30 remains uninserted.

Next: review the new candidate, reconcile the recalled wording in rows 190/334 and unresolved terms,
then select production text before building. All requested sheet updates are complete. The older
Codex session candidate is identified by the 2026-10-03 session metadata audit as gpt-6.1-sol at
High effort. Sol overrides used Low; Astra, Luna and Terra used Medium. See
`docs/stage30s_translator_usage.md` for all recovered counts and Standard credit estimates. Use the newer `tools/update_review_sheet.py` for in-place additions rather than
recreating existing tabs.

## 1. What this project is

An English fan translation of *Super Robot Taisen MX Portable* (PSP, ULJS00041). The user owns the ISO
(`Super Robot Taisen MX Portable (Japan).iso` in the project root). Project root: `E:\Projects\SRW MX`.

Read these first, in this order. They are binding:

1. `AGENTS.md` — folder layout, versioning (0.x.y), "always write a change log", and the REMEMBER list:
   - releases must work with Retro Trans Tools;
   - akurasu.net is the main source for terms;
   - **Japanese script text must never be committed to git** (local working files are fine).
2. `BASE_RULES.md` — how to translate and proofread (80-row slices, read neighbouring rows, restore
   dropped subjects, never infer gender from a name, report uncertainty, dry-run scripts).
3. `docs/CHANGELOG.md` — what was done, newest first.

## 2. State of the work

| Area | State |
|---|---|
| ISO analysis | Done. `docs/japanese_text_report.md`, `docs/static2_format.md`, `docs/stage_map.md` |
| Glossary | Done, akurasu-first. `work/glossary/glossary.json` (22 series, 279 characters, 260 units, 382 weapons, 723 terms). Rules in `docs/glossary_decisions.md` |
| Library (encyclopedia) | Translated (248 robot + 264 character entries), not yet inserted into the game |
| Variable-width font | Done and working in PPSSPP. `docs/vwf.md` |
| Prologue script | Translated (562 lines) and inserted. Build `work/output/SRWMX_EN_0.1.0.iso` |
| Stage 30, Space route | Original-rules sheet: 9 historical candidates. Updated-rules "Translation Test 2": 6 candidates (Opus, Sonnet, Fable, Sol 6.1, Astra 6, Terra 5.6), Luna excluded. Local comparisons saved. **Not inserted into a build** |
| Everything else | Japanese: other stages, menus, opening narration, battle quotes, default hero names |

Build 0.1.0 was booted in PPSSPP 1.20.4 and played into the prologue map's opening dialogue. Nothing
past that point has been seen on screen. Not tested on real hardware.

## 3. The task being handed over: add OpenAI models to the stage 30 comparison

The human reviewer compares translations side by side in this sheet:
`https://docs.google.com/spreadsheets/d/1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY` (tab "Stage 30 Space").
Columns today: `#`, Part, ID, Kind, Speaker (JP), Japanese, Speaker (EN), Opus 5.5, Sonnet 5.5,
Haiku 4.5, Fable 5.1, Best (model), Reviewer comment.

To add a model, produce its translation files and re-post. Keep the conditions identical to what the
Claude models had, or the comparison is not fair.

### 3.1 Input

`work/translation/en/script/stage30s.json` → `rows` (376 rows, `id` 0–375, in play order).
Fields: `id`, `jp` (raw line), `kind` (`dialogue` / `thought` / `plain`), `speaker_jp`, `speaker_en`
(pre-filled from the glossary), `body_jp` (the text to translate; `@` = line break in the Japanese box),
`uses` (scene:index).

If the file is missing (it is git-ignored), regenerate it — this reproduces it exactly:

```bash
python tools/extract_iso.py "Super Robot Taisen MX Portable (Japan).iso"
```
```bash
python tools/export_rows.py work/build/iso/MAP_ADD.BIN work/translation/en/script/stage30s.json i06s1b s06s10 i06s1a --exclude work/translation/en/script/prologue_merged.json
```

### 3.2 Instructions each translator received

The instructions every comparison candidate so far was given are frozen in
`work/translation/en/script/`: `TRANSLATOR_BRIEF_v1.md` and `BASE_RULES_v1.md`. To add another candidate
to the **existing** comparison, give it those two v1 files unchanged.
The live `BASE_RULES.md` has since gained five rules adapted from LinguaGacha's prompt template (one row
in / one row out, spoken register, a two-step context/decisions check per row, translate what the player
reads and leave what the game reads, no softening). Use the live files for new translation work.
Output produced under the live rules is not comparable with the v1 candidates unless those are re-run.
Each Claude translator got one slice and this task text (only the model tag and slice numbers differ):

> Translate a slice of the Super Robot Wars MX Portable script (stage 30, Space route: "Break through the
> Falcon") into English. Read TRANSLATOR_BRIEF.md and BASE_RULES.md (both binding). Input: stage30s.json.
> YOUR SLICE: rows with `id` X to Y inclusive. Read neighbouring rows for context as the brief requires.
> For every row write the English `en` (and `speaker_en` if empty). Check EVERY row with
> `python tools/textfit.py "<speaker_en>" "<en>"`; it must print FITS (3 lines x 352 px). Glossary:
> work/glossary/glossary.json; fixed spellings: work/glossary/do_not_touch.json. Write the result to
> stage30s_<model>_slice_<N>.json. Do not read any other stage30s_*_slice_*.json file: other translators
> are working on the same rows independently and the results will be compared. Final message: rows examined
> vs rows in slice, rows that needed compression, rows that do not fit, and your uncertainties.

Slices: 0 = ids 0–79, 1 = 80–159, 2 = 160–239, 3 = 240–319, 4 = 320–375. One fresh context per slice.

Conditions to keep equal:
- The translators could run tools (they checked fit themselves and could read the glossary and the
  finished prologue). If the OpenAI models are called through a plain API without tools, say so in the
  results, and run the fit check for them afterwards (§3.4) — expect more overflowing rows.
- They saw only the Japanese of rows outside their slice, never another translator's English.
- The input did **not** mark event boundaries on the battle map. `stage30s_order.json` now has them
  (see §5). Do not give it to the new models for this comparison; do use it for real translation work.

### 3.3 Output format

One file per slice: `work/translation/en/script/stage30s_<model>_slice_<N>.json`, UTF-8:

```json
{"slice": 0, "rows": [{"id": 0, "speaker_en": "Vega", "en": "English body only", "notes": "", "uncertain": ["..."]}]}
```

- `en` is the body only: no speaker name, no brackets. Dialogue/thought rows: one continuous text, no
  `@` (the build wraps). Plain rows: same number of `@`-separated lines as the Japanese.
- ASCII only: letters, digits, space and `, . : ; ? ! / ~ ' " ( ) [ ] + - = $ % & *`. `...` for ellipses.
- Keep placeholders verbatim: `#男愛称` `#女愛称` `#男姓名` `#女姓名` `#部隊名` `#機体名`.
- `<model>` is a short tag without spaces or `=` (e.g. `gpt5`).

### 3.4 Check, then post

Limit of the dialogue box: **3 lines × 352 px**, measured in the game. About 47 characters per line
on average; letters are 4–12 px wide, so use the tool rather than counting:

```bash
python tools/textfit.py "Ruri" "Your English line here."
```
```bash
python tools/textfit.py --check work/translation/en/script/stage30s_gpt5_slice_0.json
```

`--check` measures every row as a dialogue line, so it is right for dialogue and thought rows but not
for the two plain rows (ids 151, 152: check each `@`-separated line against 352 px yourself). A fuller
check is described in §6 "Checks". Then re-post with the new model appended (names after `=` become
the column headers; reviewer input already in the sheet is carried over by line ID):

```bash
python tools/post_sheet.py "C:\Users\Binh\Downloads\windy-renderer-507117-d4-2bb59e962d84.json" 1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY work/translation/en/script/stage30s "Stage 30 Space" "opus=Opus 5.5" "sonnet=Sonnet 5.5" "haiku=Haiku 4.5" "fable=Fable 5.1" "gpt5=GPT-5"
```

The sheet is shared with the service account `claude@windy-renderer-507117-d4.iam.gserviceaccount.com`
(Editor). The key file stays in the user's Downloads folder; do not copy it into the project.
Posting replaces the tabs "Stage 30 Space" and "Stage 30 Space notes" and touches nothing else.
Offline alternative: replace the first two arguments with `csv work/output/stage30s_comparison.csv`.

Post each model's **raw** output. Do not fix its spelling errors first; the reviewer should see them.

### 3.5 What the Claude runs showed (baseline for comparison)

All four translated 376/376 rows and no dialogue line overflowed (measured independently).

| | Opus 5.5 | Sonnet 5.5 | Haiku 4.5 | Fable 5.1 |
|---|---|---|---|---|
| Wrong glossary spellings | 0 | 0 | 9 ("Lagou" ×8, "Galfa" ×1) | 0 |
| Problems in the 2 condition rows (ids 151, 152) | 0 | 0 | 3 | 0 |
| Rows with a flagged uncertainty | 68 | 54 | 0 | 75 |
| Messages using all 3 lines | 47 | 35 | 26 | 70 |
| Total English characters | 21,757 | 20,615 | 19,138 | 22,716 |

The Claude runs used the Claude Code default effort for each model; effort was not varied.
The reviewer's picks ("Best" column) were not in yet at handoff.

## 4. How the game stores what we translate

- **Scripts**: `MAP_ADD.BIN`, 203 `SRWL` blocks from sector 0x579C. Each = header, commands (0x30 bytes
  each), then a pointer table and Shift-JIS strings. Names like `s06s10` (map) / `i06s1b` (scene before) /
  `i06s1a` (scene after) come from tables in `BOOT.BIN`. Full mapping: `docs/stage_map.md`.
- **Play order**: opcode 0x0B shows a message (arg 2 = string index), 0x0C shows two at once, 0x58 shows a
  victory/defeat condition, 0x6D plays a scene, 0x7E/0x7F delimit map events. `tools/play_order.py`.
- **Font and text drawing**: `docs/vwf.md`. English is stored as full-width Shift-JIS (2 bytes per
  letter); the patch gives those glyphs their own widths.
- **Names, library, help text**: `STATIC2_ADD.BIN`, `docs/static2_format.md`.

## 5. Tools (all in `tools/`, Python 3.8)

| Tool | Purpose |
|---|---|
| `extract_iso.py` | Pull BOOT / MAP_ADD / STATIC2_ADD out of the ISO into `work/build/iso/` |
| `static2_extract.py`, `stage_map.py`, `make_batches.py` | Rebuild `work/source/` (names, library, stage map) |
| `akurasu_terms.py`, `merge_glossary.py` | Refresh akurasu terms; merge glossaries and fix names (`--apply`) |
| `export_rows.py` | Export a scene's lines for translation (`--exclude` skips lines already done) |
| `play_order.py` | Play order + event boundaries of a stage → `<scene>_order.json` |
| `textfit.py` | Encode English and measure it against the dialogue box |
| `merge_slices.py` | Merge slice files into `<scene>_merged.json` and check them |
| `post_sheet.py` | Post a multi-model comparison to the Google Sheet (or CSV) |
| `update_review_sheet.py` | Preview and append new candidates in place; preserve and verify existing reviewer/candidate cells |
| `check_translation.py`, `export_model_comparison.py` | Check candidate slices and preserve raw review errors; export nine-way comparison and safe copies |
| `build_patch.py` | Build the patched ISO (`work/output/SRWMX_EN_<version>.iso`) |
| `vwf_patch.py`, `make_latin_font.py`, `native_font4x.py` | VWF, original-size Latin atlas and native 4x font patch |
| `ppsspp_dbg.py`, `nav.py`, `boottest.py` | Drive PPSSPP through its debugger; boot-test an ISO |
| `strip_jp.py` | Write `*.en.json` copies without Japanese script — run before any git commit |

Build command used for 0.1.0:

```bash
python tools/build_patch.py "Super Robot Taisen MX Portable (Japan).iso" 0.1.0 --scenes-file work/translation/en/script/prologue_merged.json
```

## 6. Things that will bite you

- **Environment**: Windows, Git Bash, Python 3.8 **32-bit**. Set `PYTHONIOENCODING=utf-8` or printing
  Japanese crashes. In bash heredocs, backslashes inside Python source get mangled (`'\n'`, `'\\'`,
  `'\0'`); write scripts to files or avoid backslash literals. Google libraries print version
  warnings on every run; they are harmless.
- **`textfit.py` needs `work/build/STATIC2_ADD.BIN`** (the atlas with Latin glyphs). If it is missing,
  run `extract_iso.py`, then
  `python tools/make_latin_font.py work/build/iso/STATIC2_ADD.BIN work/build/STATIC2_ADD.BIN`.
- **Do not put code at 0xE4EAC in BOOT.BIN.** It looks unused but is called once at boot from code in
  `.data`. The patch lives at 0x250944. BOOT.BIN is relocatable: any patched instruction that holds an
  address needs a relocation entry (`vwf_patch.patch_boot` handles this).
- **Script size and shared memory.** The build ceiling is 0x40000, while the actual map loader
  uses a 0x40000-byte heap shared with other allocations. Local 0.4.3's five enlarged scripts
  (largest 0x32000) passed native replacement allocation and ISO reads with existing non-script
  allocations retained. This does not prove peak memory use throughout every map event.
- **The build only rewrites scenes listed in the rows' `uses`.** Shared defeat lines are therefore
  translated only inside the scenes that have been built, not game-wide.
- **PPSSPP**: the debugger needs `RemoteDebuggerOnStartup = True`, `RemoteDebuggerLocal = True`,
  `RemoteISOPort = 45373` in the user's `ppsspp.ini`. The user approved this once; a backup is at
  `work/ppsspp.ini.backup` and the settings were restored afterwards. Ask before changing them again.
  The debugger's screenshot call fails on this machine; `ppsspp_dbg.Dbg.grab_window()` captures the
  window instead. Use `Dbg.tap()` for input; on the favourite-series screen Circle selects and the
  carousel then rotates by itself.
- **Checks**: the per-model check used for the table in §3.5 was a one-off script (completeness, fit,
  allowed characters, placeholder counts, old spellings from `work/glossary/name_fixes.json`). Its
  result is in `work/translation/en/script/stage30s_checks.json`. `merge_slices.py` has the same logic
  for a single set of slices.
- **Not a git repository yet.** `.gitignore` is in place. Run `tools/strip_jp.py` before the first commit.

## 7. Open items

Translation quality:
- Glossary gaps hit by several translators: Operation Moonraker, "junior science trainee" (Hokuto's
  and Ginga's cover story), Zeon Zum Deikun, Jamitov Hymem, Core 258, Little Baam, Ereism.
- Glossary inconsistencies: the short form of the Gulfer Emperor still says "Galfa Emperor"; one
  character entry says "Omzack of the Thunder" (the unit is "Omzack of the Lightning").
- Row 334 quotes row 190; the two must match in the final text.
- Spirit Command names: akurasu's literal names are in use (Hot Blood, Sure Hit…); the user has not
  yet said whether to switch to the official English names (Valor, Strike…).
- "Shuffle Alliance" is used (akurasu); the official SRW T English says "Shuffle Union".

Technical:
- Measure the victory/defeat condition window; the Japanese there is wider than 352 px.
- Default hero names shown through placeholders, the opening narration and all menus are still
  Japanese (they live in BOOT.BIN / STATIC2_ADD.BIN).
- The current Latin font is Genei LateGo v2 Medium (SIL OFL 1.1). Keep the
  complete source copyright/licence notice alongside redistribution. See `docs/vwf.md`.
- Insert the library translation (needs re-wrapping to its own window, not yet measured).
- Scenes `s0760`, `i076a/b`, `i063b` look unused; confirm in the emulator before skipping them.
- Check Retro Trans Tools' patch format before the first release.
- Battle quotes (`BATTLE2.BIN`) record layout is not decoded.

Waiting on the user:
- Reviewer's picks in the sheet, then tally per model and per kind of line.
- Whether to read the script pool capacity with the debugger now.
