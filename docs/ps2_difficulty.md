# PS2 optional PSP balance — local build 0.1.5

New Game opens a native two-option dialogue:

- **PS2 - Original:** original PS2 HP and money rewards.
- **PSP - Harder:** the PSP database's shared-unit HP and money rewards.

The prompt explains `enemy HP +50%, funds -20%`. PS2 is selected initially;
the normal Cancel button returns to the title menu without changing the mode.
Confirmation starts the usual PS2 New Game flow. After the box closes, its
original Yes/No labels and window class return, because other title-screen
prompts reuse the same object.

This is a balance option for the PS2 campaign, not a port of PSP-exclusive
scenarios. The PS2 favorite-series screen still selects one series. Other PSP
changes, difficulty/event adjustments outside the compared database fields,
and three favorite-series selections are outside this first implementation.

## Exact balance data

`tools/ps2_difficulty.py` compares original PS2 FIX00 and original PSP
STATIC2_ADD by unit ID **and original name**, then stores English-free numeric
tables in the added native executable segment. All 139 shared changed HP
records are exactly 1.5 times the PS2 values. All 294 shared nonzero changed
reward records are exactly 0.8 times their PS2 values.

The PSP Dragoon in slot 156 replaces an empty PS2 slot and is excluded.
All other HP values, including allied units, retain their original PS2 values.
No records are copied from the PSP layout wholesale. No live FIX00 fields are
rewritten or multiplied, which avoids compounding HP on reload.

Native Unit getters at `0x332a10` (HP) and `0x332af0` (funds) select exact
PSP table values only for mode 1 and IDs 0–511. Mode 0 and invalid modes use
the original PS2 lookup. The original database files and numeric records
remain unchanged. Upgrade, favorite-series and reward-bonus calculations run
through the original PS2 routines after these base values are retrieved.

## Menu and persistence

The existing New Game confirmation state machine is at `0x2bce60`.
Feature hooks set up the prompt/choices at `0x2bd120`, accept the selected
mode at `0x2bd1bc`, and restore the shared confirmation box at `0x2bd2ac`.
The wider opening animation belongs to a copied vtable on this object only.
Both choices confirm; Cancel uses the original cancellation/fade path.
The complete vtable is 0xd8 bytes. Its cursor geometry methods at +0xb8,
+0xc0, +0xc8 and +0xd0 are required by the opening routine. The animation
step count uses numeric register `$8`, matching the native PS2 convention;
Keystone's MIPS64 `$t0` name would encode register 12 instead. These two
errors caused 0.1.4 to show the explanation without any selectable choices.

The common save settings tail has 1024 bytes. The original serializer
`0x3359c0` and loader `0x335eb0` consume only the first `0xa4` bytes: flags,
two 64-byte tables and two 16-byte tables. Three words at tail offset `0x3e0`
hold `MXBD`, format version 1, and mode 0 or 1. Both existing native checksums
remain in their original positions and include this extension automatically.
Payload sizes remain 54,272 / 138,240 bytes.

The serializer epilogue at `0x335ad8` stamps the extension for scenario and
system/battle saves. The settings loader restores it. An extra validated-load
hook at `0x13b850` restores scenario mode **before** unit deserialization.
The system/battle load flow already restores settings before its unit loader.
Absent, unsupported or invalid markers select PS2 balance, so old saves
cannot inherit a previously selected harder mode.

## Validation and use

`tools/verify_ps2_difficulty.py` executes the patched native code with Unicorn:

- 3,072 record checks: all 512 HP/reward records in PS2, PSP and invalid modes,
  compared against the original native getters or the original PSP database.
- Out-of-range fallback, both confirmations and both cancellation cases.
- Menu pointers, default selection, copied vtable and Yes/No cleanup.
- Actual five-frame window opening, render dispatch for both choice labels,
  up/down selection and wrapping. Reintroducing either opening bug fails.
- Both modes written/read using real extracted scenario and system save tails;
  the original native tail-checksum loop agrees with the resulting checksum.
- Old-save/invalid-marker defaults and restoration before unit decoding.

Execution tests are separate from in-game acceptance. Visual layout,
starting both modes, gameplay HP/reward examples, and saving/reloading each
mode in PCSX2 remain required before calling the feature fully validated.
Original user memory cards are never changed by these tests; the emulator
profile uses a separate copy. Physical PS2 testing remains pending.

The complete English campaign builder integrates the feature:

```powershell
python tools/build_ps2_campaign.py 'Super Robot Taisen MX (Japan).iso'
```

It refuses to overwrite an existing output. Final test disc:
`work/output/SRWMX_PS2_EN_0.1.5.iso`. All translations and native 4x VWF from
0.1.3 remain. No GitHub push or release is part of this build.
