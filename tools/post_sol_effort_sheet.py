"""Preview/post the four Sol effort candidates into the user's empty review tab.

Preserves the original tab ID, unrelated tabs and all cells outside the authored
rectangle. Refuses to overwrite existing content or replay an attempted write.
Run without --write first and inspect the sample/plan.
"""
import argparse
import json
from pathlib import Path
import re

import gspread
import post_sheet
from update_review_sheet import bounded_range, grid, at, project, rectangle, save, value, write_cells

SID = '16nyBAPVH1OSQdYo8qMxxqmS5YtceGeK45DZt9prjuWQ'
BASE = Path('work/translation/en/script/stage30s')
SPECS = [('sol61low3', 'Sol 6.1 Low'), ('sol61med3', 'Sol 6.1 Medium'),
         ('sol61high3', 'Sol 6.1 High'), ('sol61xhigh3', 'Sol 6.1 XHigh')]
TITLE = 'Stage 30 Space'
NTITLE = TITLE + ' notes'
PREFIX = Path('work/output/stage30s_google_sol_efforts')


def get_snapshot(sh, metadata):
    ranges = []
    for sheet in metadata['sheets']:
        p = sheet['properties']
        size = p['gridProperties']
        assert size['rowCount'] * size['columnCount'] < 50000
        ranges.append(bounded_range(p['title'], size['rowCount'], size['columnCount']))
    return sh.fetch_sheet_metadata(params={'includeGridData': True, 'ranges': ranges})


def formatted(sid, data, widths):
    nr, nc = len(data), len(data[0])
    content = write_cells(sid, 0, 0, data)
    for row, raw in zip(content['updateCells']['rows'], data):
        for c, v in enumerate(raw):
            if v == '':
                row['values'][c] = {}  # A native blank, rather than an empty shared string.
    requests = [content,
                {'repeatCell': {'range': rectangle(sid, 0, nr, 0, nc),
                                'cell': {'userEnteredFormat': {'wrapStrategy': 'WRAP',
                                                              'verticalAlignment': 'TOP'}},
                                'fields': 'userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment'}},
                {'repeatCell': {'range': rectangle(sid, 0, 1, 0, nc),
                                'cell': {'userEnteredFormat': {'backgroundColor': {'red': .93, 'green': .93, 'blue': .93},
                                                              'textFormat': {'bold': True}}},
                                'fields': 'userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.bold'}},
                {'updateSheetProperties': {'properties': {'sheetId': sid, 'gridProperties': {
                                             'frozenRowCount': 1, 'frozenColumnCount': 3 if nc == 13 else 0}},
                                           'fields': 'gridProperties.frozenRowCount,gridProperties.frozenColumnCount'}},
                {'setBasicFilter': {'filter': {'range': rectangle(sid, 0, nr, 0, nc)}}}]
    for c, width in enumerate(widths):
        requests.append({'updateDimensionProperties': {
            'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': c, 'endIndex': c + 1},
            'properties': {'pixelSize': width}, 'fields': 'pixelSize'}})
    requests.append({'autoResizeDimensions': {'dimensions': {'sheetId': sid, 'dimension': 'ROWS',
                                                             'startIndex': 0, 'endIndex': nr}}})
    return requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('key', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    names = dict(SPECS)
    table, notes, unique = post_sheet.build(str(BASE), list(names), names)
    assert unique == 376 and len(table) == 383 and len(table[0]) == 13
    assert all(len(r) == 13 and all(r[7:11]) for r in table[1:])
    problems, note_counts = {}, {}
    for tag, label in SPECS:
        check = json.loads(BASE.with_name(BASE.name + '_' + tag + '_checks.json').read_text(encoding='utf-8'))
        assert check['translated_rows'] == check['expected_rows'] == 376
        problems[tag] = check['problems']
        note_counts[tag] = sum(row[1] == label for row in notes[1:])
        for problem in check['problems']:
            match = re.match(r'^(\d+): ', problem)
            if match:
                notes.append([int(match.group(1)), label, 'Automated check (not translator notes): ' + problem])
    sh = gspread.service_account(filename=str(args.key)).open_by_key(SID)
    meta = sh.fetch_sheet_metadata()
    before = get_snapshot(sh, meta)
    sheets = {s['properties']['sheetId']: s for s in before['sheets']}
    assert 0 in sheets, 'Expected the original user-linked tab ID 0.'
    original = sheets[0]
    p = original['properties']
    assert p['title'] == 'Sheet1', 'Inspect any changed destination before posting.'
    assert TITLE not in {s['properties']['title'] for s in sheets.values()}
    assert NTITLE not in {s['properties']['title'] for s in sheets.values()}
    original_grid = grid(original)
    assert not any(c.get('userEnteredValue') or c.get('note') or c.get('chipRuns') or c.get('dataValidation')
                   for row in original_grid for c in row), 'Destination is no longer empty.'
    assert not original.get('merges') and not original.get('tables') and not original.get('basicFilter')
    nsid = 2000000103
    assert nsid not in sheets
    requests = [
        {'updateSheetProperties': {'properties': {'sheetId': 0, 'title': TITLE}, 'fields': 'title'}},
        {'addSheet': {'properties': {'sheetId': nsid, 'title': NTITLE,
                                    'gridProperties': {'rowCount': max(1000, len(notes) + 5), 'columnCount': 3}}}},
    ]
    assert p['gridProperties']['rowCount'] >= len(table) and p['gridProperties']['columnCount'] >= 13
    requests.extend(formatted(0, table, [55, 180, 55, 85, 135, 325, 135, 325, 325, 325, 325, 175, 325]))
    requests.extend(formatted(nsid, notes, [65, 170, 850]))
    requests.append({'setDataValidation': {'range': rectangle(0, 1, len(table), 11, 12),
        'rule': {'condition': {'type': 'ONE_OF_LIST', 'values': [{'userEnteredValue': name} for name in names.values()]},
                 'strict': True, 'showCustomUi': True}}})
    requests.append({'updateCells': {'range': rectangle(0, 0, 1, 7, 11),
        'rows': [{'values': [{'note': 'Fresh Stage 30 translation. Model: gpt-6.1-sol. Reasoning effort: ' + effort +
                             '. Same rules, source, glossary and event context; five fresh slices.'}
                            for effort in ['low', 'medium', 'high', 'xhigh']]}], 'fields': 'note'}})
    for request in requests:
        assert isinstance(request, dict) and len(request) == 1
        if 'updateCells' in request:
            write = request['updateCells']
            area = write['range']
            assert area['endRowIndex'] - area['startRowIndex'] == len(write['rows'])
            assert all(len(row['values']) == area['endColumnIndex'] - area['startColumnIndex']
                       for row in write['rows'])
    summary = dict(title=meta['properties']['title'], spreadsheet_id=SID, sheet_id=0, notes_sheet_id=nsid,
                   models=names, occurrences=382, unique_rows=376, notes=len(notes)-1,
                   translator_note_counts=note_counts, content_problem_counts={k: len(v) for k, v in problems.items()},
                   requests=len(requests), changed_range=TITLE + '!A1:M383')
    print(json.dumps(summary, indent=2))
    print('Sample:', table[1][7:11])
    print('Plan: populate original empty tab id 0, add notes tab, retain unrelated tabs and unused cells.')
    if not args.write:
        return
    backup = PREFIX.with_name(PREFIX.name + '_before.json')
    assert not backup.exists(), 'An attempted write already exists; inspect its outcome instead of replaying.'
    save(backup, before)
    save(PREFIX.with_name(PREFIX.name + '_requests.json'), requests)
    sh.batch_update({'requests': requests})
    after = get_snapshot(sh, sh.fetch_sheet_metadata())
    updated = {s['properties']['sheetId']: s for s in after['sheets']}
    assert set(updated) == set(sheets) | {nsid}
    for sid in sheets:
        if sid != 0:
            assert sheets[sid] == updated[sid], 'Unrelated tab changed.'
    main_grid, notes_grid = grid(updated[0]), grid(updated[nsid])
    for sid, expected, actual in [(0, table, main_grid), (nsid, notes, notes_grid)]:
        for r, row in enumerate(expected):
            assert [value(at(actual, r, c)) for c in range(len(row))] == row, (sid, r)
    for r, row in enumerate(original_grid):
        for c, cell in enumerate(row):
            if r >= len(table) or c >= 13:
                assert project(cell) == project(at(main_grid, r, c)), 'Unused original cell changed.'
    for r in range(1, len(table)):
        assert at(main_grid, r, 11)['dataValidation']['condition']['type'] == 'ONE_OF_LIST'
        assert [x['userEnteredValue'] for x in at(main_grid, r, 11)['dataValidation']['condition']['values']] == list(names.values())
    summary['verified'] = True
    summary['url'] = sh.url + '#gid=0'
    save(PREFIX.with_name(PREFIX.name + '_after.json'), after)
    save(PREFIX.with_name(PREFIX.name + '_result.json'), summary)
    print('Verified all source/context cells, 1,528 candidate occurrences, notes, reviewer controls and preserved cells.')
    print('URL:', summary['url'])


if __name__ == '__main__':
    main()
