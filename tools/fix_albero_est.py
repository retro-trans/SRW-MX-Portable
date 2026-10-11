"""Correct the requested surname in current inputs and both local 0.4.17 discs.

Shorten terminated strings in their existing allocation. Preserve every
pointer, script command, file size, sector, texture and executable instruction.
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
import textfit
import strip_jp
import build_patch
from patch_wnd_headers import digest, file_digest
from play_order import load

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.17'
BASE_VERSION = '0.4.16'
TAG = 'albero'
NAME = 'Albero Est'
PREVIOUS_BASE = ROOT/'work/build/ps2/at_field_0.4.16'
EXPECTED_COUNTS = {'PSP':[1,1,16,25], 'PS2':[16,1,27]}
PATTERNS = [
    (re.compile(re.escape(textfit.encode('Albero')) + b'(?:' +
                re.escape(textfit.encode(' ')) + b'|@)+' +
                re.escape(textfit.encode('Esto'))), textfit.encode('o')),
    (re.compile(rb'Albero[ @]+Esto'), b'o'),
]


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1)+'\n', encoding='utf8')


def replace_text(data):
    count = 0
    for pattern, last in PATTERNS:
        def sub(match):
            nonlocal count
            count += 1
            assert match.group().endswith(last)
            return match.group()[:-len(last)]
        data = pattern.sub(sub, data)
    return data, count


def inputs():
    paths = {ROOT/p for p in json.loads((ROOT/'work/output/campaign_0.4.9_inputs.json').read_text())['source_files']}
    paths.update(ROOT/'work/translation/en'/p for p in (
        'library.json', 'library_C.json', 'static2/names.json',
        'battle/batch_25.json', 'battle/batch_26.json',
        'ps2/script/campaign_ps2_variants.en.json',
        'ps2/script/campaign_port.en.json', 'ps2/database_port.en.json'))
    paths.update(p for p in (ROOT/'work/glossary').glob('*.json')
                 if not p.name.startswith('akurasu'))
    changed = []
    def walk(obj):
        if isinstance(obj, str): return obj.replace('Albero Esto', 'Albero Est')
        if isinstance(obj, list): return [walk(v) for v in obj]
        if isinstance(obj, dict): return {k:walk(v) for k,v in obj.items()}
        return obj
    for path in sorted(paths):
        old = json.loads(path.read_text(encoding='utf8')); new = walk(old)
        if new == old: continue
        save(path, new)
        if path.suffix == '.json' and not path.name.endswith('.en.json') and 'translation' in path.parts and path.parent.name != 'static2':
            save(path.with_name(path.stem+'.en.json'), strip_jp.clean(new))
        changed.append(str(path.relative_to(ROOT)).replace('\\','/'))
    decisions = ROOT/'work/glossary/decisions.json'
    obj = json.loads(decisions.read_text(encoding='utf8'))
    obj['names']['アルベロ・エスト'] = 'Albero Est'
    obj['text_fixes']['Albero Esto'] = 'Albero Est'
    obj['albero_surname_reason'] = 'User explicitly requested Albero Est on 2026-10-07. MX term tables have no Albero entry; retain the requested spelling over the Esto variant in character reference pages.'
    save(decisions, obj)
    for name in ('glossary.json', 'glossary_C.json'):
        path = ROOT/'work/glossary'/name
        obj = json.loads(path.read_text(encoding='utf8'))
        def notes(x):
            if isinstance(x, dict):
                if x.get('en_full') == 'Albero Est':
                    x['notes'] = 'User-requested Albero Est spelling (2026-10-07); Esto is a reference-page variant. Game library gives age 46 (SRW wiki says 43).'
                for value in x.values(): notes(value)
            elif isinstance(x, list):
                for value in x: notes(value)
        notes(obj); save(path, obj)
    save(ROOT/'work/translation/en/ui/albero_est_0.4.17.en.json',
         dict(version=VERSION, old_name='Albero Esto', name='Albero Est', changed_current_inputs=changed,
              reason='User-requested surname spelling; short name Albero is preserved.'))
    print('Updated current translation and glossary inputs:', len(changed))


def scan(stream):
    positions = set(); pos = 0; tail = b''
    stream.seek(0)
    while True:
        block = stream.read(8*1024*1024)
        if not block: break
        data = tail+block
        for pattern, _ in PATTERNS:
            positions.update(pos-len(tail)+m.start() for m in pattern.finditer(data))
        pos += len(block); tail = data[-1024:]
    groups = {}
    for a in sorted(positions):
        stream.seek(a); tail = stream.read(4096)
        z = tail.index(0); end = a+z
        groups[end] = min(a, groups.get(end, a))
    result = []
    for end, a in sorted(groups.items()):
        stream.seek(a); before = stream.read(end-a+1)
        after, n = replace_text(before)
        assert n > 0 and len(after) <= len(before) and after != before
        after += bytes(len(before)-len(after))
        result.append((a, before, after, n))
    return result


def compare_story(old_iso, new_iso, platform):
    if platform == 'PSP':
        path = '/PSP_GAME/USRDIR/MAP_ADD.BIN'
        with old_iso.open_file_from_iso(iso_path='/PSP_GAME/SYSDIR/BOOT.BIN') as f: elf = f.read()
        offsets = struct.unpack_from('<204I', elf, build_patch.BLOCK_TABLE)
        spans = [((build_patch.SCRIPT_SECTOR+a)*2048, (b-a)*2048) for a,b in zip(offsets, offsets[1:])]
    else:
        path = '/DATA/MAP.BIN;1'
        with old_iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as f: elf = f.read()
        info=json.loads((PREVIOUS_BASE/'stage30.json').read_text())
        meta=json.loads((PREVIOUS_BASE/'patch.json').read_text())
        table=int(meta['segment_offset'],16)+int(info['script_sector_table_va'],16)-int(meta['segment_va'],16)
        offsets=struct.unpack_from('<204I',elf,table)
        base=struct.unpack_from('<18I',elf,0x37e438)[10]*2048
        spans = [(base+a*2048, (b-a)*2048) for a,b in zip(offsets, offsets[1:])]
        assert len(spans) == 203
    changed = []
    with old_iso.open_file_from_iso(iso_path=path) as a, new_iso.open_file_from_iso(iso_path=path) as b:
        for i, (start, size) in enumerate(spans):
            a.seek(start); b.seek(start); x,y = a.read(size),b.read(size)
            commands, strings = load(x,0); new_commands,new_strings = load(y,0)
            assert commands == new_commands
            ncmd,n,tab = struct.unpack_from('<3I',x,4)
            assert x[:32+48*ncmd] == y[:32+48*ncmd]
            assert x[tab:tab+4*n] == y[tab:tab+4*n]
            assert len(strings) == len(new_strings)
            for slot,(s,t) in enumerate(zip(strings,new_strings)):
                expected,count = replace_text(s.encode('cp932'))
                assert t.encode('cp932') == expected, (platform,i,slot)
                if count: changed.append(dict(block=i,slot=slot,occurrences=count))
    return dict(blocks=len(spans),changed_slots=changed,commands_and_pointers_preserved=True,
                every_unrelated_string_preserved=True)


def build(platform, verify_existing=False):
    prefix = 'SRWMX_EN_' if platform == 'PSP' else 'SRWMX_PS2_EN_'
    source = ROOT/'work/output'/f'{prefix}{BASE_VERSION}.iso'
    output = ROOT/'work/output'/f'{prefix}{VERSION}.iso'
    assert output.exists() if verify_existing else not output.exists(), 'Preserve existing versioned builds'
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = sorted(folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names)
    before = {}; edits = {}; ranges = []
    for p in paths:
        before[p] = file_digest(iso,p)
        with iso.open_file_from_iso(iso_path=p) as f: rows = scan(f)
        if not rows: continue
        edits[p] = rows
        extent = iso.get_record(iso_path=p).extent_location()*2048
        ranges += [(extent+a,old,new) for a,old,new,_ in rows]
    assert sorted(sum(r[3] for r in rows) for rows in edits.values()) == sorted(EXPECTED_COUNTS[platform])
    if not verify_existing:
        shutil.copyfile(source,output)
        with output.open('r+b') as f:
            for start,old,new in ranges:
                f.seek(start); assert f.read(len(old)) == old
                f.seek(start); f.write(new)
    check = pycdlib.PyCdlib(); check.open(str(output)); files = []
    base = ROOT/'work/build'/(f'psp_{TAG}_{VERSION}' if platform == 'PSP' else f'ps2/{TAG}_{VERSION}')
    base.mkdir(parents=True,exist_ok=True)
    for p in paths:
        old_rec,new_rec = iso.get_record(iso_path=p), check.get_record(iso_path=p)
        assert old_rec.extent_location() == new_rec.extent_location() and old_rec.data_length == new_rec.data_length
        h = file_digest(check,p)
        if p not in edits: assert h == before[p]
        with check.open_file_from_iso(iso_path=p) as f: assert not scan(f),p
        if p in edits:
            with check.open_file_from_iso(iso_path=p) as f:
                for start,old,new,_ in edits[p]:
                    f.seek(start); assert f.read(len(new)) == new
            with check.open_file_from_iso(iso_path=p) as f, (base/p.rsplit('/',1)[-1].split(';')[0]).open('wb') as out:
                shutil.copyfileobj(f,out,8*1024*1024)
        udf_ok = False
        if platform == 'PS2':
            # ISO9660 writes DUMMY.;1 while UDF writes DUMMY.
            name = p.rsplit('/',1)[-1].split(';')[0].rstrip('.')
            matches = [folder.rstrip('/')+'/'+str(n) for folder,_,names in check.walk(udf_path='/') for n in names if str(n).lower()==name.lower()]
            assert len(matches)==1,(p,matches)
            with check.open_file_from_iso(udf_path=matches[0]) as f: assert digest(f) == h
            udf_ok = True
        files.append(dict(path=p,original_sha256=before[p],target_sha256=h,changed=p in edits,
                          occurrences=sum(r[3] for r in edits.get(p,[])),udf_readback=udf_ok))
    story = compare_story(iso,check,platform)
    iso.close();check.close()
    # Independently prove no changes outside the terminated text allocations.
    with source.open('rb') as a, output.open('rb') as b:
        last = 0
        for start,old,new in sorted(ranges)+[(source.stat().st_size,b'',b'')]:
            count = start-last
            while count:
                n = min(count,8*1024*1024); assert a.read(n) == b.read(n)
                count -= n
            assert a.read(len(old)) == old and b.read(len(new)) == new
            last = start+len(old)
        assert not a.read(1) and not b.read(1)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),output.with_name(output.stem+'_FONT_LICENSE.txt'))
    with output.open('rb') as f: sha = digest(f)
    report = dict(version=VERSION,base_version=BASE_VERSION,platform=platform,name=NAME,
                  bytes=output.stat().st_size,output=str(output.relative_to(ROOT)),output_sha256=sha,
                  files=files,story=story,no_old_spelling_in_disc=True,all_other_disc_bytes_preserved=True,
                  local_build_only=True,affected_story_playthrough_verified=False,physical_hardware_verified=False,
                  edits={p:[dict(offset=hex(a),allocated_bytes=len(old),occurrences=n,
                                 source_sha256=hashlib.sha256(old).hexdigest(),target_sha256=hashlib.sha256(new).hexdigest())
                            for a,old,new,n in rows] for p,rows in edits.items()})
    save(ROOT/'work/output'/f'{platform.lower()}_{TAG}_{VERSION}_verification.json',report)
    save(base/f'{TAG}.json',report)
    if platform == 'PS2':
        previous = json.loads((ROOT/'work/output'/f'ps2_font_{BASE_VERSION}_verification.json').read_text())
        aggregate = copy.deepcopy(previous)
        lookup = {r['path']:r for r in files}
        for row in aggregate['files']: row['target_sha256']=lookup[row['path']]['target_sha256']
        aggregate['font']['target_sha256']=lookup['/SLPS_253.45;1']['target_sha256']
        aggregate.update(version=VERSION,output=str(output.relative_to(ROOT)),bytes=output.stat().st_size,
                         target_sha256=sha,inherited_execution_checks_from_version=BASE_VERSION,
                         inherited_execution_checks_reason='No instructions or pointers change. Only declared terminated text allocations change in place.',
                         current_correction_report=f'work/output/ps2_{TAG}_{VERSION}_verification.json',
                         source_build_version=BASE_VERSION,
                         source_build_sha256=previous['target_sha256'],
                         changed_from_previous=[r['path'] for r in files if r['changed']],
                         pcsx2_fresh_boot_verified=False)
        # The file bytes are current; update each affected block hash as well.
        elf=(base/'SLPS_253.45' if (base/'SLPS_253.45').exists() else PREVIOUS_BASE/'SLPS_253.45').read_bytes()
        meta=aggregate['font'];info=aggregate['stage30']
        table=int(meta['segment_offset'],16)+int(info['script_sector_table_va'],16)-int(meta['segment_va'],16)
        sectors=struct.unpack_from('<204I',elf,table)
        script_base=struct.unpack_from('<18I',elf,0x37e438)[10]*2048
        changed_blocks={r['block'] for r in story['changed_slots']}
        with (base/'MAP.BIN' if (base/'MAP.BIN').exists() else PREVIOUS_BASE/'MAP.BIN').open('rb') as f:
            for row in aggregate['blocks']:
                i=row['index']
                if i in changed_blocks:
                    f.seek(script_base+sectors[i]*2048)
                    row['new_sha256']=hashlib.sha256(f.read((sectors[i+1]-sectors[i])*2048)).hexdigest()
                    row['text_correction_build']=VERSION
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',aggregate)
        prior_base=PREVIOUS_BASE
        for p in prior_base.iterdir():
            if p.is_file() and p.suffix in ('.BIN','.DAT','.45','.json') and not (base/p.name).exists(): shutil.copyfile(p,base/p.name)
        save(base/'patch.json',aggregate['font'])
        font=ROOT/'work/build/ps2'/f'font_{VERSION}';font.mkdir(exist_ok=True)
        for name in ('SLPS_253.45','patch.json'): shutil.copyfile(base/name,font/name)
    print(platform,VERSION,'verified',sum(r['occurrences'] for r in files),'occurrences;',sha)


def runtime():
    from ppsspp_dbg import Dbg
    from verify_text_build import overflow_table
    from static2_extract import sections
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/'work/output'/f'SRWMX_EN_{VERSION}.iso'))
    with iso.open_file_from_iso(iso_path='/PSP_GAME/SYSDIR/BOOT.BIN') as f:boot=f.read()
    with iso.open_file_from_iso(iso_path='/PSP_GAME/USRDIR/STATIC2_ADD.BIN') as f:static=f.read()
    iso.close()
    encoded=textfit.encode('Albero Est')+b'\0'
    offset=boot.index(encoded);assert boot.find(encoded,offset+1)<0
    table=overflow_table(boot)
    count=json.loads((ROOT/'work/output/psp_text_0.4.14_verification.json').read_text())['overflow']['previous_overflow_entries']+3
    pointers=struct.unpack_from(f'<{count}I',boot,table+96)
    idx=pointers.index(offset-96)
    start,_,names=sections(static)['Strg']
    entries=[i for i in range(names) if struct.unpack_from('<I',static,start+12+4*i)[0]==0x80000000+idx]
    assert len(entries)==1
    with Dbg('ws://127.0.0.1:45394/debugger') as d:
        status=d.call('game.status');assert status['game']['id']=='ULJS00041'
        d.call('cpu.stepping')
        try:
            module=next(m for m in d.call('hle.module.list')['modules'] if m['name']=='SRWMXforPSP')
            base=module['address']
            actual=struct.unpack(f'<{count}I',d.read(base+table,4*count))
            assert actual==tuple(base+p for p in pointers)
            assert d.read(actual[idx],len(encoded))==encoded
        finally:d.call('cpu.resume')
    save(ROOT/'work/output'/f'psp_albero_{VERSION}_runtime.json',
         dict(version=VERSION,game=status['game'],profile='work/build/psp_0414_test',
              fresh_boot=True,native_name='Albero Est',name_table_index=entries[0],
              all_relocated_pointers_verified=count,name_bytes_loaded=True,affected_story_playthrough_verified=False))
    print('PSP fresh boot: Albero Est loaded at the unchanged native name-table pointer.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',action='store_true');parser.add_argument('--build',action='store_true')
    parser.add_argument('--platform',choices=['PSP','PS2'])
    parser.add_argument('--verify-existing',action='store_true');parser.add_argument('--runtime',action='store_true');args=parser.parse_args()
    if args.inputs: inputs()
    if args.build or args.verify_existing:
        for platform in ([args.platform] if args.platform else ('PSP','PS2')): build(platform,args.verify_existing)
    if args.runtime: runtime()
