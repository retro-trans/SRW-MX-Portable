"""Audit finished campaign stages without changing translations or approvals."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'work/translation/en/script'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through', type=int, default=30, choices=range(1, 59))
    parser.add_argument('--first', type=int, default=1, choices=range(1, 59))
    parser.add_argument('--manifest', type=Path, default=ROOT/'work/output/stages01_30_sol_medium_manifest.json')
    parser.add_argument('--output', type=Path, default=ROOT/'work/output/campaign_completion_audit.json')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = read(args.manifest)
    if args.first > args.through:
        parser.error('First stage exceeds last stage.')
    expected_stages = set(range(args.first, args.through+1))
    if not expected_stages <= {s['stage'] for s in manifest['stages']}:
        parser.error('Requested stages are absent from manifest.')
    problems, stages = [], []
    if (manifest['model'], manifest['effort'], manifest['workers_per_stage']) != ('gpt-6.1-sol', 'medium', 6):
        problems.append('Campaign model/effort/worker settings differ')
    for name, expected in manifest['snapshots'].items():
        if hashlib.sha256((SCRIPT / name).read_bytes()).hexdigest() != expected:
            problems.append('Binding snapshot changed: ' + name)
    for n in range(args.first, args.through + 1):
        packets = [p for p in manifest['packets'] if p['stage'] == n]
        agents = {p.get('agent') for p in packets}
        if None in agents or len(agents) != 6:
            problems.append('Stage{} does not have six distinct actual agents'.format(n))
        if any(p['status'] != 'validated' for p in packets):
            problems.append('Stage{} contains an unvalidated packet'.format(n))
        for packet in packets:
            final = ROOT / packet['output']
            for path in [final, final.with_name(final.name.replace('_slice_', '_draft_')),
                         final.with_name(final.name.replace('_slice_', '_report_')).with_suffix('.md'),
                         final.with_suffix('.en.json')]:
                if not path.exists():
                    problems.append('Missing packet artifact: ' + str(path.relative_to(ROOT)))
        base = 'stage{:02d}_campaign'.format(n)
        full_path = SCRIPT / (base + '_full_merged.json')
        if not full_path.exists():
            problems.append('Stage{} has no full assembly'.format(n))
            continue
        full, original = read(full_path), read(SCRIPT / (base + '_all_source.json'))
        fields = ['id', 'jp', 'kind', 'translation_owner', 'uses']
        source_identity = lambda rows: [{key: row.get(key) for key in fields} for row in rows]
        if source_identity(full['rows']) != source_identity(original['rows']):
            problems.append('Stage{} original rows/kinds/owners/uses changed'.format(n))
        review = full.get('context_review', {})
        if full.get('context_review_pending', True) or review.get('fingerprint') != fingerprint(full['rows']):
            problems.append('Stage{} exact assembly lacks matching context review'.format(n))
        if full.get('full_checks', {}).get('problems') != []:
            problems.append('Stage{} has full-check findings'.format(n))
        safe = full_path.with_suffix('.en.json')
        if not safe.exists() or len(read(safe)['rows']) != len(full['rows']):
            problems.append('Stage{} safe full copy is missing/incomplete'.format(n))
        stages.append(dict(stage=n, fresh_rows=sum(p['stop'] - p['start'] for p in packets),
                           full_rows=len(full['rows']), uses=sum(len(r['uses']) for r in full['rows']),
                           packets=len(packets), actual_agents=sorted(a for a in agents if a),
                           fingerprint=review.get('fingerprint')))
    font_path = Path(os.environ.get('SRW_STATIC2', str(ROOT / 'work/build/STATIC2_ADD.BIN'))).resolve()
    result = dict(first=args.first, through=args.through, model=manifest['model'], effort=manifest['effort'],
                  font_source=str(font_path),
                  font_sha256=hashlib.sha256(font_path.read_bytes()).hexdigest(),
                  fresh_rows=sum(s['fresh_rows'] for s in stages),
                  full_rows=sum(s['full_rows'] for s in stages),
                  packets=sum(s['packets'] for s in stages), problems=problems, stages=stages)
    print(json.dumps({k: v for k, v in result.items() if k != 'stages'}, indent=1))
    if args.write:
        args.output.write_text(json.dumps(result, indent=1), encoding='utf-8')
    if problems:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
