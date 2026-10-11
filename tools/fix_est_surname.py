"""Correct all game-facing Esto surnames and create local 0.4.24 candidates.

Earlier review baselines remain historical records. Active contributor packets,
their exact guard expectations, and current game inputs use Est consistently.
"""
import argparse
import copy
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path

import pycdlib
import fix_albero_est as inherited
import strip_jp
import textfit
from build_title_footer import stamp_existing
from patch_wnd_headers import file_digest, digest
from record_campaign_context_review import fingerprint

ROOT=Path(__file__).resolve().parents[1]
VERSION,BASE='0.4.24','0.4.23'
WORD=re.compile(r'\bEsto\b')
NOTE='2026-10-11 user correction: use Est for both Albero and Folia in every current game-facing input.'


def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n',encoding='utf8')


def inputs():
    marker=ROOT/'work/translation/en/ui/est_surname_0.4.24.en.json'
    assert not marker.exists(),'Inputs already corrected'
    script=ROOT/'work/translation/en/script'
    pattern=r'(stage\d+_campaign(?:_full_merged|_sol61medium_merged|_sol61medium_slice_\d+|_all_source)?|prologue(?:_sol61medium_merged|_sol61medium_slice_\d+)?)\.json'
    paths={p for p in script.glob('*.json') if re.fullmatch(pattern,p.name)}
    paths.add(script/'campaign_context_overrides.json')
    for folder in ['work/translation/en','work/translation/en/static2','work/translation/en/battle','work/translation/en/ps2/script','work/glossary']:
        for p in (ROOT/folder).glob('*.json'):
            if p.name.endswith('.en.json'):
                if p.with_name(p.name[:-8]+'.json').exists():continue
                if not (p.name.startswith('campaign_') or p.name.startswith('stage1_')):continue
            if p.name.startswith('akurasu'):continue
            paths.add(p)
    fields={'en','english','speaker_en','name_en','en_full','en_short','expected_en'}
    prepared=[];records=[]
    for path in sorted(paths):
        data=read(path);changes=[]
        def walk(obj,loc=''):
            if isinstance(obj,dict):
                for key,value in obj.items():
                    if isinstance(value,str) and key in fields and WORD.search(value):
                        new=WORD.sub('Est',value);obj[key]=new
                        changes.append(dict(field=loc+'/'+key,before=value,after=new))
                    elif isinstance(value,(dict,list)):walk(value,loc+'/'+key)
            elif isinstance(obj,list):
                for index,value in enumerate(obj):walk(value,loc+'/'+str(index))
        walk(data)
        if changes:prepared.append((path,data));records.append(dict(source=path.relative_to(ROOT).as_posix(),changes=changes))
    # Direct keyed UI translations store the English in arbitrary value keys.
    names_path=ROOT/'work/translation/en/static2/names.json'
    names=read(names_path)
    def names_walk(obj):
        if isinstance(obj,str):return WORD.sub('Est',obj)
        if isinstance(obj,list):return [names_walk(x) for x in obj]
        if isinstance(obj,dict):return {k:names_walk(v) for k,v in obj.items()}
        return obj
    updated=names_walk(names)
    if updated!=names:prepared.append((names_path,updated));records.append(dict(source=names_path.relative_to(ROOT).as_posix(),keyed_names_corrected=True))
    # Exact source and owner guards survive the synchronized name correction.
    lookup={str(p.resolve()):d for p,d in prepared}
    overrides=lookup.get(str((script/'campaign_context_overrides.json').resolve()),read(script/'campaign_context_overrides.json'))
    baseline_overrides=read(script/'campaign_context_overrides.json')['overrides']
    for baseline,decision in zip(baseline_overrides,overrides['overrides']):
        if not WORD.search(baseline['expected_en']):continue
        owner=ROOT/decision['expected_owner']['source']
        owner=owner.with_name(owner.stem+'_sol61medium_merged.json')
        owner_data=lookup.get(str(owner.resolve()),read(owner))
        row=next(r for r in owner_data['rows'] if r['id']==decision['expected_owner']['id'])
        assert row['en']==decision['expected_en'],(decision['stage'],decision['full_id'])
        full=read(script/('stage%02d_campaign_full_merged.json'%decision['stage']))
        target=next(r for r in full['rows'] if r['id']==decision['full_id'])
        assert target['en']==decision['en']
    for path,data in prepared:
        write(path,data)
        if 'translation' in path.parts and not path.name.endswith('.en.json'):
            write(path.with_name(path.stem+'.en.json'),strip_jp.clean(data))
    decisions_path=ROOT/'work/glossary/decisions.json';decisions=read(decisions_path)
    decisions['text_fixes'].update({'Albero Esto':'Albero Est','Folia Esto':'Folia Est','Esto':'Est'})
    decisions['est_surname_policy']=dict(date='2026-10-11',names=['Albero Est','Folia Est'],reason=NOTE,
        provenance='Explicit user choice; overrides the reference-page variant surname.')
    write(decisions_path,decisions)
    fixes_path=ROOT/'work/glossary/name_fixes.json';fixes=read(fixes_path)
    fixes['names'].update({'Albero Esto':'Albero Est','Folia Esto':'Folia Est'})
    write(fixes_path,fixes)
    # No current proofread wording changes: still check every assembled source.
    remaining=[]
    for p in sorted(script.glob('stage*_campaign_full_merged.json')):
        data=read(p)
        remaining.extend((p.name,r['id']) for r in data['rows'] if WORD.search((r.get('en') or '')+' '+(r.get('speaker_en') or '')))
        assert data['context_review']['fingerprint']==fingerprint(data['rows']),p
    assert not remaining,remaining
    write(marker,dict(version=VERSION,base_version=BASE,date='2026-10-11',reason=NOTE,files=records,
        current_proofread_dialogue_already_correct=True,context_guards_synchronized=True,
        iso_rebuilt=False,historical_review_before_text_preserved=True))
    ui=ROOT/'work/ui/psp/est_surname_0.4.24';ui.mkdir(parents=True,exist_ok=True)
    for filename,label in [('bb631974-770e-4cea-988a-579c1bbde81b','folia_reported'),('2303e730-414c-4473-afa0-1d3c3e89231d','albero_reported')]:
        shutil.copyfile(Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-'+filename+'.png'),ui/(label+'.png'))
    print('Corrected %d active input files; current proofread dialogue and fingerprints remain valid.'%len(records),flush=True)


def setup_scan():
    encoded=re.escape(textfit.encode('Esto'))
    # Put the literal first so the engine can skip gigabytes of unrelated
    # disc padding; the lookbehind includes the matched word itself.
    inherited.PATTERNS=[(re.compile(encoded+rb'(?<!\x82[\x60-\x9a]'+encoded+rb')(?!\x82[\x60-\x9a])'),textfit.encode('o')),
                        (re.compile(rb'Esto(?<![A-Za-z]Esto)(?![A-Za-z])'),b'o')]


def build(platform,patch_key='est',correction_label='surname',
          proof_flag='no_esto_in_game_files',occurrence_field='surname_occurrences',scope=None):
    setup_scan()
    prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    source=ROOT/'work/output'/(prefix+BASE+'.iso');target=source.with_name(prefix+VERSION+'.iso')
    assert not target.exists(),'Preserve existing versioned builds'
    original=pycdlib.PyCdlib();original.open(str(source))
    paths=sorted(folder.rstrip('/')+'/'+str(name) for folder,_,names in original.walk(iso_path='/') for name in names)
    edits={};hashes={};ranges=[]
    for path in paths:
        hashes[path]=file_digest(original,path)
        with original.open_file_from_iso(iso_path=path) as stream:rows=inherited.scan(stream)
        if rows:
            edits[path]=rows;extent=original.get_record(iso_path=path).extent_location()*2048
            ranges.extend((extent+a,old,new) for a,old,new,_ in rows)
            print(platform,path,sum(n for _,_,_,n in rows),correction_label+' corrections',flush=True)
    assert ranges,'No matching old text found in this source candidate'
    shutil.copyfile(source,target)
    with target.open('r+b') as stream:
        for start,old,new in ranges:
            stream.seek(start);assert stream.read(len(old))==old
            stream.seek(start);stream.write(new)
    footer=stamp_existing(target,platform,VERSION)
    current=pycdlib.PyCdlib();current.open(str(target));files=[]
    build_dir=ROOT/'work/build'/platform.lower()/(patch_key+'_'+VERSION);build_dir.mkdir(parents=True,exist_ok=True)
    for path in paths:
        old_rec,new_rec=original.get_record(iso_path=path),current.get_record(iso_path=path)
        assert (old_rec.extent_location(),old_rec.data_length)==(new_rec.extent_location(),new_rec.data_length)
        actual=file_digest(current,path)
        if path not in edits and path!=footer['asset']:assert actual==hashes[path],path
        with current.open_file_from_iso(iso_path=path) as stream:
            assert not inherited.scan(stream),path
            for start,old,new,_ in edits.get(path,[]):
                stream.seek(start);assert stream.read(len(new))==new
        if path in edits:
            with current.open_file_from_iso(iso_path=path) as src,(build_dir/path.rsplit('/',1)[-1].split(';')[0]).open('wb') as dst:
                shutil.copyfileobj(src,dst,8*1024*1024)
        udf_ok=False
        if platform=='PS2':
            name=path.rsplit('/',1)[-1].split(';')[0].rstrip('.')
            udf=[folder.rstrip('/')+'/'+str(n) for folder,_,ns in current.walk(udf_path='/') for n in ns if str(n).lower()==name.lower()]
            assert len(udf)==1,(path,udf)
            with current.open_file_from_iso(udf_path=udf[0]) as stream:assert digest(stream)==actual
            udf_ok=True
        files.append(dict(path=path,source_sha256=hashes[path],target_sha256=actual,
            **{occurrence_field:sum(n for _,_,_,n in edits.get(path,[]))},udf_readback=udf_ok))
    # The preserved executable layout lets the established scene checker verify
    # all commands, IDs and pointers. It uses only structural metadata here.
    story=inherited.compare_story(original,current,platform)
    original.close();current.close()
    allowed=[(start,start+len(old)) for start,old,new in ranges]
    allowed.extend((footer['disc_extent']+a,footer['disc_extent']+z) for a,z in footer['pixel_ranges'])
    with source.open('rb') as left,target.open('rb') as right:
        last=0
        for start,end in sorted(allowed)+[(source.stat().st_size,source.stat().st_size)]:
            assert start>=last
            remaining=start-last
            while remaining:
                count=min(remaining,8*1024*1024);assert left.read(count)==right.read(count);remaining-=count
            left.seek(end);right.seek(end);last=end
        assert not left.read(1) and not right.read(1)
    assert target.stat().st_size==source.stat().st_size
    with target.open('rb') as stream:target_hash=digest(stream)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    report=dict(version=VERSION,base_version=BASE,platform=platform,output=target.relative_to(ROOT).as_posix(),
        output_sha256=target_hash,bytes=target.stat().st_size,files=files,story=story,footer=footer,
        corrected_occurrences=sum(f[occurrence_field] for f in files),**{proof_flag:True},
        commands_ids_pointers_and_sizes_preserved=True,all_other_disc_bytes_preserved=True,
        local_build_only=True,github_release=False,affected_story_playthrough_verified=False,
        scope=scope or 'Surname-only incremental candidate plus exact version footer; later source proofreading awaits full story rebuild')
    write(ROOT/'work/output'/(platform.lower()+'_'+patch_key+'_'+VERSION+'_verification.json'),report)
    if platform=='PS2':
        previous=read(ROOT/'work/output'/('ps2_font_'+BASE+'_verification.json'));aggregate=copy.deepcopy(previous)
        lookup={f['path']:f for f in files}
        for entry in aggregate['files']:entry['target_sha256']=lookup[entry['path']]['target_sha256']
        aggregate['font']['target_sha256']=lookup['/SLPS_253.45;1']['target_sha256']
        aggregate.update(version=VERSION,output=report['output'],bytes=report['bytes'],target_sha256=target_hash,
            source_build_version=BASE,source_build_sha256=previous['target_sha256'],title_footer=footer,
            current_correction_report='work/output/ps2_'+patch_key+'_'+VERSION+'_verification.json',
            changed_from_previous=[f['path'] for f in files if f['target_sha256']!=f['source_sha256']],
            inherited_execution_checks_from_version=BASE,pcsx2_fresh_boot_verified=False,
            inherited_execution_checks_reason='Only declared terminated text allocations and footer version fields change; commands and pointers are unchanged.')
        # Refresh each changed script block hash from the actual target image.
        check=pycdlib.PyCdlib();check.open(str(target))
        with check.open_file_from_iso(iso_path='/SLPS_253.45;1') as stream:elf=stream.read()
        meta=aggregate['font'];info=aggregate['stage30']
        table=int(meta['segment_offset'],16)+int(info['script_sector_table_va'],16)-int(meta['segment_va'],16)
        sectors=struct.unpack_from('<204I',elf,table);base=struct.unpack_from('<18I',elf,0x37e438)[10]*2048
        changed_blocks={r['block'] for r in story['changed_slots']}
        with check.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
            for entry in aggregate['blocks']:
                i=entry['index']
                if i in changed_blocks:
                    stream.seek(base+sectors[i]*2048)
                    entry['new_sha256']=hashlib.sha256(stream.read((sectors[i+1]-sectors[i])*2048)).hexdigest()
                    entry['text_correction_build']=VERSION
        check.close()
        write(ROOT/'work/output'/('ps2_font_'+VERSION+'_verification.json'),aggregate)
        font=ROOT/'work/build/ps2'/('font_'+VERSION);font.mkdir(parents=True,exist_ok=True)
        (font/'SLPS_253.45').write_bytes(elf);write(font/'patch.json',aggregate['font'])
    print(platform,VERSION,'verified',report['corrected_occurrences'],'occurrences;',target_hash,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',action='store_true');parser.add_argument('--build',choices=['PSP','PS2'])
    args=parser.parse_args()
    if args.inputs:inputs()
    if args.build:build(args.build)
