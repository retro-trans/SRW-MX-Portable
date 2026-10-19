"""Build the local PSP rename fix and the two approved Ritsu lines."""
import hashlib
import json
import shutil
import struct
from contextlib import nullcontext
from pathlib import Path

import pycdlib
import build_patch
import fix_psp_rename
import play_order
import textfit
import title_footer
from build_ps2_dialogue import directory_position
from build_reviewed_ps2 import rebuild_slots
from patch_battle_banners import verify_iso as verify_banners
from verify_psp_rename import verify as verify_native

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.4.38'
BASE='0.4.36'
PREPARED=ROOT/f'work/build/psp/rename_{VERSION}'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(verify_existing=False):
    source=ROOT/f'work/output/SRWMX_EN_{BASE}.iso'
    target=ROOT/f'work/output/SRWMX_EN_{VERSION}.iso'
    assert target.exists()==verify_existing,'Use explicit verification to preserve existing test builds'
    baseline=read(ROOT/f'work/output/psp_battle_banners_{BASE}_verification.json')
    stat=(source.stat().st_size,source.stat().st_mtime_ns)
    assert stat[0]==baseline['bytes']
    title_footer.verify_iso(source,'PSP',BASE)
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=sorted(folder.rstrip('/')+'/'+str(name) for folder,_,names in iso.walk(iso_path='/') for name in names)
    records={p:(iso.get_record(iso_path=p).extent_location(),iso.get_record(iso_path=p).data_length) for p in paths}
    def asset(path):
        with iso.open_file_from_iso(iso_path=path) as f:return f.read()
    old_boot=asset('/PSP_GAME/SYSDIR/BOOT.BIN')
    assert old_boot==asset('/PSP_GAME/SYSDIR/EBOOT.BIN')
    boot=fix_psp_rename.patch_boot(old_boot)
    execution=verify_native(boot,old_boot)
    assert fix_psp_rename.patch_boot(boot)==boot
    PREPARED.mkdir(parents=True,exist_ok=True)
    (PREPARED/'BOOT.BIN').write_bytes(boot)
    save(PREPARED/'native_execution.json',execution)
    # Keep every story block and scene index in place; both revised lines are
    # shorter, so the rebuilt scene fits its existing allocation.
    map_path='/PSP_GAME/USRDIR/MAP_ADD.BIN'
    maps=asset(map_path)
    sections=struct.unpack_from('<18I',boot,build_patch.SECTION_TABLE)
    rel=struct.unpack_from('<204I',boot,build_patch.BLOCK_TABLE)
    inventory=read(ROOT/'work/source/stage_map.json')
    index=next(r['block'] for r in inventory if r['name']=='s0550')
    start,end=[(sections[10]+n)*2048 for n in rel[index:index+2]]
    old=maps[start:end]
    commands,texts=play_order.load(old,0)
    full=read(ROOT/'work/translation/en/script/stage28_campaign_full_merged.json')
    old_lines={497:'...Masato Akitsu... You cannot see it. This face of mine...!',
               520:"I'm done talking. Die... and take the blood of Masaki within you with you...!"}
    replacements={}
    for entry,slot in ((497,400),(520,427)):
        row=next(r for r in full['rows'] if r['id']==entry)
        previous=textfit.fit_dialogue('Ritsu',old_lines[entry])[0]
        rendered,lines,ok=textfit.fit_dialogue('Ritsu',row['en'])
        assert ok and texts[slot]==textfit.encode(previous).decode('cp932')
        replacements[slot]=textfit.encode(rendered)
    new=rebuild_slots(old,replacements)
    assert len(new)<=len(old)
    new=new.ljust(len(old),b'\0')
    story_block=new
    after_commands,after_texts=play_order.load(new,0)
    assert commands==after_commands
    assert [n for n,(a,b) in enumerate(zip(texts,after_texts)) if a!=b]==[400,427]
    footer_path='/PSP_GAME/USRDIR/OPWND.BIN'
    old_footer=asset(footer_path)
    footer_data,footer=title_footer.patch(old_footer,'PSP',VERSION)
    resources={'/PSP_GAME/SYSDIR/BOOT.BIN':boot,'/PSP_GAME/SYSDIR/EBOOT.BIN':boot,
               footer_path:footer_data}
    edits=[(records[map_path][0]*2048+start,old,new),
           (records[footer_path][0]*2048,old_footer,footer_data)]
    extent=stat[0]//2048
    assert stat[0]%2048==0
    appended=boot+bytes(-len(boot)%2048)
    new_records={}
    with source.open('rb') as f:
        for path in ('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN'):
            at=directory_position(iso,source,path)
            f.seek(at+2);before=f.read(16)
            after=struct.pack('<I',extent)+struct.pack('>I',extent)+struct.pack('<I',len(boot))+struct.pack('>I',len(boot))
            edits.append((at+2,before,after));new_records[path]=(extent,len(boot))
        total=(stat[0]+len(appended))//2048
        for sector in range(16,32):
            f.seek(sector*2048);header=f.read(2048)
            if header[1:6]!=b'CD001':continue
            if header[0]==255:break
            if header[0] in (1,2):
                edits.append((sector*2048+80,header[80:88],struct.pack('<I',total)+struct.pack('>I',total)))
    edits.sort();assert all(a+len(b)<=c for (a,b,_),(c,_,_) in zip(edits,edits[1:]))
    iso.close()
    source_hash=hashlib.sha256();expected_hash=hashlib.sha256();position=0
    print('Verifying existing candidate' if verify_existing else 'Writing PSP test image with verified rename fix and v0.4.38 footer',flush=True)
    with source.open('rb') as src,(nullcontext(None) if verify_existing else target.open('xb')) as dst:
        while raw:=src.read(8*1024*1024):
            source_hash.update(raw);result=bytearray(raw);end=position+len(raw)
            for at,old,new in edits:
                left,right=max(position,at),min(end,at+len(old))
                if left<right:
                    assert raw[left-position:right-position]==old[left-at:right-at]
                    result[left-position:right-position]=new[left-at:right-at]
            if dst is not None:dst.write(result)
            expected_hash.update(result);position=end
        if dst is not None:dst.write(appended)
        expected_hash.update(appended)
    assert source_hash.hexdigest()==baseline['output_sha256']
    print('Checking complete PSP image hash and actual ISO resources',flush=True)
    with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert actual==expected_hash.hexdigest()
    assert target.stat().st_size==stat[0]+len(appended)
    assert (source.stat().st_size,source.stat().st_mtime_ns)==stat
    check=pycdlib.PyCdlib();check.open(str(target))
    file_checks=[]
    for path in paths:
        rec=check.get_record(iso_path=path)
        assert (rec.extent_location(),rec.data_length)==new_records.get(path,records[path])
        if path in resources:
            with check.open_file_from_iso(iso_path=path) as f:assert f.read()==resources[path]
        file_checks.append(dict(path=path,changed=path in resources or path==map_path))
    with check.open_file_from_iso(iso_path=map_path) as f:
        f.seek(start);assert f.read(len(story_block))==story_block
    check.close()
    footer['readback']=title_footer.verify_iso(target,'PSP',VERSION)
    result=dict(version=VERSION,platform='PSP',base_version=BASE,output=target.relative_to(ROOT).as_posix(),
        bytes=target.stat().st_size,output_sha256=actual,source_sha256=source_hash.hexdigest(),
        rename=fix_psp_rename.report(),native_execution=execution,footer=footer,
        ritsu_revisions_included=[497,520],only_story_slots_changed=['s0550:400','s0550:427'],
        all_other_original_disc_bytes_preserved=True,files=file_checks,
        native_banner_artwork_preserved=verify_banners(target,'PSP'),
        fresh_in_game_visual_check='pending',github_release=False,local_build_only=True)
    save(ROOT/f'work/output/psp_rename_{VERSION}_verification.json',result)
    save(ROOT/f'work/translation/en/psp/rename_{VERSION}.en.json',result)
    save(ROOT/f'work/output/psp_title_footer_{VERSION}_verification.json',dict(version=VERSION,platform='PSP',footer=footer))
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',target.with_name(target.stem+'_FONT_LICENSE.txt'))
    print('Verified PSP',VERSION,actual,flush=True)


if __name__=='__main__':build()
