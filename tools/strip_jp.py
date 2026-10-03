"""Write commit-safe copies (*.en.json) of translation working files, without the Japanese script.

Removes the fields that hold source text (jp, body_jp, jp_rows, summary_jp, title_jp) and masks
Japanese quoted inside notes. Short Japanese names (speaker_jp, name_jp) are kept: names and UI terms
are allowed in the repository, script lines are not (AGENTS.md).

usage: python strip_jp.py [project root]
"""
import glob, json, os, re, sys

DROP = {'jp', 'body_jp', 'jp_rows', 'summary_jp', 'title_jp'}
RUN = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef\u3000-\u303f]{7,}')
KEEP_JP = {'speaker_jp', 'name_jp'}


def clean(x, key=None):
    if isinstance(x, dict):
        return {k: clean(v, k) for k, v in x.items() if k not in DROP}
    if isinstance(x, list):
        return [clean(v, key) for v in x]
    if isinstance(x, str) and key not in KEEP_JP:
        return RUN.sub('[jp]', x)
    return x


def main(root='.'):
    pats = ['work/translation/*/library*.json', 'work/translation/*/script/*.json']
    n = 0
    for pat in pats:
        for fn in glob.glob(os.path.join(root, pat)):
            if fn.endswith('.en.json'):
                continue
            d = clean(json.load(open(fn, encoding='utf-8')))
            json.dump(d, open(fn[:-5] + '.en.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            n += 1
    print(n, 'commit-safe copies written')


if __name__ == '__main__':
    main(*sys.argv[1:2])
