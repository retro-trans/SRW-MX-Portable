"""Translate native PS2 detail/search/roster labels and reflow descriptions."""
import argparse
import json
import shutil
import struct

import keystone
import insert_text as it
from port_ps2_translations import ROOT, sha
from port_ps2_prologue import save
from ps2_font4x import FILE_BIAS
from ps2_translation_native import extend
from ps2_database_port import indices
from static2_extract import sections, index

VERSION = '0.1.12'
SOURCE_VERSION = '0.1.11'
BASE = ROOT / 'work/build/ps2' / f'ui_details_{VERSION}'


def wrap_native(text, widths, limit=512):
    lines = []
    for paragraph in it.clean(text).split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if sum(widths[c] for c in candidate) > limit and line:
                lines.append(line)
                line = word
            else:
                line = candidate
            assert sum(widths[c] for c in line) <= limit, word
        lines.append(line)
    # Avoid a single orphaned word after an otherwise full first line.
    if len(lines) == 2 and sum(widths[c] for c in lines[1]) < 120:
        words = ' '.join(lines).split()
        candidates = []
        for split in range(1, len(words)):
            pair = [' '.join(words[:split]), ' '.join(words[split:])]
            sizes = [sum(widths[c] for c in v) for v in pair]
            if max(sizes) <= limit:
                candidates.append((abs(sizes[0] - sizes[1]), pair))
        lines = min(candidates)[1]
    return lines


def prepare():
    previous = ROOT / 'work/build/ps2' / f'ui_fix_{SOURCE_VERSION}'
    BASE.mkdir(parents=True, exist_ok=True)
    for path in previous.iterdir():
        if path.suffix in ('.BIN', '.DAT', '.45', '.json'):
            shutil.copyfile(path, BASE / path.name)
    original = (ROOT / 'work/source/ps2/SLPS_253.45').read_bytes()
    data = bytearray((BASE / 'SLPS_253.45').read_bytes())
    meta = json.loads((BASE / 'patch.json').read_text())
    assert sha(data) == meta['target_sha256']
    changes = dict(version=VERSION, source_build=SOURCE_VERSION,
                   data_references=[], instruction_words=[], storage=[],
                   draw_stubs=[], description_rows=[], native_font=True,
                   texture_replacement=False, psp_opening_preserved=True)

    english = ['Attr.', 'Skill Search', 'Ability Search', 'Allied Units',
               'Enemy Units', 'Neutral Units', 'Unit Info', 'Edit', 'Info',
               'Will', 'Move', 'Status', 'None', 'Yes', 'Pierce', 'Spread',
               'Null', 'Weaken']
    current = (int(meta['segment_va'], 16) + meta['segment_bytes'] + 15) & ~15
    payload = bytearray()
    targets = {}
    for label in english:
        targets[label] = current + len(payload)
        payload += it.encode(label)
    data, pool = extend(data, meta, payload)
    assert pool == current
    high = (pool + 0x8000) >> 16
    assert all((v + 0x8000) >> 16 == high for v in targets.values())

    def instruction(va, new, expected=None):
        off = va - FILE_BIAS
        old = struct.unpack_from('<I', data, off)[0]
        if expected is not None:
            assert old == expected, (hex(va), hex(old), hex(expected))
        struct.pack_into('<I', data, off, new)
        changes['instruction_words'].append(dict(va=hex(va), old=hex(old), new=hex(new)))

    def high_word(va):
        word = struct.unpack_from('<I', data, va - FILE_BIAS)[0]
        assert word >> 26 == 15
        instruction(va, (word & 0xffff0000) | high)

    def low_word(va, label):
        word = struct.unpack_from('<I', data, va - FILE_BIAS)[0]
        assert word >> 26 == 9
        instruction(va, (word & 0xffff0000) | ((targets[label] - high * 65536) & 65535))

    # Both branch paths share the same high page, including branch-delay uses.
    for site in (0x18f550, 0x18f560):
        high_word(site)
    low_word(0x18f568, 'Ability Search')
    low_word(0x18f570, 'Skill Search')
    for site in (0x147ef8, 0x147f14, 0x147f28, 0x147f38):
        high_word(site)
    for site, label in ((0x147f24, 'Allied Units'), (0x147f30, 'Enemy Units'),
                        (0x147f40, 'Neutral Units'), (0x147f48, 'Unit Info')):
        low_word(site, label)
    # The ammo value used the original 2-character heading's narrow column.
    instruction(0x173db0, 0x24100070, 0x24100050)
    changes['ammo_value_x'] = dict(old=80, new=112, label_x=32)

    labels = {'属性': 'Attr.', '気力': 'Will'}
    for jp, label in labels.items():
        needle = jp.encode('cp932') + b'\0'
        pos = 0
        while (pos := original.find(needle, pos)) >= 0:
            off = pos
            pos += 1
            if not 0x2c5e00 <= off < 0x3c5d00 or original[off - 1]:
                continue
            source = off + FILE_BIAS
            for site in range(0x2c5e00, 0x3c5d00, 4):
                if struct.unpack_from('<I', original, site)[0] == source:
                    old = struct.unpack_from('<I', data, site)[0]
                    struct.pack_into('<I', data, site, targets[label])
                    changes['data_references'].append(dict(site=hex(site + FILE_BIAS),
                        source=hex(source), old=hex(old), target=hex(targets[label]), english=label))

    def storage(va, label, old_bytes):
        off = va - FILE_BIAS
        encoded = it.encode(label)
        assert len(encoded) <= len(old_bytes)
        assert data[off:off + len(old_bytes)] == old_bytes
        data[off:off + len(old_bytes)] = encoded + bytes(len(old_bytes) - len(encoded))
        changes['storage'].append(dict(va=hex(va), english=label, bytes=len(old_bytes)))

    # The weapon attribute formatter copies exactly four full-width characters.
    ui = json.loads((ROOT / 'work/translation/en/ps2/ui_port.en.json').read_text())
    assist = {int(r['target'], 16) for r in ui['texts'] if r['english'] == 'Assist'}
    for va in assist:
        off = int(meta['segment_offset'], 16) + va - int(meta['segment_va'], 16)
        old = it.encode('Assist')
        assert data[off:off + len(old)] == old
        new = it.encode('Asst')
        data[off:off + len(old)] = new + bytes(len(old) - len(new))
        changes['storage'].append(dict(va=hex(va), english='Asst', bytes=len(old), segment=True))
    for va, label in ((0x48fa30, 'Edit'), (0x498d20, 'Will'),
                       (0x498d40, 'Critical'), (0x498d58, 'Skill')):
        off = va - FILE_BIAS
        end = (original.index(0, off) + 4) & ~3
        old = original[off:end]
        storage(va, label, old)

    ks = keystone.Ks(keystone.KS_ARCH_MIPS,
                     keystone.KS_MODE_MIPS64 | keystone.KS_MODE_LITTLE_ENDIAN)

    def append_code(source):
        nonlocal data
        va = (int(meta['segment_va'], 16) + meta['segment_bytes'] + 15) & ~15
        raw = bytes(ks.asm(source, va)[0])
        data, address = extend(data, meta, raw)
        assert va == address
        return address, len(raw)

    # GP-relative labels are invisible to the old LUI/data-pointer translator.
    # Tail-call the native renderer, keeping all coordinates and the caller RA.
    for site, label in ((0x1114f8, 'Status'), (0x11173c, 'Info'),
                        (0x1158a4, 'Will'), (0x115960, 'Move'), (0x115c64, 'Move')):
        ptr = targets[label]
        hi = (ptr + 0x8000) >> 16
        lo = ptr - (hi << 16)
        source = f'''.set noreorder
lui $a1,{hi}
addiu $a1,$a1,{lo}
j 0x130610
nop
'''
        stub, size = append_code(source)
        instruction(site, 0x0c000000 | (stub >> 2), 0x0c000000 | (0x130610 >> 2))
        changes['draw_stubs'].append(dict(site=hex(site), target=hex(stub),
            text_target=hex(ptr), english=label, bytes=size))

    # Translate the cached short weapon flags before calculating right alignment.
    # The stack buffer is 0x100 bytes; full "None" can replace the 2-character copy.
    flags = {'なし': 'None', 'あり': 'Yes', '貫通': 'Pierce', '拡散': 'Spread',
             '無効': 'Null', '弱体': 'Weaken'}
    source = ['.set noreorder', 'lbu $t8,4($a1)', 'bnez $t8,measure', 'nop',
              'lw $t8,0($a1)']
    for n, (jp, label) in enumerate(flags.items()):
        word = struct.unpack('<I', jp.encode('cp932'))[0]
        source += [f'lui $t9,{word >> 16}', f'ori $t9,$t9,{word & 65535}',
                   f'beq $t8,$t9,flag{n}', 'nop']
    source += ['b measure', 'nop']
    for n, (jp, label) in enumerate(flags.items()):
        ptr = targets[label]
        hi = (ptr + 0x8000) >> 16
        lo = ptr - (hi << 16)
        source += [f'flag{n}:', f'lui $t9,{hi}', f'addiu $t9,$t9,{lo}',
                   'move $t8,$a1', f'copy{n}:', 'lbu $at,0($t9)',
                   'sb $at,0($t8)', 'addiu $t9,$t9,1', f'bnez $at,copy{n}',
                   'addiu $t8,$t8,1', 'b measure', 'nop']
    # Use the real VWF width routine rather than the old hardcoded 14/20 advances.
    source += ['measure:', 'move $a0,$s4', 'addiu $sp,$sp,-16',
               'sd $ra,0($sp)', 'jal 0x131ba0', 'nop', 'cvt.w.s $f0,$f0',
               'mfc1 $v0,$f0', 'ld $ra,0($sp)', 'jr $ra', 'addiu $sp,$sp,16']
    flag_source = '\n'.join(source)
    flag_stub, size = append_code(flag_source)
    instruction(0x174be4, 0x0c000000 | (flag_stub >> 2), 0x0c000000 | (0x16b548 >> 2))
    (BASE / 'weapon_flags.asm').write_text(flag_source, encoding='utf8')
    changes['weapon_flags'] = dict(site='0x174be4', target=hex(flag_stub), bytes=size,
                                  labels=list(flags.values()), right_alignment_uses_vwf=True)

    fix = (BASE / 'FIX00.DAT').read_bytes()
    sec = sections(fix, 0)
    database = json.loads((ROOT / 'work/translation/en/ps2/database_port.en.json').read_text())
    widths = {g['character']: g['width'] for g in meta['glyphs']}
    count = sec['Sent'][2]
    appended = bytearray()
    appended_ids = {}
    table_rows = {tag: index(fix, sec[tag][0], sec[tag][2]) for tag in ('XSkl', 'Xabl')}
    current = (int(meta['segment_va'], 16) + meta['segment_bytes'] + 15) & ~15
    for row in database['texts']:
        if row['table'] not in table_rows:
            continue
        # Preserve every condition while keeping the two longest entries
        # within the search footer's three 28-pixel rows.
        overrides = {
            ('Xabl', 6): 'Needs 5+ EN; blocks attacks up to 4000 damage. Field-nullifying or AT Field-neutralizing weapons bypass it. If broken, full damage gets through.',
            ('Xabl', 34): 'Adds Connect beside a power source. While connected, EN fully recovers each player phase; movement is limited to 10 squares from the source.',
        }
        translated = overrides.get((row['table'], row['entry']), row['english'])
        lines = wrap_native(translated, widths)
        assert len(lines) <= 3, (row['table'], row['entry'], lines)
        ids = []
        for line in lines:
            raw = it.encode(line)
            if raw not in appended_ids:
                appended_ids[raw] = (count + len(appended_ids), current + len(appended))
                appended += raw
            ids.append(appended_ids[raw][0])
        table_rows[row['table']][row['entry']] = ids
        changes['description_rows'].append(dict(table=row['table'], entry=row['entry'],
            english=translated, source_english=row['english'], lines=lines, sentence_ids=ids,
            widths=[sum(widths[c] for c in line) for line in lines]))
    data, address = extend(data, meta, appended)
    assert current == address
    sent_off, sent_size, _ = sec['Sent']
    offsets = list(struct.unpack_from(f'<{count}I', fix, sent_off + 12))
    growth = 4 * len(appended_ids)
    offsets = [v if v & 0x80000000 else v + growth for v in offsets]
    offsets += [0x80000000 | ptr for ident, ptr in appended_ids.values()]
    new_count = len(offsets)
    assert new_count < 65536
    sent_payload = fix[sent_off + 12 + 4 * count:sent_off + sent_size]
    replacements = dict(Sent=b'Sent' + struct.pack('<2I', 12 + 4 * new_count + len(sent_payload), new_count)
        + struct.pack(f'<{new_count}I', *offsets) + sent_payload)
    replacements.update({tag: indices(tag, rows) for tag, rows in table_rows.items()})
    rebuilt = bytearray()
    positions = {}
    for tag, (off, size, _) in sec.items():
        positions[tag] = len(rebuilt)
        rebuilt += replacements.get(tag, fix[off:off + size])
        rebuilt += bytes(-len(rebuilt) % 4)
    directory = struct.unpack_from('<19I', fix, sec['Fixh'][0] + 8)
    tags = {off: tag for tag, (off, size, _) in sec.items()}
    struct.pack_into('<19I', rebuilt, positions['Fixh'] + 8, *(positions[tags[v]] for v in directory))
    (BASE / 'FIX00.DAT').write_bytes(rebuilt)
    changes['descriptions'] = dict(width_limit=512, font_size=24,
        new_sentence_rows=len(appended_ids), added_pool_bytes=len(appended),
        source_sha256=sha(fix), target_sha256=sha(rebuilt), numeric_records_preserved=True)

    meta['target_sha256'] = sha(data)
    (BASE / 'SLPS_253.45').write_bytes(data)
    save(BASE / 'patch.json', meta)
    save(BASE / 'ui_details.json', changes)
    inherited = json.loads((BASE / 'ui_fix.json').read_text())
    inherited.update(version=VERSION, source_build=SOURCE_VERSION)
    save(BASE / 'ui_fix.json', inherited)
    save(ROOT / 'work/translation/en/ps2' / f'ui_details_{VERSION}.en.json', changes)
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    info = prepare()
    print(json.dumps(dict(version=VERSION, labels=len(info['data_references']),
                         reflowed_descriptions=len(info['description_rows']))))
    if args.build:
        from verify_ps2_stage30 import verify
        from verify_ps2_prologue_fix import verify as verify_prologue_fix
        from verify_ps2_ui import verify as verify_ui
        from verify_ps2_ui_details import verify as verify_details
        from package_ps2_stage30 import build
        verify(BASE, VERSION)
        verify_prologue_fix(BASE, VERSION)
        verify_ui(BASE, VERSION)
        verify_details(BASE, VERSION)
        build(BASE, VERSION, SOURCE_VERSION, ('FACEPACK.BIN',))
