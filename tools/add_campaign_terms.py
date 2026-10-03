"""Preview or merge a sourced local JSON batch into the campaign supplement."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'work/glossary/campaign_terms.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    batch = json.loads(args.batch.read_text(encoding='utf-8'))
    changes = []
    for group, rows in batch.items():
        if group not in ['terms', 'characters', 'speaker_aliases']:
            raise ValueError('Unsupported group: '+group)
        key = 'jp_short' if group == 'characters' else 'jp'
        for row in rows:
            if not row.get('sources') or not row.get('notes'):
                raise ValueError('Source and scope notes required')
            previous = next((r for r in data[group] if r.get(key) == row[key]), None)
            if previous == row:
                continue
            changes.append(dict(group=group, previous=previous, proposed=row))
            if previous is None:
                data[group].append(row)
            else:
                data[group][data[group].index(previous)] = row
    print(json.dumps(changes, ensure_ascii=False, indent=1))
    if args.write:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
