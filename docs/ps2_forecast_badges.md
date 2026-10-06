# PS2 0.1.17 CT and AT forecast badges

Build with `python tools/fix_ps2_forecast_badges.py --build`. Output is
`work/output/SRWMX_PS2_EN_0.1.17.iso`, preserving 0.1.16.

The native WND images IM_IC00S (AT) and IM_IC01S (CT) use a 32×32 texture
with a 24×24 opaque badge. The previous PSP-to-PS2 icon mapping doubled
the PSP inner rectangle to 4..32, erasing the lower/right frame and
placing letter pixels in padding outside the native visible badge. The
shared graphics-port renderer now uses explicit native bounds for these
two assets, so a full rebuild also retains the correction.

Both assets now use the actual 2..22 inner rectangle. AT and CT are
centered at the same cap height, with their natural proportions. The
original gold frame and transparent padding are restored. Palette,
header, texture dimensions, draw coordinates and native crop stay intact.
Only these two 1,024-byte WND pixel payloads change. All other prepared
resources, including the executable and MAP, match 0.1.16 exactly.

The verifier checks every byte outside the declared payloads, original
frame/padding equality, header/palette equality, letter bounds and the
absence of opaque pixels beyond the native 24×24 area. Decoded before/
after assets and the user's actual screenshot are in
`work/ui/ps2/forecast_badges_0.1.17/`. The comparison is an asset preview;
actual in-game confirmation remains pending.

The previous native execution checks are carried forward with an explicit
reuse reason because executable bytes and every previously prepared
BIN/DAT resource are identical. Disc packaging verifies all 37 files and
the replacement files through ISO9660 and UDF. No release or push.

All 37 disc-file checks pass. Comparing final disc hashes against 0.1.16
confirms that only WND.BIN changes. A full run of the shared graphics
renderer exactly matches the incrementally patched WND archive.

Final ISO: 4,663,267,328 bytes. SHA-256:
`5e181905226266c4ea51f769acf219e24c62ee18e2edf851011a1924cbb3739f`.
