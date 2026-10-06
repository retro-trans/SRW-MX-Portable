"""Execute native detail text paths and validate description resource rebuild."""
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from fix_ps2_ui_details import ROOT, BASE, VERSION, SOURCE_VERSION, sha
from port_ps2_prologue import save
from verify_ps2_font import machine
from static2_extract import sections, index
import insert_text as it


def verify(base=BASE, version=VERSION):
    data = (base / 'SLPS_253.45').read_bytes()
    fix = (base / 'FIX00.DAT').read_bytes()
    meta = json.loads((base / 'patch.json').read_text())
    changes = json.loads((base / 'ui_details.json').read_text())
    previous = ROOT / 'work/build/ps2' / f'ui_fix_{SOURCE_VERSION}'
    assert sha(data) == meta['target_sha256']

    def off(va):
        for n in range(struct.unpack_from('<H', data, 44)[0]):
            kind, offset, start, _, size, *_ = struct.unpack_from('<8I', data, 52 + n * 32)
            if kind == 1 and start <= va < start + size:
                return offset + va - start
        raise AssertionError(hex(va))

    def text(va):
        offset = off(va)
        return data[offset:data.index(0, offset)]

    for row in changes['data_references']:
        ptr = struct.unpack_from('<I', data, off(int(row['site'], 16)))[0]
        assert ptr == int(row['target'], 16)
        assert text(ptr) == it.encode(row['english'])[:-1]
    for row in changes['instruction_words']:
        assert struct.unpack_from('<I', data, off(int(row['va'], 16)))[0] == int(row['new'], 16)
    for row in changes['storage']:
        assert text(int(row['va'], 16)) == it.encode(row['english'])[:-1]

    u = machine(data)
    initial = u.context_save()
    captured = []

    def stop_draw(vm, address, size, user):
        if address != 0x130610:
            return
        ptr = vm.reg_read(reg.UC_MIPS_REG_A1)
        raw = bytes(vm.mem_read(ptr, 64)).split(b'\0')[0]
        captured.append(raw)
        vm.emu_stop()

    draw_hook = u.hook_add(UC_HOOK_CODE, stop_draw)
    for row in changes['draw_stubs']:
        u.context_restore(initial)
        captured.clear()
        for register, value in ((reg.UC_MIPS_REG_A0, 0x900000),
                                (reg.UC_MIPS_REG_A2, 100), (reg.UC_MIPS_REG_A3, 200),
                                (reg.UC_MIPS_REG_T0, 0xffffffffffffffff)):
            u.reg_write(register, value)
        u.emu_start(int(row['site'], 16), 0x920000, count=50)
        assert captured == [it.encode(row['english'])[:-1]]
        assert u.reg_read(reg.UC_MIPS_REG_A0) == 0x900000
        assert u.reg_read(reg.UC_MIPS_REG_A2) == 100
        assert u.reg_read(reg.UC_MIPS_REG_A3) == 200
        assert u.reg_read(reg.UC_MIPS_REG_RA) == int(row['site'], 16) + 8
    u.hook_del(draw_hook)

    flag_cases = []
    widths = {g['character']: g['width'] for g in meta['glyphs']}
    flag_pairs = [('なし', 'None'), ('あり', 'Yes'), ('貫通', 'Pierce'),
                  ('拡散', 'Spread'), ('無効', 'Null'), ('弱体', 'Weaken')]
    # Actual VWF getter executes on every cached value, including unchanged numbers.
    for w, h in ((24, 24), (20, 24), (12, 24)):
        for jp, en in flag_pairs + [(None, '--'), (None, '100'), (None, 'Asst')]:
            u.context_restore(initial)
            raw = jp.encode('cp932') + b'\0' if jp else it.encode(en)
            u.mem_write(0x910000, raw + bytes(256 - len(raw)))
            u.mem_write(0x900000, struct.pack('<2f', w, h) + bytes(64))
            u.reg_write(reg.UC_MIPS_REG_A0, 0x940000)
            u.reg_write(reg.UC_MIPS_REG_A1, 0x910000)
            u.reg_write(reg.UC_MIPS_REG_S4, 0x900000)
            u.reg_write(reg.UC_MIPS_REG_RA, 0x920000)
            u.emu_start(int(changes['weapon_flags']['target'], 16), 0x920000, count=10000)
            actual = bytes(u.mem_read(0x910000, len(it.encode(en))))
            assert actual == it.encode(en), (jp, en, actual.hex(), it.encode(en).hex())
            size = h if w * 2 == h else min(w, h)
            expected = round(sum(widths[c] for c in en) * size / 24)
            assert abs(u.reg_read(reg.UC_MIPS_REG_V0) - expected) <= 1, (en, w, h)
            assert u.reg_read(reg.UC_MIPS_REG_SP) == 0xa00000
            assert bytes(u.mem_read(0x900000, 8)) == struct.pack('<2f', w, h)
            flag_cases.append(dict(text=en, native_cell=[w, h], width=u.reg_read(reg.UC_MIPS_REG_V0)))

    # Branches must select the correct translated header and preserve setup calls.
    headers = []

    def stop_header(vm, address, size, user):
        if address in (0x143ac0, 0x10cf38):
            ptr = vm.reg_read(reg.UC_MIPS_REG_A1)
            captured.append(bytes(vm.mem_read(ptr, 64)).split(b'\0')[0])
            vm.emu_stop()

    hook = u.hook_add(UC_HOOK_CODE, stop_header)
    for mode, label in ((0, 'Ability Search'), (1, 'Skill Search')):
        u.context_restore(initial)
        captured.clear()
        u.reg_write(reg.UC_MIPS_REG_S0, 0x940000)
        u.mem_write(0x94029c, struct.pack('<I', mode))
        u.emu_start(0x18f53c, 0x920000, count=100)
        assert captured == [it.encode(label)[:-1]], (mode, captured)
        headers.append(label)
    for mode, label in enumerate(('Allied Units', 'Enemy Units', 'Neutral Units', 'Unit Info')):
        u.context_restore(initial)
        captured.clear()
        u.reg_write(reg.UC_MIPS_REG_S0, 0x940000)
        u.mem_write(0x941630, struct.pack('<I', mode))
        u.emu_start(0x147ed8, 0x920000, count=100)
        assert captured == [it.encode(label)[:-1]], (mode, captured)
        headers.append(label)
    u.hook_del(hook)

    old_fix = (previous / 'FIX00.DAT').read_bytes()
    old_sections = sections(old_fix, 0)
    new_sections = sections(fix, 0)
    assert sha(fix) == changes['descriptions']['target_sha256']
    preserved = []
    for tag, (offset, size, count) in old_sections.items():
        if tag in ('Fixh', 'Sent', 'XSkl', 'Xabl'):
            continue
        new_off, new_size, new_count = new_sections[tag]
        assert (size, count) == (new_size, new_count)
        assert old_fix[offset:offset + size] == fix[new_off:new_off + new_size], tag
        preserved.append(tag)
    # Every existing sentence keeps its original text or original external pointer.
    sent = new_sections['Sent'][0]
    old_sent, _, old_count = old_sections['Sent']
    for n in range(old_count):
        old_ptr = struct.unpack_from('<I', old_fix, old_sent + 12 + 4 * n)[0]
        new_ptr = struct.unpack_from('<I', fix, sent + 12 + 4 * n)[0]
        if old_ptr & 0x80000000:
            assert old_ptr == new_ptr
        else:
            old_start, new_start = old_sent + old_ptr, sent + new_ptr
            assert old_fix[old_start:old_fix.index(0, old_start)] == fix[new_start:fix.index(0, new_start)]
    u.mem_map(0xb00000, (len(fix) + 4095) & ~4095)
    u.mem_write(0xb00000, fix)
    u.mem_write(0x940000, struct.pack('<I', 0xb00000 + sent))
    initial = u.context_save()
    line_checks = 0
    indexes = {tag: index(fix, new_sections[tag][0], new_sections[tag][2]) for tag in ('XSkl', 'Xabl')}
    for row in changes['description_rows']:
        assert indexes[row['table']][row['entry']] == row['sentence_ids']
        assert ' '.join(row['lines']) == ' '.join(it.clean(row['english']).split())
        for ident, line in zip(row['sentence_ids'], row['lines']):
            u.context_restore(initial)
            u.reg_write(reg.UC_MIPS_REG_A0, 0x940000)
            u.reg_write(reg.UC_MIPS_REG_A1, ident)
            u.reg_write(reg.UC_MIPS_REG_RA, 0x920000)
            u.emu_start(0x332518, 0x920000, count=100)
            ptr = u.reg_read(reg.UC_MIPS_REG_V0)
            assert bytes(u.mem_read(ptr, len(it.encode(line)))) == it.encode(line)
            assert sum(widths[c] for c in line) <= 512
            line_checks += 1
    scenario_assets = []
    for name in ('MAP.BIN', 'STAGE.BIN', 'D2MAPH.BIN', 'PACKMAPC.BIN', 'STATIC.BIN', 'FACEPACK.BIN'):
        from ps2_resource_preservation import check
        check(base,previous,name)
        scenario_assets.append(name)
    result = dict(version=version, passed=True, references=len(changes['data_references']),
                  instruction_checks=len(changes['instruction_words']),
                  native_draw_pointer_cases=len(changes['draw_stubs']),
                  native_header_cases=headers, native_flag_width_cases=flag_cases,
                  native_description_line_reads=line_checks, retained_sentence_ids=old_count,
                  unchanged_database_sections=preserved, description_width_limit=512,
                  preserved_scenario_assets=scenario_assets, native_font=True,
                  texture_replacement=False, psp_opening_preserved=True)
    save(ROOT / 'work/output' / f'ps2_ui_details_{version}_execution.json', result)
    print(json.dumps(dict(version=version, passed=True, descriptions=line_checks,
                         flag_cases=len(flag_cases), headers=len(headers))))
    return result


if __name__ == '__main__':
    verify()
