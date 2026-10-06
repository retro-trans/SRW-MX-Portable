"""Execute the new menu wrappers and the real VWF width routine in Unicorn.

Only GPU drawing is intercepted; native text measurement, argument restoration,
choice-row filtering, pointer getters and the previous crash regressions execute.
"""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.mips_const import *
import fix_psp_menu_alignment as align
import insert_text as it
import verify_psp_0410 as previous
from verify_text_build import resolver
from static2_extract import sections

ROOT = Path(__file__).resolve().parents[1]


def main():
    boot = (ROOT/'work/build/psp_ui_0.4.11/BOOT.fixed.BIN').read_bytes()
    static = (ROOT/'work/build/psp_ui_0.4.11/STATIC2.fixed.BIN').read_bytes()
    titles = json.loads((ROOT/'work/translation/en/static2/music.en.json').read_text())['titles']
    u = previous.machine(boot)
    obj, textptr = 0x1000000, 0x1010000
    draws = []
    def draw(u, pc, size, _):
        if pc != align.DRAW:
            return
        draws.append([u.reg_read(reg) for reg in [UC_MIPS_REG_A0, UC_MIPS_REG_A1,
                                                UC_MIPS_REG_A2, UC_MIPS_REG_A3, UC_MIPS_REG_T0]])
        u.reg_write(UC_MIPS_REG_PC, u.reg_read(UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE, draw)
    samples = {'unit_choices':['Change name','Keep name'],
               'pilot_choices':['Name','Nick','Male /','Change name','Keep name'],
               'options':['Robot Library','Character Library','Sound Select','Demo Select'],
               'demo':['Opening','Grendizer Appears','Getter Dragon Appears'],
               'music':list(titles.values())}
    report, widths = {}, {}
    for name, (site, mode) in align.SITES.items():
        ctx = obj + (0x2A4 if mode == 'panel' else 0x190 if name == 'options' else 0x2A0 if name == 'music' else 0x1FC)
        u.mem_write(obj+0xA0, struct.pack('<III',8,0,475))
        font = 20 if name in ('music','demo') else 16
        u.mem_write(ctx+8,struct.pack('<ff',font,font))
        entry = (struct.unpack_from('<I',boot,site+0x60)[0]&0x3FFFFFF)<<2
        result = []
        for n,text in enumerate(samples[name]):
            u.mem_write(textptr,it.encode(text))
            previous.invoke(u,align.WIDTH,[ctx,textptr])
            width = u.reg_read(UC_MIPS_REG_V0)
            u.reg_write(UC_MIPS_REG_T0,427 if name=='music' else 455 if name=='demo' else 0xFFFFFFFF)
            u.reg_write(UC_MIPS_REG_S1,n)
            previous.invoke(u,entry,[ctx,textptr,111,165+n*21])
            actual = draws[-1]
            center = 348 if mode in ('pilot','setup') else 245 if mode=='panel' else 240
            x = 111 if mode=='pilot' and n<3 else center-width//2
            assert actual == [ctx,textptr,x,165+n*21,427 if name=='music' else 455 if name=='demo' else 0xFFFFFFFF], actual
            assert u.reg_read(UC_MIPS_REG_S1)==n
            if name=='music':
                assert width<=427,(text,width)
                widths[text]=width
            result.append(dict(text=text,width=width,x=x))
        report[name]=result
    get = resolver(static,boot);start,_,_=sections(static)['Strg']
    for idx,text in titles.items():
        off=struct.unpack_from('<I',static,start+12+int(idx)*4)[0]
        assert get(start,off)==it.encode(text)[:-1]
    result = dict(version='0.4.11', menu_rows=report, music_titles_checked=len(titles),
                  maximum_music_width=max(widths.values()), music_width_limit=427,
                  real_native_vwf_executed=True, gpu_draw_intercepted=True,
                  previous_narration=previous.narration(boot),
                  previous_level_up=previous.level_up(boot,True))
    (ROOT/'work/output/psp_fixes_0.4.11_native_tests.json').write_text(json.dumps(result,indent=1))
    print('Native VWF, five wrappers, 80 music titles and previous crash regressions pass.',
          'Maximum music width:',max(widths.values()))


if __name__=='__main__':
    main()
