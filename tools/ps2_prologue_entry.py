"""Correct the native New Game event's hard-coded first deployment.

The campaign starts with history slot zero. Keep that convention: ordinary
map selection increments history, but the first battle must not do so.
"""
import struct
import keystone
from ps2_translation_native import extend
from port_ps2_translations import sha

BIAS = 0xff000


def patch(data, metadata):
    data = bytearray(data)
    hooks = []
    def word(site, expected, value, name):
        old = bytes(data[site-BIAS:site-BIAS+4])
        assert old == struct.pack('<I', expected), hex(site)
        new = struct.pack('<I', value)
        data[site-BIAS:site-BIAS+4] = new
        hooks.append(dict(name=name, va=hex(site), old=old.hex(), new=new.hex()))
    # Event 0x2d6 is sent after the native protagonist/unit setup completes.
    # Its Real/Super branches set the battle chapter to 0/1, but both used
    # group zero. Group four contains the corresponding added Prologue.
    for site in (0x134d88, 0x134da8):
        word(site, 0x0000302d, 0x24060004, 'prologue_new_game_deployment')
    target = (int(metadata['segment_va'],16)+metadata['segment_bytes']+15)&~15
    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    code = bytes(ks.asm('''.set noreorder
        addiu $sp, $sp, -16
        sd $ra, 0($sp)
        jal 0x346f38
        nop
        addiu $v0, $zero, 4
        sw $v0, 0x3ac($a0)
        ld $ra, 0($sp)
        jr $ra
        addiu $sp, $sp, 16
    ''', target)[0])
    data, address = extend(data, metadata, code)
    assert address == target
    word(0x134dc0, 0x0c000000|(0x346f38>>2), 0x0c000000|(target>>2),
         'prologue_new_game_campaign_group')
    metadata['hooks'] += hooks
    metadata['target_sha256'] = sha(data)
    return data, dict(native_completion_event='0x2d6', first_group=4,
                      history_slot=0, routine_va=hex(target), routine_bytes=len(code), hooks=hooks)
