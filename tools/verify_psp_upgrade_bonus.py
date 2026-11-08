"""Execute PSP bonus-menu draws with actual ISO unit and name databases.

The native record lookup, overflow-string resolver, full strcpy, draw prologue,
label iteration and epilogue execute. Only graphics services and the selection
manager's unit-index service are supplied by the fixture. This is not a live
emulator reproduction of the reporter's save.
"""
import json
import struct
import unicodedata
from pathlib import Path
import insert_text as it
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
from verify_psp_0410 import machine,invoke,cstr
from static2_extract import sections
import fix_psp_upgrade_bonus as fix

ROOT=Path(__file__).resolve().parents[1]
OBJ,GAME,UNIT,STRG=0x1000000,0x1008000,0x1010000,0x1030000
CONTEXT=0x10dabc0
GUARD=struct.pack('<4I',CONTEXT,0x0102abd0,0x0103abe0,0x0104abf0)
CONTEXT_MARKER=0x153579bd


def put(u,p,v):u.mem_write(p,struct.pack('<I',v))


def setup(boot,static):
    u=machine(boot);sec=sections(static)
    for tag,at in [('Unit',UNIT),('Strg',STRG)]:
        off,size,_=sec[tag];u.mem_write(at,static[off:off+size])
    put(u,GAME+0x24,UNIT);put(u,GAME+0xec,STRG)
    put(u,0x300e7c,GAME);put(u,0x300e80,0x1060000);put(u,0x300e84,0x1070000)
    for n in range(4):
        # Native save-name fields, including the maximum-size .38 rename form.
        u.mem_write(0x1070090+n*32,it.encode(chr(65+n)*15).ljust(32,b'\0'))
    return u,sec['Unit'][2]


def name(u,idx):
    invoke(u,0x5bf4c,[GAME+0x24,idx]);key=u.reg_read(r.UC_MIPS_REG_V0)
    invoke(u,0x5bf24,[GAME+0xec,key])
    return cstr(u,u.reg_read(r.UC_MIPS_REG_V0))


def execute(boot,static,menu,idx,selection):
    u,_=setup(boot,static);expected=name(u,idx)
    if 140<=idx<=145:
        table=0x2759ac if menu=='unit' else 0x275a30
        target=struct.unpack_from('<I',boot,table+(idx-140)*4+0x60)[0]
        start=0x1dd8e0 if menu=='unit' else 0x1de8f4
        pair={start:(0,0),start+0x1c:(0,1),start+0x38:(1,0),start+0x54:(1,1)}[target]
        expected=it.encode(chr(65+pair[0]*2+pair[1])*15)[:-1]
    u.mem_write(OBJ,bytes(0xb80));u.mem_write(OBJ+fix.OLD_NAME,b'\xa5'*52)
    guard=GUARD if menu=='weapon' else struct.pack('<I',0x2b9f3c)+GUARD[4:]
    u.mem_write(OBJ+0xb40,guard)
    for off,v in [(0xb00,idx),(0xb04,selection),(0xb08,19),(0xb8,1)]:put(u,OBJ+off,v)
    put(u,OBJ+0xa0,2);put(u,OBJ+0xa4,20)
    state=bytes(u.mem_read(OBJ+0xb00,12));draws=[];lookups=[]
    put(u,CONTEXT+0xc78,CONTEXT_MARKER)
    put(u,(CONTEXT&~255)+0xc78,0xbad0bad0)
    def service(m,pc,size,user):
        if pc==0x184380:
            lookups.append(m.reg_read(r.UC_MIPS_REG_A2))
            m.reg_write(r.UC_MIPS_REG_V0,idx)
        elif pc==0xaeb08:
            at=m.reg_read(r.UC_MIPS_REG_A1)
            draws.append(dict(at=at,text=cstr(m,at)))
        elif pc==0xb03e4:
            m.reg_write(r.UC_MIPS_REG_V0,len(cstr(m,m.reg_read(r.UC_MIPS_REG_A1)))*4)
        elif pc not in (0xb0368,0x202b7c):return
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    sentinels={r.UC_MIPS_REG_S0:0x1011110,r.UC_MIPS_REG_S1:0x1022220,
               r.UC_MIPS_REG_S2:0x1033330,r.UC_MIPS_REG_S3:0x1044440}
    for reg,v in sentinels.items():u.reg_write(reg,v)
    invoke(u,fix.MENUS[menu]['start'],[OBJ])
    assert u.reg_read(r.UC_MIPS_REG_SP)==0x11ff000
    assert all(u.reg_read(reg)==v for reg,v in sentinels.items())
    assert draws[-1]['text']==expected and lookups==[idx]
    assert bytes(u.mem_read(OBJ+0xb00,12))==state
    after=bytes(u.mem_read(OBJ+0xb40,len(GUARD)))
    return_reads=[]
    if menu=='weapon':
        # Execute the real parent's context read on return from the bonus
        # window. Constructor offsets prove these fields alias OBJ+0xb40.
        for parent_offset,pc in [(0x3560,0x898dc),(0x5080,0x8ae0c)]:
            u.reg_write(r.UC_MIPS_REG_S0,OBJ-parent_offset)
            u.emu_start(pc,pc+16,count=20)
            got=struct.unpack('<I',u.mem_read(0x2c3ec0,4))[0]
            return_reads.append(dict(parent_weapon_offset=hex(parent_offset),
                                     native_return_pc=hex(pc),correct_context=got==CONTEXT_MARKER))
    return dict(menu=menu,unit_id=idx,selection=selection,
                name=unicodedata.normalize('NFKC',expected.decode('cp932')),
                encoded_name_bytes=len(expected)+1,name_draw_pointer=hex(draws[-1]['at']),
                guard_preserved=after==guard,guard_before=guard.hex(),guard_after=after.hex(),
                bonus_state_preserved=True,full_name_drawn=True,
                native_return_context_reads=return_reads,
                stack_and_callee_saved_registers_preserved=True)


def verify(original,patched,static):
    assert fix.patch_boot(patched)==patched
    assert len(original)==len(patched)
    allowed={s+0x60+j for m in fix.MENUS.values() for s in m['sites'] for j in range(4)}
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,patched)))
    # Two actual parent constructors place the weapon window exactly 0xb40
    # after the unit window. Their context fields follow the weapon window
    # at the same distance. Verify these are native fields, not invented
    # fixture guard positions.
    for unit_site,weapon_site,unit_at,weapon_at,context in [
            (0x88a34,0x88a3c,0x2a20,0x3560,0x40a0),
            (0x8a20c,0x8a214,0x4540,0x5080,0x5bc0)]:
        assert struct.unpack_from('<I',original,unit_site+0x60)[0]==0x26040000|unit_at
        assert struct.unpack_from('<I',original,weapon_site+0x60)[0]==0x26040000|weapon_at
        assert weapon_at-unit_at==context-weapon_at==0xb40
    u,count=setup(original,static)
    names=[name(u,i) for i in range(count)]
    candidates=[i for i,n in enumerate(names) if unicodedata.normalize('NFKC',n.decode('cp932'))=='Full Armor Hyaku Shiki Kai']
    assert candidates
    longest=max(range(count),key=lambda i:len(names[i]))
    assert max(map(len,names))+1<=min(m['capacity'] for m in fix.MENUS.values())
    short=next(i for i,n in enumerate(names) if unicodedata.normalize('NFKC',n.decode('cp932'))=='Hyaku Shiki')
    old=[execute(original,static,m,candidates[0],0) for m in fix.MENUS]
    assert all(not x['guard_preserved'] and x['encoded_name_bytes']==53 for x in old)
    assert all(bytes.fromhex(x['guard_after'])==b'\0'+bytes.fromhex(x['guard_before'])[1:] for x in old)
    assert all(not x['correct_context'] for x in old[1]['native_return_context_reads'])
    cases=[]
    for m,n in [('unit',7),('weapon',8)]:
        for idx in dict.fromkeys([candidates[0],longest,short]):
            for selection in range(n):
                row=execute(patched,static,m,idx,selection)
                assert row['guard_preserved']
                assert all(x['correct_context'] for x in row['native_return_context_reads'])
                cases.append(row)
        for idx in range(140,146):
            row=execute(patched,static,m,idx,0)
            assert row['guard_preserved'] and row['encoded_name_bytes']==31
            cases.append(row)
    return dict(passed=True,public_psp_version='0.4.47',old_overwrite_reproduced=old,
                corrected_cases=cases,native_database_rows_checked=count,
                max_encoded_name_bytes=max(map(len,names))+1,
                native_database_lookup_and_strcpy_executed=True,
                native_parent_window_layout_verified=True,
                all_other_executable_bytes_preserved=True,
                reporter_save_and_live_confirmation='pending')


if __name__=='__main__':
    from verify_text_build import read_iso
    assets=['/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/USRDIR/STATIC2_ADD.BIN']
    raw=read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.47.iso'),assets)
    boot=raw[assets[0]];patched=fix.patch_boot(boot)
    report=verify(boot,patched,raw[assets[1]])
    out=ROOT/'work/build/psp/upgrade_bonus_0.4.51';out.mkdir(parents=True,exist_ok=True)
    (out/'BOOT.BIN').write_bytes(patched)
    (ROOT/'work/output/psp_upgrade_bonus_0.4.51_native_execution.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='corrected_cases'},indent=2))
    print('Corrected native draw cases:',len(report['corrected_cases']))
