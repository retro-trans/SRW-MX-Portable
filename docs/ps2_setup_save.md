# PS2 0.1.14 save, setup and series UI

Build locally with `python tools/fix_ps2_setup_save.py --build`. Input is
the preserved `work/build/ps2/roster_system_0.1.13/` candidate. Output is
`work/output/SRWMX_PS2_EN_0.1.14.iso`; prepared resources and native patch
metadata are in `work/build/ps2/setup_save_0.1.14/`.

The patch adds an English text pool, replaces ten local literal address
pairs and 24 description/confirmation table references, removes the age
suffix in the fixed seven-byte copied values, and changes the protagonist
value-column offset from 108 to 140. Yes and No both use offset 26.
Dialog control flow, controller handling, memory-card operations and the
save-progress bar are unchanged.

Both unit descriptions retain the Tsentr Project, prototype humanoid
mobile weapon and Terminus Energy meaning. Garmraid emphasizes melee
combat; Cerberus emphasizes high mobility and bombardment. Lines use the
existing glossary and fit within 300 native pixels at 24px font size.

The series selector previously centered titles by counting every English
character as a full 24px cell. Its final draw at `0x1660a8` now measures
the native VWF width, centers it on the 640px window, and scales width and
height by the same factor only when wider than 456px. The 480px title box
keeps 12px padding on each side. The shared baseline is preserved and the
font context is restored after drawing.

`tools/verify_ps2_setup_save.py` runs real native argument setup, line
registration, Yes/No initialization, protagonist header/branches, age
copies, description rows, both final-button selections and series draws.
The original 18 series names and two
stress/fallback strings run at two font sizes. Prior native regression
checks are included by the builder. Every .BIN/.DAT file remains identical
to 0.1.13. Validation reports distinguish native execution from visual
confirmation; neither substitutes for physical-console testing.

Test after a fresh disc boot. Old emulator save states contain the old
executable, so they cannot validate a rebuilt UI. Memory-card saves remain
compatible. This candidate is local; no release or push is authorized.

Final ISO: 4,663,267,328 bytes. SHA-256:
`92b871792cbb936d74b72394d9d97cd1e73022bc3574c2d113608e4ee8cde14f`.
All 37 disc resource checks pass. Fresh PCSX2 2.8.2 loaded-byte checks
confirm the immutable native segment and 164 hook/reference words at 4x,
without texture replacements or opcode/TLB warnings. Protagonist Setup
is visually confirmed in `work/ui/ps2/setup_save_0.1.14/`; other reported
panels await visual confirmation, with native execution checks passing.
