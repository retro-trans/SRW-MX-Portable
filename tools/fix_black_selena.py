"""User-requested Black Selena spelling; local PSP/PS2 0.4.18."""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path

import textfit
import strip_jp
import fix_albero_est as h

h.VERSION='0.4.18'
h.BASE_VERSION='0.4.17'
h.TAG='black_selena'
h.NAME='Black Selena'
h.PREVIOUS_BASE=h.ROOT/'work/build/ps2/albero_0.4.17'
h.EXPECTED_COUNTS={'PSP':[3,3,5,2],'PS2':[3,2,4]}
encoded_words=[textfit.encode(s) for s in ('Sarana','Sarena')]
h.PATTERNS=[
    (re.compile(re.escape(textfit.encode('Black'))+b'(?:'+re.escape(textfit.encode(' '))+b'|@)+'+
                b'(?:'+b'|'.join(re.escape(w) for w in encoded_words)+b')'),textfit.encode('Selena')),
    (re.compile(rb'Black[ @]+Sar[ae]na'),b'Selena'),
]


def replace_text(data):
    count=0
    for pattern,word in h.PATTERNS:
        def sub(match):
            nonlocal count
            count+=1
            return match.group()[:-len(word)]+word
        data=pattern.sub(sub,data)
    return data,count


h.replace_text=replace_text


def inputs():
    paths={h.ROOT/p for p in json.loads((h.ROOT/'work/output/campaign_0.4.9_inputs.json').read_text())['source_files']}
    paths.update(h.ROOT/'work/translation/en'/p for p in (
        'library.json','library_B.json','static2/names.json','static2/music.en.json',
        'ps2/script/campaign_ps2_variants.en.json','ps2/script/campaign_port.en.json',
        'ps2/database_port.en.json'))
    paths.update(p for p in (h.ROOT/'work/glossary').glob('*.json') if not p.name.startswith('akurasu'))
    def walk(x):
        if isinstance(x,str):return x.replace('Black Sarana','Black Selena').replace('Black Sarena','Black Selena')
        if isinstance(x,list):return [walk(v) for v in x]
        if isinstance(x,dict):return {k:walk(v) for k,v in x.items()}
        return x
    changed=[]
    for path in sorted(paths):
        if not path.exists():continue
        old=json.loads(path.read_text(encoding='utf8'));new=walk(old)
        if old==new:continue
        h.save(path,new)
        if 'translation' in path.parts and not path.name.endswith('.en.json') and path.parent.name!='static2':
            h.save(path.with_name(path.stem+'.en.json'),strip_jp.clean(new))
        changed.append(str(path.relative_to(h.ROOT)).replace('\\','/'))
    path=h.ROOT/'work/glossary/decisions.json';data=json.loads(path.read_text(encoding='utf8'))
    data['names'].update({'ブラックサレナ':'Black Selena','高機動型ブラックサレナ':'High-maneuver Black Selena'})
    data['text_fixes'].update({'Black Sarana':'Black Selena','Black Sarena':'Black Selena'})
    data['black_selena_reason']='User explicitly requested Black Selena on 2026-10-07. Overrides the refreshed Akurasu MX Mech List Sarana spelling, and the Sarena variant in older inputs, consistently for both forms and associated text.'
    h.save(path,data)
    fixes=h.ROOT/'work/glossary/name_fixes.json';obj=json.loads(fixes.read_text(encoding='utf8'))
    obj['names'].update({'Black Sarana':'Black Selena','Black Sarena':'Black Selena',
                         'High-maneuver Black Sarana':'High-maneuver Black Selena',
                         'High-Mobility Black Sarena':'High-maneuver Black Selena'})
    h.save(fixes,obj)
    for name in ('glossary.json','glossary_B.json'):
        path=h.ROOT/'work/glossary'/name;obj=json.loads(path.read_text(encoding='utf8'))
        def note(x):
            if isinstance(x,dict):
                if x.get('jp') in ('ブラックサレナ','高機動型ブラックサレナ'):
                    x['en']=data['names'][x['jp']]
                    x['notes']='User-requested Black Selena spelling (2026-10-07), overriding Akurasu MX Sarana; form qualifier retains the established wording.'
                for v in x.values():note(v)
            elif isinstance(x,list):
                for v in x:note(v)
        note(obj);h.save(path,obj)
    h.save(h.ROOT/'work/translation/en/ui/black_selena_0.4.18.en.json',
           dict(version=h.VERSION,name=h.NAME,current_inputs=changed,reason=data['black_selena_reason'],
                preserved_form_qualifier='High-maneuver',associated_music_title='Black Selena III'))
    print('Updated current spelling inputs:',len(changed),flush=True)


def widths():
    from ps2_narration_port import native_width
    meta=json.loads((h.PREVIOUS_BASE/'patch.json').read_text())
    checks={'PSP':{s:textfit.px(s) for s in ('Sarana','Sarena','Selena')},
            'PS2':{s:native_width(s,meta) for s in ('Sarana','Sarena','Selena')}}
    for row in checks.values():assert row['Selena']<=min(row['Sarana'],row['Sarena'])
    h.save(h.ROOT/'work/translation/en/ui/black_selena_widths_0.4.18.en.json',checks)
    print('Both native fonts: replacement is narrower.',checks,flush=True)


def runtime():
    import pycdlib
    from ppsspp_dbg import Dbg
    from verify_text_build import resolver,overflow_table
    from static2_extract import sections
    iso=pycdlib.PyCdlib();iso.open(str(h.ROOT/'work/output/SRWMX_EN_0.4.18.iso'))
    with iso.open_file_from_iso(iso_path='/PSP_GAME/SYSDIR/BOOT.BIN') as f:boot=f.read()
    with iso.open_file_from_iso(iso_path='/PSP_GAME/USRDIR/STATIC2_ADD.BIN') as f:static=f.read()
    iso.close();get=resolver(static,boot);start,_,_=sections(static)['Strg']
    expected={204:'High-maneuver Black Selena',206:'Black Selena',1738:'Black Selena III'}
    for idx,text in expected.items():assert get(start,struct.unpack_from('<I',static,start+12+idx*4)[0])==textfit.encode(text)
    count=3837;table=overflow_table(boot);ptrs=struct.unpack_from(f'<{count}I',boot,table+96)
    with Dbg('ws://127.0.0.1:45394/debugger') as d:
        status=d.call('game.status');assert status['game']['id']=='ULJS00041';d.call('cpu.stepping')
        try:
            module=next(m for m in d.call('hle.module.list')['modules'] if m['name']=='SRWMXforPSP');base=module['address']
            assert struct.unpack(f'<{count}I',d.read(base+table,4*count))==tuple(base+p for p in ptrs)
            report=json.loads((h.ROOT/'work/output/psp_black_selena_0.4.18_verification.json').read_text())
            rows=report['edits']['/PSP_GAME/SYSDIR/BOOT.BIN']
            for row in rows:
                offset=int(row['offset'],16);size=row['allocated_bytes']
                assert d.read(base+offset-96,size)==boot[offset:offset+size]
            # The two unit names are inline in native STATIC Strg.
            name_bytes=textfit.encode(expected[204])+b'\0';ram=d.read(0x08800000,24*1024*1024)
            candidates=[];a=0
            while True:
                a=ram.find(name_bytes,a)
                if a<0:break
                block=ram[a:a+len(name_bytes)+32+len(textfit.encode(expected[206]))+1]
                if textfit.encode(expected[206])+b'\0' in block:candidates.append(0x08800000+a)
                a+=len(name_bytes)
            assert candidates,'Both corrected unit names must be loaded together in native Strg'
        finally:d.call('cpu.resume')
    h.save(h.ROOT/'work/output/psp_black_selena_0.4.18_runtime.json',
           dict(version=h.VERSION,fresh_boot=True,profile='work/build/psp_0414_test',name_table_indices=expected,
                native_name_addresses=[hex(x) for x in candidates],boot_library_and_music_rows_verified=len(rows),
                all_relocated_pointers_verified=count,affected_screen_playthrough=False))
    print('PSP fresh boot: both unit names and updated library/music text loaded.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',action='store_true')
    p.add_argument('--build',action='store_true');p.add_argument('--verify-existing',action='store_true')
    p.add_argument('--platform',choices=['PSP','PS2']);p.add_argument('--runtime',action='store_true');a=p.parse_args()
    if a.inputs:inputs()
    widths()
    if a.build or a.verify_existing:
        for platform in ([a.platform] if a.platform else ('PSP','PS2')):
            print('Checking/building',platform,h.VERSION,flush=True);h.build(platform,a.verify_existing)
    if a.runtime:runtime()
