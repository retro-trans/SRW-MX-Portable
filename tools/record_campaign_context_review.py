"""Record completed human/coordinator context review; preview before --write."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'work/output/campaign_context_reviews.json'


def fingerprint(rows):
    fields = ['id', 'kind', 'jp', 'speaker_en', 'en', 'uses']
    body = [{k: row.get(k) for k in fields} for row in rows]
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stages', nargs='+', type=int)
    parser.add_argument('--note', required=True)
    parser.add_argument('--append-note', action='store_true')
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--reviews', type=Path, default=PATH)
    args = parser.parse_args()
    data = json.loads(args.reviews.read_text(encoding='utf-8')) if args.reviews.exists() else {'stages': {}}
    updates = {}
    for n in args.stages:
        source = 'work/translation/en/script/stage{:02d}_campaign.json'.format(n)
        path = ROOT / source.replace('.json', '_full_merged.json')
        full = json.loads(path.read_text(encoding='utf-8'))
        reused = [r for r in full['rows'] if r['translation_owner']['source'] != source]
        prior_note = data['stages'].get(str(n), {}).get('note', '') if args.append_note else ''
        note = prior_note+' '+args.note if prior_note else args.note
        updates[str(n)] = dict(stage=n, fingerprint=fingerprint(full['rows']),
                               reviewed_reused_ids=[r['id'] for r in reused],
                               reviewed_reused_rows=len(reused),
                               source_uncertainties_retained=True, reviewer='coordinator', note=note)
    preview = {k: {field: value for field, value in v.items() if field != 'reviewed_reused_ids'}
               for k, v in updates.items()}
    print(json.dumps(preview, ensure_ascii=False, indent=1))
    if args.write:
        data['stages'].update(updates)
        args.reviews.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
