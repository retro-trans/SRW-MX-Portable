"""Prepare an isolated native title test; preserve normal emulator settings."""
import configparser
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'work/build/ps2_title_footer_test_0.4.26'
PORT = 28036

def main():
    assert not PROFILE.exists()
    previous = ROOT/'work/build/ps2_library_test_0.4.15'
    emulator = PROFILE/'emulator'
    emulator.mkdir(parents=True)
    for path in (previous/'emulator').iterdir():
        if path.is_file():
            name = 'mx-title-test.exe' if path.suffix == '.exe' else path.name
            shutil.copyfile(path, emulator/name)
        elif path.name in ('inis', 'QtPlugins', 'resources', 'translations'):
            shutil.copytree(path, emulator/path.name)
    shutil.copytree(previous/'memcards', PROFILE/'memcards')
    for name in ('logs','sstates','snaps','cache','cheats','gamesettings','patches','textures'):
        (emulator/name).mkdir(exist_ok=True)
    ini = emulator/'inis/PCSX2.ini'
    conf = configparser.ConfigParser(interpolation=None, strict=False)
    conf.optionxform = str
    conf.read(str(ini), encoding='utf-8-sig')
    for section, key, value in [
        ('Folders','MemoryCards',str(PROFILE/'memcards')),
        ('EmuCore','PINESlot',str(PORT)), ('EmuCore','EnablePINE','true'),
        ('EmuCore','IPCSlot',str(PORT)),
        ('EmuCore/GS','LoadTextureReplacements','false'),
        ('EmuCore/GS','upscale_multiplier','1'),
        ('UI','StartPaused','false'), ('UI','PauseOnFocusLoss','false'),
    ]:
        conf.set(section,key,value)
    with ini.open('w',encoding='utf8') as f: conf.write(f)
    print(emulator/'mx-title-test.exe')

if __name__ == '__main__': main()
