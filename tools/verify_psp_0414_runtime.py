"""Verify newly relocated text pointers after the candidate's isolated fresh boot."""
import json
import base64
import struct
from pathlib import Path
from PIL import Image
from ppsspp_dbg import Dbg
from verify_text_build import read_iso,overflow_table
from psp_spirit_footer import FOOTER_PATCHES
import insert_text as it

ROOT=Path(__file__).resolve().parents[1]


def main():
    boot=read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.14.iso'),
                  ['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    report=json.loads((ROOT/'work/output/psp_text_0.4.14_verification.json').read_text())
    count=report['overflow']['previous_overflow_entries']+3;table=overflow_table(boot)
    expected=struct.unpack_from(f'<{count}I',boot,table+96)
    with Dbg('ws://127.0.0.1:45394/debugger') as d:
        def code(address,size):
            return base64.b64decode(d.call('memory.read',address=address,size=size,
                                          replacements=False)['base64'])
        status=d.call('game.status');assert status['game']['id']=='ULJS00041'
        d.call('cpu.stepping')
        try:
            module=next(m for m in d.call('hle.module.list')['modules'] if m['name']=='SRWMXforPSP')
            base=module['address'];actual=struct.unpack(f'<{count}I',d.read(base+table,count*4))
            assert actual==tuple(base+p for p in expected)
            texts=list(report['new_name'].values())+list(report['music_titles'].values())
            for ptr,text in zip(actual[-3:],texts):assert d.read(ptr,len(it.encode(text)))==it.encode(text)
            sec=it.elf(boot);off,size=struct.unpack_from('<II',boot,sec['.rel.text']+16)
            hi=None;pairs=0
            for va,info in struct.iter_unpack('<II',boot[off:off+size]):
                if info&255==5:hi=va
                elif info&255==6 and hi is not None:
                    hv=struct.unpack_from('<I',boot,hi+96)[0]&65535
                    lv=struct.unpack_from('<h',boot,va+96)[0]
                    if (hv<<16)+lv==table:
                        rh=struct.unpack('<I',code(base+hi,4))[0]&65535
                        rl=struct.unpack('<h',code(base+va,2))[0]
                        assert (rh<<16)+rl==base+table;pairs+=1
            assert pairs==3
            for va,_,word in FOOTER_PATCHES:assert code(base+va,4)==struct.pack('<I',word)
            path=ROOT/'work/ui/psp/0.4.14/fresh_boot.png'
            Image.frombytes('RGBA',(512,272),d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272)).save(path)
        finally:d.call('cpu.resume')
    result=dict(version='0.4.14',fresh_boot=True,game=status['game'],module=module,
                all_overflow_pointer_relocations_verified=count,getter_pairs_verified=pairs,
                new_text_loaded=texts,previous_footer_words_verified=True,
                affected_screen_playthrough_verified=False,hardware_psp_verified=False,
                owned_profile='work/build/psp_0414_test',screenshot='work/ui/psp/0.4.14/fresh_boot.png')
    (ROOT/'work/output/psp_text_0.4.14_runtime.json').write_text(json.dumps(result,indent=1),encoding='utf8')
    print('Fresh boot verifies',count,'relocated pointers, all three getters, and the new text.')


if __name__=='__main__':main()
