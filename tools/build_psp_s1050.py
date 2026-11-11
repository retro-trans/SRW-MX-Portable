"""Create a local PSP candidate with the reported stage's allocator fix."""
import hashlib
import json
import shutil
import struct
from contextlib import closing
from pathlib import Path
import pycdlib
import title_footer
from build_ps2_dialogue import directory_position
from build_title_footer import save
from fix_psp_s1050 import patch_boot
from verify_psp_s1050 import verify, CAPTURE
from patch_battle_banners import verify_iso as verify_captions

ROOT=Path(__file__).resolve().parents[1]
BASE,VERSION='0.4.55','0.4.57'
BOOT=('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN')
FOOTER='/PSP_GAME/USRDIR/OPWND.BIN'


def build(source_version=BASE, version=VERSION, feature='s1050'):
    BASE, VERSION = source_version, version
    assert feature in ('s1050', 'difficulty')
    source=ROOT/f'work/output/SRWMX_EN_{BASE}.iso'
    target=ROOT/f'work/output/SRWMX_EN_{VERSION}.iso'
    assert not target.exists(),'Preserve existing ISO candidates'
    prior_path=ROOT/f'work/output/psp_name_consistency_{BASE}_verification.json'
    if feature == 'difficulty':
        prior_path=ROOT/f'work/output/psp_status_rewards_{BASE}_verification.json'
    prior=json.loads(prior_path.read_text())
    stat=(source.stat().st_size,source.stat().st_mtime_ns)
    assert stat[0]==prior['bytes'] and stat[0]%2048==0
    title_footer.verify_iso(source,'PSP',BASE)
    with closing(pycdlib.PyCdlib()) as iso:
        iso.open(str(source))
        paths=[folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names]
        layout={p:(iso.get_record(iso_path=p).extent_location(),iso.get_record(iso_path=p).data_length) for p in paths}
        def asset(p):
            with iso.open_file_from_iso(iso_path=p) as f:return f.read()
        before=asset(BOOT[0]);assert before==asset(BOOT[1])
        feature_info=None
        if feature == 'difficulty':
            from psp_difficulty import patch_boot as patch_difficulty
            from verify_psp_difficulty import verify as verify_difficulty
            boot,feature_info=patch_difficulty(before)
            execution=verify_difficulty(before,boot,feature_info)
        else:
            boot=patch_boot(before);execution=verify(before,boot,CAPTURE.read_bytes())
        old=asset(FOOTER);footer,meta=title_footer.patch(old,'PSP',VERSION)
        assert len(footer)==len(old)
        extent=stat[0]//2048;payload=boot+bytes(-len(boot)%2048)
        expected_layout=dict(layout);edits=[]
        with source.open('rb') as f:
            for p in BOOT:
                at=directory_position(iso,source,p)+2
                f.seek(at);prev=f.read(16)
                edits.append((at,prev,struct.pack('<I',extent)+struct.pack('>I',extent)+struct.pack('<I',len(boot))+struct.pack('>I',len(boot))))
                expected_layout[p]=(extent,len(boot))
            sectors=extent+len(payload)//2048
            for s in range(16,32):
                f.seek(s*2048);record=f.read(2048)
                if record[1:6]!=b'CD001':continue
                if record[0]==255:break
                if record[0] in (1,2):
                    edits.append((s*2048+80,record[80:88],struct.pack('<I',sectors)+struct.pack('>I',sectors)))
        for a,z in meta['pixel_ranges']:edits.append((layout[FOOTER][0]*2048+a,old[a:z],footer[a:z]))
    edits.sort();assert all(a+len(b)<=c for (a,b,_),(c,_,_) in zip(edits,edits[1:]))
    print('Writing local PSP v'+VERSION+' with '+feature,flush=True)
    source_hash=hashlib.sha256();expected=hashlib.sha256();position=0
    with source.open('rb') as src,target.open('xb') as dst:
        while raw:=src.read(8*1024*1024):
            source_hash.update(raw);out=bytearray(raw);end=position+len(raw)
            for at,before,after in edits:
                a,z=max(position,at),min(end,at+len(before))
                if a<z:
                    assert raw[a-position:z-position]==before[a-at:z-at]
                    out[a-position:z-position]=after[a-at:z-at]
            dst.write(out);expected.update(out);position=end
        dst.write(payload);expected.update(payload)
    assert (source.stat().st_size,source.stat().st_mtime_ns)==stat
    assert source_hash.hexdigest()==prior['output_sha256']
    with target.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert actual==expected.hexdigest()
    with closing(pycdlib.PyCdlib()) as iso:
        iso.open(str(target))
        for p,(extent,size) in expected_layout.items():
            rec=iso.get_record(iso_path=p);assert (rec.extent_location(),rec.data_length)==(extent,size),p
        for p,data in [(BOOT[0],boot),(BOOT[1],boot),(FOOTER,footer)]:
            with iso.open_file_from_iso(iso_path=p) as f:assert f.read()==data,p
    meta['readback']=title_footer.verify_iso(target,'PSP',VERSION)
    from patch_battle_banners import regions
    captions=verify_captions(target,'PSP',version=VERSION)
    assert len(captions['captions'])==len(regions('PSP',VERSION))
    save(ROOT/f'work/output/psp_title_footer_{VERSION}_verification.json',dict(version=VERSION,platform='PSP',footer=meta))
    result=dict(version=VERSION,base_version=BASE,platform='PSP',output=target.relative_to(ROOT).as_posix(),
        bytes=target.stat().st_size,source_sha256=source_hash.hexdigest(),output_sha256=actual,
        complete_output_hash_verified=True,all_other_disc_bytes_preserved=True,story_data_unchanged=True,
        actual_executable_readback_verified=True,footer=meta,caption_readback=captions,
        native_execution=execution,local_build_only=True,github_release=False,save_replay='pending')
    if feature_info is not None:
        result['difficulty']=feature_info
        prepared=ROOT/f'work/build/psp/difficulty_{VERSION}'
        prepared.mkdir(parents=True,exist_ok=True)
        (prepared/'BOOT.BIN').write_bytes(boot)
        save(prepared/'patch.json',feature_info)
        save(ROOT/f'work/translation/en/psp/difficulty_{VERSION}.en.json',feature_info)
    save(ROOT/f'work/output/psp_{feature}_{VERSION}_verification.json',result)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    print('Verified PSP',VERSION,actual,flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default=BASE)
    parser.add_argument('--version',default=VERSION)
    parser.add_argument('--feature',choices=['s1050','difficulty'],default='s1050')
    args=parser.parse_args()
    build(args.base,args.version,args.feature)
