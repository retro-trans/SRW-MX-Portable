# Super Robot Taisen MX / MX Portable — translation project

English translations and an open toolchain for **Super Robot Taisen MX**
(PS2, **SLPS-25345**) and **MX Portable** (PSP, **ULJS-00041**).

## Contribute

All story dialogue and chapter titles are translated, but we have not tested
every route or completed human proofreading. Bug reports, proofreading and
playtesting are welcome. Join the Retro Trans community:

**[discord.gg/nZBZfTDfCP](https://discord.gg/nZBZfTDfCP)**

You can also [report an issue](https://github.com/retro-trans/SRW-MX-Portable/issues).
Include the build version, route, stage and an in-game screenshot.

## Play it

The latest release is **[v0.9.5](https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.9.5)**
for PSP and PS2. It fixes the PS2 player-turn freeze when opening the battle
forecast. The PSP build carries the matching title screen version and the
v0.9.0 game content. [Release notes](docs/releases/v0.9.5.md)

### Apply

With Retro Trans Tools, refresh the catalog and choose **Automatic** with your
Japanese or published English ISO. To use a bare patch directly, choose
**Apply xdelta** and select the file that matches your input.
[Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools)

| Your source | Download |
|---|---|
| Japanese PSP, ULJS-00041 | [Full PSP patch](https://github.com/retro-trans/SRW-MX-Portable/releases/download/v0.9.5/SRWMX-English-v0.9.5.xdelta) |
| Published English PSP v0.9.0 | [PSP upgrade](https://github.com/retro-trans/SRW-MX-Portable/releases/download/v0.9.5/SRWMX-English-v0.9.0-to-v0.9.5.xdelta) |
| Japanese PS2, SLPS-25345 | [Full PS2 patch](https://github.com/retro-trans/SRW-MX-Portable/releases/download/v0.9.5/SRWMX-PS2-English-v0.9.5.xdelta) |
| Published English PS2 v0.9.0 | [PS2 upgrade](https://github.com/retro-trans/SRW-MX-Portable/releases/download/v0.9.5/SRWMX-PS2-English-v0.9.0-to-v0.9.5.xdelta) |

Keep checksum verification enabled. Older public releases can use the
catalog upgrade routes. The patches also work with xdelta3.

Use an **in-game save** and restart when changing builds. Emulator save states
retain old code and resources. PS2 and PSP patches are separate platform builds.

## Check the translation

Read the Japanese beside the selected English using your own original ISO:

```sh
python tools/restore_dialogue_sources.py "Super Robot Taisen MX Portable (Japan).iso" --output-root work/build/review
```

This writes local bilingual JSON files under `work/build/review`, matching each
English row to its original scene/string locations. The repository stores those
locations and the English, while the original Japanese is read from your ISO.
Existing local files are protected from replacement.

Changing a line is described in **[TRANSLATING.md](TRANSLATING.md)**.

## Translate it

Fork the project to improve the English or translate another language. Start
with **[TRANSLATING.md](TRANSLATING.md)** and **[BASE_RULES.md](BASE_RULES.md)**.

```sh
python tools/extract_iso.py "Super Robot Taisen MX Portable (Japan).iso"
python tools/restore_dialogue_sources.py "Super Robot Taisen MX Portable (Japan).iso"
# Edit the local bilingual working files, then create public English copies:
python tools/strip_jp.py
```

Preserve row IDs, source locations, runtime placeholders and original blank
segments. Check the glossary and measure dialogue with the actual font before
building. Commit the selected final `*.en.json` files; keep original Japanese
script and game binaries local.

## What is here

| Path | Contents |
|---|---|
| `TRANSLATING.md` | Start here: editing, source restoration, building and verification |
| `BASE_RULES.md` | Translation rules |
| `tools/` | Extraction, insertion, font, text-fit, patch and verification tools |
| `work/translation/en/script/*.en.json` | English story dialogue with original scene/string locations |
| `work/translation/en/battle/*.en.json` | English battle captions |
| `work/translation/en/ui/`, `static2/` | Interface and database translations |
| `work/glossary/` | Terminology, references and decisions |
| `work/ui/` | In-game screenshots and layout metadata |
| `docs/CHANGELOG.md` | Every build and its changes |
| `docs/`, `docs/releases/` | Technical findings, handoff and release details |
| `incoming/fonts/` | Licensed source font and notices |
| `work/output/` | Local test images and release assets, ignored by Git |

## Using these tools

Tools use your own Japanese ISO and locally extracted working files. Required
Python packages and the full build sequence are in [TRANSLATING.md](TRANSLATING.md).
For a built ISO:

```sh
python tools/verify_campaign_build.py "Super Robot Taisen MX Portable (Japan).iso" 0.4.9
python tools/battle_quotes.py verify work/output/SRWMX_EN_0.4.9.iso
python tools/verify_text_build.py 0.4.9
```

The campaign verifier requires the input manifest produced by the campaign
builder. Readback checks verify stored text and preserved game structures;
runtime probes and playtesting are separate checks.

## Do not sell this

This fan patch is free. Do not sell it, pre-patched game images or access to its
downloads. No complete game images or original Japanese dialogue dumps are
distributed here. The original game and its assets belong to their rights
holders; apply the patch to a copy you own.

## Credits

The font is [Genei LateGo by o_tamon](https://okoneya.jp/font/genei-latin.html),
from the Genei Latin v2.1 package. Its acknowledgements and SIL Open Font License
accompany the patch. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

| Role | Contributor |
|---|---|
| Project lead | pow |
| Playtester | Melfice |
| Translation, tooling and reverse engineering assistance | OpenAI Codex models, directed by pow |
| Terminology reference | [Akurasu's MX wiki](https://akurasu.net/wiki/Super_Robot_Wars/MX) |
| Patch packaging and verification | [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools) |
| README and release layout | [SRW-Z](https://github.com/retro-trans/SRW-Z) |

The complete campaign pass used Sol 6.1 at Medium effort, with six translators
sharing each stage/group, followed by context, terminology and text-fit review.
The translation is machine-produced and then edited; model review does not
replace human proofreading.

## Status

v0.4.9 includes the prologue, all **54 numbered stages**, the **final and hidden
stages**, every mapped route, ending, unused scenes and closing/save messages.
All **67 chapter titles** are covered across **205 native copies**: 160 translated
copies and 45 existing English copies preserved. Some bitmap interface labels,
including the sortie-preparation header, still remain Japanese.

### Human proofreading

Complete human proofreading has not been performed. We have not established a
verified count of lines read by a human, so the script coverage figures below
are translation and insertion checks, not human proofreading totals.

### Verification and playtesting

- All 51,366 original readable script uses and 98,686 unchanged commands pass
  final ISO readback. Battle captions: 51,892 entries, no mismatches.
- Targeted PPSSPP checks cover boot, copied-save loading, selected dialogue,
  chapter-card rendering, native font hooks and the English intermission header.
- All five enlarged map scripts pass native allocation and complete ISO-read
  probes. Ending and closing blocks also pass loading checks; exact ending text
  passes a renderer probe, which does not constitute playing the ending scene.
- A full campaign playthrough and physical PSP testing remain pending. Please
  report crashes, clipped text and **Malloc Memory Over** errors.

[The changelog](docs/CHANGELOG.md) records each build's changes and testing limits.
