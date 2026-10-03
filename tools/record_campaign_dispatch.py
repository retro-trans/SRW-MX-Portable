"""Preview or record actual campaign workers. Assignment syntax: stage:slice:worker."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'work/output/stages01_30_sol_medium_manifest.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assignments', nargs='+')
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--manifest', type=Path, default=PATH)
    parser.add_argument('--agent', help='Actual reused agent task name; requires one assignment')
    args = parser.parse_args()
    if args.agent and (len(args.assignments) != 1 or not args.agent.startswith('/root/')):
        raise ValueError('Explicit actual agent requires one assignment and a root child task name')
    data = json.loads(args.manifest.read_text(encoding='utf-8'))
    preview = []
    for assignment in args.assignments:
        stage, packet, worker = map(int, assignment.split(':'))
        if not 1 <= worker <= 6:
            raise ValueError('Worker must be 1-6')
        target = next(p for p in data['packets'] if p['stage'] == stage and p['slice'] == packet)
        agent = args.agent or '/root/stage{:02d}_worker{}'.format(stage, worker)
        if target.get('agent') and target['agent'] != agent:
            raise ValueError('Existing actual agent differs: {}'.format(target))
        preview.append(dict(stage=stage, slice=packet, previous_agent=target.get('agent'),
                            agent=agent, previous_status=target['status'],
                            status='running' if target['status'] == 'pending' else target['status']))
        target['agent'] = agent
        target['actual_worker'] = worker
        if target['status'] == 'pending':
            target['status'] = 'running'
    print(json.dumps(preview, indent=1))
    if args.write:
        args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
