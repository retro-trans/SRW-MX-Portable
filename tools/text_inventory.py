"""Inventory of all non-dialogue Japanese text in the ISO (the scenario script is handled elsewhere).

usage: python text_inventory.py "<Super Robot Taisen MX Portable (Japan).iso>" [out dir]
Writes JSON files to work/source/text_inventory/ (git-ignored: they contain Japanese text) and prints
a summary. See docs/text_inventory.md for what each file means.

  boot_strings.json      BOOT.BIN strings reached through a relocation (code HI16/LO16 pair or a
                         32-bit data pointer), with category, byte length and room before the next
                         string. Every one can be moved to new space by rewriting its relocations.
  boot_unreferenced.json BOOT.BIN Japanese strings that no relocation points at (reached through
                         base + offset tables, or unused).
  static2_names.json     STATIC2_ADD.BIN `Strg` name table (1839) with owner (unit, weapon, pilot,
                         reading, skill, ability, part, BGM, voice actor, unit size/weight) and the
                         glossary English when the glossary has it.
  static2_spirits.json   `Sprt` spirit command names (inline, 12-byte field).
  static2_rows.json      `Sent` description rows that are not library rows: spirit commands, skills,
                         abilities, parts and help (XSpr/XSkl/Xabl/XPrt/XHlp). Library rows (0-4255)
                         are already translated in work/translation/en/library.json.
  static2_scenario.json  untagged block at 0x1FCD80: chapter names, map location names, stage titles
                         (two copies each) and stage summaries.
  map_tiles.json         MAP_ADD.BIN `MPTI` map tile names (probably internal, see the doc).
  textures.json          graphics with Japanese text (TX48 index per file, reviewed by eye).
"""
import io, json, os, re, struct, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pycdlib
from static2_extract import sections, strtable, index

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BOOT_OFF = 0x60                       # file offset = vaddr + 0x60
TEXT_START = 0x276000                 # .data below this holds no text (only binary hits)
FONT_TABLE = (0x28D430, 0x28F1B0)     # vaddr range of the glyph-order table (not text to translate)
EPILOGUE = (0x285DEC, 0x286730)
SAVE_MSGS = [(0x282B50, 0x282D60), (0x299200, 0x299800)]
LOCATIONS = (0x28C5C0, 0x28C7D0)
DEBUG_RANGES = [(0x276180, 0x2764D0), (0x27EAF8, 0x27EF60), (0x27FA18, 0x27FAB8)]
DEBUG_PAT = re.compile(r'::|m_p|%x|byte|!!!|Can\'t|exit_cb|disc0|= %|CMap|CWnd|Misc|Flag')
SCENARIO = 0x1FCD80                   # STATIC2: u32 x5 offsets -> chapter table, chapter names,
                                      # locations, stage titles, summary pointer table
MPTI = 0x2AA8000                      # MAP_ADD: 'MPTI', u32 count, 52-byte records, name at +8
# TX48 indexes (order of appearance in the file) whose image contains Japanese text
TEXTURES = {
    'WND.BIN': {0: 'header インターミッション', 39: 'header 出撃準備',
                50: '攻', 51: '反', 52: '援', 53: '同', 54: '戦', 55: '支', 84: '避', 85: '防',
                90: '攻 (small)', 91: '反 (small)', 92: '援 (small)', 93: '同 (small)', 94: '戦 (small)',
                95: '支 (small)', 97: '避 (small)', 98: '防 (small)', 114: '援 (small)', 115: '支 (small)',
                57: '能', 58: '武', 59: '動', 60: '装', 61: '行', 63: '移'},
    'STATIC2_ADD.BIN': dict([(i, 'battle/status label') for i in range(15, 65)] +
                            [(66, '重力波ビーム'), (67, '出入口'), (68, 'EWAC(強)'), (69, 'EWAC(弱)'),
                             (76, 'シールド防御'), (77, '援護攻撃'), (78, '援護防御'), (79, '支援攻撃')]),
    'MAP_ADD.BIN': dict([(i, 'battle/status label (copy of STATIC2 15-64)') for i in range(23, 73)] +
                        [(74, '重力波ビーム'), (75, '出入口'), (76, 'EWAC(強)'), (77, 'EWAC(弱)'),
                         (84, 'シールド防御'), (85, '援護攻撃'), (86, '援護防御'), (87, '支援攻撃')]),
    'OPWND.BIN': {44: 'title logo スーパーロボット大戦MX ポータブル'},
    '../ICON0.PNG': {0: 'XMB icon with the Japanese logo'},
    'SAVE.BIN': {0: 'save icon PNG (Japanese logo)', 1: 'save icon PNG (Japanese logo)'},
}


def jp_text(t):
    """True for real text: printable, no half-width katakana, at least one full-width character."""
    if any('｡' <= c <= 'ﾟ' for c in t):
        return False
    if not all(c == '\n' or 0x20 <= ord(c) < 0x7F or ord(c) > 0x2000 for c in t):
        return False
    if any('' <= c <= '' for c in t):           # user-defined SJIS area: binary data
        return False
    real = [c for c in t if ord(c) > 0x7F and c != '　']
    if not real:
        return False
    return not (len(real) == 1 and re.search(r'[()\\`$,<>|{}!"\']', t))   # 1 kanji + stray ASCII


def cstr(d, o):
    z = d.index(b'\0', o)
    try:
        return d[o:z].decode('cp932'), z - o
    except UnicodeDecodeError:
        return None, z - o


def elf_sections(d):
    shoff, = struct.unpack_from('<I', d, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from('<3H', d, 0x2E)
    sh = [struct.unpack_from('<10I', d, shoff + i * shentsize) for i in range(shnum)]
    st = sh[shstrndx][4]
    return {d[st + s[0]:d.index(b'\0', st + s[0])].decode(): s for s in sh}


def boot_strings(d):
    sec = elf_sections(d)
    lo, hi = sec['.data'][3], sec['.data'][3] + sec['.data'][5]
    word = lambda va: struct.unpack_from('<I', d, va + BOOT_OFF)[0]
    rels = lambda n: [struct.unpack_from('<2I', d, sec[n][4] + k) for k in range(0, sec[n][5], 8)]
    refs = defaultdict(list)
    for off, info in rels('.rel.data'):
        if info & 0xFF == 2 and lo <= word(off) < hi:
            refs[word(off)].append('data')
    hi16 = None
    for off, info in rels('.rel.text'):
        typ, ins = info & 0xFF, word(off)
        if typ == 5:
            hi16 = ins & 0xFFFF
        elif typ == 6 and hi16 is not None:
            low = ins & 0xFFFF
            t = (hi16 << 16) + (low - 0x10000 if low & 0x8000 else low)
            if lo <= t < hi:
                refs[t].append('code')
    out = []
    for va in sorted(refs):
        o = va + BOOT_OFF
        t, n = cstr(d, o)
        if not t or not jp_text(t) or va < TEXT_START or (d[o - 1] != 0 and len(t) <= 3):
            continue
        room = n
        while o + room < len(d) and d[o + room] == 0:
            room += 1
        out.append({'va': va, 'file_off': o, 'text': t, 'bytes': n, 'room': room - 1,
                    'refs': len(refs[va]), 'ref_kinds': sorted(set(refs[va])),
                    'mid_string': d[o - 1] != 0, 'category': boot_category(va, t)})
    return out, refs


def boot_category(va, t):
    inr = lambda r: r[0] <= va < r[1]
    if inr(FONT_TABLE):
        return 'font_table'
    if t.startswith(('あいうえお', 'アイウエオ')):
        return 'name_entry_charset'
    if any(inr(r) for r in DEBUG_RANGES) or DEBUG_PAT.search(t):
        return 'debug'
    if inr(EPILOGUE):
        return 'narration'
    if any(inr(r) for r in SAVE_MSGS) or 'メモリースティック' in t:
        return 'save_system'
    if inr(LOCATIONS):
        return 'intermission_locations'
    return 'ui'


def static2(d, gloss):
    S = sections(d)
    strg = strtable(d, S['Strg'][0], S['Strg'][2])
    owner = defaultdict(set)

    def add(tag, field, label):
        o, size, cnt = S[tag]
        rec = (size - 12) // cnt
        for i in range(cnt):
            v = struct.unpack_from('<H', d, o + 12 + i * rec + field)[0]
            if v < len(strg):
                owner[v].add(label)
    for args in [('Unit', 0, 'unit'), ('Unit', 2, 'unit_reading'), ('Weap', 0, 'weapon'),
                 ('Pilt', 0, 'pilot_full'), ('Pilt', 2, 'pilot_short'), ('Pilt', 16, 'pilot_reading'),
                 ('Pilt', 164, 'voice_actor'), ('Skil', 0, 'skill'), ('Abil', 0, 'ability'),
                 ('Part', 0, 'part'), ('Bgm', 0, 'bgm')]:
        add(*args)
    names = []
    for i, t in enumerate(strg):
        own = sorted(owner.get(i, ()))
        if not own:
            own = ['unit_size_weight'] if re.fullmatch(r'[０-９．]+[ｍｔ]', t) else ['placeholder'] \
                if set(t) <= set('－') else ['unreferenced']
        names.append({'idx': i, 'text': t, 'owners': own, 'bytes': len(t.encode('cp932')),
                      'en_glossary': gloss.get(t)})
    spirits = []
    o, size, cnt = S['Sprt']
    for i in range(cnt):
        t, _ = cstr(d, o + 12 + i * 16)
        spirits.append({'idx': i, 'text': t, 'field_bytes': 12, 'en_glossary': gloss.get(t)})
    sent = strtable(d, S['Sent'][0], S['Sent'][2])
    rows = []
    for tag in ['XSpr', 'XSkl', 'Xabl', 'XPrt', 'XHlp']:
        for e, rr in enumerate(index(d, S[tag][0], S[tag][2])):
            for k, r in enumerate(rr):
                rows.append({'index': tag, 'entry': e, 'line': k, 'row': r, 'text': sent[r]})
    return names, spirits, rows, S


def scenario(d):
    offs = [SCENARIO + o for o in struct.unpack_from('<5I', d, SCENARIO)]
    found = lambda a, b: [(a + m.start(), m.group()[:-1].decode('cp932'))
                          for m in re.finditer(rb'(?:[\x81-\x9f\xe0-\xfc][\x40-\xfc]|[\x20-\x7e])+\x00', d[a:b])
                          if jp_text(m.group()[:-1].decode('cp932', 'replace'))]
    chapters = [{'off': o, 'text': t, 'field_bytes': 0x58} for o, t in found(offs[1], offs[2])]
    locations = [{'off': o, 'text': t} for o, t in found(offs[2], offs[3])]
    titles = [{'off': o, 'text': t, 'field_bytes': 0x38} for o, t in found(offs[3], offs[4])]
    n = struct.unpack_from('<I', d, offs[4])[0]
    ptrs = struct.unpack_from(f'<{n}I', d, offs[4] + 4)
    summaries = [{'idx': i, 'off': offs[4] + p, 'text': cstr(d, offs[4] + p)[0]} for i, p in enumerate(ptrs)]
    return {'base': SCENARIO, 'chapters': chapters, 'locations': locations, 'stage_titles': titles,
            'summaries': summaries}


def map_tiles(m):
    assert m[MPTI:MPTI + 4] == b'MPTI'
    n = struct.unpack_from('<I', m, MPTI + 4)[0]
    out = []
    for i in range(n):
        o = MPTI + 8 + i * 52
        t, _ = cstr(m, o)
        if t and jp_text(t):
            out.append({'idx': i, 'off': o, 'text': t})
    return n, out


def glossary_map():
    g = json.load(open(os.path.join(ROOT, 'work', 'glossary', 'glossary.json'), encoding='utf-8'))
    out = {}
    for x in g['characters']:
        for k, e in (('jp_full', 'en_full'), ('jp_short', 'en_short')):
            if x.get(k) and x.get(e):
                out.setdefault(x[k], x[e])
    for sec in ('series', 'units', 'weapons', 'terms'):
        for x in g[sec]:
            if x.get('jp') and x.get('en'):
                out.setdefault(x['jp'], x['en'])
    supp = os.path.join(ROOT, 'work', 'glossary', 'campaign_terms.json')   # later sourced additions
    if os.path.exists(supp):
        for x in json.load(open(supp, encoding='utf-8')).get('terms', []):
            if x.get('jp') and x.get('en'):
                out.setdefault(x['jp'], x['en'])
    return out


def main(iso_path, out=None):
    out = out or os.path.join(ROOT, 'work', 'source', 'text_inventory')
    os.makedirs(out, exist_ok=True)
    iso = pycdlib.PyCdlib()
    iso.open(iso_path)

    def rd(p):
        f = io.BytesIO()
        iso.get_file_from_iso_fp(f, iso_path=p)
        return f.getvalue()
    save = lambda name, obj: json.dump(obj, open(os.path.join(out, name), 'w', encoding='utf-8'),
                                       ensure_ascii=False, indent=1)
    gloss = glossary_map()

    boot = rd('/PSP_GAME/SYSDIR/BOOT.BIN')
    bs, refs = boot_strings(boot)
    save('boot_strings.json', bs)
    import sjis_scan
    referenced = {x['file_off'] for x in bs}
    unref = [{'file_off': o, 'va': o - BOOT_OFF, 'text': t} for o, t in sjis_scan.scan(boot)
             if o >= 0x26358C and o not in referenced and jp_text(t)
             and not FONT_TABLE[0] <= o - BOOT_OFF < FONT_TABLE[1]]
    save('boot_unreferenced.json', unref)

    st = rd('/PSP_GAME/USRDIR/STATIC2_ADD.BIN')
    names, spirits, rows, S = static2(st, gloss)
    save('static2_names.json', names)
    save('static2_spirits.json', spirits)
    save('static2_rows.json', rows)
    sc = scenario(st)
    save('static2_scenario.json', sc)

    m = rd('/PSP_GAME/USRDIR/MAP_ADD.BIN')
    ntiles, tiles = map_tiles(m)
    save('map_tiles.json', tiles)
    save('textures.json', TEXTURES)

    # summary
    print('BOOT.BIN referenced strings by category (count / unique / Japanese chars of unique):')
    by = defaultdict(list)
    for x in bs:
        by[x['category']].append(x['text'])
    for c, ts in sorted(by.items(), key=lambda kv: -len(kv[1])):
        u = set(ts)
        print(f'  {c:24s} {len(ts):5d} / {len(u):5d} / {sum(len(t) for t in u):6d}')
    print(f'  unreferenced Japanese strings: {len(unref)}')
    oc = Counter(o for x in names for o in x['owners'])
    print('STATIC2 Strg names by owner:', dict(oc))
    trans = [x for x in names if not set(x['owners']) & {'unit_reading', 'pilot_reading', 'unit_size_weight',
                                                          'placeholder', 'unreferenced'}]
    print(f'  display names: {len(trans)}, with glossary English: {sum(1 for x in trans if x["en_glossary"])}')
    print('STATIC2 Sprt spirit names:', len(spirits), 'with glossary English:', sum(1 for x in spirits if x['en_glossary']))
    rc = Counter(x['index'] for x in rows)
    print('STATIC2 description rows:', dict(rc), 'unique', len({x['text'] for x in rows}))
    print('STATIC2 scenario block: chapters', len(sc['chapters']), 'locations', len(sc['locations']),
          'stage titles', len(sc['stage_titles']), 'summaries', len(sc['summaries']))
    print('MAP_ADD MPTI tile names:', len(tiles), 'of', ntiles, 'records; unique', len({x['text'] for x in tiles}))
    print('textures with Japanese:', {k: len(v) for k, v in TEXTURES.items()})
    print('written to', os.path.abspath(out))


if __name__ == '__main__':
    main(*sys.argv[1:3])
