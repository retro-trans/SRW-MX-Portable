# Title-screen credit and build version

Every newly numbered PSP/PS2 build displays two right-aligned lines:
`v<build version>` and `github.com/retro-trans`, following SRW Z3.
The footer remains visible after opening the title menu. PSP uses larger white
outlined text at the bottom right without a panel; PS2 uses a native title draw callback above the
menu. Both use the existing Genei LateGo font.

## Native assets

PSP uses the title-logo texture, TX48 #44 in `OPWND.BIN`: palette at
`0x2d3b40`, pixels at `0x2d3f40`, 512 x 256. From 0.4.29, the footer rectangle
is `(243,133)-(417,173)` in the texture, using 14px white text with a dark
outline and no background panel. The native title logo is drawn at screen
`(55,5)`, giving footer screen bounds `(298,138)-(472,178)` on 480 x 272,
above the title menu. The user accepts a little overlap with the logo.
The temporary upper-left panel from 0.4.27/0.4.28 is restored to original
transparent pixels. Before replacement, the complete title texture must
match original art or an exact registered footer; unknown artwork is rejected.
Historical versions retain their original layout for reproducible readback.
No quad coordinates or animation commands change. The similarly named title
background in `IM_ADD.BIN` is a separate story image and is not the PSP menu
background; a fresh emulator boot caught and rejected that initial target.

From 0.4.26, PS2 uses `tools/ps2_title_footer.py` in `SLPS_253.45`. Its callback
at `0x2c1e28` preserves the original draw call and adds two lines through a
private native font context. The 16px text is right-aligned to x626 at y250
and y268, gated to title/menu states. The old IM #141 footer was not visible
on the animated native title and is removed by the correction builder.
Native execution checks pass; live PS2 placement remains pending after the
user stopped computer use. Earlier asset readback is not proof of visibility.

## Build integration

`tools/title_footer.py` receives the requested build version, reconstructs the
footer from original artwork, rejects unknown artwork and prevents overlapping
or overflowing text. Replacing a registered earlier footer is supported;
reapplying the same version is idempotent. `verify_iso` checks the actual
output disc pixels and the PS2 UDF view, rather than trusting its filename.

- PSP full builds: `tools/build_patch.py`, also used by `build_campaign.py`.
- PS2 full builds: `tools/build_ps2_campaign.py`.
- PS2 compact packaging: `tools/package_ps2_stage30.py`.
- Incremental builds: call `build_title_footer.stamp_existing(output, platform,
  version)` **before** final hashes/manifests; incorporate its returned resource
  hash and declared pixel spans into preservation checks. Do not mutate an
  existing accepted candidate or use an old fixed-version correction script
  unmodified for a new build.
- Footer-only candidates: `tools/build_title_footer.py --base 0.4.22
  --version 0.4.23` creates both editions without rebuilding story resources.
- Release packaging: `tools/build_release.py` rejects a missing/mismatched
  footer for versions 0.4.23 onward; historical releases remain reproducible.

The visible version, output filename and verification manifest must agree.
This rule is saved in `AGENTS.md`. Local builds do not authorize a release.

## 0.4.23 scope and checks

The local candidates inherit 0.4.22 and add only title-footer pixels.
They do not incorporate the later source-only campaign proofreading changes,
including Saburota's Chapter 17 follow-up. File readback, all other disc bytes,
size preservation, repeated stamping, version changes and rejection of unknown
palettes/outside edits/overflow are checked. Native previews are in
`work/ui/{psp,ps2}/title_footer_0.4.23/`; live evidence is recorded separately.

PSP fresh-boot evidence matches the entire native title texture to the ISO
and confirms the footer above the menu rows with texture replacement disabled.
`tools/verify_title_footer_runtime.py` captures native PSP VRAM and records
the test profile, texture address and pixel hash. PS2 live placement is pending.
