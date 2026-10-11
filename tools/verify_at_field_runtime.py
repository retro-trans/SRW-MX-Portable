"""Check native PSP atlas bytes loaded by an isolated candidate fresh boot."""
import json
from PIL import Image
from patch_at_field import ROOT, SPECS, caption
from ppsspp_dbg import Dbg


def main():
    data = (ROOT/'work/build/psp_at_field_0.4.16/STATIC2_ADD.BIN').read_bytes()
    s = SPECS['PSP']; pal = data[s['palette']:s['palette']+1024]
    with Dbg('ws://127.0.0.1:45394/debugger') as d:
        status = d.call('game.status'); assert status['game']['id'] == 'ULJS00041'
        d.call('cpu.stepping')
        try:
            ram = d.read(0x08800000, 24*1024*1024)
            matches = []; start = 0
            while True:
                off = ram.find(pal, start)
                if off < 0: break
                matches.append(off); start = off+1024
            assert matches, 'Atlas palette not loaded yet'
            candidates = []
            for off in matches:
                atlas = ram[off+1024:off+1024+512*512]
                if atlas == data[s['pixels']:s['pixels']+512*512]: candidates.append(0x08800000+off)
            assert candidates, 'Candidate HUD atlas not found in game RAM'
            Image.frombytes('RGBA',(512,272),d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272)).save(ROOT/'work/ui/psp/at_field_0.4.16/fresh_boot.png')
        finally: d.call('cpu.resume')
    report = dict(version='0.4.16', platform='PSP', fresh_boot=True, game=status['game'],
        complete_native_atlas_matches_iso=True, palette_addresses=[hex(a) for a in candidates],
        emulator_texture_replacement=False, profile='work/build/psp_0414_test',
        actual_at_field_battle_playthrough=False)
    (ROOT/'work/output/psp_at_field_0.4.16_runtime.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('Fresh boot: complete translated HUD atlas loaded from candidate ISO.')


if __name__ == '__main__': main()
