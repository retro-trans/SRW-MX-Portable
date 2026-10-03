"""Extract the game database (names + library) from STATIC2_ADD.BIN.

STATIC2_ADD.BIN holds tagged sections ('Vers', 'Fixh', 'Unit', 'Weap', 'Pilt', ...):
  +0 tag(4)  +4 u32 size (incl. 12-byte header)  +8 u32 count  then data.
Sections follow each other, 4-byte aligned, starting at 0x17EF00.

  Strg  string table: count x u32 offsets (relative to section start), SJIS strings
  Sent  sentence-row table, same layout. One string = one row of a library/help box
  Xunt  robot library index:     count x u32 offsets -> {u16 n, u16 sent_row[n]}
  XPlt  character library index: same layout
  XSpr/XSkl/Xabl/XPrt/XHlp  spirit/skill/ability/part/help description indexes
  Unit  512 records x 124 bytes: u16 name(Strg) @0, u16 reading(Strg) @2, u8 series @10,
                                 u16 weapon ids @32 (16 slots, 0xFFFF-terminated)
  Pilt  512 records x 184 bytes: u16 full name @0, u16 short name @2, u8 series @4,
                                 u16 reading @16
  Weap  1024 records x 48 bytes: u16 name(Strg) @0
Unit u16 @84 = Xunt library entry; Pilt u16 @166 = XPlt library entry (0xFFFF = none).
Several records (e.g. enemy copies) can point to the same entry.

usage: python static2_extract.py STATIC2_ADD.BIN BOOT.BIN <outdir>
"""
import json, os, struct, sys

SERIES_TABLE_OFF = 0x28FDB8   # BOOT.BIN: series titles, 22 NUL-terminated strings (4-aligned)


def sections(d, start=0x17EF00):
    out, o = {}, start
    while o + 12 <= len(d):
        tag = d[o:o + 4]
        if not all(0x20 <= c < 0x7F for c in tag):
            break
        size, count = struct.unpack_from('<2I', d, o + 4)
        out[tag.decode().strip()] = (o, size, count)
        o = (o + size + 3) & ~3
    return out


def strtable(d, o, n):
    offs = struct.unpack_from(f'<{n}I', d, o + 12)
    return [d[o + p:d.index(b'\0', o + p)].decode('cp932') for p in offs]


def index(d, o, n):
    out = []
    for p in struct.unpack_from(f'<{n}I', d, o + 12):
        c = struct.unpack_from('<H', d, o + p)[0]
        out.append(list(struct.unpack_from(f'<{c}H', d, o + p + 2)))
    return out


def series_names(boot):
    names, o = [], SERIES_TABLE_OFF
    while len(names) < 22:
        z = boot.index(b'\0', o)
        names.append(boot[o:z].decode('cp932'))
        o = (z + 4) & ~3
    return names


def is_dummy(rows):
    return all(r.startswith('☆ダミー') or r.startswith('ＤＵＭＭＹ') or not r.strip() for r in rows)


def main(static2, boot, outdir):
    d = open(static2, 'rb').read()
    series = series_names(open(boot, 'rb').read())
    sec = sections(d)
    strg = strtable(d, sec['Strg'][0], sec['Strg'][2])
    sent = strtable(d, sec['Sent'][0], sec['Sent'][2])
    S = lambda i: strg[i] if i < len(strg) else None

    uo, _, un = sec['Unit']
    units = []
    for i in range(un):
        r = d[uo + 12 + i * 124: uo + 12 + (i + 1) * 124]
        name, reading = struct.unpack_from('<2H', r, 0)
        weap = []
        for w in struct.unpack_from('<16H', r, 32):   # weapon ids, 0xFFFF-terminated
            if w == 0xFFFF:
                break
            weap.append(w)
        units.append({'id': i, 'name_idx': name, 'name': S(name), 'reading_idx': reading,
                      'reading': S(reading), 'series_id': r[10],
                      'series': series[r[10]] if r[10] < len(series) else None,
                      'weapons': weap, 'library': struct.unpack_from('<H', r, 84)[0]})

    po, _, pn = sec['Pilt']
    pilots = []
    for i in range(pn):
        r = d[po + 12 + i * 184: po + 12 + (i + 1) * 184]
        full, short = struct.unpack_from('<2H', r, 0)
        reading = struct.unpack_from('<H', r, 16)[0]
        pilots.append({'id': i, 'full_idx': full, 'full': S(full), 'short_idx': short,
                       'short': S(short), 'reading_idx': reading, 'reading': S(reading),
                       'series_id': r[4], 'series': series[r[4]] if r[4] < len(series) else None,
                       'library': struct.unpack_from('<H', r, 166)[0]})

    wo, _, wn = sec['Weap']
    weapons = []
    for i in range(wn):
        n = struct.unpack_from('<H', d, wo + 12 + i * 48)[0]
        weapons.append({'id': i, 'name_idx': n, 'name': S(n)})

    so, ssize, sn = sec['Sprt']             # spirit commands: n x 16-byte records, SJIS name @0
    rs = (ssize - 12) // sn
    spirits = []
    for i in range(sn):
        r = d[so + 12 + i * rs: so + 12 + (i + 1) * rs]
        spirits.append(r[:r.index(b'\0')].decode('cp932', 'replace'))

    def library(tag, owners, title):
        # owner record -> library entry via its 'library' field (several records may share one)
        by_entry = {}
        for rec in owners:
            by_entry.setdefault(rec['library'], []).append(rec)
        o, _, n = sec[tag]
        out = []
        for i, rows in enumerate(index(d, o, n)):
            text = [sent[r] for r in rows]
            e = {'entry': i, 'rows': rows, 'jp_rows': text, 'dummy': is_dummy(text),
                 'owners': [rec['id'] for rec in by_entry.get(i, [])]}
            if by_entry.get(i):
                e.update(title(by_entry[i][0]))
            out.append(e)
        return out

    lib_units = library('Xunt', units, lambda u: {'name': u['name'], 'reading': u['reading'],
                                                  'series': u['series']})
    lib_pilots = library('XPlt', pilots, lambda p: {'name': p['full'], 'short': p['short'],
                                                    'reading': p['reading'], 'series': p['series']})

    os.makedirs(outdir, exist_ok=True)
    def dump(name, obj):
        with open(os.path.join(outdir, name), 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    dump('static2_strg.json', strg)
    dump('static2_sent.json', sent)
    dump('series.json', series)
    dump('units.json', units)
    dump('pilots.json', pilots)
    dump('weapons.json', weapons)
    dump('spirits.json', spirits)
    dump('library_units.json', lib_units)
    dump('library_pilots.json', lib_pilots)
    print(f"Strg {len(strg)}  Sent {len(sent)}  units {len(units)}  pilots {len(pilots)}  "
          f"weapons {len(weapons)}")
    print(f"library units {len(lib_units)} ({sum(not e['dummy'] for e in lib_units)} real), "
          f"pilots {len(lib_pilots)} ({sum(not e['dummy'] for e in lib_pilots)} real)")


if __name__ == '__main__':
    main(*sys.argv[1:4])
