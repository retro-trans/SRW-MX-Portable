# PS2 / PSP reuse assessment

Inspected the user's PS2 ISO read-only on 2026-10-05 and compared its original
text with the current PSP translation sources. This is a porting assessment,
not a completed PS2 patch or an in-game PS2 validation.

## Disc and method

- PS2 executable: `SLPS_253.45` (disc edition SLPS-25345).
- ISO: 3,777,167,360 bytes, 37 files. The full streamed SHA-256 and file inventory
  are recorded in `work/output/ps2_mx_reuse_assessment.json` and
  `work/output/ps2_mx_iso_inventory.json`.
- Bounded reads of ISO files; the original ISO was not modified.
- Validated all 192 SRWL script blocks against the executable's sector table
  at file offset `0x381F40`. Script base in MAP.BIN is `0x622A000`.
- Decoded the 192 scene names from the executable's pointer table at file
  offset `0x37B5F8`; all are also present in the PSP scene inventory.
- Compared readable string-table slots, not repeated message commands.
  Also counted every non-ASCII script string slot, including strings outside
  the directly referenced message/condition/defeat-line set.
- Compared database descriptions after joining their indexed sentence rows
  and removing whitespace and line-break controls. This establishes source
  text reuse, not equivalent PS2 formatting or gameplay behavior.
- Japanese scripts and extracted binaries remain in ignored `work/source/ps2/`.

## Measured reuse

| Area | Existing English applicable to matching PS2 source | Remaining work |
| --- | --- | --- |
| All non-ASCII script text slots | 49,257 / 49,659 (99.19%) have exact source matches with English | 402 slots containing 338 distinct source strings differ; review and translate them |
| Story, conditions and defeat-line slots | 48,337 / 48,739 (99.18%) have exact source matches | 402 slots containing 338 distinct source strings differ; review and translate them |
| Story matches within the same named scene | 47,732 / 48,739 (97.93%); no competing English variants for those same-scene matches | Another 605 exact-source slots match elsewhere and need contextual review |
| Battle captions | 51,434 / 51,434 entries (100%); all 10,227 distinct strings already have English | Adapt insertion, pilot lookup and wrapping, then verify in game |
| Database names and other Strg terms | 1,829 / 1,837 (99.56%) match PSP source terms | Review eight changed terms; remap indices rather than copying arrays |
| Unit library descriptions | 237 / 248 (95.56%) have matching source and existing English | Review 11 differing entries |
| Pilot library descriptions | 249 / 264 (94.32%) have matching source and existing English | Review 15 differing entries |
| Spirit descriptions | 29 / 32 have existing English; 31 / 32 match PSP source | Review one source difference and two entries without English in the current description map |
| Skill descriptions | 43 / 49 non-dummy entries have existing English; 44 / 49 match PSP source | Review five source differences and one entry without English in the current description map |
| Ability descriptions | 52 / 53 non-dummy entries | Review one difference |
| Part descriptions | 36 / 37 non-dummy entries | Review one difference |
| Help descriptions | 505 / 507 non-dummy entries | Review two differences |
| Scenario title wording | 65 / 66 distinct records (98.48%) exactly match PSP title sources | Adapt one title; locate and redraw PS2 title-card graphics |

Across the seven description tables, 1,154 / 1,190 non-dummy entries (96.97%)
match after joining the different line wraps; 1,151 have existing English in
the current translation maps. The separate raw Sent row match
is only 2,365 / 5,598; that lower number largely reflects different wrapping.
The Strg table has only 1,138 equal values at the same index, despite 1,829
matching values overall. Source matching and index remapping are essential.

The one differing title is scenario record 34: PS2 uses
`冥王、暁に出撃す`, whereas PSP uses `ゼオライマー、暁に出撃す`.
The existing English title, **Zeorymer Sorties at Dawn**, is a useful starting
point, but this wording needs a deliberate PS2 decision. PSP's scenario title
**What Gnaws at the "Heart"** is absent from the PS2 title table; this is the
renamed/reworked counterpart of PS2 scenario 29, not a hidden extra stage.
The PSP additions are the playable scenario 0 **Prologue** and scenario 30
**Zeorymer Sorties at Dawn**. PSP scenario 30 has a similar title to PS2
scenario 29 but is newly added content. This distinction was checked on
2026-10-05 against the [PSP scenario list](https://srw.wiki.cre.jp/wiki/全話一覧/MX_PORTABLE)
and [PS2 scenario list](https://srw.wiki.cre.jp/wiki/全話一覧/MX).
PS2 has 66 scenario records; PSP has 69 records and 67 distinct title wordings.
These counts describe data records, not stages on a single playthrough.

## What ports and what needs new work

The SRWL format retains its 48-byte commands, CP932 text and relative string
pointers. Of the 192 PS2 blocks, 98 have entire text tables identical to PSP
blocks and 65 have command arrays identical to PSP blocks. The remaining
blocks demonstrate why wholesale replacement by PSP script binaries is unsafe.
Scene extraction, translation lookup, command-preservation checks and string
repacking logic can be adapted.

FIX00.DAT has the same tagged database family as PSP STATIC2_ADD.BIN: Unit,
Weap, Pilt, Sprt, Strg, Sent and the library/description index tables. Existing
database parsing and glossary logic are therefore useful. Battle caption
blocks also parse with the existing block parser; PS2 has 370 pilot blocks,
with its 512-entry pilot table in STATIC.BIN at `0x1B8174`, compared with
372 pilot blocks on PSP. The caption subfile is archive entry 5.

The reusable font source is the licensed Genei Latin TTF, together with its
glyph-rasterization and width-measurement concepts. PSP renderer addresses,
hooks, atlas layouts, heap measurements and 4x implementation are platform
specific and must be investigated for PS2. The ISO boot paths and relocation
work also differ: PS2 loads SLPS_253.45 rather than PSP BOOT/EBOOT.BIN.

WND.BIN contains 112 P2IG markers and no TX48 markers; PSP graphic editing
works with TX48. English UI wording and artwork design are reusable, but the
current encoded PSP graphics and their insertion offsets are not drop-in PS2
assets. PS2 chapter-artwork coverage and native font rendering have not yet
been inspected in an emulator. Differences in hardware and file sizes do not
by themselves prove that PS2 assets are higher-resolution replacement assets.

## Repository recommendation

### Difficulty is a separate porting decision

Follow-up comparison on 2026-10-05 found 139 same-name Unit records whose base
HP differs; every one has exactly 1.5 times the HP on PSP. The other changed HP
record is a formerly empty PS2 slot populated with a Dragoon in PSP. The PSP
port also has documented 20% lower money rewards and three favorite-series
selections instead of the PS2 version's one. See the
[MX Portable overview](https://srw.wiki.cre.jp/wiki/スーパーロボット大戦MX_PORTABLE).
Raw record comparisons and unchanged English-build HP/reward fields are
recorded in `work/output/ps2_psp_unit_hp_comparison.json`.

The English PSP 0.4.9 ISO preserves all 512 original PSP Unit HP fields and
all 512 reward fields. A future PS2 port of PSP-only story content can choose
to preserve PS2 balance; importing new scenarios does not inherently require
copying PSP's increased existing-unit HP or lower rewards. New-scenario enemy
stats and relevant events still need explicit review and gameplay validation.

### Shared repository, separate builds

Use one source repository for both versions. The measured text overlap makes
shared English translations, glossary decisions and review history valuable.
Keep platform-specific source extraction, font/rendering, graphics, insertion,
disc building and emulator validation separate. Preserve the current working
PSP paths initially; introduce PS2 subdirectories without a broad migration.
The repository can later be presented as **SRW MX / MX Portable**.

Suggested additions respecting AGENTS.md's top-level layout:

```text
tools/ps2/
docs/ps2/
work/source/ps2/                 # ignored original data
work/translation/en/ps2/         # PS2 differences and use mappings
work/output/ps2/                 # ignored local builds
```

Keep PSP and PS2 as separate release/game identities and separate patches.
Preserve the published PSP `game_id` (`srw-mx-portable`) and ULJS-00041 edition;
use a distinct identity such as `srw-mx-ps2` with SLPS-25345 for PS2. Retro Trans
Tools ingests all public releases of a repository, so both identities can live
in one repository. Each release must have its own single BUILD-MANIFEST.json,
one platform label and a unique numeric version tag. Do not publish two
manifests in one release or introduce platform prefixes in version tags under
the current contract. Coordinate tag versions across the shared repository.

Reference: [Retro Trans Tools release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md).
The local catalog builder's `client.releases(repo)` loop and game/edition
identity keys were also inspected for this recommendation.

No PS2 translation build, repository rename, GitHub push or release was made
as part of this assessment. Starting a PS2 port is a separate next task.
