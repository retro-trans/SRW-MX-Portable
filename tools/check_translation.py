"""Validate an independent model's 80-row slices without changing its raw output.

Default is a read-only preview. --write saves a merged working file and report.
Example: py -3 tools/check_translation.py work/translation/en/script/stage30s.json codex --write
"""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

import textfit


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def name_context_rules():
    return read(Path('work/glossary/name_fixes.json')).get('context_exceptions', [])


@lru_cache(maxsize=1)
def name_context_replacements():
    return read(Path('work/glossary/name_fixes.json')).get('context_replacements', [])


def contextual_name_fixes(raw, fixes):
    result = dict(fixes)
    source = raw.get('body_jp', raw.get('jp', ''))
    rules = name_context_rules()
    for rule in rules:
        if rule['source_contains'] in source and (
                not rule.get('source_not_contains') or rule['source_not_contains'] not in source) and (
                not rule.get('speaker_is') or raw.get('speaker_en') == rule['speaker_is']):
            result.pop(rule['variant'], None)
    for rule in name_context_replacements():
        if rule['source_contains'] in source and (
                not rule.get('source_not_contains') or rule['source_not_contains'] not in source):
            result.update(rule['variants'])
    return result


def validate(source_path, model, review_variants=None, packet_intervals=None):
    source = read(source_path)
    original = source['rows']
    base = source_path.with_suffix('')
    files = sorted(base.parent.glob(base.name + '_' + model + '_slice_*.json'))
    files = [p for p in files if not p.name.endswith('.en.json')]
    problems, warnings, translated = [], [], []
    expected = [r['id'] for r in original]
    assert len(expected) == len(set(expected)), 'Duplicate source IDs'
    assert expected == list(range(len(expected))), 'Source IDs must be consecutive in play order'
    for path in files:
        data = read(path)
        n = data['slice']
        if packet_intervals is None:
            wanted = expected[n * 80:(n + 1) * 80]
        else:
            start, stop = packet_intervals.get(n, (0, 0))
            wanted = expected[start:stop]
        got = [r['id'] for r in data['rows']]
        if not wanted or got != wanted:
            problems.append('{}: expected ids {}, got {}'.format(path.name, wanted, got))
        translated.extend(data['rows'])
    counts = Counter(r['id'] for r in translated)
    missing = sorted(set(expected) - set(counts))
    unexpected = sorted(set(counts) - set(expected))
    duplicate = sorted(i for i, count in counts.items() if count > 1)
    if missing or unexpected or duplicate:
        problems.append('IDs: missing {}, unexpected {}, duplicate {}'.format(missing, unexpected, duplicate))
    byid = {r['id']: r for r in translated}
    fixes = dict(read(Path('work/glossary/name_fixes.json'))['names'])
    fixes.update(review_variants or {})
    allowed = set(textfit.ASCII) | {'"'}
    metrics, merged = [], []
    for raw in original:
        t = byid.get(raw['id'])
        if t is None:
            continue
        rid = raw['id']
        for key in ('speaker_en', 'en', 'notes', 'uncertain'):
            if key not in t:
                problems.append('{}: missing field {}'.format(rid, key))
        en, speaker = t.get('en', ''), t.get('speaker_en', '')
        if not isinstance(en, str) or not en.strip():
            problems.append('{}: empty/non-string translation'.format(rid))
            continue
        if not isinstance(speaker, str):
            problems.append('{}: non-string speaker'.format(rid))
            continue
        if raw['kind'] != 'plain' and not speaker:
            problems.append('{}: empty speaker'.format(rid))
        if raw.get('speaker_en') and speaker != raw['speaker_en']:
            problems.append('{}: speaker differs from prefilled glossary spelling'.format(rid))
        if not isinstance(t.get('notes', ''), str) or not isinstance(t.get('uncertain', []), list) or any(
                not isinstance(s, str) for s in t.get('uncertain', [])):
            problems.append('{}: invalid notes/uncertain type'.format(rid))
        rest = en
        for ph in textfit.PLACEHOLDER_PX:
            src = raw['jp'] if raw['kind'] == 'plain' else raw['body_jp']
            if src.count(ph) != en.count(ph):
                problems.append('{}: placeholder count differs for {}'.format(rid, ph))
            rest = rest.replace(ph, '')
        if raw['kind'] == 'plain':
            rest = rest.replace('@', '')
            if en.count('@') != raw['jp'].count('@'):
                problems.append('{}: plain line count differs'.format(rid))
            widths = [textfit.px(line) for line in en.split('@')]
            ok = all(w <= textfit.LINE_PX for w in widths)
            if not ok:
                problems.append('{}: plain line widths {}'.format(rid, widths))
        else:
            _, lines, ok = textfit.fit_dialogue(speaker, en, raw['kind'] == 'thought')
            widths = [textfit.px(line) for line in lines]
            if not ok:
                problems.append('{}: dialogue overflow {} lines, widths {}'.format(rid, len(lines), widths))
        if set(rest) - allowed:
            problems.append('{}: unsupported body characters {}'.format(rid, sorted(set(rest) - allowed)))
        sp_rest = speaker
        for ph in textfit.PLACEHOLDER_PX:
            sp_rest = sp_rest.replace(ph, '')
        if set(sp_rest) - allowed:
            problems.append('{}: unsupported speaker characters'.format(rid))
        # Protect canonical forms before searching variants nested within them.
        row_fixes = contextual_name_fixes(raw, fixes)
        # Source-prefilled labels are immutable; their equality was checked
        # above. Spelling reconciliation applies to bodies and new labels.
        name_text = ('' if raw.get('speaker_en') == speaker else speaker) + ' ' + en
        for canonical in sorted(set(row_fixes.values()), key=len, reverse=True):
            name_text = re.sub(r'(?<![A-Za-z])' + re.escape(canonical) + r'(?![A-Za-z])', '', name_text)
        for old, new in row_fixes.items():
            if re.search(r'(?<![A-Za-z])' + re.escape(old) + r'(?![A-Za-z])', name_text):
                problems.append('{}: old spelling {} (expected {})'.format(rid, old, new))
        metrics.append(dict(id=rid, kind=raw['kind'], lines=len(widths), widths=widths, fits=ok,
                            uncertain=bool(t.get('uncertain')), characters=len(en)))
        row = dict(raw)
        row.update(t)
        row.update(lines=len(widths), px=max(widths))
        merged.append(row)
    # This known source-level relationship needs semantic review, not a substring test:
    # row 334 recalls only part of 190 and changes the speaker's point of view.
    if base.name == 'stage30s' and 190 in byid and 334 in byid:
        warnings.append('Rows 190 and 334 need human review of the recalled wording before production use. Raw comparison output is preserved.')
    report = dict(model_tag=model, source=source_path.as_posix(),
                  source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                  slice_files=[p.as_posix() for p in files], expected_rows=len(original),
                  translated_rows=len(byid), problems=problems, warnings=warnings,
                  rows_with_uncertainty=sum(m['uncertain'] for m in metrics),
                  three_line_dialogue_rows=sum(m['lines'] == 3 for m in metrics if m['kind'] != 'plain'),
                  total_english_characters=sum(m['characters'] for m in metrics), rows=metrics,
                  plain_width_limit='Provisional conservative 352 px per line; condition window not measured in game.')
    if review_variants:
        report['additional_review_variants'] = review_variants
    result = dict(source)
    result['rows'] = merged
    result['translation_model_tag'] = model
    return base, result, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('model')
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--review-variants', type=Path,
                        help='Additional source-backed spelling variants to flag without changing raw translations.')
    parser.add_argument('--comparison', action='store_true',
                        help='Preserve complete raw output with content/fit errors for model review; never build it without reconciliation.')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.model):
        parser.error('model tag must contain only letters, digits, underscores or hyphens')
    review = read(args.review_variants) if args.review_variants else {}
    base, merged, report = validate(args.source, args.model, review.get('names'))
    if args.review_variants:
        report['review_variant_sources'] = review.get('sources', {})
    print('{}/{} rows; {} problems; {} warnings; {} uncertainty rows'.format(
        report['translated_rows'], report['expected_rows'], len(report['problems']),
        len(report['warnings']), report['rows_with_uncertainty']))
    for row in merged['rows'][:2]:
        print('Preview {}: {} | {}'.format(row['id'], row['speaker_en'], row['en']))
    for problem in report['problems'] + report['warnings']:
        print(problem)
    if args.write:
        structural = [p for p in report['problems'] if p.startswith('IDs:') or any(s in p for s in (
            ': expected ids ', ': missing field ', ': empty/non-string translation',
            ': non-string speaker', ': invalid notes/uncertain type'))]
        complete = report['translated_rows'] == report['expected_rows'] == len(merged['rows'])
        if report['problems'] and not (args.comparison and complete and not structural):
            raise SystemExit('Refusing to write an invalid merged translation.')
        report['comparison_only'] = bool(report['problems'])
        merged['comparison_only'] = bool(report['problems'])
        for suffix, data in [('merged', merged), ('checks', report)]:
            path = base.parent / (base.name + '_' + args.model + '_' + suffix + '.json')
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + chr(10), encoding='utf-8')
            print('Wrote', path.as_posix())
    raise SystemExit(bool(report['problems']))


if __name__ == '__main__':
    main()
