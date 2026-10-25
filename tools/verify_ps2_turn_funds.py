"""Execute the actual map-panel draw and proportional width calculation."""
import copy
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
from verify_ps2_rename import vm,call,cstr
from verify_ps2_difficulty import put
import fix_ps2_turn_funds as fix

OBJ=0x810000


def rendered_pen_end(elf,d):
    """Execute ASCII conversion and every real glyph advance up to GS calls."""
    u=vm(elf);u.mem_write(0x850000,struct.pack('<2f',*d['font'])+bytes(0x50))
    put(u,0x850044,1)  # Suppress the renderer's unrelated randomized shake.
    raw=bytes.fromhex(d['raw']);u.mem_write(0x850100,raw+b'\0');ends=[]
    def service(m,pc,size,user):
        if pc not in (0x12f5b0,0x12f718,0x12f8b8,0x36af24):return
        # Aligned libc strlen has an EE packed-instruction fast path.
        if pc==0x36af24:m.reg_write(r.UC_MIPS_REG_V0,len(cstr(m,m.reg_read(r.UC_MIPS_REG_A0))))
        if pc==0x12f8b8:
            ends.append(struct.unpack('<f',struct.pack('<I',m.reg_read(r.UC_MIPS_REG_F16)&0xffffffff))[0])
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service);u.reg_write(r.UC_MIPS_REG_8,d['flags'])
    call(u,0x130d78,0x850000,0x850100,d['x'],d['y'])
    assert len(ends)==len(raw)
    return ends[-1]


def draw(elf,turn,funds,x=440,y=300,slide=0,visible=True):
    u=vm(elf);put(u,OBJ+0x9c,x);put(u,OBJ+0xa0,y)
    put(u,OBJ+0x200,turn);put(u,OBJ+0x204,funds);put(u,OBJ+0x210,int(visible))
    u.mem_write(OBJ+0x20c,struct.pack('<2h',slide,0))
    call(u,0x1524a8,OBJ)
    u.mem_write(OBJ+0x1a8,struct.pack('<2f',24,24))
    draws=[]
    def service(m,pc,size,user):
        if pc not in (0x12c170,0x144aa0,0x131958,0x36a980,0x130610,0x130d78):return
        if pc==0x36a980:
            fmt=cstr(m,m.reg_read(r.UC_MIPS_REG_A1)).decode('ascii')
            assert fmt in ('%4d','%8d'),fmt
            value=m.reg_read(r.UC_MIPS_REG_A2)&0xffffffff
            raw=(fmt%value).encode('ascii')
            m.mem_write(m.reg_read(r.UC_MIPS_REG_A0),raw+b'\0');m.reg_write(r.UC_MIPS_REG_V0,len(raw))
        if pc in (0x130610,0x130d78):
            ctx=m.reg_read(r.UC_MIPS_REG_A0)
            draws.append(dict(kind='number' if pc==0x130d78 else 'label',
                raw=cstr(m,m.reg_read(r.UC_MIPS_REG_A1)).hex(),
                x=m.reg_read(r.UC_MIPS_REG_A2),y=m.reg_read(r.UC_MIPS_REG_A3),
                font=struct.unpack('<2f',m.mem_read(ctx,8)),flags=m.reg_read(r.UC_MIPS_REG_8)))
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    stack=u.reg_read(r.UC_MIPS_REG_SP)
    for reg,value in ((r.UC_MIPS_REG_S0,101),(r.UC_MIPS_REG_S1,202),(r.UC_MIPS_REG_S2,303)):
        u.reg_write(reg,value)
    call(u,0x152738,OBJ)
    assert u.reg_read(r.UC_MIPS_REG_SP)==stack
    assert [u.reg_read(reg) for reg in (r.UC_MIPS_REG_S0,r.UC_MIPS_REG_S1,r.UC_MIPS_REG_S2)]==[101,202,303]
    width_vm=vm(elf)
    for d in draws:
        width_vm.mem_write(0x850000,struct.pack('<2f',*d['font'])+bytes(0x34))
        width_vm.mem_write(0x850100,bytes.fromhex(d['raw'])+b'\0')
        width=call(width_vm,0x131a88 if d['kind']=='number' else 0x1319c0,0x850000,0x850100)
        d.update(width=width,right_edge=d['x']+width)
    return draws


def verify(original,elf,meta):
    old=draw(original,1,367040)
    nums=[d for d in old if d['kind']=='number']
    assert nums[0]['right_edge']!=nums[1]['right_edge'],'Reported mismatch not reproduced'
    cases=[];rendered=[]
    for turn,funds in ((0,0),(1,367040),(9,9),(10,99),(99,999),(999,999999),
                       (9999,9999999),(99999,99999999),(2147483647,2147483647)):
        for x,y,slide in ((440,300,0),(0,0,0),(440,300,80)):
            ds=draw(elf,turn,funds,x,y,slide)
            labels=[d for d in ds if d['kind']=='label'];nums=[d for d in ds if d['kind']=='number']
            assert len(labels)==len(nums)==2
            assert [int(bytes.fromhex(d['raw'])) for d in nums]==[turn,funds]
            assert nums[0]['right_edge']==nums[1]['right_edge']==x+slide+fix.ANCHOR
            for label,num in zip(labels,nums):
                assert num['x']>label['right_edge'] and num['right_edge']<x+slide+200,(label,num)
                assert num['flags']==0xffffffffffffffff
            assert [d['y'] for d in nums]==[y+6,y+32]
            if (x,y,slide)==(440,300,0):
                ends=[rendered_pen_end(elf,d) for d in nums]
                assert ends==[628,628],(turn,funds,ends)
                rendered.append(dict(turn=turn,funds=funds,actual_glyph_pen_ends=ends))
            cases.append(dict(turn=turn,funds=funds,origin=[x,y],slide=slide,
                              right_edges=[d['right_edge'] for d in nums],label_clearance=True))
    assert not draw(elf,1,367040,visible=False)
    assert fix.patch(elf,copy.deepcopy(meta))[0]==elf
    return dict(passed=True,reported_mismatch_reproduced=True,original_draws=old,cases=cases,
        example_draws=draw(elf,1,367040),native_panel_and_ascii_width_executed=True,
        native_ascii_renderer_glyph_advance_cases=rendered,
        standard_sprintf_and_packed_strlen_services_supplied=True,graphics_draw_arguments_captured=True,
        numeric_values_and_formats_preserved=True,window_visibility_preserved=True,
        stack_and_callee_saved_registers_preserved=True,patch_idempotent=True,
        pcsx2_visual_validation='pending')


if __name__=='__main__':
    import json
    root=Path(__file__).resolve().parents[1]
    base=root/'work/build/ps2/font_0.4.43'
    original=(base/'SLPS_253.45').read_bytes();meta=json.loads((base/'patch.json').read_text())
    elf,meta,info=fix.patch(original,meta)
    result=verify(original,elf,meta)
    print(json.dumps(result,indent=2))
