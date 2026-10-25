"""Build both v0.4.47 native artwork candidates with bounded ISO changes."""
import copy
import hashlib
import json
import shutil
from pathlib import Path
import pycdlib
import title_footer
import mx_branding as artwork
from build_title_footer import save

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.4.47'
BASE=ROOT/'work/build/title_credits_0.4.47'


def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def build(platform,recover_existing=False):
    psp=platform=='PSP';base='0.4.42' if psp else '0.4.46'
    prefix='SRWMX_EN_' if psp else 'SRWMX_PS2_EN_'
    source=ROOT/f'work/output/{prefix}{base}.iso';target=ROOT/f'work/output/{prefix}{VERSION}.iso'
    assert target.exists()==recover_existing,'Preserve prior builds; recovery only verifies an interrupted output'
    previous=read(ROOT/f'work/output/psp_dendoh_popup_{base}_verification.json') if psp else read(ROOT/f'work/output/ps2_font_{base}_verification.json')
    expected_source=previous['output_sha256'] if psp else previous['target_sha256']
    stat=source.stat();assert stat.st_size==previous['bytes']
    title_footer.verify_iso(source,platform,base)
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=sorted(folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names)
    positions={p:(iso.get_record(iso_path=p).extent_location()*2048,iso.get_record(iso_path=p).data_length) for p in paths}
    mutations={};reports={}
    def asset(p):
        with iso.open_file_from_iso(iso_path=p) as f:return f.read()
    def register(p,old,new):
        assert len(old)==len(new)==positions[p][1]
        mutations[p]=(old,new)
    im_path='/PSP_GAME/USRDIR/IM_ADD.BIN' if psp else '/DATA/IM.BIN;1'
    old=asset(im_path);new,copyright=artwork.copyright(old,platform)
    new,background=artwork.background(new,platform)
    spans=copyright['pixel_ranges']+background['pixel_ranges'];masked=bytearray(new)
    for a,z in spans:masked[a:z]=old[a:z]
    assert masked==old
    register(im_path,old,new);reports.update(copyright=copyright,story_title_background=background)
    del old,new,masked
    movie_path='/PSP_GAME/USRDIR/MOVIE.BIN' if psp else '/DATA/STRM.BIN;1'
    old=asset(movie_path);new=bytearray(old)
    entries=[(0x2c7d800,'PSP_movie29.pmf','PSP_movie29_english.pmf'),
             (0x460d800,'PSP_movie31.pmf','PSP_movie31_english.pmf')] if psp else [
             (0x931000,'PS2_movie1.bin','PS2_movie1_english.bin'),
             (0x6b55800,'PS2_movie2.bin','PS2_movie2_english.bin')]
    movie_spans=[]
    for offset,original,translated in entries:
        a=(BASE/original).read_bytes();b=(BASE/translated).read_bytes()
        assert len(a)==len(b) and old[offset:offset+len(a)]==a
        new[offset:offset+len(a)]=b;movie_spans.append((offset,offset+len(a)))
    masked=bytearray(new)
    for a,z in movie_spans:masked[a:z]=old[a:z]
    assert masked==old
    register(movie_path,old,bytes(new));del old,new,masked
    footer_path='/PSP_GAME/USRDIR/OPWND.BIN' if psp else '/SLPS_253.45;1'
    old=asset(footer_path);new,footer=title_footer.patch(old,platform,VERSION)
    register(footer_path,old,new)
    if not psp:
        dest=ROOT/f'work/build/ps2/font_{VERSION}';dest.mkdir(parents=True,exist_ok=recover_existing)
        (dest/'SLPS_253.45').write_bytes(new)
        font=copy.deepcopy(previous['font']);font['target_sha256']=sha(new)
        save(dest/'patch.json',font)
    else:title_footer.picture(new,platform).save(artwork.ASSETS/'PSP_menu_logo_and_footer.png')
    changes=sorted((positions[p][0],a,b,p) for p,(a,b) in mutations.items())
    assert all(a+len(b)<=c for (a,b,_,_),(c,_,_,_) in zip(changes,changes[1:]))
    source_hash=hashlib.sha256();expected_hash=hashlib.sha256();at=0
    print(platform,'writing v'+VERSION,'with native artwork, movie captions and exact footer',flush=True)
    with source.open('rb') as src,target.open('rb' if recover_existing else 'xb') as dst:
        while raw:=src.read(8*1024*1024):
            source_hash.update(raw);out=bytearray(raw)
            for offset,original,changed,path in changes:
                a,z=max(at,offset),min(at+len(raw),offset+len(original))
                if a<z:
                    assert raw[a-at:z-at]==original[a-offset:z-offset],path
                    out[a-at:z-at]=changed[a-offset:z-offset]
            if recover_existing:assert dst.read(len(out))==out,'Interrupted output does not match the complete expected transform'
            else:dst.write(out)
            expected_hash.update(out);at+=len(raw)
    assert source_hash.hexdigest()==expected_source
    assert target.stat().st_size==stat.st_size
    print(platform,'verifying complete output and resource readback',flush=True)
    actual=digest(target);assert actual==expected_hash.hexdigest()
    check=pycdlib.PyCdlib();check.open(str(target));changed_resources=[]
    udf_paths={}
    if not psp:
        udf_paths={ (folder.rstrip('/')+'/'+str(n)).upper():folder.rstrip('/')+'/'+str(n)
                    for folder,_,names in check.walk(udf_path='/') for n in names }
    for path in paths:
        r=check.get_record(iso_path=path);assert (r.extent_location()*2048,r.data_length)==positions[path]
    for path,(original,changed) in mutations.items():
        with check.open_file_from_iso(iso_path=path) as f:assert f.read()==changed
        if not psp:
            with check.open_file_from_iso(udf_path=udf_paths[path.split(';')[0].upper()]) as f:assert f.read()==changed
        changed_resources.append(dict(path=path,source_sha256=sha(original),target_sha256=sha(changed),bytes=len(changed)))
    check.close();iso.close()
    assert (source.stat().st_size,source.stat().st_mtime_ns)==(stat.st_size,stat.st_mtime_ns)
    footer['readback']=title_footer.verify_iso(target,platform,VERSION)
    result=dict(version=VERSION,platform=platform,base_version=base,output=target.relative_to(ROOT).as_posix(),
        bytes=stat.st_size,source_sha256=expected_source,output_sha256=actual,footer=footer,
        artwork=reports,movies=read(BASE/'movie_verification.json'),changed_resources=changed_resources,
        all_other_disc_bytes_preserved=True,whole_source_and_output_hash_verified=True,
        resource_sizes_and_locations_unchanged=True,all_changed_resources_read_back=True,
        udf_readback_verified=not psp,source_unchanged=True,emulator_visual_validation='pending',github_release=False)
    save(ROOT/f'work/output/{platform.lower()}_branding_{VERSION}_verification.json',result)
    save(ROOT/f'work/translation/en/{platform.lower()}/branding_{VERSION}.en.json',result)
    save(ROOT/f'work/output/{platform.lower()}_title_footer_{VERSION}_verification.json',dict(version=VERSION,platform=platform,output_sha256=actual,footer=footer))
    if not psp:
        aggregate=copy.deepcopy(previous)
        changed_hashes={r['path']:r['target_sha256'] for r in changed_resources}
        for row in aggregate['files']:
            row['changed']=row['path'] in changed_hashes
            if row['changed']:row['target_sha256']=changed_hashes[row['path']]
        aggregate.update(version=VERSION,output=result['output'],bytes=result['bytes'],target_sha256=actual,
            source_build_version=base,source_build_sha256=expected_source,font=font,title_footer=footer,
            branding=result,current_correction_report=f'work/output/ps2_branding_{VERSION}_verification.json',
            pcsx2_fresh_boot_verified=False,github_release=False)
        save(ROOT/f'work/output/ps2_font_{VERSION}_verification.json',aggregate)
        from verify_ps2_title_footer import main as verify_title
        verify_title(VERSION)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    print('Verified',platform,VERSION,actual,flush=True)
    return result


if __name__=='__main__':
    import sys
    if '--recover-ps2' in sys.argv:build('PS2',True)
    else:
        for platform in ('PSP','PS2'):build(platform)
