# PSP Chapter 55 stage-load failure — 2026-11-09

The supplied PSP in-game save reaches Scene 10 with 55 stages cleared. From
Intermission, choose Next Map, Outer Space, then Yes. This selects `s1050`,
Chapter 55, Across Infinite Time.

Public v0.4.54 requests 206,848 bytes for the English stage script. The
262,144-byte script pool already has three live allocations and only 199,360
contiguous bytes free. Its native allocator returns zero. The map can open
without its script, leaving the Objectives panel blank and skipping its
opening events. The reported emulator exit itself was not reproduced in
isolated PPSSPP v1.20.4.

Retrying in the larger map pool restored the opening, but the v0.4.56
prototype failed later. The stage buffer at `0x099e8100` was fully covered
by a successful 555,008-byte battle resource read into `0x099cbd00`. The
game then attempted to execute address zero. This pool is reused by battle
loading and cannot hold the stage script throughout the encounter. The
v0.4.56 test image is superseded and should not be used.

Local PSP v0.4.57 reserves a 206,848-byte buffer in the game's loaded
executable, outside both reused resource pools. The loader still uses the
ordinary allocator first. The fallback is restricted to the exact `s1050`
name and a nonzero request that fits the reserve. The release wrapper skips
only that reserved pointer, even if the next scene is already named; every
normal pointer follows the original free call. The two existing call-site
relocations are retained; the wrappers add three jump relocations. The
resource heap sizes, save format, stage commands and dialogue are unchanged.
The candidate is built over local v0.4.55, retaining its name corrections.

Nine offline cases execute the real allocator and free routine against pools
captured from the save. These include the original failure, repeated fallback
and cleanup, normal fits, unrelated and same-prefix names, both pools full,
and requests outside the reserve bounds. See the actual ISO evidence in
`work/output/psp_s1050_0.4.57_verification.json`.

The actual v0.4.57 ISO cold-booted in PPSSPP v1.20.4 with the PSP-1000
profile. Startup retained `0x10e6000` bytes free before the game's 16 MiB
arena allocation. The supplied save passed the former battle-resource
overwrite point, reached Sortie Prep, deployed Full Armor Dendoh and showed
the populated Chapter 55 objectives. Normal unit commands opened afterward.
All 206,848 script bytes matched the ISO at the opening, after the scripted
battle and after deployment. The replay had no execution fault and both the
incoming save and test copy were unchanged. See
`work/output/psp_s1050_0.4.57_runtime.json` and
`work/ui/psp/s1050_0.4.57/`. No release was requested.
