"""Preview, verify and build the PS2 narration clipping correction; local only."""
import argparse
import json
import shutil
import subprocess
import sys
from port_ps2_translations import ROOT,sha,read_json
from port_ps2_prologue import save
from ps2_narration_port import patch

VERSION='0.4.13'
SOURCE_VERSION='0.1.18'  # Byte-identical to shared public PS2 0.4.12.
PREVIOUS=ROOT/'work/build/ps2/favorites_0.1.18'
BASE=ROOT/'work/build/ps2'/f'narration_{VERSION}'


def prepare(dry_run=False,resume=False):
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    data=(PREVIOUS/'SLPS_253.45').read_bytes();meta=read_json(PREVIOUS/'patch.json')
    assert sha(data)==meta['target_sha256']
    changed,report=patch(original,data,meta)
    report.update(version=VERSION,source_build=SOURCE_VERSION,source_public_version='0.4.12',
                  source_sha256=sha(data),target_sha256=sha(changed))
    for name in ('opening','ending'):
        group=report[name]
        print(f'{name}: {group["translated_lines"]} lines; max {max(r["native_width_px"] for r in group["lines"])} / {group["width_limit"]} native pixels')
        print('Sample: '+group['lines'][min(10,len(group['lines'])-1)]['english'])
    if dry_run:
        print('Dry run: rebuilt in memory; no files or emulator changes.')
        return report
    if BASE.exists():
        assert resume and not (ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso').exists(), 'Existing build preserved'
        prior=read_json(BASE/'narration.json')
        assert prior['version']==VERSION and prior['source_sha256']==sha(data)
        assert sha((BASE/'SLPS_253.45').read_bytes())==prior['target_sha256']
    else:BASE.mkdir(parents=True)
    for source in PREVIOUS.iterdir():
        if source.suffix in ('.BIN','.DAT','.45','.json'):shutil.copyfile(source,BASE/source.name)
    (BASE/'SLPS_253.45').write_bytes(changed)
    save(BASE/'patch.json',meta);save(BASE/'narration.json',report)
    save(ROOT/'work/translation/en/ps2'/f'narration_{VERSION}.en.json',report)
    return report


def regression():
    for module in ('verify_ps2_narration','verify_ps2_stage30','verify_ps2_favorites',
                   'verify_ps2_prologue_fix','verify_ps2_ui','verify_ps2_ui_details',
                   'verify_ps2_roster_system','verify_ps2_setup_save'):
        source=f"import sys;sys.path.insert(0,'tools');from pathlib import Path;from {module} import verify;verify(Path({str(BASE)!r}),{VERSION!r})"
        result=subprocess.run([sys.executable,'-X','utf8','-c',source],capture_output=True,text=True)
        if result.returncode:
            print(result.stdout);print(result.stderr);raise RuntimeError(module+' failed')
        print(module+': passed',flush=True)
    # Preserve explicit evidence for unchanged drawing functions and artwork.
    for tag,suffix in [('weapon_battle','execution'),('map_support','verification'),('forecast_badges','verification')]:
        report=read_json(ROOT/'work/output'/f'ps2_{tag}_{SOURCE_VERSION}_{suffix}.json')
        report.update(reused_for_build=VERSION,evidence_source_build=SOURCE_VERSION,
                      reuse_reason='Narration verification proves all prior code except ELF/heap size words and both timed pointer tables is byte-identical; every non-executable payload is preserved.')
        save(ROOT/'work/output'/f'ps2_{tag}_{VERSION}_{suffix}.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--build',action='store_true')
    parser.add_argument('--resume',action='store_true',help='Resume this owned, unpublished candidate after a failed check')
    args=parser.parse_args()
    narration=prepare(args.dry_run,args.resume)
    if args.dry_run:return
    regression()
    if args.build:
        from package_ps2_stage30 import build
        report=build(BASE,VERSION,SOURCE_VERSION,('WND.BIN','FACEPACK.BIN'))
        previous=read_json(ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json')
        old={r['path']:r['target_sha256'] for r in previous['files']}
        changed=[r['path'] for r in report['files'] if r['target_sha256']!=old[r['path']]]
        assert changed==['/SLPS_253.45;1'],changed
        report.update(narration_corrections=narration,
                      narration_execution_checks=read_json(ROOT/'work/output'/f'ps2_narration_{VERSION}_execution.json'),
                      favorites=read_json(BASE/'favorites.json'),
                      favorites_execution_checks=read_json(ROOT/'work/output'/f'ps2_favorites_{VERSION}_execution.json'),
                      changed_from_previous=changed,source_public_version='0.4.12',
                      pcsx2_visual_validation='pending for narration',github_release=False)
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',report)


if __name__=='__main__':main()
