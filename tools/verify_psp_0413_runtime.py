"""Check the local candidate after a fresh boot in the owned test emulator."""
import json
import struct
from pathlib import Path
from PIL import Image
from ppsspp_dbg import Dbg
from psp_spirit_footer import FOOTER_PATCHES
from fix_psp_levelup import row_address
from verify_text_build import read_iso

ROOT=Path(__file__).resolve().parents[1]


def main():
    boot=read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.13.iso'),
                  ['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    with Dbg('ws://127.0.0.1:45393/debugger') as d:
        status=d.call('game.status')
        assert status['game']['id']=='ULJS00041'
        d.call('cpu.stepping')
        try:
            module=next(m for m in d.call('hle.module.list')['modules'] if m['name']=='SRWMXforPSP')
            base=module['address']
            for va,old,new in FOOTER_PATCHES:
                assert d.read(base+va,4)==struct.pack('<I',new),hex(va)
            hi=struct.unpack('<I',d.read(base+0xce364,4))[0]&0xffff
            lo=struct.unpack('<h',d.read(base+0xce378,2))[0]
            assert (hi<<16)+lo==base+row_address(boot)
            assert d.read(base+0xce604,4)==boot[0xce604+96:0xce608+96]
            path=ROOT/'work/ui/psp/0.4.13/fresh_boot.png'
            Image.frombytes('RGBA',(512,272),d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272)).save(path)
        finally:d.call('cpu.resume')
    result=dict(version='0.4.13',fresh_boot=True,owned_profile='work/build/psp_0413_test',
                game=status['game'],module=module,footer_instruction_words_verified=len(FOOTER_PATCHES),
                level_up_relocated_buffer_and_stride_verified=True,
                screenshot='work/ui/psp/0.4.13/fresh_boot.png',
                affected_screens_battle_playthrough_verified=False,physical_psp_verified=False)
    (ROOT/'work/output/psp_ui_0.4.13_runtime.json').write_text(json.dumps(result,indent=1),encoding='utf8')
    print('Fresh boot: 21 footer instructions and Level Up buffer/stride verified.')


if __name__=='__main__':main()
