"""Record the user's spaced surname and two reviewed dialogue/music changes."""
import json
from pathlib import Path
from record_campaign_context_review import fingerprint
from strip_jp import clean

ROOT=Path(__file__).resolve().parents[1]
OLD_ROCK="Damn Taiha... He grows arrogant just because he enjoys Yuratei's favor..."
NEW_ROCK="Damn Taiha... He's gotten full of himself just because he's Yuratei's favorite..."
MUSIC={'1744':'Burning Spirit - Defying Fate',
       '1745':'A Serene Mind, A Blazing Palm'}
NOTE='PSP 0.4.14: user requested George De Sand spelling; Rockfell favor/arrogance phrasing checked against source and made idiomatic.'


def read(path):return json.loads(path.read_text(encoding='utf8'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf8')


def rename(data):
    if isinstance(data,dict):return {k:rename(v) if k not in ('jp','body_jp','speaker_jp','name_jp') else v for k,v in data.items()}
    if isinstance(data,list):return [rename(v) for v in data]
    if isinstance(data,str):return data.replace('George DeSand','George De Sand')
    return data


def main():
    manifest_path=ROOT/'work/translation/en/ui/psp_0.4.14.en.json'
    assert not manifest_path.exists(), 'The correction manifest already exists; preserve its baseline wording'
    manifest=dict(version='0.4.14',base_version='0.4.13',dialogue=[],
                  name={'1190':'George De Sand'},music=MUSIC,
                  karl_translation_checked=True,karl_translation_changed=False)
    journal_paths=[ROOT/'work/output/campaign_context_reviews.json',
                   ROOT/'work/output/stages31_end_context_reviews.json']
    journals=[read(p) for p in journal_paths]
    folder=ROOT/'work/translation/en/script'
    for path in sorted(folder.glob('stage*_campaign_full_merged.json')):
        data=read(path);changed=[]
        for r in data['rows']:
            old=r['en'];new=old.replace('George DeSand','George De Sand')
            if old==OLD_ROCK:new=NEW_ROCK
            if new!=old:
                manifest['dialogue'].append(dict(source_file=str(path.relative_to(ROOT)).replace('\\','/'),
                    id=r['id'],uses=r['uses'],speaker=r['speaker_en'],kind=r['kind'],old_en=old,en=new))
                r['en']=new;changed.append(r['id'])
        if changed:
            data=rename(data)
            fp=fingerprint(data['rows']);data['context_review']['fingerprint']=fp
            data['context_review']['note']=data['context_review'].get('note','')+' '+NOTE
            write(path,data);write(path.with_name(path.stem+'.en.json'),clean(data))
            stage=str(int(path.name[5:7]))
            for journal in journals:
                if stage in journal['stages']:
                    journal['stages'][stage]['fingerprint']=fp
                    journal['stages'][stage]['note']=journal['stages'][stage].get('note','')+' '+NOTE
    assert len(manifest['dialogue'])==6
    for path,data in zip(journal_paths,journals):write(path,data)
    # Update merged contributor inputs, leaving historical drafts/slices intact.
    for stage in (5,7,16,18,31):
        path=folder/f'stage{stage:02d}_campaign_sol61medium_merged.json'
        if not path.exists():continue
        data=rename(read(path))
        for r in data.get('rows',[]):
            if r.get('en')==OLD_ROCK:r['en']=NEW_ROCK
        write(path,data);write(path.with_name(path.stem+'.en.json'),clean(data))
    path=ROOT/'work/translation/en/library.json';data=rename(read(path));write(path,data)
    write(path.with_name('library.en.json'),clean(data))
    for batch in (16,17):
        path=ROOT/f'work/translation/en/battle/batch_{batch}.json'
        data=rename(read(path));write(path,data)
        write(path.with_name(path.stem+'.en.json'),clean(data))
    for relative in ('work/glossary/glossary.json','work/glossary/do_not_touch.json'):
        path=ROOT/relative;write(path,rename(read(path)))
    path=ROOT/'work/glossary/name_fixes.json';data=read(path)
    data['names'].update({'George DeSand':'George De Sand','George de Sand':'George De Sand'})
    write(path,data)
    path=ROOT/'work/glossary/decisions.json';data=read(path)
    data['names']['ジョルジュ・ド・サンド']='George De Sand'
    data['text_fixes']['George DeSand']='George De Sand'
    data['user_spelling_0_4_14']={'en':'George De Sand','akurasu':'George DeSand',
        'reason':'Explicit user correction on 2026-10-07 takes precedence over Akurasu joined surname.'}
    data['music_display_0_4_14']={k:dict(en=v,reason='Compact English translation of both title clauses; requested translation rather than romanization and must fit a single 427px music row.') for k,v in MUSIC.items()}
    write(path,data)
    path=ROOT/'work/translation/en/static2/music.en.json';data=read(path)
    data['titles'].update(MUSIC);data['refreshed']='2026-10-07'
    data['notes']='Akurasu MX BGM terms, with compact English translations for the two long G Gundam titles. Display choices and reasons are recorded in work/glossary/decisions.json.'
    write(path,data)
    path=ROOT/'work/translation/en/static2/names.json';data=read(path)
    data.update(manifest['name']);data.update(MUSIC);write(path,data)
    write(manifest_path,manifest)
    print('Recorded six dialogue corrections, spaced surname and two English music titles.')


if __name__=='__main__':main()
