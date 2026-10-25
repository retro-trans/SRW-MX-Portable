"""Reproduce the real ending's lockout and execute saved-state recovery."""
import copy
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
from verify_ps2_rename import vm,call,cstr
from verify_ps2_difficulty import put,word
import play_order
import fix_ps2_stage30_transition as fix

ROOT=Path(__file__).resolve().parents[1]
CAMPAIGN,STAGE,PARENT,SCRIPT,CMD=0x810000,0x820000,0x840000,0x850000,0x880000


def fixture(elf,stage,route,mask=127,chapter=7,scene=5,group=10):
    u=vm(elf);u.mem_write(STAGE,stage);put(u,CAMPAIGN,STAGE);put(u,CAMPAIGN+4,STAGE)
    call(u,0x346d60,CAMPAIGN)
    put(u,0x3c8cbc,CAMPAIGN);put(u,CAMPAIGN+0x3a0,scene);put(u,CAMPAIGN+0x3a8,chapter)
    put(u,CAMPAIGN+0x3ac,group);put(u,CAMPAIGN+0x39c,mask)
    put(u,CAMPAIGN+0x3a4,32);u.mem_write(CAMPAIGN+0x3b0+64,bytes((7,6)))
    u.mem_write(CAMPAIGN+0x12,bytes((route,)))
    for n in range(7):u.mem_write(CAMPAIGN+28+7*56+n,bytes((int(bool(mask&(1<<n))),)))
    events=[]
    def service(m,pc,size,user):
        if pc==0x12efc0:
            events.append(m.reg_read(r.UC_MIPS_REG_A1));m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    return u,events


def state(u):return dict(scene=word(u,CAMPAIGN+0x3a0),chapter=word(u,CAMPAIGN+0x3a8),mask=word(u,CAMPAIGN+0x39c))


def opcode(u,op):
    u.mem_write(CMD,struct.pack('<12I',op,*([0]*11)))
    return call(u,{108:0x3000f0,112:0x3007b8}[op],SCRIPT,CMD)


def populate(u):
    before_sp=u.reg_read(r.UC_MIPS_REG_SP)
    for reg,value in ((r.UC_MIPS_REG_S0,111),(r.UC_MIPS_REG_S1,222),(r.UC_MIPS_REG_S2,333)):
        u.reg_write(reg,value)
    call(u,0x1c4ba8,PARENT)
    assert u.reg_read(r.UC_MIPS_REG_SP)==before_sp
    assert [u.reg_read(reg) for reg in (r.UC_MIPS_REG_S0,r.UC_MIPS_REG_S1,r.UC_MIPS_REG_S2)]==[111,222,333]
    return [struct.unpack('<3I',u.mem_read(PARENT+0x1b14+n*12,12)) for n in range(8)]


def verify(original,elf,meta,stage,closing):
    c,_=play_order.load(closing,0)
    assert not any(x[0]==112 for x in c)
    ending=[x[0] for x in c[69:72]];assert ending==[108,93,127]
    rows=[]
    for route,want in ((0,8),(1,9)):
        old,events=fixture(original,stage,route,63,group=12)
        opcode(old,112);assert state(old)['chapter']==7
        put(old,CAMPAIGN+0x39c,127);put(old,CAMPAIGN+0x3ac,10)
        for op in ending:
            if op==108:opcode(old,op)
        assert state(old)==dict(scene=5,chapter=7,mask=127) and events==[0x13c]
        old_rows=populate(old)
        assert state(old)['chapter']==7 and len([x for x in old_rows if x[0]])==7
        assert all(x[2]==1 for x in old_rows if x[0])
        # Execute the same original chapter-30 opcode 108 through its new hook.
        u,events=fixture(elf,stage,route)
        opcode(u,108);assert state(u)==dict(scene=6,chapter=want,mask=0)
        assert events==[0x13c]
        after=state(u);opcode(u,108);assert state(u)==after
        # Independently start from a previously stuck saved-state fixture.
        saved,events=fixture(elf,stage,route)
        prior_history=bytes(saved.mem_read(CAMPAIGN+0x3b0,256))
        prior_clear_counts=bytes(saved.mem_read(CAMPAIGN+28,896))
        current_rows=populate(saved)
        assert state(saved)==dict(scene=6,chapter=want,mask=0)
        assert bytes(saved.mem_read(CAMPAIGN+0x3b0,256))==prior_history
        assert bytes(saved.mem_read(CAMPAIGN+28,896))==prior_clear_counts
        assert word(saved,CAMPAIGN+0x3a4)==32 and bytes(saved.mem_read(CAMPAIGN+0x12,1))==bytes((route,))
        assert len([x for x in current_rows if x[0]])==1,current_rows
        assert all(x[2]==0 for x in current_rows if x[0])
        first_group=call(saved,0x346e90,CAMPAIGN,0)
        assert first_group==0
        first_title=call(saved,0x3473d0,CAMPAIGN,0)
        title=cstr(saved,first_title).decode('cp932')
        again=state(saved);assert populate(saved)==current_rows and state(saved)==again
        call(saved,0x346f88,CAMPAIGN,0)
        assert word(saved,CAMPAIGN+0x3ac)==0 and word(saved,CAMPAIGN+0x3a4)==33
        assert bytes(saved.mem_read(CAMPAIGN+0x3b0+66,2))==bytes((want,0))
        late,events=fixture(elf,stage,route,63)
        opcode(late,108);assert state(late)['chapter']==7 and events==[0x13c]
        put(late,CAMPAIGN+0x39c,127);late.mem_write(CAMPAIGN+28+7*56+6,b'\x01')
        populate(late);assert state(late)==dict(scene=6,chapter=want,mask=0)
        rows.append(dict(route='Earth' if route else 'Space',old_lockout_reproduced=True,
            old_end_commands=ending,old_chapter=7,old_clear_mask=127,old_rows=7,
            after_normal_ending=after,after_stuck_save_recovery=state(saved),
            available_stage_rows=1,first_route_title=title,history_and_completion_counts_preserved=True,
            next_stage_selection_and_history_append_pass=True,late_clear_commit_recovery_pass=True))
    guards=[]
    for mask in range(127):
        u,_=fixture(elf,stage,1,mask)
        before=bytes(u.mem_read(CAMPAIGN,0x500));call(u,int(meta['stage30_transition_fix']['helper_va'],16))
        assert bytes(u.mem_read(CAMPAIGN,0x500))==before,mask
        guards.append(mask)
    for kwargs in (dict(chapter=8),dict(chapter=9),dict(scene=4),dict(scene=6),dict(group=8),dict(group=12),dict(route=2)):
        values=dict(route=1);values.update(kwargs);u,_=fixture(elf,stage,**values)
        before=bytes(u.mem_read(CAMPAIGN,0x500));call(u,int(meta['stage30_transition_fix']['helper_va'],16))
        assert bytes(u.mem_read(CAMPAIGN,0x500))==before,kwargs
    u,_=fixture(elf,stage,1)
    count_at=struct.unpack_from('<5I',stage)[1]+7*88+56
    put(u,STAGE+count_at,6);before=state(u)
    call(u,int(meta['stage30_transition_fix']['helper_va'],16));assert state(u)==before
    for missing in ('campaign','stage'):
        u,_=fixture(elf,stage,1)
        put(u,0x3c8cbc if missing=='campaign' else CAMPAIGN,0)
        call(u,int(meta['stage30_transition_fix']['helper_va'],16));assert u.reg_read(r.UC_MIPS_REG_V0)==0
    # Script replay/special mode must retain opcode 108's original behavior.
    u,events=fixture(elf,stage,1);put(u,SCRIPT+0x2fec,1);before=state(u);opcode(u,108)
    assert state(u)==before and not events
    assert fix.patch(elf,copy.deepcopy(meta))[0]==elf
    return dict(passed=True,actual_chapter30_closing_has_no_112=True,
        previous_tests_missed_script_invocation=True,routes=rows,incomplete_mask_guard_cases=len(guards),
        other_state_guard_cases=7,unported_six_location_and_uninitialized_state_guards=True,
        special_mode_preserved=True,reentry_idempotent=True,
        native_opcode108_chapter_advance_and_stage_select_population_executed=True,
        only_intermission_event_delivery_serviced=True,save_layout_unchanged=True,
        patch_idempotent=True,reporter_memory_card_not_tested=True,pcsx2_visual_validation='pending')


if __name__=='__main__':
    import pycdlib
    base=ROOT/'work/build/ps2/font_0.4.44';old=(base/'SLPS_253.45').read_bytes()
    elf,meta,info=fix.patch(old,json.loads((base/'patch.json').read_text(encoding='utf8')))
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/'work/output/SRWMX_PS2_EN_0.4.38.iso'))
    with iso.open_file_from_iso(iso_path='/DATA/STAGE.BIN;1') as stream:stage=stream.read()
    iso.close()
    closing=(ROOT/'work/build/ps2/story_flow_0.4.38_audit/i056a.bin').read_bytes()
    result=verify(old,elf,meta,stage,closing)
    print(json.dumps(result,ensure_ascii=False,indent=2))
