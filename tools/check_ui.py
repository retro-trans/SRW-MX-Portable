"""Check work/translation/en/ui/boot_ui.json against the BOOT.BIN UI strings.

usage: python check_ui.py [--all]
Needs work/source/text_inventory/boot_strings.json (tools/text_inventory.py). Reports strings without
English, unused keys, format codes that differ (%s/%d), characters the font cannot draw, and English
wider than the widest Japanese string of its list (strings stored within 0x20 bytes of each other are
treated as one list; --strict compares each string with its own Japanese, 16 px per full-width
character). A wider string is not always wrong (menus often have spare room), but every
one needs a look in game. --all prints every row.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KEEP_JP = set('□△○×＜＞　＋')          # Japanese glyphs that stay in English strings
GROUP_GAP = 0x20                       # strings closer than this are treated as one list


def jp_px(t):
    return sum(16 if ord(c) > 0x7F else 8 for c in t if c != '\n')


def resolve(tr, x):
    o = tr['overrides'].get(f"{x['va']:06X}")
    if o:
        assert o['jp'] == x['text'], f"override {x['va']:06X} is for {o['jp']!r}, found {x['text']!r}"
        return o['en'], 'override'
    if x['text'] in tr['defaults']:
        return tr['defaults'][x['text']], 'default'
    return KeyError, 'missing'


def main(*args):
    tr = json.load(open(os.path.join(ROOT, 'work/translation/en/ui/boot_ui.json'), encoding='utf-8'))
    bs = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/boot_strings.json'), encoding='utf-8'))
    ui = [x for x in bs if x['category'] == 'ui']
    allowed = set(textfit.ASCII) | KEEP_JP | {'"'}
    missing, fmt, chars, wide, rows = [], [], [], [], 0
    used = set()
    # Strings stored next to each other usually belong to one list or window, whose column is as wide
    # as its widest Japanese entry. --strict compares each string with its own Japanese instead.
    group_px, group = {}, []
    for x in ui + [None]:
        if group and (x is None or x['va'] - group[-1]['va'] > GROUP_GAP or '--strict' in args):
            m = max(jp_px(g['text']) for g in group)
            for g in group:
                group_px[g['va']] = jp_px(g['text']) if '--strict' in args else m
            group = []
        if x is not None:
            group.append(x)
    for x in ui:
        en, how = resolve(tr, x)
        if how == 'default':
            used.add(x['text'])
        if en is KeyError:
            missing.append(x)
            continue
        if en is None:
            continue
        rows += 1
        if re.findall(r'%\w', x['text']) != re.findall(r'%\w', en):
            fmt.append((x, en))
        bad = set(en) - allowed
        if bad:
            chars.append((x, en, ''.join(sorted(bad))))
        w, j = textfit.px(en), group_px[x['va']]
        if w > j:
            wide.append((x, en, w, j))
        if '--all' in args:
            print(f"{x['va']:06X} {j:4d} {w:4d}  {x['text']!r} -> {en!r}")
    unused = sorted(set(tr['defaults']) - used - {x['text'] for x in ui})
    print(f'UI strings: {len(ui)}; translated (not kept): {rows}; missing: {len(missing)}')
    for x in missing:
        print(f"  MISSING {x['va']:06X} {x['text']!r}")
    print(f'unused default keys: {unused}')
    print(f'format code mismatches: {len(fmt)}')
    for x, en in fmt:
        print(f"  FMT {x['va']:06X} {x['text']!r} -> {en!r}")
    print(f'unsupported characters: {len(chars)}')
    for x, en, b in chars:
        print(f"  CHAR {x['va']:06X} {en!r}: {b!r}")
    print(f'wider than the Japanese: {len(wide)}')
    for x, en, w, j in sorted(wide, key=lambda r: r[2] - r[3], reverse=True):
        print(f"  WIDE {x['va']:06X} {w:4d}>{j:4d} (+{w - j:3d})  {x['text']} -> {en}")


if __name__ == '__main__':
    main(*sys.argv[1:])
