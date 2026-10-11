# PSP 0.4.14 — four screenshot reviews

1. **George De Sand**: the user's explicitly requested spelling overrides
   Akurasu's joined surname. Applied to native Strg 1190, all five story uses,
   current glossary/variant records, library name and battle speaker metadata.
   The unit/pilot IDs and short name George remain the same.
2. **Karl's line** (stage 6, i014b:23): accurate. The original says he hears
   young officers back in their homeland on the Moon are increasingly
   dissatisfied with the corruption of the man under discussion and the
   military's upper ranks. The sentence's pronoun points back to the earlier
   discussion; the original does not give a new name in this line.
3. **Sound Select**: the pictured Japanese titles had already been translated
   in PSP 0.4.11. All 80 music-table entries read back in 0.4.14. Two long
   G Gundam titles that previously used romanization now have compact English
   display translations. See `docs/glossary_decisions.md` for their meanings,
   sources and width constraints. The title highlighted in the report means
   that one's mind is clear and serene, while one's palm blazes like fire.
4. **Rockfell's line** (stage 7, i015b:73): the earlier translation preserves
   the meaning but sounds stiff. New text: `Damn Taiha... He's gotten full of
   himself just because he's Yuratei's favorite...`. More literally: "That
   Taiha... becoming conceited just because he receives Yuratei's special
   affection/favor...". The dismissive name suffix and final verb convey
   Rockfell's irritation. Special affection is stronger than simple approval;
   this sentence alone does not specify a romantic or sexual relationship.

## Build and evidence

Reproduction uses the existing local PSP 0.4.13 ISO:

```text
py -3.8-32 tools/record_psp_0414_sources.py
py -3.8-32 tools/fix_psp_0414.py
py -3.8-32 tools/verify_psp_0414.py
py -3.8-32 tools/verify_psp_0411.py 0.4.14
py -3.8-32 tools/verify_text_build.py 0.4.14
```

The source recorder preserves its baseline English manifest and refuses
accidental regeneration. Reviewed story files and their English-only copies
include refreshed review fingerprints. Japanese script remains only in
ignored local working files; no commit or release is performed.

Only six story slots change. Their rows measure at most 348 pixels against
352; the native command bytes, all other strings and sector budgets remain
exact across all 203 blocks. STATIC changes only the three Strg pointers.
The complete previous overflow table's 3,834 pointers remains exact. The
reusable table appender now recognizes an already-appended table through its
contiguous native pointer-relocation run instead of assuming its strings
immediately follow the table.

All 32 disc-file hashes pass readback. The new executable, MAP and STATIC
are preserved in `work/build/psp_text_0.4.14`. Native execution checks all
80 music titles and five menu wrappers, plus the earlier Spirit Cost,
Level Up and narration fixes. Names read back 1,580/1,580 and BOOT references
1,763/1,763. All seven entries visible in a fresh profile's actual Sound
Select are centered and readable, including `A Serene Mind, A Blazing Palm`.
The other locked music entries have native table/width verification.

An isolated fresh boot (`work/build/psp_0414_test`) verifies all 3,837
relocated text pointers, the three getter pairs and the three added strings.
Verification reads original instruction words rather than PPSSPP's JIT
replacement markers. Normal user emulator profiles are untouched.

Evidence: `work/output/psp_text_0.4.14_{verification,execution,runtime}.json`
and `work/output/psp_fixes_0.4.14_native_tests.json`. Reported screenshots and
actual Sound Select capture: `work/ui/psp/0.4.14/`. Story playthrough and
physical PSP verification remain pending.

Local ISO: `work/output/SRWMX_EN_0.4.14.iso`.
SHA-256: `15f32a409041b218068b0b026d32212a286eeb184e5e948b82d2070e979d9826`.
Public PSP/PS2 releases remain 0.4.12; this local build has no release request.
