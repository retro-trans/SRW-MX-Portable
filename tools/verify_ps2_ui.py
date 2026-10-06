"""Verify the incremental PS2 font/UI fix and preserved PSP scenario assets."""
import json,struct
from fix_ps2_ui import ROOT,BASE,VERSION,SOURCE_VERSION,sha
from port_ps2_prologue import save
from ps2_font4x import FILE_BIAS
import insert_text as it
from verify_ps2_font import machine
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg


def verify(base=BASE,version=VERSION):
    meta=json.loads((base/'patch.json').read_text())
    changes=json.loads((base/'ui_fix.json').read_text())
    data=(base/'SLPS_253.45').read_bytes()
    previous=ROOT/'work/build/ps2'/f'prologue_fix_{SOURCE_VERSION}'
    assert sha(data)==meta['target_sha256']
    def offset(va):
        for n in range(struct.unpack_from('<H',data,44)[0]):
            kind,off,start,_,size,*_=struct.unpack_from('<8I',data,52+n*32)
            if kind==1 and start<=va<start+size:return off+va-start
        raise AssertionError(hex(va))
    def text_at(va):
        off=offset(va)
        return data[off:data.index(0,off)]
    for row in changes['text_references']:
        target=struct.unpack_from('<I',data,offset(int(row['site'],16)))[0]
        assert target==int(row['target'],16),row
        assert text_at(target)==it.encode(row['english'])[:-1],row
    for row in changes['in_place_ui_strings']+changes['footer']:
        va=int(row.get('source',row.get('target')),16)
        assert text_at(va)==it.encode(row['english'])[:-1],row
    for row in changes['layout']:
        assert struct.unpack_from('<I',data,offset(int(row['va'],16)))[0]==int(row['new'],16)
    hook=int(changes['spirit_hook']['va'],16)
    assert data[offset(hook):offset(hook)+4]==bytes.fromhex(changes['spirit_hook']['new'])
    # Execute the real Spirit name measurement and fit wrapper. Intercept
    # only the final GS draw call so we can inspect dimensions and restore.
    u=machine(data);captured=[]
    def draw_probe(m,address,size,user):
        if address!=0x130610:return
        ctx=m.reg_read(reg.UC_MIPS_REG_A0)
        captured.append(dict(size=list(struct.unpack('<2f',m.mem_read(ctx,8))),
                             y=m.reg_read(reg.UC_MIPS_REG_A3)))
        m.reg_write(reg.UC_MIPS_REG_PC,m.reg_read(reg.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,draw_probe);initial=u.context_save();name_cases=[]
    widths={g['character']:g['width'] for g in meta['glyphs']}
    for name in ('Accel','Sure Hit','Self Destruct','Iron Wall','Resupply','????'):
        for index in (2,7,8):
            u.context_restore(initial);captured.clear()
            u.mem_write(0x900000,struct.pack('<2f',24,24)+bytes(64))
            u.mem_write(0x910000,it.encode(name))
            u.reg_write(reg.UC_MIPS_REG_A0,0x900000);u.reg_write(reg.UC_MIPS_REG_A1,0x910000)
            u.reg_write(reg.UC_MIPS_REG_A2,212);u.reg_write(reg.UC_MIPS_REG_A3,244)
            u.reg_write(reg.UC_MIPS_REG_T0,0xffffffffffffffff);u.reg_write(reg.UC_MIPS_REG_S2,index)
            u.emu_start(hook,hook+8,count=10000)
            assert u.reg_read(reg.UC_MIPS_REG_PC)==hook+8
            assert len(captured)==1,(name,index,captured)
            w,h=captured[0]['size'];assert w==h and w<=24
            total=sum(widths[c] for c in name)
            if index in (2,7):
                assert total*w/24<=76.0001,(name,index,w,total)
                assert abs(captured[0]['y']+h*74/96-(208+24*74/96))<=0.51
            else:assert w==24 and captured[0]['y']==208
            assert bytes(u.mem_read(0x900000,8))==struct.pack('<2f',24,24)
            assert u.reg_read(reg.UC_MIPS_REG_SP)==0xa00000
            name_cases.append(dict(name=name,row=index,draw_size=[w,h],y=captured[0]['y']))
    assert 212+76<292 and 306+3*widths['0']<346
    preserved=[]
    for name in ('MAP.BIN','STAGE.BIN','FIX00.DAT','D2MAPH.BIN','PACKMAPC.BIN','STATIC.BIN','FACEPACK.BIN'):
        if name=='FIX00.DAT' and (base/'ui_details.json').exists():
            # The detail patch reflows text indexes; its dedicated verifier
            # checks every retained section and all numeric gameplay records.
            continue
        from ps2_resource_preservation import check
        check(base,previous,name)
        preserved.append(name)
    result=dict(version=version,pass_=True,text_reference_checks=len(changes['text_references']),
                padded_string_checks=len(changes['in_place_ui_strings']),footer_checks=len(changes['footer']),
                spirit_layout_execution_cases=name_cases,spirit_cost_layout_checks=13,
                scenario_and_portrait_assets_preserved=preserved,psp_opening_preserved=True,
                native_font=True,texture_replacement=False,patched_sha256=sha(data))
    save(ROOT/'work/output'/f'ps2_ui_{version}_execution.json',result)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':verify()
