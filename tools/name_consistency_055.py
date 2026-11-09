"""Short Mazinger display names and the canonical Gulfer speaker alias."""
import json
from pathlib import Path
import struct
import re
from functools import lru_cache
import textfit
import play_order
import build_patch
from build_reviewed_ps2 import rebuild_slots
from patch_at_field import ROOT,sha
from static2_extract import sections
from verify_text_build import read_iso

OLD='Mass-produced Great Mazinger'
NEW='MP Great Mazinger'
ROWS={349:(OLD,NEW),**{528+2*i:(OLD+f' ({i+1})',NEW+f' ({i+1})') for i in range(8)}}
ASSETS={'PSP':('/PSP_GAME/USRDIR/STATIC2_ADD.BIN','/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/USRDIR/MAP_ADD.BIN'),
        'PS2':('/DATA/FIX00.DAT;1','/SLPS_253.45;1','/DATA/MAP.BIN;1')}
META=ROOT/'work/build/ps2/font_0.4.54/patch.json'
INFO=ROOT/'work/output/ps2_font_0.4.54_verification.json'


def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def update_inputs():
    import strip_jp
    from port_ps2_translations import campaign_sources
    changed=[]
    def write(path,obj):
        Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    def canonical(text):
        if text in ('Galfa Emperor','Emperor Galfa'):return 'Gulfer Emperor'
        if re.fullmatch(r'Mass-[Pp]roduced Great Mazinger(?: \([1-8]\))?',text):
            return NEW+text[len(OLD):]
        return text
    def walk(obj,key=''):
        if isinstance(obj,list):return [walk(v,key) for v in obj]
        if isinstance(obj,dict):return {k:walk(v,k) for k,v in obj.items()}
        if isinstance(obj,str) and key in ('en','en_full','en_short','english','speaker_en','name_en'):
            if key=='speaker_en':return obj.replace('Galfa','Gulfer')
            return canonical(obj)
        if isinstance(obj,str) and key=='notes':
            return obj.replace('immutable Galfa Emperor prefill','canonical Gulfer Emperor speaker label')
        return obj
    paths=[ROOT/'work/glossary'/name for name in
           ('glossary.json','glossary_A.json','glossary_B.json')]
    paths+=[ROOT/'work/translation/en/static2/names.json',ROOT/'work/translation/en/ps2/database_port.en.json']
    paths+=[ROOT/'work/translation/en'/name for name in ('library.json','library_A.json','library_B.json')]
    paths+=campaign_sources()
    for path in paths:
        before=json.loads(path.read_text(encoding='utf8'))
        after=walk(before)
        if path.name=='names.json':after={k:canonical(v) if isinstance(v,str) else v for k,v in before.items()}
        if after==before:continue
        write(path,after);changed.append(path.relative_to(ROOT).as_posix())
        if path.name=='names.json':write(path.with_name('names.en.json'),after)
        if path.parent.name=='script' or path.name.startswith('library'):
            safe=path.with_name(path.stem+'.en.json');clean=strip_jp.clean(after)
            if safe.exists():strip_jp.reject_translation_loss(json.loads(safe.read_text(encoding='utf8')),clean,safe)
            write(safe,clean)
    path=ROOT/'work/glossary/decisions.json';obj=json.loads(path.read_text(encoding='utf8'))
    obj['names']['ガルファ皇帝']='Gulfer Emperor'
    obj['text_fixes'].update({'Galfa Emperor':'Gulfer Emperor','Emperor Galfa':'Gulfer Emperor'})
    glossary=json.loads((ROOT/'work/glossary/glossary.json').read_text(encoding='utf8'))
    for row in glossary['units']:
        if row.get('en','').startswith(NEW):obj['names'][row['jp']]=row['en']
    for old,new in ROWS.values():obj['text_fixes'][old]=new
    obj['gulfer_speaker_reason']='Akurasu MX Mech List and the existing faction decision use Gulfer Emperor. Correct the stale Galfa Emperor short speaker alias as well as the full name; retain Galfa spellings only as lookup aliases or historical reference notes.'
    obj['mp_great_mazinger_reason']='User reported the full unit name overlapping HP on 2026-11-08. Use MP Great Mazinger in display names and retain numbered variants (1)-(8). MP means mass-produced; this compact display overrides the full Akurasu label for UI fit.'
    write(path,obj);changed.append(path.relative_to(ROOT).as_posix())
    path=ROOT/'work/glossary/name_fixes.json';obj=json.loads(path.read_text(encoding='utf8'))
    obj['names']={k:canonical(v) for k,v in obj['names'].items()}
    obj['names'].update(dict(ROWS.values()));obj['names']['Galfa Emperor']='Gulfer Emperor'
    write(path,obj);changed.append(path.relative_to(ROOT).as_posix())
    path=ROOT/'work/glossary/do_not_touch.json';obj=json.loads(path.read_text(encoding='utf8'))
    obj['names']=[canonical(v) for v in obj['names']];write(path,obj);changed.append(path.relative_to(ROOT).as_posix())
    return changed


def patch(data,platform,preview=None):
    start,_,_= (sections(data) if platform=='PSP' else sections(data,0))['Strg']
    out=bytearray(data);ranges=[];rows=[]
    for idx,(before_text,after_text) in ROWS.items():
        at=start+struct.unpack_from('<I',data,start+12+idx*4)[0]
        old=textfit.encode(before_text)+b'\0';new=textfit.encode(after_text)+b'\0'
        new+=bytes(len(old)-len(new))
        assert data[at:at+len(old)] in (old,new),('Unknown Mazinger name',platform,idx)
        out[at:at+len(old)]=new;ranges.append([at,at+len(old)])
        rows.append(dict(id='strg_'+str(idx),english=after_text,text=after_text,
                         offset=hex(at),allocated_bytes=len(old),already_translated=data[at:at+len(old)]==new))
    last=0
    for a,b in sorted(ranges):assert out[last:a]==data[last:a];last=b
    assert out[last:]==data[last:] and len(out)==len(data)
    report=dict(platform=platform,regions=rows,byte_ranges=ranges,native_name_pointers_preserved=True,
                all_other_bytes_preserved=True,source_resource_sha256=sha(data),target_resource_sha256=sha(out))
    if preview:save(Path(preview)/'layout.en.json',report)
    return bytes(out),report


def script_layout(elf,platform):
    if platform=='PSP':
        return build_patch.SCRIPT_SECTOR*2048,struct.unpack_from('<204I',elf,build_patch.BLOCK_TABLE)
    report=json.loads(INFO.read_text());meta,info=report['font'],report['stage30']
    at=int(meta['segment_offset'],16)+int(info['script_sector_table_va'],16)-int(meta['segment_va'],16)
    return struct.unpack_from('<18I',elf,0x37e438)[10]*2048,struct.unpack_from('<204I',elf,at)


def decode_english(native):
    reverse={code.to_bytes(2,'big').decode('cp932'):char for char,code in textfit.ASCII.items()}
    text=''.join(reverse.get(c,c) for c in native)
    # Native space bytes are shared by Latin word spaces and the full-cell
    # continuation indent. Retain the latter for conservative line fitting.
    return '@'.join('　'+s[1:] if s.startswith(' ') else s for s in text.split('@'))


@lru_cache(maxsize=1)
def ps2_widths():
    return {int(g['sjis'],16):g['width'] for g in json.loads(META.read_text())['glyphs']}


def line_width(line,platform):
    if platform=='PSP':return textfit.px(line)
    glyphs=ps2_widths()
    return sum(glyphs.get(textfit.ASCII.get(c),24) for c in line)


def fit(native,platform):
    english=decode_english(native);limit=352 if platform=='PSP' else 528
    if max(line_width(line,platform) for line in english.split('@'))<=limit:return native,False
    flat=' '.join(english.replace('@',' ').split())
    opening=flat.index('「');prefix=flat[:opening+1];suffix='」' if flat.endswith('」') else ''
    body=flat[opening+1:len(flat)-len(suffix) if suffix else None]
    lines=[];line=prefix
    for word in body.split():
        candidate=line+('' if line==prefix else ' ')+word
        if line_width(candidate+suffix,platform)>limit:
            lines.append(line);line='　'+word
        else:line=candidate
    lines.append(line+suffix)
    assert len(lines)<=3 and max(line_width(s,platform) for s in lines)<=limit
    assert ' '.join(' '.join(lines).split())==flat
    return textfit.encode('@'.join(lines)).decode('cp932'),True


def patch_story(data,elf,platform):
    base,rel=script_layout(elf,platform);out=bytearray(data);ranges=[];rows=[]
    old=textfit.encode('Galfa').decode('cp932');new=textfit.encode('Gulfer').decode('cp932')
    for i,(a,b) in enumerate(zip(rel,rel[1:])):
        start=base+a*2048;end=base+b*2048;raw=data[start:end]
        cmds,strings=play_order.load(raw,0);replacements={};expected=list(strings)
        for slot,s in enumerate(strings):
            if old in s:
                target,reflow=fit(s.replace(old,new),platform)
                replacements[slot]=target.encode('cp932');expected[slot]=target
                rows.append(dict(block=i,slot=slot,occurrences=s.count(old),reflowed=reflow,
                                 line_widths=[line_width(line,platform) for line in decode_english(target).split('@')]))
        if replacements:
            rebuilt=rebuild_slots(raw,replacements)
            assert len(rebuilt)<=len(raw),('Script block allocation exceeded',i)
            rebuilt+=bytes(len(raw)-len(rebuilt))
            commands,after=play_order.load(rebuilt,0)
            assert cmds==commands and after==expected
            out[start:end]=rebuilt;ranges.append([start,end])
    assert sum(r['occurrences'] for r in rows) in (0,13)
    assert not out.count(textfit.encode('Galfa'))
    assert out.count(textfit.encode('Gulfer Emperor'))==data.count(textfit.encode('Gulfer Emperor'))+sum(r['occurrences'] for r in rows)
    last=0
    for a,b in ranges:assert out[last:a]==data[last:a];last=b
    assert out[last:]==data[last:] and len(out)==len(data)
    return bytes(out),dict(platform=platform,changed_strings=rows,byte_ranges=ranges,
        native_commands_preserved=True,unrelated_strings_preserved=True,script_sector_layout_preserved=True,
        no_galfa_remaining=True,source_resource_sha256=sha(data),target_resource_sha256=sha(out))


def verify_iso(path,platform):
    names,elf,maps=ASSETS[platform];data=read_iso(str(path),[names,elf,maps])
    assert patch(data[names],platform)[0]==data[names]
    assert patch_story(data[maps],data[elf],platform)[0]==data[maps]
    return dict(platform=platform,nine_short_unit_names_verified=True,no_galfa_in_scripts=True,
                gulfer_emperor_verified=True,native_commands_and_sector_layout_preserved=True)
