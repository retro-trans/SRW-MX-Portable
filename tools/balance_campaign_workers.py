"""Preview six smaller assignments for untouched stages with fewer than six packets."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'work/output/stages01_30_sol_medium_manifest.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = json.loads(PATH.read_text(encoding='utf-8'))
    updates = []
    for stage in data['stages']:
        old = [p for p in data['packets'] if p['stage'] == stage['stage']]
        if len(old) >= 6:
            continue
        if any(p['status'] != 'pending' or p.get('agent') or (ROOT/p['output']).exists() for p in old):
            raise ValueError('Cannot rebalance a started stage: {}'.format(stage['stage']))
        n = stage['rows']
        if n < 6:
            raise ValueError('Too few rows for six nonempty assignments')
        new = []
        for i in range(6):
            p = dict(stage=stage['stage'], slice=i, worker=i+1, start=i*n//6,
                     stop=(i+1)*n//6, status='pending', source=old[0]['source'],
                     output='work/translation/en/script/{}_sol61medium_slice_{}.json'.format(stage['base'], i))
            assert 0 < p['stop']-p['start'] <= 80
            new.append(p)
        assert new[0]['start'] == 0 and new[-1]['stop'] == n
        updates.append(dict(stage=stage['stage'], rows=n, old_packets=len(old),
                            intervals=[[p['start'],p['stop']] for p in new]))
        data['packets'] = [p for p in data['packets'] if p['stage'] != stage['stage']] + new
        stage['packets'] = 6
    data['packets'].sort(key=lambda p:(p['stage'],p['slice']))
    data['minimum_packets_per_stage'] = 6
    print(json.dumps(dict(updates=updates, total_packets=len(data['packets'])), indent=1))
    if args.write:
        PATH.write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf-8')


if __name__ == '__main__':
    main()
