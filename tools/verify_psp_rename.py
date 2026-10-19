"""Exercise real rename initialization, export, deletion and space insertion."""
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.mips_const import (UC_MIPS_REG_S1, UC_MIPS_REG_SP, UC_MIPS_REG_PC,
    UC_MIPS_REG_RA, UC_MIPS_REG_F12)
import fix_psp_rename
import insert_text as it
from verify_psp_0410 import machine, invoke, cstr

ROOT = Path(__file__).resolve().parents[1]
OBJ, HERO, DEST = 0x1000000, 0x1010000, 0x1020000
GUARD = b'CONTROL-GUARD-012'


def initialize(boot, route, upgraded, load_saved=False, custom=None):
    u = machine(boot)
    u.mem_write(0x300e84,struct.pack('<I',HERO))
    u.mem_write(HERO+0x680,struct.pack('<2I',route,upgraded))
    u.mem_write(OBJ+0x614,bytes([0xa5])*48)
    u.mem_write(OBJ+0x644,GUARD)
    expected = []
    for field,base in enumerate((0x27f1b0,0x27f1c0)):
        pointer = struct.unpack_from('<I',boot,base+(route*2+upgraded)*4+0x60)[0]
        raw = boot[pointer+0x60:boot.index(0,pointer+0x60)]
        if custom is not None:
            raw = it.encode(custom[field])[:-1]
        expected.append(raw[:30 if field==0 else 16])
        u.mem_write(HERO+(0x90 if field==0 else 0x110)+route*64+upgraded*32,
                    (raw+b'\0').ljust(32,b'\0'))
    invoke(u,0x1c347c,[OBJ,int(load_saved)])
    return u,expected


def exported(u,field):
    u.mem_write(DEST,bytes([0xa5])*64)
    invoke(u,0x1c5ae4,[OBJ,field,DEST])
    raw=cstr(u,DEST)
    assert len(raw)<32
    assert bytes(u.mem_read(DEST+32,16))==bytes([0xa5])*16
    return raw


def run_slice(u,start,end):
    def stop(vm,pc,size,unused):
        if pc==end:
            vm.emu_stop()
    hook=u.hook_add(UC_HOOK_CODE,stop)
    u.emu_start(start,0x11e0000,count=20000)
    u.hook_del(hook)
    assert u.reg_read(UC_MIPS_REG_PC)==end


def verify(boot,baseline=None):
    fixed=fix_psp_rename.patch_boot(boot)
    rows=[]
    # The existing public executable must reproduce the reported corruption.
    old,expected=initialize(baseline if baseline is not None else boot,1,1)
    old_bad=exported(old,0)!=expected[0]
    assert old_bad, 'Public-build corruption was not reproduced'
    for route in (0,1):
        for upgraded in (0,1):
            for saved in (False,True):
                u,expected=initialize(fixed,route,upgraded,saved)
                assert bytes(u.mem_read(OBJ+0x644,len(GUARD)))==GUARD
                for field,want in enumerate(expected):
                    assert exported(u,field)==want,(route,upgraded,saved,field)
                rows.append(dict(route=route,upgraded=upgraded,loaded_from_save=saved,
                                 full_name_bytes=len(expected[0]),reading_bytes=len(expected[1])))
    # Maximum-size custom names are loaded and exported through native code.
    u,expected=initialize(fixed,1,1,True,('ABCDEFGHIJKLMNO','ABCDEFGH'))
    assert exported(u,0)==expected[0] and exported(u,1)==expected[1]
    assert bytes(u.mem_read(OBJ+0x644,len(GUARD)))==GUARD
    legacy,want=initialize(fixed,1,1,True,('Cerberus Ignited','Cerberus'))
    assert exported(legacy,0)==it.encode('Cerberus Ignite')[:-1]
    assert exported(legacy,1)==want[1]
    assert bytes(legacy.mem_read(OBJ+0x644,len(GUARD)))==GUARD
    mask_draws=[]
    for field,origin,right in ((0,84,280),(1,360,464)):
        drawing,_=initialize(fixed,1,1)
        coordinates=[]
        def draw(vm,pc,size,unused):
            if pc==0xaeff4:
                coordinates.append(struct.unpack('<f',struct.pack('<I',vm.reg_read(UC_MIPS_REG_F12)))[0])
                vm.reg_write(UC_MIPS_REG_PC,vm.reg_read(UC_MIPS_REG_RA))
        drawing.hook_add(UC_HOOK_CODE,draw)
        invoke(drawing,0x1c35fc,[OBJ,field,origin,40])
        assert coordinates and min(coordinates)>=origin-1 and max(coordinates)+12<right
        mask_draws.append(dict(field=field,slots_drawn=len(coordinates),last_x=max(coordinates),right_limit=right))
    deletion=[]
    for field,text in enumerate(('ABCDEFGHIJKLMNO','ABCDEFGH')):
        for index in (0,len(text)//2,len(text)-1):
            u,_=initialize(fixed,1,1,True,('ABCDEFGHIJKLMNO','ABCDEFGH'))
            before_other=bytes(u.mem_read(OBJ+(0x633 if field==0 else 0x614),17 if field==0 else 31))
            u.mem_write(OBJ+0x5f8,struct.pack('<2I',field,index))
            u.reg_write(UC_MIPS_REG_S1,OBJ)
            u.reg_write(UC_MIPS_REG_SP,0x11ff000)
            run_slice(u,0x1c4e44,0x1c4efc)
            expected_text=text[:index]+text[index+1:]
            assert exported(u,field)==it.encode(expected_text)[:-1]
            assert bytes(u.mem_read(OBJ+(0x633 if field==0 else 0x614),17 if field==0 else 31))==before_other
            assert bytes(u.mem_read(OBJ+0x644,len(GUARD)))==GUARD
            deletion.append(dict(field=field,index=index))
    spaces=[]
    for field,text in enumerate(('ABCDEFGHIJKLMNO','ABCDEFGH')):
        for index in (0,len(text)//2,len(text)-1):
            u,_=initialize(fixed,1,1,True,('ABCDEFGHIJKLMNO','ABCDEFGH'))
            before_other=bytes(u.mem_read(OBJ+(0x633 if field==0 else 0x614),17 if field==0 else 31))
            u.mem_write(OBJ+0x5f8,struct.pack('<2I',field,index))
            u.reg_write(UC_MIPS_REG_S1,OBJ);u.reg_write(UC_MIPS_REG_SP,0x11ff000)
            run_slice(u,0x1c4f3c,0x1c4f94)
            expected_text=(text[:index]+' '+text[index+1:]).rstrip()
            assert exported(u,field)==it.encode(expected_text)[:-1]
            assert bytes(u.mem_read(OBJ+(0x633 if field==0 else 0x614),17 if field==0 else 31))==before_other
            assert bytes(u.mem_read(OBJ+0x644,len(GUARD)))==GUARD
            spaces.append(dict(field=field,index=index))
    sections=it.elf(fixed);header=sections['.rel.text']
    offset,length=struct.unpack_from('<2I',fixed,header+16)
    relocs=dict(struct.unpack_from('<2I',fixed,k) for k in range(offset,offset+length,8))
    stub=(struct.unpack_from('<I',fixed,fix_psp_rename.CAP_SITE+0x60)[0]&0x3ffffff)<<2
    assert relocs[fix_psp_rename.CAP_SITE]&255==4 and relocs[stub+24]&255==4
    return dict(original_corruption_reproduced=old_bad,reset_and_saved_name_cases=rows,
                max_length_custom_names_pass=True,deletion_cases=deletion,space_cases=spaces,
                legacy_overlong_default_safely_loaded=True,native_underline_positions=mask_draws,
                adjacent_control_guards_preserved=True,save_layout_unchanged=True,
                native_copy_strlen_padding_and_export_executed=True,
                patch_idempotent=fix_psp_rename.patch_boot(fixed)==fixed,
                psp_relocation_entries_verified=True)


if __name__=='__main__':
    result=verify((ROOT/'work/build/rename_name_audit/BOOT.BIN').read_bytes())
    (ROOT/'work/output/psp_rename_native_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
