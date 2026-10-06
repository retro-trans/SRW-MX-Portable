"""Center PSP setup, Options, Sound and Demo rows using the native VWF width.

Only the five affected draw call sites are redirected. Font styles, selection,
vertical coordinates, truncation limits and all other text keep their native paths.
"""
import struct
import insert_text as it

DRAW = 0xAEB08
WIDTH = 0xB03E4
SITES = {
    'unit_choices': (0x1C84C0, 'setup'),
    'pilot_choices': (0x1C8D24, 'pilot'),
    'options': (0x1CA3CC, 'screen'),
    'demo': (0x1D0488, 'panel'),
    'music': (0x1D151C, 'screen'),
}


def wrapper(mode):
    i, r = it._i, it._r
    # O32 caller argument area remains available below the saved values.
    words = []
    if mode == 'pilot':
        # The first three rows are Name/Nick/sex labels, not menu choices.
        words += [i(10, 17, 1, 3), i(4, 1, 0, 3), 0,
                  (2 << 26) | (DRAW >> 2), 0]
    words += [i(9, 29, 29, -48), i(43, 29, 31, 44)]
    for reg, off in [(4, 16), (5, 20), (7, 24), (8, 28)]:
        words += [i(43, 29, reg, off)]
    if mode in ('setup', 'pilot'):
        # Native choice highlight starts at object.x + 260 and is 160 px wide.
        words += [i(35, 4, 9, 0xA0 - 0x1FC), i(9, 9, 9, 340)]
    elif mode == 'panel':
        words += [i(35, 4, 9, 0xA8 - 0x2A4), r(0, 9, 9, 1, 2),
                  i(35, 4, 10, 0xA0 - 0x2A4), r(9, 10, 9, 0, 33)]
    else:
        words += [i(9, 0, 9, 240)]
    words += [i(43, 29, 9, 32), (3 << 26) | (WIDTH >> 2), 0,
              i(35, 29, 9, 32), r(0, 2, 2, 1, 2), r(9, 2, 6, 0, 35)]
    for reg, off in [(4, 16), (5, 20), (7, 24), (8, 28), (31, 44)]:
        words += [i(35, 29, reg, off)]
    words += [(2 << 26) | (DRAW >> 2), i(9, 29, 29, 48)]
    return it._words(*words)


def patch_boot(boot):
    data = bytearray(boot)
    payload, offsets = bytearray(), {}
    for name, (_, mode) in SITES.items():
        offsets[name] = len(payload)
        payload += wrapper(mode)
    data, base = it.extend_segment(data, payload)
    relocs = []
    for name, (site, _) in SITES.items():
        old = struct.unpack_from('<I', data, site + 0x60)[0]
        assert old == (3 << 26) | (DRAW >> 2), f'{name}: unexpected draw call'
        struct.pack_into('<I', data, site + 0x60, (3 << 26) | ((base + offsets[name]) >> 2))
        # Each replaced jal already has an R_MIPS_26 relocation.
    for off in range(0, len(payload), 4):
        word = struct.unpack_from('<I', payload, off)[0]
        if word >> 26 in (2, 3):
            relocs.append((base + off, 4))
    return bytes(it.append_relocs(data, relocs))
