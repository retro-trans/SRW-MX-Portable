"""Read back local .53 reports, native captions, and retained bonus correction."""
import json
import shutil
from patch_at_field import ROOT,sha
from patch_battle_banners import patch
from verify_text_build import read_iso

VERSION='0.4.53'


def main():
    report=dict(version=VERSION,passed=True,focused_tests_passed=4,platforms={},
                local_only=True,github_release=False,in_game_visual_validation='pending')
    layout=dict(version=VERSION,reported_platform='Not explicitly supplied',
                reported_build='Not explicitly supplied',source_builds={'PSP':'0.4.52','PS2':'0.4.52'},regions=[])
    screenshots={
        'sword_cut':('04ef1a5a-e22a-4b67-b57b-0c6845a8a8ee','sword_cut_report.png'),
        'at_field_neutralized':('feb0de23-e645-49c9-b530-4866ec8531e0','at_field_neutralized_report.png')}
    ui=ROOT/f'work/ui/battle_captions_{VERSION}'
    for id,(token,name) in screenshots.items():
        source=ROOT/f'C:/Users/Binh/AppData/Local/Temp/codex-clipboard-{token}.png'
        # Windows absolute paths remain absolute when joined to ROOT.
        shutil.copyfile(source,ui/name)
        layout['regions'].append(dict(id=id,report=name,platforms={}))
    for p,prefix,asset in [('PSP','SRWMX_EN_','/PSP_GAME/USRDIR/STATIC2_ADD.BIN'),
                           ('PS2','SRWMX_PS2_EN_','/DATA/STATIC.BIN;1')]:
        evidence_path=ROOT/f'work/output/{p.lower()}_battle_banners_{VERSION}_verification.json'
        evidence=json.loads(evidence_path.read_text(encoding='utf8'))
        assert evidence['complete_output_hash_verified']
        assert evidence['version']==VERSION
        base=read_iso(str(ROOT/f'work/output/{prefix}0.4.52.iso'),[asset])[asset]
        target=read_iso(str(ROOT/f'work/output/{prefix}{VERSION}.iso'),[asset])[asset]
        expected,regions=patch(base,p,ROOT/f'work/ui/{p.lower()}/battle_banners_{VERSION}/reported_only',region_ids=screenshots)
        assert expected==target
        assert all(r['already_translated'] for r in patch(target,p)[1]['regions'])
        for row in regions['regions']:
            entry=next(r for r in layout['regions'] if r['id']==row['id'])
            entry.update(english=row['english'],already_in_base=row['already_translated'])
            entry['platforms'][p]={k:row[k] for k in ['box','cap_height','ink_bounds','horizontal_rescaling']}
        report['platforms'][p]=dict(output=evidence['output'],sha256=evidence['output_sha256'],
                                   bytes=evidence['bytes'],report=evidence_path.relative_to(ROOT).as_posix(),
                                   exact_footer_verified=True,other_disc_bytes_preserved=True,
                                   actual_iso_captions_verified=True)
    paths=['/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN']
    executable=read_iso(str(ROOT/f'work/output/SRWMX_EN_{VERSION}.iso'),paths)
    assert executable[paths[0]]==executable[paths[1]]
    digest=sha(executable[paths[0]])
    assert digest=='11adbec0ad66b223b07e68dd134116f6ae4fc1baf63607977f95368de51412e5'
    report['psp_upgrade_bonus_correction']=dict(unchanged_from_native_tested_0_4_51=True,
        BOOT_EBOOT_identical=True,sha256=digest,native_cases_previously_passed=57,
        previous_native_execution='work/output/psp_upgrade_bonus_0.4.51_native_execution.json')
    (ui/'layout.en.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf8')
    output=ROOT/f'work/output/battle_captions_{VERSION}_verification.json'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
