"""Record the five dialogue screenshots as a source-only proofreading follow-up."""
import copy
import hashlib
import html
import json
from pathlib import Path

import battle_quotes
import campaign_context_overrides
import campaign_status
import strip_jp
import textfit
from ps2_narration_port import native_width
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'work/translation/en/script'
DATE = '2026-10-12'
TAG = 'five_dialogue_screenshots_2026_10_12'
REVISIONS = [
    (19, 681, 'Saiga',
     'Heh... You hide revenge beneath your mask... And hatred colors your true face.',
     'Heh... A thirst for revenge behind that mask... And hatred written all over your face.',
     'The original is a dramatic observation of revenge behind the mask and hatred on the uncovered face. '
     'Natural English imagery preserves the taunt without the awkward hide revenge and colors your true face.'),
    (21, 269, 'Ritsu',
     'Is this the Zeorymer created by that man I hate with every fiber of my being...!?',
     'Is this the Zeorymer created by the man I hate with every fiber of my being...!?',
     'Accepted the user\'s suggestion: the definite article sounds more natural here. '
     'The demonstrative identifies the creator without naming him; the emphasis on enduring hatred remains.'),
]


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf8')


def widths(speaker, en, font):
    _, lines, ok = textfit.fit_dialogue(speaker, en)
    psp = [textfit.px(line) for line in lines]
    ps2 = [native_width(line.replace('\u300c', '').replace('\u300d', '').replace('\u3000', ' '), font)
           + 24 * (line.count('\u300c') + line.count('\u300d')) for line in lines]
    assert ok and max(psp) <= 352 and max(ps2) <= 528, (speaker, psp, ps2)
    return dict(psp_widths=psp, ps2_widths=ps2)


def render_report(report):
    cards = []
    for check in report['checks']:
        before = ('<p><b>Before:</b> ' + html.escape(check['before']) + '</p>') if 'before' in check else ''
        cards.append('<article><h2>{}. {}</h2><p class="status">{}</p>{}'
                     '<p><b>Reviewed text:</b> {}</p><p>{}</p></article>'.format(
                         check['screenshot'], html.escape(check['speaker']),
                         html.escape(check['status']), before, html.escape(check['after']),
                         html.escape(check['reason'])))
    page = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>SRW MX — Five dialogue screenshots</title><style>'
            'body{margin:0;background:#f3f6f7;color:#182a36;font:16px/1.6 system-ui}'
            'main{max-width:920px;margin:auto;padding:32px 20px}article{background:white;'
            'border:1px solid #dce5e8;border-radius:10px;margin:20px 0;padding:20px}'
            'h2{margin:0}.status{color:#006b68;font-weight:600}h1{line-height:1.2}'
            '</style><main><h1>Five dialogue screenshots, checked and explained</h1>'
            '<p>12 October 2026 · Checked against the original Japanese and scene context.</p>'
            '<p>Corrections are applied to shared PSP and PS2 translation inputs. Existing ISO images '
            'are unchanged. New wording passes both fonts’ width limits.</p>'
            + ''.join(cards) + '</main></html>')
    (ROOT / 'work/output/dialogue_review_2026_10_12.html').write_text(page, encoding='utf8')


def main():
    report_path = ROOT / 'work/translation/en/ui/dialogue_review_2026_10_12.en.json'
    assert not report_path.exists(), 'Follow-up already recorded; preserve its baseline.'
    overrides_path = SCRIPT / 'campaign_context_overrides.json'
    decisions = read(overrides_path)
    followup_path = SCRIPT / 'screenshot_proofread_followups.en.json'
    followups = read(followup_path)
    journal_path = ROOT / 'work/output/campaign_context_reviews.json'
    journal = read(journal_path)
    font = read(ROOT / 'work/build/ps2/font_0.4.30/patch.json')
    prepared, edits, validation = [], [], []
    for stage, entry, speaker, old, new, reason in REVISIONS:
        path = SCRIPT / f'stage{stage:02d}_campaign_full_merged.json'
        full = read(path)
        row = next(r for r in full['rows'] if r['id'] == entry)
        assert row['speaker_en'] == speaker and row['en'] == old
        before = copy.deepcopy(row)
        assert not any(o['stage'] == stage and o['full_id'] == entry for o in decisions['overrides'])
        decision = dict(stage=stage, full_id=entry, expected_owner=copy.deepcopy(row['translation_owner']),
                        expected_jp=row['jp'], expected_en=old, en=new, reason=reason)
        decisions['overrides'].append(decision)
        row.update(campaign_context_overrides.apply_override(stage, row, decisions['overrides']))
        owner = row['translation_owner']
        source = ROOT / owner['source']
        contributor = next(r for r in read(source.with_name(source.stem + '_sol61medium_merged.json'))['rows']
                           if r['id'] == owner['id'])
        original = next(r for r in read(SCRIPT / f'stage{stage:02d}_campaign_all_source.json')['rows']
                        if r['id'] == entry)
        rebuilt = copy.deepcopy(original)
        rebuilt.update({key: contributor.get(key, [] if key == 'uncertain' else '')
                        for key in ['speaker_en', 'en', 'notes', 'uncertain']})
        rebuilt = campaign_context_overrides.apply_override(stage, rebuilt, decisions['overrides'])
        assert all(rebuilt.get(k) == row.get(k) for k in
                   ['id', 'jp', 'en', 'speaker_en', 'kind', 'uses', 'translation_owner', 'uncertain'])
        assert all(before.get(k) == row.get(k) for k in set(before) | set(row) if k not in {'en', 'notes'})
        fit = widths(speaker, new, font)
        problems = campaign_status.check_full(full['rows'])
        assert not problems, (stage, problems)
        review = copy.deepcopy(journal['stages'][str(stage)])
        review['fingerprint'] = fingerprint(full['rows'])
        review['note'] += f' {DATE}: Entry {entry} screenshot follow-up; natural imagery/article. Source-only.'
        journal['stages'][str(stage)] = review
        full['context_review'] = review
        full['context_review_pending'] = False
        prepared.append((path, full))
        edits.append(dict(speaker=speaker, kind=row['kind'], before=old, after=new, reason=reason,
                          appearances=[[stage, entry]], review_tag=TAG,
                          source_sha256=hashlib.sha256(row['jp'].encode('utf8')).hexdigest(), **fit))
        validation.append(dict(chapter=stage, rows=len(full['rows']), problems=[],
                               guarded_reassembly_verified=True, **fit))

    battle_path = ROOT / 'work/translation/en/battle/batch_12.en.json'
    battle = read(battle_path)
    quote = next(r for r in battle['rows'] if r['id'] == 'q04997')
    assert quote['en'] == 'Hit, will you!'
    battle_reason = 'The pilot urges the shot to connect. Come on, hit! preserves the short imperative naturally.'
    quote['en'] = 'Come on, hit!'
    quote['notes'] = (quote.get('notes', '') + ' ' + battle_reason).strip()
    lines, ok = battle_quotes.fit(quote['en'])
    assert ok
    battle_fit = dict(psp_widths=[textfit.px(line) for line in lines],
                      ps2_widths=[native_width(line.replace('\u300c', '').replace('\u300d', '').replace('\u3000', ' '), font)
                                 + 24 * (line.count('\u300c') + line.count('\u300d')) for line in lines])
    assert max(battle_fit['ps2_widths']) <= 528
    burai = next(r for r in read(SCRIPT / 'stage20_campaign_full_merged.json')['rows'] if r['id'] == 74)
    burai_copy = next(r for r in read(SCRIPT / 'stage21_campaign_full_merged.json')['rows'] if r['id'] == 11)
    assert burai['en'] == burai_copy['en'] == (
        'Do not be hasty, Hidler. In this war, whoever reads the tide of events will win in the end. '
        'For now, we must build up our strength.')
    leina = next(r for r in read(SCRIPT / 'stage20_campaign_full_merged.json')['rows'] if r['id'] == 326)
    assert leina['en'] == "That's none of your business, you old hag! So there!!"
    checks = [
        dict(screenshot=1, status='corrected', **edits[0]),
        dict(screenshot=2, speaker='Burai', status='already corrected in proofreading sources',
             after=burai['en'], appearances=[[20, 74], [21, 11]],
             reason='The phrase means to judge the changing circumstances; reads the tide of events conveys strategic timing.'),
        dict(screenshot=3, speaker='Quattro Bajeena', status='corrected', before='Hit, will you!',
             after=quote['en'], battle_quote='q04997', source_uses=11,
             shared_with=['Mondo Agake', 'Leina Ashta'], reason=battle_reason, **battle_fit),
        dict(screenshot=4, speaker='Leina', status='retained', after=leina['en'], appearances=[[20, 326]],
             reason='The source contains the old-hag insult and a deliberately childish retort. So there! conveys that defiance.'),
        dict(screenshot=5, status='corrected', **edits[1]),
    ]
    followups['date'] = DATE
    followups['edits'].extend(edits)
    followups.setdefault('followup_validations', []).append(dict(date=DATE, review_tag=TAG,
        chapters=validation, guarded_reassembly_verified=True, all_non_editorial_metadata_preserved=True,
        iso_rebuilt=False, battle_quote='q04997'))
    report = dict(date=DATE, scope='Five user dialogue screenshots', checks=checks, chapters=validation,
                  iso_rebuilt=False, platforms=['PSP', 'PS2'],
                  note='Story and battle inputs are shared by both platform builders. Existing ISO images are unchanged.')
    # All source, reassembly and width checks precede the first write.
    for path, full in prepared:
        write(path, full)
        write(path.with_name(path.stem + '.en.json'), strip_jp.clean(full))
    write(overrides_path, decisions)
    write(overrides_path.with_name(overrides_path.stem + '.en.json'), strip_jp.clean(decisions))
    write(journal_path, journal)
    write(followup_path, followups)
    write(battle_path, battle)
    write(report_path, report)
    render_report(report)
    assert battle_quotes.check([str(battle_path)]) == 0
    print('Two story entries and one shared battle quote corrected; Burai already corrected; Leina retained.')
    print('Both changed chapters, guarded reassembly, both font limits and the entire battle batch pass.')


if __name__ == '__main__':
    main()
