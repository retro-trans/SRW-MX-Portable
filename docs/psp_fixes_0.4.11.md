# PSP 0.4.11: menu alignment and music titles

Addresses all six screenshots reported on 2026-10-06. Local testing build;
the published release remains 0.4.9.

## Changes

`tools/fix_psp_menu_alignment.py` redirects five native draw calls. The
wrappers call the existing VWF-aware width routine, preserve draw arguments
and return through the original renderer. Existing JAL relocations are reused;
new wrapper jumps have explicit R_MIPS_26 relocations.

| Screen | Draw call | Horizontal center |
| --- | --- | --- |
| Unit rename choices | 0x1C84C0 | object.x + 340 (native highlight x + 260, width 160) |
| Hero / Partner choices | 0x1C8D24 | object.x + 340, choice rows only |
| Options | 0x1CA3CC | 240 |
| Demo rows | 0x1D0488 | object.x + floor(panel width / 2) |
| Music rows | 0x1D151C | 240 |

The native Japanese width estimates are overridden only at these draws.
Vertical positions, font sizes/styles, selection logic and text limits remain
native. Name, nickname and sex labels are not centered by the choice wrapper.
The same hook is included in `tools/build_patch.py` for subsequent full builds.

`work/translation/en/static2/music.en.json` maps 80 Strg IDs to English music
titles. Source: [Akurasu's MX BGM list](https://akurasu.net/wiki/Super_Robot_Wars/MX/BGM),
refreshed through `tools/akurasu_terms.py` into the ignored local cache
`work/source/music_0411/`. For the two very long G Gundam titles, the page's
short romanized forms fit the menu. Entries absent from that page are labeled
in the mapping's notes; unused slot placeholders are retained. The normal
name-table generator now reads this mapping.

The incremental builder preserves the existing 3,754 overflow pointers in a
new relocated table, appends the music strings, and retargets all three shared
getter address pairs. Only the 80 Strg offset words change in STATIC2. Its
file size and section positions remain unchanged.

## Validation

- `tools/verify_psp_0411.py`: executes every wrapper and the actual native
  VWF routine in Unicorn. Only GPU drawing is intercepted. Checks centers,
  argument restoration, pilot label filtering, music fit and all title pointers.
  Maximum music width is 413 px at size 20, below the 427 px text limit.
  Native Level Up and narration regression fixtures from 0.4.10 also pass.
- `tools/verify_text_build.py 0.4.11`: 1,763 correct BOOT references, zero
  wrong references; all 1,580 English names read back from the ISO.
- Fresh boot in an isolated PPSSPP profile: Hero Setup, Partner Setup,
  Cerberus Rename Unit, Options, Sound Select and Demo Select render correctly.
  Screenshots are under `work/ui/psp/fixes_0.4.11/`.
- The test save naturally exposes eight songs and Opening. Two controlled
  debugger fixtures replace only the active window's temporary list to show
  the nine music rows reported by the user and all three demo rows. Native
  database getters and the renderer run normally; unlock flags and savedata
  are untouched. These screenshots end in `_fixture.png`.
- All 32 disc files pass readback hash checks. BOOT.BIN and EBOOT.BIN are
  identical. The other 29 files match 0.4.10 exactly. Deterministic patch
  reproduction and Python compilation checks pass.

## Build and outputs

Run `python tools/fix_psp_0411.py` with the 0.4.10 ISO present. The builder
refuses to overwrite an existing versioned output. The full build also reads
the music mapping through `tools/build_static2_names.py` and includes the
alignment hook.

- ISO: `work/output/SRWMX_EN_0.4.11.iso`, 1,317,414,912 bytes.
- SHA-256: `50e6440438778cc6da32d963c9500e0b4265afb6142bdc360913b55081600f58`.
- Disc verification: `work/output/psp_fixes_0.4.11_verification.json`.
- Native tests: `work/output/psp_fixes_0.4.11_native_tests.json`.
- Font license: `work/output/SRWMX_EN_0.4.11_FONT_LICENSE.txt`.
