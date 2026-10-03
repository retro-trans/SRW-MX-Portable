"""Export script rows of chosen scenes for translation, in play order, deduplicated.

usage: python export_rows.py <MAP_ADD.BIN> <out.json> <scene name> [...] [--exclude done.json]
Scene names come from work/source/stage_map.json (e.g. i001b s00r00 i00r0a).

Row kinds:
  dialogue  Speaker「body」     -> translate body, speaker from glossary
  thought   Speaker（body）
  plain     anything else with Japanese (mission objectives, notes) -> keep '@' line breaks
  label     ASCII asset labels (i00r1a ...) -> never translated, not exported
"""
import json, os, re, struct, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SCRIPT_BASE = 0x579C * 0x800
SPK = re.compile(r'^([^「（@]{1,14}?)([「（])(.*?)([」）]?)$', re.S)


def blocks(map_add):
    d = open(map_add, 'rb').read()
    sm = json.load(open(os.path.join(ROOT, 'work/source/stage_map.json'), encoding='utf-8'))
    out = {}
    for r in sm:
        o = r['offset']
        n, tab = struct.unpack_from('<2I', d, o + 8)
        strs = [d[o + p:d.index(b'\0', o + p)].decode('cp932') for p in struct.unpack_from(f'<{n}I', d, o + tab)]
        out[r['name']] = strs
    return out


def speakers():
    g = json.load(open(os.path.join(ROOT, 'work/glossary/glossary.json'), encoding='utf-8'))
    m = {'？？？': '???', '#男愛称': '#男愛称', '#女愛称': '#女愛称'}
    for c in g['characters']:
        for k in (c.get('jp_short'), c.get('jp_full')):
            if k and c.get('en_short'):
                m.setdefault(k, c['en_short'])
    return m


def classify(s):
    if not any(ord(c) > 0x7F for c in s):
        return None
    m = SPK.match(s)
    if m and m.group(4) in ('」', '）', ''):
        return dict(kind='thought' if m.group(2) == '（' else 'dialogue', speaker_jp=m.group(1),
                    body_jp=m.group(3))
    return dict(kind='plain', speaker_jp='', body_jp=s)


def main(map_add, out, *scenes):
    # --exclude <file.json>: skip lines already present in that file (e.g. shared lines done earlier)
    scenes, skip = list(scenes), set()
    while '--exclude' in scenes:
        i = scenes.index('--exclude')
        skip |= {r['jp'] for r in json.load(open(scenes[i + 1], encoding='utf-8'))['rows']}
        del scenes[i:i + 2]
    B = blocks(map_add)
    spk = speakers()
    rows, seen = [], {}
    for sc in scenes:
        for i, s in enumerate(B[sc]):
            c = classify(s)
            if not c or s in skip:
                continue
            if s in seen:
                seen[s]['uses'].append(f'{sc}:{i}')
                continue
            r = dict(id=len(rows), jp=s, uses=[f'{sc}:{i}'], **c)
            r['speaker_en'] = spk.get(c['speaker_jp']) if c['speaker_jp'] else ''
            r['en'] = ''
            rows.append(r)
            seen[s] = r
    json.dump({'scenes': scenes, 'rows': rows}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    miss = sorted({r['speaker_jp'] for r in rows if r['speaker_jp'] and not r['speaker_en']})
    print(len(rows), 'rows;', sum(r['kind'] == 'plain' for r in rows), 'plain; speakers without glossary name:', miss)


if __name__ == '__main__':
    main(*sys.argv[1:])
