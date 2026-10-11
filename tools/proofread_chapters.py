"""Read local review batches, save English decisions, and apply scoped corrections."""
import argparse
import copy
import hashlib
import html
import json
import re
import difflib
from pathlib import Path

import campaign_status
import check_translation
import strip_jp
import textfit
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work/source/proofread_chapters01_14'
DECISIONS = ROOT / 'work/translation/en/script/chapters01_14_proofread.en.json'
FIRST, LAST = 1, 14
SLUG = 'chapters01_14_proofread'


def configure(first, last):
    global WORK, DECISIONS, FIRST, LAST, SLUG
    FIRST, LAST = first, last
    SLUG = 'chapters{:02d}_{:02d}_proofread'.format(first, last)
    WORK = ROOT / ('work/source/proofread_chapters{:02d}_{:02d}'.format(first, last))
    DECISIONS = ROOT / 'work/translation/en/script' / (SLUG + '.en.json')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


def add_decisions(edits, start, stop):
    rows = read(WORK / 'review_rows.json')
    data = read(DECISIONS) if DECISIONS.exists() else {
        'date': '2026-10-09', 'scope': 'Chapters {}-{}, all routes; source proofreading only'.format(FIRST, LAST),
        'edits': [], 'reviewed_ranges': []}
    for rid, after, reason in edits:
        row = rows[rid]
        assert not any(e['review_id'] == rid for e in data['edits'])
        if row['kind'] != 'plain':
            _, lines, fits = textfit.fit_dialogue(row['speaker_en'], after, row['kind'] == 'thought')
            assert fits, (rid, lines)
        data['edits'].append(dict(review_id=rid, speaker=row['speaker_en'], before=row['en'],
                                 after=after, reason=reason, appearances=row['appearances'],
                                 source_sha256=hashlib.sha256(row['jp'].encode('utf-8')).hexdigest()))
    data['reviewed_ranges'].append([start, stop])
    write(DECISIONS, data)
    print('Recorded {} edits; reviewed {}:{}'.format(len(edits), start, stop))


def show(start, stop):
    for row in read(WORK / 'review_rows.json')[start:stop]:
        print('{}|{}|{}|{}|{}'.format(row['review_id'], row['chapter'], row['speaker_en'],
                                     row['jp'].replace('@', ' '), row['en']))


def expected_owner_english(row):
    """Mirror legacy spelling/reuse reconciliation before a context override."""
    owner = row['translation_owner']
    if not owner['source'].endswith('/prologue_merged.json'):
        return row['en']
    legacy = next(r for r in read(ROOT / owner['source'])['rows'] if r['id'] == owner['id'])
    legacy = dict(legacy)
    for decision in read(ROOT / 'work/translation/en/script/campaign_reuse_decisions.json')['overrides']:
        if decision['source'] == owner['source'] and decision['id'] == owner['id']:
            assert legacy['en'] == decision['expected_en']
            legacy['en'] = decision['en']
    fixes = check_translation.contextual_name_fixes(
        legacy, read(ROOT / 'work/glossary/name_fixes.json')['names'])
    result = legacy['en']
    for old, new in sorted(fixes.items(), key=lambda x: len(x[0]), reverse=True):
        result = re.sub(r'(?<![A-Za-z])' + re.escape(old) + r'(?![A-Za-z])', new, result)
    return result


def apply_review():
    """Validate everything before writing; keep corrections local to reviewed stages."""
    data = read(DECISIONS)
    corpus = read(WORK / 'review_rows.json')
    covered = set()
    for start, stop in data['reviewed_ranges']:
        covered.update(range(start, stop))
    assert covered == set(range(len(corpus))), 'Incomplete review coverage'
    assert len({e['review_id'] for e in data['edits']}) == len(data['edits'])
    script = ROOT / 'work/translation/en/script'
    override_path = script / 'campaign_context_overrides.json'
    review_path = ROOT / 'work/output/campaign_context_reviews.json'
    manifest_path = WORK / 'reassembly_manifest.json'
    if manifest_path.exists():
        review_path = ROOT / read(manifest_path).get('context_reviews', 'work/output/campaign_context_reviews.json')
    overrides = read(override_path)
    reviews = read(review_path)
    for path in [override_path, review_path]:
        backup = WORK / ('before_' + path.name)
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    edited = {}
    for edit in data['edits']:
        row = corpus[edit['review_id']]
        assert edit['before'] == row['en']
        assert edit['source_sha256'] == hashlib.sha256(row['jp'].encode('utf-8')).hexdigest()
        assert edit['appearances'] == row['appearances']
        for stage, full_id in edit['appearances']:
            assert (stage, full_id) not in edited
            edited[stage, full_id] = edit
    prepared = []
    validation = []
    for stage in range(FIRST, LAST + 1):
        path = script / 'stage{:02d}_campaign_full_merged.json'.format(stage)
        full = read(path)
        baseline = read(WORK / path.name)
        assert len(full['rows']) == len(baseline['rows'])
        changes = 0
        for row, old in zip(full['rows'], baseline['rows']):
            # Notes are the only metadata intentionally extended by this review.
            for key in set(row) | set(old):
                if key not in {'en', 'notes'}:
                    assert row.get(key) == old.get(key), (stage, row['id'], key)
            edit = edited.get((stage, row['id']))
            if not edit:
                assert row['en'] == old['en']
                continue
            assert row['en'] in {edit['before'], edit['after']}, (stage, row['id'])
            assert old['en'] == edit['before']
            reason = 'Chapters {}-{} proofreading: '.format(FIRST, LAST) + edit['reason']
            matches = [o for o in overrides['overrides']
                       if o['stage'] == stage and o['full_id'] == row['id']]
            assert len(matches) <= 1
            if matches:
                override = matches[0]
                assert override['expected_owner'] == row['translation_owner']
                assert override['expected_jp'] == row['jp']
                assert override['en'] in {edit['before'], edit['after']}
                override['en'] = edit['after']
                if reason not in override['reason']:
                    override['reason'] += ' ' + reason
            else:
                overrides['overrides'].append(dict(stage=stage, full_id=row['id'],
                    expected_owner=copy.deepcopy(row['translation_owner']), expected_jp=row['jp'],
                    expected_en=expected_owner_english(old), en=edit['after'], reason=reason))
            row['en'] = edit['after']
            if reason not in row.get('notes', ''):
                row['notes'] = row.get('notes', '') + ' ' + reason
            changes += 1
        findings = campaign_status.check_full(full['rows'])
        assert not findings, (stage, findings)
        prior = reviews['stages'].get(str(stage), {})
        reused = [r for r in full['rows'] if r['translation_owner']['source'] !=
                  'work/translation/en/script/stage{:02d}_campaign.json'.format(stage)]
        note = ('2026-10-09: All Chapter {} rows proofread against the original source in scene '
                'context, including all applicable routes and reused rows. {} row occurrences '
                'corrected; every correction explained in {}.en.json '
                'and {}.html. Source uncertainty annotations retained. '
                'No ISO build or in-game verification in this review.').format(stage, changes, SLUG, SLUG)
        prior_note = prior.get('note', '')
        review = dict(stage=stage, fingerprint=fingerprint(full['rows']),
                      reviewed_reused_ids=[r['id'] for r in reused],
                      reviewed_reused_rows=len(reused), source_uncertainties_retained=True,
                      reviewer='coordinator', note=prior_note if note in prior_note else
                      (prior_note + ' ' + note).strip())
        reviews['stages'][str(stage)] = review
        full['context_review'] = review
        full['context_review_pending'] = False
        full['full_checks'] = dict(rows=len(full['rows']),
                                  uses=sum(len(r['uses']) for r in full['rows']), problems=[])
        prepared.append((path, full))
        validation.append(dict(chapter=stage, rows=len(full['rows']),
                               changed_occurrences=changes, source_metadata_preserved=True,
                               problems=findings, fingerprint=review['fingerprint']))
    keys = [(o['stage'], o['full_id']) for o in overrides['overrides']]
    assert len(keys) == len(set(keys)), 'Duplicate overrides'
    for path, full in prepared:
        write(path, full)
        write(path.with_name(path.stem + '.en.json'), strip_jp.clean(full))
    write(override_path, overrides)
    write(override_path.with_name(override_path.stem + '.en.json'), strip_jp.clean(overrides))
    write(review_path, reviews)
    data['edits'].sort(key=lambda e: e['review_id'])
    data['validation'] = validation
    data['status'] = 'applied to current full campaign sources and scoped context overrides'
    data['reviewed_unique_rows'] = len(corpus)
    data['reviewed_assembled_rows'] = sum(v['rows'] for v in validation)
    data['changed_occurrences'] = len(edited)
    data['iso_rebuilt'] = False
    write(DECISIONS, data)
    coverage = read(WORK / 'coverage.json')
    coverage['reviewed_ranges'] = data['reviewed_ranges']
    coverage['complete'] = True
    write(WORK / 'coverage.json', coverage)
    write(ROOT / 'work/output' / (SLUG + '_verification.json'),
          {k: v for k, v in data.items() if k != 'edits'})
    print('Applied {} distinct corrections at {} row occurrences; {} rows pass checks.'.format(
        len(data['edits']), len(edited), data['reviewed_assembled_rows']))


def display(text):
    substitutions = {'#男愛称': '[Hugo]', '#男姓名': '[Hugo Medio]',
                     '#女愛称': '[Aqua]', '#女姓名': '[Aqua Centolm]',
                     '#機体名': '[unit name]', '#部隊名': '[squad name]'}
    for old, new in substitutions.items():
        text = text.replace(old, new)
    return text


def word_diff(before, after):
    a, b = display(before).split(' '), display(after).split(' ')
    old, new = [], []
    for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        x, y = html.escape(' '.join(a[i:j])), html.escape(' '.join(b[k:l]))
        if x:
            old.append('<mark>' + x + '</mark>' if tag != 'equal' else x)
        if y:
            new.append('<mark>' + y + '</mark>' if tag != 'equal' else y)
    return ' '.join(old), ' '.join(new)


def group_label(number):
    return {55: 'Finale', 56: 'Hidden stage', 57: 'Unused scenes',
            58: 'Closing / save messages'}.get(number, 'Chapter {}'.format(number))


def make_report(data=None, coverage=None, corpus=None, first=None, last=None, output=None):
    data = read(DECISIONS) if data is None else data
    assert data.get('validation'), 'Apply and validate the review first'
    coverage = read(WORK / 'coverage.json') if coverage is None else coverage
    corpus = read(WORK / 'review_rows.json') if corpus is None else corpus
    first = FIRST if first is None else first
    last = LAST if last is None else last
    assembled_count = data['reviewed_assembled_rows']
    distinct_count = data['reviewed_unique_rows']
    chapters = []
    for c, v in zip(coverage['chapters'], data['validation']):
        assert c['chapter'] == v['chapter']
        titles = '<br>'.join(html.escape(r['title']) +
                            (' <small>(' + html.escape(r['route']) + ' route)</small>'
                             if r['route'] != '-' else '') for r in c['routes'])
        chapters.append('<tr><th>{}</th><td>{}</td><td>{:,}</td><td>{}</td><td>Reviewed</td></tr>'.format(
            html.escape(group_label(c['chapter'])), titles, c['rows'], v['changed_occurrences']))
    cards = []
    for number, e in enumerate(data['edits'], 1):
        chapters_used = sorted({p[0] for p in e['appearances']})
        old, new = word_diff(e['before'], e['after'])
        row = e if 'kind' in e else corpus[e['review_id']]
        locs = []
        for chapter, full_id in e['appearances']:
            locs.append('{} · entry {}'.format(group_label(chapter), full_id))
        locations = html.escape('; '.join(locs))
        reason = html.escape(display(e['reason']))
        reason = re.sub(r'(https://www\.shorinjikempo\.or\.jp/en/what/discipline)',
                        r'<a href="\1" target="_blank" rel="noopener">Official Shorinji Kempo terminology</a>', reason)
        speaker = display(e['speaker'])
        if row['kind'] == 'thought':
            speaker += ' · thought'
        if not speaker:
            speaker = 'System text'
        badges = ''.join('<span>{}</span>'.format(html.escape(group_label(c))) for c in chapters_used)
        cards.append('''<article class="change" data-chapters="{chapters}" id="change-{n}">
<div class="card-head"><div class="badges">{badges}</div><a href="#change-{n}" class="index">Change {n:02d}</a></div>
<h3>{speaker}</h3><div class="comparison"><section class="before"><h4>Before</h4><p>{old}</p></section>
<section class="after"><h4>After</h4><p>{new}</p></section></div>
<p class="reason"><strong>Why it changed</strong> {reason}</p>
<details><summary>Locations ({count})</summary><p>{locations}</p></details></article>'''.format(
            chapters=','.join(map(str, chapters_used)), n=number, badges=badges,
            speaker=html.escape(speaker), old=old, new=new, reason=reason,
            count=len(locs), locations=locations))
    options = ''.join('<option value="{0}">{1}</option>'.format(n, html.escape(group_label(n))) for n in range(first, last + 1))
    retained = []
    for e in data.get('prior_fix_packet_sync', []):
        old, new = word_diff(e['before'], e['after'])
        chapter = int(re.search(r'stage(\d+)', e['source']).group(1))
        retained.append('''<section class="prior-item"><h3>{chapter} · source entry {id}</h3>
<div class="comparison"><section class="before"><h4>Older final packet</h4><p>{old}</p></section>
<section class="after"><h4>Retained approved text</h4><p>{new}</p></section></div>
<p class="reason">{reason}</p></section>'''.format(chapter=html.escape(group_label(chapter)), id=e['id'],
            old=old, new=new, reason=html.escape(e['reason'])))
    retained_section = ('''<details class="coverage retained"><summary>6 previously approved fixes retained in final inputs</summary>
<div class="prior-list"><p>These lines were already corrected in the assembled chapter sources before this review. Six older final-packet rows were synchronized so reassembly preserves those fixes. They are separate from the 91 new corrections above.</p>{items}</div></details>'''.format(items='\n'.join(retained))) if retained else ''
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SRW MX · Chapters 1–14 proofreading</title>
<style>
:root{color-scheme:light;--ink:#182a36;--muted:#536775;--teal:#006b68;--line:#dce5e8;--paper:#fff;--bg:#f3f6f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--teal);text-underline-offset:3px}main{max-width:1120px;margin:auto;padding:44px 28px 80px}
.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--teal);font-weight:750;margin:0 0 12px}
h1{font-size:clamp(32px,5vw,52px);line-height:1.12;letter-spacing:-1.5px;margin:0 0 20px;max-width:900px}
.intro{max-width:850px;color:var(--muted);margin-bottom:30px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:28px 0}
.stat{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:18px 20px}.stat b{display:block;font-size:32px;line-height:1.3;color:var(--teal)}.stat span{font-size:13px;color:var(--muted)}
.scope{border-left:3px solid var(--teal);padding:12px 20px;background:#e7f1f0;border-radius:0 8px 8px 0;margin:26px 0}.scope p{margin:0}.scope p+p{margin-top:8px}
.coverage{background:white;border:1px solid var(--line);border-radius:12px;margin:24px 0}.coverage>summary{padding:18px 22px;font-weight:650;cursor:pointer}.table-wrap{overflow:auto;padding:0 22px 18px}
table{width:100%;border-collapse:collapse;font-size:14px;text-align:left}th,td{padding:10px 14px;border-bottom:1px solid var(--line)}th:first-child,td:first-child{padding-left:0}small{color:var(--muted)}
.toolbar{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:16px 0;display:flex;align-items:flex-end;gap:14px;margin:32px 0 12px}
label{display:block;font-size:12px;font-weight:700;color:var(--muted);margin-bottom:5px}.search{flex:1}input,select,button{font:inherit;border:1px solid #b6c9ce;border-radius:7px;padding:10px 12px;color:var(--ink);background:white}
input{width:100%}button{cursor:pointer}button:hover{background:#e7f1f0}input:focus,select:focus,button:focus,summary:focus{outline:3px solid #73c6c3;outline-offset:2px}.count{color:var(--muted);font-size:14px}
.change{background:white;border:1px solid var(--line);border-radius:12px;padding:24px;margin:20px 0;scroll-margin-top:130px}.change[hidden]{display:none}
.card-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.badges{display:flex;flex-wrap:wrap;gap:5px}.badges span{font-size:11px;background:#e7f1f0;border-radius:4px;padding:3px 8px;color:var(--teal);font-weight:650}
.index{font-size:12px;color:var(--muted);white-space:nowrap}h3{font-size:19px;margin:10px 0 15px}h4{font-size:11px;letter-spacing:1.2px;text-transform:uppercase;margin:0 0 8px}
.comparison{display:grid;grid-template-columns:1fr 1fr;gap:16px}.comparison section{padding:18px;border-radius:8px}.comparison p{margin:0;white-space:pre-wrap;overflow-wrap:anywhere}
.before{background:#faf3f0}.after{background:#edf6f2}.before h4{color:#963d27}.after h4{color:#216044}mark{color:inherit;padding:1px 0;border-radius:2px}.before mark{background:#f4d6cd}.after mark{background:#cce9da}
.reason{font-size:14px;margin:18px 0 12px}.reason strong{display:block;color:var(--teal);font-size:12px;margin-bottom:3px}.change details{font-size:12px;color:var(--muted)}summary{cursor:pointer}.change details p{overflow-wrap:anywhere}
.prior-list{padding:0 22px 22px}.prior-item{border-top:1px solid var(--line);padding:14px 0}.empty{border:1px dashed #b6c9ce;padding:32px;text-align:center}.footer{color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:24px;margin-top:35px}
@media(max-width:720px){main{padding:28px 16px 60px}.stats{grid-template-columns:1fr 1fr}.comparison{grid-template-columns:1fr}.toolbar{flex-wrap:wrap;gap:8px}.search{flex-basis:100%}.change{padding:18px;scroll-margin-top:220px}select{max-width:200px}.stat{padding:14px}}
@media print{body{background:white;font-size:11pt}main{padding:0;max-width:none}.toolbar,.count,.print-button{display:none}.change{break-inside:avoid}.change[hidden]{display:block}.coverage:not(.retained){display:none}.stats{margin:15px 0}.stat b{font-size:24px}.change details{display:block}.change details p{display:block}.comparison section{border:1px solid #ddd}.change{margin:12px 0;padding:14px}.footer{font-size:10pt}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body><main>
<p class="eyebrow">Super Robot Wars MX · Editorial review · 9 October 2026</p>
<h1>Chapters 1–14,<br>proofread and explained.</h1>
<p class="intro">Every applicable route was checked against the Japanese source, with surrounding dialogue used to resolve meaning. Each correction below shows the previous English, the applied replacement, and its reason. Changed words are highlighted.</p>
<div class="stats"><div class="stat"><b>9,766</b><span>chapter entries reviewed</span></div><div class="stat"><b>7,745</b><span>distinct entries checked</span></div><div class="stat"><b>__EDITS__</b><span>distinct corrections</span></div><div class="stat"><b>__OCCURRENCES__</b><span>entry occurrences updated</span></div></div>
<div class="scope"><p><strong>Applied to current campaign translation sources.</strong> Identical repeated lines were reviewed once and corrections applied to every listed occurrence within Chapters 1–14. All routes are included, including both opening routes.</p>
<p>All 9,766 entries pass the current source checks for font width, dialogue length, names, characters and runtime placeholders. Existing source uncertainty notes were retained. This is a source review; PSP and PS2 ISO images have not been rebuilt or tested in game as part of this work.</p></div>
<details class="coverage"><summary>Review coverage by chapter · all 14 complete</summary><div class="table-wrap"><table><thead><tr><th>Chapter</th><th>Current route title</th><th>Entries</th><th>Changed entries</th><th>Status</th></tr></thead><tbody>__CHAPTERS__</tbody></table><p><small>Entry counts include reused dialogue, choices and objective text. Titles are the current route labels, included for orientation.</small></p></div></details>
<p class="count">Deliberate jokes, dialect, interrupted speech and plot-specific beliefs were preserved. Square brackets display customizable names and unit names in readable form; the underlying runtime placeholders are unchanged.</p>
<div class="toolbar"><div class="search"><label for="search">Search changes</label><input type="search" id="search" placeholder="Speaker, wording, or reason…"></div><div><label for="chapter">Chapter</label><select id="chapter"><option value="all">All chapters</option>__OPTIONS__</select></div><button id="reset" type="button">Reset</button><button class="print-button" id="print" type="button">Print</button></div>
<p id="count" class="count" role="status" aria-live="polite"></p><div id="changes">__CARDS__</div><p id="empty" class="empty" hidden>No changes match these filters.</p>
__RETAINED__<p class="footer">The report documents every applied correction. It does not include the original Japanese script. Source checks confirm formatting and metadata preservation; actual rendering and playthrough checks require a subsequent game build. No release was created.</p>
</main><script>
const cards=Array.from(document.querySelectorAll('.change'));
const search=document.getElementById('search'),chapter=document.getElementById('chapter');
function filter(){const q=search.value.trim().toLocaleLowerCase(),c=chapter.value;let n=0;for(const card of cards){const show=(c==='all'||card.dataset.chapters.split(',').includes(c))&&card.textContent.toLocaleLowerCase().includes(q);card.hidden=!show;if(show)n++;}document.getElementById('count').textContent=`Showing ${n} of ${cards.length} corrections`;document.getElementById('empty').hidden=n!==0;}
search.addEventListener('input',filter);chapter.addEventListener('change',filter);document.getElementById('reset').addEventListener('click',()=>{search.value='';chapter.value='all';filter();});document.getElementById('print').addEventListener('click',()=>window.print());filter();
const printDetails=Array.from(document.querySelectorAll('details'));window.addEventListener('beforeprint',()=>{cards.forEach(card=>card.hidden=false);printDetails.forEach(d=>{d.dataset.wasOpen=d.open?'1':'0';d.open=true;});});window.addEventListener('afterprint',()=>{printDetails.forEach(d=>d.open=d.dataset.wasOpen==='1');filter();});
</script></body></html>'''
    for key, value in {'EDITS': str(len(data['edits'])), 'OCCURRENCES': str(data['changed_occurrences']),
                       'CHAPTERS': '\n'.join(chapters), 'OPTIONS': options,
                       'CARDS': '\n'.join(cards), 'RETAINED': retained_section}.items():
        page = page.replace('__' + key + '__', value)
    # Keep the original report reproducible while supporting later chapter ranges.
    page = page.replace('Chapters 1–14', 'Chapters {}–{}'.format(first, last))
    page = page.replace('all 14 complete', 'all {} complete'.format(last - first + 1))
    page = page.replace('9,766', '{:,}'.format(assembled_count)).replace('7,745', '{:,}'.format(distinct_count))
    page = page.replace('6 previously approved fixes', '{} previously approved fixes'.format(len(retained)))
    page = page.replace('Six older final-packet rows', '{} older final-packet rows'.format(len(retained)))
    page = page.replace('the 91 new corrections above', 'the {} proofreading corrections above'.format(len(data['edits'])))
    if last == 58:
        page = page.replace('Chapters {}–58'.format(first), 'Chapters {}–end'.format(first))
        page = page.replace('all {} complete'.format(last - first + 1),
                            'all {} source groups complete'.format(last - first + 1))
        page = page.replace('including both opening routes.',
                            'including alternate battles, the finale, epilogue, hidden stage, unused scenes and closing/save messages.')
        page = page.replace('by chapter ·', 'by chapter and scene group ·')
        page = page.replace('chapter entries reviewed', 'campaign entries reviewed')
        page = page.replace('<th>Chapter</th>', '<th>Chapter / scene</th>')
        page = page.replace('<label for="chapter">Chapter</label>', '<label for="chapter">Chapter / scene</label>')
        page = page.replace('>All chapters</option>', '>All scenes</option>')
        if first == 1:
            page = page.replace('Chapters 1–end,<br>', 'Complete campaign,<br>')
    if first == 15 and last == 30:
        page = page.replace('<span>distinct entries checked</span>', '<span>additional distinct entries checked</span>')
        page = page.replace('Every applicable route was checked against the Japanese source, with surrounding dialogue used to resolve meaning.',
            'This continuation checked 8,140 additional distinct entries against the Japanese source in scene context. '
            'Another 3,048 chapter-entry occurrences inherit exact source, speaker and English matches from completed earlier reviews.')
    from datetime import date
    reviewed_date = date.fromisoformat(data['date'])
    page = page.replace('9 October 2026', '{} {} {}'.format(
        reviewed_date.day, reviewed_date.strftime('%B'), reviewed_date.year))
    output = ROOT / ('work/output/' + SLUG + '.html') if output is None else output
    output.write_text(page, encoding='utf-8')
    assert page.count('<article class="change"') == len(data['edits'])
    assert not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', page)
    print('HTML report: ' + str(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('start', type=int, nargs='?')
    parser.add_argument('stop', type=int, nargs='?')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--chapters', nargs=2, type=int, default=[1, 14])
    args = parser.parse_args()
    configure(*args.chapters)
    if args.apply:
        apply_review()
    if args.report:
        make_report()
    if args.start is not None and args.stop is not None:
        show(args.start, args.stop)
