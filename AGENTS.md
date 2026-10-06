** Organize folder like this **
work - work folder
    output - contains the file for testing (iso, zip, etc...)
    glossary - contains the one or many json files for glossary
    ui - contains screenshot of actual UI element ingame with label on screenshot if possible, contains files (json,py,...) describe the coordinate, width and height, id and other attributes
    translation/<language code> - contains the target translation of ui element or dialogues or anything that need translation
docs - documents
tools - any tools help with translation
incoming - outside files that need agent to look into

** SOME RULES **
- Avoid contains extensive Japanese scripts (UI elements is fine)
- Identified each build with version 0.x.y (start at 0.1.0)
- Always write change log
- If user told you to remember anything write it down here, make sure to ask user if the new one conflict with old one
- Be conscious of subscription limit before creating sub-agents

** REMEMBER **
- Publish bare `.xdelta` patches for both platforms; do not wrap the PS2 patch in a ZIP.
- Public PSP and PS2 releases share the PSP version number; preserve historical PS2 test labels in verification records.
- Thought dialogue must have exactly one space between the speaker name and opening parenthesis: `Daisuke (thought...)`.
- Do not create or publish a GitHub release until the user explicitly requests a release for that build. Translation and local builds do not imply release permission.
- Every new github release must work with [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).
- Use akurasu.net (https://akurasu.net/wiki/Super_Robot_Wars/MX) as the main source for terms (names, units, abilities, spirit commands, parts). Use other wikis only where akurasu has no entry. Refresh with `tools/akurasu_terms.py`; overrides of akurasu need a reason in `work/glossary/decisions.json` / `docs/glossary_decisions.md`.
- Japanese script text must never be committed to git. Keeping it in local working files is fine: `.gitignore` covers `work/source/` and the translation working files. Commit only the `*.en.json` copies written by `tools/strip_jp.py` (run it before committing). Names and UI terms in Japanese are allowed.
