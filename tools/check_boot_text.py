"""Check work/translation/en/ui/boot_text.json (BOOT.BIN narration, intermission locations, save text).

usage: python check_boot_text.py [--show]
Narration paragraphs are wrapped to the widest Japanese narration line (416 px) and must fit the
line table (opening 32 lines, ending 24). Locations and in-game save messages are checked for
drawable characters and format codes; raw (system) strings must be plain ASCII. Locations are one list: each must fit the widest
Japanese entry (208 px).
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LINE_PX = 416
ALLOWED = set(textfit.ASCII) | {'"', '㌣'}


def jp_px(t):
    return sum(16 if ord(c) > 0x7F else 8 for c in t if c != '\n')


def main(*args):
    tr = json.load(open(os.path.join(ROOT, 'work/translation/en/ui/boot_text.json'), encoding='utf-8'))
    bs = {f"{x['va']:06X}": x for x in json.load(open(os.path.join(
        ROOT, 'work/source/text_inventory/boot_strings.json'), encoding='utf-8'))}
    problems = []
    # the location list is one window: its width is set by the widest Japanese entry
    loc_px = max(jp_px(x['text']) for x in bs.values() if x['category'] == 'intermission_locations')
    for name, paras in tr['narration'].items():
        start, slots = tr['narration_tables'][name]
        lines = []
        for p in paras:
            ls, _ = textfit.wrap('', p, '', line_px=LINE_PX, indent='')
            lines += ls
        for p in paras:
            if set(p) - ALLOWED:
                problems.append(f'{name}: bad characters {"".join(sorted(set(p) - ALLOWED))!r}')
        print(f'{name}: {len(lines)} of {slots} lines used')
        if len(lines) > slots:
            problems.append(f'{name}: {len(lines)} lines, table has {slots}')
        if '--show' in args:
            for l in lines:
                print(f'  {textfit.px(l):3d} | {l}')
    for group in ('locations', 'save'):
        for va, v in tr[group].items():
            en, raw = (v, False) if isinstance(v, str) else (v['en'], v.get('raw', False))
            x = bs.get(va)
            if x is None:
                problems.append(f'{group} {va}: no Japanese string at this address')
                continue
            if re.findall(r'%\d*\w', x['text']) != re.findall(r'%\d*\w', en):
                problems.append(f'{group} {va}: format codes differ: {x["text"]!r} -> {en!r}')
            if raw:
                if not all(32 <= ord(c) < 127 or c == '\n' for c in en):
                    problems.append(f'{group} {va}: raw string is not plain ASCII: {en!r}')
                continue
            if set(en) - ALLOWED:
                problems.append(f'{group} {va}: bad characters {"".join(sorted(set(en) - ALLOWED))!r}')
            if group == 'locations' and textfit.px(en) > loc_px:
                problems.append(f'{group} {va}: {en!r} {textfit.px(en)} px > widest Japanese entry {loc_px} px')
    cats = {'intermission_locations': 'locations', 'save_system': 'save'}
    for va, x in bs.items():
        g = cats.get(x['category'])
        if g and va not in tr[g]:
            problems.append(f'{g} {va}: missing ({x["text"]!r})')
    print(f'problems: {len(problems)}')
    for p in problems:
        print(' ', p)


if __name__ == '__main__':
    main(*sys.argv[1:])
