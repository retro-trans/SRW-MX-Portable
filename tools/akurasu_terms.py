"""Download and parse the akurasu.net SRW MX wiki pages into a JP -> EN term list.

akurasu.net is the project's main source for terms (see AGENTS.md).

usage: python akurasu_terms.py <out dir> [--offline]
Writes <out dir>/akurasu/<page>.wiki (raw wikitext) and <out dir>/akurasu_terms.json:
  [{"jp", "key", "en", "en_alt", "page", "section", "url"}]
  key    = normalized Japanese used for matching (see norm())
  en_alt = name given in parentheses, e.g. "Hot Blood (Valor)" -> en "Hot Blood", en_alt "Valor"
"""
import json, os, re, subprocess, sys, unicodedata, urllib.parse

PAGES = ['Character List', 'Mech List', 'Spirit Commands', 'Pilot Abilities', 'Mech Abilities',
         'Parts', 'Series']
API = 'https://akurasu.net/wiki/api.php?action=parse&prop=wikitext&format=json&page='
URL = 'https://akurasu.net/wiki/'
JP = re.compile(r'[぀-ヿ一-鿿]')


def norm(s):
    """NFKC, drop spaces / middle dots / brackets so game and wiki spellings line up."""
    s = unicodedata.normalize('NFKC', s or '')
    return re.sub(r'[\s・･·=＝()（）\[\]<>＜＞〈〉]', '', s).replace('：', ':')


def clean(cell):
    cell = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', cell)       # [[link|text]] -> text
    cell = re.sub(r"<[^>]+>|'''?|&nbsp;", ' ', cell)
    return re.sub(r'\s+', ' ', cell).strip()


def fetch(page, outdir, offline):
    path = os.path.join(outdir, 'akurasu', page.replace(' ', '_') + '.wiki')
    if not offline:
        raw = subprocess.run(['curl', '-s', '-A', 'Mozilla/5.0',
                              API + urllib.parse.quote('Super Robot Wars/MX/' + page)],
                             capture_output=True, check=True).stdout
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8').write(json.loads(raw)['parse']['wikitext']['*'])
    return open(path, encoding='utf-8').read()


def parse(page, text):
    out, section, header = [], '', None
    rows, cur = [], None
    for line in text.splitlines():
        h = re.match(r'^(=+)\s*(.*?)\s*\1\s*$', line)
        if h:
            section = clean(h.group(2))
            continue
        if line.startswith('{|') or line.startswith('|}') or line.startswith('|-'):
            if cur:
                rows.append((section, cur))
            cur = None
            if line.startswith('{|'):
                header = None
            continue
        if line.startswith('!'):
            header = [clean(c).lower() for c in re.split(r'!!|\|\|', line[1:])]
            continue
        if line.startswith('|'):
            cells = [clean(c) for c in re.split(r'\|\|', line[1:])]
            cur = (cur or []) + cells
            if header:
                rows.append((section, cur, header))
                cur = None
    for r in rows:
        if len(r) != 3:
            continue
        section, cells, header = r
        cells = cells + [''] * (len(header) - len(cells))
        ji = next((i for i, h in enumerate(header) if 'japanese' in h), None)
        ei = next((i for i, h in enumerate(header) if h in ('english', 'english name', 'skill', 'name')), None)
        if ji is None or ei is None or ji >= len(cells) or ei >= len(cells):
            continue
        jp, en = cells[ji], cells[ei]
        if not JP.search(jp) and not re.search(r'[A-Za-z0-9]', jp):
            continue
        if not en or JP.search(en):
            continue
        m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', en)
        alt = None
        if m and page == 'Spirit Commands':
            en, alt = m.group(1), m.group(2)
        out.append({'jp': jp, 'key': norm(jp), 'en': en, 'en_alt': alt, 'page': page,
                    'section': section, 'url': URL + 'Super_Robot_Wars/MX/' + page.replace(' ', '_')})
    return out


def main(outdir, offline):
    terms = []
    for p in PAGES:
        t = parse(p, fetch(p, outdir, offline))
        print(f'{p:16s} {len(t)}')
        terms += t
    json.dump(terms, open(os.path.join(outdir, 'akurasu_terms.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('total', len(terms))


if __name__ == '__main__':
    main(sys.argv[1], '--offline' in sys.argv)
