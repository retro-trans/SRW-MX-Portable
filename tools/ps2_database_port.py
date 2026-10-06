"""Rebuild native PS2 FIX00 translations using PSP source text, never PSP IDs.

The PS2 loader allocates and reads the actual FIX00 file length (0x334a4c,
0x334a5c, 0x334a98). Every numeric gameplay record stays byte-identical.
Original sentence IDs are retained; translated rows are appended.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

import insert_text as it
from static2_extract import sections,strtable,index,is_dummy
from port_ps2_translations import ROOT,read_json,normalize,sha


def strings(tag,raw):
    head=12+4*len(raw);offsets=[];data=bytearray()
    for text in raw:
        offsets.append(head+len(data));data+=text
    return tag.encode()+struct.pack('<2I',head+len(data),len(raw))+struct.pack('<%dI'%len(raw),*offsets)+data


def indices(tag,rows):
    head=12+4*len(rows);offsets=[];data=bytearray()
    for ids in rows:
        offsets.append(head+len(data));data+=struct.pack('<H',len(ids))+struct.pack('<%dH'%len(ids),*ids)
    return tag.encode()+struct.pack('<2I',head+len(data),len(rows))+struct.pack('<%dI'%len(rows),*offsets)+data


def build(original):
    psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    s=sections(original,0);p=sections(psp)
    names=read_json(ROOT/'work/translation/en/static2/names.json')
    pstr=strtable(psp,p['Strg'][0],p['Strg'][2]);ostr=strtable(original,s['Strg'][0],s['Strg'][2])
    lookup=defaultdict(set)
    for i,jp in enumerate(pstr):
        if names.get(str(i)):lookup[jp].add(names[str(i)])
    # Names absent from PSP source use the already approved glossary spelling.
    manual={"晨星２型":"Shinsei Type II", "中田　和宏":"Kazuhiro Nakata",
            "鶴野　恭子":"Kyoko Tsuruno", "上田　祐司":"Yuji Ueda",
            "日高　のり子":"Noriko Hidaka", "柏倉　つとむ":"Tsutomu Kashiwakura",
            "吉田　理保子":"Rihoko Yoshida", "竹松　拓":"Taku Takemura"}
    # PS2 uses historical spellings/spacing for these credited voice actors.
    actors=read_json(ROOT/'work/translation/en/static2/voice_actors.json')
    for i,jp in enumerate(pstr):
        en=actors.get(jp)
        if isinstance(en,dict):en=en.get('en')
        if en:lookup[jp].add(en)
    loose=defaultdict(set)
    for jp,values in lookup.items():loose[normalize(jp)].update(values)
    new={};manifest=[];missing_names=[]
    raw_names=[]
    for i,jp in enumerate(ostr):
        values=lookup[jp] or loose[normalize(jp)]
        en=manual.get(jp) or (next(iter(values)) if len(values)==1 else None)
        if en:
            raw_names.append(it.encode(it.clean(en)))
            manifest.append(dict(table='Strg',entry=i,source_sha256=sha(jp.encode('cp932')),english=en))
        else:
            raw_names.append(jp.encode('cp932')+b'\0')
            if jp not in set(pstr):missing_names.append(dict(table='Strg',entry=i,jp=jp))
    new['Strg']=strings('Strg',raw_names)
    lib=read_json(ROOT/'work/translation/en/library.json');desc=read_json(ROOT/'work/translation/en/static2/descriptions.json')
    psent=strtable(psp,p['Sent'][0],p['Sent'][2]);sent=strtable(original,s['Sent'][0],s['Sent'][2])
    rows_out=[v.encode('cp932')+b'\0' for v in sent];missing=[];counts={};append_cache={};retained=set()
    overrides={}
    override_path=ROOT/'work/translation/en/ps2/database_variants.en.json'
    if override_path.exists():overrides={r['source_sha256']:r['english'] for r in read_json(override_path)['rows']}
    widths={'Xunt':496,'XPlt':496,'XSpr':416,'XSkl':416,'Xabl':416,'XPrt':272,'XHlp':416}
    for tag in widths:
        trans=defaultdict(set)
        for i,ids in enumerate(index(psp,p[tag][0],p[tag][2])):
            en=(lib['units' if tag=='Xunt' else 'pilots'].get(str(i),{}).get('en')
                if tag in ('Xunt','XPlt') else desc[tag].get(str(i)))
            if en:trans[normalize(''.join(psent[j] for j in ids))].add(en)
        updated=[];count=0
        for i,ids in enumerate(index(original,s[tag][0],s[tag][2])):
            jp=''.join(sent[j] for j in ids);key=sha(jp.encode('cp932'));values=trans[normalize(jp)]
            en=overrides.get(key) or (sorted(values)[0] if values else None)
            if not en:
                updated.append(ids)
                retained.update(ids)
                if not is_dummy([sent[j] for j in ids]):missing.append(dict(table=tag,entry=i,source_sha256=key,jp=jp))
                continue
            lines=it.wrap(it.clean(en),widths[tag]);outids=[]
            if tag in ('Xunt','XPlt'):assert len(lines)<=25,(tag,i,len(lines))
            for line in lines:
                encoded=it.encode(line)
                if encoded not in append_cache:
                    append_cache[encoded]=len(rows_out);rows_out.append(encoded)
                outids.append(append_cache[encoded])
            updated.append(outids);count+=1
            manifest.append(dict(table=tag,entry=i,source_sha256=key,english=en,lines=lines))
        new[tag]=indices(tag,updated);counts[tag]=dict(translated=count,total=s[tag][2],remaining=sum(x['table']==tag for x in missing))
    assert len(rows_out)<65536
    # Untranslated/dummy indexes retain their source rows. All other original
    # IDs remain valid but their now-unreferenced Japanese storage is released.
    for i in range(len(sent)):
        if i not in retained:rows_out[i]=b'\0'
    # Keep the fixed 0x3e4000 resource heap within its original budget. The
    # longest translated rows are resolved by the native sentence getter.
    candidates=sorted(range(len(sent),len(rows_out)),key=lambda i:len(rows_out[i]),reverse=True)
    external=[];external_ids={};total=0
    for i in candidates:
        if total>=320000:break
        external_ids[i]=len(external);external.append(rows_out[i]);total+=len(rows_out[i]);rows_out[i]=b'\0'
    head=12+4*len(rows_out);payload=bytearray();offsets=[];cache={}
    for i,row in enumerate(rows_out):
        if i in external_ids:offsets.append(0x80000000|external_ids[i]);continue
        if row not in cache:cache[row]=head+len(payload);payload+=row
        offsets.append(cache[row])
    new['Sent']=b'Sent'+struct.pack('<2I',head+len(payload),len(rows_out))+struct.pack('<%dI'%len(rows_out),*offsets)+payload
    data=bytearray();new_offsets={}
    for tag,(offset,size,count) in s.items():
        new_offsets[tag]=len(data);data+=new.get(tag,original[offset:offset+size]);data+=bytes(-len(data)%4)
    # Fixh's 19 offset words include the Unit offset in its apparent count word.
    old_directory=struct.unpack_from('<19I',original,s['Fixh'][0]+8)
    offset_tags={o:tag for tag,(o,size,count) in s.items()}
    assert all(o in offset_tags for o in old_directory)
    struct.pack_into('<19I',data,new_offsets['Fixh']+8,*(new_offsets[offset_tags[o]] for o in old_directory))
    rebuilt=bytes(data);rs=sections(rebuilt,0)
    for tag in s:
        if tag not in new and tag!='Fixh':
            a,n,c=s[tag];z,nn,cc=rs[tag];assert original[a:a+n]==rebuilt[z:z+nn],tag
    for i in retained:
        ptr=offsets[i];assert rebuilt[rs['Sent'][0]+ptr:rs['Sent'][0]+ptr+len(sent[i].encode('cp932'))+1]==sent[i].encode('cp932')+b'\0'
    for tag in widths:
        for ids in index(rebuilt,rs[tag][0],rs[tag][2]):assert all(i<len(rows_out) for i in ids)
    report=dict(names_translated=sum(r['table']=='Strg' for r in manifest),descriptions=counts,
                original_sentence_ids_retained=True,unreferenced_source_sentence_storage_released=True,
                external_sentence_rows=len(external),external_sentence_bytes=total,numeric_gameplay_records_unchanged=True,
                original_bytes=len(original),english_bytes=len(rebuilt),source_sha256=sha(original),
                target_sha256=sha(rebuilt),texts=manifest,remaining_names=[{k:v for k,v in r.items() if k!='jp'} for r in missing_names])
    private=ROOT/'work/source/ps2/database_missing.json'
    private.write_text(json.dumps(missing+missing_names,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (ROOT/'work/build/ps2/campaign/database_overflow.json').write_text(json.dumps([b.hex() for b in external]),encoding='utf8')
    return rebuilt,report


if __name__=='__main__':
    data,report=build((ROOT/'work/source/ps2/FIX00.DAT').read_bytes())
    out=ROOT/'work/build/ps2/campaign/FIX00.DAT';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    (ROOT/'work/translation/en/ps2/database_port.en.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='texts'},indent=2))
