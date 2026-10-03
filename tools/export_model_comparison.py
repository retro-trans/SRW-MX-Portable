"""Preview or export a Stage 30 comparison and commit-safe new-model copies.

The default exports the original nine candidates. --updated-rules exports the
six candidates translated under the current rules, excluding Luna. --sol-efforts
exports the fresh Sol 6.1 Low/Medium/High/XHigh comparison.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

import post_sheet
import strip_jp
import textfit

BASE = Path('work/translation/en/script/stage30s')
NEW = [('sol61', 'Sol 6.1', 'gpt-6.1-sol'), ('astra6', 'Astra 6', 'gpt-6-astra'),
       ('luna6', 'Luna 6', 'gpt-6-luna'), ('terra56', 'Terra 5.6', 'gpt-5.6-terra')]
OLD = [('opus', 'Opus 5.5'), ('sonnet', 'Sonnet 5.5'), ('haiku', 'Haiku 4.5'),
       ('fable', 'Fable 5.1'), ('codex', 'Codex (OpenAI session)')]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--updated-rules', action='store_true',
                        help='Export the six-candidate rerun with Sol, Astra and Terra; excludes Luna.')
    parser.add_argument('--sol-efforts', action='store_true',
                        help='Export the four fresh Sol 6.1 Low/Medium/High/XHigh candidates.')
    args = parser.parse_args()
    if args.updated_rules and args.sol_efforts:
        parser.error('Choose either --updated-rules or --sol-efforts.')
    new = ([('sol61r2', 'Sol 6.1', 'gpt-6.1-sol'), ('astra6r2', 'Astra 6', 'gpt-6-astra'),
            ('terra56r2', 'Terra 5.6', 'gpt-5.6-terra')] if args.updated_rules else NEW)
    old = ([('opus2', 'Opus 5.5'), ('sonnet2', 'Sonnet 5.5'), ('fable2', 'Fable 5.1')]
           if args.updated_rules else OLD)
    run_name = 'updated_rules' if args.updated_rules else 'openai_models'
    if args.sol_efforts:
        new = [('sol61low3', 'Sol 6.1 Low', 'gpt-6.1-sol'),
               ('sol61med3', 'Sol 6.1 Medium', 'gpt-6.1-sol'),
               ('sol61high3', 'Sol 6.1 High', 'gpt-6.1-sol'),
               ('sol61xhigh3', 'Sol 6.1 XHigh', 'gpt-6.1-sol')]
        old, run_name = [], 'sol_efforts'
    source_path = BASE.with_suffix('.json')
    source = read(source_path)['rows']
    fingerprint = hashlib.sha256(source_path.read_bytes()).hexdigest()
    stats, copies = [], []
    for tag, label, model_id in new:
        prefix = BASE.with_name(BASE.name + '_' + tag)
        final = read(prefix.with_name(prefix.name + '_merged.json'))['rows']
        checks = read(prefix.with_name(prefix.name + '_checks.json'))
        assert checks['source_sha256'] == fingerprint
        assert checks['translated_rows'] == checks['expected_rows'] == len(final) == 376
        drafts = [r for n in range(5) for r in read(prefix.with_name(prefix.name + '_draft_' + str(n) + '.json'))['rows']]
        assert [r['id'] for r in drafts] == list(range(376))
        compressed, overflow_drafts, changed = [], [], []
        for original, draft, row in zip(source, drafts, final):
            assert original['id'] == draft['id'] == row['id']
            if original['kind'] == 'plain':
                fits = all(textfit.px(line) <= 352 for line in draft['en'].split('@'))
            else:
                _, _, fits = textfit.fit_dialogue(draft['speaker_en'], draft['en'], original['kind'] == 'thought')
            if not fits:
                overflow_drafts.append(row['id'])
            if row['en'] != draft['en']:
                changed.append(row['id'])
                if not fits:
                    compressed.append(row['id'])
        stats.append(dict(tag=tag, label=label, requested_model_id=model_id, translated_rows=376,
                          uncertainty_rows=checks['rows_with_uncertainty'],
                          final_nonfit_ids=[r['id'] for r in checks['rows'] if not r['fits']],
                          content_problems=checks['problems'],
                          three_line_dialogue_rows=checks['three_line_dialogue_rows'],
                          english_characters=checks['total_english_characters'],
                          initial_nonfit_ids=overflow_drafts, compressed_ids=compressed,
                          body_changed_ids=changed, source_sha256=fingerprint))
        for path in sorted(prefix.parent.glob(prefix.name + '_*.json')):
            if path.name.endswith('.en.json'):
                continue
            copies.append((path.with_name(path.stem + '.en.json'), strip_jp.clean(read(path))))
    names = dict(old + [(tag, label) for tag, label, _ in new])
    table, notes, unique = post_sheet.build(str(BASE), list(names), names)
    diagnostic_notes = []
    for row in stats:
        for problem in row['content_problems']:
            match = re.match(r'^(\d+): ', problem)
            if match:
                diagnostic_notes.append([int(match.group(1)), row['label'],
                                         'Automated check (not translator notes): ' + problem])
    notes.extend(diagnostic_notes)
    candidate_count = len(names)
    columns = 9 + candidate_count
    assert unique == 376 and len(table) == 383 and len(table[0]) == columns
    assert all(len(row) == columns and all(row[7:7+candidate_count]) for row in table[1:])
    summary = dict(source_sha256=fingerprint, unique_rows=unique, occurrences=len(table)-1,
                   candidate_count=candidate_count, new_candidates=stats, reasoning_settings='Inherited session settings, not experimentally varied.')
    if args.sol_efforts:
        summary['reasoning_settings'] = dict(zip([tag for tag, _, _ in new],
                                                 ['low', 'medium', 'high', 'xhigh']))
        summary['independent_fresh_translations'] = True
    if args.updated_rules or args.sol_efforts:
        summary['base_rules_sha256'] = hashlib.sha256(Path('BASE_RULES.md').read_bytes()).hexdigest()
        summary['brief_sha256'] = hashlib.sha256((BASE.parent / 'TRANSLATOR_BRIEF.md').read_bytes()).hexdigest()
        summary['event_order_sha256'] = hashlib.sha256(BASE.with_name(BASE.name + '_order.json').read_bytes()).hexdigest()
        summary['luna_excluded'] = True
    summary['automated_note_count'] = len(diagnostic_notes)
    header = '| Model | Rows | Final fit failures | Check problems | Uncertainty rows | Compressed rows | Three-line dialogue | English characters |'
    lines = [header, '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in stats:
        lines.append('| {} | 376/376 | {} | {} | {} | {} | {} | {:,} |'.format(
            row['label'], len(row['final_nonfit_ids']), len(row['content_problems']), row['uncertainty_rows'],
            ', '.join(map(str, row['compressed_ids'])) or 'None', row['three_line_dialogue_rows'], row['english_characters']))
    markdown = chr(10).join(lines)
    print(markdown)
    print('Preview: {} rows, {} columns, {} note entries; {} English-only copies.'.format(len(table)-1, len(table[0]), len(notes)-1, len(copies)))
    print('Headers:', table[0])
    print('Sample new candidate bodies:', table[1][7+len(old):7+candidate_count])
    if not args.write:
        return
    for path, values in [
            (Path('work/output/stage30s_comparison_' + run_name + '.csv'), table),
            (Path('work/output/stage30s_comparison_' + run_name + '_notes.csv'), notes)]:
        assert not path.exists(), str(path)
        with path.open('w', encoding='utf-8-sig', newline='') as stream:
            csv.writer(stream).writerows(values)
    for path, data in copies:
        assert not path.exists(), str(path)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + chr(10), encoding='utf-8')
    suffix = ('_sol_efforts_summary.en.json' if args.sol_efforts else
              '_updated_rules_summary.en.json' if args.updated_rules else '_openai_model_summary.en.json')
    path = BASE.with_name(BASE.name + suffix)
    assert not path.exists(), str(path)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=1) + chr(10), encoding='utf-8')
    metrics_name = 'sol_efforts' if args.sol_efforts else 'updated_rules' if args.updated_rules else 'openai'
    Path('work/output/stage30s_' + metrics_name + '_metrics.md').write_text(markdown + chr(10), encoding='utf-8')
    print('Saved offline comparison, notes, metrics, summary and new-candidate commit-safe copies.')


if __name__ == '__main__':
    main()
