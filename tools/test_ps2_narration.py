"""Create a separate portable emulator profile for the corrected crawl."""
import argparse
import configparser
import shutil
from port_ps2_translations import ROOT

PROFILE=ROOT/'work/build/ps2_narration_test_0.4.13'
PREVIOUS=ROOT/'work/build/ps2_favorites_test_0.1.18'
PORT=28029


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
    assert not PROFILE.exists(), 'Existing profile preserved'
    print(f'Copy existing test emulator into {PROFILE}; separate PINE {PORT}, memory cards, logs and states.')
    if args.dry_run:
        print('Dry run: no file writes or emulator launch.');return
    emulator=PROFILE/'emulator';emulator.mkdir(parents=True)
    source=PREVIOUS/'emulator'
    for path in source.iterdir():
        if path.is_file():
            name='mx-narration-test.exe' if path.name=='mx-favorites-test.exe' else path.name
            shutil.copyfile(path,emulator/name)
        elif path.name in ('inis','QtPlugins','resources','translations'):
            shutil.copytree(path,emulator/path.name)
    shutil.copytree(PREVIOUS/'memcards',PROFILE/'memcards')
    for name in ('logs','sstates','snaps','cache','cheats','gamesettings','patches','textures'):
        (emulator/name).mkdir(exist_ok=True)
    ini=emulator/'inis/PCSX2.ini'
    conf=configparser.ConfigParser(interpolation=None,strict=False)
    conf.optionxform=str;conf.read(str(ini),encoding='utf-8-sig')
    conf.set('Folders','MemoryCards',str(PROFILE/'memcards'))
    conf.set('EmuCore','PINESlot',str(PORT));conf.set('EmuCore','EnablePINE','true')
    conf.set('EmuCore','IPCSlot',str(PORT))
    conf.set('EmuCore/GS','LoadTextureReplacements','false')
    conf.set('UI','StartPaused','false');conf.set('UI','PauseOnFocusLoss','false')
    with ini.open('w',encoding='utf-8') as f:conf.write(f)
    print('Prepared isolated portable test profile; no normal emulator settings changed.')


if __name__=='__main__':main()
