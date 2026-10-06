"""Give the post-battle Level Up formatter six independent 256-byte rows.

The other Level Up path already uses 256-byte rows. This path originally
used 32-byte rows at 0x2C63DC, followed immediately by a number scratchpad.
Keep the formatter, skill flags, level values and renderer unchanged.
"""
import struct
import insert_text as it


def patch_boot(boot):
    data = bytearray(boot)
    word = lambda va: struct.unpack_from('<I', data, va + 0x60)[0]
    assert word(0xCE364) == 0x3C11002C
    assert word(0xCE378) == 0x263163DC
    assert word(0xCE604) == 0x26310020
    data, rows = it.extend_segment(data, bytes(6 * 256))
    hi, lo = it._hi_lo(rows)
    struct.pack_into('<I', data, 0xCE364 + 0x60, 0x3C110000 | hi)
    struct.pack_into('<I', data, 0xCE378 + 0x60, 0x26310000 | (lo & 0xFFFF))
    struct.pack_into('<I', data, 0xCE604 + 0x60, 0x26310100)
    # The existing paired HI16/LO16 relocations load the new array at runtime.
    return bytes(data)


def row_address(boot):
    hi = struct.unpack_from('<I', boot, 0xCE364 + 0x60)[0] & 0xFFFF
    lo = struct.unpack_from('<h', boot, 0xCE378 + 0x60)[0]
    assert struct.unpack_from('<I', boot, 0xCE604 + 0x60)[0] == 0x26310100
    return (hi << 16) + lo
