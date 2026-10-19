"""Apply the two approved Ritsu screenshot revisions without rebuilding ISOs."""
import ast
import copy
import hashlib
import json
from pathlib import Path

import campaign_context_overrides
import campaign_status
import insert_text as it
import strip_jp
import textfit
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'work/translation/en/script'
TAG = 'ritsu_screenshots_2026_10_18'
REVISIONS = [
    (497, '...Masato Akitsu... You cannot see it. This face of mine...!',
     "...Masato Akitsu... You can't see this face of mine...!",
     'Approved screenshot revision: combines the fragmented face clause into natural English. '
     'Masato cannot see Ritsu\'s face; the following dialogue explains his resentment.'),
    (520, "I'm done talking. Die... and take the blood of Masaki within you with you...!",
     "Enough talk. Die... and take Masaki's blood with you...!",
     'Approved screenshot revision: removes the repeated within you with you. '
     'The threat still includes the blood of Masaki that Masato carries.'),
]


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf8')


def ps2_fit(target, font):
    # Execute the actual PS2 builder's nested width and reflow helpers so this
    # source-only check uses the same punctuation and indent measurements.
    tree = ast.parse((ROOT / 'tools/build_reviewed_ps2.py').read_text(encoding='utf8'))
    refresh = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'refresh_story')
    helpers = [n for n in refresh.body if isinstance(n, ast.FunctionDef) and n.name in {'width', 'fit'}]
    assert len(helpers) == 2
    context = dict(textfit=textfit, it=it, reflows=[], overflow=[],
                   glyphs={int(g['sjis'], 16): g['width'] for g in font['glyphs']})
    exec(compile(ast.Module(body=helpers, type_ignores=[]), 'build_reviewed_ps2.py', 'exec'), context)
    rendered = context['fit'](target, 's0550', 'approved-Ritsu-review')
    assert not context['overflow']
    return rendered.split('@'), [context['width'](line) for line in rendered.split('@')]


def main():
    report_path = ROOT / 'work/translation/en/ui/ritsu_review_2026_10_18.en.json'
    assert not report_path.exists(), 'Review already applied; preserve its baseline.'
    path = SCRIPT / 'stage28_campaign_full_merged.json'
    full = read(path)
    before_rows = copy.deepcopy(full['rows'])
    decisions_path = SCRIPT / 'campaign_context_overrides.json'
    decisions = read(decisions_path)
    followups_path = SCRIPT / 'screenshot_proofread_followups.en.json'
    followups = read(followups_path)
    font = read(ROOT / 'work/build/ps2/font_0.4.36/patch.json')
    edits = []
    for entry, old, new, reason in REVISIONS:
        row = next(r for r in full['rows'] if r['id'] == entry)
        assert row['speaker_en'] == 'Ritsu' and row['en'] == old
        assert not any(d['stage'] == 28 and d['full_id'] == entry for d in decisions['overrides'])
        decisions['overrides'].append(dict(stage=28, full_id=entry,
            expected_owner=copy.deepcopy(row['translation_owner']), expected_jp=row['jp'],
            expected_en=old, en=new, reason=reason))
        row.update(campaign_context_overrides.apply_override(28, row, decisions['overrides']))

        owner = row['translation_owner']
        source = ROOT / owner['source']
        contributor = next(r for r in read(source.with_name(source.stem + '_sol61medium_merged.json'))['rows']
                           if r['id'] == owner['id'])
        rebuilt = copy.deepcopy(next(r for r in read(SCRIPT / 'stage28_campaign_all_source.json')['rows']
                                    if r['id'] == entry))
        rebuilt.update({k: contributor.get(k, [] if k == 'uncertain' else '')
                        for k in ['speaker_en', 'en', 'notes', 'uncertain']})
        rebuilt = campaign_context_overrides.apply_override(28, rebuilt, decisions['overrides'])
        assert all(rebuilt.get(k) == row.get(k) for k in
                   ['id', 'jp', 'en', 'speaker_en', 'kind', 'uses', 'translation_owner', 'uncertain'])
        rendered, lines, ok = textfit.fit_dialogue('Ritsu', new)
        psp = [textfit.px(line) for line in lines]
        ps2_lines, ps2 = ps2_fit(rendered, font)
        assert ok and max(psp) <= 352 and max(ps2) <= 528, (entry, psp, ps2)
        edits.append(dict(speaker='Ritsu', kind=row['kind'], before=old, after=new, reason=reason,
                          appearances=[[28, entry]], review_tag=TAG,
                          source_sha256=hashlib.sha256(row['jp'].encode('utf8')).hexdigest(),
                          psp_widths=psp, ps2_widths=ps2))

    changed = []
    for before, after in zip(before_rows, full['rows']):
        if before != after:
            changed.append(after['id'])
            assert all(before.get(k) == after.get(k) for k in set(before) | set(after)
                       if k not in {'en', 'notes'})
    assert changed == [497, 520]
    assert not campaign_status.check_full(full['rows'])
    journal_path = ROOT / 'work/output/campaign_context_reviews.json'
    journal = read(journal_path) if journal_path.exists() else None
    review = copy.deepcopy(journal['stages']['28'] if journal else full['context_review'])
    assert review['fingerprint'] == fingerprint(before_rows), 'Review baseline has changed.'
    review['fingerprint'] = fingerprint(full['rows'])
    review['note'] += ' 2026-10-18: Approved natural-English revisions to Ritsu entries 497 and 520; source-only.'
    full['context_review'] = review
    full['context_review_pending'] = False
    if journal:
        journal['stages']['28'] = review
    followups['date'] = '2026-10-18'
    followups['edits'].extend(edits)
    validation = dict(date='2026-10-18', review_tag=TAG, chapter=28, rows=len(full['rows']),
                      problems=[], guarded_reassembly_verified=True,
                      all_non_editorial_metadata_preserved=True, iso_rebuilt=False)
    followups.setdefault('followup_validations', []).append(validation)
    report = dict(date='2026-10-18', edits=edits, validation=validation,
                  platforms=['PSP', 'PS2'], iso_rebuilt=False)
    safe = strip_jp.clean(full)
    safe_path = path.with_name(path.stem + '.en.json')
    strip_jp.reject_translation_loss(read(safe_path), safe, safe_path)
    # Complete all source guards, reassembly and font checks before writing.
    write(path, full)
    write(safe_path, safe)
    write(decisions_path, decisions)
    write(decisions_path.with_name(decisions_path.stem + '.en.json'), strip_jp.clean(decisions))
    write(followups_path, followups)
    write(report_path, report)
    if journal:
        write(journal_path, journal)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
