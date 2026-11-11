"""PS2/PSP balance selection in the PSP New Game confirmation."""
import json
import struct

import insert_text as it
from patch_at_field import ROOT, sha
from static2_extract import sections, strtable

VERSION = '0.4.61'
TAIL_OFFSET = 0x3E0
MAGIC = 0x4442584D
FORMAT = 1
VTABLE = 0x2B8EDC
VTABLE_BYTES = 0x70
HP_SITE, REWARD_SITE = 0x5C06C, 0x5C14C
SETUP_SITE, ACCEPT_SITE = 0x172F88, 0x173020
SAVE_SITE, LOAD_SITE = 0x57A24, 0x57EC8
EARLY_SITE, CLEANUP_SITE = 0x72944, 0x173114


def balance_data():
    ps2 = (ROOT / 'work/source/ps2/FIX00.DAT').read_bytes()
    psp = (ROOT / 'work/build/STATIC2_ADD.orig').read_bytes()
    a, b = sections(ps2, 0), sections(psp)
    an = strtable(ps2, a['Strg'][0], a['Strg'][2])
    bn = strtable(psp, b['Strg'][0], b['Strg'][2])
    hp, rewards, changes = [], [], []
    for index in range(512):
        x, y = a['Unit'][0] + 12 + index * 124, b['Unit'][0] + 12 + index * 124
        same = an[struct.unpack_from('<H', ps2, x)[0]] == bn[struct.unpack_from('<H', psp, y)[0]]
        old_hp, native_hp = struct.unpack_from('<I', ps2, x + 12)[0], struct.unpack_from('<I', psp, y + 12)[0]
        old_reward, native_reward = struct.unpack_from('<H', ps2, x + 26)[0], struct.unpack_from('<H', psp, y + 26)[0]
        hp.append(old_hp if same else native_hp)
        rewards.append(old_reward if same else native_reward)
        if same and (old_hp != native_hp or old_reward != native_reward):
            changes.append(dict(id=index, ps2_hp=old_hp, psp_hp=native_hp,
                                ps2_reward=old_reward, psp_reward=native_reward))
    assert sum(c['ps2_hp'] != c['psp_hp'] for c in changes) == 139
    assert sum(c['ps2_reward'] != c['psp_reward'] for c in changes) == 294
    return hp, rewards, changes


def patch_boot(boot):
    import keystone
    marker = b'MX_PSP_BALANCE1\0'
    if marker in boot:
        raise AssertionError('Difficulty feature already present. Build from the registered baseline.')
    original = (ROOT / 'work/build/iso/BOOT.BIN').read_bytes()
    hp, rewards, changes = balance_data()
    ph = struct.unpack_from('<I', boot, 28)[0]
    base = (struct.unpack_from('<I', boot, ph + 20)[0] + 15) & ~15
    blob = bytearray(marker)
    mode = base + len(blob)
    blob += struct.pack('<4I', 1, 0, 0, 0)
    hp_va = base + len(blob)
    blob += struct.pack('<512I', *hp)
    reward_va = base + len(blob)
    blob += struct.pack('<512H', *rewards)
    vtable = base + len(blob)
    blob += boot[VTABLE + 0x60:VTABLE + 0x60 + VTABLE_BYTES]
    strings = {}
    for key, text in [('question', 'Choose the game balance.'),
                      ('details', 'PSP: enemy HP +50%, funds -20%.'),
                      ('ps2', 'PS2 - Original'), ('psp', 'PSP - Harder')]:
        strings[key] = base + len(blob)
        blob += it.encode(text)
    blob += bytes(-len(blob) % 4)
    routines, relocs, hooks = {}, [], []
    addresses = {mode, hp_va, reward_va, vtable, VTABLE, *strings.values()}
    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 | keystone.KS_MODE_LITTLE_ENDIAN)

    def ptr(register, address):
        high = (address + 0x8000) >> 16
        low = address - (high << 16)
        return f'lui {register}, {high}\naddiu {register}, {register}, {low}'

    def routine(name, source):
        va = base + len(blob)
        code = bytes(ks.asm('.set noreorder\n.option pic0\n' + source, va)[0])
        words = list(struct.unpack(f'<{len(code)//4}I', code))
        for index, word in enumerate(words):
            if word >> 26 in (2, 3):
                relocs.append((va + index * 4, 4))
            if word >> 26 == 15 and index + 1 < len(words):
                following = words[index + 1]
                low = following & 65535
                target = ((word & 65535) << 16) + low - (65536 if low >= 32768 else 0)
                if following >> 26 == 9 and target in addresses:
                    assert (word >> 16) & 31 == (following >> 21) & 31 == (following >> 16) & 31
                    relocs.extend([(va + index * 4, 5), (va + index * 4 + 4, 6)])
        routines[name] = dict(va=hex(va), bytes=len(code))
        blob.extend(code)
        return va

    for name, site, table, shift, load in [('hp', HP_SITE, hp_va, 2, 'lw'),
                                           ('reward', REWARD_SITE, reward_va, 1, 'lhu')]:
        routine(name, f'''
            {ptr('$t0', mode)}
            lw $t0, 0($t0)
            bnez $t0, normal
            sltiu $t1, $a1, 512
            beqz $t1, normal
            sll $t1, $a1, {shift}
            {ptr('$t0', table)}
            addu $t0, $t0, $t1
            jr $ra
            {load} $v0, 0($t0)
        normal:
            addiu $sp, $sp, -16
            sw $ra, 12($sp)
            j {site + 8}
            nop
        ''')

    opening = routine('opening', '''
        addiu $v0, $zero, -1
        sw $v0, 0x270($a0)
        addiu $a1, $zero, 180
        addiu $a2, $zero, 46
        addiu $a3, $a0, 0x210
        j 0x1afc60
        addiu $t0, $zero, 5
    ''')
    width = routine('cursor_width', 'jr $ra\naddiu $v0, $zero, 178')
    controls = routine('controls', '''
        addiu $sp, $sp, -16
        sw $ra, 12($sp)
        sw $a0, 8($sp)
        jal 0x1b2b00
        nop
        lw $t0, 8($sp)
        addiu $t1, $zero, 178
        sw $t1, 0x218($t0)
        lw $ra, 12($sp)
        jr $ra
        addiu $sp, $sp, 16
    ''')
    for offset, target in [(0x24, opening), (0x2C, controls), (0x68, width)]:
        struct.pack_into('<I', blob, vtable - base + offset, target)
    for offset in range(0, VTABLE_BYTES, 4):
        if struct.unpack_from('<I', blob, vtable - base + offset)[0]:
            relocs.append((vtable + offset, 2))

    routine('setup', f'''
        addiu $sp, $sp, -16
        sw $ra, 12($sp)
        addiu $a0, $s1, 0x3e80
        {ptr('$a1', strings['details'])}
        jal 0x1b2510
        addiu $a2, $zero, 11
        addiu $t0, $s1, 0x40c0
        {ptr('$v0', vtable)}
        sw $v0, 0($t0)
        {ptr('$v0', strings['ps2'])}
        sw $v0, 0x208($t0)
        {ptr('$v0', strings['psp'])}
        sw $v0, 0x20c($t0)
        addiu $v0, $zero, 150
        sw $v0, 0xa0($t0)
        addiu $v0, $zero, 175
        sw $v0, 0xa4($t0)
        addiu $v0, $zero, 8
        sw $v0, 0x200($t0)
        sw $v0, 0x204($t0)
        addiu $v0, $zero, 1
        sw $v0, 0x194($t0)
        lw $v0, 0x56a4($s1)
        addiu $v0, $v0, 1
        lw $ra, 12($sp)
        j {SETUP_SITE + 8}
        addiu $sp, $sp, 16
    ''')
    routine('accept', f'''
        lw $v0, 0x56a8($s1)
        addiu $a3, $zero, 1
        bne $v0, $a3, finish
        lw $t0, 0x56ac($s1)
        sltiu $t1, $t0, 2
        beqz $t1, finish
        nop
        {ptr('$t1', mode)}
        sw $t0, 0($t1)
        sw $zero, 0x56ac($s1)
    finish:
        j {ACCEPT_SITE + 8}
        nop
    ''')
    routine('cleanup', f'''
        addiu $sp, $sp, -16
        sw $ra, 12($sp)
        jal 0x201690
        nop
        addiu $a0, $s1, 0x40c0
        {ptr('$t0', VTABLE)}
        jal 0x1b2ab8
        sw $t0, 0($a0)
        lw $ra, 12($sp)
        jr $ra
        addiu $sp, $sp, 16
    ''')
    restore = routine('restore', f'''
        lw $t0, {TAIL_OFFSET}($a1)
        lui $t1, {MAGIC >> 16}
        ori $t1, $t1, {MAGIC & 65535}
        bne $t0, $t1, legacy
        lw $t0, {TAIL_OFFSET + 4}($a1)
        addiu $t1, $zero, {FORMAT}
        bne $t0, $t1, legacy
        lw $t0, {TAIL_OFFSET + 8}($a1)
        sltiu $t1, $t0, 2
        bnez $t1, store
        nop
    legacy:
        addiu $t0, $zero, 1
    store:
        {ptr('$t1', mode)}
        jr $ra
        sw $t0, 0($t1)
    ''')
    routine('settings_load', f'''
        addiu $sp, $sp, -16
        sw $ra, 12($sp)
        jal {restore}
        nop
        lw $ra, 12($sp)
        addiu $sp, $sp, 16
        addiu $sp, $sp, -48
        sw $ra, 12($sp)
        j {LOAD_SITE + 8}
        nop
    ''')
    routine('early_load', f'''
        addiu $sp, $sp, -16
        sw $ra, 12($sp)
        sw $a0, 8($sp)
        sw $a1, 4($sp)
        jal {restore}
        move $a1, $s1
        lw $a0, 8($sp)
        lw $a1, 4($sp)
        lw $ra, 12($sp)
        j 0x182a20
        addiu $sp, $sp, 16
    ''')
    routine('save_stamp', f'''
        lui $t0, {MAGIC >> 16}
        ori $t0, $t0, {MAGIC & 65535}
        sw $t0, {TAIL_OFFSET}($s1)
        addiu $t0, $zero, {FORMAT}
        sw $t0, {TAIL_OFFSET + 4}($s1)
        {ptr('$t0', mode)}
        lw $t0, 0($t0)
        sltiu $t1, $t0, 2
        bnez $t1, valid
        nop
        addiu $t0, $zero, 1
    valid:
        sw $t0, {TAIL_OFFSET + 8}($s1)
        lw $ra, 12($sp)
        lw $s1, 8($sp)
        j {SAVE_SITE + 8}
        nop
    ''')

    result, actual = it.extend_segment(boot, bytes(blob))
    assert actual == base
    header = it.elf(boot)['.rel.text']
    pos, length = struct.unpack_from('<2I', boot, header + 16)
    existing = dict(struct.iter_unpack('<2I', boot[pos:pos + length]))
    for name, site, link in [('hp', HP_SITE, False), ('reward', REWARD_SITE, False),
                             ('setup', SETUP_SITE, False), ('accept', ACCEPT_SITE, False),
                             ('cleanup', CLEANUP_SITE, True), ('early_load', EARLY_SITE, True),
                             ('save_stamp', SAVE_SITE, False), ('settings_load', LOAD_SITE, False)]:
        before = boot[site + 0x60:site + 0x60 + (4 if link else 8)]
        assert before == original[site + 0x60:site + 0x60 + len(before)], hex(site)
        target = int(routines[name]['va'], 16)
        instruction = ((3 if link else 2) << 26) | (target >> 2)
        struct.pack_into('<I', result, site + 0x60, instruction)
        if not link:
            struct.pack_into('<I', result, site + 0x64, 0)
        if site not in existing:
            relocs.append((site, 4))
        else:
            assert existing[site] & 255 == 4
        hooks.append(dict(name=name, va=hex(site), old=before.hex(),
                          new=bytes(result[site + 0x60:site + 0x60 + len(before)]).hex()))
    high, low = (strings['question'] + 0x8000) >> 16, strings['question'] & 65535
    for site, immediate in [(0x172EF0, high), (0x172EFC, low)]:
        word = struct.unpack_from('<I', result, site + 0x60)[0]
        struct.pack_into('<I', result, site + 0x60, word & 0xFFFF0000 | immediate)
        hooks.append(dict(name='question', va=hex(site), old=struct.pack('<I', word).hex(),
                          new=bytes(result[site + 0x60:site + 0x64]).hex()))
    result = bytes(it.append_relocs(result, relocs))
    report = dict(version=VERSION, mode_va=hex(mode), hp_table_va=hex(hp_va),
                  reward_table_va=hex(reward_va), vtable_va=hex(vtable),
                  routines=routines, strings={k: hex(v) for k, v in strings.items()},
                  hooks=hooks, added_relocations=relocs, balance_changes=changes,
                  default_choice='PSP - Harder', legacy_saves_default='PSP',
                  save_tail_offset=TAIL_OFFSET, save_magic=MAGIC, save_format=FORMAT,
                  source_executable_sha256=sha(boot), target_executable_sha256=sha(result))
    return result, report
