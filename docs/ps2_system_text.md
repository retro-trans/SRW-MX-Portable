# PS2 0.4.19 — Option menu, save/load screen and memory-card dialogs

`tools/fix_ps2_system_text.py` (build with `--build`) starts from local PS2
0.4.18. The general UI port only repointed Japanese strings that had exactly
one PSP translation, so PS2-only memory-card (PS2) messages and a few labels
with several PSP renderings stayed Japanese.

What changes, all in `SLPS_253.45`:

- An English pool (79 strings, 3,136 bytes) is appended to the extension
  segment, inside one signed-low 64 KiB page so shared `lui` words need a
  single high half.
- 12 data pointer words: Option menu table (0x4c18f8/fc), library header
  table (0x495d78/84) and both save/load column-header tables.
- 59 `lui`/`addiu` groups found by the same register-liveness scan as the
  original UI port, plus 11 literal pairs completed in branch delay slots
  (listed explicitly, each word checked).
- Four save-slot labels (Clear Data, No data, Corrupt data, Not enough
  space) were copied inline with a fixed byte count. Each block now calls the
  library strcpy (0x36ae10) into the same 256-byte buffer at sp+0x90 and
  reloads a3/t0 exactly like the scenario-name branch at 0x192a00.

English line widths are checked with the native PS2 glyph advances: labels
fit their Japanese width, dialog lines stay within 600 of the 720-unit
message window. CWndMessage::AddItem stores line pointers, so long lines
need no buffer changes.

Verification: every repointed reference decodes to its English string, no
translated Japanese string is still addressed, and Unicorn executes the
four slot blocks (strcpy itself uses EE MMI instructions, so the check stops
at the call, verifies its arguments and resumes). The ELF is the last disc
file and grows in place; all 37 files match through ISO9660 and UDF.

Not translated: the boot health-warning screen (an image; user decision).
