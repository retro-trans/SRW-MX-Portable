# PS2 library corrections, local 0.4.15

The reported Hugo Medio character page had an untranslated heading, an
overlapping Voice label and a clipped biography. The description transfer
used PSP advances even though the native PS2 renderer uses a larger Latin
font. Some resulting rows also exceeded the native copy-buffer capacity.

`tools/fix_ps2_library.py` starts from the preserved 0.4.14 resources. It
translates Character Library and Robot Library on twelve heading paths,
rewraps all 512 reviewed biographies/descriptions, and moves character detail
values to a shared column. Descriptions retain words, punctuation meaning,
paragraph breaks and editable nickname placeholders. All lines fit 560 native
pixels at the existing 12x24 context (uniform 24-pixel Latin advances) and
128 encoded bytes, including maximum-length nickname expansion.

Character label x=24 and value x=104 leave a measurable gap. Values fit 302
pixels before the portrait at panel x=406; the drawing wrapper temporarily
scales oversized metadata and restores the context. Ordinary actor names,
including Hiroki Takahashi, retain their normal size.

## Resource and executable preservation

FIX00 stays below its prior 517,328-byte size: the candidate is 517,304 bytes.
Only Sent, XPlt, Xunt and the Fixh directory change. All gameplay and other
database sections are exact. Original sentence IDs remain present; obsolete
library-only rows become empty, and replacement IDs are appended below the
native signed 16-bit limit. Every nonlibrary sentence and its external address
is preserved.

New library sentences reuse unreferenced library storage in the existing ELF
pool. An additional 15,540 bytes of text, headings and one metadata wrapper
extend the font/text segment to 0x7d8980, below STATIC at 0x800000. Every
existing executable change is restricted to twelve heading-reference pairs,
three coordinate words, one checked library draw call, proven obsolete text
storage and ELF size/heap bookkeeping. All other disc resources are exact
0.4.14 copies, including the AI name and corrected status/AT/CT artwork.

## Checks and reproduction

Run with the configured 32-bit Python that provides Keystone, Unicorn,
Capstone, Pillow and pycdlib:

```powershell
py -3.8-32 -X utf8 tools/fix_ps2_library.py --build
```

Existing builds are protected from overwrite. To recheck the prepared
candidate, use `--verify-existing`; add `--build` only before its ISO exists.

`tools/verify_ps2_library.py` independently compares source and candidate
resources, executes all 4,708 native line widths and sentence reads, checks
native page counts/line lookup, and exercises all twelve headings and 103
metadata values. Original overflows are regression fixtures: 3,059 overwide
rows and 3,020 rows over the buffer limit. Maximum-length nickname cases
check expanded width and bytes. Font hooks and unchanged fallback behavior
are also exercised.

The value-fitting wrapper uses the EE-supported `CVT.W.S` conversion. Its
entire COP1 instruction set is checked against the native subset documented
by the [PCSX2 R5900 opcode table](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/R5900OpcodeTables.cpp#L566).
The unpublished candidate was corrected before delivery, and the affected
native/regression, disc and fresh-boot resource checks were repeated.

The existing narration, campaign, favorite selection, prologue, UI, detail,
roster and setup/save checks execute current code. Historical byte/retained-row
comparisons use the pre-library snapshot only after structural verification
proves every unrelated byte, sentence and section remains exact. The campaign
text check now reads the current candidate database and current reflowed line
lists. Prior battle/status/map pixel proofs carry forward with explicit exact
preservation evidence.

Evidence: `work/output/ps2_library_0.4.15_execution.json`, the candidate's
`library.json`, and `work/ui/ps2/library_0.4.15/`. Only English copies and UI
terms are suitable for Git; raw Japanese script source remains ignored.

Final ISO9660/UDF readback verifies all 37 files. Only FIX00 and the ELF differ
from 0.4.14. The image is 4,663,291,904 bytes, SHA-256
`c4fbc932b67a04088c6bbd6213c9aa008bea42fef733b56b39b4ff388aa82676`.
A fresh boot in the separate `ps2_library_test_0.4.15` emulator profile on
PINE port 28031 verifies the complete 801,080-byte text segment, all 28 changed
library code/data words and the exact 517,304-byte loaded FIX00 database.
No unknown opcode or TLB warnings occur. The user's normal emulator and
memory cards are not controlled. Read-only runtime checks are in
`tools/verify_ps2_library_runtime.py` and
`work/output/ps2_library_0.4.15_runtime.json`.

These tests establish layout arithmetic, indexed paging and preservation.
In-game library visual acceptance and physical PS2 play remain pending.
Fresh boot the local ISO so the new executable and database are loaded.
Public releases remain 0.4.12; this work does not authorize a GitHub release.
