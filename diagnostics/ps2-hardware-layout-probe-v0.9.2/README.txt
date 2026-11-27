PS2 HARDWARE LAYOUT PROBE v0.9.2 - DIAGNOSTIC ONLY

This is an experiment for GitHub issue #1, not a confirmed fix or public release.

Apply the bare xdelta patch to the correctly patched PS2 English v0.9.0 ISO.
Do not apply it to a Japanese ISO or a PSP image. Preserve your v0.9.0 image.
Expected source SHA-256: f2a7b452d5feecc7dd784d94d332842cb0ddb0160f8e62474a3d92dca0a3faee
Expected test output SHA-256: 1b5ad1ed0e653b39edadd6d9dde708323854d75f3e73690f318d6ad64ad4f166

The native title must show v0.9.2 and github.com/retro-trans.
This test packs all live resources below 4 GiB. It retains the public v0.9.0
runtime hooks, replacement font and translation data. Only disc placement,
filesystem metadata and the native title version change.
The earlier v0.9.1 stock-font test still froze on the reporting console.

Use the same real PS2, OPL build and MC2ISO setup as the failing test. Start a
New Game and trigger the first battle. Report separately:
1. Does the first New Game combat/menu transition still freeze?
2. If it works, does the attack finish and return to the map?
3. Report adapter or SMB loading and confirm the output hash above.
Please test the same console and OPL version as before.

If combat works here, disc placement is implicated. This alone does not identify
a particular loader bug or prove 4 GiB overflow. If it still freezes, the
runtime/resource changes remain under investigation.
Do not use this diagnostic build for a long playthrough or a release update.

No ISO is included. This diagnostic is hosted for issue #1 testing; no GitHub release was created.

