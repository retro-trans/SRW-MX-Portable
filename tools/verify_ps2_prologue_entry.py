"""Run the actual native New Game completion event, including both branches."""
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from verify_ps2_font import machine
from verify_ps2_difficulty import run, put, word
from port_ps2_translations import ROOT


def completion(data, stage, robot, balance):
    u = machine(data)
    parent, resources, campaign, stage_va = 0x810000, 0x820000, 0x830000, 0x840000
    battle, hero = 0x850000, 0x980000
    u.mem_write(stage_va, stage)
    put(u,campaign,stage_va);put(u,campaign+4,stage_va)
    u.reg_write(reg.UC_MIPS_REG_A0,campaign);run(u,0x346d60)
    put(u,parent+0x30,resources);put(u,parent+0x34,battle)
    put(u,resources+0x201c,campaign);put(u,resources+0x2014,hero)
    put(u,hero+0x5e0,robot);put(u,0x7cce90,balance)
    # Only window attachment and overlay animation are intercepted. Native
    # event dispatch, first battle arguments and campaign advance execute.
    def services(vm,pc,size,user):
        if pc in (0x12ee18,0x143318):
            vm.reg_write(reg.UC_MIPS_REG_V0,1)
            vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    handle=u.hook_add(UC_HOOK_CODE,services)
    u.reg_write(reg.UC_MIPS_REG_A0,parent)
    u.reg_write(reg.UC_MIPS_REG_A1,0x2d6)
    u.reg_write(reg.UC_MIPS_REG_A2,0)
    stack=u.reg_read(reg.UC_MIPS_REG_SP)
    run(u,0x134b40)
    u.hook_del(handle)
    assert u.reg_read(reg.UC_MIPS_REG_SP)==stack
    chapter=word(u,battle+0xcbda4);group=word(u,battle+0xcbda8)
    assert word(u,battle+0xcbcf4)==0
    assert chapter==word(u,campaign+0x3a8)
    assert word(u,campaign+0x3a4)==0
    assert word(u,campaign+0x3a0)==0
    assert u.mem_read(campaign+0x3b0,2)==b'\0\0'
    assert word(u,0x7cce90)==balance
    return dict(robot='Real' if robot else 'Super',balance=balance,chapter=chapter,
                deployment_group=group,campaign_group=word(u,campaign+0x3ac),history_index=0)


def verify(data,stage):
    old=(ROOT/'work/build/ps2/prologue_0.1.6/SLPS_253.45').read_bytes()
    observations=[]
    for robot,chapter in ((1,0),(0,1)):
        for balance in (0,1):
            prior=completion(old,stage,robot,balance)
            assert prior['deployment_group']==prior['campaign_group']==0
            current=completion(data,stage,robot,balance)
            assert current['chapter']==chapter
            assert current['deployment_group']==current['campaign_group']==4,current
            observations.append(current)
    return dict(native_new_game_completion=observations,
                old_build_skip_reproduced=True,both_balance_modes_preserved=True,
                initial_history_convention_preserved=True)


if __name__=='__main__':
    base=ROOT/'work/build/ps2/prologue_0.1.7'
    result=verify((base/'SLPS_253.45').read_bytes(),(base/'STAGE.BIN').read_bytes())
    (ROOT/'work/output/ps2_prologue_0.1.7_entry_execution.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
