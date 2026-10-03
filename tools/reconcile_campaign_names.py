"""Preview fixed glossary spellings in completed final packets; preserve drafts."""
import argparse
import json
from pathlib import Path
import re
import check_translation

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'work/translation/en/script'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stages', nargs='+', type=int)
    parser.add_argument('--slices', nargs='+', type=int)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    fixes = json.loads((ROOT/'work/glossary/name_fixes.json').read_text(encoding='utf-8'))['names']
    changes, writes = [], []
    for stage in args.stages:
        source = SCRIPT/('stage%02d_campaign.json' % stage)
        src = {r['id']:r for r in json.loads(source.read_text(encoding='utf-8'))['rows']}
        for packet in sorted(SCRIPT.glob(source.stem+'_sol61medium_slice_*.json')):
            if packet.name.endswith('.en.json'):
                continue
            data = json.loads(packet.read_text(encoding='utf-8'))
            if args.slices is not None and data['slice'] not in args.slices:
                continue
            edits = []
            for row in data['rows']:
                mapping = check_translation.contextual_name_fixes(src[row['id']], fixes)
                for field in ['speaker_en', 'en']:
                    if field == 'speaker_en' and src[row['id']].get('speaker_en'):
                        continue
                    before = row[field]
                    after = before
                    # Protect canonical forms before replacing overlapping old forms.
                    protected = {}
                    # A short canonical name inside an old longer form must
                    # remain available to the old-form replacement (Mr. Rikudo).
                    for index, canonical in enumerate(sorted(set(mapping.values()), key=len, reverse=True)):
                        token = '\x00%d\x00' % index
                        containing_old = [old for old in mapping if canonical in old and canonical != old]
                        old_spans = [m.span() for old in containing_old for m in re.finditer(
                            r'(?<![A-Za-z])'+re.escape(old)+r'(?![A-Za-z])', after)]
                        def protect(match):
                            if any(a <= match.start() and match.end() <= b
                                   and (a, b) != match.span() for a, b in old_spans):
                                return match.group()
                            return token
                        after = re.sub(r'(?<![A-Za-z])'+re.escape(canonical)+r'(?![A-Za-z])', protect, after)
                        if token in after:
                            protected[token] = canonical
                    for old, new in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
                        after = re.sub(r'(?<![A-Za-z])'+re.escape(old)+r'(?![A-Za-z])', new, after)
                    for token, canonical in protected.items():
                        after = after.replace(token, canonical)
                    if after != before:
                        edits.append(dict(file=packet.name, id=row['id'], field=field, before=before, after=after))
                        row[field] = after
                        row['notes'] += ' Fixed glossary spelling reconciled after meaning review; initial draft retained.'
            if edits:
                changes.extend(edits)
                writes.append((packet, data, edits))
    print(json.dumps(changes, ensure_ascii=False, indent=1))
    if args.write:
        for packet, data, edits in writes:
            packet.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
            report = packet.with_name(packet.name.replace('_slice_', '_report_')).with_suffix('.md')
            with report.open('a', encoding='utf-8') as out:
                out.write('\n## Coordinator fixed-spelling reconciliation\n\nInitial draft retained.\n')
                for edit in edits:
                    out.write('\nRow {id}, {field}: `{before}` -> `{after}`\n'.format(**edit))
        audit = ROOT/'work/output/campaign_fixed_spelling_reconciliation.json'
        prior = json.loads(audit.read_text(encoding='utf-8')) if audit.exists() else []
        prior.extend(changes)
        audit.write_text(json.dumps(prior, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
