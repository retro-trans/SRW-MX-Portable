"""Trace the reported DFC conversation without exporting Japanese script text."""
import difflib
import hashlib
import json
import re
import struct
import unicodedata
from pathlib import Path
import pycdlib
import play_order
import ps2_title_footer

ROOT=Path(__file__).resolve().parents[1]
ANCHOR='Have you finished adjusting the new'
STAGE28=('i055b','s0550','i055a')
STAGE29=('i057b','s0570','i057a')


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def sha(data):return hashlib.sha256(data).hexdigest()
def norm(text):return re.sub(r'[@\s\u3000]','',text)
def english(text):return ' '.join(unicodedata.normalize('NFKC',text).replace('@',' ').split())


def uses(commands,slot):
    return [i for i,c in enumerate(commands) if c[0]==11 and c[2]==slot
            or c[0]==12 and slot in (c[1],c[6])]


def spoken(commands,texts):
    out=[]
    for i,c in enumerate(commands):
        slots=[c[2]] if c[0]==11 else [c[1],c[6]] if c[0]==12 else []
        out.extend((i,s,norm(texts[s])) for s in slots)
    return out


def audit():
    source=ROOT/'work/translation/en/script/stage56_campaign_full_merged.json'
    row=next(r for r in read(source)['rows'] if ANCHOR in r.get('en',''))
    needle=norm(row['jp'])
    psp=(ROOT/'work/build/MAP_ADD.orig').read_bytes()
    inventory=read(ROOT/'work/source/stage_map.json');blocks={};original_matches=[]
    for b in inventory:
        c,t=play_order.load(psp,b['offset']);blocks[b['name']]=(c,t)
        for slot,text in enumerate(t):
            if norm(text)==needle:
                original_matches.append(dict(scene=b['name'],slot=slot,command_indexes=uses(c,slot)))
    assert original_matches==[dict(scene='s0570',slot=336,command_indexes=[692])]
    previous=read(ROOT/'work/output/ps2_font_0.4.38_verification.json')
    meta,info=previous['font'],previous['stage30']
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/'work/output/SRWMX_PS2_EN_0.4.38.iso'))
    with iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as stream:elf=stream.read()
    assert sha(elf)==meta['target_sha256']
    offset=lambda va:int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
    rel=struct.unpack_from('<204I',elf,offset(int(info['script_sector_table_va'],16)))
    names=[]
    for va in struct.unpack_from('<203I',elf,offset(int(info['script_name_table_va'],16))):
        a=offset(va);names.append(elf[a:elf.index(0,a)].decode('ascii'))
    start=struct.unpack_from('<18I',elf,0x37e438)[10]
    active={};matches=[];provenance=[]
    with iso.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
        for n,name in enumerate(names):
            stream.seek((start+rel[n])*2048);raw=stream.read((rel[n+1]-rel[n])*2048)
            c,t=play_order.load(raw,0);active[name]=(c,t)
            for slot,text in enumerate(t):
                if ANCHOR in english(text):
                    matches.append(dict(scene=name,slot=slot,command_indexes=uses(c,slot),line=english(text)))
            if name in STAGE28+STAGE29:
                expected=[(178,*r[1:]) if r[0]==179 else r for r in blocks[name][0]]
                assert c==expected,name
                provenance.append(dict(scene=name,commands=len(c),original_psp_commands_match=True,
                    native_portrait_cache_opcode_adaptations=sum(r[0]==179 for r in blocks[name][0]),
                    command_sha256=sha(raw[32:32+48*len(c)])))
    iso.close()
    assert len(matches)==1 and matches[0]['scene']=='s0570' and matches[0]['slot']==336
    # Compare native spoken-message order, rather than string table proximity.
    later=spoken(*blocks['s0570']);chapter28=[]
    for name in STAGE28:
        early=spoken(*blocks[name])
        matcher=difflib.SequenceMatcher(None,[r[2] for r in early],[r[2] for r in later],autojunk=False)
        runs=[m.size for m in matcher.get_matching_blocks() if m.size>=3]
        chapter28.append(dict(scene=name,matching_spoken_runs_of_three_or_more=runs,
                              exact_anchor_occurrences=sum(norm(s)==needle for s in blocks[name][1])))
    assert not any(r['matching_spoken_runs_of_three_or_more'] for r in chapter28)
    ps2=next(b for b in read(ROOT/'work/source/ps2/script_comparison.json')['ps2_blocks'] if b['name']=='i055a')
    psp29=blocks['s0570'][1]
    later_set={norm(t) for t in psp29[335:450] if len(norm(t))>18}
    shared=[i for i,t in enumerate(ps2['strings']) if norm(t) in later_set]
    matcher=difflib.SequenceMatcher(None,list(map(norm,ps2['strings'])),list(map(norm,psp29)),autojunk=False)
    old_runs=[dict(ps2_slot=m.a,psp_slot=m.b,strings=m.size) for m in matcher.get_matching_blocks() if m.size>=3]
    older=[]
    for version in ('0.4.33','0.4.36'):
        path=ROOT/f'work/output/SRWMX_PS2_EN_{version}.iso'
        if not path.exists():continue
        disc=pycdlib.PyCdlib();disc.open(str(path))
        with disc.open_file_from_iso(iso_path='/SLPS_253.45;1') as stream:old_elf=stream.read()
        ps2_title_footer.verify(old_elf,version)
        old_rel=struct.unpack_from('<204I',old_elf,offset(int(info['script_sector_table_va'],16)))
        old_names=[]
        for va in struct.unpack_from('<203I',old_elf,offset(int(info['script_name_table_va'],16))):
            a=offset(va);old_names.append(old_elf[a:old_elf.index(0,a)].decode('ascii'))
        assert old_names==names
        section=struct.unpack_from('<18I',old_elf,0x37e438)[10];scenes={}
        with disc.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
            for name in ('i055a','s0570'):
                n=names.index(name);stream.seek((section+old_rel[n])*2048)
                raw=stream.read((old_rel[n+1]-old_rel[n])*2048);commands,texts=play_order.load(raw,0)
                if name=='i055a':assert sha(raw[32:32+len(commands)*48])==ps2['command_sha256']
                else:assert commands==[(178,*r[1:]) if r[0]==179 else r for r in blocks[name][0]]
                scenes[name]=(commands,texts)
        early={english(t) for t in scenes['i055a'][1] if len(norm(t))>28}
        later={english(t) for t in scenes['s0570'][1][335:450] if len(norm(t))>28}
        shared_english=len(early&later);assert shared_english>20
        older.append(dict(version=version,native_footer_verified=True,executable_sha256=sha(old_elf),
            chapter28_commands_original_ps2=True,chapter29_commands_psp_with_native_cache_adaptation=True,
            identical_long_english_strings_in_body_conversation=shared_english,
            duplicate_body_conversation_present_in_scripts=True))
        disc.close()
    c=active['s0570'][0]
    event_start=max(i for i in range(692) if c[i][0]==126)
    event_end=next(i for i in range(693,len(c)) if c[i][0]==127)
    current=read(ROOT/'work/output/ps2_font_0.4.44_verification.json')
    file_hash=lambda r:next(f['target_sha256'] for f in r['files'] if f['path']=='/DATA/MAP.BIN;1')
    assert file_hash(current)==file_hash(previous)
    result=dict(date='2026-10-26',version_examined='0.4.38',latest_local_same_map='0.4.44',
        actual_iso_executable_sha256=sha(elf),map_sha256=file_hash(previous),
        source_row=dict(path=source.relative_to(ROOT).as_posix(),id=row['id'],uses=row['uses'],
                        japanese_sha256=sha(row['jp'].encode('cp932')),english=row['en']),
        original_psp_exact_matches=original_matches,active_ps2_exact_matches=matches,
        chapter28_and_29_command_provenance=provenance,
        chapter28_psp_vs_chapter29_spoken_comparison=chapter28,
        original_ps2_chapter28_after_vs_psp29=dict(scene='i055a',shared_long_string_slots=len(shared),
            matching_runs=old_runs,interpretation='Much of the body/upgrade conversation was in original PS2 chapter 28 aftermath and is in PSP chapter 29.'),
        older_ps2_builds_examined=older,
        chapter29_event=dict(scene='s0570',start=event_start,end=event_end,
            opening_guards=[list(c[i]) for i in range(event_start+1,event_start+5)],
            anchor_command=692,anchor_slot=336),
        chapter28_content='Aqua mourns Hugo after he goes missing; the new-machine DFC/body-reveal conversation is absent.',
        screenshot_content='Hugo explains his artificial body and the new machine; this is an original PSP chapter-29 conversation.',
        runtime_repetition_confirmed=False,requires_exact_first_occurrence_or_checkpoint=True,
        reporter_reply='exact I think',reporter_exact_repeat_is_tentative=True,
        save_origin_unknown=True,old_save_or_cached_script_is_only_a_hypothesis=True,
        game_files_changed=False,github_release=False)
    out=ROOT/'work/output/ps2_repeated_dfc_dialogue_0.4.38_audit.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':audit()
