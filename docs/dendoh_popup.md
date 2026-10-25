# PSP Dendoh form-choice window

The Choose Sortie Units screen uses a dedicated `CWndDendohChoice` popup for
Full Armor Dendoh / GEAR Fighter Dendoh. Its native width was fixed at 128 PSP
pixels, so both translated labels crossed the right border at the existing font
size. The user requested a wider box rather than shorter names.

`tools/fix_psp_dendoh_popup.py` changes only the width immediate at native code
address `0x1b19a0` (executable offset `0x1b1a00`) from 128 to 176. The native setup
continues to center the box: x=152, y=111, width=176, height=50 on a 480x272 screen.
It also expands the selection highlight automatically. Names, row offsets,
fonts, form selection, input logic, object size and save layout are unchanged.
The regular PSP build path applies this guarded, idempotent patch.

`tools/verify_psp_dendoh_popup.py` executes the actual option initializer, popup
setup, shared draw routine and VWF width calculation in Unicorn, intercepting
only graphics service calls. Both selections reproduce the original overflow
and pass after the patch. The native width is 115px for Full Armor Dendoh and
134px for GEAR Fighter Dendoh. Their right edges after widening are 289 and 302,
inside the box's right edge at 328 with the required 8px inset. The original
font context (18,18,15,15), two choices, highlight dimensions and object guard
are checked. Restoring the width instruction reproduces the original BOOT
exactly. This verifies native geometry, not a new in-game screenshot.

Local PSP v0.4.42 is based on verified v0.4.41. The incremental builder patches
the existing BOOT/EBOOT extent(s) in place, handles shared extents once, and
regenerates the native title footer as v0.4.42 with github.com/retro-trans.
Complete source/output hashing and actual ISO executable/footer readback check
the result. Every directory record, resource size and unrelated disc byte is
preserved. Earlier translation, rename, Parts, header and battle-caption fixes
remain intact. PS2 remains at local v0.4.41; this code change is PSP-specific.

- Builder: `tools/build_psp_dendoh_popup.py`.
- Test ISO: `work/output/SRWMX_EN_0.4.42.iso`.
- Verification: `work/output/psp_dendoh_popup_0.4.42_verification.json`.
- Reported screenshot and native coordinate evidence:
  `work/ui/sortie_popup_2026_10_24/`.

Fresh in-game visual acceptance is pending. GUI testing was not resumed.
This is a local test build; public release and Retro Trans Tools remain v0.4.38.
