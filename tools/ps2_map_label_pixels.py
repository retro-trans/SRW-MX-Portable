"""Native 128x32 PSMT4 map captions uploaded as a 16x32 PSMCT32 image.

GS address bit permutations checked against PCSX2's documented GS tables:
https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSTables.cpp
This module expresses the address facts as bit arithmetic, not copied code.
Other P2IG sizes/upload layouts require separate validation.
"""


def pixel_order():
    physical_to_file = {}
    for y in range(32):
        for x in range(16):
            bx, by = x // 8, y // 8
            block = (bx & 1) | ((by & 1) << 1) | ((bx & 2) << 1) | ((by & 2) << 2)
            col = (x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((x & 4) << 1) | ((y & 2) << 3) | ((y & 4) << 3)
            address = block * 256 + col * 4
            for byte in range(4):
                physical_to_file[address + byte] = (y * 16 + x) * 4 + byte
    order = []
    for y in range(32):
        for x in range(128):
            bx, by = x // 32, y // 16
            block = (by & 1) | ((bx & 1) << 1) | ((by & 2) << 1) | ((bx & 2) << 2)
            col = ((y & 2) >> 1) | ((x & 8) >> 2) | ((x & 16) >> 2) | ((x & 1) << 3) | ((y & 1) << 4) | ((x & 2) << 4) | ((((x >> 2) ^ (y >> 1) ^ (y >> 2)) & 1) << 6) | ((y & 4) << 5) | ((y & 8) << 5)
            nibble = block * 512 + col
            order.append(physical_to_file[nibble // 2] * 2 + (nibble & 1))
    assert sorted(order) == list(range(4096))
    return order


ORDER = pixel_order()


def decode(raw):
    if len(raw) != 2048:
        raise ValueError('Expected native 128x32 map-caption payload')
    return [(raw[n // 2] >> ((n & 1) * 4)) & 15 for n in ORDER]


def encode(pixels):
    if len(pixels) != 4096 or any(type(v) is not int or not 0 <= v < 16 for v in pixels):
        raise ValueError('Expected 4096 palette indexes in 0..15')
    raw = bytearray(2048)
    for value, n in zip(pixels, ORDER):
        raw[n // 2] |= value << ((n & 1) * 4)
    return bytes(raw)
