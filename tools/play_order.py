"""Play order of a stage's lines, read from the script commands.

SRWL block = header (0x20) + N commands of 0x30 bytes (12 x i32: opcode, args) + string table.
  0x0B  show message        arg2 = string index
  0x0C  show two messages   arg1, arg6 = string indices (two speakers at once)
  0x58  show condition      arg2 = string index (victory / defeat conditions)
  0x6D  play scene          arg1 = string index of the scene label (i06s1b ...)
  0x7E / 0x7F               begin / end of an event handler in a map script
  0x7D  register a unit's defeat line (not shown in order; skipped)
A map script calls its "before" scene from its first event and its "after" scene from its last one,
so one pass over the map script gives the whole stage. Lines inside a map are in script order: which
event fires when depends on the battle (who attacks whom, turn count), so that part is the closest
available approximation of chronological order.

usage: python play_order.py <MAP_ADD.BIN> <map scene, e.g. s06s10> <rows.json> <out order.json>
"""
import json, os, struct, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def load(m, o):
    ncmd, n, tab = struct.unpack_from('<3I', m, o + 4)
    cmds = [struct.unpack_from('<12i', m, o + 0x20 + i * 0x30) for i in range(ncmd)]
    strs = [m[o + p:m.index(b'\0', o + p)].decode('cp932') for p in struct.unpack_from(f'<{n}I', m, o + tab)]
    return cmds, strs


def main(map_add, scene, rows_json, out):
    m = open(map_add, 'rb').read()
    sm = {r['name']: r for r in json.load(open(os.path.join(ROOT, 'work/source/stage_map.json'), encoding='utf-8'))}
    ids = {r['jp']: r['id'] for r in json.load(open(rows_json, encoding='utf-8'))['rows']}
    seq, event = [], 0

    def emit(part, s):
        if s in ids:
            seq.append({'part': part, 'id': ids[s]})

    def scene_lines(name, part):
        cmds, strs = load(m, sm[name]['offset'])
        for c in cmds:
            if c[0] == 0x0B:
                emit(part, strs[c[2]])
            elif c[0] == 0x0C:
                emit(part, strs[c[1]])
                emit(part, strs[c[6]])

    cmds, strs = load(m, sm[scene]['offset'])
    for c in cmds:
        op = c[0]
        if op == 0x7E:
            event += 1
        part = f'2. Battle map (event {event})'
        if op == 0x6D:
            label = strs[c[1]]
            scene_lines(label, '1. Before the battle' if label.endswith('b') else '3. After the battle')
        elif op == 0x0B or op == 0x58:
            emit(part, strs[c[2]])
        elif op == 0x0C:
            emit(part, strs[c[1]])
            emit(part, strs[c[6]])
    seen = set()
    for x in seq:
        x['repeat'] = x['id'] in seen
        seen.add(x['id'])
    json.dump(seq, open(out, 'w'), indent=0)
    missing = sorted(set(ids.values()) - seen)
    print(len(seq), 'lines in play order;', sum(x['repeat'] for x in seq), 'repeats; rows never shown:', missing)


if __name__ == '__main__':
    main(*sys.argv[1:5])
