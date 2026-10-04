"""Translate the map terrain names (MAP_ADD.BIN MPTI section; work/translation/en/ui/map_tiles.json).

MPTI at MAP_ADD 0x2AA8000: 'MPTI', u32 count, then 52-byte records whose first 32 bytes are a
NUL-padded SJIS text 'name@note'. The map cursor info box shows the name (the part before '@').
English is written full-width (2 bytes a letter). The '@note' is kept when it still fits the field.
The section sits before the script area, so its offset does not change when scripts grow.
"""
import json
import os
import struct

import textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MPTI = 0x2AA8000
RECORD = 52
FIELD = 32


def patch(map_add):
    data = bytearray(map_add)
    assert data[MPTI:MPTI + 4] == b'MPTI', 'MPTI section not at its original offset'
    count = struct.unpack_from('<I', data, MPTI + 4)[0]
    names = json.load(open(os.path.join(ROOT, 'work/translation/en/ui/map_tiles.json'), encoding='utf-8'))['names']
    done = notes_dropped = 0
    missing = set()
    for k in range(count):
        o = MPTI + 8 + RECORD * k
        raw = bytes(data[o:o + FIELD]).split(b'\0')[0]
        if not raw:
            continue
        text = raw.decode('cp932')
        name, at, note = text.partition('@')
        en = names.get(name)
        if en is None:
            missing.add(name)
            continue
        b = textfit.encode(en)
        assert len(b) < FIELD, f'{en}: {len(b)} bytes'
        if at and len(b) + 1 + len(note.encode('cp932')) < FIELD:
            b += b'@' + note.encode('cp932')
        elif at:
            notes_dropped += 1
        data[o:o + FIELD] = b + bytes(FIELD - len(b))
        done += 1
    assert not missing, f'terrain names without English: {sorted(missing)}'
    print(f'MAP_ADD terrain names: {done} records translated ({notes_dropped} developer notes dropped to fit)')
    return bytes(data)
