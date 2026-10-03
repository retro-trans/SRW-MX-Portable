"""Split glossary + library work into per-agent batches grouped by series.

usage: python make_batches.py <work/source dir> <out dir>
Reads the JSON written by static2_extract.py.
"""
import json, os, sys

GROUPS = {
    'A': ['マシンロボ　クロノスの大逆襲', '機甲戦記ドラグナー', '勇者ライディーン', '闘将ダイモス'],
    'B': ['ＧＥＡＲ戦士電童', '機動戦艦ナデシコ', '劇場版　機動戦艦ナデシコ', '冥王計画ゼオライマー'],
    'C': ['新世紀エヴァンゲリオン', 'ＴＨＥ　ＥＮＤ　ＯＦ　ＥＶＡＮＧＥＬＩＯＮ', 'ラーゼフォン',
          'バンプレストオリジナル', '機動戦士Ζガンダム', '機動戦士ガンダムΖΖ', '機動戦士ガンダム　逆襲のシャア'],
    'D': ['機動武闘伝Ｇガンダム', 'マジンガーＺ', 'グレートマジンガー', 'ゲッターロボ', 'ゲッターロボＧ',
          'ＵＦＯロボ　グレンダイザー', '劇場版マジンガーシリーズ'],
}
SYSTEM_GROUP = 'D'   # also gets spirit commands / skills / parts


def main(src, out):
    L = lambda f: json.load(open(os.path.join(src, f), encoding='utf-8'))
    lu, lp = L('library_units.json'), L('library_pilots.json')
    units, pilots, weapons, strg = L('units.json'), L('pilots.json'), L('weapons.json'), L('static2_strg.json')
    os.makedirs(out, exist_ok=True)
    for g, series in GROUPS.items():
        su = [u for u in units if u['series'] in series and u['name'] not in (None, '無し', 'ダミー')]
        wid = sorted({w for u in su for w in u['weapons']})
        b = {
            'group': g,
            'series': series,
            'unit_names': sorted({(u['name'], u['reading'], u['series']) for u in su}),
            'pilot_names': sorted({(p['full'], p['short'], p['reading'], p['series'])
                                   for p in pilots if p['series'] in series and p['full']}),
            'weapon_names': sorted({weapons[w]['name'] for w in wid if weapons[w]['name']}),
            'library_units': [{k: e[k] for k in ('entry', 'name', 'reading', 'series', 'jp_rows')}
                              for e in lu if not e['dummy'] and e.get('series') in series],
            'library_pilots': [{k: e[k] for k in ('entry', 'name', 'short', 'reading', 'series', 'jp_rows')}
                               for e in lp if not e['dummy'] and e.get('series') in series],
        }
        if g == SYSTEM_GROUP:
            # Strg 0..103: skills, abilities, parts names etc. (before the first unit name)
            b['system_terms'] = [s for s in strg[:104] if s not in ('無し',)]
            b['spirit_commands'] = [s for s in L('spirits.json') if s not in ('無し', '')]
        path = os.path.join(out, f'batch_{g}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(b, f, ensure_ascii=False, indent=1)
        chars = sum(len(''.join(e['jp_rows'])) for e in b['library_units'] + b['library_pilots'])
        print(g, len(b['library_units']), 'unit entries', len(b['library_pilots']), 'char entries',
              chars, 'chars', len(b['unit_names']), 'units', len(b['pilot_names']), 'pilots',
              len(b['weapon_names']), 'weapons')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
