PS2 FORECAST COPY FIX CANDIDATE v0.9.4 - HARDWARE TEST

Apply this bare xdelta ONLY to the correctly patched PS2 English v0.9.0 ISO.
Do not apply it to a Japanese ISO, PSP image or previous diagnostic build.
Preserve your existing image.

Source SHA-256: f2a7b452d5feecc7dd784d94d332842cb0ddb0160f8e62474a3d92dca0a3faee
Expected output SHA-256: 2663be07358f1eaa0d2c2f5dab4825cb6f2abc4dc3ef495c94ef082933b5ea90
The native title must show v0.9.4 and github.com/retro-trans.

This candidate fixes three forecast action-label copies. English No Counter
and Support Def strings are not eight-byte aligned and exceed the original
fixed copy length. The original native LD instructions fault in strict CPU
tests; these same faults remain in the earlier v0.9.1, v0.9.2 and v0.9.3 probes.
The candidate copies complete NUL-terminated strings using byte reads instead.

The mission, gameplay, English resource data, replacement font, disc positions,
heap boundary and original public menu wrappers remain unchanged. The shared
32-byte helper fits existing segment padding. This is a focused forecast fix
candidate, not a complete UI audit or a public release.

Validation: three public forecast faults reproduced; 24 forecast path cases
and 24 arbitrary-alignment cases pass with complete strings and dirty-buffer
guards. Full xdelta reconstruction and image hash verification pass.
Physical PS2 validation and visual forecast verification are still pending.

Use the same PS2, loader and settings as the failing test. Repeat the exact
action that previously froze before the battle forecast. Please report:
1. Does the battle forecast now appear?
2. Can you select an action and complete the battle?
3. Which loading method and OPL compatibility modes were used?

No ISO is included. This patch is hosted for issue #1 hardware testing.
