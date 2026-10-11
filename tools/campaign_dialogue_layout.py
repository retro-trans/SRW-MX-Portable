"""Use reviewed line breaks for exact English dialogue on both platforms."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/'work/translation/en/ui/campaign_dialogue_layout.en.json'


def key(speaker,body,kind):
    return hashlib.sha256(json.dumps([speaker,body,kind],ensure_ascii=False).encode('utf8')).hexdigest()


@lru_cache(maxsize=1)
def layouts():
    return {r['english_key']:r for r in json.loads(PATH.read_text(encoding='utf8'))['rows']} if PATH.exists() else {}


def apply(speaker,body,kind,default_lines):
    row=layouts().get(key(speaker,body,kind))
    if row is None:return default_lines
    assert row['speaker']==speaker and row['body']==body and row['kind']==kind
    import textfit
    lines=row['lines']
    assert len(lines)<=3 and max(map(textfit.px,lines))<=352
    # A layout must only move line breaks; preserve words and delimiters.
    normalize=lambda values:' '.join(' '.join(values).split())
    assert normalize(lines)==normalize(default_lines), 'Reviewed layout differs from current game text'
    return lines
