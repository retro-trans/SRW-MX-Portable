"""Read back the non-dialogue text from a built ISO, following the game's own pointers.

usage: python verify_text_build.py <version>
BOOT.BIN: every relocated reference (data pointer or lui/addiu pair) to a translated string must
resolve to that string's English. STATIC2_ADD.BIN: names through Strg, description / library rows
through the X... indexes found via Fixh, summaries through their offset table, and the in-place
scenario fields. Prints a sample and a pass/fail count.
"""
import io, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pycdlib
import insert_text
from static2_extract import sections

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def read_iso(path, files):
    iso = pycdlib.PyCdlib()
    iso.open(path)
    out = {}
    for f in files:
        b = io.BytesIO()
        iso.get_file_from_iso_fp(b, iso_path=f)
        out[f] = b.getvalue()
    iso.close()
    return out


def cstr(d, o):
    return bytes(d[o:d.index(b'\0', o)])


def overflow_table(boot):
    """Table address used by the patched Strg getter: j stub -> lui/lw pair in the stub."""
    w = lambda va: struct.unpack_from('<I', boot, va + 0x60)[0]
    j = w(insert_text.GETTERS['Strg'] + 0x20)
    stub = (j & 0x3FFFFFF) << 2
    hi, lo = w(stub) & 0xFFFF, w(stub + 8) & 0xFFFF
    return (hi << 16) + (lo - 0x10000 if lo & 0x8000 else lo)


def resolver(d, boot):
    """Mimic the patched getters: section-relative offset, or overflow entry 0x80000000 + n."""
    table = overflow_table(boot)

    def get(base, off):
        if off & insert_text.OVERFLOW_FLAG:
            ptr = struct.unpack_from('<I', boot, table + 4 * (off & 0x7FFFFFFF) + 0x60)[0]
            return cstr(boot, ptr + 0x60)
        return cstr(d, base + off)
    return get


def main(version):
    iso = os.path.join(ROOT, 'work', 'output', f'SRWMX_EN_{version}.iso')
    f = read_iso(iso, ['/PSP_GAME/SYSDIR/BOOT.BIN', '/PSP_GAME/SYSDIR/EBOOT.BIN',
                       '/PSP_GAME/USRDIR/STATIC2_ADD.BIN', '/PSP_GAME/PARAM.SFO'])
    boot, static2 = f['/PSP_GAME/SYSDIR/BOOT.BIN'], f['/PSP_GAME/USRDIR/STATIC2_ADD.BIN']
    ok = bad = 0
    assert boot == f['/PSP_GAME/SYSDIR/EBOOT.BIN'], 'EBOOT.BIN differs from BOOT.BIN'

    # BOOT.BIN
    trans, bt = insert_text.boot_translations()
    trans.update(insert_text.narration_slots(bt))
    want = {v: insert_text.encode(en, raw)[:-1] for v, (en, raw) in trans.items()}
    orig = open(os.path.join(ROOT, 'work/build/iso/BOOT.BIN'), 'rb').read()
    semantic_orig = bytearray(orig)
    insert_text.patch_narration_script(semantic_orig, bt)
    secs_o, secs_n = insert_text.elf(orig), insert_text.elf(bytearray(boot))

    def rels(data, secs, name):
        off, size = struct.unpack_from('<2I', data, secs[name] + 16)
        return [struct.unpack_from('<2I', data, off + k) for k in range(0, size, 8)]
    w = lambda data, va: struct.unpack_from('<I', data, va + 0x60)[0]
    # data pointers: same relocation offsets in both files
    for off, info in rels(orig, secs_o, '.rel.data'):
        target = w(semantic_orig, off)
        if info & 0xFF == 2 and target in want:
            got = cstr(boot, w(boot, off) + 0x60)
            ok, bad = (ok + 1, bad) if got == want[target] else (ok, bad + 1)
    # code: pair HI16 with its LO16s in the new relocation table
    hi = None
    for off, info in rels(boot, secs_n, '.rel.text'):
        t = info & 0xFF
        if t == 5:
            hi = off
        elif t == 6 and hi is not None:
            def target(data):
                lo = w(data, off) & 0xFFFF
                return ((w(data, hi) & 0xFFFF) << 16) + (lo - 0x10000 if lo & 0x8000 else lo)
            if off < len(orig) and target(orig) in want:
                got = cstr(boot, target(boot) + 0x60)
                ok, bad = (ok + 1, bad) if got == want[target(orig)] else (ok, bad + 1)
    print(f'BOOT.BIN references to translated strings: {ok} correct, {bad} wrong')
    assert not bad, 'A translated BOOT string reference differs'

    # STATIC2_ADD.BIN
    d = static2
    S = sections(d)
    fix = insert_text.fixh_slots(bytearray(open(os.path.join(ROOT, 'work/build/STATIC2_ADD.orig'), 'rb').read()),
                                 sections(open(os.path.join(ROOT, 'work/build/STATIC2_ADD.orig'), 'rb').read()))
    sec_at = {tag: insert_text.VERS + struct.unpack_from('<I', d, slot)[0] for tag, slot in fix.items()}
    names = insert_text.load('static2/names.json')
    o = sec_at['Strg']
    n = struct.unpack_from('<I', d, o + 8)[0]
    offs = struct.unpack_from(f'<{n}I', d, o + 12)
    get = resolver(d, boot)
    good = sum(1 for k, en in names.items() if en and get(o, offs[int(k)]) == insert_text.encode(en)[:-1])
    print(f'Strg: {good} of {sum(1 for v in names.values() if v)} English names read back')
    so = sec_at['Sent']
    sn = struct.unpack_from('<I', d, so + 8)[0]
    soffs = struct.unpack_from(f'<{sn}I', d, so + 12)

    def entry(tag, e):
        io_ = sec_at[tag]
        p = struct.unpack_from('<I', d, io_ + 12 + 4 * e)[0]
        c = struct.unpack_from('<H', d, io_ + p)[0]
        rows = struct.unpack_from(f'<{c}H', d, io_ + p + 2)
        return [get(so, soffs[r]).decode('cp932') for r in rows]
    for tag, e in [('XSpr', 2), ('XSkl', 39), ('Xabl', 34), ('XPrt', 14), ('XHlp', 6), ('XHlp', 120), ('Xunt', 1), ('XPlt', 1)]:
        print(f'  {tag} {e}:', ' | '.join(entry(tag, e))[:200])
    sub4 = insert_text.SCENARIO + struct.unpack_from('<5I', d, insert_text.SCENARIO)[4]
    p = struct.unpack_from('<I', d, sub4 + 4)[0]
    print('  summary 0:', get(sub4, p).decode('cp932')[:160])
    last = struct.unpack_from('<I', d, sub4 + 4 + 4 * 66)[0]
    print('  summary 66:', get(sub4, last).decode('cp932')[:160])
    sc = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/static2_scenario.json'), encoding='utf-8'))
    print('  stage title 1:', cstr(d, sc['stage_titles'][2]['off']).decode('cp932'))
    print('  chapter 2:', cstr(d, sc['chapters'][2]['off']).decode('cp932'))
    sfo = f['/PSP_GAME/PARAM.SFO']
    print('  PARAM.SFO has English title:', b'Super Robot Wars MX Portable' in sfo)
    print(f'STATIC2_ADD.BIN: {len(d)} bytes (original 3576512)')


if __name__ == '__main__':
    main(*sys.argv[1:2])
