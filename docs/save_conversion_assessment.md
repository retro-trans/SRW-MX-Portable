# PS2 / PSP save comparison

Read-only assessment, 2026-10-05. A converter looks worth investigating, but
conversion in either direction has not been demonstrated. Matching file sizes
are evidence of related save formats, not proof that their fields are compatible.

## Samples and measured sizes

The active PCSX2 configuration selects `ace3 end.ps2` in its memory-card folder.
Only the two MX directories were extracted from that card. The originals were
opened for reading only, and the card's SHA-256 remained unchanged after analysis.
PSP samples came from `work/build/campaign043_test/memstick/PSP/SAVEDATA/`.

| Save type | PS2 directory | PS2 payload | PSP directory | PSP stored file | PSP decoded payload |
| --- | --- | ---: | --- | ---: | ---: |
| Scenario, slot 1 | BISLPS-25345S00 | 54,272 bytes | ULJS000410000 | 54,288 bytes | 54,272 bytes |
| System | BISLPS-25345 | 138,240 bytes | ULJS000419999 | 138,256 bytes | 138,240 bytes |

The type names are confirmed by PS2 icon titles and PSP PARAM.SFO metadata.
Do not describe the larger file solely as a battle suspend save: both games
label it system data, and its complete contents have not yet been mapped.

Both PSP metadata entries identify Hugo at level 7, one clear, two turns,
zero funds and Scene 0 / Prologue. These are older local test saves, not a
controlled pair taken at the same checkpoint as the new PS2 saves. Equivalent
PS2 progress values have not been independently decoded from the payload.

## Integrity and encoding

PSP DATA.BIN uses the platform's savedata encryption and a 16-byte header.
Offline decoding used mode 3 and the fixed game key located in original
BOOT.BIN at file offset `0x276bc0`; the copy routine is at virtual address
`0x23a900`. Both encrypted files passed the keyed file-MAC comparison against
their PARAM.SFO entries. The algorithm was checked against PPSSPP's
[savedata implementation](https://github.com/hrydgard/ppsspp/blob/master/Core/Dialog/SavedataParam.cpp)
and [sceChnnlsv implementation](https://github.com/hrydgard/ppsspp/blob/master/Core/HLE/sceChnnlsv.cpp).
Private decoding work and decoded saves remain under ignored working folders.

Each PS2 payload ends with two little-endian 32-bit checksums. With payload
length N and base `0x78945612`, the word at N-8 checks bytes N-1024 through N-9;
the word at N-4 checks bytes 0 through N-1025. Each checksum is the unsigned
sum of that region's 32-bit words plus the base, modulo 2^32. Both checksums
passed for both extracted files. The PS2 executable's loading routines compare
these sums at virtual addresses `0x13b3d0` / `0x13b420` for scenario data and
`0x13bd30` / `0x13bd80` for system data.

The repeated penultimate value `0x2389a742` is a checksum of an identical tail
region in these samples, not a demonstrated fixed format signature. Neither
PSP decoded sample has the corresponding PS2 checksum pair.

The memory-card reader follows the public-domain
[mymc directory and allocation formats](https://github.com/ps2dev/mymc).
File chains and declared lengths were checked; memory-card page ECC was not.
Passing the game-level checksums supports the extracted MX payloads' integrity.

## What this establishes

The two platforms reserve exactly the same sizes for both save types after
removing the PSP encryption header. The contents differ, including headers and
the final region. Scenario samples share 47,769 bytes and differ at 6,503;
system samples share 115,483 and differ at 22,757. Most bytes are zero padding,
so these counts must not be presented as percentages of conversion readiness.
Different progression also prevents assigning every difference to the port.

A simple filename change will not bridge the platform containers. Even a
decoded payload must be checked for field meaning, record layout and IDs
before being used in the other game. PSP-only scenarios found in the separate
ISO comparison also require a defined fallback when converting to PS2.

## Remaining work for a converter

Start with scenario saves from the same shared intermission/checkpoint, with
matching protagonist, route and visible progress. Map progress, money, pilot,
unit, upgrade, inventory and unlock fields against both games' loading code.
Then construct destination metadata and integrity data and test on copied cards
and copied PSP save directories. Validate load, continued play and save/reload
in both directions before claiming support. Treat system/battle-state transfer
as a separate validation scope.

The machine-readable result, hashes and integrity checks are in
`work/output/ps2_psp_save_comparison.json`. Extracted and decoded originals stay
in ignored `work/source/save_compare/`. No save was converted or installed;
no game build, GitHub push or release was made for this comparison.
