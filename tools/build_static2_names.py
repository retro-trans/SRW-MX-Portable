"""Build the English name tables for STATIC2_ADD.BIN (Strg names and Sprt spirit names).

usage: python build_static2_names.py
Reads work/source/text_inventory/static2_names.json and static2_spirits.json (tools/text_inventory.py),
the glossary (glossary.json + campaign_terms.json) and work/translation/en/static2/voice_actors.json.
Writes work/translation/en/static2/names.json and spirits.json (English only, keyed by index) and
reports names without English, characters the font cannot draw, and names wider than the Japanese.

Rules: display names (units, weapons, pilots, skills, abilities, parts) take the glossary English;
voice actors take voice_actors.json; unit height/weight strings are converted to ASCII digits;
sort readings and placeholders keep their Japanese bytes (null); BGM takes music.en.json.
A string shared by a display name and a reading is translated (the display wins).
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit
from text_inventory import glossary_map

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'work/source/text_inventory')
OUT = os.path.join(ROOT, 'work/translation/en/static2')
DISPLAY = {'unit', 'weapon', 'pilot_full', 'pilot_short', 'skill', 'ability', 'part'}
FULLWIDTH = {chr(0xFF10 + i): str(i) for i in range(10)}
FULLWIDTH.update({'．': '.', 'ｍ': 'm', 'ｔ': 't'})
SPECIAL = {'無し': 'None'}
# Consistency fixes on top of the glossary (akurasu uses both spellings; majority form kept).
FIXES = {'Power Riser (Garudi)': 'Power Raiser (Garudi)'}
SPRT_FIELD = 12                     # bytes, inline in each Sprt record (incl. NUL)
# Sprt names are drawn in the spirit list, whose SP column starts about 63 px after the name
# (seen in game, 0.2.0); longer glossary names get a short form there.
# Pilot skills are listed on the pilot status screen with the level digit appended, in 121 px before
# the level column (x+0x117 .. x+0x190; seen in game, 0.2.1). Longer ones get a short form.
# Weapon names are listed in the weapon list with about 150 px (14 px font) before the Attack
# column (seen in game, 0.4.4); 30 longer glossary names get a short display form.
WEAPON_SHORT = {
    'Tenku Shinken Secret: Twin Kamaitachi': 'Shinken: Twin Kamaitachi',
    'Tenku Shin Ken: Lightning Double Slash': 'Shinken: Lightning 2-Slash',
    'Tenku Shin Ken: Explosive Aerial Spin': 'Shinken: Explosive Spin',
    'Deadly Gale Correct Fist Thrust Kai': 'Gale Fist Thrust Kai',
    'Deadly Gale Correct Fist Thrust': 'Gale Fist Thrust',
    'Mandala Formation: Gokuraku Ojo': 'Mandala: Gokuraku Ojo',
    'Tenku Chushin Ken: Straight Punch': 'Chushin: Straight Punch',
    'Tenku Chushin Ken: Rapid-Fire Fist': 'Chushin: Rapid-Fire Fist',
    'Lightning Cyclone Bedrock Splitter': 'Lightning Rock Splitter',
    'Tenku Shin Ken: Swallow Reversal': 'Shinken: Swallow Reversal',
    'Tenku Shin Ken: Vacuum Tornado': 'Shinken: Vacuum Tornado',
    'Tenku Chushin Ken: Rock Splitter': 'Chushin: Rock Splitter',
    'Multi-Convergence Impact Laser': 'Multi-Conv. Impact Laser',
    'Fate-Severing Sword Twin Blade': 'Fate-Severing Twin Blade',
    'High Mega Cannon (Full Power)': 'High Mega Cannon (Full)',
    'Double Tomahawk Boomerang': 'D. Tomahawk Boomerang',
    'Tenku Chushin Ken: Mantis Fist': 'Chushin: Mantis Fist',
    'Large Vegatron Beam Cannon': 'Large Vegatron Cannon',
    'Tenku Shinken: Piercing Thrust': 'Shinken: Piercing Thrust',
    'Super Vegatron Beam Cannon': 'Super Vegatron Cannon',
    'Twin 25 mm Machine Cannon': 'Twin 25mm Autocannon',
    'Twin 20 mm Machine Cannon': 'Twin 20mm Autocannon',
    'Bueikyaku (No-Shadow Kick)': 'Bueikyaku',
    'Sekiha Love Love Tenkyoken': 'Love Love Tenkyoken',
    'Dimensional Coupler Cannon': 'Dim. Coupler Cannon',
    'Hyper Mega Particle Cannon': 'Hyper Mega Part. Cannon',
    'Large Mega Particle Cannon': 'Lg. Mega Particle Cannon',
    'Tenku Shin Ken: Falling Leaf': 'Shinken: Falling Leaf',
    'Large-Caliber Beam Cannon': 'Large-Cal. Beam Cannon',
    'Tenku Shin Ken: Kamaitachi': 'Shinken: Kamaitachi',
}
SKILL_SHORT = {'Support Attack Lv': 'Support Atk Lv', 'Support Attack+': 'Support Atk+',
               'Support Defend Lv': 'Support Def Lv', 'Support Defend+': 'Support Def+',
               'Enhanced Human Lv': 'Enh. Human Lv', 'Clear Mind Still Water': 'Clear Mind'}
SPRT_SHORT = {'Accelerate': 'Accel', 'Disturbance': 'Disturb', 'Inspiration': 'Inspire',
              'Super Guts': 'S. Guts', 'Encourage': 'Encour.'}


def main():
    g = glossary_map()
    va = json.load(open(os.path.join(OUT, 'voice_actors.json'), encoding='utf-8'))
    music = json.load(open(os.path.join(OUT, 'music.en.json'), encoding='utf-8'))['titles']
    names = json.load(open(os.path.join(SRC, 'static2_names.json'), encoding='utf-8'))
    allowed = set(textfit.ASCII) | {'"'}
    out, missing, chars, wide = {}, [], [], []
    for x in names:
        t, own = x['text'], set(x['owners'])
        en = None
        if t in SPECIAL:
            en = SPECIAL[t]
        elif set(t) <= set('－'):
            en = None                                   # dash placeholder ("no voice actor")
        elif own & DISPLAY:
            en = FIXES.get(g.get(t), g.get(t))
            if 'skill' in own:
                en = SKILL_SHORT.get(en, en)
            if 'weapon' in own:
                en = WEAPON_SHORT.get(en, en)
            if en is None:
                missing.append(x)
        elif 'voice_actor' in own:
            en = va.get(t)
            if en is None:
                missing.append(x)
        elif 'bgm' in own:
            en = music.get(str(x['idx']))
        elif 'unit_size_weight' in own:
            en = ''.join(FULLWIDTH[c] for c in t)
        out[str(x['idx'])] = en
        if en:
            bad = set(en) - allowed
            if bad:
                chars.append((x, en, bad))
            if textfit.px(en) > 16 * len(t) and own & DISPLAY:
                wide.append((x, en))
    sp = json.load(open(os.path.join(SRC, 'static2_spirits.json'), encoding='utf-8'))
    spirits, sp_long = {}, []
    for x in sp:
        en = SPECIAL.get(x['text']) or g.get(x['text']) or (None if set(x['text']) <= set('？') else '')
        en = SPRT_SHORT.get(en, en)
        spirits[str(x['idx'])] = en
        if en and len(textfit.encode(en)) >= SPRT_FIELD:
            sp_long.append((x['text'], en))
    json.dump(out, open(os.path.join(OUT, 'names.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(spirits, open(os.path.join(OUT, 'spirits.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    n = sum(1 for v in out.values() if v)
    print(f'Strg: {len(out)} strings, {n} with English, {len(out) - n} kept (readings, BGM, placeholders)')
    print(f'  missing English: {len(missing)}', [x["text"] for x in missing][:20])
    print(f'  undrawable characters: {len(chars)}')
    for x, en, bad in chars:
        print(f'    {x["idx"]} {en!r}: {"".join(sorted(bad))!r}')
    print(f'  display names wider than their Japanese: {len(wide)} (fine in most windows; check long ones)')
    print(f'Sprt: {len(spirits)} spirit names; {len(sp_long)} do not fit the {SPRT_FIELD}-byte inline field '
          f'(2 bytes per letter): served from the PRX overflow table by the patched name getter (insert_text.py)')


if __name__ == '__main__':
    main()
