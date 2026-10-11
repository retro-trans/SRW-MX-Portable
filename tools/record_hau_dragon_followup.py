"""Apply the user's Hau Dragon terminology correction and reviewed enemy list.

Historical contributor packets remain intact; exact context overrides reproduce
each change. This updates translation sources/reports, not existing game ISOs.
"""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import campaign_context_overrides as overrides_tool
import campaign_status
import strip_jp
import textfit
import campaign_dialogue_layout
from ps2_narration_port import native_width
from record_campaign_context_review import fingerprint

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'work/translation/en/script'
DATE='2026-10-11'
REASON=('User screenshot follow-up: use Hau Dragon consistently for the organization; '
        'the older Tekkoryu spelling and unspoken Iron Dragon gloss are not the ordinary display name.')
LIST=('Giganos, Gulfer, the Mu... The Hyakki Empire and Hau Dragon... '
      'Plus the Vegan Empire, and the Angels on top of that.')


def read(path):return json.loads(path.read_text(encoding='utf8'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
def safe(path,data):write(path.with_name(path.stem+'.en.json'),strip_jp.clean(data))


def main():
    followup_path=SCRIPT/'screenshot_proofread_followups.en.json'
    followups=read(followup_path)
    assert not any(e.get('review_tag')=='hau_dragon_2026_10_11' for e in followups['edits']), 'Follow-up already applied'
    decisions_path=SCRIPT/'campaign_context_overrides.json';decisions=read(decisions_path)
    by_location={(o['stage'],o['full_id']):o for o in decisions['overrides']}
    journals={key:read(ROOT/'work/output'/key) for key in ['campaign_context_reviews.json','stages31_end_context_reviews.json']}
    font=read(ROOT/'work/build/ps2/font_0.4.23/patch.json')
    prepared=[];changes=[];validation=[];layouts={}
    for path in sorted(SCRIPT.glob('stage*_campaign_full_merged.json')):
        stage=int(path.name[5:7]);data=read(path);edited=0
        for row in data['rows']:
            if 'Tekkoryu' not in row['en']:continue
            before=copy.deepcopy(row);old=row['en'];reason=REASON
            if (stage,row['id'])==(18,1201):
                assert row['speaker_en']=='Prospector' and row['uses']==['i03s4b:82']
                new=LIST
                reason+=' The Japanese lists seven enemies cumulatively. Plus avoids implying a chronology; the Mu uses the requested article.'
            elif 'Hau Dragon' in old:
                # Three source lines explicitly contrast the written name with
                # its foreign reading. Retain the distinction as an English
                # literal alias, rather than duplicating Hau Dragon twice.
                assert (stage,row['id']) in {(12,53),(21,371),(56,477)}
                new=old.replace('Tekkoryu','the Iron Dragon')
                reason+=' This source explicitly says both name forms; the Iron Dragon is retained only as its literal alias, preserving the pause/self-correction.'
            else:
                new=old.replace('Tekkoryu (Iron Dragon)','Hau Dragon').replace('Tekkoryu','Hau Dragon')
            key=(stage,row['id'])
            if key in by_location:
                decision=by_location[key]
                assert decision['en']==old and decision['expected_owner']==row['translation_owner'] and decision['expected_jp']==row['jp']
                decision['en']=new;decision['reason']+=' '+reason
            else:
                decision=dict(stage=stage,full_id=row['id'],expected_owner=copy.deepcopy(row['translation_owner']),
                    expected_jp=row['jp'],expected_en=old,en=new,reason=reason)
                decisions['overrides'].append(decision);by_location[key]=decision
            row['en']=new;row['notes']=row.get('notes','')+' '+reason
            # Reassemble from the unchanged exact contributor, then apply the
            # guarded override; all non-editorial fields must match.
            owner=row['translation_owner'];source=ROOT/owner['source']
            contributor_path=source.with_name(source.stem+'_sol61medium_merged.json')
            contributor=next(r for r in read(contributor_path)['rows'] if r['id']==owner['id'])
            original=next(r for r in read(path.with_name('stage%02d_campaign_all_source.json'%stage))['rows'] if r['id']==row['id'])
            rebuilt=copy.deepcopy(original)
            rebuilt.update({k:contributor.get(k,[] if k=='uncertain' else '') for k in ['speaker_en','en','notes','uncertain']})
            rebuilt=overrides_tool.apply_override(stage,rebuilt,decisions['overrides'])
            assert all(rebuilt.get(k)==row.get(k) for k in ['id','jp','speaker_en','en','uses','kind','translation_owner','uncertain']),key
            assert all(before.get(k)==row.get(k) for k in set(before)|set(row) if k not in {'en','notes'}),key
            opening,closing=('（','）') if row['kind']=='thought' else ('「','」')
            # Preserve every word; select greedy line breaks that fit both
            # packaged fonts rather than changing the wording for PS2 width.
            for limit in range(352,299,-1):
                lines,ok=textfit.wrap(row['speaker_en']+opening,new,closing,line_px=limit)
                widths=[native_width(''.join(c for c in l.replace('　',' ') if c not in '「」（）'),font)
                        +24*sum(l.count(c) for c in '「」（）') for l in lines]
                if ok and max(widths)<=528:break
            assert ok and max(widths)<=528,(key,widths)
            english_key=campaign_dialogue_layout.key(row['speaker_en'],new,row['kind'])
            layout=layouts.setdefault(english_key,dict(english_key=english_key,speaker=row['speaker_en'],
                body=new,kind=row['kind'],lines=lines,psp_widths=[textfit.px(l) for l in lines],
                ps2_widths=widths,line_limit=limit,appearances=[]))
            layout['appearances'].append(list(key))
            changes.append(dict(speaker=row['speaker_en'],kind=row['kind'],before=old,after=new,reason=reason,
                appearances=[[stage,row['id']]],source_sha256=hashlib.sha256(row['jp'].encode('utf8')).hexdigest(),
                review_tag='hau_dragon_2026_10_11',psp_widths=[textfit.px(l) for l in lines],ps2_widths=widths))
            edited+=1
        if not edited:continue
        findings=campaign_status.check_full(data['rows']);assert not findings,(stage,findings)
        journal_name='campaign_context_reviews.json' if stage<=30 else 'stages31_end_context_reviews.json'
        journal=journals[journal_name];review=copy.deepcopy(journal['stages'][str(stage)])
        review['fingerprint']=fingerprint(data['rows'])
        review['note']+=' '+DATE+': Hau Dragon screenshot terminology follow-up applied to current sources; aliases retained only where explicitly contrasted. Source-only.'
        journal['stages'][str(stage)]=review;data['context_review']=review;data['context_review_pending']=False
        prepared.append((path,data));validation.append(dict(chapter=stage,rows=len(data['rows']),changes=edited,problems=[],guarded_reassembly_verified=True))
    assert len(changes)==54,len(changes)
    # Prepare glossary changes without rewriting historical translator packets.
    glossary_path=ROOT/'work/glossary/glossary.json';glossary=read(glossary_path)
    entry=next(e for e in glossary['terms'] if e['jp']=='鉄甲龍')
    assert entry['en']=='Tekkoryu (Iron Dragon)'
    entry['en']='Hau Dragon';entry['notes']=REASON+' Explicit dual-name dialogue may retain the literal Iron Dragon alias.'
    glossary_decisions_path=ROOT/'work/glossary/decisions.json';glossary_decisions=read(glossary_decisions_path)
    glossary_decisions['names']['鉄甲龍']='Hau Dragon';glossary_decisions['names']['ハウドラゴン']='Hau Dragon'
    glossary_decisions['hau_dragon_display']=dict(date=DATE,en='Hau Dragon',reason=REASON,
        source='Explicit user request; Akurasu MX term tables have no organization entry.',
        explicit_alias_exception='Only lines explicitly naming/contrasting both readings retain the literal Iron Dragon alias.')
    layout_path=ROOT/'work/translation/en/ui/campaign_dialogue_layout.en.json'
    existing=read(layout_path) if layout_path.exists() else dict(rows=[])
    assert not set(layouts)&{r['english_key'] for r in existing['rows']}
    # Apply all prepared changes after every source, width and guard has passed.
    for path,data in prepared:write(path,data);safe(path,data)
    write(decisions_path,decisions);safe(decisions_path,decisions)
    for name,journal in journals.items():write(ROOT/'work/output'/name,journal)
    write(glossary_path,glossary);write(glossary_decisions_path,glossary_decisions)
    existing['rows'].extend(layouts.values());existing['date']=DATE
    existing['scope']='Exact reviewed English line breaks; wording is preserved on both PSP and PS2'
    write(layout_path,existing)
    followups['edits'].extend(changes);followups['date']=DATE
    followups.setdefault('followup_validations',[]).append(dict(date=DATE,scope='Hau Dragon terminology and Prospector enemy list',
        changed_occurrences=len(changes),changed_chapters=len(prepared),chapters=validation,
        guarded_reassembly_verified=True,all_non_editorial_metadata_preserved=True,iso_rebuilt=False))
    write(followup_path,followups)
    ui=ROOT/'work/ui/psp/proofread_followups';ui.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-30f7a097-0f5d-4d28-a347-3c38307301d0.png'),ui/'chapter18_prospector_enemy_list_reported.png')
    print('Applied %d source occurrences across %d chapters; both font limits and guarded reassembly pass.'%(len(changes),len(prepared)))


def library_followup():
    """Keep current encyclopedia text and its assembly inputs consistent."""
    target=ROOT/'work/translation/en/ui/hau_dragon_library_followup.en.json'
    assert not target.exists()
    records=[];prepared=[]
    for path in sorted((ROOT/'work/translation/en').glob('library*.json')):
        if path.name.endswith('.en.json'):continue
        data=read(path);changes=[]
        def visit(obj):
            if isinstance(obj,dict):
                if isinstance(obj.get('en'),str) and 'Tekkoryu' in obj['en']:
                    old=obj['en'];obj['en']=old.replace('Tekkoryu (Iron Dragon)','Hau Dragon').replace('Tekkoryu','Hau Dragon')
                    changes.append(dict(entry=obj['entry'],before=old,after=obj['en'],
                        source_sha256=hashlib.sha256(obj['jp'].encode('utf8')).hexdigest(),reason=REASON))
                    obj['notes']=obj.get('notes','')+' '+REASON
                for value in obj.values():visit(value)
            elif isinstance(obj,list):
                for value in obj:visit(value)
        visit(data)
        if changes:
            prepared.append((path,data))
            records.append(dict(source=path.relative_to(ROOT).as_posix(),changes=changes))
    assert records and sum(len(r['changes']) for r in records if r['source'].endswith('/library.json'))==7
    for path,data in prepared:write(path,data);safe(path,data)
    write(target,dict(date=DATE,iso_rebuilt=False,reason=REASON,files=records))
    print('Standardized 7 encyclopedia entries and their current assembly inputs.')


if __name__=='__main__':
    import sys
    if '--library-only' in sys.argv:library_followup()
    else:main()
