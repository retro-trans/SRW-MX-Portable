# SRW MX PS2 ↔ PSP save converter handoff

Handoff **0.1.0**, 2026-10-06. Destination: `retro-trans/retro-trans-tools`.
Source project: `E:/Projects/SRW MX`. Current PS2 test build: **0.1.14**.

## Objective and current status

Implement an offline MX save converter in Retro Trans, in both directions,
with a balance choice when producing saves for the PS2 English port. Start
with manual scenario/intermission saves at shared checkpoints. Extend to
system data and battle suspend only after their layouts and relationships
have been mapped and tested. Do not silently discard required system state.

**No cross-platform conversion has been demonstrated.** This handoff provides
measured containers, integrity rules, native difficulty persistence and
campaign information. Equal payload sizes and many matching zero bytes do
not establish field compatibility. The portable reference utility only
checks PS2 integrity and edits its known balance extension; it is not a
cross-platform converter or a complete save-format validator.

The local Retro Trans checkout inspected for integration was commit
`64d4deec88e045d5cddef2d008d0c3df2ad193af`. Recheck current code before work.
Reuse its Z3 conversion workflow, worker/progress/cancellation interfaces,
source hash checks, backups and verified output packaging. Add a separate
MX codec; Z3's endian reversal and checksum rules do not apply to MX.
Relevant files: `retro_trans/z3_saves.py`, `retro_trans/gui.py`,
`retro_trans/core.py`, `tests/test_z3_saves.py`, `tests/test_gui.py`, and
`retro_trans/resources/Z3-SAVE-CONVERSION.txt`.

## User flow and difficulty selection

Offer a game selector in Save conversion, retaining Z3. For MX:

1. Choose **PSP → PS2**, **PS2 → PSP**, or both, then select the source saves,
   required destination templates and a new output folder.
2. Choose the destination game profile: **PSP MX Portable**, **PS2 English
   port with PSP stages (validated build)**, or **original PS2 campaign**.
   Do not infer campaign compatibility from the unchanged PS2 game ID alone.
3. For the patched PS2 destination, show **Game balance** with:
   **Keep source balance**, **PS2 – Original**, **PSP – Harder**.
   Default to Keep source balance: valid patched-PS2 markers are preserved;
   PSP imports resolve to PSP – Harder; legacy original PS2 saves resolve to
   PS2 – Original. Explain the resolved mode in the checked preview.
4. Explain PSP – Harder as **higher enemy HP and lower funds rewards**.
   Detail text may say most compared enemies have +50% base HP and shared
   changed rewards are −20%. This is the port's HP/reward setting, not a
   promise of every PSP gameplay mechanic.
5. For original PS2, disable PSP – Harder and say it requires the PS2 English
   port with the balance feature. For PSP output, show **PSP balance (fixed)**;
   the PSP game does not read the PS2 extension and has no implemented PS2
   balance option. Explain that converting an easier PS2 campaign to PSP
   changes future gameplay balance; do not rescale accumulated funds.
6. Close the emulators, **Check saves**, review slots, checkpoint/route,
   destination profile, effective balance and any unsupported content, then
   **Convert saves**. Changing any input/profile/mode invalidates the check.
7. Save new outputs, original backups, a conversion report and import guide.
   For both directions use separate output subfolders and read the original
   snapshots for each direction; never feed one converted output into the
   other direction automatically.

Keep the UI focused on these decisions; offsets/checksum details belong in
developer logs. Destination templates supply container metadata/icons only;
never overwrite converted progression with template progression.

The PS2 game also already offers a balance prompt during New Game setup.
Complete protagonist/partner and robot setup, choose Finish Setup, then at
**Choose the game balance** select **PSP – Harder** with the directional
controls and confirm with the game's normal confirm button. Cancel follows
the existing return path. The choice is persisted when saving. Loading a
save restores its stored mode rather than reopening the New Game prompt.
Retro Trans must set the saved mode for a converted campaign; starting a
separate harder New Game does not change the imported save's mode.

## Confirmed containers and samples

| Kind | PS2 observed directory / payload filename | PS2 bytes | PSP observed directory | Encrypted DATA.BIN bytes | Decoded bytes |
|---|---|---:|---|---:|---:|
| Scenario/manual slot 1 | `BISLPS-25345S00/BISLPS-25345S00` | 54,272 (`0xd400`) | `ULJS000410000` | 54,288 | 54,272 |
| System | `BISLPS-25345/BISLPS-25345` | 138,240 (`0x21c00`) | `ULJS000419999` | 138,256 | 138,240 |

These are observed slots, not an established formula for all slot names.
Determine every supported slot mapping from native code and fixtures.
The larger save is system data; it is not proven to consist solely of
battle suspend data. Some gameplay/global state may require a paired file.

PS2 exports contain `icon.sys` and `mx1.ico` / `mx0.ico`. PSP directories
contain `PARAM.SFO`, `DATA.BIN`, `ICON0.PNG`, and `PIC1.PNG` in these samples.
Emulator save states are a different format and must be rejected.

Samples at `work/source/save_compare/` are local, ignored research data.
They come from different progression and are **not a matched checkpoint
pair**. Their hashes are in `work/output/ps2_psp_save_comparison.json` and
the portable `facts.json`. Originals must remain read-only. No save data,
icons, game executables, ROMs or encryption key bytes are bundled here.

PS2 card extraction: `tools/ps2_memcard_read.py`. It supports card images
with data-only pages or pages with spare/ECC bytes, validates directory
chains and lengths, but **does not validate or generate ECC**. It is a
reader, not a card writer. Support extracted directory input first; add
read-only `.ps2` input extraction if useful. Produce a validated importable
container, or a new card only through an independently tested writer.
A directory ZIP alone is not a demonstrated PCSX2 card import format.
Never modify the user's live memory card.

## PS2 checksums and difficulty extension

For payload length `N`, use little-endian 32-bit words and unsigned sums:

```text
tail checksum at N-8 = (0x78945612 + sum_u32(bytes[N-1024:N-8])) mod 2^32
main checksum at N-4 = (0x78945612 + sum_u32(bytes[0:N-1024])) mod 2^32
```

Validate both before edits and recompute after all destination edits.
Native scenario validation: `0x13b3d0`, `0x13b420`; system validation:
`0x13bd30`, `0x13bd80`. The repeated sample checksum `0x2389a742` is not
a format signature. PSP decoded saves lack this PS2 checksum pair.

The patched PS2 game puts three little-endian words in its final 1024-byte
settings tail at relative offset `0x3e0`, i.e. **absolute `N-32`**:

| Word | Relative to tail | Absolute | Value |
|---|---:|---:|---|
| Magic | `0x3e0` | `N-32` | `0x4442584d` → bytes `MXBD` |
| Format | `0x3e4` | `N-28` | `1` |
| Mode | `0x3e8` | `N-24` | `0` PS2 Original; `1` PSP Harder |

Scenario marker starts at `0xd3e0`; system marker at `0x21be0`.
This is a save-extension version, unrelated to game build 0.1.14.
Original settings serialization consumes `[0,0xa4)` of the tail. Preserve
all other bytes, including `[N-20,N-8)`, and the payload length. Both native
checksums cover the extension automatically; no outer-file growth occurs.

Serializer epilogue hook: `0x335ad8`; settings loader: `0x335eb0`;
early scenario mode restoration: `0x13b850`, before unit deserialization.
The system loader already reads settings before decoding units.
`tail-0xd608` in the native test is an in-memory object relationship,
**not the tail's disk-file offset**.

Absent, unsupported or invalid markers make the patched game use mode 0.
The converter should report invalid/unknown extensions and refuse to
overwrite unknown future versions, rather than silently downgrade them.
For original PS2 output, never promise harder mode; clear only a recognized
extension as part of a validated profile transformation and recalculate
checksums. This does not make PSP-stage progress compatible with stock PS2.

For patched output, keep scenario and companion system modes consistent
when both belong to the same converted campaign. Do not merge unrelated
system saves or blindly apply one campaign's mode to every slot. Establish
which system/global state is required before allowing scenario-only output.
Do not copy `MXBD` into PSP padding as a cross-platform mechanism.

## Exact current PS2 balance behavior

The original patch compared unit IDs **and original unit names** across
the two databases. The port changes lookup results rather than multiplying
stored HP or rewriting the numeric database on each load.

- 139 shared changed HP records use the exact PSP value, all 1.5× PS2 base HP.
- 294 shared changed nonzero funds rewards use exact PSP values, all 0.8× PS2.
- The added Dragoon row 156 makes the current reward-change count **295**.
  It has HP 3900 in both modes, reward 2500 in mode 0 and 2000 in mode 1.
- Getters are `0x332a10` (HP) and `0x332af0` (reward). Mode 1 and valid IDs
  select the alternate values; invalid modes/IDs retain native fallback.
- Accumulated funds, pilot levels, upgrades, bonuses and favorite-series
  logic are not scaled by the converter merely because balance changes.
  Unit HP/current HP fields still need format mapping. Begin at intermission;
  active-battle HP conversion requires a separately verified policy.

`balance_changes.json` captures the current exact changed numeric records.
`tools/ps2_difficulty.py` and `tools/verify_ps2_difficulty.py` are the source
references. The handoff utility preserves every non-marker/non-checksum byte.
It proves extension arithmetic only, not converted campaign acceptance.

## Campaign profiles and unsupported content

Whitelist tested format/build profiles, not just `SLPS-25345` / `ULJS00041`.
The English PSP translation is expected to share the original PSP save
layout, but must be checked; translation of a menu does not prove that.
The PS2 English port adds PSP content without growing the save payload.
The following are **confirmed PS2 destination coordinates**, not a finished
PSP→PS2 save-field map:

- Prologue: scenario/location IDs **66** and **67**, protagonist chapters
  **0** and **1**, group **4**, scenes `s00r00` and `s00s00`.
  First-chapter location order is `[4,0,2]` by group. Stock saves do not
  already contain the new first-location meaning.
- Added scenario 30, **Zeorymer Sorties at Dawn**: scenario/location ID
  **68**, chapter **7**, group **10**, scene `s0560`.
- PSP reworked scenario 29, **What Gnaws at the "Heart"**: chapter 7,
  group **12**, scene `s0570`. Do not swap these using their filenames.
  Patched chapter-7 global location order is `[29,30,31,32,33,68,34]`;
  group order `[0,2,4,6,8,12,10]`. Preserve branching/unlock prerequisites.
- Added native records: enemy unit **156** based on native Dragoon **69**;
  pilots **431/432** are Aqua variants, **433** is Researcher. Original
  scenario IDs are preserved, but matching numbers alone do not establish
  every save record's meaning across platforms.

Map semantic scene/protagonist/route, clear counts, history, availability
masks and event flags. A blanket stage-number +1/−1 adjustment is wrong.
Favorites also need an explicit tested mapping. Local PS2 build 0.1.18 now
offers three choices in both balance modes. PS2 already stores a favorite
bitset at scenario payload offset `0x1008`, backed by settings object +0x5e8;
the new selector uses it without changing the save format. Native multiple-bit
save-field and bonus checks pass; actual card reload testing is pending.
See `docs/ps2_favorites.md`. The PSP field and cross-platform series-ID mapping
still require evidence. Do not truncate a mapped set merely because older PS2
menus only offered one choice. If a destination truly cannot express a mapped
favorite, ask the user to choose a retained series and disclose the loss;
do not silently select one or emulate bonuses by editing upgrades. This is a
local follow-up to the preserved 0.1.0 handoff bundle, not a rebuilt bundle.

For stock PS2, block saves in PSP-exclusive stages and any other unproven
state. A shared checkpoint is not sufficient unless all campaign flags and
IDs are mapped. Offer the last validated compatible checkpoint only if
such a migration has actually been implemented; do not invent progress or
skip an unfinished battle. Existing stock/older patched PS2 save migration
into the PSP-stage campaign is also unimplemented.

Native campaign structure references, not disk-file offsets:
`0x347198` / `0x3470a0` serialize/load 16 bytes at object+12;
`0x3471c8` / `0x3470d0` serialize/load 896 bytes at object+28;
`0x347250` / `0x347150` serialize/load 256 bytes at object+`0x3b0`.
Find their enclosing save-file offsets from callers before patching files.
Object+`0x3a8` holds chapter; location history pairs are under object+`0x3b0`.
These relationships have native round-trip checks, not platform conversion.

## PSP encryption and metadata

The sampled `DATA.BIN` files have a 16-byte encryption header and decoded
payload sizes matching the PS2 types. The comparison successfully decoded
mode **3** and verified the keyed file MAC against `PARAM.SFO` for both
samples. A full output encryptor/SFO integrity writer is **not implemented**.

Original game key location: PSP `BOOT.BIN` file offset `0x276bc0`, 16 bytes;
copy routine VA `0x23a900`. Key bytes and game binaries are not in the bundle.
Local investigation: `work/source/save_compare/psp_crypto_analysis.py` and
`work/build/save_compare_reference/`. That decoder is private, depends on
PyCryptodome and downloaded KIRK reference data, and is not a distributable
standalone engine. It must not be copied into Retro Trans without checking
its dependencies and the referenced implementation's license requirements.

Use PPSSPP's savedata/Chnnlsv implementation as primary format reference.
Encrypted output must regenerate the per-file and SFO integrity metadata,
including `SAVEDATA_PARAMS` / file-list information as required by the
selected mode. Reusing an encrypted template's stale MAC is not valid.
PPSSPP also has a plaintext savedata path; emulator-only output is a possible
first milestone, but its `PARAM.SFO` must describe plaintext correctly and
MX load/save must be demonstrated. Merely dropping an encrypted header does
not make an importable save. Plaintext emulator support must be labeled
separately from tested encrypted PSP-console support.

## Proposed implementation milestones

1. **Inspector:** identify validated profiles/containers, validate PS2 checksums
   and PSP integrity, list slots and unsupported states, with no writes.
2. **Matched fixtures:** capture both protagonists at the same shared
   intermission on each platform. Vary one field at a time: funds, level/EXP,
   PP, kills, upgrades, parts, skills, favorites, route/clear/history flags.
   Record visible values and source hashes. Include original PS2 and current
   PSP-stage PS2 port separately. Map arrays, field widths, record IDs,
   string encodings and unknown bytes against native load/save routines.
3. **Scenario codec:** semantic source→destination model, explicit profile
   and ID/flag maps, destination serialization and fresh metadata. Preserve
   understood unknown bytes where safe; block incompatible unknown state.
4. **Packaging:** PSP folder and validated PS2 import format; backups,
   cancellation cleanup, changed-source rejection and verified ZIPs. Reuse
   Retro Trans conventions and add standalone-executable dependencies/notices.
5. **Acceptance:** actual load, inspect key values, play the next battle,
   then save/reload on each destination. Test both routes/protagonists,
   extra-stage boundaries, favorite-series differences and both PS2 balances.
6. **System/battle scope:** separately map/validate before advertising it.
   Do not carry dynamic battle state merely because the larger file fits.

Suggested files: `retro_trans/mx_saves.py`, `tests/test_mx_saves.py`, and
`retro_trans/resources/MX-SAVE-CONVERSION.txt`. An optional later CLI could
use `--direction psp-to-ps2|ps2-to-psp|both`, explicit destination profiles,
`--ps2-balance keep|original|psp`, and opt-in `--write`. These are proposed
interfaces, not existing commands. Check-only must remain the default.

## Acceptance criteria and tests

- Corrupt/truncated/wrong-game saves, unknown format versions, unsupported
  markers, duplicate slots and unsupported campaign states are rejected.
- Tests exercise real checksum regions and corrupted main/tail data;
  mode 0/1 persists at N-32, preserves length and all unrelated bytes, and
  unknown extension versions are not silently overwritten.
- Both-direction tests preserve mapped progression semantically. Byte-exact
  round trips are only claimed when demonstrated; otherwise list intentional
  representation changes and every discarded field in the report.
- Difficulty choice/defaults, target capability checks and check invalidation
  are tested in GUI and CLI. Companion-save consistency is validated.
- Destination templates, slot metadata, crypto/MACs, ZIP contents and import
  format are verified. Cancellation and changed-source checks leave originals
  intact; output must be new, outside input roots, and never a live install.
- Native PS2 markers are checked before unit decoding; gameplay examples
  compare base HP/rewards without applying changes twice on save/reload.
- Actual PCSX2/PPSSPP acceptance evidence precedes a supported-converter
  claim. Physical hardware support is separately validated. A handoff or
  successful synthetic test does not authorize a release.

## Reference bundle and sources

`facts.json` is machine-readable evidence with explicit unknowns and profile
identities. `balance_changes.json` describes current numeric lookup changes.
`reference/mx_save_reference.py` and its tests cover known PS2 tail behavior;
`reference/ps2_memcard_read.py` is extraction-only. Run:

```text
python -m unittest discover -s tests -v
```

Historical supporting assessments are under `context/`; this document's
current campaign scope supersedes their earlier build limitations.
No ROMs, real save files, icons or crypto implementation are bundled.
Private fixtures remain in the source project and require fresh matched pairs.

Primary references:

- https://github.com/retro-trans/retro-trans-tools
- https://github.com/retro-trans/retro-trans-tools/blob/main/retro_trans/z3_saves.py
- https://github.com/hrydgard/ppsspp/blob/master/Core/Dialog/SavedataParam.cpp
- https://github.com/hrydgard/ppsspp/blob/master/Core/HLE/sceChnnlsv.cpp
- https://github.com/ps2dev/mymc/blob/master/ps2mc.py
- https://github.com/ps2dev/mymc/blob/master/ps2mc_dir.py

This handoff requests the converter work only. It does not publish a game
patch or release, install any converted save, or dispatch a different chat.
