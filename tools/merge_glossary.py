"""Merge per-group glossaries and library translations, reconcile names, run checks.

usage: python merge_glossary.py [project root] [--apply]
Reads   work/glossary/glossary_<G>.json, work/translation/en/library_<G>.json,
        work/glossary/decisions.json (manual picks: {"<section>": {"<jp>": "<en>"}})
Writes  work/glossary/glossary.json            merged, one English form per Japanese key
        work/glossary/name_fixes.json          variant -> canonical replacements for library text
        work/translation/en/library.json       merged library (name fixes applied only with --apply)
        work/translation/en/library_check.md   problems found + dry-run of the name fixes

Conflict rule: decisions.json first; otherwise the group that owns the entry's series wins
(group ownership = make_batches.GROUPS); otherwise the first group seen wins and it is logged.
"""
import collections, difflib, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from make_batches import GROUPS
from akurasu_terms import norm

SECTIONS = ('series', 'characters', 'units', 'weapons', 'terms')
OWNER = {s: g for g, ss in GROUPS.items() for s in ss}


SPLIT_BY_READING = set()   # character full names shared by different people (公安 A/B), filled in main()


def key(sec, e):
    if sec == 'characters':
        if e.get('jp_full') in SPLIT_BY_READING:
            return e['jp_full'] + '|' + (e.get('reading') or '')
        return e.get('jp_full')
    return e.get('jp')


def jp_of(k):
    return k.split('|')[0]


def en(sec, e):
    return e.get('en_full') if sec == 'characters' else e.get('en')


def owns(e):
    return OWNER.get(e.get('series')) == e['_group']


def fixable(variant, canon, strong=False):
    """Only rewrite proper-noun variants. Containment pairs ('Melee' / 'Melee Attack') are skipped
    unless the canonical form comes from akurasu or a manual decision (strong)."""
    if not variant or not canon or variant == canon:
        return False
    if variant.lower() == canon.lower():
        return variant[:1].isupper() and canon[:1].isupper()   # e.g. 'Maffu' vs 'MAFFU'
    if not strong and (variant.lower() in canon.lower() or canon.lower() in variant.lower()):
        return False
    return len(variant) >= 4 and variant[:1].isupper()


def retoken(old_full, new_full, old_short):
    """Carry a short name over to a renamed full name: 'Ulube' in 'Ulube Ishikawa' -> 'Urube'."""
    if not old_short or not old_full:
        return old_short, []
    if old_short == old_full:
        return new_full, []
    ot, nt = old_full.split(), new_full.split()
    pairs = [(a, b) for a, b in zip(ot, nt) if a != b] if len(ot) == len(nt) else []
    pairs = [(a, b) for a, b in pairs if b not in ot and a not in nt]   # reordered, not renamed
    pairs = [(a, b) for a, b in pairs if difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= 0.6]
    if old_short in ot:
        i = ot.index(old_short)
        if len(ot) == len(nt):
            new = nt[i]
        elif i == len(ot) - 1:
            new = nt[-1]                 # 'Earth Attack Captain Blaki' -> 'Commander Blacky'
        else:
            new = old_short
        if new in ot and new != old_short:   # tokens were reordered, the person was not renamed
            new = old_short
        return new, pairs
    return old_short, pairs


def main(root, apply):
    gdir = os.path.join(root, 'work', 'glossary')
    tdir = os.path.join(root, 'work', 'translation', 'en')
    src = os.path.join(root, 'work', 'source')
    problems = collections.defaultdict(list)
    dpath = os.path.join(gdir, 'decisions.json')
    decisions = json.load(open(dpath, encoding='utf-8')) if os.path.exists(dpath) else {}

    readings = collections.defaultdict(set)
    for path in sorted(glob.glob(os.path.join(gdir, 'glossary_?.json'))):
        for e in json.load(open(path, encoding='utf-8')).get('characters', []):
            if e.get('reading'):
                readings[e.get('jp_full')].add(e['reading'])
    SPLIT_BY_READING.update(k for k, v in readings.items() if len(v) > 1)

    cands = {s: collections.defaultdict(list) for s in SECTIONS}
    for path in sorted(glob.glob(os.path.join(gdir, 'glossary_?.json'))):
        g = json.load(open(path, encoding='utf-8'))
        grp = g.get('group') or os.path.basename(path)[9]
        for sec in SECTIONS:
            for e in g.get(sec, []):
                k = key(sec, e)
                if not k or jp_of(k) == '無し':
                    continue
                if sec == 'characters' and not e.get('sources'):
                    problems['character without source'].append(f'{grp}: {k}')
                cands[sec][k].append(dict(e, _group=grp))

    # akurasu.net = main source for terms (AGENTS.md)
    ak, akurl, akterm = collections.defaultdict(set), {}, {}
    apath = os.path.join(gdir, 'akurasu_terms.json')
    alpath = os.path.join(gdir, 'akurasu_aliases.json')
    aliases = json.load(open(alpath, encoding='utf-8'))['aliases'] if os.path.exists(alpath) else {}
    for t in (json.load(open(apath, encoding='utf-8')) if os.path.exists(apath) else []):
        kk = norm(aliases.get(t['jp'], t['jp']))
        ak[kk].add(t['en'])
        akurl[kk] = t['url']
        akterm[kk] = t
    used_ak = set()
    suffix = re.compile(r'^(.+?)(Lv|\+|\d)$')    # game 'X Lv' / 'X+' / 'X (3)' -> akurasu 'X'

    def ak_lookup(j):
        """-> (english, key) | (None, None); logs ambiguous keys."""
        n = norm(j)
        if n in ak:
            s = ak[n]
            if len(s) == 1:
                return next(iter(s)), n
            problems['akurasu has several names for one Japanese key (skipped)'].append(f'{j}: {sorted(s)}')
            return None, n
        m = suffix.match(n)
        if m and m.group(1) in ak and len(ak[m.group(1)]) == 1:
            tail = {'Lv': ' Lv', '+': '+'}.get(m.group(2), f' ({m.group(2)})')
            return next(iter(ak[m.group(1)])) + tail, m.group(1)
        return None, None

    merged, fixes, quoted = {s: [] for s in SECTIONS}, {}, {}
    names = decisions.get('names', {})
    no_fix = set(decisions.get('no_text_fix', []))
    canon_by_jp = {}                        # first section wins: characters > units > weapons > terms

    def add_fix(variant, canon, k, strong, system):
        if k in no_fix or not fixable(variant, canon, strong):
            return
        table = quoted if system else fixes      # system terms are only rewritten inside "quotes"
        if table.get(variant, canon) != canon:
            problems['variant maps to two canonical names'].append(
                f'{variant!r}: {table[variant]!r} vs {canon!r} ({k})')
        table.setdefault(variant, canon)

    for sec in ('characters', 'units', 'weapons', 'terms', 'series'):
        for k, es in cands[sec].items():
            forms = []
            for e in es:
                if en(sec, e) not in forms:
                    forms.append(en(sec, e))
            # base pick: owner group, else first seen
            owners = [e for e in es if owns(e)]
            base, how = (owners[0], f'owner {owners[0]["_group"]}') if owners else (es[0], 'first seen')
            # akurasu lookup (characters also by short name)
            ak_en, ak_key = None, None
            for j in [jp_of(k)] + ([e.get('jp_short') for e in es] if sec == 'characters' else []):
                if j:
                    ak_en, ak_key = ak_lookup(j)
                    if ak_key:
                        used_ak.add(ak_key)
                    if ak_en:
                        break
            want, how2 = None, ''
            if jp_of(k) in names:
                want, how2 = names[jp_of(k)], 'decision'
                if ak_en and ak_en != want:
                    problems['decision overrides akurasu'].append(f'{k}: akurasu {ak_en!r} -> {want!r}')
            elif ak_en:
                want, how2 = ak_en, 'akurasu'
            elif sec != 'characters' and jp_of(k) in canon_by_jp:
                want, how2 = canon_by_jp[jp_of(k)], 'same name in a higher section'
            pick = dict(base)
            if want:
                how = how2
                if sec == 'characters':
                    old_full = pick.get('en_full')
                    pick['en_full'] = want
                    pick['en_short'], pairs = retoken(old_full, want, pick.get('en_short'))
                    for a, b in pairs:
                        add_fix(a, b, k, True, False)
                    if pick['en_short'] not in forms and pick['en_short'] != base.get('en_short'):
                        add_fix(base.get('en_short'), pick['en_short'], k, True, False)
                else:
                    pick['en'] = want
                if how2 == 'akurasu':
                    pick['sources'] = [akurl[ak_key]] + [u for u in pick.get('sources') or []
                                                          if u != akurl[ak_key]]
                    pick['source_main'] = 'akurasu'
                if want not in forms:
                    forms.append(want)
            elif len(forms) > 1 and not owners:
                problems['conflict resolved by first-seen (needs decision)'].append(
                    f'{sec} {k}: {forms} -> {en(sec, pick)!r}')
            canon = en(sec, pick)
            canon_by_jp.setdefault(jp_of(k), canon)
            if len(forms) > 1:
                pick['variants'] = [f for f in forms if f != canon]
                problems['conflicts resolved'].append(f'{sec} {k}: {forms} -> {canon!r} ({how})')
                system = sec == 'terms' and (pick.get('category') == 'system' or pick.get('series') == 'system')
                for f in forms:
                    add_fix(f, canon, k, how in ('akurasu', 'decision'), system)
            merged[sec].append(pick)
        merged[sec].sort(key=lambda e: (e.get('series') or '', key(sec, e)))
    for v, c in decisions.get('text_fixes', {}).items():   # manual variant -> canonical
        fixes[v] = c

    # akurasu terms no glossary entry matched (e.g. parts) become new terms
    category = {'Parts': 'system', 'Pilot Abilities': 'system', 'Mech Abilities': 'system',
                'Spirit Commands': 'system'}
    for kk, t in akterm.items():
        if kk in used_ak or len(ak[kk]) != 1:
            continue
        if t['page'] in category:
            merged['terms'].append({'jp': aliases.get(t['jp'], t['jp']), 'en': t['en'],
                                    'category': category[t['page']], 'series': 'system',
                                    'sources': [t['url']], 'source_main': 'akurasu',
                                    'notes': f'added from akurasu {t["page"]}', '_group': 'akurasu'})
        else:
            problems['akurasu term not in game glossary (not added)'].append(
                f'{t["page"]}: {t["jp"]} = {t["en"]}')

    # name fixes (library text: dry run unless --apply; glossary: always)
    word = lambda s: r'(?<![A-Za-z])' + re.escape(s) + r'(?![A-Za-z])'
    pats = [(re.compile(word(v)), c, re.compile(word(c))) for v, c in fixes.items()]
    # One pass, longest match first. Canonical names map to themselves so an already-correct
    # name is consumed whole and never partly rewritten, and a replacement is never re-replaced
    # ('Vigor'->'Guts' must not then become 'Super Guts'). Where a string is both a canonical
    # name and another entry's variant, the variant mapping wins (the text predates the merge).
    table = {c: c for c in fixes.values()}
    table.update(fixes)
    qtable = {f'"{c}"': f'"{c}"' for c in quoted.values()}
    qtable.update({f'"{v}"': f'"{c}"' for v, c in quoted.items()})
    alts = sorted(table, key=len, reverse=True)
    qalts = sorted(qtable, key=len, reverse=True)
    rx = re.compile('|'.join(word(a) for a in alts)) if alts else None
    qrx = re.compile('|'.join(re.escape(a) for a in qalts)) if qalts else None
    del pats

    def rewrite(txt, log):
        def sub(tab):
            def f(m):
                c = tab[m.group(0)]
                if c != m.group(0):
                    log.append(f'{m.group(0)!r}->{c!r}')
                return c
            return f
        if qrx:
            txt = qrx.sub(sub(qtable), txt)
        if rx:
            txt = rx.sub(sub(table), txt)
        return txt

    # derived glossary names (e.g. 量産型グレート（２）) follow their renamed base names
    for sec in ('units', 'weapons', 'terms'):
        for e in merged[sec]:
            if e.get('source_main') or e.get('category') == 'system' or not e.get('en') \
                    or e.get('jp') in names:
                continue
            log = []
            new = rewrite(e['en'], log)
            if new != e['en']:
                problems['glossary entries renamed by name fixes'].append(f'{sec} {e["jp"]}: {e["en"]!r} -> {new!r}')
                e.setdefault('variants', []).append(e['en'])
                e['en'] = new
    json.dump(merged, open(os.path.join(gdir, 'glossary.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump({'names': fixes, 'quoted_system_terms': quoted},
              open(os.path.join(gdir, 'name_fixes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # library
    lu = json.load(open(os.path.join(src, 'library_units.json'), encoding='utf-8'))
    lp = json.load(open(os.path.join(src, 'library_pilots.json'), encoding='utf-8'))
    want = {'units': {e['entry'] for e in lu if not e['dummy']},
            'pilots': {e['entry'] for e in lp if not e['dummy']}}
    lib = {'units': {}, 'pilots': {}}
    for path in sorted(glob.glob(os.path.join(tdir, 'library_?.json'))):
        t = json.load(open(path, encoding='utf-8'))
        for kind in ('units', 'pilots'):
            for e in t.get(kind, []):
                if e['entry'] in lib[kind]:
                    problems['duplicate library entry'].append(f'{kind} {e["entry"]}')
                lib[kind][e['entry']] = dict(e, _group=t.get('group'))

    changes = []
    for kind in ('units', 'pilots'):
        for i, e in sorted(lib[kind].items()):
            for fld in ('name_en', 'en'):
                txt = e.get(fld)
                if not txt:
                    continue
                log = []
                new = rewrite(txt, log)
                if new != txt:
                    changes.append(f'{kind} {i} {fld}: ' + '; '.join(log))
                    if apply:
                        e[fld] = new

    for kind in ('units', 'pilots'):
        missing = sorted(want[kind] - set(lib[kind]))
        if missing:
            problems[f'library {kind} missing'].append(str(missing))
        for i, e in sorted(lib[kind].items()):
            txt = e.get('en')
            if not txt:
                problems['untranslated entry'].append(f'{kind} {i} {e.get("name_jp")}')
                continue
            bad = re.sub(r'#[男女]愛称', '', txt + (e.get('name_en') or ''))
            bad = sorted({c for c in bad if ord(c) > 0x7E or ord(c) < 0x20})
            if bad:
                problems['non-ASCII characters'].append(f'{kind} {i}: {"".join(bad)!r}')

    # name consistency: a glossary name (>= 3 chars) in the Japanese -> one of its English forms in the English
    names = []
    for c in merged['characters']:
        forms = {c.get('en_full'), c.get('en_short'), *(c.get('nicknames') or [])} - {None, ''}
        for jp in {c.get('jp_full'), c.get('jp_short')} - {None, ''}:
            if len(jp) >= 3:
                names.append((jp, forms))
    for sec in ('units', 'terms'):
        for e in merged[sec]:
            if e.get('jp') and e.get('en') and len(e['jp']) >= 3:
                names.append((e['jp'], {e['en']}))
    names.sort(key=lambda x: -len(x[0]))
    for kind in ('units', 'pilots'):
        for i, e in sorted(lib[kind].items()):
            if not e.get('en'):
                continue
            jp, eng = e.get('jp') or '', (e['en'] + ' ' + (e.get('name_en') or '')).lower()
            for n, forms in names:
                if n in jp:
                    words = [w for f in forms for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", f)]
                    if words and not any(w.lower() in eng for w in words):
                        problems['glossary name not found in translation'].append(
                            f'{kind} {i} ({e.get("name_jp")}): {n} -> {sorted(forms)}')
                    jp = jp.replace(n, '')

    json.dump(lib, open(os.path.join(tdir, 'library.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(tdir, 'library_check.md'), 'w', encoding='utf-8') as f:
        f.write('# Library / glossary check\n\n')
        for s in SECTIONS:
            f.write(f'- glossary {s}: {len(merged[s])}\n')
        for kind in ('units', 'pilots'):
            f.write(f'- library {kind} translated: '
                    f'{sum(1 for e in lib[kind].values() if e.get("en"))}/{len(want[kind])}\n')
        f.write(f'- name fixes: {len(fixes)} variants, {len(changes)} fields '
                f'{"APPLIED" if apply else "would change (dry run)"}\n\n')
        f.write(f'## name fixes ({len(changes)})\n\n' + ''.join(f'- {c}\n' for c in changes) + '\n')
        for k, v in problems.items():
            f.write(f'## {k} ({len(v)})\n\n' + ''.join(f'- {x}\n' for x in v) + '\n')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--apply']
    main(args[0] if args else '.', '--apply' in sys.argv)
