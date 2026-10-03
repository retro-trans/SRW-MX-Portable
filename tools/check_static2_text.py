"""Wrap and check the English for STATIC2_ADD.BIN description / help entries.

usage: python check_static2_text.py [table ...] [--show]
Reads work/translation/en/static2/descriptions.json and the Japanese rows in
work/source/text_inventory/static2_rows.json (tools/text_inventory.py). Each English paragraph is
wrapped to the box of its table: the row width is the widest Japanese row of that table (16 px per
full-width character) and the row limit is the most rows any Japanese entry of that table uses.
Reports entries without English, entries that need more rows than the box has, and characters the
font cannot draw. --show prints every wrapped entry.
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TABLES = ['XSpr', 'XSkl', 'Xabl', 'XPrt', 'XHlp']
# the top help window holds about 420 px per row (seen in game, 0.3.2); same values as insert_text
WIDTH_CAP = {'XSpr': 416, 'XSkl': 416, 'Xabl': 416, 'XHlp': 416}
ALLOWED = set(textfit.ASCII) | {'"'} | set('㍉㌦㌧○□△')   # icon glyphs kept from the Japanese font


def jp_px(t):
    return sum(16 if ord(c) > 0x7F else 8 for c in t)


def boxes(rows):
    ent = defaultdict(list)
    for r in rows:
        ent[(r['index'], r['entry'])].append(r['text'])
    box = {}
    for t in TABLES:
        es = [v for (i, _), v in ent.items() if i == t]
        box[t] = (min(max(jp_px(x) for v in es for x in v), WIDTH_CAP.get(t, 9999)), max(len(v) for v in es))
    return ent, box


def wrap(text, width):
    lines, _ = textfit.wrap('', text, '', line_px=width, indent='')
    return lines


def main(*args):
    tr = json.load(open(os.path.join(ROOT, 'work/translation/en/static2/descriptions.json'), encoding='utf-8'))
    rows = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/static2_rows.json'), encoding='utf-8'))
    ent, box = boxes(rows)
    tables = [a for a in args if a in TABLES] or TABLES
    total = bad = 0
    for t in tables:
        width, maxrows = box[t]
        es = sorted(e for (i, e) in ent if i == t)
        missing = [e for e in es if str(e) not in tr.get(t, {})]
        over, chars = [], []
        for e in es:
            en = tr.get(t, {}).get(str(e))
            if en is None:
                continue
            total += 1
            lines = wrap(en, width)
            if len(lines) > maxrows or any(textfit.px(l) > width for l in lines):
                over.append((e, lines))
            if set(en) - ALLOWED:
                chars.append((e, ''.join(sorted(set(en) - ALLOWED))))
            if '--show' in args:
                print(f'{t} {e}:', ' | '.join(lines))
        bad += len(missing) + len(over) + len(chars)
        print(f'{t}: box {width} px x {maxrows} rows; entries {len(es)}; missing {len(missing)}; '
              f'too long {len(over)}; bad characters {len(chars)}')
        for e in missing[:20]:
            print('  MISSING', e)
        for e, lines in over:
            print(f'  OVER {e} ({len(lines)} rows):', ' | '.join(f'{l} [{textfit.px(l)}]' for l in lines))
        for e, c in chars:
            print(f'  CHAR {e}: {c!r}')
    print(f'checked {total} entries; problems: {bad}')


if __name__ == '__main__':
    main(*sys.argv[1:])
