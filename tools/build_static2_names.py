"""Build the English name tables for STATIC2_ADD.BIN (Strg names and Sprt spirit names).

usage: python build_static2_names.py
Reads work/source/text_inventory/static2_names.json and static2_spirits.json (tools/text_inventory.py),
the glossary (glossary.json + campaign_terms.json) and work/translation/en/static2/voice_actors.json.
Writes work/translation/en/static2/names.json and spirits.json (English only, keyed by index) and
reports names without English, characters the font cannot draw, and names wider than the Japanese.

Rules: display names (units, weapons, pilots, skills, abilities, parts) take the glossary English;
voice actors take voice_actors.json; unit height/weight strings are converted to ASCII digits;
sort readings, BGM titles (out of scope) and placeholders keep their Japanese bytes (null).
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
SKILL_SHORT = {'Support Attack Lv': 'Support Atk Lv', 'Support Attack+': 'Support Atk+',
               'Support Defend Lv': 'Support Def Lv', 'Support Defend+': 'Support Def+',
               'Enhanced Human Lv': 'Enh. Human Lv', 'Clear Mind Still Water': 'Clear Mind'}
SPRT_SHORT = {'Accelerate': 'Accel', 'Disturbance': 'Disturb', 'Inspiration': 'Inspire',
              'Super Guts': 'S. Guts', 'Encourage': 'Encour.'}


def main():
    g = glossary_map()
    va = json.load(open(os.path.join(OUT, 'voice_actors.json'), encoding='utf-8'))
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
            if en is None:
                missing.append(x)
        elif 'voice_actor' in own:
            en = va.get(t)
            if en is None:
                missing.append(x)
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
