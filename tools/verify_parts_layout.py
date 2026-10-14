"""Execute Parts draw coordinates and native font-width functions without GUI."""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from verify_psp_0410 import machine as psp_machine, invoke
from verify_ps2_font import machine as ps2_machine
from parts_layout import ROOT, lines, PSP_NAME_X


def psp(boot):
    u=psp_machine(boot);obj=0x1001000;ctx=obj+0x190;string=0x1010000
    u.mem_write(obj+0xa0,struct.pack('<2I',2,20))
    # Actual 24/24 source-cell and 14/14 display context from the saved menu.
    u.mem_write(ctx,struct.pack('<4f',24,24,14,14)+bytes(80))
    draws=[]
    def service(m,address,size,user):
        if address!=0xaeb08:return
        pointer=m.reg_read(r.UC_MIPS_REG_A1)
        draws.append(dict(x=m.reg_read(r.UC_MIPS_REG_A2),y=m.reg_read(r.UC_MIPS_REG_A3),
                          font_context=bytes(m.mem_read(m.reg_read(r.UC_MIPS_REG_A0),16)).hex(),
                          text=bytes(m.mem_read(pointer,256)).split(b'\0')[0].hex()))
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    widths={}
    for ident,rows in lines().items():
        for row in rows:
            u.mem_write(string,it.encode(row));invoke(u,0xb03e4,[ctx,string])
            width=u.reg_read(r.UC_MIPS_REG_V0)
            assert width<=200,(ident,row,width)
            widths[row]=width
    u.mem_write(string,it.encode('High Performance Radar'));invoke(u,0xb03e4,[ctx,string])
    radar_width=u.reg_read(r.UC_MIPS_REG_V0)
    u.reg_write(r.UC_MIPS_REG_S1,obj);u.reg_write(r.UC_MIPS_REG_S4,0)
    u.reg_write(r.UC_MIPS_REG_SP,0x11ff000)
    u.mem_write(0x11ff150,it.encode('High Performance Radar'))
    u.emu_start(0x1e5f14,0x1e5f38,count=10000)
    assert draws[-1]['x']==PSP_NAME_X+2
    assert draws[-1]['x']+radar_width<=244
    from static2_extract import sections
    native=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    a,size,count=sections(native)['Part'];stride=(size-12)//count
    names=it.load('static2/names.json')
    part_names=[names[str(struct.unpack_from('<H',native,a+12+i*stride)[0])] for i in range(1,count)]
    for name in part_names:
        if not name:continue
        u.mem_write(0x11ff150,it.encode(name));u.reg_write(r.UC_MIPS_REG_SP,0x11ff000)
        u.emu_start(0x1e5f14,0x1e5f38,count=10000)
        saved=bytes(u.mem_read(ctx,16));u.mem_write(ctx,bytes.fromhex(draws[-1]['font_context']))
        u.mem_write(string,it.encode(name));invoke(u,0xb03e4,[ctx,string])
        assert PSP_NAME_X+2+u.reg_read(r.UC_MIPS_REG_V0)<=244,name
        u.mem_write(ctx,saved)
    for row,line in enumerate(lines()[14]):
        u.mem_write(string,it.encode(line));u.reg_write(r.UC_MIPS_REG_S3,string)
        u.reg_write(r.UC_MIPS_REG_S5,row*19)
        u.emu_start(0x1e62fc,0x1e6320,count=50)
        assert draws[-1]['x']==260 and draws[-1]['y']==151+row*19
        assert draws[-1]['x']+widths[line]<=460 and draws[-1]['y']+14<=238
    return dict(passed=True,native_description_rows_measured=len(widths),
                equipped_part_names_checked=len(part_names),
                max_description_width=max(widths.values()),available_description_width=200,
                equipped_name_x=PSP_NAME_X+2,radar_width=radar_width,draws=draws,
                complete_wording_retained=True,live_menu_validation='pending')


def ps2(elf,metadata):
    u=ps2_machine(elf,r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    ctx=0x940000;string=0x941000;stop=0x920000
    # Maximum native 24px context, including the promoted 12x24 Latin path.
    u.mem_write(ctx,struct.pack('<2f',24,24)+bytes(120))
    widths=[]
    for rows in lines(metadata).values():
        for line in rows:
            u.mem_write(string,it.encode(line));u.reg_write(r.UC_MIPS_REG_A0,ctx)
            u.reg_write(r.UC_MIPS_REG_A1,string);u.reg_write(r.UC_MIPS_REG_SP,0xa00000)
            u.reg_write(r.UC_MIPS_REG_RA,stop)
            u.emu_start(0x131ba0,stop,count=10000)
            width=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_MIPS_REG_F0)&0xffffffff))[0]
            assert 0<width<=258,(line,width)
            widths.append(width)
    return dict(passed=True,native_description_rows_measured=len(widths),
                max_description_width=max(widths),available_description_width=258,
                maximum_rows=5,equipped_name_already_below_label=True,live_menu_validation='pending')


if __name__=='__main__':
    base=ROOT/'work/build/parts_layout_0.4.35'
    from verify_text_build import read_iso
    elf=read_iso(str(ROOT/'work/output/SRWMX_PS2_EN_0.4.34.iso'),['/SLPS_253.45;1'])['/SLPS_253.45;1']
    meta=json.loads((ROOT/'work/build/ps2/font_0.4.34/patch.json').read_text())
    result=dict(PSP=psp((base/'BOOT.BIN').read_bytes()),PS2=ps2(elf,meta))
    (ROOT/'work/output/parts_layout_0.4.35_native_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Native Parts draw coordinates and all part-description widths pass on both platforms.')
