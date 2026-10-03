"""Variable-width font (VWF) patch for SRW MX Portable (ULJS00041) BOOT.BIN.

How the game draws text (see docs/vwf.md):
  font atlas  STATIC2_ADD.BIN +0x40000, 4bpp, 256 px wide, 18x18 cells, 14 per row,
              slot = (sjis-0x8140) - ((sjis-0x8140)>>8)*64 for lead bytes 0x81-0x98
  4 renderers (0xAEB08, 0xAEFF4, 0xAF548, 0xAFA24) and 4 width functions
  (0xB03E4, 0xB04D8, 0xB061C, 0xB06E0) compute each glyph's advance from the font size,
  optionally scaled by a character class when ctx+0x2C ("proportional") is set.

The patch: every site jumps (j, never jal - some are leaf functions) to a stub that looks the
glyph up in a 384-byte width table (slots of lead bytes 0x81/0x82: punctuation, digits, A-Z, a-z).
Entry byte = W | L<<5 (W = cell columns to show incl. 1px spacing, L = left bearing).
If W != 0: texture u += L, texture width = W, draw width/advance = W*size/18 (glyph is cropped,
not squashed). If W == 0 the original code runs unchanged, so Japanese text is untouched.
The stubs and table live in dead library code at 0x250944 (0x848 bytes). (0xE4EAC looked unused
but is called once at startup from code in .data - do not use it.)
BOOT.BIN is a relocatable PRX: the build assembles at base 0 and replaces the unused function's
relocation entries with ones for our jumps / table address (patch_boot). The live mode writes
absolute code for the module loaded at 0x08804000.

usage:
  python vwf_patch.py build <STATIC2_ADD.BIN> <BOOT.BIN in> <BOOT.BIN out>
  python vwf_patch.py live  <STATIC2_ADD.BIN>          (write into a running PPSSPP via debugger)
  python vwf_patch.py table <STATIC2_ADD.BIN> <png>     (preview the width table)
"""
import os, struct, sys
import keystone

BASE = 0x08804000          # main module load address
CAVE = 0x250944            # dead library code: no relocation in any table targets it, no branch
CAVE_SIZE = 0x848          # or call word anywhere in the file points into it (see docs/vwf.md)
TABLE = CAVE               # 384 bytes
CODE = CAVE + 0x180
ATLAS = 0x40000            # in STATIC2_ADD.BIN
SPACE_W = 5                # width of the full-width space 0x8140 (word spacing)

# site: hook vaddr (a 'beqz flag, SKIP' whose delay slot is kept), continuation addresses, how to
# read the 2-byte code, and how to apply W/L.
SITES = [
    # renderers (int width)
    dict(name='R1 drawString', hook=0xAEDC4, skip=0xAEEB4, cls=0xAEDCC, flag='$v1',
         code=('reg', '$s4'), kind='rint', wreg='$s1', ureg='$s2', tex=('sp', 0x38), hctx='$s5'),
    dict(name='R3', hook=0xAF810, skip=0xAF900, cls=0xAF818, flag='$v1',
         code=('sp', 0x4C), kind='rint', wreg='$s0', ureg='$s1', tex=('sp', 0x38), hctx='$s5'),
    # renderers (float width)
    dict(name='R2', hook=0xAF294, skip=0xAF348, cls=0xAF29C, flag='$v1',
         code=('reg', '$s2'), kind='rflt', wreg='$f20', ureg='$s0', tex=('reg', '$s5'), hctx='$s3'),
    dict(name='R4', hook=0xAFCD4, skip=0xAFD88, cls=0xAFCDC, flag='$v1',
         code=('sp', 0x4C), kind='rflt', wreg='$f20', ureg='$s0', tex=('reg', '$s5'), hctx='$s3'),
    # width functions
    dict(name='W1', hook=0xB0450, skip=0xB04C0, cls=0xB0458, flag='$a0',
         code=('lead', '$t8', '$a1'), kind='wint', wreg='$a3', size='$a2', hctx='$f8'),
    dict(name='W2', hook=0xB052C, skip=0xB05F0, cls=0xB0534, flag='$v0',
         code=('sp', 0x1C), kind='wint', wreg='$a1', size='$a1', hctx='$s2'),
    dict(name='W3', hook=0xB067C, skip=0xB06C8, cls=0xB0684, flag='$a3',
         code=('lead', '$t0', '$a1'), kind='wflt', wreg='$f4', size='$f5', ftmp='$f6', hctx='$f8'),
    dict(name='W4', hook=0xB0730, skip=0xB07BC, cls=0xB0738, flag='$v0',
         code=('sp', 0x2C), kind='wflt', wreg='$f2', size='$f2', ftmp='$f0', hctx='$s1'),
]
# hctx: where the stub finds the text context's font HEIGHT (ctx+0xC): the register holding the
# context, or '$f8' where a PRE stub saved the height (W1 and W3 reuse $a0 before their loop).
# Many screens draw values with a font much narrower than it is tall (10x15, 10x16, 12x16): the
# Japanese game squeezes full-width glyphs into half-width ones that way. Latin glyphs are already
# narrow, so when width/height < 10/13 (10x15 status values, 10x16 weapon values, since 0.3.3 also
# 12x16 screen tabs) they are scaled by the height instead of the width (normal proportions; digits
# W=10 then advance 10*16/18 = 9 px instead of 6). Fonts closer to square (14x18 library text,
# 10x13, 14x16 labels, 15x15) keep the width, so text wrapped and fitted to them does not move.
# Since 0.2.2 (cut-off 0.7 until 0.3.3).
# Fonts WIDER than tall (the battle message box, some name headers) stretched Latin glyphs
# sideways; since 0.3.2 they are also scaled by the height (only ever makes text narrower).
PRE = [  # (hook, original instruction, resume): run the instruction, save the font height in $f8
    dict(hook=0xB0400, orig='lwc1 $f0, 8($a0)', resume=0xB0408),     # W1, before $a0 = flag
    dict(hook=0xB063C, orig='lwc1 $f5, 8($a0)', resume=0xB0644),     # W3, before $a0 = 0x824f
]


def pre_stubs():
    out = []
    for n, p in enumerate(PRE):
        out += [f'pre{n}:', p['orig'], 'lwc1 $f8, 0xc($a0)', f"j {A(p['resume']):#x}"]
    return out


_base = BASE               # absolute for live patching; 0 when building a relocatable BOOT.BIN


def A(v):
    return _base + v


# NOTE on keystone: it inserts a nop after every branch/jump (it fills the delay slot itself),
# so the sources below are written as if MIPS had no delay slots.

def load_code(c):
    """-> $t9 = 2-byte SJIS code of the glyph being drawn."""
    if c[0] == 'reg':
        ld = [f'lbu $t9, 0({c[1]})', f'lbu $at, 1({c[1]})']
    elif c[0] == 'sp':
        ld = [f'lbu $t9, {c[1]}($sp)', f'lbu $at, {c[1] + 1}($sp)']
    else:                                               # lead byte already in a register
        ld = [f'move $t9, {c[1]}', f'lbu $at, 1({c[2]})']
    return ld + ['sll $t9, $t9, 8', 'or $t9, $t9, $at']


def lookup():
    """Shared routine. in: $t9 = SJIS code; out: $t9 = width-table entry (0 = not a VWF glyph).
    Clobbers $at. The only place that needs the table address (one HI16/LO16 relocation)."""
    hi = (A(TABLE) + 0x8000) >> 16
    lo = A(TABLE) - (hi << 16)
    return ['lookup:',
            'addiu $t9, $t9, -0x4000', 'addiu $t9, $t9, -0x4140',     # code - 0x8140
            'sltiu $at, $t9, 0x1c0', 'beqz $at, lk_none',             # lead bytes 0x81 / 0x82 only
            'srl $at, $t9, 8', 'sll $at, $at, 6', 'subu $t9, $t9, $at',
            f'lui $at, {hi:#x}', 'addu $at, $at, $t9', f'lbu $t9, {lo}($at)', 'jr $ra',
            'lk_none:', 'move $t9, $zero', 'jr $ra']


def size_from_height(s, n):
    """Instructions that leave the effective font size in the register the scaling uses (see hctx).
    Returns (instructions, size register). Temporaries: $f8-$f11 (unused by all eight functions)."""
    k, c = s['kind'], s['hctx']
    integer = k in ('rint', 'wint')
    if k in ('rint', 'rflt'):
        out, reg = [], s['wreg']                     # renderers: wreg holds the font width
    elif s['size'] == s['wreg']:
        out, reg = [], s['wreg']                     # W2 / W4: recomputed for every glyph
    else:                                            # W1 / W3: size is a loop constant, keep it
        out, reg = [('move' if integer else 'mov.s') + f" {s['wreg']}, {s['size']}"], s['wreg']
    if c != '$f8':
        out.append(f'lwc1 $f8, 0xc({c})')
    out += ([f'mtc1 {reg}, $f9', 'cvt.s.w $f9, $f9'] if integer else [f'mov.s $f9, {reg}'])
    out += ['add.s $f10, $f9, $f9', 'add.s $f10, $f10, $f10',                             # 4 * width
            'add.s $f11, $f10, $f10', 'add.s $f10, $f10, $f11', 'add.s $f10, $f10, $f9',  # 13 * width
            'add.s $f11, $f8, $f8', 'add.s $f11, $f11, $f11', 'add.s $f11, $f11, $f8',    # 5 * height
            'add.s $f11, $f11, $f11',                                                     # 10 * height
            'c.lt.s $f10, $f11', 'nop', f'bc1t useh{n}',                            # narrow: 13w < 10h
            'c.lt.s $f8, $f9', 'nop', f'bc1f keep{n}',                              # wide: h < w
            f'useh{n}:']
    out += (['trunc.w.s $f9, $f8', f'mfc1 {reg}, $f9'] if integer else [f'mov.s {reg}, $f8'])
    return out + [f'keep{n}:'], reg


def stub(s, n):
    fb, ex = f'fb{n}', f'ex{n}'
    # $ra is live in the leaf width functions, so it is parked in LO around the call
    L = load_code(s['code']) + ['mtlo $ra', 'bal lookup', 'mflo $ra',
                                f'beqz $t9, {fb}', 'andi $at, $t9, 0x1f', 'srl $t9, $t9, 5']
    k = s['kind']                                       # here: $at = W, $t9 = L (left bearing)
    eff, zreg = size_from_height(s, n)
    L += eff
    if k in ('rint', 'rflt'):
        L.append(f"addu {s['ureg']}, {s['ureg']}, $t9")
        L.append(f"sw $at, {s['tex'][1]}($sp)" if s['tex'][0] == 'sp' else f"move {s['tex'][1]}, $at")
    if k == 'rint':
        w = s['wreg']
        L += [f'mult $at, {w}', f'mflo {w}', f'addiu {w}, {w}, 9', 'addiu $at, $zero, 18',
              f'div $zero, {w}, $at', f'mflo {w}']
    elif k == 'wint':
        w, z = s['wreg'], zreg
        L += [f'mult $at, {z}', f'mflo {w}', f'addiu {w}, {w}, 9', 'addiu $at, $zero, 18',
              f'div $zero, {w}, $at', f'mflo {w}']
    elif k == 'rflt':
        w = s['wreg']
        L += ['mtc1 $at, $f0', 'cvt.s.w $f0, $f0', f'mul.s {w}, {w}, $f0',
              'lui $at, 0x4190', 'mtc1 $at, $f0', f'div.s {w}, {w}, $f0']
    elif k == 'wflt':
        w, z, f = s['wreg'], zreg, s['ftmp']
        L += [f'mtc1 $at, {f}', f'cvt.s.w {f}, {f}', f'mul.s {w}, {z}, {f}',
              'lui $at, 0x4190', f'mtc1 $at, {f}', f'div.s {w}, {w}, {f}']
    L += [f'{ex}:', f"j {A(s['skip']):#x}",
          f'{fb}:', f"beqz {s['flag']}, {ex}", f"j {A(s['cls']):#x}"]
    return L


def assemble(base=BASE):
    """-> (code bytes, [(hook vaddr, 4 bytes)], [(vaddr, reloc type)]) assembled for load address `base`.
    Relocations (R_MIPS_26 = 4 for every j, HI16/LO16 = 5/6 for the table address) are what a
    relocatable build (base 0) needs."""
    global _base
    _base = base
    try:
        ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 + keystone.KS_MODE_LITTLE_ENDIAN)
        src, entry = lookup() + pre_stubs(), {}
        for n, s in enumerate(SITES):
            src.append(f'stub{n}:')
            src += stub(s, n)
        code = bytes(ks.asm(chr(10).join(src), A(CODE))[0])
        labels = [f'stub{n}' for n in range(len(SITES))] + [f'pre{n}' for n in range(len(PRE))]
        for label in labels:                 # entry addresses: assemble a probe jump after the code
            probe = bytes(ks.asm(chr(10).join(src + [f'j {label}']), A(CODE))[0])
            entry[label] = ((struct.unpack_from('<I', probe, len(code))[0] & 0x3FFFFFF) << 2) - _base
        hooks, relocs = [], []
        targets = [(f'stub{n}', s['hook']) for n, s in enumerate(SITES)]
        targets += [(f'pre{n}', p['hook']) for n, p in enumerate(PRE)]
        for label, hook in targets:
            j = bytes(ks.asm(f'j {A(entry[label]):#x}', A(hook))[0])[:4]   # keep the original delay slot
            hooks.append((hook, j))
            relocs.append((hook, 4))
        words = struct.unpack(f'<{len(code) // 4}I', code)
        for i, w in enumerate(words):
            op = w >> 26
            if op == 2:                                           # j
                relocs.append((CODE + i * 4, 4))
            elif op == 0x0F and (w >> 16) & 31 == 1:              # lui $at, hi
                for k in (1, 2):                                  # ... lbu $t9, lo($at)
                    if i + k >= len(words):
                        break
                    w2 = words[i + k]
                    if w2 >> 26 == 0x24 and (w2 >> 21) & 31 == 1:
                        relocs += [(CODE + i * 4, 5), (CODE + (i + k) * 4, 6)]
                        break
        assert CODE + len(code) <= CAVE + CAVE_SIZE, 'stubs do not fit the cave'
        return code, hooks, relocs
    finally:
        _base = BASE


def width_table(static2):
    """Measure the ink of every glyph in slots 0..383 (lead bytes 0x81/0x82); entries only for
    punctuation, digits and Latin letters."""
    d = open(static2, 'rb').read()
    tab = bytearray(384)

    def pix(slot, x, y):
        row, col = divmod(slot, 14)
        o = ATLAS + (row * 18 + y) * 128 + (col * 18 + x) // 2
        b = d[o]
        return (b >> 4) if (col * 18 + x) & 1 else (b & 15)

    def sjis_slot(code):
        v = code - 0x8140
        return v - (v >> 8) * 64

    from make_latin_font import CHARS                # only glyphs we redraw get a width entry
    wanted = sorted(c for c in CHARS if c != 0x8140)
    for code in wanted:
        s = sjis_slot(code)
        cols = [x for x in range(18) if any(pix(s, x, y) for y in range(18))]
        if not cols:
            continue
        left, right = cols[0], cols[-1]
        w = right - left + 1 + 1          # +1 px spacing (glyph outline already pads)
        tab[s] = min(w, 31) | (min(left, 7) << 5)
        if left > 7:                      # bearing does not fit 3 bits: keep 7, widen
            tab[s] = min(w + left - 7, 31) | (7 << 5)
    tab[sjis_slot(0x8140)] = SPACE_W      # full-width space = word space
    from make_latin_font import DIGITS, DIGIT_W, DIGIT_LEFT
    for code, ch in CHARS.items():        # tabular digits: one advance for all (make_latin_font.py)
        if ch in DIGITS:
            tab[sjis_slot(code)] = DIGIT_W | (DIGIT_LEFT << 5)
    return bytes(tab)


REL_TEXT_NAME = b'.rel.text'


def patch_boot(boot, static2):
    """Return a patched copy of BOOT.BIN (relocatable ELF). The unused function's relocation
    entries are replaced by the ones our code needs; the surplus entries are removed."""
    b = bytearray(boot)
    code, hooks, relocs = assemble(0)
    for va, data in [(TABLE, width_table(static2)), (CODE, code)] + hooks:
        b[0x60 + va:0x60 + va + len(data)] = data
    b[0x60 + CODE + len(code):0x60 + CAVE + CAVE_SIZE] = bytes(CAVE + CAVE_SIZE - CODE - len(code))

    shoff, = struct.unpack_from('<I', b, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from('<3H', b, 0x2E)
    stroff = struct.unpack_from('<I', b, shoff + shstrndx * shentsize + 16)[0]
    for i in range(shnum):
        h = shoff + i * shentsize
        name = struct.unpack_from('<I', b, h)[0]
        if b[stroff + name:stroff + name + len(REL_TEXT_NAME) + 1] == REL_TEXT_NAME + bytes(1):
            off, size = struct.unpack_from('<2I', b, h + 16)
            break
    else:
        raise ValueError('.rel.text not found')
    ents = [struct.unpack_from('<2I', b, off + k) for k in range(0, size, 8)]
    inside = [k for k, (o, _) in enumerate(ents) if CAVE <= o < CAVE + CAVE_SIZE]
    assert inside and inside[-1] - inside[0] + 1 == len(inside), 'cave relocations are not contiguous'
    assert not any(any(sx['hook'] <= o < sx['hook'] + 4 for sx in SITES) for o, _ in ents)
    new = ents[:inside[0]] + [(va, typ) for va, typ in relocs] + ents[inside[-1] + 1:]
    assert len(new) <= len(ents)
    blob = b''.join(struct.pack('<2I', o, i) for o, i in new)
    b[off:off + size] = blob + bytes(size - len(blob))
    struct.pack_into('<I', b, h + 20, len(blob))
    return bytes(b)


def build(static2, boot_in, boot_out):
    open(boot_out, 'wb').write(patch_boot(open(boot_in, 'rb').read(), static2))
    print('patched', boot_out)


def live(static2):
    """Write the patch into a running PPSSPP (absolute addresses, module already relocated)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ppsspp_dbg import Dbg
    code, hooks, _ = assemble(BASE)
    with Dbg() as dbg:
        dbg.call('cpu.stepping')
        for va, data in [(TABLE, width_table(static2)), (CODE, code)] + hooks:
            dbg.write(BASE + va, data)
        dbg.call('cpu.resume')
    print('live patch written')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'build':
        build(*sys.argv[2:5])
    elif cmd == 'live':
        live(sys.argv[2])
    elif cmd == 'table':
        t = width_table(sys.argv[2])
        print(' '.join(f'{x & 31}/{x >> 5}' for x in t[:0x6c]))
        print(' '.join(f'{x & 31}/{x >> 5}' for x in t[0xcf:0x11b]))
