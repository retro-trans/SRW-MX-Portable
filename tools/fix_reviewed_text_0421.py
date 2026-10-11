"""Five screenshot corrections, guarded incremental PSP/PS2 local builds."""
import argparse
import copy
import io
import json
import re
import shutil
import struct
import unicodedata
from pathlib import Path

import pycdlib
from PIL import Image
import build_patch
import textfit
import strip_jp
import patch_chapter_cards as cards
from ps2_graphics_port import logical_palette
from patch_wnd_headers import digest, file_digest
from play_order import load
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parents[1]
VERSION, BASE = '0.4.21', '0.4.20'
OLD = 'They are ideal for buying time... No, as decoys to draw our gaze and the enemy to them.'
NEW = "They're ideal for stalling... No, as decoys to draw our attention and lure the enemy."
TITLE = 'Blue Meets White'
TEXT_PAIRS = [('Briest', 'Bryst'), ('MU', 'Mu'), ('Blue meets White', TITLE)]
PATTERNS = [re.compile(re.escape(textfit.encode(a))) for a, _ in TEXT_PAIRS]
BAHBEM = re.compile(re.escape(textfit.encode('Bahbem「They are ideal for buying time')))
NOTE = '0.4.21 screenshot review: Bryst and Mu terminology; Bahbem attraction/decoy wording checked against Japanese.'


def read(p): return json.loads(p.read_text(encoding='utf8'))
def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1)+'\n', encoding='utf8')
def sha(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()
def normalized(b):
    return unicodedata.normalize('NFKC', b.decode('cp932')).replace('’', "'")


def replace_text(data):
    """Replace fullwidth font text only; avoid ASCII machine-code matches."""
    try:
        check=normalized(data)
        for placeholder in textfit.PLACEHOLDER_PX:check=check.replace(placeholder,'')
        if re.search('[\u3040-\u30ff\u3400-\u9fff]',check):return data,0
    except UnicodeDecodeError:
        pass
    count = 0
    for (old, new), pat in zip(TEXT_PAIRS, PATTERNS):
        def sub(m):
            nonlocal count
            # A two-byte Latin neighbour means this is part of a longer word.
            for neighbour in (data[max(0,m.start()-2):m.start()], data[m.end():m.end()+2]):
                try: s = normalized(neighbour)
                except UnicodeDecodeError: continue
                if len(s)==1 and s.isascii() and (s.isalnum() or s=='_'): return m.group()
            count += 1
            return textfit.encode(new)
        data = pat.sub(sub, data)
    if BAHBEM.search(data):
        plain = normalized(data.rstrip(b'\0'))
        assert ' '.join(plain.replace('@',' ').split()) == 'Bahbem「'+OLD+'」', plain
        rendered, lines, ok = textfit.fit_dialogue('Bahbem', NEW)
        assert ok and max(map(textfit.px,lines))<=352
        data = textfit.encode(rendered)+b'\0'; count += 1
    return data, count


def scan(stream):
    positions=set(); pos=0; tail=b''
    stream.seek(0)
    while True:
        chunk=stream.read(8*1024*1024)
        if not chunk: break
        data=tail+chunk
        for pat in PATTERNS+[BAHBEM]:
            positions.update(pos-len(tail)+m.start() for m in pat.finditer(data))
        pos+=len(chunk);tail=data[-1024:]
    groups={}
    for a in sorted(positions):
        stream.seek(a); part=stream.read(4096)
        assert 0 in part, ('unterminated candidate',a)
        end=a+part.index(0)
        groups[end]=min(a,groups.get(end,a))
    rows=[]
    for end,a in sorted(groups.items()):
        # Include neighbouring glyphs for word-boundary checks, but preserve
        # everything before the match. Bahbem's match includes the speaker.
        stream.seek(max(0,a-2)); neighbour=stream.read(a-max(0,a-2))
        stream.seek(a);old=stream.read(end-a+1)
        if not BAHBEM.match(old):
            joined,n=replace_text(neighbour+old)
            if not n: continue
            assert joined.startswith(neighbour)
            new=joined[len(neighbour):]
        else: new,n=replace_text(old)
        assert n and len(new)<=len(old),(a,len(new),len(old))
        # Every candidate must be decodable font text through its terminator.
        before=normalized(old[:-1]);after=normalized(new.rstrip(b'\0'))
        assert not any(ord(c)<32 and c!='\n' for c in before)
        rows.append((a,old,new+bytes(len(old)-len(new)),n,before,after))
    return rows


def rename(obj):
    if isinstance(obj,str):
        s=obj.replace('Briest','Bryst').replace('Blue meets White',TITLE)
        return re.sub(r'\bMU\b','Mu',s)
    if isinstance(obj,list): return [rename(x) for x in obj]
    if isinstance(obj,dict):
        return {k: v if k in ('jp','body_jp','speaker_jp','name_jp','expected_jp') else rename(v) for k,v in obj.items()}
    return obj


def inputs():
    assert not (ROOT/'work/translation/en/ui/screenshot_review_0.4.21.en.json').exists(), 'Preserve the recorded correction baseline'
    manifest=dict(version=VERSION,base_version=BASE,changes=[],current_inputs=[],
                  rom=dict(changed=False,english='I have no name to give the likes of you!!',
                           meaning='I refuse to give my name to the likes of you.',stage=15,full_id=869),
                  bahbem=dict(stage=13,full_id=8,old_en=OLD,en=NEW,
                              meaning='Attract our attention and the enemy; not draw them out.'),
                  chapter16=TITLE)
    paths={ROOT/p for p in read(ROOT/'work/output/campaign_0.4.9_inputs.json')['source_files']}
    full_paths=list((ROOT/'work/translation/en/script').glob('stage*_campaign_full_merged.json'))
    paths.update(full_paths)
    for p in full_paths:
        for r in read(p)['rows']: paths.add(ROOT/r['translation_owner']['source'])
    paths.update((ROOT/'work/translation/en/script').glob('stage*_campaign_sol61medium_merged.json'))
    paths.update((ROOT/'work/translation/en').glob('library*.json'))
    paths.update((ROOT/'work/translation/en/battle').glob('batch_*.json'))
    paths.update(ROOT/'work/translation/en'/p for p in ('static2/names.json',
        'ps2/script/campaign_ps2_variants.en.json','ps2/script/campaign_port.en.json',
        'ps2/database_port.en.json','script/campaign_context_overrides.json'))
    paths.update(p for p in (ROOT/'work/glossary').glob('*.json') if not p.name.startswith('akurasu'))
    journals=[ROOT/'work/output/campaign_context_reviews.json',ROOT/'work/output/stages31_end_context_reviews.json']
    journal_data=[read(p) for p in journals]
    for path in sorted(paths):
        if not path.exists() or path.name.endswith('.en.json') and path.with_name(path.name[:-8]+'.json').exists(): continue
        old=read(path);new=rename(old)
        if 'script' in path.parts:
            for r in new.get('rows',[]) if isinstance(new,dict) else []:
                if r.get('en')==OLD:r['en']=NEW
        if old==new:continue
        if path in full_paths:
            for a,b in zip(old['rows'],new['rows']):
                if a['en']!=b['en']:
                    manifest['changes'].append(dict(source_file=path.relative_to(ROOT).as_posix(),
                        id=b['id'],uses=b['uses'],speaker=b['speaker_en'],old_en=a['en'],en=b['en']))
            fp=fingerprint(new['rows']);new['context_review']['fingerprint']=fp
            new['context_review']['note']=new['context_review'].get('note','')+' '+NOTE
            stage=str(int(path.name[5:7]))
            for journal in journal_data:
                if stage in journal['stages']:
                    journal['stages'][stage]['fingerprint']=fp
                    journal['stages'][stage]['note']=journal['stages'][stage].get('note','')+' '+NOTE
        save(path,new)
        if 'translation' in path.parts and not path.name.endswith('.en.json'):
            save(path.with_name(path.stem+'.en.json'),strip_jp.clean(new))
        manifest['current_inputs'].append(path.relative_to(ROOT).as_posix())
    for p,data in zip(journals,journal_data):save(p,data)
    dp=ROOT/'work/glossary/decisions.json';d=read(dp)
    d['names']['火のブライスト']='Bryst of the Fires'
    d['text_fixes'].update({'Briest':'Bryst','MU':'Mu'})
    d['screenshot_terms_0_4_21']=dict(bryst='Explicit user correction 2026-10-10 overrides Akurasu MX Mech List Briest; retain the established of the Fires epithet.',
        mu='Explicit user correction 2026-10-10: RahXephon faction Mu, with the article the in running text, rather than the uppercase acronym MU.')
    save(dp,d)
    np=ROOT/'work/glossary/name_fixes.json';n=read(np)
    n['names'].update({'Briest of the Fires':'Bryst of the Fires','Bryst of the Fire':'Bryst of the Fires',
                       'Fire Bryst':'Bryst of the Fires'})
    # A self-mapping adds no correction and confuses spelling checks.
    n['names']={a:b for a,b in n['names'].items() if a!=b};save(np,n)
    p=ROOT/'work/translation/en/ui/all_chapter_cards.json';d=read(p)
    for r in d['cards']:
        if r['id'] in ('card_17_main','card_17_duplicate','card_18_gallery'):
            r.update(en=TITLE,needs_translation=True,
                     redraw_reason='User requested uniform readable Chapter 16 lettering (0.4.21).')
    save(p,d);save(p.with_name(p.stem+'.en.json'),strip_jp.clean(d))
    p=ROOT/'work/source/ps2/chapter_mapping.json';d=read(p)
    for r in d['matched']:
        if r['psp_id']=='card_17_main':r.update(english=TITLE,needs_translation=True)
    save(p,d)
    names=ROOT/'work/translation/en/static2/names.json';d=read(names)
    for k,v in d.items():
        if v=='Blue meets White':d[k]=TITLE
    save(names,d);save(names.with_name('names.en.json'),strip_jp.clean(d))
    save(ROOT/'work/translation/en/ui/screenshot_review_0.4.21.en.json',manifest)
    print('Current inputs updated:',len(manifest['current_inputs']),'campaign rows:',len(manifest['changes']),flush=True)


def card_edits(stream,platform):
    specs=read(ROOT/'work/translation/en/ui/all_chapter_cards.json')['cards'] if platform=='PSP' else read(ROOT/'work/source/ps2/chapter_mapping.json')['matched']
    specs=[r for r in specs if r.get('id') in ('card_17_main','card_17_duplicate','card_18_gallery') or r.get('psp_id')=='card_17_main']
    assert len(specs)==3
    mask,layout=cards.render_title(TITLE);rows=[]
    for i,r in enumerate(specs):
        off=r['pixel_offset'];stream.seek(off-1024);pal=stream.read(1024);old=stream.read(256*52)
        assert sha(pal)==r['palette_sha256']
        assert sha(old) in r.get('accepted_title_sha256',[r.get('title_sha256')])
        lp=logical_palette(pal) if platform=='PS2' else pal
        new=cards.indexed_title(mask,lp)
        ui=ROOT/'work/ui'/platform.lower()/f'screenshot_review_{VERSION}';ui.mkdir(parents=True,exist_ok=True)
        for label,pixels in [('original',old),('english',new)]:
            im=Image.frombytes('P',(256,52),pixels);im.putpalette(bytes(c for j in range(256) for c in lp[j*4:j*4+3]))
            im.convert('RGB').resize((768,156)).save(ui/f'chapter16_{i}_{label}.png')
        save(ui/f'chapter16_{i}_layout.json',dict(title=TITLE,pixel_offset=hex(off),**layout,
            palette_preserved=True,chapter_digits_and_logo_preserved=True))
        rows.append((off,old,new,1,'Blue meets White (native mixed-size artwork)',TITLE))
    return rows


def paths(iso):return sorted(folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names)
def read_iso(iso,p):
    with iso.open_file_from_iso(iso_path=p) as f:return f.read()
def story_spans(iso,platform):
    if platform=='PSP':
        elf=read_iso(iso,'/PSP_GAME/SYSDIR/BOOT.BIN');sectors=struct.unpack_from('<204I',elf,build_patch.BLOCK_TABLE)
        return '/PSP_GAME/USRDIR/MAP_ADD.BIN',[(2048*(build_patch.SCRIPT_SECTOR+a),2048*(b-a)) for a,b in zip(sectors,sectors[1:])]
    elf=read_iso(iso,'/SLPS_253.45;1');meta=read(ROOT/f'work/output/ps2_font_{BASE}_verification.json')
    font=meta['font'];table=int(font['segment_offset'],16)+int(meta['stage30']['script_sector_table_va'],16)-int(font['segment_va'],16)
    sectors=struct.unpack_from('<204I',elf,table);base=struct.unpack_from('<18I',elf,0x37e438)[10]*2048
    return '/DATA/MAP.BIN;1',[(base+a*2048,(b-a)*2048) for a,b in zip(sectors,sectors[1:])]


def build(platform,audit=False):
    prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    source=ROOT/f'work/output/{prefix}{BASE}.iso';target=ROOT/f'work/output/{prefix}{VERSION}.iso'
    assert audit or not target.exists(), 'Preserve versioned builds'
    iso=pycdlib.PyCdlib();iso.open(str(source));allpaths=paths(iso);edits={};hashes={};ranges=[]
    card='/PSP_GAME/USRDIR/PACKMAPC2_ADD.BIN' if platform=='PSP' else '/DATA/PACKMAPC.BIN;1'
    textfiles={'BOOT.BIN','EBOOT.BIN','STATIC2_ADD.BIN','MAP_ADD.BIN','BATTLE2.BIN'} if platform=='PSP' else {'SLPS_253.45','FIX00.DAT','MAP.BIN','BATTLE.BIN'}
    for p in allpaths:
        if not audit:hashes[p]=file_digest(iso,p)
        rows=[]
        with iso.open_file_from_iso(iso_path=p) as f:
            if p==card:rows=card_edits(f,platform)
            elif p.rsplit('/',1)[-1].split(';')[0] in textfiles:rows=scan(f)
        if rows:
            edits[p]=rows;extent=iso.get_record(iso_path=p).extent_location()*2048
            ranges += [(extent+a,old,new) for a,old,new,*_ in rows]
    # Review exact native string candidates before any ISO writes.
    summary={p:[dict(offset=hex(a),allocated=len(old),before=before,after=after) for a,old,new,n,before,after in rows] for p,rows in edits.items()}
    save(ROOT/f'work/output/{platform.lower()}_screenshot_review_{VERSION}_candidates.json',summary)
    print(platform,'candidate strings/cards',sum(map(len,edits.values())),{p:len(r) for p,r in edits.items()},flush=True)
    if audit:iso.close();return
    assert edits and any('Bahbem' in row[4] for rows in edits.values() for row in rows)
    shutil.copyfile(source,target)
    with target.open('r+b') as f:
        for off,old,new in sorted(ranges):
            f.seek(off);assert f.read(len(old))==old;f.seek(off);f.write(new)
    check=pycdlib.PyCdlib();check.open(str(target));files=[]
    base=ROOT/'work/build'/platform.lower()/f'screenshot_review_{VERSION}';base.mkdir(parents=True,exist_ok=True)
    for p in allpaths:
        a,b=iso.get_record(iso_path=p),check.get_record(iso_path=p)
        assert (a.extent_location(),a.data_length)==(b.extent_location(),b.data_length)
        actual=file_digest(check,p)
        if p not in edits:assert actual==hashes[p]
        with check.open_file_from_iso(iso_path=p) as f:
            for off,old,new,*_ in edits.get(p,[]):f.seek(off);assert f.read(len(new))==new
            if p.rsplit('/',1)[-1].split(';')[0] in textfiles:assert not scan(f),p
        if p in edits:
            with check.open_file_from_iso(iso_path=p) as f,(base/p.rsplit('/',1)[-1].split(';')[0]).open('wb') as out:shutil.copyfileobj(f,out,8*1024*1024)
        if platform=='PS2':
            name=p.rsplit('/',1)[-1].split(';')[0].rstrip('.').lower()
            matches=[q for q in paths_udf(check) if q.rsplit('/',1)[-1].lower()==name];assert len(matches)==1
            with check.open_file_from_iso(udf_path=matches[0]) as f:assert digest(f)==actual
        files.append(dict(path=p,original_sha256=hashes[p],target_sha256=actual,changed=p in edits))
    story_path,spans=story_spans(iso,platform);changed=[]
    with iso.open_file_from_iso(iso_path=story_path) as a,check.open_file_from_iso(iso_path=story_path) as b:
        for i,(start,size) in enumerate(spans):
            a.seek(start);b.seek(start);old=a.read(size);new=b.read(size)
            c,s=load(old,0);nc,ns=load(new,0);assert c==nc
            ncmd,n,tab=struct.unpack_from('<3I',old,4)
            assert old[:32+48*ncmd]==new[:32+48*ncmd] and old[tab:tab+4*n]==new[tab:tab+4*n]
            for slot,(x,y) in enumerate(zip(s,ns)):
                expected,count=replace_text(x.encode('cp932')+b'\0')
                assert y.encode('cp932')==expected.rstrip(b'\0'),(platform,i,slot)
                if count:changed.append(dict(block=i,slot=slot))
    with source.open('rb') as a,target.open('rb') as b:
        last=0
        for off,old,new in sorted(ranges)+[(source.stat().st_size,b'',b'')]:
            n=off-last
            while n:
                take=min(n,8*1024*1024);assert a.read(take)==b.read(take);n-=take
            assert a.read(len(old))==old and b.read(len(new))==new;last=off+len(old)
        assert not a.read(1) and not b.read(1)
    with target.open('rb') as f:targetsha=digest(f)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    report=dict(version=VERSION,base_version=BASE,platform=platform,output=target.relative_to(ROOT).as_posix(),
        output_sha256=targetsha,bytes=target.stat().st_size,files=files,edits=summary,
        story=dict(blocks=len(spans),changed_slots=changed,commands_and_pointers_preserved=True,every_unrelated_string_preserved=True),
        all_other_disc_bytes_preserved=True,local_build_only=True,in_game_visual_validation='pending',github_release=False)
    save(ROOT/f'work/output/{platform.lower()}_screenshot_review_{VERSION}_verification.json',report)
    if platform=='PS2':
        aggregate=read(ROOT/f'work/output/ps2_font_{BASE}_verification.json');lookup={r['path']:r for r in files}
        for row in aggregate['files']:row['target_sha256']=lookup[row['path']]['target_sha256']
        aggregate['font']['target_sha256']=lookup['/SLPS_253.45;1']['target_sha256']
        aggregate.update(version=VERSION,target_sha256=targetsha,output=report['output'],bytes=report['bytes'],
            source_build_version=BASE,changed_from_previous=[p for p in edits],pcsx2_fresh_boot_verified=False,
            current_correction_report=f'work/output/ps2_screenshot_review_{VERSION}_verification.json')
        data=read_iso(check,story_path)
        for row in aggregate['blocks']:
            i=row['index']
            if i in {x['block'] for x in changed}:
                start,size=spans[i];row['new_sha256']=sha(data[start:start+size]);row['text_correction_build']=VERSION
        save(ROOT/f'work/output/ps2_font_{VERSION}_verification.json',aggregate)
        font=ROOT/f'work/build/ps2/font_{VERSION}';font.mkdir(parents=True,exist_ok=True)
        (font/'SLPS_253.45').write_bytes(read_iso(check,'/SLPS_253.45;1'));save(font/'patch.json',aggregate['font'])
    iso.close();check.close();print(platform,'verified',VERSION,targetsha,flush=True)


def paths_udf(iso):return [folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(udf_path='/') for n in names]


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',action='store_true');ap.add_argument('--audit',action='store_true');ap.add_argument('--build',action='store_true');ap.add_argument('--platform',choices=['PSP','PS2']);args=ap.parse_args()
    if args.inputs:inputs()
    if args.audit or args.build:
        for p in ([args.platform] if args.platform else ['PSP','PS2']):build(p,args.audit)
