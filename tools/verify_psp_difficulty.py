"""Execute PSP balance getters, New Game controls and save-tail persistence."""
import json
import struct

from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r

from patch_at_field import ROOT
import psp_difficulty as fix
from static2_extract import sections
from verify_psp_0410 import machine, cstr

OBJ, GAME, TABLE, TAIL = 0x1000000, 0x1010000, 0x1040000, 0x1100000
SP, RETURN = 0x11FF000, 0x11E0000


def put(u, address, value):
    u.mem_write(address, struct.pack('<I', value & 0xFFFFFFFF))


def word(u, address):
    return struct.unpack('<I', u.mem_read(address, 4))[0]


def call(u, address, *args, end=RETURN):
    for reg, value in zip((r.UC_MIPS_REG_A0, r.UC_MIPS_REG_A1, r.UC_MIPS_REG_A2, r.UC_MIPS_REG_A3), args):
        u.reg_write(reg, value)
    u.reg_write(r.UC_MIPS_REG_SP, SP)
    u.reg_write(r.UC_MIPS_REG_RA, RETURN)
    u.emu_start(address, end, count=200000)
    assert u.reg_read(r.UC_MIPS_REG_PC) == end, hex(u.reg_read(r.UC_MIPS_REG_PC))
    return u.reg_read(r.UC_MIPS_REG_V0)


def verify(original, patched, info):
    u, baseline = machine(patched), machine(original)
    mode = int(info['mode_va'], 16)
    routines = {key: int(row['va'], 16) for key, row in info['routines'].items()}
    static = (ROOT / 'work/build/STATIC2_ADD.orig').read_bytes()
    start, size, _ = sections(static)['Unit']
    for vm in (u, baseline):
        vm.mem_write(TABLE, static[start:start + size] + bytes(124))
        put(vm, GAME, TABLE)
    hp, rewards, _ = fix.balance_data()
    checks = 0
    for selected in (0, 1, 2, 0xFFFFFFFF):
        put(u, mode, selected)
        for index in range(512):
            for site, values in ((fix.HP_SITE, hp), (fix.REWARD_SITE, rewards)):
                expected = values[index] if selected == 0 else call(baseline, site, GAME, index)
                assert call(u, site, GAME, index) == expected, (selected, index, hex(site))
                assert u.reg_read(r.UC_MIPS_REG_SP) == SP
                checks += 1
    for site in (fix.HP_SITE, fix.REWARD_SITE):
        put(u, mode, 0)
        assert call(u, site, GAME, 512) == call(baseline, site, GAME, 512)

    u.reg_write(r.UC_MIPS_REG_S1, OBJ)
    put(u, OBJ + 0x56A4, 4)
    messages = []

    def message(vm, address, size, _):
        if address == 0x1B2510:
            messages.append(cstr(vm, vm.reg_read(r.UC_MIPS_REG_A1)).hex())
            vm.reg_write(r.UC_MIPS_REG_PC, vm.reg_read(r.UC_MIPS_REG_RA))

    handle = u.hook_add(UC_HOOK_CODE, message)
    call(u, fix.SETUP_SITE, end=fix.SETUP_SITE + 8)
    u.hook_del(handle)
    box = OBJ + 0x40C0
    assert len(messages) == 1
    assert word(u, box) == int(info['vtable_va'], 16)
    assert word(u, box + 0x194) == 1
    assert word(u, box + 0x208) == int(info['strings']['ps2'], 16)
    assert word(u, box + 0x20C) == int(info['strings']['psp'], 16)
    assert u.reg_read(r.UC_MIPS_REG_V0) == 5
    assert u.reg_read(r.UC_MIPS_REG_SP) == SP
    opening = []
    for frame in range(5):
        call(u, routines['opening'], box)
        opening.append(word(u, box + 0x190))
    assert opening == [1, 2, 3, 4, 0]
    assert word(u, box + 0xA8) == 180
    assert word(u, box + 0x218) == 178

    inputs = dict(arrow=0, confirm=False, cancel=False)
    delivered = []

    def controls(vm, address, size, _):
        if address == 0xBA7FC:
            result = int(vm.reg_read(r.UC_MIPS_REG_A1) == inputs['arrow'])
        elif address == 0xBA7C0:
            button = vm.reg_read(r.UC_MIPS_REG_A1)
            result = int((button == 101 and inputs['confirm']) or (button == 202 and inputs['cancel']))
        elif address == 0xBA6B4:
            delivered.append((vm.reg_read(r.UC_MIPS_REG_A2), vm.reg_read(r.UC_MIPS_REG_A3)))
            result = 1
        elif address in (0xBA784, 0x21F450, 0x22C888, 0x22CC78, 0x203FD8, 0x20403C):
            result = 0
        else:
            return
        vm.reg_write(r.UC_MIPS_REG_V0, result)
        vm.reg_write(r.UC_MIPS_REG_PC, vm.reg_read(r.UC_MIPS_REG_RA))

    handle = u.hook_add(UC_HOOK_CODE, controls)
    u.mem_write(box + 0xB8, struct.pack('<H', 1))
    put(u, box + 0x8C, 101)
    put(u, box + 0x90, 202)
    put(u, box + 0x134, 1)
    put(u, box + 0x138, 2)
    input_cases = []
    for selected, arrow in ((0, 0x400040), (1, 0x100010), (0, 0x100010), (1, 0x400040)):
        inputs.update(arrow=arrow, confirm=False, cancel=False)
        put(u, box + 0x194, selected)
        call(u, routines['controls'], box)
        assert word(u, box + 0x194) == 1 - selected
        assert word(u, box + 0x218) == 178
        input_cases.append(dict(before=selected, after=1 - selected))
    for selected, cancel in ((0, False), (1, False), (1, True)):
        inputs.update(arrow=0, confirm=not cancel, cancel=cancel)
        put(u, box + 0x194, selected)
        call(u, routines['controls'], box)
        assert delivered[-1] == ((2, 0) if cancel else (1, selected))
    u.hook_del(handle)
    for selected, event, previous in ((0, 1, 1), (1, 1, 0), (0, 2, 1), (1, 2, 0), (2, 1, 1)):
        put(u, mode, previous)
        put(u, OBJ + 0x56A8, event)
        put(u, OBJ + 0x56AC, selected)
        call(u, fix.ACCEPT_SITE, end=fix.ACCEPT_SITE + 8)
        assert word(u, mode) == (selected if event == 1 and selected < 2 else previous)
        assert word(u, OBJ + 0x56AC) == (0 if event == 1 and selected < 2 else selected)

    save_cases = []
    for source in sorted((ROOT / 'work/source/save_compare/psp').glob('*.decoded.bin')):
        tail = source.read_bytes()[-1024:]
        assert tail[fix.TAIL_OFFSET:fix.TAIL_OFFSET + 12] == bytes(12)
        for selected in (0, 1, 2):
            u.mem_write(TAIL, tail)
            put(u, mode, selected)
            u.reg_write(r.UC_MIPS_REG_S1, TAIL)
            u.mem_write(SP, bytes(16))
            put(u, SP + 12, RETURN)
            call(u, fix.SAVE_SITE)
            stamped = bytes(u.mem_read(TAIL, 1024))
            expected = bytearray(tail)
            struct.pack_into('<3I', expected, fix.TAIL_OFFSET, fix.MAGIC, fix.FORMAT, selected if selected < 2 else 1)
            assert stamped == expected
            put(u, mode, 1 - (selected & 1))
            call(u, routines['restore'], GAME, TAIL)
            assert word(u, mode) == (selected if selected < 2 else 1)
            save_cases.append(dict(source=source.name, mode=selected, marker_roundtrip=True))
    for magic, version, value in ((0, 1, 0), (fix.MAGIC, 2, 0), (fix.MAGIC, 1, 2), (fix.MAGIC, 1, 0xFFFFFFFF)):
        u.mem_write(TAIL + fix.TAIL_OFFSET, struct.pack('<3I', magic, version, value))
        put(u, mode, 0)
        call(u, routines['restore'], GAME, TAIL)
        assert word(u, mode) == 1
    # Execute the complete original serializer and compare every native field.
    for vm in (u, baseline):
        put(vm, GAME + 0x10014, 0x1080000)
        vm.mem_write(0x1080000, bytes(0x1000))
        vm.mem_write(TAIL, bytes([0xA5]) * 1024)
    put(u, mode, 0)
    call(baseline, 0x5781C, GAME, TAIL)
    call(u, 0x5781C, GAME, TAIL)
    stored = bytes(u.mem_read(TAIL, 1024))
    expected = bytearray(baseline.mem_read(TAIL, 1024))
    struct.pack_into('<3I', expected, fix.TAIL_OFFSET, fix.MAGIC, fix.FORMAT, 0)
    assert stored == expected
    # Settings restoration runs before the original loader reads its fields.
    put(u, mode, 1)
    call(u, fix.LOAD_SITE, GAME, TAIL, end=fix.LOAD_SITE + 8)
    assert word(u, mode) == 0
    assert u.reg_read(r.UC_MIPS_REG_A0) == GAME and u.reg_read(r.UC_MIPS_REG_A1) == TAIL
    assert u.reg_read(r.UC_MIPS_REG_SP) == SP - 48
    # Scenario loading must select balance before the unit deserializer runs.
    ordering = []
    def loader(vm, address, size, _):
        if address == 0x182A20:
            ordering.append((word(vm, mode), vm.reg_read(r.UC_MIPS_REG_A0), vm.reg_read(r.UC_MIPS_REG_A1)))
            vm.reg_write(r.UC_MIPS_REG_PC, vm.reg_read(r.UC_MIPS_REG_RA))
    handle = u.hook_add(UC_HOOK_CODE, loader)
    put(u, mode, 1)
    u.reg_write(r.UC_MIPS_REG_S1, TAIL)
    u.reg_write(r.UC_MIPS_REG_S3, 0x1080000)
    call(u, fix.EARLY_SITE, GAME, end=fix.EARLY_SITE + 8)
    u.hook_del(handle)
    assert ordering == [(0, GAME, 0x1080000)]
    assert u.reg_read(r.UC_MIPS_REG_SP) == SP
    return dict(passed=True, getter_cases=checks, out_of_range_cases=2,
                menu_setup=True, opening_frames=opening, directional_cases=input_cases,
                confirm_cancel_cases=3, accept_cases=5, save_roundtrips=save_cases,
                old_and_invalid_saves_default_psp=True, complete_native_serializer=True,
                settings_restore_before_load=True, scenario_restore_before_unit_decode=True,
                in_game_validation='pending')


if __name__ == '__main__':
    root = ROOT / 'work/build/psp_difficulty_061'
    report = verify((root / 'BOOT_BASE.BIN').read_bytes(), (root / 'BOOT_PATCHED.BIN').read_bytes(),
                    json.loads((root / 'patch.json').read_text()))
    (root / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
