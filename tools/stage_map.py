"""Map every SRWL script block in MAP_ADD.BIN to its scene name and stage.

usage: python stage_map.py MAP_ADD.BIN BOOT.BIN STATIC2_ADD.BIN <MXPFlow_Chart.wiki> <out.json>

How the link works (see docs/stage_map.md):
  BOOT.BIN 0x27CA20  203 x u32  sector offset of each script, relative to MAP_ADD sector 0x579C
  BOOT.BIN 0x27D3A8  203 x u32  pointer (vaddr = file offset - 0x60) to the script's name
  Entry i of both tables describes the same script.
Names: s<PP><route><N>0 = stage map script, i<PP><route><N>b / a = scene before / after the map,
  PP = part 00-10, route = r/s (part 0: Real/Super) or e/s (parts 3, 6: Earth/Space) or none, N = stage in part.
STATIC2_ADD.BIN 0x1FF8A8: 69 x 0x80 scenario records (title @+0), summaries from 0x201C30 in the same order.
"""
import json, re, struct, sys

NAMES = 0x27D3A8
SECTORS = 0x27CA20
COUNT = 203
SCRIPT_BASE = 0x579C * 0x800

# stages per part, in order; (part, route) -> list of stage labels
PARTS = {
    ('00', 'r'): ['0', '1', '2'], ('00', 's'): ['0', '1', '2'],
    ('01', ''): ['3', '4', '5', '6', '7'],
    ('02', ''): ['8', '9', '10', '11', '12', '13', '14'],
    ('03', 'e'): ['15', '16', '17', '18'], ('03', 's'): ['15', '16', '17', '18'],
    ('04', ''): ['19', '20', '21', '22', '23'],
    ('05', ''): ['24', '25', '26', '27', '28', '29', 'SECRET'],
    ('06', 'e'): ['30', '31', '32', '33', '34'], ('06', 's'): ['30', '31', '32', '33', '34'],
    ('06', ''): ['UNUSED?'] * 5,          # i063b: unreferenced, old line format
    ('07', ''): ['35', '36', '37', '38', '39', 'UNUSED?'],
    ('08', ''): ['40', '41', '42', '43', '44'],
    ('09', ''): ['45', '46', '47', '48', '49'],
    ('10', ''): ['50', '51', '52', '53', '54', 'FINAL'],
}
ROUTE = {'r': 'Real', 's': 'Super', 'e': 'Earth'}
# game scenario-record index for (stage, route); route-split parts list Space first, then Earth
def game_index(stage, route, part):
    if stage == 'SECRET':
        return 66
    if stage == 'FINAL':
        return 65
    if stage == '0':
        return 67 if route == 'r' else 68
    n = int(stage)
    if part == '00':
        return {('1', 'r'): 0, ('2', 'r'): 1, ('1', 's'): 2, ('2', 's'): 3}[(stage, route)]
    if 3 <= n <= 14:
        return n + 1
    if 15 <= n <= 18:
        return n + 1 if route == 's' else n + 5
    if 19 <= n <= 29:
        return n + 5
    if 30 <= n <= 34:
        return n + 5 if route == 's' else n + 10
    return n + 10            # 35-54


def flowchart(path):
    """(stage label, route class) -> English title, from the akurasu MX Portable flow chart."""
    out = {}
    for line in open(path, encoding='utf-8'):
        for m in re.finditer(r"'''(?:第[^<]*?|プロローグ)<br>\s*Scenario (\w+) - (.*?)'''", line):
            cls = re.search(r'class="([^"]+)"', line)
            route = {'fc-route3': 'A', 'fc-route4': 'B'}.get(cls.group(1) if cls else '', '')
            out[(m.group(1), route)] = m.group(2).strip()
    return out


def main(map_add, boot, static2, flow, out):
    b = open(boot, 'rb').read()
    s2 = open(static2, 'rb').read()
    m = open(map_add, 'rb').read()
    titles, o = [], 0x1FF8A8
    while o < 0x201B00:
        titles.append(s2[o:o + 0x38].split(b'\0')[0].decode('cp932', 'replace'))
        o += 0x80
    sums, o = [], 0x201C30
    while len(sums) < len(titles):
        z = s2.index(b'\0', o)
        sums.append(s2[o:z].decode('cp932', 'replace').replace('＠', ''))
        o = z + 1
        while s2[o] == 0:
            o += 1
    fc = flowchart(flow)

    rows = []
    for i in range(COUNT):
        p = struct.unpack_from('<I', b, NAMES + i * 4)[0] + 0x60
        name = b[p:b.index(b'\0', p)].decode()
        off = SCRIPT_BASE + struct.unpack_from('<I', b, SECTORS + i * 4)[0] * 0x800
        assert m[off:off + 4] == b'SRWL', (i, name, hex(off))
        n = struct.unpack_from('<I', m, off + 8)[0]
        row = {'block': i, 'offset': off, 'name': name, 'strings': n}
        mm = re.match(r'^([si])(\d\d)([rse]?)(\d)([0ab])$', name)
        if mm:
            kind, part, route, k, sub = mm.groups()
            stages = PARTS.get((part, route))
            stage = stages[int(k) - (0 if part == '00' else 1)] if stages else None
            row.update({'kind': {'s': 'map', 'i': {'b': 'scene_before', 'a': 'scene_after'}.get(sub)}[kind],
                        'part': int(part), 'route': ROUTE.get(route, ''), 'stage': stage})
            if stage and not stage.startswith('UNUSED'):
                gi = game_index(stage, route, part)
                row['title_jp'], row['summary_jp'] = titles[gi], sums[gi]
                # flow chart: route-split stages use class route3 (Real/Earth) and route4 (Super/Space)
                fr = '' if not route else ('A' if route in 're' else 'B')
                if stage == '0':
                    fr = 'A' if route == 'r' else 'B'
                row['title_en'] = fc.get(('0' if stage == '0' else stage, fr)) or fc.get((stage, ''))
        else:
            row.update({'kind': {'end_mes': 'save_messages'}.get(name, 'dummy' if name.startswith('dummy') else 'other')})
        if name == 'i001b':
            row.update({'kind': 'scene_before', 'part': 0, 'stage': 'opening', 'route': ''})
        rows.append(row)
    json.dump(rows, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(rows), 'blocks;', sum(r.get('kind') == 'map' for r in rows), 'map scripts')


if __name__ == '__main__':
    main(*sys.argv[1:6])
