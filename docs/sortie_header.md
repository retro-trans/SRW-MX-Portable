# Sortie Prep header — 2026-10-24, local v0.4.41

The highlighted heading means **Sortie Prep** (sortie preparations). Its
translation already existed in the UI table, but PSP texture 39 had no native
text-box configuration, and the corresponding PS2 header was omitted from the
earlier artwork port.

| Platform | Native asset | Texture | Text box | Origin | Mask height |
|---|---|---|---|---|---|
| PSP | `WND.BIN` | TX48 index 39, `0x2eb80`, 512×32 | `(10,4)-(150,25)` | `(14,6)` | 16px |
| PS2 | `WND.BIN` | P2IG `IM_W10`, `0xc7040`, 1024×64 | `(20,4)-(194,32)` | `(26,6)` | 22px |

The replacement uses the existing header font and native palette, with the
complete title-case label and no horizontal squeezing. Only indexed pixels in
the registered text rectangle change. The flat navy background, slanted bar,
blue line, transparency, palette, dimensions and every other resource byte stay
exact. Unrecognized source artwork is rejected; applying the patch twice is
idempotent.

`tools/sortie_header.py` applies and verifies the guarded rectangles. The PSP
regular builder uses the new texture-39 configuration through `redraw_wnd.py`.
Both PS2 build paths and `ps2_graphics_port.py` apply the same replacement;
regular-builder header output was compared with the incremental result on both
platforms. Historical PS2 comparisons restore only the registered header pixels
after verifying that reapplying the patch reproduces the current resource.

Local candidates are created from exact verified v0.4.40 images with:

```text
tools/build_battle_banners.py --base 0.4.40 --version 0.4.41 --artwork sortie_header
```

Both native title footers are regenerated as v0.4.41 with the project credit.
Complete source/output hashes, actual ISO header/footer readback, retained file
positions/sizes and PS2 ISO9660/UDF agreement verify the candidate images.
All earlier fixes remain included. Fresh in-game display is pending; no release
was requested, and public v0.4.38 is unchanged.

Reported screenshot: `work/ui/sortie_header_2026_10_24/reported.png`.
Actual output previews: `work/ui/{psp,ps2}/sortie_header_0.4.41/iso_readback/`.
Verification: `work/output/{psp,ps2}_sortie_header_0.4.41_verification.json`.
