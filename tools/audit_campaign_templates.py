"""Verify original generic defeat-line registrations; never approves translation."""
import argparse
import json
from pathlib import Path

import play_order

ROOT = Path(__file__).resolve().parent.parent


def audit(stage):
    script = ROOT / 'work/translation/en/script'
    full = json.loads((script / f'stage{stage:02d}_campaign_all_source.json').read_text(encoding='utf-8'))['rows']
    legacy = {r['id']: r for r in json.loads((script / 'prologue_merged.json').read_text(encoding='utf-8'))['rows']}
    scenes = {r['name']: r for r in json.loads((ROOT / 'work/source/stage_map.json').read_text(encoding='utf-8'))}
    data = (ROOT / 'work/build/iso/MAP_ADD.BIN').read_bytes()
    loaded = {}
    result = dict(stage=stage, template_rows=0, registered_uses=0, ordinary_uses=[], problems=[], registrations=[])
    for row in full:
        owner = row['translation_owner']
        if not (owner['source'].endswith('prologue_merged.json') and 254 <= owner['id'] <= 396):
            continue
        result['template_rows'] += 1
        original = legacy[owner['id']]
        if (row['jp'], row['kind']) != (original['jp'], original['kind']):
            result['problems'].append(f"FULL {row['id']}: original template differs")
        for use in row['uses']:
            scene, index = use.rsplit(':', 1)
            index = int(index)
            if scene not in loaded:
                loaded[scene] = play_order.load(data, scenes[scene]['offset'])
            commands, strings = loaded[scene]
            if strings[index] != row['jp']:
                result['problems'].append(f'{use}: original string differs')
            registered = [i for i, c in enumerate(commands) if c[0] == 0x7D and c[2] == index]
            ordinary = [i for i, c in enumerate(commands) if
                        (c[0] in (0x0B, 0x58) and c[2] == index) or
                        (c[0] == 0x0C and index in (c[1], c[6]))]
            if registered:
                result['registered_uses'] += 1
                result['registrations'].append(dict(full_id=row['id'], use=use, commands=registered))
            if ordinary:
                result['ordinary_uses'].append(dict(full_id=row['id'], use=use, commands=ordinary))
            if not registered and not ordinary:
                result['problems'].append(f'{use}: no readable command or defeat registration')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=int)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = audit(args.stage)
    print(json.dumps({k: v for k, v in result.items() if k != 'registrations'}, indent=1))
    if args.write:
        path = ROOT / f'work/output/stage{args.stage:02d}_template_context_audit.json'
        path.write_text(json.dumps(result, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
