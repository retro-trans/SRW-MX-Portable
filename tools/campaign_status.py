"""Read-only campaign checks; --write saves status and valid assembled stage files."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import check_translation
import strip_jp
import textfit
import campaign_context_overrides
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT/'work/output/stages01_30_sol_medium_manifest.json'
TAG = 'sol61medium'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


def safe_copy(path, data):
    write(path.with_name(path.stem+'.en.json'), strip_jp.clean(data))


def check_full(rows):
    findings = []
    allowed = set(textfit.ASCII) | {'"'}
    fixes = read(ROOT/'work/glossary/name_fixes.json')['names']
    for row in rows:
        en = row['en']
        if row.get('kind') != 'plain' and not row.get('speaker_en', '').strip():
            findings.append('{}: empty speaker'.format(row['id']))
        rest = en
        for ph in textfit.PLACEHOLDER_PX:
            if row['body_jp'].count(ph) != en.count(ph):
                findings.append('{}: placeholder {}'.format(row['id'],ph))
            rest = rest.replace(ph,'')
        if row['kind'] == 'plain':
            widths = [textfit.px(x) for x in en.split('@')]
            ok = all(w <=352 for w in widths)
            rest = rest.replace('@','')
            if en.count('@') != row['jp'].count('@'):
                findings.append('{}: plain line breaks'.format(row['id']))
        else:
            _, lines, ok = textfit.fit_dialogue(row['speaker_en'],en,row['kind']=='thought')
            widths = [textfit.px(x) for x in lines]
        if not ok:
            findings.append('{}: overflow {}'.format(row['id'],widths))
        if set(rest)-allowed:
            findings.append('{}: unsupported body characters'.format(row['id']))
        if not en.strip():
            findings.append('{}: empty body'.format(row['id']))
        row_fixes = check_translation.contextual_name_fixes(row, fixes)
        # Full rows inherit validated, immutable source speaker prefills.
        name_text = en
        for canonical in sorted(set(row_fixes.values()),key=len,reverse=True):
            name_text = re.sub(r'(?<![A-Za-z])'+re.escape(canonical)+r'(?![A-Za-z])','',name_text)
        for old,new in row_fixes.items():
            if re.search(r'(?<![A-Za-z])'+re.escape(old)+r'(?![A-Za-z])',name_text):
                findings.append('{}: old spelling {} -> {}'.format(row['id'],old,new))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    args = parser.parse_args()
    manifest = read(args.manifest)
    available = {}
    for seed in manifest.get('seed_sources', []):
        if seed.endswith('prologue_merged.json'):
            continue  # The legacy reconciliation below handles this source.
        available[seed] = {r['id']: r for r in read(ROOT/seed)['rows']}
    validation = []
    total = 0
    context_overrides = campaign_context_overrides.load_overrides()
    for stage in manifest['stages']:
        source = ROOT/'work/translation/en/script'/ (stage['base']+'.json')
        if hashlib.sha256(source.read_bytes()).hexdigest() != stage['source_sha256']:
            raise RuntimeError('Source changed: '+str(source))
        stage_packets = [p for p in manifest['packets'] if p['stage'] == stage['stage']]
        cursor = 0
        for index, packet in enumerate(stage_packets):
            if packet['slice'] != index or packet['start'] != cursor or not 0 < packet['stop']-packet['start'] <= 80:
                raise ValueError('Invalid campaign interval: {}'.format(packet))
            cursor = packet['stop']
        if cursor != stage['rows']:
            raise ValueError('Campaign intervals do not cover stage {}'.format(stage['stage']))
        intervals = {p['slice']: (p['start'], p['stop']) for p in stage_packets}
        base, merged, report = check_translation.validate(source, TAG, packet_intervals=intervals)
        # Missing packets are normal in progress; duplicates/unexpected IDs never are.
        pending_coverage = 'IDs: missing '
        findings = [p for p in report['problems'] if not (p.startswith(pending_coverage)
                    and p.endswith('unexpected [], duplicate []'))]
        report['available_row_problems'] = findings
        report['complete'] = not report['problems'] and report['translated_rows'] == stage['rows']
        validation.append(report)
        files = {read(Path(p))['slice']: Path(p) for p in report['slice_files']}
        metrics = {r['id']: r for r in report['rows']}
        for packet in [p for p in manifest['packets'] if p['stage'] == stage['stage']]:
            index = packet['slice']
            path = files.get(index)
            if not path:
                continue
            problems = [p for p in findings if p.startswith(path.name+':') or
                        any(p.startswith(str(i)+':') for i in range(packet['start'],packet['stop'])) or p.startswith('IDs:')]
            report_path = path.with_name(path.name.replace('_slice_', '_report_')).with_suffix('.md')
            draft_path = path.with_name(path.name.replace('_slice_', '_draft_'))
            if not draft_path.exists():
                problems.append('Initial draft missing')
            else:
                draft = read(draft_path)
                if [r['id'] for r in draft['rows']] != list(range(packet['start'],packet['stop'])):
                    problems.append('Initial draft coverage differs')
            if not report_path.exists():
                problems.append('Decision/fit report pending')
            packet['findings'] = problems
            packet['status'] = 'check_failed' if problems else 'validated'
            packet['translated_rows'] = len(read(path)['rows'])
            packet['uncertain_rows'] = sum(metrics.get(i,{}).get('uncertain',False) for i in range(packet['start'],packet['stop']))
            if not problems:
                total += packet['translated_rows']
                if args.write:
                    safe_copy(path, read(path))
                    safe_copy(draft_path, read(draft_path))
        if report['complete']:
            available[str(source.relative_to(ROOT)).replace('\\','/')] = {r['id']:r for r in merged['rows']}
            if args.write:
                target = base.parent/(base.name+'_'+TAG+'_merged.json')
                write(target, merged)
                safe_copy(target, merged)
        if args.write and report['translated_rows']:
            write(ROOT/'work/output'/(stage['base']+'_checks.json'), report)
    legacy = read(ROOT/'work/translation/en/script/prologue_merged.json')['rows']
    legacy_fixes = []
    decisions_path = ROOT/'work/translation/en/script/campaign_reuse_decisions.json'
    decisions = read(decisions_path)['overrides'] if decisions_path.exists() else []
    reuse_edits = []
    fixes = read(ROOT/'work/glossary/name_fixes.json')['names']
    for original in legacy:
        row = dict(original)
        for decision in decisions:
            if decision['source'] == 'work/translation/en/script/prologue_merged.json' and decision['id'] == row['id']:
                if row['en'] != decision['expected_en']:
                    raise ValueError('Reuse override original differs: {}'.format(row['id']))
                reuse_edits.append(dict(id=row['id'], before=row['en'], after=decision['en'], reason=decision['reason']))
                row['en'] = decision['en']
                row['notes'] = row.get('notes', '')+' '+decision['reason']
        # This legacy file already passed meaning review. Reconcile source-backed
        # spellings on copies, leaving original prologue/build untouched.
        for field in ['speaker_en','en']:
            before = row.get(field,'')
            after = before
            for old,new in sorted(check_translation.contextual_name_fixes(row, fixes).items(),key=lambda x:len(x[0]),reverse=True):
                after = re.sub(r'(?<![A-Za-z])'+re.escape(old)+r'(?![A-Za-z])',new,after)
            if before != after:
                legacy_fixes.append(dict(id=row['id'],field=field,before=before,after=after))
                row[field] = after
                row['notes'] = row.get('notes','')+' Campaign assembly reconciles legacy spelling to name_fixes.json; original prologue retained.'
        available.setdefault('work/translation/en/script/prologue_merged.json',{})[row['id']] = row
    if legacy_fixes:
        print('Legacy spelling reconciliation preview: '+json.dumps(legacy_fixes,ensure_ascii=False))
        if args.write:
            write(ROOT/'work/output/campaign_prologue_spelling_reconciliation.json',legacy_fixes)
    if reuse_edits:
        print('Reuse meaning review preview: '+json.dumps(reuse_edits,ensure_ascii=False))
    if args.write:
        write(ROOT/'work/output/campaign_reuse_meaning_reconciliation.json',reuse_edits)
    assembled = []
    context_reviews_path = ROOT / manifest.get('context_reviews', 'work/output/campaign_context_reviews.json')
    context_reviews = read(context_reviews_path)['stages'] if context_reviews_path.exists() else {}
    for stage in manifest['stages']:
        all_path = ROOT/'work/translation/en/script'/(stage['base']+'_all_source.json')
        full = read(all_path)
        rows = []
        for original in full['rows']:
            owner = original['translation_owner']
            translated = available.get(owner['source'],{}).get(owner['id'])
            if not translated:
                break
            row = dict(original)
            row.update({k:translated.get(k,[] if k=='uncertain' else '') for k in ['speaker_en','en','notes','uncertain']})
            row = campaign_context_overrides.apply_override(stage['stage'], row, context_overrides)
            rows.append(row)
        if len(rows) != stage['all_rows']:
            continue
        findings = check_full(rows)
        stage['full_stage_findings'] = findings
        if findings:
            print('Stage {} full-stage findings: {}'.format(stage['stage'],findings))
            continue
        assembled.append(stage['stage'])
        full['rows'] = rows
        full['translation_model_tag'] = TAG
        review = context_reviews.get(str(stage['stage']), {})
        full['context_review_pending'] = review.get('fingerprint') != fingerprint(rows)
        if not full['context_review_pending']:
            full['context_review'] = review
        full['full_checks'] = dict(rows=len(rows), uses=sum(len(r['uses']) for r in rows), problems=[])
        if args.write:
            target = all_path.with_name(stage['base']+'_full_merged.json')
            write(target, full)
            safe_copy(target, full)
    manifest['validated_new_rows'] = total
    manifest['assembled_stages'] = assembled
    summary = dict(validated_new_rows=total, total_new_rows=sum(s['rows'] for s in manifest['stages']),
                   validated_packets=sum(p['status']=='validated' for p in manifest['packets']),
                   running_packets=[dict(stage=p['stage'],slice=p['slice'],agent=p.get('agent')) for p in manifest['packets'] if p['status']=='running'],
                   failures=[dict(stage=p['stage'],slice=p['slice'],findings=p.get('findings')) for p in manifest['packets'] if p['status']=='check_failed'],
                   assembled_stages=assembled)
    print(json.dumps(summary,ensure_ascii=False))
    if args.write:
        write(args.manifest, manifest)
        write(args.manifest.with_name(args.manifest.stem.replace('_manifest', '_status')+'.json'),summary)


if __name__ == '__main__':
    main()
