# Super Robot Taisen MX Portable — translation project

An open toolchain for translating **Super Robot Taisen MX Portable** (PSP,
Japanese edition **ULJS-00041**), plus the English translation built with it.

## Contribute

All story dialogue and chapter titles are translated, but we have not tested
every route or completed human proofreading. Bug reports, proofreading and
playtesting are welcome. Join the Retro Trans community:

**[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**

You can also [report an issue](https://github.com/retro-trans/SRW-MX-Portable/issues).
Include the build version, route, stage and an in-game screenshot.

## Play it

The latest release is **[v0.4.9](https://github.com/retro-trans/SRW-MX-Portable/releases/tag/v0.4.9)**,
for the original Japanese PSP edition **ULJS-00041**. You need your own matching
Japanese ISO, or the exact published English v0.4.1 image for an upgrade.

This release includes all story dialogue through the ending, every mapped route
branch, the hidden stage, closing/save messages and all 67 chapter titles.
It also includes battle captions, interface translations and the cumulative
menu, font and dialogue fixes. The build remains experimental; see the release
notes for changes and remaining playtesting checks.

### Apply

**The easiest way:** [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools)
provides a desktop interface for applying translation patches. Download the app
from its Releases page, refresh its catalog, choose **Automatic**, select your
source ISO, wait for analysis and click **Patch**. v0.4.9 is registered in the
verified catalog. You can also choose **Apply xdelta** with the downloaded patch.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher)
accepts the same `.xdelta` files. Select the matching source ISO and patch.

**Command line:** Get [xdelta3](https://github.com/jmacd/xdelta) and use the patch
that matches your source image:

| Your source image | Patch |
|---|---|
| Original Japanese PSP release, ULJS-00041 | [SRWMX-English-v0.4.9.xdelta](https://github.com/retro-trans/SRW-MX-Portable/releases/download/v0.4.9/SRWMX-English-v0.4.9.xdelta) |
| Published English v0.4.1, ULJS-00041 | [SRWMX-English-v0.4.1-to-v0.4.9.xdelta](https://github.com/retro-trans/SRW-MX-Portable/releases/download/v0.4.9/SRWMX-English-v0.4.1-to-v0.4.9.xdelta) |

**Original Japanese edition:**

```sh
xdelta3 -d -s "Super Robot Taisen MX Portable (Japan).iso" SRWMX-English-v0.4.9.xdelta "SRWMX English v0.4.9.iso"
```

**Already on the published v0.4.1?** Use the upgrade patch:

```sh
xdelta3 -d -s "SRWMX English v0.4.1.iso" SRWMX-English-v0.4.1-to-v0.4.9.xdelta "SRWMX English v0.4.9.iso"
```

The upgrade requires the exact published v0.4.1 output; local test builds with
the same version label may differ. Both patches produce the identical v0.4.9
image. If the patcher reports a checksum mismatch, compare your source with
`README-v0.4.9.txt` or `BUILD-MANIFEST.json` from the release. Keep source
verification enabled. Other English versions are not supported upgrade sources.

Use an **in-game save** and restart when changing builds. Emulator save states
retain the old executable and resources.

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
| Project lead | Binh |
| Translation, tooling and reverse engineering assistance | OpenAI Codex models, directed by Binh |
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
