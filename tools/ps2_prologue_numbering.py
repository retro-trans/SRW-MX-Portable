"""Exclude the added training Prologue from displayed story chapter numbers.

Hero +0x5f0 remains the native total cleared-battle count. Only the chapter
animation and objective-window display copies change; save/progression fields
are never decremented. This campaign requires a new game, as before.
"""
import struct
from port_ps2_translations import sha

SITES = (
    (0x348634, 0x24e70001, 'prologue_chapter_number'),
    (0x3489b4, 0x24e70001, 'prologue_chapter_number_alternate'),
    (0x224f08, 0x26310001, 'prologue_objective_number'),
    (0x2fe7cc, 0x26100001, 'prologue_script_objective_number'),
)


def patch(data, metadata):
    data = bytearray(data)
    hooks = []
    for address, original, name in SITES:
        offset = address - 0xff000
        assert struct.unpack_from('<I', data, offset)[0] == original, hex(address)
        corrected = original & 0xffff0000
        struct.pack_into('<I', data, offset, corrected)
        hooks.append(dict(name=name, va=hex(address),
                          old=struct.pack('<I', original).hex(),
                          new=struct.pack('<I', corrected).hex()))
    metadata['hooks'] += hooks
    metadata['target_sha256'] = sha(data)
    return bytes(data), dict(displayed_prologue_number=0,
                            first_story_chapter_number=1,
                            native_cleared_battle_count_preserved=True,
                            original_save_fields_preserved=True, hooks=hooks)
