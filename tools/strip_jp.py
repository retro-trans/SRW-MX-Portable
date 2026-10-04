"""Write commit-safe copies (*.en.json) of translation working files, without the Japanese script.

Removes source-text fields, including context-override expectations, and masks
Japanese excerpts inside notes regardless of length. Short Japanese names (speaker_jp, name_jp) are kept: names and UI terms
are allowed in the repository, script lines are not (AGENTS.md).

usage: python strip_jp.py [project root]
"""
import glob, json, os, re, sys

DROP = {'jp', 'body_jp', 'jp_rows', 'summary_jp', 'title_jp', 'expected_jp'}
RUN = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef\u3000-\u303f]{7,}')
KEEP_JP = {'speaker_jp', 'name_jp'}
# Short source utterances can appear in review annotations too. Public notes
# retain their English explanation; original annotations remain in local files.
ANNOTATIONS = {'notes', 'note', 'uncertain', 'reason', 'context', 'decisions',
               'source_flags', 'final_flags'}
SHORT_RUN = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef\u3000-\u303f]+')
REFERENCE = re.compile(r'(https?://[^\s<>]+|#[\u3040-\u30ff\u4e00-\u9fff]+)')


def clean(x, key=None):
    if isinstance(x, dict):
        return {k: clean(v, k) for k, v in x.items() if k not in DROP}
    if isinstance(x, list):
        return [clean(v, key) for v in x]
    if isinstance(x, str) and key not in KEEP_JP:
        if key in ANNOTATIONS:
            # Preserve provenance links and literal runtime placeholders.
            return ''.join(part if i % 2 else SHORT_RUN.sub('[jp]', part)
                           for i, part in enumerate(REFERENCE.split(x)))
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
