# PS2 narration clipping correction — local 0.4.13

The reported screenshot belongs to SRW MX on PS2. Long English lines in the
opening crawl extend beyond the right side of the game viewport. The same
wrapping error affects the ending crawl.

## Cause and correction

`tools/ps2_narration_port.py` previously used PSP text-fitting advances to wrap
the PS2 strings. The native PS2 crawl uses the packaged 24-pixel font, whose
advances are larger. Executing the native width routine at `0x131ba0` reproduces
33 lines wider than the corrected 560-pixel limit, including 635 pixels for
the Gryps Conflict / Devil Gundam line shown in the report.

The wrapper now measures the exact glyph advances from the PS2 font metadata,
keeps whole words, and limits each encoded row to 128 bytes including its
terminator. At the reported text origin of approximately x=68 on the native
640-pixel viewport, 560 pixels leaves a right margin. Font size remains 24.
Editable protagonist nicknames reserve six full-width characters each.

Opening is wrapped into 30 lines, maximum 557 pixels; ending into 26 lines,
maximum 558. Every word and runtime placeholder is preserved. Both original
12-byte timed record sequences retain their command words, delays, record
counts and end markers. Blank records absorb the additional line count within
the existing sequence. New strings are appended to the existing font segment;
only narration pointer words and executable/heap size bookkeeping change.

## Verification

- `tools/verify_ps2_narration.py` executes all 56 corrected lines through the
  native MIPS width routine, independently of the wrapper. It expands both
  nickname placeholders to their maximum native width. All rows fit.
- Decoded table strings match the prior translated wording and placeholders.
  Exact byte comparisons prove the earlier executable code and string pools
  remain unchanged outside the permitted pointer/size words.
- Narration, stage-30/campaign, favorites, prologue, UI, UI details, roster/system
  and setup/save regression suites all pass. Favorites checks cover all 1,632
  triple/mode combinations and the native save/bonus paths.
- Both ISO9660 and UDF verify all 37 packaged disc files. Only
  `/SLPS_253.45;1` changes from the public PS2 0.4.12 image, whose historical
  local test label is 0.1.18.
- Fresh-boot emulator memory verification confirms the loaded corrected font
  segment and all hook/reference words match the packaged executable, with no
  unknown-opcode or TLB-miss warnings at that check. Visual crawl review is
  recorded separately below; physical-console testing remains pending.

Evidence:

- `work/output/ps2_narration_0.4.13_execution.json`
- `work/output/ps2_font_0.4.13_verification.json`
- `work/output/ps2_font_0.4.13_runtime.json`
- `work/output/ps2_narration_0.4.13_build.log`
- `work/ui/ps2/narration_0.4.13/`

## Build and test

Use the project's Python runtime with the existing native-emulation libraries:

```powershell
py -3.8-32 -X utf8 tools/fix_ps2_narration.py --dry-run
py -3.8-32 -X utf8 tools/fix_ps2_narration.py --build
```

The builder preserves existing candidate/output files and requires the prior
prepared 0.1.18 resources. It does not publish a release. The isolated test
profile prepared by `tools/test_ps2_narration.py` uses copied test memory cards
and PINE port 28029; the normal emulator profile is untouched. Boot the new ISO
freshly to load the corrected executable.

Output: `work/output/SRWMX_PS2_EN_0.4.13.iso`, 4,663,275,520 bytes.
SHA-256: `28dd376b20d54381a85c0b1073191212f66a07fead5fe71603d7fdaba0995e0c`.
This is a local PS2 candidate. Public releases and PSP remain at 0.4.12.

## Visual review

The isolated profile booted the verified ISO through the BIOS and opening
movie. Read-only memory checks passed for the loaded correction. Desktop
controller inputs did not reliably leave the attract sequence and enter New
Game, so no visual crawl walkthrough is claimed. The isolated test process
was stopped; the normal emulator was not controlled. Native width execution
covers both crawls; an ending playthrough has not been performed for this
change.
