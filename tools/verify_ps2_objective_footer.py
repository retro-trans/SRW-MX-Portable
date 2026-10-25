"""Run the native Objectives footer and both actual text renderers."""
import copy
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from verify_ps2_rename import vm,call,cstr
from verify_ps2_difficulty import put
import fix_ps2_objective_footer as fix

OBJ=0x810000
TITLE='Shine of the Red Dragon'


def draw(elf,chapter,x=12,y=38):
    u=vm(elf);put(u,OBJ+0x9c,x);put(u,OBJ+0xa0,y)
    put(u,OBJ+0x230,chapter);put(u,OBJ+0x234,0x850100)
    u.mem_write(0x850100,it.encode(TITLE));seen=[]
    def service(m,pc,size,user):
        if pc==0x36a980:
            fmt=cstr(m,m.reg_read(r.UC_MIPS_REG_A1)).decode('ascii')
            raw=(fmt%m.reg_read(r.UC_MIPS_REG_A2)).encode('ascii')
            m.mem_write(m.reg_read(r.UC_MIPS_REG_A0),raw+b'\0')
            m.reg_write(r.UC_MIPS_REG_V0,len(raw))
        elif pc in (0x130610,0x130d78):
            ctx=m.reg_read(r.UC_MIPS_REG_A0)
            seen.append(dict(renderer=hex(pc),raw=cstr(m,m.reg_read(r.UC_MIPS_REG_A1)).hex(),
                x=m.reg_read(r.UC_MIPS_REG_A2),y=m.reg_read(r.UC_MIPS_REG_A3),
                font=list(struct.unpack('<2f',m.mem_read(ctx,8))),flags=m.reg_read(r.UC_MIPS_REG_8)))
        else:return
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    stack=u.reg_read(r.UC_MIPS_REG_SP)
    saved=(r.UC_MIPS_REG_S0,r.UC_MIPS_REG_S1,r.UC_MIPS_REG_F20)
    for reg,val in zip(saved,(101,202,0x41200000)):u.reg_write(reg,val)
    before=bytes(u.mem_read(OBJ+0x200,0x3c))
    call(u,0x153dd8,OBJ)
    assert u.reg_read(r.UC_MIPS_REG_SP)==stack
    assert [u.reg_read(reg) for reg in saved]==[101,202,0x41200000]
    assert bytes(u.mem_read(OBJ+0x200,0x3c))==before
    return seen


def geometry(elf,d):
    u=vm(elf);ctx,txt=0x850000,0x850100
    u.mem_write(ctx,struct.pack('<2f',*d['font'])+bytes(0x50));put(u,ctx+0x44,1)
    raw=bytes.fromhex(d['raw']);u.mem_write(txt,raw+b'\0');glyphs=[]
    def f(m,n):return struct.unpack('<f',struct.pack('<I',m.reg_read(getattr(r,'UC_MIPS_REG_F'+str(n)))&0xffffffff))[0]
    def service(m,pc,size,user):
        if pc==0x12f8c0:
            # Let the real sprite geometry hook run before capturing its result.
            glyphs.append(dict(top=f(m,13),bottom=f(m,15),
                               left=f(m,12),right=f(m,16),texture_cell=m.reg_read(r.UC_MIPS_REG_A1)))
            # The native hook has executed the GS routine's stack prologue.
            m.reg_write(r.UC_MIPS_REG_SP,m.reg_read(r.UC_MIPS_REG_SP)+0x3a0)
        elif pc==0x36af24:m.reg_write(r.UC_MIPS_REG_V0,len(cstr(m,m.reg_read(r.UC_MIPS_REG_A0))))
        elif pc not in (0x12f5b0,0x12f718):return
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service);u.reg_write(r.UC_MIPS_REG_8,d['flags'])
    call(u,int(d['renderer'],16),ctx,txt,d['x'],d['y'])
    assert glyphs
    for g in glyphs:
        g['size']=g['bottom']-g['top']
        g['baseline']=g['top']+g['size']*74/96
        assert g['texture_cell']==96
    return glyphs


def verify(original,elf,meta):
    old=draw(original,31);new=draw(elf,31)
    assert old[-1]['font']==[16,24] and new[-1]['font']==new[0]['font']==[20,24]
    prior_title,prior_number=geometry(original,old[0]),geometry(original,old[-1])
    title,number=geometry(elf,new[0]),geometry(elf,new[-1])
    assert prior_title==title and prior_number[0]['size']==16
    assert prior_number[0]['baseline']!=prior_title[0]['baseline']
    assert {g['size'] for g in title+number}=={20}
    assert len({g['baseline'] for g in title+number})==1
    cases=[]
    for chapter in (0,1,9,10,28,30,31,54,55,99):
        for x,y in ((12,38),(0,0),(28,64)):
            a,b=draw(original,chapter,x,y),draw(elf,chapter,x,y)
            assert len(a)==len(b)
            for p,q in zip(a,b):
                if p['renderer']=='0x130d78':
                    assert p['raw']==q['raw'] and int(bytes.fromhex(q['raw']))==chapter
                    assert q==dict(p,font=[20,24])
                    assert q['y']==b[0]['y'] and q['x']+40<b[0]['x']
                else:assert p==q
            assert (chapter<55)==any(d['renderer']=='0x130d78' for d in b)
            cases.append(dict(chapter=chapter,origin=[x,y],draws=b))
    assert fix.patch(elf,copy.deepcopy(meta))[0]==elf
    assert len(original)==len(elf)
    # The build separately protects all other bytes and regenerates its footer.
    assert sum(a!=b for a,b in zip(original[:0x2bef18],elf[:0x2bef18]))==1
    return dict(passed=True,native_footer_cases=cases,
                original_mismatch_reproduced=True,original_number_geometry=prior_number,
                title_geometry=title,corrected_number_geometry=number,
                actual_ascii_sjis_and_sprite_hooks_executed=True,
                same_glyph_size_and_baseline=True,chapter_values_titles_and_origins_preserved=True,
                late_game_footer_branch_preserved=True,stack_registers_and_campaign_fields_preserved=True,
                patch_idempotent=True,pcsx2_visual_validation='pending')


if __name__=='__main__':
    base=Path(__file__).resolve().parents[1]/'work/build/ps2/font_0.4.45'
    original=(base/'SLPS_253.45').read_bytes();meta=json.loads((base/'patch.json').read_text())
    elf,meta,info=fix.patch(original,meta)
    report=verify(original,elf,meta)
    print(json.dumps({k:v for k,v in report.items() if k!='native_footer_cases'},indent=2))
