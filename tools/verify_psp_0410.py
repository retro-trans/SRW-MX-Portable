"""Execute the affected native copy/row-building code with buffer guards.

Unicorn runs the original MIPS routines. The Level Up fixture supplies skill
getters/window callbacks and a small printf stand-in; the native string copy,
numeric glyph conversion, row stride and stored row pointers run unmodified.
This is a controlled regression fixture, not a battle playthrough.
"""
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import *
import insert_text as it
import fix_psp_levelup as lu
from verify_text_build import read_iso

ROOT = Path(__file__).resolve().parents[1]
GUARD = b'GUARD01234567890'


def machine(boot):
    u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0, 0x1000000)
    ph = struct.unpack_from('<I', boot, 28)[0]
    size = struct.unpack_from('<I', boot, ph + 16)[0]
    u.mem_write(0, boot[0x60:0x60 + size])
    u.mem_map(0x1000000, 0x200000)
    return u


def invoke(u, pc, args):
    for reg, value in zip([UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3], args):
        u.reg_write(reg, value)
    u.reg_write(UC_MIPS_REG_SP, 0x11FF000)
    u.reg_write(UC_MIPS_REG_RA, 0x11E0000)
    u.emu_start(pc, 0x11E0000, count=2000000)
    assert u.reg_read(UC_MIPS_REG_PC) == 0x11E0000


def cstr(u, pointer):
    return bytes(u.mem_read(pointer, 256)).split(b'\0')[0]


def narration(boot):
    u = machine(boot)
    def search(u, pc, size, _):
        if pc == 0x259604:  # no native placeholder prefix in these English lines
            u.reg_write(UC_MIPS_REG_V0, 0)
            u.reg_write(UC_MIPS_REG_PC, u.reg_read(UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE, search)
    def copy(line):
        u.mem_write(0x1000000, bytes(0x1300))
        u.mem_write(0x1000100, GUARD)
        u.mem_write(0x10012B4, struct.pack('<I', 0x1010000))
        u.mem_write(0x1010000, struct.pack('<III', 7, 0x1011000, 207))
        u.mem_write(0x1011000, it.encode(line))
        invoke(u, 0x171110, [0x1000000, 0, 0])
        assert cstr(u, 0x1000080) == it.encode(line)[:-1]
        return bytes(u.mem_read(0x1000100, len(GUARD)))
    _, bt = it.boot_translations()
    old_bad = [line for paras in bt['narration'].values() for p in paras
               for line in it.wrap(p, 416) if len(it.encode(line)) > 128]
    assert old_bad and all(copy(line) != GUARD for line in old_bad)
    lines = [line for paras in bt['narration'].values() for p in paras for line in it.wrap_narration(p)]
    assert all(copy(line) == GUARD for line in lines)
    original = (ROOT / 'work/build/iso/BOOT.BIN').read_bytes()
    semantic = bytearray(original); it.patch_narration_script(semantic, bt)
    slots = it.narration_slots(bt)
    records = 0
    for va in range(it.NARRATION_SCRIPT, len(original) - 0x60 - 12, 12):
        delay, kind, target = struct.unpack_from('<iII', semantic, va + 0x60)
        if kind != 7:
            break
        got_delay, got_kind, pointer = struct.unpack_from('<iII', boot, va + 0x60)
        assert (got_delay, got_kind) == (delay, kind)
        if target in slots:
            assert boot[pointer+0x60:boot.index(b'\0', pointer+0x60)+1] == it.encode(slots[target][0])
        else:
            assert pointer == target
        records += 1
    return dict(unsafe_old_lines_reproduce_corruption=len(old_bad), safe_lines_executed=len(lines),
                native_row_copy_guard_preserved=True, original_record_timing_verified=records)


def level_up(boot, fixed):
    u = machine(boot)
    obj, ctx, manager, result, strings = 0x1000000, 0x1040000, 0x1080000, 0x1090000, 0x10A0000
    u.mem_write(obj+0x2C, struct.pack('<I', ctx))
    u.mem_write(ctx+0x1000C, struct.pack('<I', manager))
    ids = [2, 6, 14, 22, 10, 18]
    names = ['Newtype Lv', 'Sword Cut Lv', 'Shield Defense Lv', 'Assist Attack Lv', 'Support Atk Lv', 'Gunfight Lv']
    r = bytearray(0x9C)
    for i, (idx, name) in enumerate(zip(ids, names)):
        u.mem_write(strings+idx*256, it.encode(name))
        for offset, value in [(0x20, idx), (0x6C, idx), (0x38, 1), (0x84, 2)]:
            struct.pack_into('<I', r, offset+i*4, value)
    u.mem_write(result, bytes(r))
    rows = lu.row_address(boot) if fixed else 0x2C63DC
    stride = 256 if fixed else 32
    for i in range(6):
        u.mem_write(rows+i*stride, bytes([0xA5])*stride)
    def callbacks(u, pc, size, _):
        if pc in (0x1B4B9C, 0xBA538, 0x2016B0, 0x2015C0):
            pass
        elif pc == 0x5BE04:
            u.reg_write(UC_MIPS_REG_V0, u.reg_read(UC_MIPS_REG_A1))
        elif pc == 0x5BE24:
            u.reg_write(UC_MIPS_REG_V0, 1)
        elif pc == 0x5BF24:
            u.reg_write(UC_MIPS_REG_V0, strings+u.reg_read(UC_MIPS_REG_A1)*256)
        elif pc == 0x5BEC8:
            u.reg_write(UC_MIPS_REG_V0, strings)
        elif pc == 0x259020:
            dest, fmt, a2, a3 = [u.reg_read(x) for x in [UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3]]
            template = cstr(u, fmt)
            if template == b'%s%s':
                text = cstr(u, a2)+cstr(u, a3)
            else:
                assert template == b'%d', template
                text = str(a2).encode('ascii')
            u.mem_write(dest, text+b'\0'); u.reg_write(UC_MIPS_REG_V0, len(text))
        else:
            return
        u.reg_write(UC_MIPS_REG_PC, u.reg_read(UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE, callbacks)
    invoke(u, 0xCE26C, [obj, result])
    expected = [it.encode(name+'1')[:-1] for name in names]
    actual = [cstr(u, rows+i*stride) for i in range(6)]
    stored = [struct.unpack('<I', u.mem_read(obj+0xA39C+i*4,4))[0] for i in range(6)]
    assert stored == [rows+i*stride for i in range(6)]
    if fixed:
        assert actual == expected, actual
        for i, value in enumerate(expected):
            assert bytes(u.mem_read(rows+i*stride+len(value)+1,stride-len(value)-1)) == bytes([0xA5])*(stride-len(value)-1)
    else:
        assert actual != expected
    return dict(native_row_pointers_verified=True, adjacent_rows_intact=fixed, fixture_names=names)


def main():
    fixed = read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.10.iso'), ['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    old = read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.9.iso'), ['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    report = dict(version='0.4.10', narration=narration(fixed), old_level_up=level_up(old, False), new_level_up=level_up(fixed, True))
    (ROOT/'work/output/psp_fixes_0.4.10_native_tests.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
