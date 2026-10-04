"""Battle quotes (BATTLE2.BIN sub-file 5): export translator batches, fit-check English, merge results.

Format (see docs/battle_quotes.md):
- BATTLE2.BIN starts with a u32 table of sub-file offsets; sub-file 5 holds the quotes.
- STATIC2_ADD.BIN 0x17E1C0: u32[512], one per pilot id (same ids as work/source/pilots.json); the
  offset of that pilot's quote block inside sub-file 5, or 0xFFFFFFFF (no quotes). 372 pilots have one.
- A block starts on a 0x800 boundary: 8 bytes, then u16[10] section offsets relative to the block;
  the last one is where the NUL-terminated strings start. Section 7 = u16 offset of each string,
  section 8 = u32 text id of each string (the same line repeated in a block shares the id).
- Quotes are 「...」, '/' = new line, at most 2 lines. A few strings are the second half of a line
  (no opening 「) or end with full-width space padding.

usage:
  python battle_quotes.py export [lines_per_batch]   -> work/source/battle/quotes.json,
                                                       work/translation/en/battle/batch_NN.json
  python battle_quotes.py fit "English text" [--no-open] [--no-close]
  python battle_quotes.py check <batch_NN.en.json ...>
  python battle_quotes.py merge NN                    -> joins batch_NN.en.partK.json into batch_NN.en.json
  python battle_quotes.py status
  python battle_quotes.py verify <built.iso>        -> reads every quote back as the game would
"""
import glob
import io
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ISO = os.path.join(ROOT, 'Super Robot Taisen MX Portable (Japan).iso')
SRC = os.path.join(ROOT, 'work', 'source', 'battle')
OUT = os.path.join(ROOT, 'work', 'translation', 'en', 'battle')
PILOT_TABLE = 0x17E1C0
NPILOTS = 512
SUBFILE = 5
LINE_PX = 352          # same box width as dialogue: 22 Japanese cells of 16 px (longest JP line)
MAX_LINES = 2
OPEN, CLOSE, INDENT = '「', '」', '　'
UNNAMED = '無し'
UNNAMED_EN = '(original characters: Hugo Medio / Aqua Centrum and others; infer the speaker)'


def read_iso(path, size=None):
    import pycdlib
    iso = pycdlib.PyCdlib()
    iso.open(ISO)
    with iso.open_file_from_iso(iso_path=path) as f:
        data = f.read(size) if size else f.read()
    iso.close()
    return data


def subfile():
    cache = os.path.join(SRC, 'BATTLE2_quotes.bin')
    if os.path.exists(cache):
        return open(cache, 'rb').read()
    head = read_iso('/PSP_GAME/USRDIR/BATTLE2.BIN', 0x400000)
    offs = struct.unpack_from('<12I', head, 0)
    data = head[offs[SUBFILE]:offs[SUBFILE + 1]]
    os.makedirs(SRC, exist_ok=True)
    open(cache, 'wb').write(data)
    return data


def static2():
    p = os.path.join(ROOT, 'work', 'build', 'STATIC2_ADD.orig')
    return open(p, 'rb').read() if os.path.exists(p) else read_iso('/PSP_GAME/USRDIR/STATIC2_ADD.BIN')


def parse_block(s, p):
    offs = struct.unpack_from('<10H', s, p + 8)
    q = p + offs[-1]
    strs = []
    while s[q] != 0:
        e = s.index(b'\0', q)
        strs.append(s[q:e].decode('cp932'))
        q = e + 1
    ids = list(struct.unpack_from(f'<{len(strs)}I', s, p + offs[8])) if offs[8] != 0xFFFF else []
    return {'offset': p, 'sections': list(offs), 'end': q, 'strings': strs, 'text_ids': ids}


def split_quote(t):
    """raw string -> (body, open, close, pad). body keeps '/' line breaks without the indent."""
    pad = len(t) - len(t.rstrip(INDENT))
    t = t.rstrip(INDENT)
    o = t.startswith(OPEN)
    c = t.endswith(CLOSE)
    body = t[1 if o else 0: -1 if c else None]
    body = '/'.join(x[1:] if x.startswith(INDENT) else x for x in body.split('/'))
    return body, o, c, pad


def glossary():
    g = json.load(open(os.path.join(ROOT, 'work', 'glossary', 'glossary.json'), encoding='utf-8'))
    chars = {}
    for c in g['characters']:
        for k in ('jp_full', 'jp_short'):
            if c.get(k):
                chars.setdefault(c[k], c)
    terms = []
    for kind in ('characters', 'units', 'weapons', 'terms', 'series'):
        for e in g[kind]:
            pairs = [(e.get('jp_full'), e.get('en_full')), (e.get('jp_short'), e.get('en_short'))] \
                if kind == 'characters' else [(e.get('jp'), e.get('en'))]
            for jp, en in pairs:
                if jp and en and len(jp) >= 2:
                    terms.append((jp, en, kind))
    series = {e['jp']: e['en'] for e in g['series']}
    return chars, terms, series


def export(per_batch=420):
    s = subfile()
    st = static2()
    table = struct.unpack_from(f'<{NPILOTS}I', st, PILOT_TABLE)
    pilots = json.load(open(os.path.join(ROOT, 'work', 'source', 'pilots.json'), encoding='utf-8'))
    chars, terms, series_en = glossary()

    blocks = []
    for pid, off in enumerate(table):
        if off == 0xFFFFFFFF:
            continue
        b = parse_block(s, off)
        pl = dict(pilots[pid])
        if pl['full'] == UNNAMED:
            # slots 450-509: the original characters' sets (Hugo / Aqua and their partner lines,
            # one per unit and story variant). Several speakers share a block; series id is 0.
            pl.update(series='バンプレストオリジナル', series_id=21)
        c = chars.get(pl['full']) or chars.get(pl['short'])
        b.update(pilot=pid, speaker_jp=pl['full'], speaker_en=(c or {}).get('en_full', ''),
                 series_jp=pl.get('series', ''), series_en=series_en.get(pl.get('series', ''), ''),
                 series_id=pl['series_id'])
        if pl['full'] == UNNAMED:
            b['speaker_en'] = UNNAMED_EN
        blocks.append(b)
    json.dump(blocks, open(os.path.join(SRC, 'quotes.json'), 'w', encoding='utf-8'), ensure_ascii=False)

    # unique lines: key = raw string; owner = first pilot (table order) that says it
    uniq, order = {}, []
    for b in blocks:
        for i, t in enumerate(b['strings']):
            u = uniq.get(t)
            if u is None:
                body, o, c, pad = split_quote(t)
                u = uniq[t] = {'id': f'q{len(order):05d}', 'raw': t, 'jp': body, 'open': o, 'close': c,
                               'pad': pad, 'jp_lines': body.count('/') + 1, 'pilot': b['pilot'],
                               'speaker_jp': b['speaker_jp'], 'speaker_en': b['speaker_en'],
                               'series_en': b['series_en'], 'uses': 0, 'also': []}
                order.append(u)
            u['uses'] += 1
            if b['pilot'] != u['pilot'] and b['speaker_jp'] not in u['also']:
                u['also'].append(b['speaker_jp'])

    # batches: whole pilots in series order, split only pilots larger than a batch
    by_pilot = {}
    for u in order:
        by_pilot.setdefault(u['pilot'], []).append(u)
    pilot_series = {b['pilot']: (b['series_id'], b['pilot']) for b in blocks}
    batches, cur = [], []
    for pid in sorted(by_pilot, key=lambda p: pilot_series[p]):
        rows = by_pilot[pid]
        if cur and len(cur) + len(rows) > per_batch:
            batches.append(cur)
            cur = []
        while len(rows) > per_batch:
            batches.append(rows[:per_batch])
            rows = rows[per_batch:]
        cur += rows
    if cur:
        batches.append(cur)

    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, 'batch_*.json')):
        if not f.endswith('.en.json'):
            os.remove(f)
    for n, rows in enumerate(batches):
        text = ''.join(r['jp'] for r in rows)
        found = sorted({(jp, en, kind) for jp, en, kind in terms if jp in text}, key=lambda x: -len(x[0]))
        out = {'batch': n, 'speakers': sorted({r['speaker_en'] or r['speaker_jp'] for r in rows}),
               'glossary_hits': [{'jp': jp, 'en': en, 'kind': k} for jp, en, k in found],
               'rows': [{k: r[k] for k in ('id', 'jp', 'jp_lines', 'open', 'close', 'speaker_jp', 'speaker_en',
                                           'series_en', 'uses', 'also')} for r in rows]}
        json.dump(out, open(os.path.join(OUT, f'batch_{n:02d}.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    json.dump({u['id']: {k: u[k] for k in ('raw', 'open', 'close', 'pad', 'pilot')} for u in order},
              open(os.path.join(SRC, 'unique.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'pilots with quotes: {len(blocks)}; strings: {sum(len(b["strings"]) for b in blocks)}; '
          f'unique: {len(order)}; batches: {len(batches)} '
          f'(sizes {min(map(len, batches))}-{max(map(len, batches))}); '
          f'unnamed speakers: {sum(1 for b in blocks if not b["speaker_en"])}')


def fit(en, open_=True, close=True):
    """Wrap English into the battle box. Returns (lines, ok)."""
    lines, ok = textfit.wrap(OPEN if open_ else INDENT, en, CLOSE if close else '', line_px=LINE_PX)
    ok = ok and len(lines) <= MAX_LINES
    return lines, ok


BAD = re.compile(r"[^A-Za-z0-9 ,.:;?!~'\"()\[\]+\-=$%&*]")


def check(paths):
    meta = json.load(open(os.path.join(SRC, 'unique.json'), encoding='utf-8'))
    bad = total = 0
    for p in paths:
        data = json.load(open(p, encoding='utf-8'))
        for r in data['rows'] if isinstance(data, dict) else data:
            total += 1
            m = meta.get(r['id'])
            en = r.get('en', '')
            probs = []
            if not m:
                probs.append('unknown id')
            elif not en:
                probs.append('empty')
            else:
                if BAD.search(en):
                    probs.append('characters ' + ''.join(sorted(set(BAD.findall(en)))))
                lines, ok = fit(en, m['open'], m['close'])
                if not ok:
                    probs.append(f'{len(lines)} lines: ' + ' | '.join(f'{textfit.px(l)}px' for l in lines))
            if probs:
                bad += 1
                print(f"{os.path.basename(p)} {r['id']}: {'; '.join(probs)}")
    print(f'rows: {total}; problems: {bad}')
    return bad


def merge(n):
    n = int(n)
    src = json.load(open(os.path.join(OUT, f'batch_{n:02d}.json'), encoding='utf-8'))
    parts = sorted(glob.glob(os.path.join(OUT, f'batch_{n:02d}.en.part*.json')),
                   key=lambda f: int(re.search(r'part(\d+)', f).group(1)))
    got = {}
    for f in parts:
        for r in json.load(open(f, encoding='utf-8'))['rows']:
            got[r['id']] = {'id': r['id'], 'en': r.get('en', ''), 'notes': r.get('notes', ''),
                            'uncertain': r.get('uncertain', [])}
    want = [r['id'] for r in src['rows']]
    missing = [i for i in want if i not in got]
    extra = [i for i in got if i not in set(want)]
    if missing or extra:
        print(f'not merged: missing {len(missing)} {missing[:10]}; unknown ids {extra[:10]}')
        return 1
    out = os.path.join(OUT, f'batch_{n:02d}.en.json')
    json.dump({'batch': n, 'rows': [got[i] for i in want]}, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for f in parts:
        os.remove(f)
    print(f'merged {len(parts)} parts, {len(want)} rows -> {out}')
    return check([out])


def status():
    ins = sorted(glob.glob(os.path.join(OUT, 'batch_[0-9][0-9].json')))
    done = 0
    for f in ins:
        n = len(json.load(open(f, encoding='utf-8'))['rows'])
        o = f[:-5] + '.en.json'
        got = len(json.load(open(o, encoding='utf-8'))['rows']) if os.path.exists(o) else 0
        done += got
        print(f'{os.path.basename(f)}: {got}/{n}')
    print('translated rows:', done)


# ------------------------------------------------------------------------------------------ insertion
# The game loads one pilot's block with a fixed 0x4800-byte read (0x495F4):
#   sector = BATTLE2 start + (BATTLE2 header[5] >> 11) + (pilot table entry >> 11)
# so blocks stay 0x800-aligned and at most 0x4800 bytes. Everything before the strings (records,
# flags, text ids) is kept; section 7 (u16 offset of each string from the string start) is rewritten.
# English is longer than the Japanese, so the rebuilt sub-file goes to the end of BATTLE2.BIN and
# header[5] points there; the old copy stays in place, unused.
BLOCK_MAX = 0x4800
OVERFLOW_BIT = 0x8000
SECTION_STR_OFFS = 7


def encode_quote(en, m):
    """English row -> game bytes: wrapped lines joined by ASCII '/', like the Japanese."""
    lines, ok = fit(en, m['open'], m['close'])
    b = b'/'.join(textfit.encode(l) for l in lines)
    return b + INDENT.encode('cp932') * m['pad'], ok


def translations():
    en = {}
    for f in glob.glob(os.path.join(OUT, 'batch_[0-9][0-9].en.json')):
        for r in json.load(open(f, encoding='utf-8'))['rows']:
            if r.get('en'):
                en[r['id']] = r['en']
    return en


def build_subfile(s, static2_bytes):
    """-> (new sub-file 5 bytes, new STATIC2 bytes, report). s = original sub-file 5."""
    uniq = json.load(open(os.path.join(SRC, 'unique.json'), encoding='utf-8'))
    by_raw = {v['raw']: (k, v) for k, v in uniq.items()}
    en = translations()
    st = bytearray(static2_bytes)
    table = list(struct.unpack_from(f'<{NPILOTS}I', st, PILOT_TABLE))
    out = bytearray()
    moved, kept, overfull = {}, 0, []
    overflow, overflow_at = [], {}
    for off in sorted(set(t for t in table if t != 0xFFFFFFFF)):
        b = parse_block(s, off)
        secs, n = b['sections'], len(b['strings'])
        str_start = secs[-1]
        so = secs[SECTION_STR_OFFS]
        count = (secs[SECTION_STR_OFFS + 1] - so) // 2          # entries; some alias, the last may pad
        old_offs = struct.unpack_from(f'<{count}H', s, off + so)
        starts, pos = {}, 0
        for t in b['strings']:
            starts[pos] = t
            pos += len(t.encode('cp932')) + 1
        assert all(o in starts for o in old_offs), \
            f'block {off:#x}: section {SECTION_STR_OFFS} has an entry that is not a string start'
        head = bytearray(s[off:off + str_start])
        data_at = {}
        for o, t in starts.items():
            k, m = by_raw[t]
            if k in en:
                data_at[o], ok = encode_quote(en[k], m)
            else:
                data_at[o] = t.encode('cp932')
                kept += 1
        # strings that do not fit the 0x4800 read go to the PRX overflow table, longest first
        uniq_data = sorted(set(data_at.values()), key=lambda d: (-len(d), d))   # deterministic order
        size = str_start + sum(len(d) + 1 for d in uniq_data) + 1
        out_of_block = set()
        for d in uniq_data:
            if size <= BLOCK_MAX:
                break
            out_of_block.add(d)
            size -= len(d) + 1
        blob, where, new_at = bytearray(), {}, {}
        for o, d in data_at.items():
            if d in out_of_block:
                if d not in overflow_at:
                    overflow_at[d] = len(overflow)
                    overflow.append(d + b'\0')
                new_at[o] = OVERFLOW_BIT | overflow_at[d]
                continue
            if d not in where:
                where[d] = len(blob)
                blob += d + b'\0'
            new_at[o] = where[d]
        assert len(blob) < OVERFLOW_BIT, f'block {off:#x}: strings exceed 32 KB'
        struct.pack_into(f'<{count}H', head, so, *(new_at[o] for o in old_offs))
        block = head + blob + b'\0'
        if len(block) > BLOCK_MAX:
            overfull.append((off, len(block)))
        moved[off] = len(out)
        out += block + bytes((-len(block)) % 0x800)
    out += bytes(BLOCK_MAX)                        # the fixed-size read of the last block stays in the file
    for i, t in enumerate(table):
        if t != 0xFFFFFFFF:
            table[i] = moved[t]
    struct.pack_into(f'<{NPILOTS}I', st, PILOT_TABLE, *table)
    assert not overfull, f'blocks larger than {BLOCK_MAX:#x}: {[(hex(a), hex(b)) for a, b in overfull]}'
    assert len(overflow) < OVERFLOW_BIT
    report = (f'battle quotes: {len(moved)} blocks, {len(out):#x} bytes (was {len(s):#x}); '
              f'strings kept in Japanese: {kept}; in the PRX overflow table: {len(overflow)} '
              f'({sum(map(len, overflow))} bytes)')
    return bytes(out), bytes(st), overflow, report


def patch_battle2(src_path, dst_path, static2_bytes):
    """Copy BATTLE2.BIN to dst_path with the English sub-file 5 appended; returns the new STATIC2."""
    import shutil
    with open(src_path, 'rb') as f:
        head = f.read(0x40)
        offs = list(struct.unpack_from('<12I', head, 0))
        f.seek(offs[SUBFILE])
        s = f.read(offs[SUBFILE + 1] - offs[SUBFILE])
    new, st, overflow, report = build_subfile(s, static2_bytes)
    shutil.copyfile(src_path, dst_path)
    with open(dst_path, 'r+b') as f:
        f.seek(0, 2)
        end = f.tell()
        assert end % 0x800 == 0
        f.write(new)
        offs[SUBFILE] = end
        f.seek(0)
        f.write(struct.pack('<I', end) if SUBFILE == 0 else head[:4 * SUBFILE] + struct.pack('<I', end))
    print(report + f'; sub-file {SUBFILE} moved to {end:#x}')
    return st, overflow


# The three places that turn a string offset into a pointer: base + offset, stored at result + 0x34.
# Each `addu` becomes `jal stub` (the following `sw v1, 0x34(v0)` runs in the delay slot with a stale
# value; the stub stores again). Offsets with bit 15 set index the overflow table instead.
QUOTE_SITES = [  # (vaddr, original addu, base register, offset register)
    (0x49C08, 0x00851821, 4, 5),      # addu v1, a0, a1
    (0x4A22C, 0x00851821, 4, 5),      # addu v1, a0, a1
    (0x4A578, 0x00641821, 3, 4),      # addu v1, v1, a0
]


def patch_boot_quotes(boot, overflow):
    import insert_text as it
    data = bytearray(boot)
    for va, orig, _, _ in QUOTE_SITES:
        assert struct.unpack_from('<I', data, va + 0x60)[0] == orig, f'{va:#x}: unexpected code'
        assert struct.unpack_from('<I', data, va + 0x64)[0] == 0xAC430034, f'{va + 4:#x}: expected sw v1, 0x34(v0)'
    AT, V0, V1, T9, RA = 1, 2, 3, 25, 31
    stub_len = 13 * 4
    table_off = stub_len * len(QUOTE_SITES)
    blob = bytearray(table_off + 4 * len(overflow))
    str_rel = []
    for b in overflow:
        str_rel.append(len(blob))
        blob += b
    blob += bytes((-len(blob)) % 4)
    data, base = it.extend_segment(data, bytes(blob))
    put = lambda va, b: data.__setitem__(slice(va + 0x60, va + 0x60 + len(b)), b)
    table = base + table_off
    hi, lo = it._hi_lo(table)
    relocs = []
    for n, (va, orig, rb, ro) in enumerate(QUOTE_SITES):
        stub = base + n * stub_len
        put(stub, it._words(
            it._i(0xC, ro, AT, 0x8000), it._i(5, AT, 0, 4), 0,           # andi at, off, 0x8000; bnez at, ovf
            it._r(rb, ro, V1, 0, 0x21), it._r(RA, 0, 0, 0, 8), it._i(0x2B, V0, V1, 0x34),
            it._i(0xC, ro, AT, 0x7FFF), it._r(0, AT, AT, 2, 0),            # ovf: at = (off & 0x7fff) * 4
            it._i(0xF, 0, T9, hi), it._r(T9, AT, T9, 0, 0x21), it._i(0x23, T9, V1, lo),
            it._r(RA, 0, 0, 0, 8), it._i(0x2B, V0, V1, 0x34)))
        relocs += [(stub + 32, 5), (stub + 40, 6)]
        put(va, struct.pack('<I', (3 << 26) | ((stub >> 2) & 0x3FFFFFF)))
        relocs.append((va, 4))
    put(table, b''.join(struct.pack('<I', base + o) for o in str_rel))
    relocs += [(table + 4 * k, 2) for k in range(len(overflow))]
    data = it.append_relocs(data, relocs)
    print(f'battle quote overflow: {len(overflow)} strings, {len(blob)} bytes at {base:#x}; '
          f'{len(QUOTE_SITES)} pointer sites hooked')
    return bytes(data)


def verify(iso_path):
    """Read every quote back from a built ISO the way the game does and compare with the translation."""
    import pycdlib
    import insert_text as it
    iso = pycdlib.PyCdlib()
    iso.open(iso_path)

    def get(p, size=None, offset=0):
        with iso.open_file_from_iso(iso_path=p) as f:
            f.seek(offset)
            return f.read(size) if size else f.read()
    head = get('/PSP_GAME/USRDIR/BATTLE2.BIN', 0x40)
    base5 = struct.unpack_from('<12I', head, 0)[SUBFILE]
    st = get('/PSP_GAME/USRDIR/STATIC2_ADD.BIN')
    boot = get('/PSP_GAME/SYSDIR/BOOT.BIN')
    table = struct.unpack_from(f'<{NPILOTS}I', st, PILOT_TABLE)
    # overflow table address from the first stub (lui t9 / lw v1 pair)
    j = struct.unpack_from('<I', boot, QUOTE_SITES[0][0] + 0x60)[0]
    stub = (j & 0x3FFFFFF) << 2
    hi = struct.unpack_from('<I', boot, stub + 32 + 0x60)[0] & 0xFFFF
    lo = struct.unpack_from('<h', boot, stub + 40 + 0x60)[0]
    ovt = (hi << 16) + lo
    orig = subfile()
    uniq = json.load(open(os.path.join(SRC, 'unique.json'), encoding='utf-8'))
    by_raw = {v['raw']: (k, v) for k, v in uniq.items()}
    en = translations()
    checked = bad = ovf = 0
    for pid, off in enumerate(table):
        if off == 0xFFFFFFFF:
            continue
        blk = get('/PSP_GAME/USRDIR/BATTLE2.BIN', BLOCK_MAX, base5 + off)
        secs = struct.unpack_from('<10H', blk, 8)
        so, n = secs[SECTION_STR_OFFS], (secs[SECTION_STR_OFFS + 1] - secs[SECTION_STR_OFFS]) // 2
        offs = struct.unpack_from(f'<{n}H', blk, so)
        # the matching original block, to know which line each entry is
        o_table = struct.unpack_from(f'<{NPILOTS}I', static2(), PILOT_TABLE)
        ob = parse_block(orig, o_table[pid])
        oo = struct.unpack_from(f'<{n}H', orig, o_table[pid] + so)
        starts, pos = {}, 0
        for t in ob['strings']:
            starts[pos] = t
            pos += len(t.encode('cp932')) + 1
        for new_o, old_o in zip(offs, oo):
            if new_o & OVERFLOW_BIT:
                ptr = struct.unpack_from('<I', boot, ovt + 4 * (new_o & 0x7FFF) + 0x60)[0]
                data = boot[ptr + 0x60:boot.index(b'\0', ptr + 0x60)]
                ovf += 1
            else:
                a = secs[-1] + new_o
                data = blk[a:blk.index(b'\0', a)]
            k, m = by_raw[starts[old_o]]
            want = encode_quote(en[k], m)[0] if k in en else starts[old_o].encode('cp932')
            checked += 1
            if data != want:
                bad += 1
                if bad <= 5:
                    print('MISMATCH pilot', pid, k, data[:40], want[:40])
    iso.close()
    print(f'quote entries checked: {checked}; via overflow table: {ovf}; mismatches: {bad}')
    return bad


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'export':
        export(int(sys.argv[2]) if len(sys.argv) > 2 else 420)
    elif cmd == 'fit':
        lines, ok = fit(sys.argv[2], '--no-open' not in sys.argv, '--no-close' not in sys.argv)
        for l in lines:
            print(f'{textfit.px(l):4d}px | {l}')
        print('FITS' if ok else f'DOES NOT FIT ({len(lines)} lines, max {MAX_LINES}, {LINE_PX}px each)')
    elif cmd == 'check':
        sys.exit(1 if check(sys.argv[2:]) else 0)
    elif cmd == 'merge':
        sys.exit(1 if merge(sys.argv[2]) else 0)
    elif cmd == 'status':
        status()
    elif cmd == 'verify':
        sys.exit(1 if verify(sys.argv[2]) else 0)
    else:
        print(__doc__)
