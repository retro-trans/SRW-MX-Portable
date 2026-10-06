"""Execute both native chapter-card animation paths with real campaign lookup."""
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from verify_ps2_font import machine
from verify_ps2_difficulty import run, put, word
from port_ps2_translations import ROOT
from ps2_prologue_numbering import SITES


def chapter_card(data, chapter, group, cleared, function):
    u = machine(data)
    window, hero, campaign = 0x810000, 0x820000, 0x830000
    put(u, 0x3c8cb4, hero); put(u, 0x3c8cbc, campaign)
    put(u, hero+0x5f0, cleared)
    put(u, campaign+0x3a8, chapter); put(u, campaign+0x3ac, group)
    put(u, window+0x1c, 0)
    seen = []
    def service(vm, pc, size, unused):
        if pc in (0x2e2e08, 0x2e3158):
            if pc == 0x2e3158:
                seen.append(dict(animation=vm.reg_read(reg.UC_MIPS_REG_A1),
                                 number=vm.reg_read(reg.UC_MIPS_REG_A3)))
            vm.reg_write(reg.UC_MIPS_REG_V0, 1)
            vm.reg_write(reg.UC_MIPS_REG_PC, vm.reg_read(reg.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE, service)
    u.reg_write(reg.UC_MIPS_REG_A0, window)
    stack = u.reg_read(reg.UC_MIPS_REG_SP)
    run(u, function)
    assert u.reg_read(reg.UC_MIPS_REG_SP) == stack
    assert word(u, hero+0x5f0) == cleared
    assert word(u, campaign+0x3a8) == chapter
    assert word(u, campaign+0x3ac) == group
    assert len(seen) == 1, seen
    return seen[0]


def objective_numbers(data, chapter, cleared):
    stage = (ROOT/'work/build/ps2/prologue_0.1.8/STAGE.BIN').read_bytes()
    battle, hero, campaign, stage_va, args = 0x850000, 0x820000, 0x830000, 0x900000, 0x870000
    values = []
    for script in (False, True):
        u = machine(data)
        u.mem_write(stage_va, stage)
        put(u, campaign, stage_va); put(u, campaign+4, stage_va)
        put(u, campaign+0x3a8, chapter); put(u, campaign+0x3ac, 0)
        put(u, 0x3c8cbc, campaign); put(u, 0x3c8cb4, hero)
        put(u, hero+0x5f0, cleared)
        if script:
            u.mem_write(args, struct.pack('<12i', 0x58, *([0]*11)))
            def service(vm, pc, size, unused):
                if pc in (0x12ee18, 0x143460, 0x143318):
                    vm.reg_write(reg.UC_MIPS_REG_V0, 1)
                    vm.reg_write(reg.UC_MIPS_REG_PC, vm.reg_read(reg.UC_MIPS_REG_RA))
            u.hook_add(UC_HOOK_CODE, service)
            u.reg_write(reg.UC_MIPS_REG_A0, battle)
            u.reg_write(reg.UC_MIPS_REG_A1, args)
            stack = u.reg_read(reg.UC_MIPS_REG_SP)
            run(u, 0x2fe620)
            assert u.reg_read(reg.UC_MIPS_REG_SP) == stack
            values.append(word(u, battle+0x1b20+0x230))
        else:
            # Run the menu's native display preparation and campaign title lookup,
            # ending immediately after both values reach the objective window.
            u.reg_write(reg.UC_MIPS_REG_S1, hero)
            u.reg_write(reg.UC_MIPS_REG_S2, campaign)
            u.reg_write(reg.UC_MIPS_REG_S0, battle)
            stopped = []
            def stop(vm, pc, size, unused):
                if pc == 0x224f24:
                    stopped.append(pc); vm.emu_stop()
            u.hook_add(UC_HOOK_CODE, stop)
            u.emu_start(0x224ef8, 0x920000, count=10000)
            assert stopped == [0x224f24]
            values.append(word(u, battle+0x230))
        assert word(u, hero+0x5f0) == cleared
    return values


def verify(data):
    # Reproduce the old display code without requiring a previous local build.
    old = bytearray(data)
    for address, original, name in SITES:
        offset = address - 0xff000
        assert struct.unpack_from('<I', data, offset)[0] == original & 0xffff0000, name
        struct.pack_into('<I', old, offset, original)
    old = bytes(old)
    observations = []
    for chapter in (0, 1):
        for group in (0, 2):
            for cleared in (1, 2, 9, 10, 30, 54, 55, 56):
                for function in (0x348588, 0x348908):
                    prior = chapter_card(old, chapter, group, cleared, function)
                    current = chapter_card(data, chapter, group, cleared, function)
                    assert prior['number'] == cleared+1 and current['number'] == cleared
                    assert prior['animation'] == current['animation']
                    observations.append(dict(route=chapter, group=group,
                                             cleared_battles=cleared,
                                             animation_path=hex(function),
                                             animation=current['animation'],
                                             old_chapter=prior['number'], chapter=current['number']))
        for function in (0x348588, 0x348908):
            prior = chapter_card(old, chapter, 4, 0, function)
            current = chapter_card(data, chapter, 4, 0, function)
            assert prior == current == dict(animation=0x1b, number=0)
    objective_cases = 0
    for chapter in (0, 1):
        for cleared in (0, 1, 2, 10, 55, 56):
            assert objective_numbers(old, chapter, cleared) == [cleared+1]*2
            assert objective_numbers(data, chapter, cleared) == [cleared]*2
            objective_cases += 2
    return dict(native_animation_cases=len(observations),
                native_objective_display_cases=objective_cases,
                prologue_fallback_animation_unchanged=True,
                original_off_by_one_reproduced=True,
                campaign_and_clear_count_unchanged=True, cases=observations)


if __name__ == '__main__':
    data = (ROOT/'work/build/ps2/prologue_0.1.8/SLPS_253.45').read_bytes()
    result = verify(data)
    (ROOT/'work/output/ps2_prologue_0.1.8_numbering_execution.json').write_text(
        json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}, indent=2))
