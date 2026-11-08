"""Build a local PSP bonus-window correction over exact public v0.4.47.

Includes the pending .48-.50 registered battle captions and regenerates the
native version footer. Only the two executable copies, registered caption
pixels and footer pixels change. No release is created or published.
"""
import hashlib
import json
import shutil
from pathlib import Path
import pycdlib
import title_footer
from build_title_footer import save
from fix_psp_upgrade_bonus import patch_boot,report,MENUS
from patch_battle_banners import patch as banners,verify_iso as verify_banners
from verify_psp_upgrade_bonus import verify

ROOT=Path(__file__).resolve().parents[1]
VERSION,BASE='0.4.51','0.4.47'


def build():
    source=ROOT/f'work/output/SRWMX_EN_{BASE}.iso'
    target=ROOT/f'work/output/SRWMX_EN_{VERSION}.iso'
    assert source.exists() and not target.exists(),'Preserve existing images'
    manifest=json.loads((ROOT/f'work/output/release-v{BASE}/BUILD-MANIFEST.json').read_text())
    baseline=next(p for p in manifest['patches'] if p['platform']=='PSP')
    stat=(source.stat().st_size,source.stat().st_mtime_ns)
    assert stat[0]==baseline['target_bytes']
    title_footer.verify_iso(source,'PSP',BASE)
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=sorted(folder.rstrip('/')+'/'+str(n) for folder,_,names in iso.walk(iso_path='/') for n in names)
    layout={p:(iso.get_record(iso_path=p).extent_location(),iso.get_record(iso_path=p).data_length) for p in paths}
    def read(p):
        with iso.open_file_from_iso(iso_path=p) as stream:return stream.read()
    boots=('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN')
    static_path='/PSP_GAME/USRDIR/STATIC2_ADD.BIN'
    footer_path='/PSP_GAME/USRDIR/OPWND.BIN'
    original=read(boots[0]);assert original==read(boots[1])
    boot=patch_boot(original);static=read(static_path)
    execution=verify(original,boot,static)
    ui=ROOT/f'work/ui/psp/upgrade_bonus_{VERSION}'
    updated_static,captions=banners(static,'PSP',ui/'captions')
    old_footer=read(footer_path)
    registration=ROOT/f'work/output/psp_title_footer_{BASE}_verification.json'
    if not registration.exists():
        save(registration,dict(version=BASE,platform='PSP',restored_from_verified_iso=True,
             footer=dict(target_region_sha256=title_footer.sha(title_footer.region(old_footer,'PSP',BASE)))))
    footer,footer_report=title_footer.patch(old_footer,'PSP',VERSION)
    assert title_footer.patch(footer,'PSP',VERSION)[0]==footer
    assert patch_boot(boot)==boot and banners(updated_static,'PSP')[0]==updated_static
    code_spans=sorted((s+0x60,s+0x64) for m in MENUS.values() for s in m['sites'])
    resources={p:(original,boot,code_spans) for p in boots}
    resources[static_path]=(static,updated_static,captions['pixel_ranges'])
    resources[footer_path]=(old_footer,footer,footer_report['pixel_ranges'])
    by_offset={}
    for p,(old,new,spans) in resources.items():
        assert len(old)==len(new)==layout[p][1]
        for a,z in spans:
            at=layout[p][0]*2048+a;pair=(old[a:z],new[a:z])
            # This PSP image aliases BOOT and EBOOT to the same disc extent.
            # Verify identical replacements, then write that extent once.
            assert at not in by_offset or by_offset[at]==pair
            by_offset[at]=pair
    edits=[(at,old,new) for at,(old,new) in by_offset.items()]
    edits.sort();assert all(a+len(b)<=c for (a,b,_),(c,_,_) in zip(edits,edits[1:]))
    iso.close()
    print('Writing PSP v'+VERSION+' with native bonus correction, pending captions and exact footer',flush=True)
    source_hash=hashlib.sha256();expected=hashlib.sha256();position=0
    with source.open('rb') as src,target.open('xb') as dst:
        while raw:=src.read(8*1024*1024):
            source_hash.update(raw);new=bytearray(raw);end=position+len(raw)
            for at,old,replacement in edits:
                a,z=max(position,at),min(end,at+len(old))
                if a<z:
                    assert raw[a-position:z-position]==old[a-at:z-at]
                    new[a-position:z-position]=replacement[a-at:z-at]
            dst.write(new);expected.update(new);position=end
    assert source_hash.hexdigest()==baseline['target_sha256']
    assert (source.stat().st_size,source.stat().st_mtime_ns)==stat and target.stat().st_size==stat[0]
    with target.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    assert actual==expected.hexdigest()
    check=pycdlib.PyCdlib();check.open(str(target))
    for p in paths:
        rec=check.get_record(iso_path=p);assert (rec.extent_location(),rec.data_length)==layout[p]
    for p,(_,new,_) in resources.items():
        with check.open_file_from_iso(iso_path=p) as stream:assert stream.read()==new
    check.close()
    footer_report['readback']=title_footer.verify_iso(target,'PSP',VERSION)
    caption_readback=verify_banners(target,'PSP')
    # Native execution covers the exact executable verified by readback above.
    prepared=ROOT/f'work/build/psp/upgrade_bonus_{VERSION}';prepared.mkdir(parents=True,exist_ok=True)
    (prepared/'BOOT.BIN').write_bytes(boot)
    save(prepared/'native_execution.json',execution)
    save(ROOT/f'work/output/psp_upgrade_bonus_{VERSION}_native_execution.json',execution)
    result=dict(version=VERSION,base_version=BASE,platform='PSP',output=target.relative_to(ROOT).as_posix(),
                bytes=position,source_sha256=source_hash.hexdigest(),output_sha256=actual,
                correction=report(),native_execution=execution,footer=footer_report,
                caption_artwork=captions,caption_readback=caption_readback,
                complete_output_hash_verified=True,actual_iso_executable_readback_verified=True,
                iso_resource_layout_unchanged=True,all_other_disc_bytes_preserved=True,
                changed_resources=sorted(resources),allowed_disc_ranges=[[a,a+len(b)] for a,b,_ in edits],
                reporter_save_and_live_confirmation='pending',local_build_only=True,github_release=False)
    save(ROOT/f'work/output/psp_upgrade_bonus_{VERSION}_verification.json',result)
    save(ROOT/f'work/translation/en/psp/upgrade_bonus_{VERSION}.en.json',result)
    save(ROOT/f'work/output/psp_title_footer_{VERSION}_verification.json',dict(version=VERSION,platform='PSP',footer=footer_report))
    license=source.with_name(source.stem+'_FONT_LICENSE.txt')
    if not license.exists():license=ROOT/'incoming/fonts/FONT_LICENSE.txt'
    shutil.copyfile(license,target.with_name(target.stem+'_FONT_LICENSE.txt'))
    print('Verified PSP',VERSION,actual,flush=True)
    return result


if __name__=='__main__':build()
