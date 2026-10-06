# PS2 0.1.16 weapon and battle UI

Build with `python tools/fix_ps2_weapon_battle.py --build`, starting from
the preserved 0.1.15 resources. Output is
`work/output/SRWMX_PS2_EN_0.1.16.iso`. No release or push is requested.

Weapon selection uses **Weapons**. The native attribute formatter now
always terminates its temporary string after one encoded character.
The previous two-character Assist abbreviation exceeded that formatter's
three-byte buffer, exposing old weapon-name bytes on the stack. Assist
uses **A**, solid/physical weapons use **S**, and the existing M/G/B flags
retain their meaning. Dirty-buffer execution checks cover all four flags.

Long names in the weapon list fit a 174px area inside the original 182px
column. Both font axes scale together; the baseline is compensated and
the original font context is restored after each draw. Names remain
complete. Numeric and attribute columns keep their original dimensions.

Only the battle forecast abbreviates **Giganos Soldier** to
**Giganos Sldr.** The full database and dialogue name is retained. Exact
whole-string matching protects other pilot names and prefix matches.

The shared MAP M_19 image reads **Critical**, using its original palette
and native pixel layout. The original Critical string slot is translated
too. Integer and float CFont entry wrappers translate complete cached
Japanese Will, Critical and Weapons labels that bypass pointer tables.
Other strings pass through, with the original function prologue replayed.

Verification executes eight dirty-buffer flag cases, ten forecast cases,
ten cached-label cases and twenty weapon-name fitting cases. It checks
uniform proportions, baseline placement, argument/context restoration,
exact executable edit ranges and the 2,048-byte M_19 pixel payload.
Earlier prologue, UI, details, roster, setup, campaign and difficulty checks
run again. Historical MAP preservation checks allow only the declared
support-caption and Critical payloads, checking every other byte.

User screenshots and asset previews are in
`work/ui/ps2/weapon_battle_0.1.16/`. The decoded Critical preview is an
asset preview, not an emulator capture. Actual battle-animation Critical
and Will visual confirmation remains pending: the animation's draw path
has not been positively identified as CFont. Native fallback execution
checks alone do not prove that every baked battle graphic is translated.

Test with a fresh disc boot, then a memory-card save. An emulator save
state restores old executable bytes and cached resources. Existing user
PCSX2 processes must be left untouched; use the isolated PINE 28018 profile
for fresh-boot runtime checks. Physical PS2 validation remains pending.

Final validation: all 37 ISO9660 disc files and replacement UDF readbacks
pass. Compared with 0.1.15, only the executable and MAP archive change.
Fresh PCSX2 boot at 4x with texture replacements disabled confirms all
177 hook/reference checks and the 778,168-byte
native segment. No unknown opcode or TLB warnings were observed. This
checks loaded bytes, not battle-animation visuals.

Final ISO: 4,663,267,328 bytes. SHA-256:
`d5d904e771e2f72410b757f250d2eca89568cefa547628b5bc0eb75419b4d066`.
