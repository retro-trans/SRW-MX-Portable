"""Native Genei LateGo 4x VWF patch for the original SLPS-25345 executable.

PS2-only hooks; the PSP executable is never modified. Glyphs are loaded through
an added ELF segment and uploaded through the game's existing GIF/DMA path.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import struct

import keystone
from PIL import Image, ImageDraw, ImageFont
import make_latin_font as latin

ROOT = Path(__file__).resolve().parent.parent
FILE_BIAS = 0xff000
CELL = 24
HIGH_CELL = 96
GLYPH_BYTES = HIGH_CELL * HIGH_CELL // 2
SEGMENT_VA = 0x715000

SITES = [
    dict(name='R1', hook=0x1307dc, flag='$v0', default='move $s7, $s4',
         code='$s3', ctx='$s1', out='$a2', kind='int', crop='$s7', height='$s4',
         bearing='sw $t9, 0x40($sp)', fallback=0x1307e4, resume=0x130878),
    dict(name='R2', hook=0x130b74, flag='$v0', default='move $s5, $s4',
         code='$s2', ctx='$s1', out='$f2', kind='float', crop='$s5', height='$s4',
         bearing='move $s7, $t9', fallback=0x130b7c, resume=0x130bf8),
    dict(name='R3', hook=0x130f54, flag='$v0', default='move $s7, $s3',
         code=0x30, ctx='$s1', out='$s0', kind='int', crop='$s7', height='$s3',
         bearing='sw $t9, 0x50($sp)', fallback=0x130f5c, resume=0x130ff0),
    dict(name='R4', hook=0x1312f4, flag='$v0', default='move $s6, $s3',
         code=0x30, ctx='$s1', out='$f20', kind='float', crop='$s6', height='$s3',
         bearing='move $fp, $t9', fallback=0x1312fc, resume=0x131378),
    dict(name='W1', hook=0x1319f8, flag='$t2', code='$a1', ctx=None,
         out='$a2', kind='int', height_saved=True, fallback=0x131a00,
         resume=0x131a6c, fixed=0x131a70),
    dict(name='W2', hook=0x131afc, flag='$v0', code=0, ctx='$s2',
         out='$a1', kind='int', fallback=0x131b00, resume=0x131b6c),
    dict(name='W3', hook=0x131bf8, flag='$a3', default='mov.s $f0, $f3',
         code='$a1', ctx=None, out='$f0', kind='float', height_saved=True,
         fallback=0x131c00, resume=0x131c40),
    dict(name='W4', hook=0x131cf0, flag='$v0', default='lwc1 $f0, ($s1)',
         code=0, ctx='$s1', out='$f0', kind='float', fallback=0x131cf8,
         resume=0x131d38),
]


def rasterize(baseline_fix=True):
    low_font = ImageFont.truetype(latin.FONT, 20)
    high_font = ImageFont.truetype(latin.FONT, 80)
    table = bytearray(384 * 4)
    data = bytearray()
    preview = Image.new('L', (HIGH_CELL * 12, HIGH_CELL * 8))
    metadata = []
    for index, (sjis, char) in enumerate(latin.CHARS.items(), 1):
        low = Image.new('L', (40, 40))
        if char != ' ':
            ImageDraw.Draw(low).text((1, 19 - low_font.getmetrics()[0]), char,
                                     font=low_font, fill=255)
        bounds = low.getbbox()
        glyph = Image.new('L', (HIGH_CELL, HIGH_CELL))
        left, width = 0, 7
        if bounds:
            assert 0 <= bounds[0] < bounds[2] <= CELL, (char, bounds)
            assert 0 <= bounds[1] < bounds[3] <= CELL, (char, bounds)
            # The GS quad uses its crop width as the absolute right UV,
            # not a length added to the left bearing. Pack Latin ink at x=0
            # so the complete letter fits the sampled [0,width) interval.
            left, width = 0, bounds[2] - bounds[0] + 1
            if char in latin.DIGITS:
                left, width = 0, 13
                target_x = (13 - (bounds[2] - bounds[0])) // 2
            else:
                target_x = 0
            source = Image.new('L', (128, 128))
            # Keep one high-resolution baseline for the whole alphabet. The
            # legacy atlas resized each glyph to its independently hinted 20px
            # bounding box, making otherwise aligned bottoms differ by 4px.
            # At baseline 74 the deepest descender leaves two guard rows.
            baseline = 74 if baseline_fix else 76
            ImageDraw.Draw(source).text((4, baseline - high_font.getmetrics()[0]), char,
                                        font=high_font, fill=255)
            full = source.getbbox()
            mask = high_font.getmask(char).getbbox()
            assert full and full[2] < 128 and full[3] < 128
            assert (full[2]-full[0], full[3]-full[1]) == (mask[2]-mask[0], mask[3]-mask[1]), char
            target_height = full[3]-full[1] if baseline_fix else (bounds[3]-bounds[1])*4
            target_y = full[1] if baseline_fix else bounds[1]*4
            ink = source.crop(full).resize(((bounds[2]-bounds[0])*4,
                                           target_height), Image.LANCZOS)
            glyph.paste(ink, (target_x*4, target_y))
            if baseline_fix:
                assert full[3] <= HIGH_CELL-2, (char, full, 'descender guard')
                assert target_y == full[1] and ink.height == full[3]-full[1]
        assert width < 32 and left < 8
        ink_bounds=glyph.getbbox()
        assert not ink_bounds or (ink_bounds[0]>=left*4 and ink_bounds[2]<=width*4
                                  and ink_bounds[1]>=left*4 and ink_bounds[3]<=HIGH_CELL),char
        struct.pack_into('<4B', table, latin.slot(sjis)*4, width, left, index, 0)
        pixels = [0 if x < 40 else min(15, 6 + x*10//255) for x in glyph.getdata()]
        data += bytes(pixels[n] | pixels[n+1] << 4 for n in range(0, len(pixels), 2))
        preview.paste(glyph, (((index-1)%12)*HIGH_CELL, ((index-1)//12)*HIGH_CELL))
        entry=dict(character=char, sjis=hex(sjis), width=width, left=left,
                   index=index, source_clipping_checked=True,uv_clipping_checked=True)
        if baseline_fix:
            entry.update(baseline=74,ink_bounds=ink_bounds,
                         source_bounds=full if bounds else None,
                         vertical_rescaling=False)
        metadata.append(entry)
    return bytes(table), bytes(data), preview, metadata


def assemble(table_va, atlas_va, state_va, code_va, count, uniform_aspect=False):
    ks = keystone.Ks(keystone.KS_ARCH_MIPS,
                     keystone.KS_MODE_MIPS64 | keystone.KS_MODE_LITTLE_ENDIAN)
    src = []
    labels = []

    def address(register, va):
        return ['lui %s, %d' % (register, (va+0x8000)>>16),
                'addiu %s, %s, %d' % (register, register, va-(((va+0x8000)>>16)<<16))]

    def lookup(code, miss):
        if isinstance(code, int):
            out = ['lbu $t9, %d($sp)' % code, 'lbu $t8, %d($sp)' % (code+1)]
        else:
            out = ['lbu $t9, 0(%s)' % code, 'lbu $t8, 1(%s)' % code]
        # Restrict to the original PSP Latin whitelist, not all Shift-JIS.
        out += ['sll $t9, $t9, 8', 'or $t9, $t9, $t8',
                'addiu $t9, $t9, -0x4000', 'addiu $t9, $t9, -0x4140',
                'sltiu $t8, $t9, 0x1c0', 'beqz $t8, '+miss,
                'srl $t8, $t9, 8', 'sll $t8, $t8, 6', 'subu $t9, $t9, $t8',
                'sll $t9, $t9, 2'] + address('$at', table_va)
        out += ['addu $at, $at, $t9', 'lbu $t8, 2($at)', 'beqz $t8, '+miss,
                'lbu $t8, 0($at)', 'lbu $t9, 1($at)']
        return out

    def scale(site, name):
        if site.get('height_saved'):
            out = ['mov.s $f10, $f8']
            if site['kind']=='int':
                out += ['mtc1 %s, $f9' % site['out'], 'cvt.s.w $f9, $f9']
            else:
                out += ['mov.s $f9, $f3']
        else:
            out = ['lwc1 $f9, 0(%s)' % site['ctx'],
                   'lwc1 $f10, 4(%s)' % site['ctx']]
        threshold = struct.unpack('<I', struct.pack('<f', 10/13))[0]
        if uniform_aspect:
            # Latin uses the smaller native cell dimension for both axes.
            # Dialogue cells are 20x30; widening advances to 30 causes the
            # game's bounded-line renderer to squeeze them back horizontally.
            # Numeric widgets use a 12x24 half-width ASCII context. Its
            # width is the original fixed digit advance, not a small font.
            # Latin's own digit advance already supplies that half width.
            out += ['add.s $f11, $f9, $f9', 'c.eq.s $f11, $f10',
                    'bc1t '+name+'_half_width',
                    'c.olt.s $f10, $f9', 'bc1f '+name+'_size',
                    name+'_half_width:', 'mov.s $f9, $f10', name+'_size:']
            if name.startswith('R'):
                out += address('$at', state_va) + ['swc1 $f9, 4($at)']
        else:
            out += address('$at', threshold) + ['mtc1 $at, $f11',
                # R5900 C.LT uses function 0x34 (MIPS C.OLT), not the
                # generic MIPS signaling C.LT encoding 0x3c.
                'mul.s $f11, $f10, $f11', 'c.olt.s $f9, $f11',
                'bc1t '+name+'_height', 'c.olt.s $f10, $f9',
                'bc1f '+name+'_size', name+'_height:', 'mov.s $f9, $f10',
                    name+'_size:']
        if site['kind']=='int':
            out += ['cvt.w.s $f9, $f9', 'mfc1 %s, $f9' % site['out'],
                    'mult $t8, %s' % site['out'], 'mflo %s' % site['out'],
                    'addiu $at, $zero, 24', 'div $zero, %s, $at' % site['out'],
                    'mflo %s' % site['out']]
        else:
            out += ['mtc1 $t8, $f11', 'cvt.s.w $f11, $f11',
                    'mul.s $f9, $f9, $f11', 'lui $at, 0x41c0',
                    'mtc1 $at, $f11', 'div.s %s, $f9, $f11' % site['out']]
        return out

    for site in SITES:
        name = site['name']; labels.append(name)
        src += [name+':'] + ([site['default']] if site.get('default') else [])
        src += lookup(site['code'], name+'_original') + scale(site, name)
        if name.startswith('R'):
            src += ['sll $t9, $t9, 2', site['bearing'], 'sll %s, $t8, 2' % site['crop'],
                    'addiu %s, $zero, 96' % site['height']]
        src += ['j %d' % site['resume'], name+'_original:']
        if 'fixed' in site:
            src += ['bnez %s, %s_class' % (site['flag'], name),
                    'addiu $a1, $a1, 2', 'j %d' % site['fixed'], name+'_class:',
                    'j %d' % site['fallback']]
        else:
            src += ['beqz %s, %s_fixed' % (site['flag'], name),
                    'j %d' % site['fallback'], name+'_fixed:', 'j %d' % site['resume']]

    for name, width, height, resume in [('PRE1','$f0','$f8',0x1319e8),
                                       ('PRE3','$f3','$f8',0x131bd0)]:
        labels.append(name)
        src += [name+':', 'lwc1 %s, 0($a0)' % width,
                'lwc1 %s, 4($a0)' % height, 'j %d' % resume]
        if name=='PRE1':
            src.insert(len(src)-1, 'ori $t3, $zero, 0x889e')
        else:
            src.insert(len(src)-1, 'ori $t0, $zero, 0x889e')

    labels.append('GLYPH')
    src += ['GLYPH:'] + lookup('$a1','GLYPH_original')
    src += ['lbu $t8, 2($at)'] + address('$t9',state_va)
    src += ['sw $t8, 0($t9)', 'addiu $t8, $t8, -1',
            'sll $t9, $t8, 3', 'addu $t9, $t9, $t8', 'sll $t9, $t9, 9']
    src += address('$v0',atlas_va) + ['addu $v0, $v0, $t9', 'jr $ra',
            'GLYPH_original:'] + address('$t9',state_va)
    src += ['sw $zero, 0($t9)', 'addiu $sp, $sp, -0x10',
            'ori $v1, $zero, 0x8444', 'j 0x131d80']

    labels.append('UPLOAD')
    src += ['UPLOAD:'] + address('$t8',atlas_va)
    src += ['sltu $t9, $a1, $t8', 'bnez $t9, UPLOAD_original']
    src += address('$t8',atlas_va+count*GLYPH_BYTES)
    src += ['sltu $t9, $a1, $t8', 'beqz $t9, UPLOAD_original',
            'addiu $a2, $zero, 96', 'UPLOAD_original:',
            'addiu $sp, $sp, -0xa0', 'sd $s1, 0x78($sp)', 'j 0x12f720']

    labels.append('DRAW')
    src += ['DRAW:'] + address('$t9',state_va)
    src += ['lw $t8, 0($t9)', 'beqz $t8, DRAW_original', 'addiu $a1, $zero, 96']
    if uniform_aspect:
        src += ['lwc1 $f10, 4($t9)', 'add.s $f15, $f13, $f10',
                'add.s $f19, $f17, $f10']
    src += ['DRAW_original:', 'addiu $sp, $sp, -0x3a0',
            'lw $v0, 0x3c0($sp)', 'j 0x12f8c0']
    for name, va, reg, value, shifted in [('TEXA',0x12fa18,'$v0',0xa000,17),
                                         ('TEXB',0x12fa20,'$v1',0x8280,19),
                                         ('TEXC',0x1300e0,'$v0',0xa000,17),
                                         ('TEXD',0x1300e8,'$v1',0x8280,19)]:
        labels.append(name)
        src += [name+':'] + address('$t9',state_va)
        src += ['lw $t8, 0($t9)', 'beqz $t8, '+name+'_original',
                'ori %s, $zero, %d' % (reg, 0xe000 if shifted==17 else 0x8380),
                'j '+name+'_shift', name+'_original:', 'ori %s, $zero, %d' % (reg,value),
                name+'_shift:', 'dsll %s, %s, %d' % (reg,reg,shifted), 'j %d' % (va+8)]
    source='\n'.join(src)
    # LLVM's MIPS64 assembler names t0..t7 according to N64. The game uses
    # the EE/EABI register numbers (8..15); use explicit numbers for these.
    source=re.sub(r'\$t([0-7])\b',lambda m:'$'+str(8+int(m.group(1))),source)
    code=bytes(ks.asm(source,code_va)[0]);entries={}
    for label in labels:
        probe=bytes(ks.asm(source+'\nj '+label,code_va)[0])
        entries[label]=(struct.unpack_from('<I',probe,len(code))[0]&0x3ffffff)<<2
    hooks=[(s['hook'],s['name']) for s in SITES]
    hooks += [(0x1319e0,'PRE1'),(0x131bc8,'PRE3'),(0x131d78,'GLYPH'),
              (0x12f718,'UPLOAD'),(0x12f8b8,'DRAW'),(0x12fa18,'TEXA'),
              (0x12fa20,'TEXB'),(0x1300e0,'TEXC'),(0x1300e8,'TEXD')]
    return code, entries, [(va,bytes(ks.asm('j %d'%entries[n],va)[0]),n) for va,n in hooks], source


def patch_elf(original, evidence, baseline_fix=True):
    original=bytes(original);data=bytearray(original);evidence=Path(evidence)
    evidence.mkdir(parents=True,exist_ok=True)
    assert data[:16]==bytes.fromhex('7f454c46010101000000000000000000')
    assert struct.unpack_from('<H',data,44)[0]==3
    assert data[148:180]==bytes(32)
    assert struct.unpack_from('<I',data,0x131d78-FILE_BIAS)[0]==0x27bdfff0
    table,atlas,preview,meta=rasterize(baseline_fix=baseline_fix)
    table_va=SEGMENT_VA;state_va=table_va+len(table);atlas_va=(state_va+16+127)&~127
    code_va=atlas_va+len(atlas)
    code,entries,hooks,source=assemble(table_va,atlas_va,state_va,code_va,len(meta))
    payload=table+bytes(atlas_va-table_va-len(table))+atlas+code
    end=(SEGMENT_VA+len(payload)+127)&~127
    assert end<0x800000, 'Would overlap original STATIC/font region'
    applied=[]
    for va,patch,name in hooks:
        assert len(patch)==8,(name,len(patch))
        off=va-FILE_BIAS;old=bytes(data[off:off+8]);data[off:off+8]=patch
        applied.append(dict(name=name,va=hex(va),old=old.hex(),new=patch.hex(),target=hex(entries[name])))
    # InitHeap must begin after the new segment. Original BSS clear boundary stays.
    hi=(end+0x8000)>>16;lo=end-(hi<<16)
    for va,word in [(0x100180,0x3c040000|hi),(0x100188,0x24840000|(lo&65535))]:
        off=va-FILE_BIAS;old=bytes(data[off:off+4]);patch=struct.pack('<I',word)
        data[off:off+4]=patch
        applied.append(dict(name='InitHeap',va=hex(va),old=old.hex(),new=patch.hex()))
    offset=(len(data)+4095)&~4095
    data += bytes(offset-len(data))+payload
    struct.pack_into('<8I',data,148,1,offset,SEGMENT_VA,SEGMENT_VA,len(payload),len(payload),7,4096)
    struct.pack_into('<H',data,44,4)
    preview.save(evidence/'atlas.png');(evidence/'hooks.asm').write_text(source,encoding='utf8')
    report=dict(platform='PS2',edition='SLPS-25345',native_font=True,texture_replacement=False,
                glyph_cell=24,high_glyph_cell=96,raster_em=80,glyph_count=len(meta),
                source_sha256=hashlib.sha256(original).hexdigest(),
                target_sha256=hashlib.sha256(data).hexdigest(),segment_va=hex(SEGMENT_VA),
                segment_offset=hex(offset),segment_bytes=len(payload),heap_start=hex(end),
                table_va=hex(table_va),atlas_va=hex(atlas_va),state_va=hex(state_va),
                code_va=hex(code_va),code_bytes=len(code),hooks=applied,glyphs=meta)
    if baseline_fix:
        report.update(font_revision='shared_high_resolution_baseline',baseline=74,
                      vertical_glyph_rescaling=False,descender_guard_rows=2)
    (evidence/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return bytes(data),report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source');p.add_argument('output');p.add_argument('evidence')
    a=p.parse_args();out=Path(a.output)
    if out.exists():raise FileExistsError(out)
    data,report=patch_elf(Path(a.source).read_bytes(),a.evidence);out.write_bytes(data)
    print(json.dumps({k:report[k] for k in ('glyph_count','segment_bytes','heap_start','target_sha256')},indent=2))
