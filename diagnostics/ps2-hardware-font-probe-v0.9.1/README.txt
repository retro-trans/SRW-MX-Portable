PS2 HARDWARE FONT PROBE v0.9.1 - DIAGNOSTIC ONLY

This is an experiment for GitHub issue #1, not a confirmed fix or public release.

Apply the bare xdelta patch to the correctly patched PS2 English v0.9.0 ISO.
Do not apply it to a Japanese ISO or a PSP image. Preserve your v0.9.0 image.
Expected source SHA-256: f2a7b452d5feecc7dd784d94d332842cb0ddb0160f8e62474a3d92dca0a3faee
Expected test output SHA-256: b115e8876e07783186379f5420b7c3411b4e0b8a333afc66e39edcb8c17f2c00

The native title must show v0.9.1 and github.com/retro-trans.
This test restores the original 24-pixel font path. English remains, but text
may be wider and crowd the menus. Translation and battle resources, disc layout,
combat hooks, gameplay data and save format match public v0.9.0.

Use the same real PS2, OPL build and MC2ISO setup as the failing test. Start a
New Game and trigger the first battle. Report separately:
1. Does combat still freeze at the same point?
2. Does the unit-name text still have missing strokes?
3. Does the unmodified Japanese game start combat on the same loader/setup?

If combat works here, that implicates the replacement font path; it does not
identify the precise fault. If it still freezes, the cause remains unresolved.
Do not use this diagnostic build for a long playthrough or a release update.

No ISO is included in this folder. Nothing was published to GitHub.
