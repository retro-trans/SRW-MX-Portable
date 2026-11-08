"""Shorten one shared unit display name without changing native pointers."""
import json
from pathlib import Path
import struct
import textfit
from patch_at_field import ROOT,sha
from static2_extract import sections
from verify_text_build import read_iso

OLD='High-maneuver Black Selena'
NEW='HM Black Selena'
SPECS={'PSP':('/PSP_GAME/USRDIR/STATIC2_ADD.BIN',0x1b6824),
       'PS2':('/DATA/FIX00.DAT;1',0x37920)}


def update_inputs():
    import strip_jp
    files=['work/glossary/'+n+'.json' for n in
           ('decisions','do_not_touch','glossary','glossary_B','name_fixes')]
    files+=['work/translation/en/'+n for n in
            ('static2/names.json','static2/names.en.json','ps2/database_port.en.json',
             'library.json','library.en.json','library_B.json','library_B.en.json')]
    def replace(obj):
        if isinstance(obj,str):return obj.replace(OLD,NEW)
        if isinstance(obj,list):return [replace(v) for v in obj]
        if isinstance(obj,dict):
            out={k:replace(v) for k,v in obj.items()}
            if obj.get('jp')=='高機動型ブラックサレナ':
                out['notes']='User requested HM Black Selena (2026-11-08) to fit Pilot Training. HM means High-maneuver; retains the user-requested Selena spelling over Akurasu Sarana.'
            return out
        return obj
    changed=[]
    for name in files:
        path=ROOT/name
        if not path.exists():continue
        before=json.loads(path.read_text(encoding='utf8'));after=replace(before)
        if name.endswith('decisions.json'):
            after['names']['高機動型ブラックサレナ']=NEW
            after['text_fixes'][OLD]=NEW
            after['hm_black_selena_reason']='User requested HM Black Selena on 2026-11-08 because the full name overlaps PP in Pilot Training. HM abbreviates High-maneuver. Supersedes the full form from the 2026-10-07 decision for display names; Black Selena spelling is retained. Overrides the Akurasu full-form label for UI fit.'
        if name.endswith('name_fixes.json'):after['names'][OLD]=NEW
        if before==after:continue
        path.write_text(json.dumps(after,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
        if name.endswith(('library.json','library_B.json')):
            safe=path.with_name(path.stem+'.en.json')
            safe.write_text(json.dumps(strip_jp.clean(after),ensure_ascii=False,indent=1)+'\n',encoding='utf8')
        changed.append(name)
    return changed


def patch(data,platform,preview=None):
    old=textfit.encode(OLD)+b'\0';new=textfit.encode(NEW)+b'\0'
    path,offset=SPECS[platform]
    allocated=len(old)
    wanted=new+bytes(allocated-len(new))
    before=data[offset:offset+allocated]
    assert before in (old,wanted),'Unexpected HM Black Selena allocation'
    assert len(new)<allocated
    # Both platforms' Strg entry 204 must still point to this allocation.
    start,_,_=(sections(data,0) if platform=='PS2' else sections(data))['Strg']
    assert start+struct.unpack_from('<I',data,start+12+204*4)[0]==offset
    out=data[:offset]+wanted+data[offset+allocated:]
    assert len(out)==len(data)
    assert out[:offset]==data[:offset] and out[offset+allocated:]==data[offset+allocated:]
    evidence=dict(platform=platform,regions=[dict(id='hm_black_selena',english=NEW,
        old_name=OLD,text=NEW,already_translated=before==wanted,offset=hex(offset),
        allocated_bytes=allocated,source_allocation_sha256=sha(old),target_allocation_sha256=sha(wanted))],
        byte_ranges=[[offset,offset+allocated]],all_other_pixels_and_bytes_preserved=True,
        native_pointers_preserved=True,source_resource_sha256=sha(data),target_resource_sha256=sha(out))
    if preview:
        preview=Path(preview);preview.mkdir(parents=True,exist_ok=True)
        (preview/'layout.en.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
    return out,evidence


def verify_iso(path,platform):
    asset=SPECS[platform][0]
    data=read_iso(str(path),[asset])[asset]
    expected,report=patch(data,platform)
    assert expected==data and report['regions'][0]['already_translated']
    return dict(platform=platform,native_unit_name_verified=True,name=NEW,entry=204,
                resource_sha256=sha(data),native_pointers_preserved=True)
