"""Build and read back local 0.4.22 HUD-only corrections over 0.4.21."""
import copy
import json
import shutil
import sys
import pycdlib
from patch_battle_hud import ROOT, VERSION, patch
from patch_wnd_headers import file_digest, digest
from patch_at_field import sha

BASE='0.4.21'


def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')


def build(platform,verify_existing=False):
    prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    source=ROOT/f'work/output/{prefix}{BASE}.iso';output=ROOT/f'work/output/{prefix}{VERSION}.iso'
    assert output.exists() if verify_existing else not output.exists(), 'Preserve earlier versioned images'
    path='/PSP_GAME/USRDIR/STATIC2_ADD.BIN' if platform=='PSP' else '/DATA/STATIC.BIN;1'
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=[folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names]
    hashes={p:file_digest(iso,p) for p in paths}
    with iso.open_file_from_iso(iso_path=path) as f:original=f.read()
    ui=ROOT/'work/ui'/platform.lower()/f'battle_hud_{VERSION}'
    changed,evidence=patch(original,platform,ui)
    assert all(not r['already_translated'] for r in evidence['regions'])
    assert patch(changed,platform)[0]==changed, 'Patch must be idempotent'
    record=iso.get_record(iso_path=path);extent=record.extent_location()*2048
    assert len(changed)==record.data_length
    iso.close()
    if not verify_existing:
        shutil.copyfile(source,output)
        with output.open('r+b') as f:
            for a,z in evidence['pixel_ranges']:f.seek(extent+a);f.write(changed[a:z])
    check=pycdlib.PyCdlib();check.open(str(output));files=[]
    for p in paths:
        actual=file_digest(check,p);assert actual==(sha(changed) if p==path else hashes[p]),p
        files.append(dict(path=p,sha256=actual,changed=p==path))
    udf=False
    if platform=='PS2':
        matches=[folder.rstrip('/')+'/'+str(n) for folder,_,names in check.walk(udf_path='/') for n in names if str(n).lower()=='static.bin']
        assert len(matches)==1
        with check.open_file_from_iso(udf_path=matches[0]) as f:assert digest(f)==sha(changed)
        udf=True
    with check.open_file_from_iso(iso_path=path) as f:assert f.read()==changed
    check.close()
    with source.open('rb') as a,output.open('rb') as b:
        last=0
        for start,end in [(extent+a,extent+z) for a,z in evidence['pixel_ranges']]+[(source.stat().st_size,source.stat().st_size)]:
            remaining=start-last
            while remaining:
                count=min(remaining,8*1024*1024);assert a.read(count)==b.read(count);remaining-=count
            a.seek(end);b.seek(end);last=end
        assert not a.read(1) and not b.read(1)
    assert output.stat().st_size==source.stat().st_size
    with output.open('rb') as f:targetsha=digest(f)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),output.with_name(output.stem+'_FONT_LICENSE.txt'))
    base=ROOT/'work/build'/platform.lower()/f'battle_hud_{VERSION}';base.mkdir(parents=True,exist_ok=True)
    (base/path.rsplit('/',1)[-1].split(';')[0]).write_bytes(changed);save(base/'battle_hud.json',evidence)
    report=dict(version=VERSION,base_version=BASE,platform=platform,output=output.relative_to(ROOT).as_posix(),
        output_sha256=targetsha,bytes=output.stat().st_size,hud=evidence,files=files,
        all_other_disc_bytes_preserved=True,udf_readback=udf,extracted_previews_verified=True,
        idempotence_verified=True,in_game_visual_validation='pending',local_build_only=True,github_release=False)
    save(ROOT/f'work/output/{platform.lower()}_battle_hud_{VERSION}_verification.json',report)
    save(ROOT/'work/translation/en'/platform.lower()/f'battle_hud_{VERSION}.en.json',report)
    if platform=='PS2':
        prior=json.loads((ROOT/f'work/output/ps2_font_{BASE}_verification.json').read_text())
        aggregate=copy.deepcopy(prior)
        for row in aggregate['files']:
            assert hashes[row['path']]==row['target_sha256']
            if row['path']==path:row['target_sha256']=sha(changed)
        aggregate.update(version=VERSION,output=report['output'],target_sha256=targetsha,bytes=report['bytes'],
            source_build_version=BASE,source_build_sha256=prior['target_sha256'],changed_from_previous=[path],
            battle_hud=evidence,current_correction_report=f'work/output/ps2_battle_hud_{VERSION}_verification.json',
            inherited_execution_checks_from_version=BASE,
            inherited_execution_checks_reason='Executable and gameplay resources are byte-identical; only the declared HUD pixel rectangles change.',
            pcsx2_fresh_boot_verified=False,pcsx2_visual_validation='Battle HUD pending',github_release=False)
        save(ROOT/f'work/output/ps2_font_{VERSION}_verification.json',aggregate)
        font=ROOT/f'work/build/ps2/font_{VERSION}';font.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/f'work/build/ps2/font_{BASE}/SLPS_253.45',font/'SLPS_253.45');save(font/'patch.json',aggregate['font'])
    print(platform,VERSION,targetsha,flush=True)


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--platform',choices=['PSP','PS2']);ap.add_argument('--verify-existing',action='store_true');args=ap.parse_args()
    for platform in ([args.platform] if args.platform else ['PSP','PS2']):build(platform,args.verify_existing)
