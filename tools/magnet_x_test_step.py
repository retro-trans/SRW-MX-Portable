"""Operate only the owned Magnet X test instance and capture native PSP VRAM."""
import sys
from pathlib import Path
from PIL import Image
from ppsspp_dbg import Dbg

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    output=ROOT/'work/ui/psp/magnet_x_0.4.25'/sys.argv[1]
    with Dbg('ws://127.0.0.1:45396/debugger') as d:
        assert d.call('game.status')['game']['id']=='ULJS00041'
        for spec in sys.argv[2:]:
            button,_,wait=spec.partition(':');d.tap(button,wait=float(wait or 0.5))
        d.call('cpu.stepping')
        try:Image.frombytes('RGBA',(512,272),d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272)).save(output)
        finally:d.call('cpu.resume')
    print(output)
