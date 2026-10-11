"""Read native PSP title-menu pixels from an isolated test instance.

No texture replacement, desktop capture or user emulator configuration changes.
The dedicated profile must already be running the exact candidate at the title.
"""
import json
import pycdlib
from PIL import Image
from ppsspp_dbg import Dbg
from title_footer import ROOT, SPECS, sha, verify_iso,layout_spec


def main(version='0.4.23',url='ws://127.0.0.1:45395/debugger',profile=None):
    iso_path=ROOT/f'work/output/SRWMX_EN_{version}.iso'
    verify_iso(iso_path,'PSP',version)
    iso=pycdlib.PyCdlib();iso.open(str(iso_path))
    with iso.open_file_from_iso(iso_path=SPECS['PSP']['asset']) as f:resource=f.read()
    iso.close();o=SPECS['PSP']['offset'];w,h=SPECS['PSP']['size']
    texture=resource[o:o+1024+w*h]
    with Dbg(url) as d:
        status=d.call('game.status');assert status['game']['id']=='ULJS00041'
        d.call('cpu.stepping')
        try:
            ram=d.read(0x08800000,24*1024*1024)
            at=ram.find(texture);assert at>=0, 'Complete candidate title texture not loaded'
            image=Image.frombytes('RGBA',(512,272),d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272))
            dest=ROOT/f'work/ui/psp/title_footer_{version}/title_menu.png'
            image.save(dest)
        finally:d.call('cpu.resume')
    report=dict(version=version,platform='PSP',game=status['game'],fresh_boot=True,
        full_native_title_texture_matches_candidate=True,texture_address=hex(at+0x08800000),
        texture_sha256=sha(texture),footer_screen_box=[v+d for v,d in zip(layout_spec('PSP',version)['box'],[55,5,55,5])],
        screenshot=dest.relative_to(ROOT).as_posix(),screenshot_method='Native PSP VRAM via debugger',
        profile=profile or f'work/build/title_footer_test_{version}',texture_replacement=False,
        user_emulator_configuration_modified=False,physical_hardware_tested=False)
    path=ROOT/f'work/output/psp_title_footer_{version}_runtime.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    import sys
    main(*sys.argv[1:])
