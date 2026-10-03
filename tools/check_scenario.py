"""Check work/translation/en/static2/scenario.json (chapter names, locations, stage titles, summaries).

usage: python check_scenario.py [--show]
Needs work/source/text_inventory/static2_scenario.json (tools/text_inventory.py).
Limits: stage titles live in 0x38-byte inline fields and location names in 0x40-byte fields, chapter
names are treated the same (English is 2 bytes per letter, plus the NUL). Titles must also fit the
widest Japanese title (400 px) plus a little room, 448 px. Summaries are wrapped to the summary box:
448 px per line, at most 4 lines (the most any Japanese summary uses).
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FIELD = {'chapters': 0x40, 'locations': 0x40, 'stage_titles': 0x38}
LINE_PX, LINES = 448, 4
ALLOWED = set(textfit.ASCII) | {'"'}


def main(*args):
    tr = json.load(open(os.path.join(ROOT, 'work/translation/en/static2/scenario.json'), encoding='utf-8'))
    sc = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/static2_scenario.json'), encoding='utf-8'))
    problems = []

    def check_field(kind, jp, en):
        if en is None:
            problems.append(f'{kind}: no English for {jp!r}')
            return
        n = len(textfit.encode(en)) + 1
        if n > FIELD[kind]:
            problems.append(f'{kind}: {en!r} needs {n} bytes, field is {FIELD[kind]}')
        if set(en) - ALLOWED:
            problems.append(f'{kind}: {en!r} has {"".join(sorted(set(en) - ALLOWED))!r}')
        if kind == 'stage_titles' and textfit.px(en) > LINE_PX:
            problems.append(f'{kind}: {en!r} is {textfit.px(en)} px')

    for i, x in enumerate(sc['chapters']):
        check_field('chapters', x['text'], tr['chapters'].get(str(i)))
    for x in sc['locations']:
        check_field('locations', x['text'], tr['locations'].get(x['text']))
    for x in sc['stage_titles']:
        check_field('stage_titles', x['text'], (tr['stage_titles'].get(x['text']) or {}).get('en'))
    for x in sc['summaries']:
        k = str(x['idx'])
        if k not in tr['summaries']:
            problems.append(f'summary {k}: missing')
            continue
        en = tr['summaries'][k]
        if en is None:
            continue
        lines, _ = textfit.wrap('', en, '', line_px=LINE_PX, indent='')
        if len(lines) > LINES or any(textfit.px(l) > LINE_PX for l in lines):
            problems.append(f'summary {k}: {len(lines)} lines: ' + ' | '.join(lines))
        if set(en) - ALLOWED:
            problems.append(f'summary {k}: bad characters {"".join(sorted(set(en) - ALLOWED))!r}')
        if '--show' in args:
            print(k, ' | '.join(lines))
    print(f"chapters {len(sc['chapters'])}, locations {len(sc['locations'])}, stage titles "
          f"{len(sc['stage_titles'])}, summaries {len(sc['summaries'])}; problems: {len(problems)}")
    for p in problems:
        print(' ', p)


if __name__ == '__main__':
    main(*sys.argv[1:])
