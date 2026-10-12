"""PSP game-protocol probe for the isolated parts regression profile.

Only emulated PSP buttons, debugger resources and native VRAM are accessed.
No Windows input, capture, user profile or original save is touched.
"""
import argparse
import hashlib
import json
import struct
import time
from pathlib import Path
from PIL import Image
from ppsspp_dbg import Dbg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'work/build/parts_crash_test_0.4.30'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tap', nargs='*', default=[])
    p.add_argument('--capture', default='probe')
    p.add_argument('--hardware', action='store_true', help='Do not interpret VRAM as a software framebuffer')
    p.add_argument('--no-capture', action='store_true', help='Send controller input without pausing the CPU')
    p.add_argument('--memory', action='store_true', help='Save native RAM at a debugger breakpoint')
    a = p.parse_args()
    fixture = ROOT/'incoming/ULJS000410002'
    copied = OUT/'memstick/PSP/SAVEDATA/ULJS000410002'
    hashes = {x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in fixture.iterdir() if x.is_file()}
    assert all(hashlib.sha256((copied/n).read_bytes()).hexdigest()==h for n,h in hashes.items())
    raw = (fixture/'PARAM.SFO').read_bytes()
    keys, values, count = struct.unpack_from('<III',raw,8)
    meta = {}
    for i in range(count):
        k, typ, size, _, v = struct.unpack_from('<HHIII',raw,20+16*i)
        name = raw[keys+k:raw.index(b'\0',keys+k)].decode()
        value = raw[values+v:values+v+size]
        if typ == 0x204:
            meta[name] = value.rstrip(b'\0').decode('utf8','replace')
    (OUT/'fixture.json').write_text(json.dumps(dict(files=hashes,metadata=meta),indent=1))
    print(meta.get('SAVEDATA_DETAIL',''))
    with Dbg('ws://127.0.0.1:45431/debugger') as d:
        assert d.call('game.status')['game']['id'] == 'ULJS00041'
        d.call('input.analog.send', x=0, y=0)
        for button in a.tap:
            d.tap(button, hold=.15, wait=.45)
        if a.no_capture:
            print(d.call('cpu.status'))
            return
        paused = d.is_stepping()
        if not paused:
            d.call('cpu.stepping')
        info = dict(status=d.call('cpu.status'), regs=d.regs())
        (OUT/(a.capture+'.json')).write_text(json.dumps(info, indent=1))
        if a.memory:
            import base64
            raw=d.call('memory.read', address=0x08000000, size=0x02000000,
                       replacements=False, timeout=30)
            (OUT/(a.capture+'.bin')).write_bytes(base64.b64decode(raw['base64']))
        if not a.hardware:
            Image.frombytes('RGBA', (512,272), d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272)).save(OUT/(a.capture+'.png'))
        if not paused:
            d.call('cpu.resume')
        print(a.capture, 'PC', hex(info['regs']['pc']), 'paused', paused)


if __name__ == '__main__':
    main()
