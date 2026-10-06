"""Prepare, verify and package the local PS2 three-favorites build."""
import argparse
import json
import shutil
import subprocess
import sys
from port_ps2_translations import ROOT, sha
from port_ps2_prologue import save
from ps2_favorites import patch, VERSION

SOURCE_VERSION = '0.1.17'
PREVIOUS = ROOT/'work/build/ps2'/f'forecast_badges_{SOURCE_VERSION}'
BASE = ROOT/'work/build/ps2'/f'favorites_{VERSION}'


def prepare():
    BASE.mkdir(parents=True, exist_ok=True)
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT','.45','.json'):
            shutil.copyfile(path,BASE/path.name)
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    data=(BASE/'SLPS_253.45').read_bytes()
    meta=json.loads((BASE/'patch.json').read_text())
    assert sha(data)==meta['target_sha256']
    data,report=patch(original,data,meta)
    (BASE/'SLPS_253.45').write_bytes(data)
    save(BASE/'patch.json',meta);save(BASE/'favorites.json',report)
    save(ROOT/'work/translation/en/ps2'/f'favorites_{VERSION}.en.json',report)
    return report


def regression():
    # Independent emulators are released between suites (important with the
    # workstation's 32-bit Python runtime and large native asset fixtures).
    for module in ('verify_ps2_favorites','verify_ps2_stage30','verify_ps2_prologue_fix',
                   'verify_ps2_ui','verify_ps2_ui_details','verify_ps2_roster_system','verify_ps2_setup_save'):
        source=f"import sys;sys.path.insert(0,'tools');from pathlib import Path;from {module} import verify;verify(Path({str(BASE)!r}),{VERSION!r})"
        result=subprocess.run([sys.executable,'-c',source],capture_output=True,text=True)
        if result.returncode:
            print(result.stdout);print(result.stderr);raise RuntimeError(module+' failed')
        print(module+': passed',flush=True)
    # Only unrelated instruction ranges precede the appended feature.
    # Preserve prior pixel/weapon test evidence and verify their exact bytes.
    original=(PREVIOUS/'SLPS_253.45').read_bytes();data=(BASE/'SLPS_253.45').read_bytes()
    for tag,suffix in [('weapon_battle','execution'),('map_support','verification'),('forecast_badges','verification')]:
        report=json.loads((ROOT/'work/output'/f'ps2_{tag}_{SOURCE_VERSION}_{suffix}.json').read_text())
        if tag=='weapon_battle':
            feature=json.loads((BASE/'weapon_battle.json').read_text())
            for row in feature['instruction_words']:
                a=int(row['va'],16)-0xff000;assert data[a:a+4]==original[a:a+4]
            for row in feature['storage']:
                a=int(row['va'],16)-0xff000;n=len(bytes.fromhex(row['new']))
                assert data[a:a+n]==original[a:a+n]
        report.update(reused_for_build=VERSION,evidence_source_build=SOURCE_VERSION,
                      reuse_reason='Affected native routines/assets remain byte-identical; favorites hooks are verified separately.')
        save(ROOT/'work/output'/f'ps2_{tag}_{VERSION}_{suffix}.json',report)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');args=parser.parse_args()
    prepare();regression()
    if args.build:
        from package_ps2_stage30 import build
        report=build(BASE,VERSION,SOURCE_VERSION,('WND.BIN','FACEPACK.BIN'))
        previous=json.loads((ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json').read_text())
        old={r['path']:r['target_sha256'] for r in previous['files']}
        changed=[r['path'] for r in report['files'] if r['target_sha256']!=old[r['path']]]
        assert changed==['/SLPS_253.45;1'],changed
        report.update(favorites=json.loads((BASE/'favorites.json').read_text()),
                      favorites_execution_checks=json.loads((ROOT/'work/output'/f'ps2_favorites_{VERSION}_execution.json').read_text()),
                      changed_from_previous=changed)
        report['scope']='English PS2 campaign with PSP extra scenarios, selectable balance and three favorite series in both modes; new games only'
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',report)
