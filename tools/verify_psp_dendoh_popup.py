"""Execute the actual Dendoh setup/draw routines and native VWF measurement."""
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from verify_psp_0410 import machine,invoke,cstr
from fix_psp_dendoh_popup import patch_boot,SITE,OLD_WIDTH,NEW_WIDTH

ROOT=Path(__file__).resolve().parents[1]
NAMES=('Full Armor Dendoh','GEAR Fighter Dendoh')


def execute(boot,selection=0):
    u=machine(boot);obj=0x1000000
    u.mem_write(obj,bytes(0x400));u.mem_write(obj+0x300,b'UNTOUCHED-GUARD')
    invoke(u,0x1b193c,[obj]) # Real two-row option initializer, including translated pointers.
    invoke(u,0xaeaa4,[obj+0x1a8]) # Native font context initializer.
    u.mem_write(obj+0x194,struct.pack('<I',selection))
    calls=[];draws=[]
    def service(m,pc,size,user):
        if pc not in (0x21f3bc,0x201778,0x21f4c8,0xaeb08):return
        args=[m.reg_read(reg) for reg in (r.UC_MIPS_REG_A0,r.UC_MIPS_REG_A1,r.UC_MIPS_REG_A2,r.UC_MIPS_REG_A3,r.UC_MIPS_REG_T0)]
        if pc==0xaeb08:
            text=cstr(m,args[1])
            draws.append(dict(text_hex=text.hex(),x=args[2],y=args[3],font_context=bytes(m.mem_read(args[0],16)).hex()))
        else:calls.append(dict(pc=hex(pc),args=args))
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    invoke(u,0x1b1994,[obj]) # Width, automatic centering and highlight setup execute unchanged.
    x,y,width,height=struct.unpack('<4I',u.mem_read(obj+0xa0,16))
    assert width in (OLD_WIDTH,NEW_WIDTH) and x==(480-width)//2
    assert height==50 and y==(272-height)//2
    invoke(u,0x1b12f0,[obj]) # Native frame and both option draws.
    assert len(draws)==2
    for name,draw in zip(NAMES,draws):
        assert draw['text_hex']==it.encode(name)[:-1].hex()
        context=bytes.fromhex(draw['font_context'])
        assert struct.unpack('<4f',context)==(18,18,15,15)
        u.mem_write(0x1010000,it.encode(name))
        invoke(u,0xb03e4,[obj+0x1a8,0x1010000])
        draw.update(text=name,width=u.reg_read(r.UC_MIPS_REG_V0))
        draw['fits']=draw['x']>=x+8 and draw['x']+draw['width']<=x+width-8
    setup=next(c for c in calls if c['pc']=='0x21f3bc')['args']
    assert setup[1:]==[x,y+8+selection*17,width,17]
    assert any(c['pc']=='0x201778' for c in calls)
    assert struct.unpack('<I',u.mem_read(obj+0x200,4))[0]==2
    assert bytes(u.mem_read(obj+0x300,15))==b'UNTOUCHED-GUARD'
    return dict(selection=selection,x=x,y=y,width=width,height=height,draws=draws,
                highlight=dict(x=setup[1],y=setup[2],width=setup[3],height=setup[4]))


def verify(original,patched):
    assert patch_boot(original)==patched and patch_boot(patched)==patched
    restored=bytearray(patched);restored[SITE+0x60:SITE+0x64]=original[SITE+0x60:SITE+0x64]
    assert restored==original,'Unexpected unrelated executable change'
    before=[execute(original,n) for n in (0,1)]
    after=[execute(patched,n) for n in (0,1)]
    assert any(not d['fits'] for row in before for d in row['draws'])
    assert all(d['fits'] for row in after for d in row['draws'])
    return dict(passed=True,old_overflow_reproduced=True,before=before,after=after,
        only_width_instruction_changed=True,font_choices_and_object_guards_preserved=True,
        native_setup_draw_width_and_highlight_executed=True,in_game_validation='pending')


if __name__=='__main__':
    source=ROOT/'work/build/psp/sortie_popup_audit/BOOT.BIN'
    raw=source.read_bytes();result=verify(raw,patch_boot(raw))
    out=ROOT/'work/output/psp_dendoh_popup_native_verification.json'
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))
