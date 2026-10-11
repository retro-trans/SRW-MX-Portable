"""Create a versioned local footer-only build over a previous PSP/PS2 candidate.

python tools/build_title_footer.py --base 0.4.22 --version 0.4.23
The reusable stamp_existing function is for incremental builders, before hashing
their output and writing final verification manifests. It changes no other asset.
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

import pycdlib
from title_footer import ROOT, SPECS, sha, patch, picture, verify_iso, version_key
from patch_wnd_headers import file_digest, digest


def save(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')


def stamp_existing(output, platform, version):
    """Stamp a newly created ISO, then read back actual native pixels.

    Use only before publishing its final hashes. Never call on an older immutable
    candidate: create a new versioned output first. Returns the changed-file hash
    and pixel spans for the caller's preservation checks and final manifest.
    """
    version_key(version); output=Path(output)
    prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    assert output.name==prefix+version+'.iso', 'Output filename/version mismatch'
    native_title=platform=='PS2' and version_key(version)>=(0,4,26)
    path='/SLPS_253.45;1' if native_title else SPECS[platform]['asset']
    iso=pycdlib.PyCdlib();iso.open(str(output))
    with iso.open_file_from_iso(iso_path=path) as f:original=f.read()
    changed,evidence=patch(original,platform,version)
    record=iso.get_record(iso_path=path);extent=record.extent_location()*2048
    assert len(changed)==record.data_length, 'Install first PS2 native footer with build_ps2_title_fix before in-place updates'
    iso.close()
    with output.open('r+b') as f:
        for a,z in evidence['pixel_ranges']:f.seek(extent+a);f.write(changed[a:z])
    evidence['readback']=verify_iso(output,platform,version)
    evidence['disc_extent']=extent
    ui=ROOT/'work/ui'/platform.lower()/f'title_footer_{version}'
    ui.mkdir(parents=True,exist_ok=True)
    if not native_title:
        picture(original,platform).save(ui/'before.png')
        picture(changed,platform).save(ui/'after.png')
    save(ui/'layout.json',evidence)
    base=ROOT/'work/build'/platform.lower()/f'title_footer_{version}'
    base.mkdir(parents=True,exist_ok=True)
    (base/path.rsplit('/',1)[-1].split(';')[0]).write_bytes(changed)
    save(base/'title_footer.json',evidence)
    # Register this exact footer to permit guarded version replacement later.
    save(ROOT/f'work/output/{platform.lower()}_title_footer_{version}_verification.json',
         dict(version=version,platform=platform,footer=evidence))
    assert patch(changed,platform,version)[0]==changed
    return evidence


def build(platform, base, version):
    assert version_key(version)>version_key(base)
    if platform=='PS2' and version_key(version)>=(0,4,26) and version_key(base)<(0,4,26):
        from build_ps2_title_fix import build as install_native
        return install_native(base,version)
    prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    source=ROOT/f'work/output/{prefix}{base}.iso'
    output=ROOT/f'work/output/{prefix}{version}.iso'
    assert source.exists() and not output.exists(), 'Preserve previous versioned images'
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=[folder.rstrip('/')+'/'+str(n) for folder,_,files in iso.walk(iso_path='/') for n in files]
    hashes={p:file_digest(iso,p) for p in paths};iso.close()
    shutil.copyfile(source,output)
    evidence=stamp_existing(output,platform,version);target=evidence['asset']
    verify=pycdlib.PyCdlib();verify.open(str(output));checks=[]
    for path in paths:
        actual=file_digest(verify,path)
        assert actual==(evidence['target_resource_sha256'] if path==target else hashes[path]),path
        checks.append(dict(path=path,sha256=actual,changed=path==target))
    verify.close()
    extent=evidence['disc_extent']
    allowed=[(extent+a,extent+z) for a,z in evidence['pixel_ranges']]
    with source.open('rb') as a,output.open('rb') as b:
        last=0
        for start,end in allowed+[(source.stat().st_size,source.stat().st_size)]:
            remaining=start-last
            while remaining:
                size=min(remaining,8*1024*1024);assert a.read(size)==b.read(size);remaining-=size
            a.seek(end);b.seek(end);last=end
        assert not a.read(1) and not b.read(1)
    assert output.stat().st_size==source.stat().st_size
    with output.open('rb') as f:targetsha=digest(f)
    license=source.with_name(source.stem+'_FONT_LICENSE.txt')
    shutil.copyfile(license,output.with_name(output.stem+'_FONT_LICENSE.txt'))
    report=dict(version=version,base_version=base,platform=platform,footer=evidence,files=checks,
        output=output.relative_to(ROOT).as_posix(),output_sha256=targetsha,bytes=output.stat().st_size,
        all_other_disc_bytes_preserved=True,idempotence_verified=True,
        in_game_visual_validation='pending',local_build_only=True,github_release=False)
    save(ROOT/f'work/output/{platform.lower()}_title_footer_{version}_verification.json',report)
    save(ROOT/'work/translation/en'/platform.lower()/f'title_footer_{version}.en.json',report)
    if platform=='PS2':
        prior=json.loads((ROOT/f'work/output/ps2_font_{base}_verification.json').read_text())
        aggregate=copy.deepcopy(prior)
        for row in aggregate['files']:
            assert hashes[row['path']]==row['target_sha256']
            if row['path']==target:row['target_sha256']=evidence['target_resource_sha256']
        aggregate.update(version=version,output=report['output'],target_sha256=targetsha,
            bytes=report['bytes'],source_build_version=base,source_build_sha256=prior['target_sha256'],
            changed_from_previous=[target],title_footer=evidence,
            current_correction_report=f'work/output/ps2_title_footer_{version}_verification.json',
            inherited_execution_checks_from_version=base,
            inherited_execution_checks_reason='Executable/gameplay resources identical; only native title-footer pixels change.',
            pcsx2_fresh_boot_verified=False,pcsx2_visual_validation='Title footer pending',github_release=False)
        save(ROOT/f'work/output/ps2_font_{version}_verification.json',aggregate)
        font=ROOT/f'work/build/ps2/font_{version}';font.mkdir(parents=True,exist_ok=True)
        if target=='/SLPS_253.45;1':
            aggregate['font']['target_sha256']=evidence['target_resource_sha256']
            shutil.copyfile(ROOT/f'work/build/ps2/title_footer_{version}/SLPS_253.45',font/'SLPS_253.45')
            save(ROOT/f'work/output/ps2_font_{version}_verification.json',aggregate)
        else:shutil.copyfile(ROOT/f'work/build/ps2/font_{base}/SLPS_253.45',font/'SLPS_253.45')
        save(font/'patch.json',aggregate['font'])
    print(platform,version,targetsha,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',required=True);ap.add_argument('--version',required=True)
    ap.add_argument('--platform',choices=SPECS);args=ap.parse_args()
    for platform in ([args.platform] if args.platform else ['PSP','PS2']):build(platform,args.base,args.version)
