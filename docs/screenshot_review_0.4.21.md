# Screenshot corrections 0.4.21

The five reported issues are applied to PSP and the matching PS2 data.
Both local candidates start from 0.4.20, retaining its startup warning fix.

| Item | Result | Reason |
| --- | --- | --- |
| Unit name | Bryst of the Fires | Explicit user spelling; overrides Akurasu's Briest. Short references and battle quotes use Bryst too. |
| Bahbem, Chapter 13 | They're ideal for stalling... No, as decoys to draw our attention and lure the enemy. | The Japanese means attract attention and the enemy, rather than draw them out. The speaker's self-correction is retained. |
| Dr. Inoue, Chapter 14 | the Mu | The faction name is Mu, not an uppercase acronym. His explanation about the Bahbem Foundation's research and advanced technology is otherwise accurate. |
| Rom, Chapter 15 | I have no name to give the likes of you!! | Accurate contemptuous refusal to introduce himself: he refuses to tell his opponents his name, rather than claiming to be nameless. No change. |
| Chapter 16 title | Blue Meets White | Uniform centered lettering replaces the native mixed-size artwork. All three copies on each platform are covered. |

## Source and build records

`work/translation/en/ui/screenshot_review_0.4.21.en.json` lists every changed
assembled campaign row and the current input files. The retained Japanese
baselines remain in ignored working sources. Current review fingerprints and
their journals are updated. Historical proofreading decisions retain their
original wording; the cumulative HTML report incorporates documented later
terminology corrections without editing those frozen decisions.

`tools/fix_reviewed_text_0421.py --audit` identifies and records exact native
terminated-string candidates before any ISO mutation. `--inputs` updates
current translation inputs once, preserving the baseline manifest.
`--build` creates new versioned candidates without replacing earlier builds.
Its scope excludes untranslated Japanese backup strings and executable code.

## Validation

Native replacements retain their allocation and terminators; shorter text is
padded with zero bytes. Script commands, pointer tables, file lengths and disc
sectors are preserved. All 203 story blocks are compared independently, with
every unrelated string unchanged. Every ISO file is read back and verified;
PS2 ISO9660 and UDF views must agree. An independent comparison checks every
disc byte outside the declared text allocations and title rectangles.

Chapter-card palettes are hash guarded and unchanged. Native PSP and PS2
previews are in `work/ui/{psp,ps2}/screenshot_review_0.4.21/`; all ink fits inside
the title rectangle and the two inspected platform previews match. The image
patch covers only the first 52 rows of each 256×256 title atlas.

Verification reports: `work/output/psp_screenshot_review_0.4.21_verification.json`
and `work/output/ps2_screenshot_review_0.4.21_verification.json`. The PS2 font
chain also records the updated executable and affected story block hashes.
Current-source text fits are recorded separately in
`work/output/screenshot_review_0.4.21_source_validation.json`.

These incremental ISOs include only the listed corrections over 0.4.20; they
do not contain the broader completed campaign proofreading. In-game visual
confirmation and physical hardware testing remain pending. No release created.
