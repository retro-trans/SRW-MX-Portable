"""Read-only original-context review aid. Never records approval automatically."""
import argparse
import json
from pathlib import Path
import campaign_context_overrides

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=int)
    parser.add_argument('--reused', action='store_true')
    parser.add_argument('--uncertain', action='store_true')
    parser.add_argument('--ids', nargs='*', type=int)
    parser.add_argument('--neighbors', type=int, default=0)
    parser.add_argument('--pending', action='store_true', help='Review original reused context before full assembly exists')
    parser.add_argument('--skip-battle-template', action='store_true', help='Skip previously reviewed generic prologue defeat rows254-396')
    args = parser.parse_args()
    base = 'work/translation/en/script/stage{:02d}_campaign'.format(args.stage)
    suffix = '_all_source.json' if args.pending else '_full_merged.json'
    full = json.loads((ROOT / (base+suffix)).read_text(encoding='utf-8'))
    rows = full['rows']
    if args.pending:
        owners = {}
        for row in rows:
            owner = row['translation_owner']
            path = owner['source']
            if path not in owners:
                candidate = ROOT / path
                if not path.endswith(('prologue_merged.json', '_full_merged.json')):
                    candidate = candidate.with_name(candidate.stem+'_sol61medium_merged.json')
                owners[path] = {r['id']:r for r in json.loads(candidate.read_text(encoding='utf-8'))['rows']} if candidate.exists() else {}
                if not path.endswith(('prologue_merged.json', '_full_merged.json')):
                    # Pending stages have no merged file yet. Read finished local
                    # packets for advisory context only; status validation is separate.
                    packet_pattern = Path(path).stem+'_sol61medium_slice_*.json'
                    for packet in candidate.parent.glob(packet_pattern):
                        if packet.name.endswith('.en.json'):
                            continue
                        try:
                            packet_rows = json.loads(packet.read_text(encoding='utf-8'))['rows']
                        except (json.JSONDecodeError, KeyError):
                            continue
                        owners[path].update({r['id']:r for r in packet_rows})
            translated = owners[path].get(owner['id'], {})
            row.update({key:translated.get(key, [] if key=='uncertain' else '') for key in ['en','uncertain']})
            if not row.get('speaker_en') and translated.get('speaker_en'):
                row['speaker_en'] = translated['speaker_en']
        decisions = campaign_context_overrides.load_overrides()
        rows = [campaign_context_overrides.apply_override(args.stage, row, decisions) for row in rows]
    selected = [r for r in rows if
                (not args.reused or r['translation_owner']['source'] != base+'.json') and
                (not args.uncertain or r.get('uncertain')) and
                (args.ids is None or r['id'] in args.ids) and
                (not args.skip_battle_template or not (r['translation_owner']['source'].endswith('prologue_merged.json') and 254<=r['translation_owner']['id']<=396))]
    print('Stage {}: total {}, reused {}, uncertain {}, selected {}'.format(
        args.stage, len(rows), sum(r['translation_owner']['source'] != base+'.json' for r in rows),
        sum(bool(r.get('uncertain')) for r in rows), len(selected)))
    by_use = {u: r for r in rows for u in r['uses']}
    for row in selected:
        print('\nFULL {} OWNER {}:{} USES {}'.format(row['id'],row['translation_owner']['source'],
              row['translation_owner']['id'], ','.join(row['uses'])))
        print(row['jp'])
        print('{}: {}'.format(row['speaker_en'], row['en']))
        if row.get('uncertain'):
            print('UNCERTAIN: '+str(row['uncertain']))
        if args.neighbors:
            for use in row['uses']:
                scene, index = use.rsplit(':',1)
                for i in range(max(0,int(index)-args.neighbors), int(index)+args.neighbors+1):
                    other = by_use.get('{}:{}'.format(scene,i))
                    if other and other['id'] != row['id']:
                        print('  {}:{} [{}] {} => {}'.format(scene,i,other['id'],other['jp'],other['en']))


if __name__ == '__main__':
    main()
