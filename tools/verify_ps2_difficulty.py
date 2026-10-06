"""Execute native difficulty hooks against all records and real save tails."""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from verify_ps2_font import machine
from ps2_difficulty import ROOT, TAIL_OFFSET, MAGIC, VERSION, BUILD_VERSION, YESNO_VTABLE, YESNO_VTABLE_BYTES, balance_data
from static2_extract import sections

def run(u,start,end=0x920000):
    u.reg_write(reg.UC_MIPS_REG_RA,0x920000)
    def stop(vm,address,size,user):
        if address==end:vm.emu_stop()
    handle=u.hook_add(UC_HOOK_CODE,stop)
    u.emu_start(start,end+4,count=10000)
    u.hook_del(handle)
    assert u.reg_read(reg.UC_MIPS_REG_PC)==end,hex(u.reg_read(reg.UC_MIPS_REG_PC))

def word(u,addr):return struct.unpack('<I',u.mem_read(addr,4))[0]
def put(u,addr,value):u.mem_write(addr,struct.pack('<I',value))
def checksum(data):
    n=len(data)
    for begin,end,out in [(n-1024,n-8,n-8),(0,n-1024,n-4)]:
        struct.pack_into('<I',data,out,(0x78945612+sum(struct.unpack('<%dI'%((end-begin)//4),data[begin:end])))&0xffffffff)

def verify(data,meta):
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    baseline=machine(original);u=machine(data)
    mode=int(meta['mode_va'],16);routine={k:int(v['va'],16) for k,v in meta['routines'].items()}
    hp,rewards,_=balance_data()
    fix=(ROOT/'work/source/ps2/FIX00.DAT').read_bytes();sec=sections(fix,0)
    unit=bytearray(fix[sec['Unit'][0]:sec['Unit'][0]+sec['Unit'][1]])
    if 'added_enemy_dragoon' in meta:
        added=meta['added_enemy_dragoon'];assert added['id']==156 and added['native_template_id']==69
        unit[12+156*124:12+157*124]=unit[12+69*124:12+70*124]
        hp[156]=added['psp_hp'];rewards[156]=added['psp_reward']
    obj=0x810000;table=0x820000
    for vm in [baseline,u]:vm.mem_write(table,bytes(unit));put(vm,obj,table)
    values=0
    for difficulty in (0,1,2):
        put(u,mode,difficulty)
        for i in range(512):
            for name,site,expected in [('hp',0x332a10,hp[i]),('reward',0x332af0,rewards[i])]:
                for vm in [baseline,u]:
                    vm.reg_write(reg.UC_MIPS_REG_SP,0xa00000)
                    vm.reg_write(reg.UC_MIPS_REG_A0,obj);vm.reg_write(reg.UC_MIPS_REG_A1,i)
                    run(vm,site)
                wanted=expected if difficulty==1 else baseline.reg_read(reg.UC_MIPS_REG_V0)
                assert u.reg_read(reg.UC_MIPS_REG_V0)==wanted,(difficulty,name,i)
                assert u.reg_read(reg.UC_MIPS_REG_SP)==0xa00000
                values+=1
    # An out-of-range sentinel still uses original lookup (with a valid test backing record).
    for name,site,field in [('hp',0x332a10,12),('reward',0x332af0,26)]:
        i=512;put(u,mode,1);u.mem_write(table+12+124*i+field,struct.pack('<I',12345))
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,i)
        run(u,site);assert u.reg_read(reg.UC_MIPS_REG_V0)==12345
    menu=0x830000;tail=0x850000;checks=0
    for selected,event,previous in [(0,1,1),(1,1,0),(0,2,1),(1,2,0)]:
        put(u,mode,previous);put(u,menu+0x5698,event);put(u,menu+0x569c,selected)
        u.reg_write(reg.UC_MIPS_REG_S4,menu)
        run(u,0x2bd1bc,0x2bd1c4)
        assert word(u,mode)==(selected if event==1 else previous)
        assert u.reg_read(reg.UC_MIPS_REG_V1)==event
        assert u.reg_read(reg.UC_MIPS_REG_V0)==1
        checks+=1
    # Run setup with only the existing message insertion call intercepted.
    calls=[]
    def mock(vm,addr,size,user):
        if addr==0x151a08:
            calls.append((vm.reg_read(reg.UC_MIPS_REG_A0),vm.reg_read(reg.UC_MIPS_REG_A1),vm.reg_read(reg.UC_MIPS_REG_A2)))
            vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    h=u.hook_add(UC_HOOK_CODE,mock)
    u.reg_write(reg.UC_MIPS_REG_S4,menu);put(u,menu+0x5694,5)
    run(u,0x2bd120,0x2bd238);u.hook_del(h)
    assert calls==[(menu+0x3e80,int(meta['strings']['details'],16),7)]
    box=menu+0x40c0
    assert word(u,box+0x24)==int(meta['vtable_va'],16)
    assert word(u,box+0x208)==int(meta['strings']['ps2'],16)
    assert word(u,box+0x20c)==int(meta['strings']['psp'],16)
    assert word(u,box+0x194)==0 and word(u,box+0x9c)==200 and word(u,box+0xa0)==260
    assert word(u,int(meta['vtable_va'],16)+0x44)==routine['opening']
    # The opening routine dispatches cursor geometry at vtable +0xb8..+0xd0.
    # The old 0x90-byte copy pointed into prompt strings and left choices invisible.
    expected_table=bytearray(original[YESNO_VTABLE-0xff000:YESNO_VTABLE-0xff000+YESNO_VTABLE_BYTES])
    struct.pack_into('<I',expected_table,0x44,routine['opening'])
    assert bytes(u.mem_read(int(meta['vtable_va'],16),YESNO_VTABLE_BYTES))==expected_table
    # Run the actual window update/opening and render dispatch. Only external
    # drawing/cursor services are intercepted; EE multiply/divide semantics are
    # supplied because Unicorn lacks the PS2's second LO register.
    cursor=[];drawn=[];ee={'lo1':0}
    def window_services(vm,address,size,user):
        if address==0x14fd54:
            result=(vm.reg_read(reg.UC_MIPS_REG_A0)*vm.reg_read(reg.UC_MIPS_REG_V1))&0xffffffff
            vm.reg_write(reg.UC_MIPS_REG_V0,result)
            vm.reg_write(reg.UC_MIPS_REG_PC,address+4);return
        if address==0x14fd58:
            ee['lo1']=vm.reg_read(reg.UC_MIPS_REG_A2)//vm.reg_read(reg.UC_MIPS_REG_S4)
            vm.reg_write(reg.UC_MIPS_REG_PC,address+4);return
        if address==0x14fd78:
            vm.reg_write(reg.UC_MIPS_REG_A2,ee['lo1'])
            vm.reg_write(reg.UC_MIPS_REG_PC,address+4);return
        if address==0x19ebd8:
            cursor.append(tuple(vm.reg_read(r) for r in (reg.UC_MIPS_REG_A1,reg.UC_MIPS_REG_A2,reg.UC_MIPS_REG_A3,reg.UC_MIPS_REG_T0)))
        elif address==0x130610:
            drawn.append(tuple(vm.reg_read(r) for r in (reg.UC_MIPS_REG_A1,reg.UC_MIPS_REG_A2,reg.UC_MIPS_REG_A3)))
        elif address not in (0x146640,0x12c170,0x1438e0,0x12e3f8,0x19ed10,0x131958):return
        vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    h=u.hook_add(UC_HOOK_CODE,window_services)
    put(u,box+0xb0,1);put(u,box+0x190,0)
    u.mem_write(box+0x98,struct.pack('<2H',1,1))
    for frame in range(5):
        u.reg_write(reg.UC_MIPS_REG_A0,box);u.reg_write(reg.UC_MIPS_REG_SP,0xa00000)
        run(u,0x142f50)
        assert word(u,box+0xb0)==(3 if frame==4 else 1)
    assert cursor==[(200,267,240,26)]
    assert word(u,box+0xa4)==240 and word(u,box+0xa8)==74
    u.reg_write(reg.UC_MIPS_REG_A0,box);run(u,0x143118)
    u.hook_del(h)
    assert drawn==[(int(meta['strings']['ps2'],16),218,270),(int(meta['strings']['psp'],16),218,296)]
    # Execute the game's original Yes/No input handler, mocking only controller
    # queries, parent notification dispatch and sound/cursor services.
    delivered=[];button={'cancel':False,'queries':0,'arrow':0,'quiet':False}
    def controls(vm,address,size,user):
        # Unicorn mishandles MOVN/MOVZ in these JR delay slots. Supply the
        # original delay-slot operation and return; preceding native arithmetic
        # and the complete parent input-handler path still execute.
        if address in (0x152278,0x15228c):
            condition=vm.reg_read(reg.UC_MIPS_REG_V1)
            if address==0x152278 and condition:vm.reg_write(reg.UC_MIPS_REG_V0,vm.reg_read(reg.UC_MIPS_REG_A0))
            if address==0x15228c and not condition:vm.reg_write(reg.UC_MIPS_REG_V0,0)
            vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA));return
        if address==0x12f180:
            vm.reg_write(reg.UC_MIPS_REG_V0,int(vm.reg_read(reg.UC_MIPS_REG_A1)==button['arrow']))
        elif address==0x12f070:
            button['queries']+=1
            down=(button['queries']==2) if button['cancel'] else (button['queries']==1)
            vm.reg_write(reg.UC_MIPS_REG_V0,int(down and not button['quiet']))
        elif address==0x12ef30:
            event=vm.reg_read(reg.UC_MIPS_REG_A2);selected=vm.reg_read(reg.UC_MIPS_REG_A3)
            delivered.append((event,selected))
            put(vm,menu+0x5698,event);put(vm,menu+0x569c,selected)
        elif address not in (0x19ec10,0x19ec70,0x1a1060):return
        vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    handle=u.hook_add(UC_HOOK_CODE,controls)
    for selected,cancel in [(0,False),(1,False),(1,True)]:
        button.update(cancel=cancel,queries=0)
        u.mem_write(box+0xb4,struct.pack('<H',1));put(u,box+0x194,selected)
        put(u,box+0x134,1);put(u,box+0x138,2);put(u,box+0xbc,menu)
        u.reg_write(reg.UC_MIPS_REG_A0,box);u.reg_write(reg.UC_MIPS_REG_SP,0xa00000)
        run(u,0x151ed8)
        assert delivered[-1]==((2,0) if cancel else (1,selected))
    before_notifications=len(delivered)
    for selected,arrow in [(0,0x404000),(1,0x101000),(1,0x404000),(0,0x101000)]:
        button.update(arrow=arrow,quiet=True,queries=0)
        put(u,box+0x194,selected);put(u,box+0x26c,0xffffffff)
        u.reg_write(reg.UC_MIPS_REG_A0,box);run(u,0x151ed8)
        assert word(u,box+0x194)==1-selected
    assert len(delivered)==before_notifications
    u.hook_del(handle)
    u.reg_write(reg.UC_MIPS_REG_S4,menu);u.reg_write(reg.UC_MIPS_REG_GP,0x900000)
    put(u,0x900000-0x50c0,2);put(u,menu+0x5698,1)
    run(u,0x2bd2ac,0x2bd2b4)
    assert word(u,box+0x24)==0x488fa0 and word(u,menu+0x5698)==0
    assert word(u,box+0x208)!=int(meta['strings']['ps2'],16)
    assert word(u,box+0x20c)!=int(meta['strings']['psp'],16)
    assert u.reg_read(reg.UC_MIPS_REG_V0)==2
    save_cases=[]
    for directory in ('BISLPS-25345S00','BISLPS-25345'):
        source=(ROOT/'work/source/save_compare/ps2'/directory/directory).read_bytes()
        original_tail=source[-1024:]
        assert original_tail[TAIL_OFFSET:TAIL_OFFSET+12]==bytes(12)
        for choice in (0,1):
            u.mem_write(tail,original_tail);put(u,mode,choice)
            u.reg_write(reg.UC_MIPS_REG_S0,tail);u.reg_write(reg.UC_MIPS_REG_SP,0x9f0000)
            u.mem_write(0x9f0000,bytes(32))
            run(u,0x335ad8,0x335ae0)
            stamped=bytes(u.mem_read(tail,1024));expected=bytearray(original_tail)
            struct.pack_into('<3I',expected,TAIL_OFFSET,MAGIC,VERSION,choice)
            assert stamped==expected
            saved=bytearray(source);saved[-1024:]=stamped;checksum(saved)
            assert saved[:-1024]==source[:-1024] and len(saved)==len(source)
            # The native tail-checksum loop must compute the same integrity value.
            u.reg_write(reg.UC_MIPS_REG_A0,tail);u.reg_write(reg.UC_MIPS_REG_A1,0)
            u.reg_write(reg.UC_MIPS_REG_T0,0);u.reg_write(reg.UC_MIPS_REG_S2,tail-0xd608)
            run(u,0x13971c,0x139748)
            native=word(u,tail+0x3f8)
            assert native==struct.unpack_from('<I',saved,len(saved)-8)[0]
            put(u,mode,1-choice);u.reg_write(reg.UC_MIPS_REG_A1,tail)
            run(u,routine['restore']);assert word(u,mode)==choice
            save_cases.append(dict(type=directory,mode=choice,bytes=len(saved),native_checksum_pass=True))
        u.mem_write(tail,original_tail);put(u,mode,1);u.reg_write(reg.UC_MIPS_REG_A1,tail)
        run(u,routine['restore']);assert word(u,mode)==0
    for tag,version,value in [(0,1,1),(MAGIC,2,1),(MAGIC,1,2),(MAGIC,1,0xffffffff)]:
        u.mem_write(tail+TAIL_OFFSET,struct.pack('<3I',tag,version,value));put(u,mode,1)
        u.reg_write(reg.UC_MIPS_REG_A1,tail);run(u,routine['restore']);assert word(u,mode)==0
    # Settings entry preserves arguments/prologue, and early scenario loading precedes unit decoding.
    u.mem_write(tail+TAIL_OFFSET,struct.pack('<3I',MAGIC,1,1));put(u,mode,0)
    u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,tail)
    u.reg_write(reg.UC_MIPS_REG_SP,0xa00000);u.reg_write(reg.UC_MIPS_REG_S1,0x11223344)
    run(u,0x335eb0,0x335eb8)
    assert word(u,mode)==1 and u.reg_read(reg.UC_MIPS_REG_SP)==0xa00000-80
    assert u.reg_read(reg.UC_MIPS_REG_A0)==obj and u.reg_read(reg.UC_MIPS_REG_A1)==tail
    assert word(u,0xa00000-80+0x38)==0x11223344
    u.reg_write(reg.UC_MIPS_REG_S2,tail-0xd608);put(u,tail-0xd608+0x318,11)
    put(u,mode,0);u.reg_write(reg.UC_MIPS_REG_SP,0xa00000)
    run(u,0x13b850,0x13b858)
    assert word(u,mode)==1 and u.reg_read(reg.UC_MIPS_REG_V0)==12
    assert u.reg_read(reg.UC_MIPS_REG_SP)==0xa00000
    return dict(record_execution_cases=values,out_of_range_fallback_cases=2,menu_confirm_cancel_cases=checks,
                native_menu_setup_pass=True,shared_confirmation_box_restored=True,
                full_vtable_and_five_frame_opening_pass=True,native_render_dispatch_draws_both_choices=True,
                original_controller_handler_confirm_cancel_cases=3,
                original_controller_handler_up_down_cases=4,
                save_tail_roundtrips=save_cases,legacy_saves_default_ps2=True,
                invalid_save_marker_cases=4,mode_restored_before_scenario_unit_deserialization=True,
                original_numeric_database_untouched=True,visual_and_real_save_reload_validation='pending')

if __name__=='__main__':
    base=ROOT/'work/build/ps2'/('difficulty_'+BUILD_VERSION)
    result=verify((base/'SLPS_253.45').read_bytes(),json.loads((base/'difficulty.json').read_text()))
    out=ROOT/'work/output'/f'ps2_difficulty_{BUILD_VERSION}_execution.json'
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
