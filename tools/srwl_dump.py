"""Dump all SRWL scenario-script message tables from MAP_ADD.BIN to JSON.

SRWL block (0x800-aligned inside MAP_ADD.BIN):
  +0x00 'SRWL'  +0x04 u32 ?  +0x08 u32 string_count  +0x0C u32 string_table_offset
  string table = string_count x u32 offsets, relative to the SRWL block start.
  Strings are NUL-terminated Shift-JIS.

usage: python srwl_dump.py MAP_ADD.BIN out.json
"""
import json, re, struct, sys

def dump(path):
    d = open(path, 'rb').read()
    blocks = []
    for m in re.finditer(b'SRWL', d):
        o = m.start()
        if o % 0x800:
            continue
        n, tab = struct.unpack_from('<2I', d, o + 8)
        strs = []
        for p in struct.unpack_from(f'<{n}I', d, o + tab):
            q = o + p
            strs.append(d[q:d.index(b'\0', q)].decode('cp932', 'replace'))
        blocks.append({'offset': o, 'count': n, 'table': tab, 'strings': strs})
    return blocks

if __name__ == '__main__':
    b = dump(sys.argv[1])
    json.dump(b, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(b), 'blocks,', sum(x['count'] for x in b), 'strings')
