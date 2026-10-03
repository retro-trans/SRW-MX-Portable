"""Native 4x Latin atlas and renderer patch; no emulator texture replacement.

Keeps the 1x VWF advances and Japanese path. Extends the existing PRX load
segment after its original memory allocation, retaining zero-initialized BSS.
Latin rows use legal 512x128 PSP textures with 72px cells, seven per row.
"""
import math
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import keystone
import make_latin_font as glyphs
import vwf_patch as vwf

GLYPH_CALLS = [0xAED64, 0xAF240, 0xAF7B0, 0xAFC80]
HEIGHT_PATCHES = {0xAEF48: 'lw $a1, 0x34($sp)', 0xAF974: 'lw $a1, 0x34($sp)',
                  0xAF418: 'lw $a0, 0x40($sp)', 0xAFE58: 'lw $a0, 0x40($sp)'}


def atlas():
    low_font = ImageFont.truetype(glyphs.FONT, glyphs.SIZE)
    high_font = ImageFont.truetype(glyphs.FONT, glyphs.SIZE * 4)
    index = bytearray(384)
    rows = math.ceil(len(glyphs.CHARS) / 7)
    image = Image.new('L', (512, rows * 72 + 56))
    for number, (code, char) in enumerate(glyphs.CHARS.items()):
        index[glyphs.slot(code)] = number + 1
        if char == ' ':
            continue
        low = Image.new('L', (18, 18))
        low.putdata([value for line in glyphs.render(char, low_font) for value in line])
        target = low.getbbox()
        # Render before packing: 60px descenders extend below a 72px cell.
        # Cropping the source to the cell first silently cuts g/j/p/q/y/comma.
        high = Image.new('L', (96, 96))
        ascent, _ = high_font.getmetrics()
        ImageDraw.Draw(high).text((4, glyphs.BASELINE * 4 - ascent), char, font=high_font, fill=255)
        bounds = high.getbbox()
        assert target and bounds, char
        assert bounds[0] >= 0 and bounds[1] >= 0 and bounds[2] < 96 and bounds[3] < 96, char
        full_mask = high_font.getmask(char).getbbox()
        assert (bounds[2] - bounds[0], bounds[3] - bounds[1]) == (
            full_mask[2] - full_mask[0], full_mask[3] - full_mask[1]), 'Clipped source glyph: ' + char
        # Keep the exact original ink placement/cropping contract despite size-dependent hinting.
        ink = high.crop(bounds).resize(((target[2] - target[0]) * 4,
                                       (target[3] - target[1]) * 4), Image.LANCZOS)
        x, y = (number % 7) * 72 + target[0] * 4, (number // 7) * 72 + target[1] * 4
        image.paste(ink, (x, y))
    values = bytes(image.getdata())
    quantized = [0 if value < 40 else max(6, min(14, 6 + value * 9 // 255)) for value in values]
    data = bytes(quantized[i] | quantized[i + 1] << 4 for i in range(0, len(quantized), 2))
    return data, bytes(index), image


def assemble(table_va, index_va, atlas_va, code_va):
    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 + keystone.KS_MODE_LITTLE_ENDIAN)
    def lookup(label, location):
        hi, lo = (location + 0x8000) >> 16, location - (((location + 0x8000) >> 16) << 16)
        return [label + ':', 'addiu $t9, $t9, -0x4000', 'addiu $t9, $t9, -0x4140',
                'sltiu $at, $t9, 0x1c0', 'beqz $at, ' + label + '_none',
                'srl $at, $t9, 8', 'sll $at, $at, 6', 'subu $t9, $t9, $at',
                'lui $at, %d' % hi, 'addu $at, $at, $t9', 'lbu $t9, %d($at)' % lo,
                'jr $ra', label + '_none:', 'move $t9, $zero', 'jr $ra']
    src = lookup('lookup', table_va) + lookup('lookup_index', index_va)
    previous_base = vwf._base
    try:
        vwf._base = 0
        src += vwf.pre_stubs()
    finally:
        vwf._base = previous_base
    for n, site in enumerate(vwf.SITES):
        if site['kind'].startswith('w'):
            previous_base = vwf._base
            try:
                vwf._base = 0
                src += ['stub%d:' % n] + vwf.stub(site, n)
            finally:
                vwf._base = previous_base
            continue
        flag, integer = site['flag'], site['kind'] == 'rint'
        src += ['stub%d:' % n]
        src += (['addiu $t9, $zero, 18', 'sw $t9, 0x34($sp)'] if integer else
                ['lui $t9, 0x4190', 'sw $t9, 0x40($sp)'])
        src += vwf.load_code(site['code']) + ['mtlo $ra', 'bal lookup', 'mflo $ra',
                'beqz $t9, fb%d' % n, 'andi $at, $t9, 0x1f', 'srl $t9, $t9, 5',
                'sll $t9, $t9, 2', 'move %s, $t9' % site['ureg'], 'sll $at, $at, 2']
        src += ['sw $at, %d($sp)' % site['tex'][1]] if integer else ['move %s, $at' % site['tex'][1]]
        src += ['srl $at, $at, 2']
        src += vwf.size_from_height(site, n)[0]
        if integer:
            w = site['wreg']
            src += ['mult $at, ' + w, 'mflo ' + w, 'addiu %s, %s, 9' % (w, w),
                    'addiu $at, $zero, 18', 'div $zero, %s, $at' % w, 'mflo ' + w]
        else:
            w = site['wreg']
            src += ['mtc1 $at, $f0', 'cvt.s.w $f0, $f0', 'mul.s %s, %s, $f0' % (w, w),
                    'lui $at, 0x4190', 'mtc1 $at, $f0', 'div.s %s, %s, $f0' % (w, w)]
        src += vwf.load_code(site['code']) + ['mtlo $ra', 'bal lookup_index', 'mflo $ra',
                'addiu $t9, $t9, -1', 'addiu $at, $zero, 7', 'divu $zero, $t9, $at',
                'mfhi $t9', 'sll $at, $t9, 3', 'addu $at, $at, $t9', 'sll $at, $at, 3',
                'addu %s, %s, $at' % (site['ureg'], site['ureg']),
                'addiu $a1, $zero, 512', 'addiu $a2, $zero, 128']
        src += (['addiu $t9, $zero, 72', 'sw $t9, 0x34($sp)'] if integer else
                ['lui $t9, 0x4290', 'sw $t9, 0x40($sp)'])
        src += ['j %d' % site['skip'], 'fb%d:' % n, 'beqz %s, ex%d' % (flag, n),
                'j %d' % site['cls'], 'ex%d:' % n, 'j %d' % site['skip']]
    hi, lo = (atlas_va + 0x8000) >> 16, atlas_va - (((atlas_va + 0x8000) >> 16) << 16)
    src += ['latin_glyph:'] + vwf.load_code(('reg', '$a1'))
    src += ['mtlo $ra', 'bal lookup_index', 'mflo $ra', 'beqz $t9, original_glyph',
            'addiu $t9, $t9, -1', 'addiu $at, $zero, 7', 'divu $zero, $t9, $at',
            'mflo $t9', 'sll $t8, $t9, 3', 'addu $t9, $t8, $t9', 'sll $t9, $t9, 11',
            'lui $at, %d' % hi, 'addu $at, $at, $t9', 'addiu $v0, $at, %d' % lo,
            'lbu $t8, 0($a1)', 'lbu $at, 1($a1)', 'sll $t8, $t8, 8', 'or $t8, $t8, $at',
            'addiu $t8, $t8, -0x4000', 'addiu $t8, $t8, -0x4140',
            'srl $at, $t8, 8', 'sll $at, $at, 6', 'subu $t8, $t8, $at', 'sw $t8, 0($a2)',
            'jr $ra', 'original_glyph:', 'j 0xb07e8']
    source = '\n'.join(src)
    code = bytes(ks.asm(source, code_va)[0])
    entries = {}
    # Recover labels from a probe jump appended after the complete source.
    for label in ['latin_glyph'] + ['stub%d' % n for n in range(8)] + ['pre%d' % n for n in range(len(vwf.PRE))]:
        probe = bytes(ks.asm(source + '\nj ' + label, code_va)[0])
        word = struct.unpack_from('<I', probe, len(code))[0]
        entries[label] = (word & 0x3ffffff) << 2
    hooks = [(site['hook'], bytes(ks.asm('j %d' % entries['stub%d' % n], site['hook'])[0])[:4])
             for n, site in enumerate(vwf.SITES)]
    hooks += [(p['hook'], bytes(ks.asm('j %d' % entries['pre%d' % n], p['hook'])[0])[:4])
              for n, p in enumerate(vwf.PRE)]
    hooks += [(call, bytes(ks.asm('jal %d' % entries['latin_glyph'], call)[0])[:4]) for call in GLYPH_CALLS]
    hooks += [(offset, bytes(ks.asm(instruction, offset)[0])[:4]) for offset, instruction in HEIGHT_PATCHES.items()]
    relocs = [(site['hook'], 4) for site in vwf.SITES] + [(p['hook'], 4) for p in vwf.PRE]
    words = struct.unpack('<%dI' % (len(code) // 4), code)
    for n, word in enumerate(words):
        op = word >> 26
        if op in (2, 3):
            assert (word & 0x3ffffff) << 2 < code_va + len(code), 'Unrelocated absolute jump'
            relocs.append((code_va + n * 4, 4))
        elif op == 15 and ((word >> 16) & 31) == 1:
            # Address loads use $at. Float constant loads also use $at but mtc1 is not a LO16.
            for step in [1, 2]:
                following = words[n + step] if n + step < len(words) else 0
                if following >> 26 in (9, 36) and ((following >> 21) & 31) == 1:
                    relocs.extend([(code_va + n * 4, 5), (code_va + (n + step) * 4, 6)])
                    break
    return code, hooks, relocs, source


def patch_boot(boot, static2, evidence_dir):
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    atlas_data, index, preview = atlas()
    table = vwf.width_table(static2)
    phoff = struct.unpack_from('<I', boot, 28)[0]
    assert struct.unpack_from('<H', boot, 44)[0] == 1
    kind, offset, va, pa, filesz, memsz, flags, align = struct.unpack_from('<8I', boot, phoff)
    assert kind == 1 and offset == 0x60 and va == 0 and memsz >= filesz
    start = (memsz + 127) & ~127
    table_va, index_va, atlas_va = start, start + 384, start + 768
    code_va = (atlas_va + len(atlas_data) + 15) & ~15
    code, hooks, relocs, source = assemble(table_va, index_va, atlas_va, code_va)
    payload = table + index + atlas_data + bytes(code_va - atlas_va - len(atlas_data)) + code
    new_size = start + len(payload)
    old_end = offset + filesz
    delta = new_size - filesz
    data = bytearray(boot[:old_end] + bytes(start - filesz) + payload + boot[old_end:])
    struct.pack_into('<2I', data, phoff + 16, new_size, new_size)
    old_shoff = struct.unpack_from('<I', boot, 32)[0]
    shoff = old_shoff + delta
    struct.pack_into('<I', data, 32, shoff)
    shsize, count, string_index = struct.unpack_from('<3H', boot, 46)
    for n in range(count):
        header = shoff + n * shsize
        section_type = struct.unpack_from('<I', data, header + 4)[0]
        old_offset = struct.unpack_from('<I', data, header + 16)[0]
        if old_offset >= old_end and section_type != 8:
            struct.pack_into('<I', data, header + 16, old_offset + delta)
    strings = struct.unpack_from('<I', data, shoff + string_index * shsize + 16)[0]
    for n in range(count):
        header = shoff + n * shsize
        name = struct.unpack_from('<I', data, header)[0]
        if data[strings + name:strings + name + 10] == b'.rel.text\0':
            reloc_header = header
            reloff, relsize = struct.unpack_from('<2I', data, header + 16)
            break
    else:
        raise ValueError('Missing .rel.text')
    existing = [struct.unpack_from('<2I', data, reloff + n) for n in range(0, relsize, 8)]
    assert all(any(location == call for location, _ in existing) for call in GLYPH_CALLS)
    assert not any(location == site['hook'] for location, _ in existing for site in vwf.SITES)
    merged = existing + relocs
    new_reloff = (len(data) + 3) & ~3
    data.extend(bytes(new_reloff - len(data)))
    data.extend(b''.join(struct.pack('<2I', *row) for row in merged))
    struct.pack_into('<2I', data, reloc_header + 16, new_reloff, len(merged) * 8)
    for location, patch in hooks:
        data[offset + location:offset + location + len(patch)] = patch
    assert data[offset + filesz:offset + memsz] == bytes(memsz - filesz)
    assert data[offset + atlas_va:offset + atlas_va + len(atlas_data)] == atlas_data
    preview.save(evidence_dir / 'native_latin_4x.png')
    (evidence_dir / 'native_renderer.asm').write_text(source, encoding='utf-8')
    (evidence_dir / 'atlas_4x.bin').write_bytes(atlas_data)
    (evidence_dir / 'layout.json').write_text(json.dumps(dict(
        original_filesz=filesz, original_memsz=memsz, new_size=new_size,
        table_va=table_va, index_va=index_va, atlas_va=atlas_va, code_va=code_va,
        atlas_bytes=len(atlas_data), code_bytes=len(code), relocations=relocs,
        cells_per_row=7, cell_size=72, texture_width=512, texture_height=128), indent=1), encoding='utf-8')
    print('Native 4x Latin atlas: %d bytes; PRX memory growth: %d bytes' % (len(atlas_data), new_size - memsz))
    return bytes(data)
