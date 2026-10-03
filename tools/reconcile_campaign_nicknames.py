"""Preview source-scoped Ryo/Harry nickname fixes; change final bodies only."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'work/translation/en/script'
REASON = ('Source nickname maps to Ryo per campaign_terms.json and '
          'https://srw.wiki.cre.jp/wiki/流竜馬; full 竜馬 remains Ryoma.')
HARRY_REASON = ('Source ハーリー maps to Harry per the sourced glossary nickname; '
                'prefilled Hari speaker and full Hari Makibi are retained.')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    changes, writes, scan = [], [], []
    for stage in range(1, 31):
        source = SCRIPT / ('stage%02d_campaign.json' % stage)
        ids = {r['id'] for r in read(source)['rows']
               if re.search('リョウ(?!コ|マ|ジ)', r['body_jp'])}
        harry_ids = {r['id'] for r in read(source)['rows'] if 'ハーリー' in r['body_jp']}
        scan.append(dict(stage=stage, source_nickname_ids=sorted(ids),
                         source_harry_ids=sorted(harry_ids)))
        for packet in sorted(SCRIPT.glob(source.stem+'_sol61medium_slice_*.json')):
            if packet.name.endswith('.en.json'):
                continue
            data = read(packet)
            edits = []
            for row in data['rows']:
                if row['id'] not in ids and row['id'] not in harry_ids:
                    continue
                before = row['en']
                after = before
                reasons = []
                if row['id'] in ids:
                    after = re.sub(r'(?<![A-Za-z])Ryoma(?![A-Za-z])', 'Ryo', after)
                    if after != before:
                        reasons.append(REASON)
                pre_harry = after
                if row['id'] in harry_ids:
                    after = re.sub(r'(?<![A-Za-z])Hari(?![A-Za-z]| Makibi)', 'Harry', after)
                    if after != pre_harry:
                        reasons.append(HARRY_REASON)
                if before == after:
                    continue
                reason = ' '.join(reasons)
                edits.append(dict(file=packet.name, id=row['id'], before=before, after=after, reason=reason))
                row['en'] = after
                row['notes'] = row.get('notes', '')+' '+reason
            if edits:
                changes.extend(edits)
                writes.append((packet, data, edits))
    decision_path = SCRIPT / 'campaign_reuse_decisions.json'
    decisions = read(decision_path)
    legacy_changes = []
    for row in read(SCRIPT / 'prologue_merged.json')['rows']:
        if not re.search('リョウ(?!コ|マ|ジ)', row['body_jp']):
            continue
        after = re.sub(r'(?<![A-Za-z])Ryoma(?![A-Za-z])', 'Ryo', row['en'])
        if after == row['en']:
            continue
        decision = dict(source='work/translation/en/script/prologue_merged.json',
                        id=row['id'], expected_en=row['en'], en=after, reason=REASON)
        existing = [d for d in decisions['overrides'] if d['source']==decision['source'] and d['id']==row['id']]
        if existing and existing != [decision]:
            raise ValueError('Conflicting legacy decision: %s' % row['id'])
        if not existing:
            decisions['overrides'].append(decision)
            legacy_changes.append(decision)
    print(json.dumps(dict(scan=scan, final_packet_changes=changes,
                         new_legacy_copy_overrides=legacy_changes), ensure_ascii=False, indent=1))
    if args.write:
        for packet, data, edits in writes:
            write(packet, data)
            report = packet.with_name(packet.name.replace('_slice_', '_report_')).with_suffix('.md')
            with report.open('a', encoding='utf-8') as out:
                out.write('\n## Coordinator source-scoped nickname reconciliation\n\n')
                out.write('Initial drafts are retained; changes below affect final bodies only.\n')
                for edit in edits:
                    out.write('\nRow {id}: `{before}` -> `{after}`\n{reason}\n'.format(**edit))
        write(decision_path, decisions)
        audit = ROOT / 'work/output/campaign_nickname_reconciliation.json'
        prior = read(audit) if audit.exists() else {'changes': [], 'legacy_copy_overrides': []}
        prior['changes'].extend(changes)
        prior['legacy_copy_overrides'].extend(legacy_changes)
        prior['source_scan'] = scan
        write(audit, prior)


if __name__ == '__main__':
    main()
