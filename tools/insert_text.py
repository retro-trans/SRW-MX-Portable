"""Insert the non-dialogue translations into BOOT.BIN, STATIC2_ADD.BIN and PARAM.SFO.

Called by build_patch.py (--text). Sources (English only, see docs/text_inventory.md):
  work/translation/en/ui/boot_ui.json, ui/boot_text.json          -> BOOT.BIN strings
  work/translation/en/static2/names.json, spirits.json,
      descriptions.json, scenario.json, library.json              -> STATIC2_ADD.BIN
  work/translation/en/ui/textures.json (PARAM.SFO title)           -> PARAM.SFO

BOOT.BIN: every translated string is written to a new block appended to the PRX load segment
(after whatever native_font4x.py appended), and every reference is rewritten: 32-bit data
pointers (.rel.data R_MIPS_32) and lui/addiu pairs (.rel.text HI16 + its LO16s). A lui is only
rewritten when every address it serves is a moved string (true for all 813 groups in 1.04).
The game's renderers count characters as strlen / 2, so English is stored as full-width SJIS;
format codes (%d, %s ...) and strings shown by the PSP system (raw) stay single-byte ASCII.

STATIC2_ADD.BIN must keep its exact size (the game reads 0x3692C0 bytes into a fixed memory map,
see LAYOUT). Sections are found through the Fixh directory (offsets relative to 'Vers' at
0x17EF00). Strg and Sent keep their place: their offset tables are rewritten and the strings fill
the old sections; X... indexes are rewritten in place, and an index that grew moves to space
reserved at the end of the old Sent section. Summaries refill their old area. Chapter names, stage
locations and stage titles are written in place where they fit.

Strings that do not fit (most of the library, some names and help, summaries, long spirit names)
go to an overflow table in the PRX: their table entry becomes 0x80000000 + n (spirit names get the
marker FF FF + n in their 12-byte field), and patch_overflow() makes the four getters (Strg, Sent,
summaries, spirit names) return overflow[n] for such entries. See docs/text_insertion.md.
"""
import json, os, re, struct, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfit
from static2_extract import sections, strtable, index

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TR = os.path.join(ROOT, 'work', 'translation', 'en')
VERS = 0x17EF00
SCENARIO = 0x1FCD80
SCENARIO_END = 0x204040             # first byte after the summaries: a texture the code addresses directly
OVERFLOW_FLAG = 0x80000000
FORMAT = re.compile(r'%[-+ 0#]*\d*(?:\.\d+)?[sdiuxXcfeg%]|\n')
FULLWIDTH_AT = '＠'                 # line break inside STATIC2 summaries
LIBRARY_PX, LIBRARY_ROWS = 496, 25


def load(path):
    return json.load(open(os.path.join(TR, path), encoding='utf-8'))


def encode(text, raw=False):
    """English -> bytes for the game. Format codes stay ASCII; raw strings are plain ASCII."""
    if raw:
        return text.encode('ascii') + b'\0'
    out, pos = bytearray(), 0
    for m in FORMAT.finditer(text):
        out += textfit.encode(text[pos:m.start()]) + m.group().encode('ascii')
        pos = m.end()
    return bytes(out + textfit.encode(text[pos:]) + b'\0')


CLEAN = {'‘': "'", '’': "'", '“': '"', '”': '"', '—': ' - ', '–': '-',
         '…': '...', 'é': 'e', 'è': 'e', 'à': 'a', 'ü': 'u', 'ö': 'o',
         'ō': 'o', 'ū': 'u', '×': 'x', '　': ' ', '^': '', '_': ' ', '<': '(', '>': ')'}


def clean(text):
    """Characters the game font has no Latin glyph for -> drawable equivalents (#... placeholders kept)."""
    return ''.join(CLEAN.get(c, c) for c in text)


def wrap(text, width, indent=''):
    return textfit.wrap('', text, '', line_px=width, indent=indent)[0]


# ---------------------------------------------------------------------------------------- BOOT.BIN

def elf(data):
    shoff, = struct.unpack_from('<I', data, 0x20)
    size, count, stridx = struct.unpack_from('<3H', data, 0x2E)
    heads = [shoff + i * size for i in range(count)]
    names = struct.unpack_from('<I', data, heads[stridx] + 16)[0]
    out = {}
    for h in heads:
        n = struct.unpack_from('<I', data, h)[0]
        out[data[names + n:data.index(b'\0', names + n)].decode()] = h
    return out


def boot_translations():
    """-> {vaddr: (english, raw)} for every BOOT.BIN string that changes."""
    inv = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/boot_strings.json'), encoding='utf-8'))
    ui = load('ui/boot_ui.json')
    bt = load('ui/boot_text.json')
    out = {}
    for x in inv:
        if x['category'] != 'ui':
            continue
        o = ui['overrides'].get(f"{x['va']:06X}")
        en = o['en'] if o else ui['defaults'].get(x['text'])
        if en is not None:
            out[x['va']] = (en, False)
    for group in ('locations', 'save'):
        for va, v in bt[group].items():
            en, raw = (v, False) if isinstance(v, str) else (v['en'], v.get('raw', False))
            out[int(va, 16)] = (en, raw)
    return out, bt


NARRATION_SCRIPT = 0x273AD4      # records (delay, 7, string pointer); 12 bytes each
NARRATION_BLANK = 0x285DE8       # '　' (one full-width space): a blank line
NARRATION_END = 0x286318         # '' : end of a narration


def narration_paragraphs(bt):
    """-> {table name: [[slot vaddr of each line] per paragraph]}, matching narration_slots."""
    inv = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/boot_strings.json'), encoding='utf-8'))
    vas = sorted(x['va'] for x in inv if x['category'] == 'narration')
    tables = sorted((int(v[0], 16), v[1], k) for k, v in bt['narration_tables'].items())
    out = {}
    for n, (start, slots, name) in enumerate(tables):
        end = tables[n + 1][0] if n + 1 < len(tables) else 1 << 32
        mine = iter(v for v in vas if start <= v < end)
        out[name] = [[next(mine) for _ in wrap(p, 416)] for p in bt['narration'][name]]
    return out


def patch_narration_script(data, bt, offset=0x60):
    """Rewrite the opening / ending narration scripts for the English line layout.
    The Japanese script shows its 32 / 24 lines with blank records between paragraphs at fixed
    positions, and ends at a record pointing to NARRATION_END (''). English has a different number
    of lines per paragraph, so each script is refilled with the English lines and blank lines between
    paragraphs, keeping the original timing (see the comment in the loop). Unused line slots are never referenced (an empty slot
    would act as an end marker and stall the narration). Pointer words keep their relocations."""
    paras = narration_paragraphs(bt)
    recs = []
    o = NARRATION_SCRIPT
    while True:
        t, ty, ptr = struct.unpack_from('<iII', data, o + offset)
        if ty != 7:
            break
        recs.append((o, t, ptr))
        o += 12
    ends = [i for i, r in enumerate(recs) if r[2] == NARRATION_END]
    starts = [i for i, r in enumerate(recs) if r[1] == 207]
    assert len(ends) == 2 and len(starts) == 2, 'narration script differs'
    for name, first, last in (('opening', starts[0], ends[0]), ('ending', starts[1], ends[1])):
        # Timing: the narration runs against fixed visuals, and reaching the end record early stalls
        # or repeats it (seen in game, 0.4.2 / 0.4.5). So the end record stays where it was, the last
        # English line lands on the record of the last Japanese line, and the extra records are
        # spread as blank lines between paragraphs (any remainder goes before the first line).
        texts = [i for i in range(first, last) if recs[i][2] != NARRATION_BLANK]
        target = texts[-1] - first + 1                     # records up to and including the last line
        paras_ = paras[name]
        n_lines = sum(len(p) for p in paras_)
        gaps = len(paras_) - 1
        spare = target - n_lines
        assert spare >= gaps, f'{name}: not enough records ({target}) for {n_lines} lines'
        per, extra = divmod(spare, gaps) if gaps else (0, spare)
        lead = extra if gaps else spare
        seq = [NARRATION_BLANK] * lead
        for k, para in enumerate(paras_):
            if k:
                seq += [NARRATION_BLANK] * per
            seq += para
        seq += [NARRATION_BLANK] * (last - first - len(seq))
        assert len(seq) == last - first
        for i, ptr in zip(range(first, last), seq):
            struct.pack_into('<I', data, recs[i][0] + 8 + offset, ptr)


def narration_slots(bt):
    """Narration tables: the line strings in address order -> English lines (padded with '')."""
    inv = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/boot_strings.json'), encoding='utf-8'))
    vas = sorted(x['va'] for x in inv if x['category'] == 'narration')
    out = {}
    tables = sorted((int(v[0], 16), v[1], k) for k, v in bt['narration_tables'].items())
    for n, (start, slots, name) in enumerate(tables):
        end = tables[n + 1][0] if n + 1 < len(tables) else 1 << 32
        mine = [v for v in vas if start <= v < end]
        assert len(mine) == slots, f'{name}: {len(mine)} line strings, expected {slots}'
        lines = []
        for p in bt['narration'][name]:
            lines += wrap(p, 416)
        assert len(lines) <= slots, f'{name}: {len(lines)} lines > {slots}'
        lines += [''] * (slots - len(lines))
        for v, l in zip(mine, lines):
            out[v] = (l, False)
    return out


# Layout changes in game code: (vaddr, original instruction word, new word, why). Applied by patch_boot,
# which checks the original word first.
CODE_PATCHES = [
    # pilot status, spirit list: cost "(%3d)" drawn at x+0xD0, the name at x+0x9F (49 px for the
    # name). Moved 14 px right (room to the panel edge: about 6 px left): names up to 63 px fit.
    (0x1F043C, 0x246600D0, 0x246600DE, 'spirit list cost column x+0xD0 -> x+0xDE'),
    # support / assist command menus: per-item x offsets centred the Japanese (data, no relocations)
    (0x28BD84, 0x0000001E, 0x0000000F, 'support menus: left-align item at x+15 (was 30, centred Japanese)'),
    (0x28BD8C, 0x0000000A, 0x0000000F, 'support menus: left-align item at x+15 (was 10, centred Japanese)'),
    (0x28BD9C, 0x00000014, 0x0000000F, 'support menus: left-align item at x+15 (was 20, centred Japanese)'),
    (0x28BE04, 0x0000001E, 0x0000000F, 'support menus: left-align item at x+15 (was 30, centred Japanese)'),
    (0x28BE14, 0x0000001E, 0x0000000F, 'support menus: left-align item at x+15 (was 30, centred Japanese)'),
    (0x28BE1C, 0x0000000A, 0x0000000F, 'support menus: left-align item at x+15 (was 10, centred Japanese)'),
    (0x28BE2C, 0x00000014, 0x0000000F, 'support menus: left-align item at x+15 (was 20, centred Japanese)'),
    # active spirit codes (Fl, Fc ...) after the 'Spr' label: 16 px apart fitted one kanji each; 24 px
    (0x1D5304, 0x26100010, 0x26100018, 'active spirit codes: step 16 -> 24 px'),
    # more menus whose per-item x offsets centred the Japanese words (0.4.6)
    (0x1FA9A4, 0x246600AC, 0x246600A6, 'battle setup: Battle Anim. at x+0xAC like the other rows (x+0xA6)'),
    (0x1B2AD0, 0x24030017, 0x24030012, 'yes/no box: Yes at x+0x12 like No (was 0x17, centred Japanese)'),
    (0x28AF38, 0x000F001E, 0x000F000F, 'search menu: Spirit at x+15 like Skills / Abilities (was 30)'),
    (0x296538, 0x00000007, 0x00000001, 'transfer menu: Sub at x+1 like Main (was 7)'),
    (0x296660, 0x0000000B, 0x00000001, 'upgrade menu: Weapons at x+1 like Status (was 11)'),
    (0x29666C, 0x00000006, 0x00000001, 'upgrade menu: Shield at x+1 like Status (was 6)'),
    (0x296678, 0x00000018, 0x00000008, 'pilot training menu: Raise Stats at x+8 like Learn Skills (was 24)'),
]


# Code blocks that need relocations: (vaddr, original bytes, new words, [(word index, reloc type)], why).
# Applied by patch_centering (after the PRX segment is final, since it appends relocations).
CODE_BLOCKS = [
    # new-game series pick screen: the header centres the series name using 16 px per character
    # (Japanese width). English names start off the left edge. The counting loop is replaced by a
    # call to the real width function W1 (0xB03E4, VWF-aware); the string pointer is kept in $f16
    # (unused in this function) across the call.
    (0x1D32D8, '212000000000a2800c004010211800002110a3000000429088004228020040541000842410008424'
               '020063242110a30000004280f7ff40542110a300',
     [0x44858000,                     # mtc1  a1, f16
      (9 << 26) | (16 << 21) | (4 << 16) | 0x190,   # addiu a0, s0, 0x190 (text context)
      (3 << 26) | (0xB03E4 >> 2),     # jal   W1 (width of a1 in context a0)
      0,
      0x44058000,                     # mfc1  a1, f16
      (2 << 21) | (4 << 11) | 0x21,   # move  a0, v0 (width)
      0, 0, 0, 0, 0, 0, 0, 0, 0],
     [(2, 4)], 'series pick screen: centre the series name by its real width'),
    # spirit / skill search grids: their own width estimate (20 px per kanji, 14 per other character)
    # centred English far off; it now returns the real width from W1 in the screen's text context
    # (object + 0x190, the context the grid is drawn with)
    (0x1EAE70, '0000a3802130000016006010',
     [(9 << 26) | (4 << 21) | (4 << 16) | 0x190,   # addiu a0, a0, 0x190
      (2 << 26) | (0xB03E4 >> 2),                  # j     W1
      0],
     [(1, 4)], 'search grids: centre names by their real width'),
]


def patch_centering(boot):
    data = bytearray(boot)
    relocs = []
    for va, orig, words, rel, why in CODE_BLOCKS:
        o = bytes.fromhex(orig)
        assert len(o) == 4 * len(words), why
        assert data[va + 0x60:va + 0x60 + len(o)] == o, f'{va:#x}: unexpected code ({why})'
        data[va + 0x60:va + 0x60 + len(o)] = b''.join(struct.pack('<I', w) for w in words)
        relocs += [(va + 4 * k, t) for k, t in rel]
    return bytes(append_relocs(data, relocs))


def patch_code(data, offset=0x60):
    for va, orig, new, why in CODE_PATCHES:
        cur = struct.unpack_from('<I', data, va + offset)[0]
        assert cur == orig, f'{va:#x}: expected {orig:#010x}, found {cur:#010x} ({why})'
        struct.pack_into('<I', data, va + offset, new)


def patch_boot(boot):
    data = bytearray(boot)
    patch_code(data)
    patch_narration_script(data, boot_translations()[1])
    secs = elf(data)
    phoff = struct.unpack_from('<I', data, 28)[0]
    kind, offset, va, pa, filesz, memsz, flags, align = struct.unpack_from('<8I', data, phoff)
    assert kind == 1 and offset == 0x60 and va == 0

    def rels(name):
        off, size = struct.unpack_from('<2I', data, secs[name] + 16)
        return [struct.unpack_from('<2I', data, off + k) for k in range(0, size, 8)]
    rel_text, rel_data = rels('.rel.text'), [o for o, i in rels('.rel.data') if i & 0xFF == 2]
    word = lambda v: struct.unpack_from('<I', data, v + offset)[0]

    trans, bt = boot_translations()
    trans.update(narration_slots(bt))

    # lay out the new strings (identical byte strings shared)
    start = (memsz + 127) & ~127
    blob, where, new_va = bytearray(), {}, {}
    for v in sorted(trans):
        en, raw = trans[v]
        b = encode(en, raw)
        if b not in where:
            where[b] = start + len(blob)
            blob += b
            blob += bytes((-len(blob)) % 4)
        new_va[v] = where[b]

    # references: data pointers
    fixed_data = 0
    for off in rel_data:
        t = word(off)
        if t in new_va:
            struct.pack_into('<I', data, off + offset, new_va[t])
            fixed_data += 1
    # references: lui (HI16) groups followed by their LO16s
    groups, cur = [], None
    for off, info in rel_text:
        t = info & 0xFF
        if t == 5:
            cur = [off, []]
            groups.append(cur)
        elif t == 6 and cur is not None:
            cur[1].append(off)
    fixed_code = 0
    for hi_off, los in groups:
        hi = word(hi_off) & 0xFFFF
        targets = []
        for lo_off in los:
            lo = word(lo_off) & 0xFFFF
            targets.append((hi << 16) + (lo - 0x10000 if lo & 0x8000 else lo))
        moved = [t in new_va for t in targets]
        if not any(moved):
            continue
        assert all(moved), f'lui at {hi_off:#x} serves moved and unmoved addresses'
        news = [new_va[t] for t in targets]
        nhi = (news[0] + 0x8000) >> 16
        assert all(-0x8000 <= n - (nhi << 16) < 0x8000 for n in news), f'group {hi_off:#x} spans > 64 KB'
        ins = word(hi_off)
        struct.pack_into('<I', data, hi_off + offset, (ins & 0xFFFF0000) | nhi)
        for lo_off, n in zip(los, news):
            ins = word(lo_off)
            struct.pack_into('<I', data, lo_off + offset, (ins & 0xFFFF0000) | ((n - (nhi << 16)) & 0xFFFF))
            fixed_code += 1
    oldlen = {v: data.index(b'\0', v + offset) - (v + offset) for v in new_va}
    targets_all = sorted(set(word(o) for o in rel_data))
    import bisect
    inside = []
    for v, n in oldlen.items():
        i = bisect.bisect_right(targets_all, v)
        while i < len(targets_all) and targets_all[i] < v + n:
            if targets_all[i] not in new_va:
                inside.append((v, targets_all[i]))
            i += 1

    # append the block to the load segment; shift everything stored after it
    new_size = start + len(blob)
    old_end = offset + filesz
    assert data[offset + filesz:offset + memsz] == bytes(memsz - filesz)
    delta = new_size - filesz
    data = bytearray(data[:old_end] + bytes(start - filesz) + blob + data[old_end:])
    struct.pack_into('<2I', data, phoff + 16, new_size, new_size)
    shoff = struct.unpack_from('<I', data, 0x20)[0] + delta
    struct.pack_into('<I', data, 0x20, shoff)
    shsize, count, _ = struct.unpack_from('<3H', data, 46)
    for n in range(count):
        h = shoff + n * shsize
        stype, soff = struct.unpack_from('<I', data, h + 4)[0], struct.unpack_from('<I', data, h + 16)[0]
        if soff >= old_end and stype != 8:
            struct.pack_into('<I', data, h + 16, soff + delta)
    print(f'BOOT text: {len(trans)} strings -> {len(where)} unique, {len(blob)} bytes at {start:#x}; '
          f'{fixed_data} data pointers and {fixed_code} code references rewritten; PRX memory +{new_size - memsz} bytes')
    if inside:
        print(f'  note: {len(inside)} pointers point inside moved strings and keep the Japanese')
    return bytes(data)


# ----------------------------------------------------------------------------------- STATIC2_ADD.BIN

def table_bytes(tag, count, offsets, payload):
    head = 12 + 4 * count
    body = struct.pack(f'<{count}I', *[head + o for o in offsets]) + payload
    return tag + struct.pack('<2I', 12 + len(body), count) + body


def build_index(tag, entries):
    payload, offs = bytearray(), []
    for rows in entries:
        offs.append(len(payload))
        payload += struct.pack(f'<H{len(rows)}H', len(rows), *rows)
        payload += bytes((-len(payload)) % 4)
    return table_bytes(tag, len(entries), offs, bytes(payload))


def fixh_slots(d, S):
    o = S['Fixh'][0]
    n = (S['Fixh'][1] - 12) // 4
    vals = struct.unpack_from(f'<{n}I', d, o + 12)
    out = {}
    for tag, (off, _, _) in S.items():
        for i, v in enumerate(vals):
            if v and VERS + v == off:
                out[tag] = (o + 12 + 4 * i)
    return out


def patch_static2(static2):
    d = bytearray(static2)
    S = sections(bytes(d))
    fix = fixh_slots(d, S)
    report = []

    # names (Strg)
    names = load('static2/names.json')
    strg_raw = []
    o, size, cnt = S['Strg']
    offs = struct.unpack_from(f'<{cnt}I', d, o + 12)
    for i, p in enumerate(offs):
        z = d.index(b'\0', o + p)
        en = names.get(str(i))
        strg_raw.append(encode(en) if en else bytes(d[o + p:z + 1]))
    new = {}

    # sentence rows + indexes
    sent = strtable(bytes(d), S['Sent'][0], S['Sent'][2])
    sent_raw = [s.encode('cp932') + b'\0' for s in sent]
    rows_out, entries = [], {}
    desc = load('static2/descriptions.json')
    lib = load('library.json')
    # the help window at the top of the screen holds about 420 px per row (seen in game, 0.3.2: a
    # 438 px row ran past it), less than the widest Japanese row suggested
    width = {'XSpr': 416, 'XSkl': 416, 'Xabl': 416, 'XPrt': 272, 'XHlp': 416}
    for tag in ['Xunt', 'XPlt', 'XSpr', 'XSkl', 'Xabl', 'XPrt', 'XHlp']:
        old = index(bytes(d), S[tag][0], S[tag][2])
        es = []
        for e, rows in enumerate(old):
            en = None
            if tag in ('Xunt', 'XPlt'):
                x = lib['units' if tag == 'Xunt' else 'pilots'].get(str(e))
                en = x.get('en') if x else None
            else:
                en = desc[tag].get(str(e))
            if en:
                lines = wrap(clean(en), LIBRARY_PX if tag in ('Xunt', 'XPlt') else width[tag])
                if tag in ('Xunt', 'XPlt') and len(lines) > LIBRARY_ROWS:
                    report.append(f'{tag} {e}: {len(lines)} rows (library box shows {LIBRARY_ROWS})')
                new_rows = []
                for l in lines:
                    new_rows.append(len(rows_out))
                    rows_out.append(encode(l))
                es.append(new_rows)
            else:
                new_rows = []
                for r in rows:
                    new_rows.append(len(rows_out))
                    rows_out.append(sent_raw[r])
                es.append(new_rows)
        new[tag] = build_index(tag.encode().ljust(4), es)
    assert len(rows_out) < 0x10000

    # STATIC2_ADD.BIN must keep its size: the game reads exactly 0x3692C0 bytes into a fixed memory
    # map (see LAYOUT). Strg and Sent keep their place: offset tables are rewritten in place and the
    # strings fill the old section. Strings that do not fit go to `overflow`; their table entry is
    # 0x80000000 + n, which the patched getters in BOOT.BIN (patch_overflow) resolve through a
    # pointer table in the PRX. Indexes are rewritten in place; an index that grew is moved into
    # space reserved at the end of the old Sent section (Fixh repointed).
    overflow = []

    def ref(b):
        overflow.append(b)
        return OVERFLOW_FLAG | (len(overflow) - 1)

    so, ssize, _ = S['Sent']
    reserve_end = so + ssize
    grown = []
    for tag in ['Xunt', 'XPlt', 'XSpr', 'XSkl', 'Xabl', 'XPrt', 'XHlp']:
        off, size, _ = S[tag]
        b = new[tag]
        if len(b) <= size:
            d[off:off + size] = b[:4] + struct.pack('<I', size) + b[8:] + bytes(size - len(b))
        else:
            grown.append(tag)
            reserve_end = (reserve_end - len(b)) & ~15
            d[reserve_end:reserve_end + len(b)] = b
            struct.pack_into('<I', d, fix[tag], reserve_end - VERS)
    moved_x = [(reserve_end, so + ssize)] if grown else []
    for tag, strings in (('Strg', strg_raw), ('Sent', rows_out)):
        off, size, _ = S[tag]
        limit = reserve_end if tag == 'Sent' else off + size
        n = len(strings)
        head = 12 + 4 * n
        assert head <= limit - off, f'{tag}: offset table no longer fits its section'
        pos, offsets = off + head, []
        for b in strings:
            if pos + len(b) <= limit:
                d[pos:pos + len(b)] = b
                offsets.append(pos - off)
                pos += len(b)
            else:
                offsets.append(ref(b))
        d[pos:limit] = bytes(limit - pos)
        d[off:off + head] = tag.encode() + struct.pack('<2I', size, n) + struct.pack(f'<{n}I', *offsets)
    if grown:
        report.append(f'indexes that grew, moved to the end of the old Sent section: {", ".join(grown)}')

    # scenario block: in-place fields, appended summaries
    sc_src = json.load(open(os.path.join(ROOT, 'work/source/text_inventory/static2_scenario.json'), encoding='utf-8'))
    sc = load('static2/scenario.json')

    def put_inline(off, jp, en, what, field):
        room = len(jp.encode('cp932'))
        while d[off + room] == 0 and room < field:
            room += 1
        b = encode(en)
        if len(b) > room:
            report.append(f'{what}: {en!r} needs {len(b)} bytes, room {room}; kept Japanese')
            return
        d[off:off + room] = b + bytes(room - len(b))
    for i, x in enumerate(sc_src['chapters']):
        put_inline(x['off'], x['text'], sc['chapters'][str(i)], f'chapter {i}', 0x40)
    for x in sc_src['locations']:
        put_inline(x['off'], x['text'], sc['locations'][x['text']], 'location', 0x40)
    for x in sc_src['stage_titles']:
        put_inline(x['off'], x['text'], sc['stage_titles'][x['text']]['en'], 'stage title', 0x38)
    # summaries: the old strings area (after the offset table, up to the end of the scenario block)
    # is refilled; what does not fit goes to the overflow table like Strg / Sent
    sub4 = SCENARIO + struct.unpack_from('<5I', d, SCENARIO)[4]
    n = struct.unpack_from('<I', d, sub4)[0]
    pos, limit = sub4 + 4 + 4 * n, SCENARIO_END
    old_offs = struct.unpack_from(f'<{n}I', d, sub4 + 4)
    texts = []
    for i in range(n):
        en = sc['summaries'].get(str(i))
        texts.append(encode(FULLWIDTH_AT.join(wrap(en, 448))) if en else bytes(d[sub4 + old_offs[i]:d.index(b'\0', sub4 + old_offs[i]) + 1]))
    offs = []
    for b in texts:
        if pos + len(b) <= limit:
            d[pos:pos + len(b)] = b
            offs.append(pos - sub4)
            pos += len(b)
        else:
            offs.append(ref(b))
    d[pos:limit] = bytes(limit - pos)
    struct.pack_into(f'<{n}I', d, sub4 + 4, *offs)

    # spirit command names (12-byte inline field)
    # names longer than the 12-byte field get the marker FF FF + u16 overflow index; the patched name
    # getter (SPRT_NAME_GETTER) returns the overflow string for them
    sp = load('static2/spirits.json')
    o = S['Sprt'][0]
    marked = 0
    for i in range(S['Sprt'][2]):
        en = sp.get(str(i))
        if not en:
            continue
        b = encode(en)
        if len(b) > 12:
            b = SPRT_MARK + struct.pack('<H', ref(b) & 0xFFFF)
            marked += 1
        d[o + 12 + i * 16:o + 12 + i * 16 + 12] = b + bytes(12 - len(b))
    if marked:
        report.append(f'spirit names longer than the 12-byte field, served from the overflow table: {marked}')
    assert len(d) == len(static2), 'STATIC2_ADD.BIN changed size'
    print(f'STATIC2 text: {len(strg_raw)} names, {len(rows_out)} sentence rows, '
          f'{len(sc_src["summaries"])} summaries; {len(overflow)} strings ({sum(map(len, overflow))} bytes) '
          f'moved to the PRX overflow table')
    for r in report:
        print('  note:', r)
    return bytes(d), overflow


# -------------------------------------------------------------------------------------- PARAM.SFO

def patch_sfo(sfo):
    d = bytearray(sfo)
    title = load('ui/textures.json')['PARAM.SFO']['TITLE']['en'].encode('utf-8')
    kt, dt, n = struct.unpack_from('<3I', d, 8)
    for j in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', d, 20 + j * 16)
        key = d[kt + ko:d.index(b'\0', kt + ko)]
        if key == b'TITLE':
            assert len(title) + 1 <= mx
            d[dt + do:dt + do + mx] = title + bytes(mx - len(title))
            struct.pack_into('<I', d, 20 + j * 16 + 4, len(title) + 1)
    return bytes(d)


# ---------------------------------------------------------------------------------- memory layout

# Why STATIC2_ADD.BIN cannot grow: the game reads exactly 0x3692C0 bytes of it into the start of a
# fixed 16 MB area. The region boundaries after it are constants written by 176 identical static
# initializers (0x29A808-0x2B79D4: 0x3692C0, 0x369300, 0x40E680 ... 0xEE9B00), the malloc heap is
# 0xEE9B00-0xF00000, and more code adds hard-coded area offsets directly (0x7E6640, 0xF00000 ...).
# Shifting the layout starves the heap ("Malloc Memory Over", tested in 0.2.0). See
# docs/text_insertion.md. Overflow text therefore lives in the PRX instead (below).
LAYOUT = [0x3692c0, 0x369300, 0x40e680, 0x421300, 0x421400, 0x98c300, 0xa3b300, 0xa72b00, 0xa8b300,
          0xaab300, 0xc72300, 0xeb8b00, 0xec9300, 0xee9b00]


# ------------------------------------------------------------------- overflow strings in BOOT.BIN

# Getters that turn a table entry into a pointer (identical code for each section class):
#   lw a0,(a0); sll v0,a1,2; addiu v1,a0,0xc; addu v0,v1,v0; lw v0,(v0);
#   bgezl v0,L; addu v0,a0,v0 (likely); move v0,zero; L: jr ra; nop
# A negative entry used to mean "no string". It now means "overflow string n" (0x80000000 + n)
# and is looked up in a pointer table appended to the PRX. The summary getter ends with
# jr ra; addu v0,a3,v0 and gets the same treatment through a second stub.
GETTERS = {'Strg': 0x5BF24, 'Sent': 0x5BDDC}
GETTER_ORIG = bytes.fromhex('0000848c801005000c008324211062000000428c0200430421108200211000000800e00300000000')
SUMMARY_TAIL = 0x1A41D4
SPRT_NAME_GETTER = 0x5BEC8            # j 0x5BF10 (record pointer = name); has an R_MIPS_26 relocation
SPRT_MARK = b'\xff\xff'
SUMMARY_ORIG = bytes.fromhex('0800e003' '2110e200')
ZERO, AT, V0, A0, A1, A3, RA = 0, 1, 2, 4, 5, 7, 31


def _r(rs, rt, rd, sa, fn):
    return (rs << 21) | (rt << 16) | (rd << 11) | (sa << 6) | fn


def _i(op, rs, rt, imm):
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)


def _words(*ws):
    return b''.join(struct.pack('<I', w) for w in ws)


def _hi_lo(addr):
    hi = (addr + 0x8000) >> 16
    return hi, addr - (hi << 16)


def extend_segment(data, payload, align=16):
    """Append payload to the PRX load segment; returns (new data, payload vaddr)."""
    phoff = struct.unpack_from('<I', data, 28)[0]
    kind, offset, va, pa, filesz, memsz, flags, al = struct.unpack_from('<8I', data, phoff)
    assert kind == 1 and offset == 0x60 and va == 0
    assert data[offset + filesz:offset + memsz] == bytes(memsz - filesz)
    start = (memsz + align - 1) & ~(align - 1)
    new_size = start + len(payload)
    old_end = offset + filesz
    delta = new_size - filesz
    data = bytearray(data[:old_end] + bytes(start - filesz) + payload + data[old_end:])
    struct.pack_into('<2I', data, phoff + 16, new_size, new_size)
    shoff = struct.unpack_from('<I', data, 0x20)[0] + delta
    struct.pack_into('<I', data, 0x20, shoff)
    shsize, count, _ = struct.unpack_from('<3H', data, 46)
    for n in range(count):
        h = shoff + n * shsize
        stype, soff = struct.unpack_from('<I', data, h + 4)[0], struct.unpack_from('<I', data, h + 16)[0]
        if soff >= old_end and stype != 8:
            struct.pack_into('<I', data, h + 16, soff + delta)
    return data, start


def append_relocs(data, entries):
    """Move .rel.text to the end of the file with extra (vaddr, type) entries."""
    secs = elf(data)
    h = secs['.rel.text']
    off, size = struct.unpack_from('<2I', data, h + 16)
    old = bytes(data[off:off + size])
    have = {struct.unpack_from('<I', old, k)[0] for k in range(0, len(old), 8)}
    assert not any(va in have for va, _ in entries if _ != 2), 'instruction already has a relocation'
    data += bytes((-len(data)) % 4)
    new_off = len(data)
    data += old + b''.join(struct.pack('<2I', va, t) for va, t in entries)
    struct.pack_into('<2I', data, h + 16, new_off, size + 8 * len(entries))
    return data


def patch_overflow(boot, overflow):
    data = bytearray(boot)
    for name, g in GETTERS.items():
        assert data[g + 0x60:g + 0x60 + 40] == GETTER_ORIG, f'{name} getter at {g:#x} is not the expected code'
    assert data[SUMMARY_TAIL + 0x60:SUMMARY_TAIL + 0x68] == SUMMARY_ORIG, 'summary getter tail differs'
    n = len(overflow)
    w = lambda va: struct.unpack_from('<I', data, va + 0x60)[0]
    assert w(SPRT_NAME_GETTER) == (2 << 26) | (0x5BF10 >> 2) and w(SPRT_NAME_GETTER + 4) == 0, 'spirit name getter differs'
    code_len = 4 * 5 + 4 * 10 + 4 * 18
    table_off = code_len
    strings_off = table_off + 4 * n
    # payload is laid out first with placeholder addresses, then filled once its vaddr is known
    blob = bytearray(strings_off)
    str_rel = []
    for b in overflow:
        str_rel.append(len(blob))
        blob += b
    blob += bytes((-len(blob)) % 4)
    data, base = extend_segment(data, bytes(blob))
    put = lambda va, b: data.__setitem__(slice(va + 0x60, va + 0x60 + len(b)), b)
    stub1, stub2, table = base, base + 20, base + table_off
    hi, lo = _hi_lo(table)
    put(stub1, _words(_i(0xF, 0, AT, hi), _r(AT, V0, AT, 0, 0x21), _i(0x23, AT, V0, lo), _r(RA, 0, 0, 0, 8), 0))
    put(stub2, _words(_i(1, V0, 0, 3), 0, _r(RA, 0, 0, 0, 8), _r(A3, V0, V0, 0, 0x21),
                      _r(0, V0, V0, 2, 0), _i(0xF, 0, AT, hi), _r(AT, V0, AT, 0, 0x21), _i(0x23, AT, V0, lo),
                      _r(RA, 0, 0, 0, 8), 0))
    put(table, b''.join(struct.pack('<I', base + o) for o in str_rel))
    stub3 = base + 60
    # v0 = record (base + 12 + idx * 16); if it starts with FF FF, return overflow[u16 at +2]
    put(stub3, _words(_i(0x23, A0, 3, 0), _r(0, A1, V0, 4, 0), _r(3, V0, V0, 0, 0x21), _i(9, V0, V0, 0xC),
                      _i(0x24, V0, 3, 0), _i(9, ZERO, AT, 0xFF), _i(5, 3, AT, 9), 0,
                      _i(0x24, V0, 3, 1), _i(5, 3, AT, 6), 0,
                      _i(0x25, V0, 3, 2), _r(0, 3, 3, 2, 0), _i(0xF, 0, AT, hi), _r(AT, 3, AT, 0, 0x21),
                      _i(0x23, AT, V0, lo)))
    put(stub3 + 64, _words(_r(RA, 0, 0, 0, 8), 0))
    relocs = [(stub1, 5), (stub1 + 8, 6), (stub2 + 20, 5), (stub2 + 28, 6), (stub3 + 52, 5), (stub3 + 60, 6)]
    put(SPRT_NAME_GETTER, _words((2 << 26) | ((stub3 >> 2) & 0x3FFFFFF), 0))   # keeps its R_MIPS_26
    for g in GETTERS.values():
        put(g, _words(_i(0x23, A0, A0, 0), _r(0, A1, V0, 2, 0), _r(A0, V0, V0, 0, 0x21), _i(0x23, V0, V0, 0xC),
                      _i(1, V0, 0, 3), 0, _r(RA, 0, 0, 0, 8), _r(A0, V0, V0, 0, 0x21),
                      (2 << 26) | ((stub1 >> 2) & 0x3FFFFFF), _r(0, V0, V0, 2, 0)))
        relocs.append((g + 0x20, 4))
    put(SUMMARY_TAIL, _words((2 << 26) | ((stub2 >> 2) & 0x3FFFFFF), 0))
    relocs.append((SUMMARY_TAIL, 4))
    relocs += [(table + 4 * k, 2) for k in range(n)]
    data = append_relocs(data, relocs)
    print(f'overflow: {n} strings, {len(blob)} bytes at {base:#x} (stubs, pointer table, strings); '
          f'getters patched: Strg, Sent, summaries, spirit names; {len(relocs)} relocations added')
    return bytes(data)
