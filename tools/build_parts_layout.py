"""Build local Parts-layout candidates over verified v0.4.34 images."""
import hashlib
import json
import struct
import shutil
from pathlib import Path
import pycdlib
import parts_layout
import title_footer
from patch_at_field import ROOT,sha
from build_title_footer import save
from build_ps2_dialogue import directory_position
from patch_battle_banners import verify_iso as verify_banners

VERSION='0.4.35';BASE='0.4.34'
PREPARED=ROOT/f'work/build/parts_layout_{VERSION}'


def build(platform):
    prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    source=ROOT/f'work/output/{prefix}{BASE}.iso';target=ROOT/f'work/output/{prefix}{VERSION}.iso'
    assert not target.exists(),'Preserve existing builds'
    baseline=json.loads((ROOT/f'work/output/{platform.lower()}_battle_banners_{BASE}_verification.json').read_text())
    stat=(source.stat().st_size,source.stat().st_mtime_ns)
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=sorted(folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names)
    records={p:(iso.get_record(iso_path=p).extent_location(),iso.get_record(iso_path=p).data_length) for p in paths}
    def asset(p):
        with iso.open_file_from_iso(iso_path=p) as f:return f.read()
    resources={};report=json.loads((PREPARED/f'{platform.lower()}.json').read_text())
    if platform=='PSP':
        boot=(PREPARED/'BOOT.BIN').read_bytes()
        for p in ('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN'):
            resources[p]=(asset(p),boot)
        p='/PSP_GAME/USRDIR/STATIC2_ADD.BIN'
        resources[p]=(asset(p),(PREPARED/'STATIC2_ADD.BIN').read_bytes())
    else:
        p='/DATA/FIX00.DAT;1';resources[p]=(asset(p),(PREPARED/'FIX00.DAT').read_bytes())
    footer_path='/PSP_GAME/USRDIR/OPWND.BIN' if platform=='PSP' else '/SLPS_253.45;1'
    old=asset(footer_path);new,footer=title_footer.patch(old,platform,VERSION)
    assert len(old)==len(new)
    resources[footer_path]=(old,new)
    footer['disc_extent']=records[footer_path][0]*2048
    appended=b'';edits=[];new_records={}
    if platform=='PSP':
        # Both executable names resolve to the same identical new PRX payload.
        extent=(stat[0]+2047)//2048
        appended=bytes(extent*2048-stat[0])+boot+bytes(-len(boot)%2048)
        for p in ('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN'):
            at=directory_position(iso,source,p)
            with source.open('rb') as f:f.seek(at+2);before=f.read(16)
            after=struct.pack('<I',extent)+struct.pack('>I',extent)+struct.pack('<I',len(boot))+struct.pack('>I',len(boot))
            edits.append((at+2,before,after));new_records[p]=(extent,len(boot))
        total=(stat[0]+len(appended))//2048
        with source.open('rb') as f:
            for sector in range(16,32):
                f.seek(sector*2048);descriptor=f.read(2048)
                if descriptor[1:6]!=b'CD001':continue
                if descriptor[0]==255:break
                if descriptor[0] in (1,2):
                    edits.append((sector*2048+80,descriptor[80:88],struct.pack('<I',total)+struct.pack('>I',total)))
    for p,(old,new) in resources.items():
        if p in new_records:continue
        assert len(new)==len(old)
        edits.append((records[p][0]*2048,old,new))
    edits.sort();assert all(a+len(b)<=c for (a,b,_),(c,_,_) in zip(edits,edits[1:]))
    iso.close()
    source_hash=hashlib.sha256();expected=hashlib.sha256();position=0
    print(platform,'writing Parts layout and native version footer',flush=True)
    with source.open('rb') as src,target.open('xb') as dst:
        while raw:=src.read(8*1024*1024):
            source_hash.update(raw);out=bytearray(raw);end=position+len(raw)
            for at,old,new in edits:
                left,right=max(position,at),min(end,at+len(old))
                if left<right:
                    assert raw[left-position:right-position]==old[left-at:right-at]
                    out[left-position:right-position]=new[left-at:right-at]
            dst.write(out);expected.update(out);position=end
        dst.write(appended);expected.update(appended)
    assert source_hash.hexdigest()==baseline['output_sha256']
    with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert actual==expected.hexdigest() and target.stat().st_size==stat[0]+len(appended)
    assert (source.stat().st_size,source.stat().st_mtime_ns)==stat
    check=pycdlib.PyCdlib();check.open(str(target));checked=[]
    for p in paths:
        rec=check.get_record(iso_path=p)
        assert (rec.extent_location(),rec.data_length)==new_records.get(p,records[p]),p
        if p in resources:
            with check.open_file_from_iso(iso_path=p) as f:assert f.read()==resources[p][1],p
        checked.append(dict(path=p,layout_preserved=p not in new_records,changed=p in resources))
    udf={}
    if platform=='PS2':
        for p in resources:
            name=p.rsplit('/',1)[-1].split(';')[0].lower()
            matches=[folder.rstrip('/')+'/'+str(n) for folder,_,names in check.walk(udf_path='/') for n in names if str(n).lower()==name]
            assert len(matches)==1
            with check.open_file_from_iso(udf_path=matches[0]) as f:assert f.read()==resources[p][1]
            udf[p]=True
    check.close()
    footer['readback']=title_footer.verify_iso(target,platform,VERSION)
    save(ROOT/f'work/output/{platform.lower()}_title_footer_{VERSION}_verification.json',dict(version=VERSION,platform=platform,footer=footer))
    result=dict(version=VERSION,base_version=BASE,platform=platform,output=target.relative_to(ROOT).as_posix(),
        output_sha256=actual,bytes=target.stat().st_size,source_sha256=source_hash.hexdigest(),
        parts_layout=report,native_execution=json.loads((ROOT/f'work/output/parts_layout_{VERSION}_native_verification.json').read_text())[platform],
        complete_iso_readback_hash_verified=True,unrelated_disc_bytes_preserved=True,
        changed_resources={p:dict(bytes=len(new),sha256=sha(new)) for p,(_,new) in resources.items()},
        native_caption_artwork_retained=verify_banners(target,platform),footer=footer,files=checked,udf_readback=udf,
        local_build_only=True,github_release=False,live_menu_validation='pending')
    save(ROOT/f'work/output/{platform.lower()}_parts_layout_{VERSION}_verification.json',result)
    save(ROOT/f'work/translation/en/{platform.lower()}/parts_layout_{VERSION}.en.json',result)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    if platform=='PS2':
        base=ROOT/f'work/build/ps2/font_{VERSION}';base.mkdir(parents=True,exist_ok=True)
        elf=resources[footer_path][1];(base/'SLPS_253.45').write_bytes(elf)
        meta=json.loads((ROOT/f'work/build/ps2/font_{BASE}/patch.json').read_text());meta['target_sha256']=sha(elf)
        save(base/'patch.json',meta)
    print(platform,VERSION,'verified',actual,flush=True)


if __name__=='__main__':
    for platform in ('PSP','PS2'):build(platform)
