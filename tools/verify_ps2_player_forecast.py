"""Run the action-row dispatch with the original, public and candidate ELFs."""
import json
import struct
from pathlib import Path

from unicorn import UcError, UC_HOOK_CODE, UC_ERR_READ_UNALIGNED
from unicorn import mips_const as r

from insert_text import encode
from ps2_font4x import FILE_BIAS
from verify_ps2_font import machine


def run(data, action, counter, mask, dirty, stop):
    vm = machine(data, r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    sp, menu, font = 0xa00000, 0x900000, 0x910000
    vm.mem_write(sp, bytes([dirty]) * 0x100)
    vm.mem_write(menu + 0x260, bytes([action]))
    vm.mem_write(menu + 0x25c, struct.pack('<I', counter))
    vm.mem_write(menu + 0x4ec, struct.pack('<I', mask))
    # Exercise the existing strcpy byte path for an ordinary pool string.
    vm.mem_write(sp + 0x100, struct.pack('<I', 0x910801))
    vm.mem_write(0x910801, encode('Evade'))
    for reg, value in [(r.UC_MIPS_REG_S0, 1), (r.UC_MIPS_REG_S1, menu),
                       (r.UC_MIPS_REG_S2, font)]:
        vm.reg_write(reg, value)
    seen = []
    def trace(u, pc, size, _):
        seen.append(pc)
        if pc == stop:
            u.emu_stop()
    vm.hook_add(UC_HOOK_CODE, trace)
    try:
        vm.emu_start(0x17ab34, 0x920000, count=2500)
    except UcError as exc:
        assert exc.errno == UC_ERR_READ_UNALIGNED, (exc, hex(seen[-1]))
        return None, (seen[-1], vm.reg_read(r.UC_MIPS_REG_V0))
    assert seen[-1] == stop, (hex(seen[-1]), hex(stop))
    assert vm.reg_read(r.UC_MIPS_REG_SP) == sp
    assert vm.reg_read(r.UC_MIPS_REG_S1) == menu
    assert vm.reg_read(r.UC_MIPS_REG_S2) == font
    return bytes(vm.mem_read(sp, 0x100)), None


def verify(original, public, previous, target, directory):
    paths = [(0, 0, 'Attack', (0x17ab58, 0x77b5b9)),
             (1, 0, 'No Counter', (0x17ab88, 0x779ada))]
    faults = []
    for action, counter, label, fault in paths:
        assert run(original, action, counter, 0, 0xa5, 0x17abb8)[1] is None
        for version, data in [('0.9.0', public), ('0.9.4', previous)]:
            assert run(data, action, counter, 0, 0xa5, 0x17abb8)[1] == fault
            faults.append(dict(version=version, label=label, pc=hex(fault[0]), address=hex(fault[1])))
    cases = []
    choices = [(a, c, label) for a, c, label, _ in paths]
    choices.extend([(1, 1, 'Evade'), (2, 0, 'Evade')])
    for action, counter, label in choices:
        for dirty in (0, 0xa5, 0x7f):
            for mask in (0, 1):
                # After the copy, the native renderer can overlay the disabled
                # marker. Compare its original bytes, including the terminator.
                before, error = run(target, action, counter, mask, dirty, 0x17abb8)
                raw = encode(label)
                expected = bytearray(raw + bytes([dirty]) * (0x100 - len(raw)))
                assert error is None and before == expected
                after, error = run(target, action, counter, mask, dirty, 0x17abdc)
                if mask:
                    offset = 0x49a4b0 - FILE_BIAS
                    expected[:9] = original[offset:offset + 9]
                assert error is None and after == expected, (action, counter, dirty, mask)
                cases.append(dict(label=label, action=action, counter=counter, mask=mask, fill=dirty))
    result = dict(reproduced=faults, verified_paths=cases)
    (Path(directory) / 'player_forecast_execution.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf8')
    return result
