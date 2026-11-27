"""Repair both fixed-size copies in the player forecast's action row."""
import struct

from fix_ps2_forecast_strings import patch as patch_forecast
from ps2_font4x import FILE_BIAS


# Start and end of the native copy. Both paths rejoin the action row at
# 0x17abb8, including its optional mask and subsequent measurement.
SITES = (
    ('Attack', 0x17ab54),
    ('No Counter', 0x17ab84),
)


def patch(public, metadata, original):
    data, metadata, fix = patch_forecast(public, metadata)
    data = bytearray(data)
    entry = int(fix['helper_va'], 16)
    records = []
    for label, start in SITES:
        off = start - FILE_BIAS
        assert public[off:off + 20] == original[off:off + 20]
        branch = struct.unpack_from('<I', original, off + 12)[0]
        assert branch == 0x10000000 | ((0x17abb8 - (start + 16)) // 4)
        words = [0x0c000000 | (entry >> 2), 0, 0, branch, 0]
        for index, word in enumerate(words):
            location = off + index * 4
            before = bytes(data[location:location + 4])
            after = struct.pack('<I', word)
            data[location:location + 4] = after
            fix['changes'].append(dict(va=hex(location + FILE_BIAS), offset=location,
                                       before=before.hex(), after=after.hex()))
        records.append(dict(label=label, start=hex(start), resume='0x17abb8'))
    fix['player_battle_copies'] = records
    return bytes(data), metadata, fix
