"""Merge translated slices into <scene>_merged.json and check them.

usage: python merge_slices.py work/translation/en/script/prologue.json
Reads <scene>_slice_*.json next to it, writes <scene>_merged.json, prints problems.
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

ALLOWED = set(textfit.ASCII) | {'"'}


def main(path):
    base = path[:-5]
    d = json.load(open(path, encoding='utf-8'))
    rows = {r['id']: r for r in d['rows']}
    done = set()
    for fn in sorted(glob.glob(base + '_slice_*.json')):
        for r in json.load(open(fn, encoding='utf-8'))['rows']:
            t = rows[r['id']]
            t['en'] = r.get('en') or ''
            if r.get('speaker_en'):
                t['speaker_en'] = r['speaker_en']
            t['notes'] = r.get('notes', '')
            t['uncertain'] = r.get('uncertain', [])
            done.add(r['id'])
    problems = []
    for i, r in rows.items():
        if not r.get('en'):
            problems.append(f'{i}: not translated')
            continue
        rest = r['en']
        for ph in textfit.PLACEHOLDER_PX:
            if (r['jp'] if r['kind'] == 'plain' else r['body_jp']).count(ph) != rest.count(ph):
                problems.append(f'{i}: placeholder {ph} count differs')
            rest = rest.replace(ph, '')
        if r['kind'] != 'plain':
            bad = sorted(set(rest) - ALLOWED)
            if bad:
                problems.append(f'{i}: characters not in font {bad}')
            o = '（' if r['kind'] == 'thought' else '「'
            lines, ok = textfit.wrap((r.get('speaker_en') or '') + o, r['en'], '」')
            r['lines'] = len(lines)
            r['px'] = max(textfit.px(l) for l in lines)
            if not ok:
                problems.append(f'{i}: does not fit ({len(lines)} lines, {r["px"]}px)')
        else:
            bad = sorted(set(rest.replace('@', '')) - ALLOWED)
            if bad:
                problems.append(f'{i}: characters not in font {bad}')
            if r['jp'].count('@') != r['en'].count('@'):
                problems.append(f'{i}: line count differs from Japanese')
    json.dump(d, open(base + '_merged.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(done)}/{len(rows)} rows translated; problems: {len(problems)}')
    for p in problems:
        print('  ', p)


if __name__ == '__main__':
    main(sys.argv[1])
