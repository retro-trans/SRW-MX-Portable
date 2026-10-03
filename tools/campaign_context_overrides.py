"""Apply explicitly reviewed English alternatives to exact stage-context copies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / 'work/translation/en/script/campaign_context_overrides.json'


def load_overrides():
    return json.loads(PATH.read_text(encoding='utf-8'))['overrides'] if PATH.exists() else []


def apply_override(stage, row, decisions):
    matches = [d for d in decisions if d['stage'] == stage and d['full_id'] == row['id']]
    if len(matches) > 1:
        raise ValueError('Duplicate context override: {}:{}'.format(stage, row['id']))
    if not matches:
        return row
    decision = matches[0]
    owner = row['translation_owner']
    if owner != decision['expected_owner'] or row['jp'] != decision['expected_jp']:
        raise ValueError('Context override source differs: {}:{}'.format(stage, row['id']))
    # A pending advisory projection may not yet have its owner's English.
    if not row.get('en'):
        return row
    if row['en'] != decision['expected_en']:
        raise ValueError('Context override English differs: {}:{}'.format(stage, row['id']))
    result = dict(row)
    result['en'] = decision['en']
    result['notes'] = result.get('notes', '') + ' ' + decision['reason']
    return result
