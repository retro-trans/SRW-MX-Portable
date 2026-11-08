"""Prove the release differs from public .47 only by the declared fixes."""
import hashlib
import json
from pathlib import Path
import pycdlib
import title_footer
import patch_battle_banners as banners
import shorten_hm_black_selena as names
import fix_psp_upgrade_bonus as bonus
from verify_psp_upgrade_bonus import verify as verify_bonus
from patch_at_field import ROOT,sha


def read(path):return json.loads(path.read_text(encoding='utf8'))


def main(version='0.4.54'):
    prior=read(ROOT/'work/output/release-v0.4.47/BUILD-TESTS-v0.4.47.json')
    manifest=read(ROOT/'work/output/release-v0.4.47/BUILD-MANIFEST.json')
    assert prior['all_artifact_checks_passed'] and prior['campaign_proofreading_included']
    result=dict(version=version,outputs={},native_iso_footer_readback={},checks={},
                campaign_proofreading_included=True,public_baseline='0.4.47',
                inherited_baseline_artifact_checks='release-v0.4.47/BUILD-TESTS-v0.4.47.json',
                fresh_emulator_visual_validation='pending',physical_console_tested=False,
                complete_playthrough_tested=False,reporter_bonus_save_validation='pending')
    for p,prefix,source in [('PSP','SRWMX_EN_',ROOT/'work/output/SRWMX_EN_0.4.47.iso'),
                            ('PS2','SRWMX_PS2_EN_',ROOT/'work/build/release_baseline_0.4.47/SRWMX_PS2_EN_0.4.47.iso')]:
        target=ROOT/f'work/output/{prefix}{version}.iso'
        current=read(ROOT/f'work/output/{p.lower()}_unit_name_{version}_verification.json')
        old=pycdlib.PyCdlib();old.open(str(source))
        new=pycdlib.PyCdlib();new.open(str(target))
        paths=sorted(folder.rstrip('/')+'/'+str(n) for folder,_,files in old.walk(iso_path='/') for n in files)
        for path in paths:
            a,b=old.get_record(iso_path=path),new.get_record(iso_path=path)
            assert (a.extent_location(),a.data_length)==(b.extent_location(),b.data_length)
        def asset(iso,path):
            with iso.open_file_from_iso(iso_path=path) as f:return f.read()
        static='/PSP_GAME/USRDIR/STATIC2_ADD.BIN' if p=='PSP' else '/DATA/STATIC.BIN;1'
        unit=names.SPECS[p][0]
        footer='/PSP_GAME/USRDIR/OPWND.BIN' if p=='PSP' else '/SLPS_253.45;1'
        before={path:asset(old,path) for path in {static,unit,footer}}
        after=dict(before)
        after[static]=banners.patch(after[static],p)[0]
        after[unit]=names.patch(after[unit],p)[0]
        after[footer]=title_footer.patch(after[footer],p,version)[0]
        if p=='PSP':
            boot='/PSP_GAME/SYSDIR/BOOT.BIN';eboot='/PSP_GAME/SYSDIR/EBOOT.BIN'
            before[boot]=asset(old,boot);after[boot]=bonus.patch_boot(before[boot])
            actual_static=asset(new,static)
            native=verify_bonus(before[boot],asset(new,boot),actual_static)
            assert native['passed'] and len(native['corrected_cases'])==57
            assert asset(new,eboot)==after[boot]
            result['checks']['psp_bonus_native']=native
        edits=[]
        for path,wanted in after.items():
            assert asset(new,path)==wanted,path
            assert len(wanted)==len(before[path])
            edits.append((old.get_record(iso_path=path).extent_location()*2048,before[path],wanted))
        old.close();new.close()
        edits.sort();assert all(a+len(b)<=c for (a,b,_),(c,_,_) in zip(edits,edits[1:]))
        expected=hashlib.sha256();source_hash=hashlib.sha256();position=0
        print(p,'proving the complete public-to-current transformation',flush=True)
        with source.open('rb') as stream:
            while raw:=stream.read(8*1024*1024):
                source_hash.update(raw);out=bytearray(raw);end=position+len(raw)
                for at,a,b in edits:
                    lo,hi=max(position,at),min(end,at+len(a))
                    if lo<hi:
                        assert raw[lo-position:hi-position]==a[lo-at:hi-at]
                        out[lo-position:hi-position]=b[lo-at:hi-at]
                expected.update(out);position=end
        baseline=next(row for row in manifest['patches'] if row['platform']==p)
        assert source_hash.hexdigest()==baseline['target_sha256']==prior['outputs'][p]['sha256']
        assert expected.hexdigest()==current['output_sha256'] and position==target.stat().st_size
        result['outputs'][p]=dict(file=target.name,bytes=position,sha256=expected.hexdigest())
        result['checks'][p+'_baseline_preservation']=dict(public_sha256=source_hash.hexdigest(),
            expected_target_sha256=expected.hexdigest(),all_other_disc_bytes_preserved=True,
            all_file_layouts_preserved=True,changed_resources=sorted(after),
            campaign_commands_and_story_bytes_unchanged=True,branding_and_movies_unchanged=True)
        result['checks'][p+'_captions']=banners.verify_iso(target,p)
        result['checks'][p+'_unit_name']=names.verify_iso(target,p)
        result['native_iso_footer_readback'][p]=title_footer.verify_iso(target,p,version)
        print(p,'public baseline preservation and current native readbacks pass',flush=True)
    regressions=read(ROOT/f'work/output/release_{version}_native_regressions.json')
    assert regressions['passed']
    result['checks']['current_native_regressions']=regressions
    result['all_artifact_checks_passed']=True
    output=ROOT/f'work/output/release_{version}_build_tests.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('Release artifact evidence:',output,flush=True)


if __name__=='__main__':main()
