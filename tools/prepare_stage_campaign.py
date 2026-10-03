"""Preview/export stages 1-30 and a six-worker translation queue. No ISO mutation."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re

import export_rows
import play_order

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'work/translation/en/script'
MANIFEST = ROOT / 'work/output/stages01_30_sol_medium_manifest.json'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding='utf-8')


def plan():
    blocks = export_rows.blocks(str(ROOT / 'work/build/iso/MAP_ADD.BIN'))
    speakers = export_rows.speakers()
    stages = []
    for line in (ROOT / 'docs/stage_map.md').read_text(encoding='utf-8').splitlines():
        cells = [x.strip() for x in line.split('|')[1:-1]]
        if len(cells) != 7 or not cells[0].isdigit() or not 1 <= int(cells[0]) <= 30:
            continue
        number = int(cells[0])
        scenes = [re.search(r'`([^`]+)`', c).group(1) for c in cells[4:] if '`' in c]
        route = dict(route=cells[1], title=cells[3], scenes=scenes,
                     map_scene=re.search(r'`([^`]+)`', cells[5]).group(1))
        if not stages or stages[-1]['stage'] != number:
            stages.append(dict(stage=number, routes=[]))
        stages[-1]['routes'].append(route)
    packets = []
    completed = json.loads((OUT/'prologue_merged.json').read_text(encoding='utf-8'))['rows']
    owners = {r['jp']: dict(source='work/translation/en/script/prologue_merged.json', id=r['id']) for r in completed}
    for stage in stages:
        rows, seen = [], {}
        scenes = [s for route in stage['routes'] for s in route['scenes']]
        for scene in scenes:
            for index, jp in enumerate(blocks[scene]):
                classified = export_rows.classify(jp)
                if not classified:
                    continue
                if re.match(r'^[０-９]+、', jp):
                    classified = dict(kind='plain', speaker_jp='', body_jp=jp)
                if jp in seen:
                    seen[jp]['uses'].append('{}:{}'.format(scene, index))
                    continue
                row = dict(id=len(rows), jp=jp, uses=['{}:{}'.format(scene, index)], **classified)
                row.update(speaker_en=speakers.get(row['speaker_jp']) if row['speaker_jp'] else '', en='')
                seen[jp] = row
                rows.append(row)
        base = 'stage{:02d}_campaign'.format(stage['stage'])
        fresh = []
        for row in rows:
            if row['jp'] not in owners:
                new = dict(row, id=len(fresh))
                fresh.append(new)
                owners[row['jp']] = dict(source='work/translation/en/script/'+base+'.json', id=new['id'])
            row['translation_owner'] = owners[row['jp']]
        stage.update(base=base, rows=len(fresh), all_rows=len(rows), reused_rows=len(rows)-len(fresh),
                     packets=max(6, (len(fresh)+79)//80),
                     missing_speakers=sorted({r['speaker_jp'] for r in fresh if r['speaker_jp'] and not r['speaker_en']}))
        stage['_source'] = dict(scenes=scenes, routes=stage['routes'], rows=fresh)
        stage['_all_source'] = dict(scenes=scenes, routes=stage['routes'], rows=rows)
        for index in range(stage['packets']):
            smaller = len(fresh) <= 400
            start = index * len(fresh) // 6 if smaller else index * 80
            stop = (index+1) * len(fresh) // 6 if smaller else min((index+1)*80, len(fresh))
            packet = dict(stage=stage['stage'], slice=index, worker=index % 6 + 1,
                          start=start, stop=stop, status='pending',
                          source='work/translation/en/script/'+base+'.json',
                          output='work/translation/en/script/'+base+'_sol61medium_slice_'+str(index)+'.json')
            packets.append(packet)
    return stages, packets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    stages, packets = plan()
    print(json.dumps([dict(stage=s['stage'], routes=len(s['routes']), rows=s['rows'], packets=s['packets'],
                           missing_speakers=s['missing_speakers']) for s in stages], ensure_ascii=False))
    print('{} stages, {} rows, {} assignments'.format(len(stages), sum(s['rows'] for s in stages), len(packets)))
    if not args.write:
        return
    targets = [OUT/(s['base']+suffix) for s in stages for suffix in ('.json','_all_source.json')] + [MANIFEST]
    if any(p.exists() for p in targets):
        raise RuntimeError('Refusing to overwrite campaign files')
    snapshots = {}
    for name, src in [('BASE_RULES_campaign.md', ROOT/'BASE_RULES.md'),
                      ('TRANSLATOR_BRIEF_campaign.md', OUT/'TRANSLATOR_BRIEF.md')]:
        dst = OUT/name
        if dst.exists():
            raise RuntimeError('Snapshot already exists: '+str(dst))
        dst.write_bytes(src.read_bytes())
        snapshots[name] = hashlib.sha256(dst.read_bytes()).hexdigest()
    for stage in stages:
        source = OUT/(stage['base']+'.json')
        write_json(source, stage.pop('_source'))
        all_source = OUT/(stage['base']+'_all_source.json')
        write_json(all_source, stage.pop('_all_source'))
        stage['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        orders = []
        for route in stage['routes']:
            order_path = OUT/(stage['base']+'_'+route['map_scene']+'_order.json')
            with contextlib.redirect_stdout(io.StringIO()):
                play_order.main(str(ROOT/'work/build/iso/MAP_ADD.BIN'), route['map_scene'], str(all_source), str(order_path))
            orders.append(str(order_path.relative_to(ROOT)).replace('\\','/'))
        stage['order_files'] = orders
    write_json(MANIFEST, dict(model='gpt-6.1-sol', effort='medium', workers_per_stage=6,
                             packet_size=80, snapshots=snapshots, stages=stages, packets=packets))
    print('Saved campaign sources, route orders, rule snapshots, and queue.')


if __name__ == '__main__':
    main()
