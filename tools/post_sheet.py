"""Post a multi-model translation comparison to a Google Sheet for human review.

usage: python post_sheet.py <service-account.json | csv> <sheet id | out.csv> <scene base> <tab title>
                            model[=Display name] [model[=Display name] ...]
  scene base  e.g. work/translation/en/script/stage30s   (reads <base>.json,
              <base>_<model>_slice_*.json and, if present, <base>_order.json from play_order.py)
Writes two tabs:
  <tab title>         one row per line in play order (a line spoken twice appears twice):
                      #, part, ID, Japanese, then one English column per model (named), and empty
                      reviewer columns (Best / Comment)
  <tab title> notes   the translators' uncertainty notes per line and model
Existing tabs with these titles are replaced; reviewer input already typed in the Best / Comment
columns is carried over by line ID. Other tabs are not touched.
"""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load(base, models):
    rows = json.load(open(base + '.json', encoding='utf-8'))['rows']
    out = {}
    for m in models:
        got = {}
        for fn in sorted(glob.glob(f'{base}_{m}_slice_*.json')):
            for r in json.load(open(fn, encoding='utf-8'))['rows']:
                got[r['id']] = r
        if not got:
            raise SystemExit(f'no translation files found for model "{m}" ({base}_{m}_slice_*.json)')
        out[m] = got
    return rows, out


def build(base, models, names):
    rows, tr = load(base, models)
    byid = {r['id']: r for r in rows}
    opath = base + '_order.json'
    order = json.load(open(opath)) if os.path.exists(opath) else \
        [{'part': r['uses'][0].split(':')[0], 'id': r['id'], 'repeat': False} for r in rows]
    head = ['#', 'Part', 'ID', 'Kind', 'Speaker (JP)', 'Japanese', 'Speaker (EN)'] + \
           [names[m] for m in models] + ['Best (model)', 'Reviewer comment']
    table = [head]
    for n, x in enumerate(order, 1):
        r = byid[x['id']]
        spk = r.get('speaker_en') or next((tr[m][r['id']].get('speaker_en') for m in models
                                           if tr[m].get(r['id'], {}).get('speaker_en')), '')
        part = x['part'] + (' (repeated line)' if x.get('repeat') else '')
        table.append([n, part, r['id'], r['kind'], r['speaker_jp'], r['body_jp'].replace('@', '\n'), spk] +
                     [(tr[m].get(r['id']) or {}).get('en') or '' for m in models] + ['', ''])
    notes = [['ID', 'Model', 'Translator notes / uncertainties']]
    for r in rows:
        for m in models:
            t = tr[m].get(r['id']) or {}
            unc = '; '.join(x for x in [t.get('notes') or ''] + list(t.get('uncertain') or []) if x)
            if unc:
                notes.append([r['id'], names[m], unc])
    return table, notes, len(rows)


def main(key, sheet_id, base, title, *specs):
    models = [s.split('=')[0] for s in specs]
    names = {s.split('=')[0]: (s.split('=', 1)[1] if '=' in s else s.split('=')[0]) for s in specs}
    table, notes, nrows = build(base, models, names)
    ncol = len(table[0])
    if key == 'csv':
        import csv
        with open(sheet_id, 'w', encoding='utf-8-sig', newline='') as f:
            csv.writer(f).writerows(table)
        print(f'wrote {len(table) - 1} lines ({nrows} unique) to {sheet_id}')
        return
    import gspread
    gc = gspread.service_account(filename=key)
    sh = gc.open_by_key(sheet_id)

    # carry over anything the reviewer already typed (matched by line ID)
    kept = 0
    try:
        old = sh.worksheet(title).get_all_values()
        h = old[0]
        idc = h.index('ID')
        bc = next(i for i, x in enumerate(h) if x.startswith('Best'))
        cc = h.index('Reviewer comment')
        prev = {}
        for row in old[1:]:
            row = row + [''] * (len(h) - len(row))
            if row[bc].strip() or row[cc].strip():
                prev[row[idc]] = (row[bc].strip(), row[cc])
        for row in table[1:]:
            if str(row[2]) in prev:
                row[-2], row[-1] = prev[str(row[2])]
                kept += 1
    except (gspread.WorksheetNotFound, ValueError, StopIteration, IndexError):
        pass

    def put(name, data):
        try:
            sh.del_worksheet(sh.worksheet(name))
        except gspread.WorksheetNotFound:
            pass
        ws = sh.add_worksheet(title=name, rows=len(data) + 5, cols=max(len(x) for x in data) + 1)
        ws.update(data, 'A1', value_input_option='RAW')
        ws.freeze(rows=1)
        return ws

    ws = put(title, table)
    last = gspread.utils.rowcol_to_a1(len(table), ncol)
    ws.format(f'A1:{gspread.utils.rowcol_to_a1(1, ncol)}', {'textFormat': {'bold': True}})
    ws.format(f'F2:{last}', {'wrapStrategy': 'WRAP', 'verticalAlignment': 'TOP'})
    put(title + ' notes', notes)
    try:                                                    # the blind key tab of the first layout
        sh.del_worksheet(sh.worksheet(title + ' key'))
    except gspread.WorksheetNotFound:
        pass
    print(f'posted {len(table) - 1} lines ({nrows} unique) to "{title}"; reviewer cells carried over: {kept}')
    print('url:', f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={ws.id}')


if __name__ == '__main__':
    main(*sys.argv[1:])
