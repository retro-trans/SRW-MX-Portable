"""Combine completed campaign proofreading records through Chapter 30 or the end."""
import argparse
import copy
import hashlib
from collections import defaultdict

import proofread_chapters as p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through-end', action='store_true')
    args = parser.parse_args()
    last = 58 if args.through_end else 30
    slug = 'chapters01_end_proofread' if args.through_end else 'chapters01_30_proofread'
    script = p.ROOT / 'work/translation/en/script'
    names = [
        'chapters01_14_proofread.en.json', 'chapter15_super_proofread.en.json',
        'chapters15_30_proofread.en.json']
    if args.through_end:
        names.append('chapters31_58_proofread.en.json')
    sources = [p.read(script / name) for name in names]
    # Keep frozen proofreading decisions intact. Later screenshot corrections
    # may supersede their final wording, but only with a recorded exact baseline.
    followup_paths = sorted((p.ROOT/'work/translation/en/ui').glob('screenshot_review_*.en.json'))
    followups = defaultdict(list)
    for path in followup_paths:
        for change in p.read(path).get('changes', []):
            chapter = int(change['source_file'].split('/')[-1][5:7])
            followups[chapter, change['id']].append(change)
    screenshot_reviews = script/'screenshot_proofread_followups.en.json'
    screenshot_data = p.read(screenshot_reviews) if screenshot_reviews.exists() else {}
    for change in screenshot_data.get('edits', []):
        for location in change['appearances']:
            followups[tuple(location)].append(dict(old_en=change['before'], en=change['after'],
                reason=change['reason'], source_sha256=change['source_sha256']))
    current = {}
    matches = defaultdict(list)
    distinct = set()
    for chapter in range(1, last + 1):
        rows = p.read(script / ('stage%02d_campaign_full_merged.json' % chapter))['rows']
        for row in rows:
            current[chapter, row['id']] = row
            digest = hashlib.sha256(row['jp'].encode('utf-8')).hexdigest()
            matches[digest, row['speaker_en'], row['en']].append([chapter, row['id']])
            distinct.add((row['jp'], row['speaker_en'], row['en']))
    edits = []
    changed = set()
    for source in sources:
        for original in source['edits']:
            edit = copy.deepcopy(original)
            location = edit.get('appearances', [[15, edit.get('full_id')]])[0]
            row = current[tuple(location)]
            for change in followups[tuple(location)]:
                if edit['after'] == change['old_en']:
                    if 'source_sha256' in change:
                        assert edit['source_sha256'] == change['source_sha256'], location
                    edit.setdefault('proofread_after', edit['after'])
                    edit.setdefault('followup_history', []).append(dict(before=edit['after'],
                        after=change['en'], reason=change.get('reason', 'Screenshot terminology correction')))
                    edit['after'] = change['en']
                    edit['reason'] += ' Later screenshot review: ' + change.get('reason', 'terminology corrected.')
            assert row['en'] == edit['after'], location
            edit['speaker'] = row['speaker_en']
            edit['kind'] = row['kind']
            if source is not sources[-1] or not args.through_end:
                edit['appearances'] = [loc for loc in matches[edit['source_sha256'], edit['speaker'], edit['after']]
                                       if loc[0] <= 30]
            else:
                for loc in edit['appearances']:
                    assert current[tuple(loc)]['en'] == edit['after'], loc
            assert edit['appearances']
            changed.update(map(tuple, edit['appearances']))
            edits.append(edit)
    if screenshot_reviews.exists():
        for original in screenshot_data['edits']:
            edit=copy.deepcopy(original)
            edit['appearances']=[loc for loc in edit['appearances'] if loc[0]<=last]
            if not edit['appearances']:continue
            for loc in edit['appearances']:
                row=current[tuple(loc)]
                assert row['en']==edit['after'],loc
                assert hashlib.sha256(row['jp'].encode('utf8')).hexdigest()==edit['source_sha256'],loc
            # Already reported locations have their follow-up history merged
            # into the original review above; keep only additional appearances.
            edit['appearances']=[loc for loc in edit['appearances'] if tuple(loc) not in changed]
            if not edit['appearances']:continue
            changed.update(map(tuple,edit['appearances']));edits.append(edit)
        names.append(screenshot_reviews.name)
    assert len(changed) == sum(len(e['appearances']) for e in edits), 'Duplicate reported changes'
    coverage = {'chapters': []}
    ranges = ['chapters01_14', 'chapters15_30']
    if args.through_end:
        ranges.append('chapters31_58')
    for review_range in ranges:
        coverage['chapters'].extend(p.read(p.ROOT / ('work/source/proofread_' + review_range + '/coverage.json'))['chapters'])
    validations = []
    for chapter in coverage['chapters']:
        validations.append(dict(chapter=chapter['chapter'], rows=chapter['rows'],
            changed_occurrences=sum(c == chapter['chapter'] for c, _ in changed)))
    data = dict(date=screenshot_data.get('date', '2026-10-09'), scope='Chapters 1-{}, all routes; cumulative source review'.format('end' if args.through_end else 30),
        edits=edits, validation=validations, reviewed_assembled_rows=len(current),
        reviewed_unique_rows=len(distinct), changed_occurrences=len(changed), iso_rebuilt=False,
        reassembly_checks=sources[-1].get('reassembly_checks', {}),
        html_browser_checks=sources[-1].get('html_browser_checks', {}),
        prior_fix_packet_sync=sum((s.get('prior_fix_packet_sync', []) for s in sources), []),
        source_manifests=names,
        later_screenshot_corrections=[path.relative_to(p.ROOT).as_posix() for path in followup_paths])
    p.write(script / (slug + '.en.json'), data)
    p.make_report(data=data, coverage=coverage, corpus=[], first=1, last=last,
        output=p.ROOT / ('work/output/' + slug + '.html'))
    print('%d corrections, %d occurrences; %d distinct reviewed entries out of %d assembled entries.' %
        (len(edits), len(changed), len(distinct), len(current)))


if __name__ == '__main__':
    main()
