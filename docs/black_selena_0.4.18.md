# Black Selena — local PSP and PS2 0.4.18

The user's PSP screenshots show **High-maneuver Black Sarana** in Unit Stats
and Robot Library, with the same spelling in the description. Both platform
builds now use **Black Selena**, retaining the existing form qualifier.
The Sarena variant is normalized too, including the associated music title
Black Selena III. The requested override of Akurasu MX's Sarana spelling is
recorded in `docs/glossary_decisions.md` and the current glossary decisions.

Each encoded surname has six characters, so text storage, terminators and
all pointers retain their addresses. Both native font tables measure the
new spelling narrower: PSP 39px versus 43/42px, PS2 61px versus 66/65px.
Existing lines retain their breaks; descriptions and unit names cannot gain
overflow from this correction. Commands, textures and executable code are
preserved. Every byte outside the declared terminated text allocations is
compared with the local 0.4.17 base.

Expected corrections: 13 PSP occurrences across BOOT/EBOOT, STATIC and MAP;
9 PS2 occurrences across the executable text pool, FIX00 and MAP. The shared
builder verifies every disc file, all 203 script blocks per platform and both
PS2 filesystem views. All earlier Albero Est and AT Field corrections remain.

Reproduce: `py -3.8-32 -X utf8 tools/fix_black_selena.py --inputs --build`.
Use `--verify-existing` for existing images; do not overwrite historical builds.
Reports: `work/output/psp_black_selena_0.4.18_verification.json` and
`work/output/ps2_black_selena_0.4.18_verification.json`.
Images: `work/output/SRWMX_EN_0.4.18.iso` and
`work/output/SRWMX_PS2_EN_0.4.18.iso`.

Isolated PSP fresh boot verifies both native unit-name strings in RAM, the
changed library/music pool strings and all 3,837 relocated pointers. The
native Strg resolver checks indices 204, 206 and 1738 against the corrected
full labels. Reproduce with `--runtime` against the owned profile on port
45394; this does not modify the user's emulator profile.

Affected Unit Stats/Robot Library playthrough, PS2 live checks and physical
hardware tests remain pending. No release is authorized.

Both builds pass all resource checks (32 PSP / 37 PS2), native script-table
checks, absence of old spellings in every accessible disc file and the full
disc comparison outside declared text allocations. Both PS2 filesystem
views read back the same verified resources.

| Platform | SHA-256 |
|---|---|
| PSP | `85661aa0da298c5a49e1cb9dd9ef7e34c8094762a6c111f803a33731d0445635` |
| PS2 | `8c8b3e2583b46239c27fa0f1bdaf81c23800fcfa245c351e907f3eb45e6f7d57` |
