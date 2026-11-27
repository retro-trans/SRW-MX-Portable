PS2 HARDWARE MENU PROBE v0.9.3 - DIAGNOSTIC ONLY

This is an experiment for GitHub issue #1, not a confirmed fix or public release.

Apply the bare xdelta patch to the correctly patched PS2 English v0.9.0 ISO.
Do not apply it to a Japanese ISO, PSP image or earlier diagnostic build.
Preserve your v0.9.0 image.
Expected source SHA-256: f2a7b452d5feecc7dd784d94d332842cb0ddb0160f8e62474a3d92dca0a3faee
Expected test output SHA-256: 4be1fc8a446f66e28a8aa6c0619496a9a809c3859397ed2db9a0f0080fbed0a9

The native title must show v0.9.3 and github.com/retro-trans.
This test restores five original menu/forecast call sites: cached-label
translation, long weapon-name fitting and forecast-name abbreviation.
English resources, the replacement font, heap boundary, combat-quote hooks
and disc layout match public v0.9.0. The native title version is updated.
Some cached labels may be Japanese and long names may overlap columns.

Use the same real PS2, OPL build and MC2ISO setup as the failing test. Start a
New Game and trigger the first battle. Report separately:
1. Repeat the exact action that previously froze before the weapon window.
2. Does the weapon-selection window now appear?
3. If it does, can you select an attack and complete combat?
Report the loading method and confirm the output hash above.

If the weapon window works here, these menu/forecast wrappers are implicated;
that does not yet identify which wrapper is responsible. If it still freezes,
other runtime and resource changes remain under investigation.
Do not use this diagnostic build for a long playthrough or a release update.

No ISO is included. This diagnostic is hosted for issue #1 testing; no GitHub release was created.

Validation: 36 native call cases pass. Complete patch reconstruction and image
hashes pass. The player weapon window has not been visually verified: Windows
denied desktop access during that check. Hardware compatibility is unconfirmed.

