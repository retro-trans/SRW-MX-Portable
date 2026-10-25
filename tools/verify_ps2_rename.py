"""Execute PS2 unit-rename loading, editing, export and layout with real code."""
import copy
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from verify_ps2_font import machine
from verify_ps2_difficulty import run,put,word
import fix_ps2_rename as fix

ROOT=Path(__file__).resolve().parents[1]
OBJ,HERO,DEST=0x810000,0x820000,0x830000
GUARD=b'CONTROL-GUARD-012'


def vm(elf):
    # This model supports the EE's scalar conditional moves, including those
    # in JAL/branch delay slots. No instruction substitution is needed here.
    u=machine(elf,r.UC_CPU_MIPS64_5KF);u.reg_write(r.UC_MIPS_REG_GP,0x4c84f0)
    def strcat(m,pc,size,user):
        if pc!=0x36aa10:return
        # This libc implementation uses EE 128-bit packed instructions.
        # Supply only its standard byte-concatenation service; the editor's
        # padding loop, strcpy, strlen and all field arithmetic still execute.
        dest=m.reg_read(r.UC_MIPS_REG_A0);src=m.reg_read(r.UC_MIPS_REG_A1)
        left=cstr(m,dest);right=cstr(m,src)
        m.mem_write(dest+len(left),right+b'\0')
        m.reg_write(r.UC_MIPS_REG_V0,dest)
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,strcat)
    return u


def call(u,pc,*args):
    for reg,arg in zip((r.UC_MIPS_REG_A0,r.UC_MIPS_REG_A1,r.UC_MIPS_REG_A2,r.UC_MIPS_REG_A3),args):u.reg_write(reg,arg)
    run(u,pc);return u.reg_read(r.UC_MIPS_REG_V0)


def cstr(u,at):
    raw=bytes(u.mem_read(at,256));return raw.split(b'\0')[0]


def initialize(elf,route,upgraded,saved=False,custom=None):
    u=vm(elf);put(u,0x3c8cb4,HERO);put(u,HERO+0x5e0,route);put(u,HERO+0x5e4,upgraded)
    u.mem_write(OBJ+0x634,b'\xa5'*48);u.mem_write(OBJ+0x664,GUARD)
    expected=[]
    for field,table in enumerate((0x47d348,0x47d358)):
        raw=cstr(u,word(u,table+(route*2+upgraded)*4))
        if custom is not None:raw=it.encode(custom[field])[:-1]
        expected.append(raw[:30 if field==0 else 16])
        u.mem_write(HERO+(0x90 if field==0 else 0x110)+route*64+upgraded*32,(raw+b'\0').ljust(32,b'\0'))
    call(u,0x15a968,OBJ,int(saved))
    return u,expected


def exported(u,field):
    u.mem_write(DEST,b'\xa5'*64)
    call(u,0x15c5c0,OBJ,field,DEST)
    assert bytes(u.mem_read(DEST+32,16))==b'\xa5'*16
    return cstr(u,DEST)


def slice(u,start,end):
    u.emu_start(start,end,count=20000)
    assert u.reg_read(r.UC_MIPS_REG_PC)==end


def verify(original,elf,meta):
    old,want=initialize(original,0,1)
    assert exported(old,0)!=want[0],'Reported Garmraid corruption not reproduced'
    rows=[]
    for route in (0,1):
        for upgraded in (0,1):
            for saved in (False,True):
                u,want=initialize(elf,route,upgraded,saved)
                for field in (0,1):assert exported(u,field)==want[field],(route,upgraded,saved,field)
                assert bytes(u.mem_read(OBJ+0x664,len(GUARD)))==GUARD
                rows.append(dict(route=route,upgraded=upgraded,saved=saved,full_name_bytes=len(want[0]),reading_bytes=len(want[1])))
    for names in [('ABCDEFGHIJKLMNO','ABCDEFGH'),('Cerberus Ignited','Cerberus')]:
        u,want=initialize(elf,1,1,True,names)
        assert [exported(u,f) for f in (0,1)]==want
        assert bytes(u.mem_read(OBJ+0x664,len(GUARD)))==GUARD
    edits=[]
    for field,text in enumerate(('ABCDEFGHIJKLMNO','ABCDEFGH')):
        for index in (0,len(text)//2,len(text)-1):
            for mode in ('delete','space','type'):
                u,want=initialize(elf,1,1,True,('ABCDEFGHIJKLMNO','ABCDEFGH'))
                put(u,OBJ+0x618,field);put(u,OBJ+0x61c,index)
                u.reg_write(r.UC_MIPS_REG_S4,OBJ)
                other=bytes(u.mem_read(OBJ+(0x653 if field==0 else 0x634),17 if field==0 else 31))
                if mode=='delete':
                    slice(u,0x15bb28,0x15bba8);expected=text[:index]+text[index+1:]
                elif mode=='space':
                    slice(u,0x15bbd4,0x15bc00);expected=(text[:index]+' '+text[index+1:]).rstrip()
                else:
                    u.mem_write(u.reg_read(r.UC_MIPS_REG_SP),it.encode('Z'))
                    for reg,value in ((r.UC_MIPS_REG_S0,112),(r.UC_MIPS_REG_S1,210),
                                      (r.UC_MIPS_REG_S2,16),(r.UC_MIPS_REG_S3,30)):
                        u.reg_write(reg,value)
                    slice(u,0x15b924,0x15b9c4);expected=text[:index]+'Z'+text[index+1:]
                assert exported(u,field)==it.encode(expected)[:-1],(mode,field,index)
                assert bytes(u.mem_read(OBJ+(0x653 if field==0 else 0x634),17 if field==0 else 31))==other
                assert bytes(u.mem_read(OBJ+0x664,len(GUARD)))==GUARD,(mode,field,index,bytes(u.mem_read(OBJ+0x664,len(GUARD))).hex())
                edits.append(dict(mode=mode,field=field,index=index))
    layout=verify_layout(elf)
    assert fix.patch(elf,copy.deepcopy(meta))[0]==elf
    return dict(passed=True,reported_garmraid_corruption_reproduced=True,reset_saved_cases=rows,
        editing_cases=edits,layout=layout,max_length_and_legacy_defaults_pass=True,control_and_other_field_guards_preserved=True,
        native_copy_strlen_padding_loop_export_and_editing_executed=True,
        vector_libc_strcat_service_supplied=True,save_layout_unchanged=True,
        patch_idempotent=True,pcsx2_visual_validation='pending')


def verify_layout(elf):
    u,want=initialize(elf,0,1)
    u.mem_write(OBJ+0x4ec,struct.pack('<2f',24,28))
    u.mem_write(OBJ+0x540,struct.pack('<2f',24,28))
    def width(text,w):
        u.mem_write(0x850000,struct.pack('<2f',w,28)+bytes(0x34))
        u.mem_write(0x850100,it.encode(text))
        call(u,0x131ba0,0x850000,0x850100)
        return struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_MIPS_REG_F0)&0xffffffff))[0]
    nw,rw=width('Name',28),width('Reading',28)
    assert 44+nw<116 and 372+rw<476,(nw,rw)
    baseline=vm((ROOT/'work/source/ps2/SLPS_253.45').read_bytes())
    width_entry=(word(u,0x15ab90)&0x03ffffff)<<2
    width_cases=[]
    for raw in [it.encode(c)[:-1] for c in ' A0Z9az']+[bytes.fromhex(h) for h in ('82a0','889f','8141','8175')]:
        out=[]
        for m,entry in ((baseline,0x157fb8),(u,width_entry)):
            m.mem_write(0x850100,raw+b'\0');call(m,entry,OBJ,0x850100)
            out.append(struct.unpack('<f',struct.pack('<I',m.reg_read(r.UC_MIPS_REG_F0)&0xffffffff))[0])
        expected=16 if raw[0]==0x82 and 0x4f<=raw[1]<0x59 else 14 if raw[0]<0x88 else 20
        assert out[1]==expected,(raw.hex(),out,expected)
        width_cases.append(dict(glyph=raw.hex(),native_original=out[0],private_helper=out[1],expected=expected))
    draws=[]
    def service(m,pc,size,user):
        if pc not in (0x130610,0x131958,0x157b80):return
        if pc==0x130610:
            ctx=m.reg_read(r.UC_MIPS_REG_A0)
            draws.append(dict(text=cstr(m,m.reg_read(r.UC_MIPS_REG_A1)).hex(),
                x=m.reg_read(r.UC_MIPS_REG_A2),y=m.reg_read(r.UC_MIPS_REG_A3),
                font=struct.unpack('<2f',m.mem_read(ctx,8))))
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    put(u,OBJ+0x618,2)
    rows=[]
    for field,x,limit in ((0,116,372),(1,476,625)):
        draws.clear();end=call(u,0x15ab20,OBJ,field,x,18)
        assert len(draws)==(15 if field==0 else 8),(field,draws)
        assert all(x<=d['x']<end for d in draws) and end<limit,(field,end,draws)
        rows.append(dict(field=field,x=x,end=end,underline_draws=len(draws),next_boundary=limit))
    call(u,0x15a968,OBJ,0)
    frames=[]
    for route in (0,1):
        put(u,HERO+0x5e0,route);call(u,0x15a968,OBJ,0)
        draws.clear();call(u,0x15aca0,OBJ)
        values=[d for d in draws if d['x'] in (116,476) and d['y']==18]
        assert len(values)==2,values
        for field,d in enumerate(values):
            raw=exported(u,field)
            assert bytes.fromhex(d['text']).startswith(raw),(field,d,raw.hex())
            u.mem_write(0x850000,struct.pack('<2f',*d['font'])+bytes(0x34))
            u.mem_write(0x850100,raw+b'\0');call(u,0x131ba0,0x850000,0x850100)
            actual=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_MIPS_REG_F0)&0xffffffff))[0]
            assert d['x']+actual<(372 if field==0 else 625),(route,field,actual)
            d['text_width']=actual
        frames.append(dict(route=route,values=values))
    return dict(native_vwf_label_widths=dict(name=nw,reading=rw),labels_clear_values=True,
                private_cell_width_cases=width_cases,native_underline_execution=rows,native_window_draw=frames,
                default_values_and_underlines_clear_adjacent_field=True)


if __name__=='__main__':
    previous=json.loads((ROOT/'work/output/ps2_font_0.4.38_verification.json').read_text(encoding='utf8'))
    original=(ROOT/'work/build/ps2/story_flow_0.4.38_audit/SLPS_253.45').read_bytes()
    elf,meta,info=fix.patch(original,copy.deepcopy(previous['font']))
    result=verify(original,elf,meta)
    base=ROOT/'work/build/ps2/rename_audit';base.mkdir(parents=True,exist_ok=True)
    (base/'SLPS_253.45').write_bytes(elf);(base/'patch.json').write_text(json.dumps(meta,indent=2)+'\n')
    (ROOT/'work/output/ps2_rename_native_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
