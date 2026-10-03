"""Add independent model candidates to the existing Stage 30 review sheet in place.

Default is a read-only plan. --write inserts candidate columns before the review columns,
appends translator notes, and verifies all original cells remained unchanged. Raw model
output is retained even when its content checks report review issues.

Example: py -3 -X utf8 tools/update_review_sheet.py <key> "sol61=Sol 6.1" --write
"""
import argparse
import json
from pathlib import Path
import re
import sys

import gspread

SID = '1lM4a8A9B86JXndgcBgEcZtjFhXfcVpbFpOwu7tc10TY'
TITLE = 'Stage 30 Space'
NTITLE = TITLE + ' notes'
FIELDS = ('userEnteredValue', 'userEnteredFormat', 'dataValidation', 'note', 'textFormatRuns', 'chipRuns')


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + chr(10), encoding='utf-8')


def grid(sheet):
    return [row.get('values', []) for row in sheet.get('data', [{}])[0].get('rowData', [])]


def value(cell):
    val = cell.get('effectiveValue', cell.get('userEnteredValue', {}))
    return val.get('stringValue', val.get('numberValue', val.get('boolValue', '')))


def at(rows, r, c):
    return rows[r][c] if r < len(rows) and c < len(rows[r]) else {}


def project(cell):
    return {key: cell[key] for key in FIELDS if key in cell}


def native(values):
    return [{'values': [{'userEnteredValue': {'numberValue': v} if isinstance(v, (int, float))
                         else {'stringValue': str(v)}} for v in row]} for row in values]


def rectangle(sid, r0, r1, c0, c1):
    return dict(sheetId=sid, startRowIndex=r0, endRowIndex=r1, startColumnIndex=c0, endColumnIndex=c1)


def write_cells(sid, r0, c0, values):
    width = len(values[0])
    assert all(len(row) == width for row in values)
    return {'updateCells': {'range': rectangle(sid, r0, r0 + len(values), c0, c0 + width),
                            'rows': native(values), 'fields': 'userEnteredValue'}}


def copy_format(sid, r0, r1, c0, c1, dr0, dr1, dc0, dc1):
    return {'copyPaste': {'source': rectangle(sid, r0, r1, c0, c1),
                          'destination': rectangle(sid, dr0, dr1, dc0, dc1),
                          'pasteType': 'PASTE_FORMAT', 'pasteOrientation': 'NORMAL'}}


def bounded_range(title, rows, columns):
    column = gspread.utils.rowcol_to_a1(1, columns)[:-1]
    return "'{}'!A1:{}{}".format(title.replace("'", "''"), column, rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key', type=Path)
    parser.add_argument('models', nargs='+', help='tag=Display name')
    parser.add_argument('--spreadsheet-id', default=SID,
                        help='Existing destination spreadsheet; defaults to the original comparison.')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    specs = [spec.split('=', 1) for spec in args.models]
    assert all(len(spec) == 2 and re.fullmatch(r'[A-Za-z0-9_-]+', spec[0]) and spec[1] for spec in specs)
    tags, labels = [s[0] for s in specs], [s[1] for s in specs]
    assert len(set(tags)) == len(tags) and len(set(labels)) == len(labels)
    candidates, checks = {}, {}
    for tag in tags:
        base = Path('work/translation/en/script/stage30s_' + tag)
        rows = json.loads(base.with_name(base.name + '_merged.json').read_text(encoding='utf-8'))['rows']
        assert [r['id'] for r in rows] == list(range(376))
        assert all(isinstance(r.get('en'), str) and r['en'].strip() for r in rows)
        candidates[tag] = {r['id']: r for r in rows}
        checks[tag] = json.loads(base.with_name(base.name + '_checks.json').read_text(encoding='utf-8'))
    sh = gspread.service_account(filename=str(args.key)).open_by_key(args.spreadsheet_id)
    metadata = sh.fetch_sheet_metadata()
    props = {s['properties']['title']: s['properties'] for s in metadata['sheets']}
    assert TITLE in props and NTITLE in props
    main_p, notes_p = props[TITLE], props[NTITLE]
    ranges = []
    # Snapshot all tabs, including the user-owned Prompt tab, without modifying them.
    for title, prop in props.items():
        size = prop['gridProperties']
        assert size['rowCount'] * size['columnCount'] < 50000
        ranges.append(bounded_range(title, size['rowCount'], size['columnCount']))
    before = sh.fetch_sheet_metadata(params={'includeGridData': True, 'ranges': ranges})
    sheets = {s['properties']['title']: s for s in before['sheets']}
    main_grid, notes_grid = grid(sheets[TITLE]), grid(sheets[NTITLE])
    header = [value(c) for c in main_grid[0]]
    while header and not header[-1]:
        header.pop()
    assert header[:7] == ['#', 'Part', 'ID', 'Kind', 'Speaker (JP)', 'Japanese', 'Speaker (EN)']
    assert all(label in header for label in ['Best (model)', 'Reviewer comment'])
    assert header.index('Best (model)') >= 8, 'Expected existing candidate columns.'
    assert header[-2:] == ['Best (model)', 'Reviewer comment']
    assert not any(label in header for label in labels), 'Candidate already exists; inspect the outcome instead of inserting twice.'
    target = header.index('Best (model)')
    active = []
    for i, row in enumerate(main_grid[1:], 1):
        rid = value(at(main_grid, i, 2))
        if rid == '':
            assert not any(value(c) != '' for c in row), 'Unexpected nonempty row without ID'
            continue
        rid = int(rid)
        assert 0 <= rid < 376
        active.append((i, rid))
    assert len(active) == 382 and len({rid for _, rid in active}) == 376
    assert [i for i, _ in active] == list(range(1, 383))
    assert [value(c) for c in notes_grid[0][:3]] == ['ID', 'Model', 'Translator notes / uncertainties']
    last_note = max([i for i, row in enumerate(notes_grid) if any(value(c) != '' for c in row)])
    assert not any(value(at(notes_grid, i, 1)) in labels for i in range(1, len(notes_grid))), 'Candidate notes already exist.'
    new_notes = []
    note_counts = {}
    automated_note_counts = {}
    for tag, label in specs:
        entries = []
        for rid, row in candidates[tag].items():
            note = '; '.join(s for s in [row.get('notes', '')] + row.get('uncertain', []) if s)
            if note:
                entries.append([rid, label, note])
        new_notes.extend(entries)
        note_counts[tag] = len(entries)
        diagnostics = []
        for problem in checks[tag]['problems']:
            match = re.match(r'^(\d+): ', problem)
            if match:
                diagnostics.append([int(match.group(1)), label,
                                    'Automated check (not translator notes): ' + problem])
        new_notes.extend(diagnostics)
        automated_note_counts[tag] = len(diagnostics)
    msid, nsid = main_p['sheetId'], notes_p['sheetId']
    count, append_start = len(tags), last_note + 1
    body = [labels] + [[candidates[tag][rid]['en'] for tag in tags] for _, rid in active]
    requests = [
        {'insertDimension': {'range': {'sheetId': msid, 'dimension': 'COLUMNS', 'startIndex': target, 'endIndex': target + count}, 'inheritFromBefore': True}},
        copy_format(msid, 0, 383, target - 1, target, 0, 383, target, target + count),
        write_cells(msid, 0, target, body),
    ]
    required_notes = append_start + len(new_notes)
    if required_notes > notes_p['gridProperties']['rowCount']:
        requests.append({'appendDimension': {'sheetId': nsid, 'dimension': 'ROWS', 'length': required_notes - notes_p['gridProperties']['rowCount']}})
    if new_notes:
        requests.extend([
            copy_format(nsid, last_note, last_note + 1, 0, 3, append_start, required_notes, 0, 3),
            write_cells(nsid, append_start, 0, new_notes),
            {'repeatCell': {'range': rectangle(nsid, append_start, required_notes, 2, 3),
                             'cell': {'userEnteredFormat': {'wrapStrategy': 'WRAP', 'verticalAlignment': 'TOP'}},
                             'fields': 'userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment'}},
        ])
    assert all(len(request) == 1 for request in requests)
    summary = dict(title=metadata.get('properties', {}).get('title'), spreadsheet_id=args.spreadsheet_id,
                   sheet_id=msid, notes_sheet_id=nsid, models=dict(specs), start_column=target + 1,
                   occurrences=len(active), unique_rows=376, note_counts=note_counts,
                   automated_note_counts=automated_note_counts,
                   notes_appended=len(new_notes), request_count=len(requests),
                   content_problem_counts={tag: len(checks[tag]['problems']) for tag in tags},
                   reviewer_cells_populated=sum(value(at(main_grid, i, j)) != '' for i, _ in active
                                                for j in [target, header.index('Reviewer comment')]))
    print(json.dumps(summary, indent=1))
    print('Sample:', active[0][1], [candidates[tag][active[0][1]]['en'] for tag in tags])
    print('Plan preserves all existing tabs, candidate cells, and reviewer cells in place.')
    if not args.write:
        return
    prefix = Path('work/output/stage30s_google_' + '_'.join(tags))
    backup = prefix.with_name(prefix.name + '_before.json')
    assert not backup.exists(), 'Snapshot exists; inspect the previous outcome before another write.'
    save(backup, before)
    save(prefix.with_name(prefix.name + '_requests.json'), requests)
    sh.batch_update({'requests': requests})
    new_ranges = [bounded_range(TITLE, main_p['gridProperties']['rowCount'], main_p['gridProperties']['columnCount'] + count),
                  bounded_range(NTITLE, max(notes_p['gridProperties']['rowCount'], required_notes), notes_p['gridProperties']['columnCount'])]
    new_ranges.extend(bounded_range(title, prop['gridProperties']['rowCount'], prop['gridProperties']['columnCount'])
                      for title, prop in props.items() if title not in (TITLE, NTITLE))
    after = sh.fetch_sheet_metadata(params={'includeGridData': True, 'ranges': new_ranges})
    after_sheets = {s['properties']['title']: s for s in after['sheets']}
    assert set(after_sheets) == set(sheets), 'Unexpected tab added or removed.'
    for title in sheets:
        assert after_sheets[title]['properties']['sheetId'] == sheets[title]['properties']['sheetId']
        if title not in (TITLE, NTITLE):
            assert after_sheets[title] == sheets[title], 'Unrelated tab changed: ' + title
    ag, ng = grid(after_sheets[TITLE]), grid(after_sheets[NTITLE])
    assert [value(at(ag, 0, target + j)) for j in range(count)] == labels
    for i, rid in active:
        assert [value(at(ag, i, target + j)) for j in range(count)] == [candidates[tag][rid]['en'] for tag in tags]
    for i, row in enumerate(main_grid):
        for j, cell in enumerate(row):
            nj = j + (count if j >= target else 0)
            assert project(cell) == project(at(ag, i, nj)), 'Existing main cell changed at row {}, column {}'.format(i+1, j+1)
    for i, row in enumerate(notes_grid):
        for j, cell in enumerate(row):
            assert project(cell) == project(at(ng, i, j)), 'Existing note cell changed at row {}, column {}'.format(i+1, j+1)
    written_notes = [tuple(value(at(ng, i, j)) for j in range(3)) for i in range(1, len(ng)) if value(at(ng, i, 1)) in labels]
    assert sorted(written_notes) == sorted(tuple(row) for row in new_notes)
    for i in range(383):
        for j in range(count):
            assert at(ag, i, target + j).get('userEnteredFormat', {}) == at(main_grid, i, target - 1).get('userEnteredFormat', {})
    summary['verified'] = True
    summary['url'] = sh.url + '#gid=' + str(msid)
    save(prefix.with_name(prefix.name + '_result.json'), summary)
    print('Verified all new translations and notes, plus unchanged original cell values, styles, validation and cell notes.')
    print('URL:', summary['url'])


if __name__ == '__main__':
    main()
