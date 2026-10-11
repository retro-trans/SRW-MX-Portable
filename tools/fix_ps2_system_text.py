"""PS2 0.4.19: Option menu library entries, save/load screen and memory-card dialogs in English.

The general UI port only repointed Japanese strings that had exactly one PSP translation,
so the PS2-only memory-card (PS2) messages and a few shared labels were left untouched.
This patch appends an English pool to the executable segment and repoints:
  * pointer words in the loaded data (Option menu tables, save/load column headers);
  * lui/addiu literal pairs in code (dialog lines passed by pointer to CWndMessage::AddItem);
  * four save-slot labels the compiler copied inline with a fixed byte count. Those copy
    blocks are rewritten to call the game's own strcpy (0x36ae10) into the same 256-byte
    stack buffer, as the scenario-name branch of the same function already does.

The ELF is the last file on the 0.4.18 disc, so the image is rebuilt in place: the larger
executable is written at its original extent and the ISO9660 / UDF records are updated.
Every other file keeps its sector and bytes; both filesystem views are read back.

usage: python tools/fix_ps2_system_text.py [--build]
"""
import argparse
import copy
import hashlib
import json
import shutil
import struct

import pycdlib

import insert_text as it
from build_ps2_dialogue import directory_position
from build_ps2_font import patch_udf
from ps2_font4x import FILE_BIAS
from ps2_narration_port import native_width
from ps2_translation_native import extend, source_registers, written_register
from port_ps2_translations import ROOT, sha
from port_ps2_prologue import save

VERSION = '0.4.19'
BASE_VERSION = '0.4.18'
PREVIOUS = ROOT/'work/build/ps2/black_selena_0.4.18'
BASE = ROOT/'work/build/ps2'/f'system_text_{VERSION}'
DATA = (0x2c5e00, 0x3c5d00)          # file offsets of the loaded data section
CODE_END = 0x2bef18                  # file offset where executable code ends
STRCPY = 0x36ae10
SLOT_BUFFER = 0x90                   # sp offset of the 256-byte slot label buffer

CARD_MISSING = ['No memory card (PS2) in MEMORY CARD slot 1.', 'Please check the connection.']
HANDS_OFF = 'the memory card (PS2) or controller.'
# One group per screen or dialog. Each English line must fit the widest Japanese line
# of its own group (native VWF units; one Japanese character is 24); dialog lines may use
# up to DIALOG_PX of the shared message window.
GROUPS = [
    # Option menu (title) and the library screen header table
    {0x4926b8: 'Character Library', 0x4926d0: 'Robot Library'},
    {0x495d28: 'Robot Library', 0x495d38: 'Character Library'},
    # Save / load list: header, column titles, slot labels
    {0x49ce68: 'Save Data', 0x49ce78: 'Load Data'},
    {0x49cc98: 'Free', 0x49cca8: 'Hero', 0x49ccb8: 'Clears', 0x49ccc8: 'Date'},
    {0x49cd78: 'Clear Data', 0x49cd88: 'No data', 0x49cda0: 'Corrupt data', 0x49cdb0: 'Not enough space'},
    # Scenario save
    {0x4a05b0: CARD_MISSING[0], 0x4a05f0: CARD_MISSING[1]},
    {0x4a0620: 'Not enough free space. Saving scenario data', 0x4a0660: 'requires at least 66 KB of free space.'},
    {0x4a0688: 'Formatting. Do not insert or remove', 0x4a06c8: HANDS_OFF},
    {0x4a06e8: 'Formatting failed.'},
    {0x4a0708: 'Save complete.'},
    {0x4a0770: 'Formatting complete.', 0x4a07a8: 'Save the scenario data?'},
    {0x4a07b8: 'The memory card (PS2) is not formatted.', 0x4a07f0: 'Format it?'},
    {0x4a0808: 'No system data found. Create it?'},
    {0x4a0838: 'Overwrite this scenario data?'},
    # Scenario load
    {0x4a0b98: CARD_MISSING[0], 0x4a0bd8: CARD_MISSING[1]},
    {0x4a0c08: 'No scenario data found.'},
    {0x4a0c28: 'Loading. Do not insert or remove', 0x4a0c60: HANDS_OFF},
    {0x4a0c80: 'The scenario data is corrupted and cannot be loaded.'},
    {0x4a0cb8: 'Load complete.'},
    {0x4a0cd0: 'Loading failed.'},
    {0x4a0d10: 'Loading will discard the current game data.', 0x4a0d40: 'Load anyway?'},
    {0x4a0d58: 'Exit the load screen?'},
    {0x4a0d78: 'Return to the title screen?'},
    # System data save (intermission)
    {0x4a5cd0: CARD_MISSING[0], 0x4a5d10: CARD_MISSING[1]},
    {0x4a5d40: 'Return to the main command menu?'},
    {0x4a5d78: 'Not enough free space. Saving system data', 0x4a5db8: 'requires at least 154 KB of free space.'},
    {0x4a5df8: 'No system data found. Create it?'},
    {0x4a5e48: 'The memory card (PS2) is not formatted.', 0x4a5e88: 'Format it?'},
    {0x4a5ea8: 'Formatting. Do not insert or remove', 0x4a5ee8: HANDS_OFF},
    {0x4a5f08: 'Formatting complete.', 0x4a5f40: 'Save the system data?'},
    {0x4a5ff8: 'Save complete. Continue the game?'},
    {0x4a6028: 'The save failed.'},
    # Title screen: Continue
    {0x4a9068: 'Checking the memory card (PS2).'},
    {0x4a9098: CARD_MISSING[0], 0x4a90d8: CARD_MISSING[1]},
    {0x4a9168: 'No system data found, so you cannot continue.'},
    {0x4a91a0: 'Loading. Do not insert or remove', 0x4a9148: HANDS_OFF},
    {0x4a91d8: 'The system data is corrupted and cannot be loaded.'},
    {0x4a9210: 'Loading failed.'},
    {0x4a9250: 'Return to the title screen?'},
    # Title screen: New Game memory-card checks
    {0x4a9408: 'Checking the memory card (PS2).'},
    {0x4a9438: CARD_MISSING[0], 0x4a9478: 'Saving the game requires a memory card (PS2)',
     0x4a94b8: 'with at least 220 KB of free space.', 0x4a94f8: 'Start without saving?'},
    {0x4a9510: 'The memory card (PS2) does not have enough', 0x4a9550: 'free space to save scenario data. Saving',
     0x4a9588: 'scenario data requires at least 66 KB.', 0x4a95b8: '(System and scenario data together need',
     0x4a95f0: 'at least 220 KB of free space.)'},
    {0x4a9608: 'The memory card (PS2) does not have enough', 0x4a9648: 'free space to save system data. Saving',
     0x4a9680: 'system data requires at least 154 KB.'},
    {0x4a96b0: 'The memory card (PS2) does not have enough free space.',
     0x4a96e8: 'Saving the game requires a memory card (PS2)', 0x4a9720: 'with at least 220 KB of free space.'},
]
TEXT = {va: en for g in GROUPS for va, en in g.items()}
FIRST_DIALOG = 5            # groups from here on are CWndMessage dialogs
DIALOG_PX = 600             # the shared dialog window shows 30-character Japanese lines (720)
# Save-slot labels copied inline: (first instruction, instruction count, source string).
INLINE_COPIES = [(0x192a30, 10, 0x49cd78), (0x192a58, 12, 0x49cd88), (0x192a88, 10, 0x49cda0), (0x192ab0, 8, 0x49cdb0)]
# Literal pairs completed in a branch delay slot, which the general scan leaves alone.
# (lui, addiu, string): each lui value is dead after its addiu (the addiu rewrites the same
# register, or the branch target calls a function before the register is read again).
DELAY_PAIRS = [
    (0x193798, 0x1937a0, 0x49ce68), (0x19378c, 0x1937a8, 0x49ce78),   # header; 0x19378c is a beq delay slot
    (0x1cf1b8, 0x1cf1c4, 0x4a06e8), (0x1cf380, 0x1cf38c, 0x4a0808), (0x1cf390, 0x1cf39c, 0x4a0838),
    (0x1d34e8, 0x1d34f4, 0x4a0c08), (0x1d3520, 0x1d352c, 0x4a0c80),
    (0x2c0828, 0x2c0834, 0x4a9068), (0x2c0888, 0x2c0894, 0x4a9168),
    (0x2c4f70, 0x2c4f78, 0x4a94b8), (0x2c4fa8, 0x2c4fb0, 0x4a9588),
]
LOADS = {32, 33, 34, 35, 36, 37, 38, 26, 27, 55}   # lb lh lwl lw lbu lhu lwr ldl ldr ld


def jp_at(data, va):
    o = va - FILE_BIAS
    return data[o:data.index(b'\0', o)].decode('cp932')


def word(data, va):
    return struct.unpack_from('<I', data, va - FILE_BIAS)[0]


def check_widths(original, meta):
    rows = []
    for n, g in enumerate(GROUPS):
        budget = max(len(jp_at(original, va)) * 24 for va in g)
        if n >= FIRST_DIALOG:
            budget = max(budget, DIALOG_PX)
        for va, en in g.items():
            w = native_width(en, meta)
            assert w <= budget, (hex(va), en, w, budget)
            rows.append(dict(source=hex(va), japanese=jp_at(original, va), english=en, width=w, budget=budget))
    return rows


def code_pairs(data, targets):
    """lui/addiu literal groups whose loaded register only ever addresses translated strings."""
    groups, rejected = [], []
    for off in range(0x1000, CODE_END, 4):
        w = struct.unpack_from('<I', data, off)[0]
        if w >> 26 != 15 or not 0x48 <= (w & 0xffff) <= 0x4b:
            continue
        reg = (w >> 16) & 31
        uses, unsafe, ended, delay_end = [], False, False, None
        for nxt in range(off + 4, min(off + 4 * 65, CODE_END), 4):
            ins = struct.unpack_from('<I', data, nxt)[0]
            op, rs = ins >> 26, (ins >> 21) & 31
            if reg in source_registers(ins):
                if op in (9, 13) and rs == reg:
                    lo = ins & 0xffff
                    if op == 9 and lo >= 0x8000:
                        lo -= 0x10000
                    addr = ((w & 0xffff) << 16) + lo
                    if addr in targets:
                        uses.append((nxt, ins, addr))
                    else:
                        unsafe = True
                else:
                    unsafe = True
            if written_register(ins) == reg or delay_end == nxt:
                ended = True
                break
            if op in (2, 3) or (op == 0 and ins & 63 in (8, 9)):
                if reg not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25):
                    unsafe = True
                delay_end = nxt + 4
            elif op in (1, 4, 5, 6, 7, 20, 21, 22, 23):
                unsafe = True
                break
        if not uses:
            continue
        if unsafe or not ended:
            rejected.append(dict(site=hex(off + FILE_BIAS), sources=[hex(u[2]) for u in uses]))
            continue
        groups.append((off, w, uses))
    return groups, rejected


def loads_through(data, site, reg):
    """True when the address in reg is read like a struct (inline copy) before reg is replaced."""
    for nxt in range(site + 4, site + 4 * 12, 4):
        ins = struct.unpack_from('<I', data, nxt)[0]
        if ins >> 26 in LOADS and (ins >> 21) & 31 == reg:
            return True
        if written_register(ins) == reg:
            return False
    return False


def prepare():
    BASE.mkdir(parents=True, exist_ok=True)
    for p in PREVIOUS.iterdir():
        if p.is_file() and p.suffix in ('.BIN', '.DAT', '.45', '.json'):
            shutil.copyfile(p, BASE/p.name)
    meta = json.loads((BASE/'patch.json').read_text())
    data = bytearray((BASE/'SLPS_253.45').read_bytes())
    assert sha(data) == meta['target_sha256']
    original = (ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    for va in TEXT:
        assert jp_at(data, va) == jp_at(original, va), hex(va)
    widths = check_widths(original, meta)
    report = dict(version=VERSION, source_build=BASE_VERSION, strings=widths, data_references=[],
                  instruction_words=[], inline_copies=[])
    # English pool in one signed-low 64 KiB page, so a shared lui keeps a single high half.
    blob, rel = bytearray(), {}
    for en in dict.fromkeys(TEXT.values()):
        rel[en] = len(blob)
        blob += it.encode(en)
        blob += bytes(-len(blob) % 4)
    current = int(meta['segment_va'], 16) + meta['segment_bytes']
    start = (current + 15) & ~15
    if (start + 0x8000) >> 16 != (start + len(blob) + 0x8000) >> 16:
        start = ((start + 0x8000 + 0xffff) & ~0xffff) - 0x8000     # next signed-low page
    targets = {va: start + rel[en] for va, en in TEXT.items()}
    high = (start + 0x8000) >> 16
    assert all((t + 0x8000) >> 16 == high for t in targets.values())
    data, pool_va = extend(data, meta, bytes(start - current) + blob, alignment=1)
    assert pool_va == current

    def put(va, new, kind):
        old = word(data, va)
        struct.pack_into('<I', data, va - FILE_BIAS, new)
        report['instruction_words'].append(dict(va=hex(va), old=hex(old), new=hex(new), kind=kind))

    # Inline slot copies first; their lui/addiu pairs are replaced, not repointed.
    # The scenario-name branch (0x192a00) already strcpy's into the buffer and then reloads
    # a3 / t0, which the call clobbers; reuse its exact reload words.
    reload_a3, reload_t0 = word(data, 0x192a24), word(data, 0x192a2c)
    assert (reload_a3, reload_t0) == (0x8e4702b0, 0x8e4802a8)
    inline_sites = set()
    for site, count, source in INLINE_COPIES:
        before = bytes(data[site - FILE_BIAS:site - FILE_BIAS + 4 * count])
        lui, addiu = word(data, site), word(data, site + 8)
        assert lui == 0x3c02004a and addiu >> 16 == 0x2442 and ((addiu & 0xffff) - 0x10000) + 0x4a0000 == source
        assert word(data, site + 4) == 0x27b30000 | SLOT_BUFFER          # addiu s3, sp, 0x90
        assert (word(data, site + 4 * count - 8) >> 16) == 0x1000         # b 0x192ad4
        t = targets[source]
        hi = (t + 0x8000) >> 16
        branch = site + 4 * 6                                             # the b sits at word 6
        code = struct.pack('<8I',
                           0x27b30000 | SLOT_BUFFER,                      # addiu s3, sp, 0x90
                           0x3c050000 | hi,                               # lui   a1, hi
                           0x02602021,                                    # move  a0, s3
                           0x0c000000 | (STRCPY >> 2),                    # jal   strcpy
                           0x24a50000 | ((t - (hi << 16)) & 0xffff),      # addiu a1, a1, lo
                           reload_a3,                                     # lw a3, 0x2b0(s2)
                           0x10000000 | (((0x192ad4 - branch - 4) >> 2) & 0xffff),   # b 0x192ad4
                           reload_t0)                                     # lw t0, 0x2a8(s2)
        code += bytes(4 * count - len(code))                              # trailing nops are unreachable
        data[site - FILE_BIAS:site - FILE_BIAS + 4 * count] = code
        inline_sites.update(range(site, site + 4 * count, 4))
        report['inline_copies'].append(dict(site=hex(site), source=hex(source), english=TEXT[source],
                                            old=before.hex(), new=code.hex(), strcpy=hex(STRCPY)))
    # Pointer words in loaded data.
    for off in range(DATA[0], DATA[1], 4):
        w = struct.unpack_from('<I', data, off)[0]
        if w in targets and struct.unpack_from('<I', original, off)[0] == w:
            struct.pack_into('<I', data, off, targets[w])
            report['data_references'].append(dict(site=hex(off + FILE_BIAS), source=hex(w), target=hex(targets[w]),
                                                  english=TEXT[w]))
    # Literal pairs in code.
    groups, rejected = code_pairs(data, targets)
    for off, w, uses in groups:
        assert off + FILE_BIAS not in inline_sites
        for nxt, ins, addr in uses:
            dest = (ins >> 16) & 31
            assert not loads_through(data, nxt, dest), ('inline copy', hex(nxt + FILE_BIAS))
        put(off + FILE_BIAS, (w & 0xffff0000) | high, 'lui')
        for nxt, ins, addr in uses:
            t = targets[addr]
            if ins >> 26 == 13:
                ins = (ins & 0x03ffffff) | (9 << 26)      # ori -> addiu for a signed low half
            put(nxt + FILE_BIAS, (ins & 0xffff0000) | ((t - (high << 16)) & 0xffff), 'addiu')
            report.setdefault('code_pairs', []).append(dict(lui=hex(off + FILE_BIAS), addiu=hex(nxt + FILE_BIAS),
                                                            source=hex(addr), target=hex(t), english=TEXT[addr]))
    for lui_va, addiu_va, source in DELAY_PAIRS:
        lui, addiu = word(data, lui_va), word(data, addiu_va)
        reg, old_hi = (lui >> 16) & 31, (source + 0x8000) >> 16
        assert lui == 0x3c000000 | (reg << 16) | old_hi, hex(lui_va)
        assert addiu >> 26 == 9 and (addiu >> 21) & 31 == reg and (addiu & 0xffff) == (source - (old_hi << 16)) & 0xffff
        t = targets[source]
        put(lui_va, (lui & 0xffff0000) | high, 'lui (delay pair)')
        put(addiu_va, (addiu & 0xffff0000) | ((t - (high << 16)) & 0xffff), 'addiu (delay slot)')
        report.setdefault('delay_pairs', []).append(dict(lui=hex(lui_va), addiu=hex(addiu_va), source=hex(source),
                                                         target=hex(t), english=TEXT[source]))
    report['rejected_shared_groups'] = rejected
    assert not rejected, rejected
    # Every translated string must now be unreferenced by its old address.
    reached = {r['source'] for r in report['data_references']} | {r['source'] for r in report['inline_copies']}
    reached |= {hex(a) for _, _, uses in groups for _, _, a in uses}
    reached |= {r['source'] for r in report.get('delay_pairs', [])}
    missing = sorted(hex(va) for va in TEXT if hex(va) not in reached)
    assert not missing, ('no live reference found', missing)
    meta['target_sha256'] = sha(data)
    (BASE/'SLPS_253.45').write_bytes(data)
    report.update(pool_va=hex(start), pool_bytes=len(blob), elf_bytes=len(data), elf_sha256=sha(data))
    save(BASE/'patch.json', meta)
    save(BASE/'system_text.json', report)
    save(ROOT/'work/translation/en/ps2'/f'system_text_{VERSION}.en.json',
         dict(version=VERSION, strings=[dict(source=r['source'], english=r['english']) for r in widths]))
    print(f"strings {len(TEXT)}  data refs {len(report['data_references'])}  code groups {len(groups)}  "
          f"inline copies {len(report['inline_copies'])}  pool {hex(start)}+{len(blob)}")
    return data, meta, report


def verify(elf, report, meta):
    """Static readback of every repointed reference, and native execution of the slot copies."""
    from unicorn import UC_HOOK_CODE
    from unicorn import mips_const as r
    from verify_ps2_font import machine

    seg_va, seg_off = int(meta['segment_va'], 16), int(meta['segment_offset'], 16)

    def string(va):
        o = va - seg_va + seg_off if va >= seg_va else va - FILE_BIAS
        return elf[o:elf.index(b'\0', o) + 1]
    checks = 0
    for row in report['data_references']:
        assert string(word(elf, int(row['site'], 16))) == it.encode(row['english']); checks += 1
    lui_hi = {}
    for row in report['instruction_words']:
        if row['kind'].startswith('lui'):
            lui_hi[row['va']] = int(row['new'], 16) & 0xffff
    for row in report.get('delay_pairs', []) + report.get('code_pairs', []):
        lo = word(elf, int(row['addiu'], 16)) & 0xffff
        va = (lui_hi[row['lui']] << 16) + (lo - 0x10000 if lo & 0x8000 else lo)
        assert string(va) == it.encode(row['english']); checks += 1
    # No translated Japanese string is still addressed by a data word or a literal pair.
    sources = {int(s['source'], 16) for s in report['strings']}
    words = struct.unpack_from(f'<{len(elf) // 4}I', elf)
    for off in range(DATA[0], DATA[1], 4):
        assert words[off // 4] not in sources, hex(off + FILE_BIAS)
    lui = {}
    for i in range(0x1000 // 4, CODE_END // 4):
        w = words[i]
        if w >> 26 == 15:
            lui[(w >> 16) & 31] = (i, (w & 0xffff) << 16)
        elif w >> 26 in (9, 13) and (w >> 21) & 31 in lui and i - lui[(w >> 21) & 31][0] < 40:
            lo = w & 0xffff
            va = lui[(w >> 21) & 31][1] + (lo - 0x10000 if w >> 26 == 9 and lo & 0x8000 else lo)
            assert va not in sources, (hex(i * 4 + FILE_BIAS), hex(va))
            if va >= int(report['pool_va'], 16) and va < int(report['pool_va'], 16) + report['pool_bytes']:
                checks += 1
    # Execute each rewritten slot block: strcpy must leave the whole English label in the buffer.
    for row in report['inline_copies']:
        u = machine(elf)
        sp, s2 = 0x900000, 0x940000
        u.reg_write(r.UC_MIPS_REG_SP, sp); u.reg_write(r.UC_MIPS_REG_S2, s2)
        u.mem_write(s2 + 0x2b0, struct.pack('<I', 0x1234)); u.mem_write(s2 + 0x2a8, struct.pack('<I', 0x5678))
        u.mem_write(sp + SLOT_BUFFER, b'\xaa' * 256)
        # strcpy's aligned path uses EE 128-bit MMI instructions Unicorn cannot run: stop at the
        # call, check its arguments, copy like the library does and resume at the return address.
        u.emu_start(int(row['site'], 16), STRCPY, count=100)
        a0, a1, ra = (u.reg_read(x) for x in (r.UC_MIPS_REG_A0, r.UC_MIPS_REG_A1, r.UC_MIPS_REG_RA))
        assert a0 == sp + SLOT_BUFFER and string(a1) == it.encode(row['english'])
        u.mem_write(a0, string(a1)); u.reg_write(r.UC_MIPS_REG_V0, a0)
        u.emu_start(ra, 0x192ad4, count=100)
        assert u.reg_read(r.UC_MIPS_REG_PC) == 0x192ad4
        assert u.reg_read(r.UC_MIPS_REG_S3) == sp + SLOT_BUFFER
        assert (u.reg_read(r.UC_MIPS_REG_A3), u.reg_read(r.UC_MIPS_REG_T0)) == (0x1234, 0x5678)
        enc = it.encode(row['english'])
        assert bytes(u.mem_read(sp + SLOT_BUFFER, len(enc))) == enc, row['english']
        checks += 1
    report['verification'] = dict(passed=True, checks=checks, slot_copy_executions=len(report['inline_copies']),
                                  japanese_sources_unreferenced=len(sources))
    print('verified', checks, 'checks')


def digest(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(8 << 20), b''):
        h.update(chunk)
    return h.hexdigest()


def package(elf, meta, report):
    source = ROOT/'work/output'/f'SRWMX_PS2_EN_{BASE_VERSION}.iso'
    output = ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso'
    assert not output.exists(), 'Preserve existing versioned builds'
    previous = json.loads((ROOT/'work/output'/f'ps2_font_{BASE_VERSION}_verification.json').read_text())
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = sorted(f.rstrip('/') + '/' + n for f, _, names in iso.walk(iso_path='/') for n in names)
    rec = iso.get_record(iso_path='/SLPS_253.45;1')
    sector, old_len = rec.extent_location(), rec.data_length
    for p in paths:      # the executable must be the last file so it can grow in place
        r = iso.get_record(iso_path=p)
        assert p == '/SLPS_253.45;1' or r.extent_location() < sector, p
    assert source.stat().st_size == ((sector + (old_len + 2047) // 2048) + 1) * 2048
    before = {}
    for p in paths:
        with iso.open_file_from_iso(iso_path=p) as f:
            before[p] = digest(f)
    position = directory_position(iso, source, '/SLPS_253.45;1')
    last = sector + (len(elf) + 2047) // 2048
    shutil.copyfile(source, output)
    with output.open('r+b') as dst:
        dst.seek(sector * 2048); dst.write(elf); dst.write(bytes(-len(elf) % 2048))
        assert dst.tell() == last * 2048
        dst.write(bytes(2048)); dst.truncate(); total = last + 1
        dst.seek(position + 10); dst.write(struct.pack('<I', len(elf)) + struct.pack('>I', len(elf)))
        descriptor = 16
        while True:
            dst.seek(descriptor * 2048); head = dst.read(7); assert head[1:6] == b'CD001'
            if head[0] == 255:
                break
            if head[0] in (1, 2):
                dst.seek(descriptor * 2048 + 80); dst.write(struct.pack('<I', total) + struct.pack('>I', total))
            descriptor += 1
        patch_udf(iso, dst, sector, len(elf), last)
    iso.close()
    check = pycdlib.PyCdlib(); check.open(str(output)); files = []
    for p in paths:
        with check.open_file_from_iso(iso_path=p) as f:
            h = digest(f)
        changed = p == '/SLPS_253.45;1'
        assert h == (sha(elf) if changed else before[p]), p
        name = p.rsplit('/', 1)[-1].split(';')[0].rstrip('.')
        matches = [f.rstrip('/') + '/' + n for f, _, names in check.walk(udf_path='/') for n in names
                   if n.lower() == name.lower()]
        assert len(matches) == 1, (p, matches)
        with check.open_file_from_iso(udf_path=matches[0]) as f:
            assert digest(f) == h, ('UDF', p)
        r = check.get_record(iso_path=p)
        files.append(dict(path=p, changed=changed, source_sha256=before[p], target_sha256=h,
                          sector=r.extent_location(), bytes=r.data_length, udf_readback=True))
    check.close()
    with output.open('rb') as f:
        out_sha = digest(f)
    shutil.copyfile(source.with_name(source.stem + '_FONT_LICENSE.txt'), output.with_name(output.stem + '_FONT_LICENSE.txt'))
    result = dict(version=VERSION, base_version=BASE_VERSION, output=str(output.relative_to(ROOT)),
                  bytes=output.stat().st_size, output_sha256=out_sha, files=files,
                  only_executable_changed=True, local_build_only=True, pcsx2_fresh_boot_verified=False,
                  physical_hardware_verified=False, github_release=False, corrections=report)
    save(ROOT/'work/output'/f'ps2_system_text_{VERSION}_verification.json', result)
    # Keep the PS2 build chain readable by the other incremental tools.
    aggregate = copy.deepcopy(previous)
    lookup = {r['path']: r for r in files}
    for row in aggregate['files']:
        row['target_sha256'] = lookup[row['path']]['target_sha256']
        if row['path'] == '/SLPS_253.45;1' and 'bytes' in row:
            row['bytes'] = len(elf)
    aggregate['font'] = meta
    aggregate.update(version=VERSION, output=str(output.relative_to(ROOT)), bytes=output.stat().st_size,
                     target_sha256=out_sha, source_build_version=BASE_VERSION,
                     source_build_sha256=previous['target_sha256'], changed_from_previous=['/SLPS_253.45;1'],
                     current_correction_report=f'work/output/ps2_system_text_{VERSION}_verification.json',
                     inherited_execution_checks_from_version=BASE_VERSION,
                     inherited_execution_checks_reason='Only the English pool, data pointer words, literal pairs '
                     'and four save-slot copy blocks change in the executable; all other resources are byte-identical.',
                     pcsx2_fresh_boot_verified=False)
    save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json', aggregate)
    font = ROOT/'work/build/ps2'/f'font_{VERSION}'; font.mkdir(exist_ok=True)
    for name in ('SLPS_253.45', 'patch.json'):
        shutil.copyfile(BASE/name, font/name)
    print('PS2', VERSION, output.name, out_sha)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--build', action='store_true'); a = p.parse_args()
    elf, meta, report = prepare()
    verify(bytes(elf), report, meta)
    save(BASE/'system_text.json', report)
    if a.build:
        package(bytes(elf), meta, report)
