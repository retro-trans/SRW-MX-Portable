# Albero Est correction — local PSP and PS2 0.4.17

The user's screenshot shows Hugo introducing his former commanding officer
as Albero Esto. The requested spelling is **Albero Est**. The same correction
applies to full-name tables, all matching story lines and battle dialogue in
both platforms. Short-name Albero, ranks, dialogue wording and line breaks
are preserved. The glossary decision is recorded in `glossary_decisions.md`.

Both images use local 0.4.16 as their base. The correction removes the final
encoded `o` in the surname and terminates each string earlier, filling the
remaining allocation with zero bytes. Every pointer and allocation remains
at its original address. No script is rebuilt and no instruction is patched.

The builder scans every disc file for both ASCII and full-width encodings,
including names split across dialogue lines. Expected occurrence counts are
43 for PSP (25 story, 16 battle, one full name in each identical executable)
and 44 for PS2 (27 story, 16 battle, one FIX00 full name). Verification checks
all 203 story blocks on each platform, preserving commands, string pointers
and every unrelated string. It also checks all disc-file hashes, both PS2
filesystem views, and every byte outside the declared text allocations.

Reproduction: `py -3.8-32 -X utf8 tools/fix_albero_est.py --inputs --build`.
Do not overwrite versioned images; `--verify-existing` audits existing builds.
Reports: `work/output/psp_albero_0.4.17_verification.json` and
`work/output/ps2_albero_0.4.17_verification.json`.

An isolated PSP fresh boot verifies that the native full-name table resolves
to **Albero Est** and all 3,837 relocated text pointers retain their expected
addresses. Run `--runtime` against the owned test profile on port 45394.
This confirms the corrected full name is loaded; it does not claim a story
playthrough or a PS2 live check.

Local test images: `work/output/SRWMX_EN_0.4.17.iso` and
`work/output/SRWMX_PS2_EN_0.4.17.iso`. Affected dialogue playthrough and
physical-hardware validation remain pending. No release is authorized.

Both disc checks pass: all 32 PSP and 37 PS2 files read back correctly,
both PS2 filesystem views agree, no old spelling remains in accessible disc
files, and no bytes outside the declared text allocations differ from 0.4.16.

| Platform | SHA-256 |
|---|---|
| PSP | `d8a60aff9c1a285f35e3a54ea097823fe4d48529eea11b658fcf988172c20e14` |
| PS2 | `2987863fd649e00b25a71d38ef0130043e4416d789754deecf312efd73d1193c` |
