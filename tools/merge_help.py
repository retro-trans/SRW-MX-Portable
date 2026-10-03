"""Fill the XHlp table of work/translation/en/static2/descriptions.json.

usage: python merge_help.py [--write]
Help entries whose Japanese is a word-for-word copy of a spirit / skill / ability / part description
get that description's English; the others come from work/translation/en/static2/help.json. Without
--write it only reports what it would do.
"""
import json, os, sys
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DESC = os.path.join(ROOT, 'work/translation/en/static2/descriptions.json')


def main(*args):
    rows = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/static2_rows.json'), encoding='utf-8'))
    tr = json.load(open(DESC, encoding='utf-8'))
    manual = json.load(open(os.path.join(ROOT, 'work/translation/en/static2/help.json'), encoding='utf-8'))
    ent = defaultdict(list)
    for r in rows:
        ent[(r['index'], r['entry'])].append(r['text'])
    known = {}
    for (i, e), v in ent.items():
        if i != 'XHlp' and tr[i].get(str(e)):
            known.setdefault(''.join(v), tr[i][str(e)])
    out, copied, missing = {}, 0, []
    for e in sorted(e for (i, e) in ent if i == 'XHlp'):
        k = str(e)
        if k in manual:
            out[k] = manual[k]
        elif ''.join(ent[('XHlp', e)]) in known:
            out[k] = known[''.join(ent[('XHlp', e)])]
            copied += 1
        else:
            missing.append(e)
    print(f'help entries: {len(out)} ({copied} copied from descriptions); missing: {missing}')
    if '--write' in args:
        tr['XHlp'] = out
        json.dump(tr, open(DESC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('written', DESC)


if __name__ == '__main__':
    main(*sys.argv[1:])
