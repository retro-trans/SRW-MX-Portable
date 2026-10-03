# Translating MX Portable

Use your own Japanese ULJS-00041 ISO. Python tools expect `pycdlib`, `Pillow`, `keystone-engine` and, for selected debugging tools, `capstone`, `fonttools` or `websockets`. The native font source is included under `incoming/fonts/` with its SIL OFL notices.

Read `AGENTS.md`, `BASE_RULES.md`, `docs/HANDOFF.md` and `docs/CHANGELOG.md` first. The handoff contains historical notes; the latest continuation and changelog determine the current build. Keep game binaries, extracted Japanese dialogue and bilingual working files local.

## Restore local source text

```sh
python tools/extract_iso.py "Super Robot Taisen MX Portable (Japan).iso"
python tools/restore_dialogue_sources.py "Super Robot Taisen MX Portable (Japan).iso"
```

The second command reads the original scene-name and string-pointer tables, restores each reviewed English row's Japanese from its `uses` locations, and writes ignored bilingual `*_merged.json` files plus `work/source/stage_map.json`. It rejects conflicting locations and existing bilingual files unless explicitly passed `--overwrite`. It does not modify the ISO.

Battle captions can be extracted locally with `python tools/battle_quotes.py export`; the published final `batch_NN.en.json` files hold the English translations. Other extraction and fitting procedures are documented in `docs/battle_quotes.md`, `docs/static2_format.md` and `docs/text_insertion.md`.

## Edit and check

Edit local bilingual working rows, preserving their `uses`, row IDs and control codes. Check terminology against the glossary and measure text with `tools/textfit.py` and the relevant checks in `tools/`. Keep ambiguity or deliberate terminology exceptions in the decision records. Before committing:

```sh
python tools/strip_jp.py
```

Commit only selected final `*.en.json` dialogue files. Never commit original Japanese dialogue or source game binaries. UI terms and names in Japanese are allowed.

## Build and release

`tools/build_patch.py` builds the campaign/font/UI/battle base from the original ISO. Pass the prologue and each reviewed `stageNN_campaign_full_merged.json` explicitly with repeated `--scenes-file` options and use `--native-font4x --text --battle`. Its default glob can include experimental files; explicit inputs are required for a release. `tools/patch_screenshot_text.py` applies the 0.4.1 chapter-card and closing-line changes to the 0.4.0 base.

Exact reproduction of old test ISOs from a fresh checkout is not yet established. A source rebuild must be verified as a new candidate, including all dialogue and battle checks and gameplay testing, before publication. The published xdelta reproduces the exact released ISO, with complete hash and round-trip evidence.

Every release must use the [Retro Trans game release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md). `tools/build_release.py` prepares the local configuration and invokes the standard builder. Supply a committed source revision, your original ISO and verified output ISO. It emits only the patch, manifest, checksums and validation report, after applying the patch locally and checking the complete output. See `docs/releases/v0.4.1.md` for this release's scope and validation.
