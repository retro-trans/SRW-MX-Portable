# Translator brief — script dialogue (SRW MX Portable → English)

Read `BASE_RULES.md` first; its rules are binding.

## Input
`work/translation/en/script/<scene>.json` → `rows`: `id`, `jp` (raw line), `kind`
(`dialogue` = Speaker「body」, `thought` = Speaker（body）, `plain` = anything else), `speaker_jp`,
`speaker_en` (pre-filled from the glossary; may be empty), `body_jp` (the text to translate; `@` = line
break in the Japanese box, `　` = indent), `uses` (scene:index where the line appears).
Rows are in play order. You may read rows outside your slice for context, and must read the rows on
either side before deciding who a line is aimed at.

## Output (one JSON file per slice, path given in your task)
`{"slice": N, "rows": [{"id": ..., "speaker_en": "...", "en": "...", "notes": "", "uncertain": ["..."]}]}`
- `en` = the body only. Do NOT add the speaker name, 「」 or （） — the build adds them.
- dialogue/thought rows: write one continuous text, no `@` — the build wraps it.
- plain rows: keep the same number of `@`-separated lines as the Japanese.
- Fill `speaker_en` when empty (glossary first; unknown/hidden speakers stay `???`).

## Hard limits (the box is 352 px per line, 3 lines per message, VWF font)
Check EVERY row with: `python tools/textfit.py "<speaker_en>" "<en>"` — it must print FITS.
Write the line in full first; only if it does not fit, compress (abbreviate, tighten wording) — never drop
the end of the sentence. If it still cannot fit, keep your best version and flag it in `uncertain`.

## Characters
ASCII only: letters, digits, space and `, . : ; ? ! / ~ ' " ( ) [ ] + - = $ % & *`.
Use `...` for ellipses, no em/en dashes, no accented letters, no curly quotes.
Keep these placeholders verbatim, they expand at runtime: `#男愛称` / `#女愛称` (male / female lead's
nickname), `#男姓名` / `#女姓名` (male / female lead's full name), `#部隊名` (squad name), `#機体名` (unit name).

## Names
Use `work/glossary/glossary.json` (characters: `jp_full`/`jp_short` → `en_full`/`en_short`; units; terms).
Names in `work/glossary/do_not_touch.json` must be spelled exactly as listed. If a name is missing from the
glossary, check akurasu.net first (project rule), then other wikis, and list it in `uncertain`.

## Style
Natural spoken English that fits each character (BASE_RULES on pro-drop and on direction for 頼む/よろしく).
Keep tone and register; keep stutters and shouts in English form ("W-wait!"). Do not infer gender from
names; the glossary records sourced genders.

## Rules added on 2026-10-02
Five rules adapted from LinguaGacha's English prompt template now live in `BASE_RULES.md` (one row in /
one row out, spoken register, a two-step context/decisions check per row, translate what the player
reads and leave what the game reads, no softening). Read them there; they are not repeated here.
The files as they were for the first Stage 30 comparison are kept as `TRANSLATOR_BRIEF_v1.md` and
`BASE_RULES_v1.md` in this folder.

## Conventions already used in the translated prologue (keep them)
- Honorifics are dropped (ブライトさん -> "Bright") unless the glossary gives a fixed form.
- Long silences (………) become "...".
- 第一種/第二種戦闘配置 -> "Level 1 / Level 2 battle stations".
- Some raw lines carry a stray `」@　` at the end; ignore it, translate the text only.
- `work/translation/en/script/prologue_merged.json` holds finished lines; you may read it to see how
  similar lines were solved, but translate your own lines yourself.
