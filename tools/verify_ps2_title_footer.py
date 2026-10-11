"""Execute title-state guards, native width calls and draw arguments."""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from ps2_title_footer import verify, URL
from verify_ps2_font import machine

ROOT=Path(__file__).resolve().parents[1]

def main(version='0.4.26'):
    elf=(ROOT/f'work/build/ps2/font_{version}/SLPS_253.45').read_bytes()
    info=verify(elf,version);va=int(info['renderer_va'],16)
    u=machine(elf,r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    draws=[];calls=[]
    def service(m,address,size,user):
        if address not in (0x12e640,0x130498,0x1305d8,0x130610):return
        calls.append(hex(address))
        if address==0x130498:m.mem_write(m.reg_read(r.UC_MIPS_REG_A0),bytes(96))
        if address==0x130610:
            ptr=m.reg_read(r.UC_MIPS_REG_A1)
            text=bytes(m.mem_read(ptr,64)).split(b'\0')[0]
            draws.append(dict(text=text.hex(),x=m.reg_read(r.UC_MIPS_REG_A2),y=m.reg_read(r.UC_MIPS_REG_A3)))
        m.reg_write(r.UC_MIPS_REG_PC,m.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    cases=[]
    for state in range(7):
        for phase in (0,2,3,4,7,200):
            u.reg_write(r.UC_MIPS_REG_SP,0xa00000);u.reg_write(r.UC_MIPS_REG_RA,0x920000)
            u.reg_write(r.UC_MIPS_REG_S1,0x900000)
            for reg,value in [(r.UC_MIPS_REG_S0,111),(r.UC_MIPS_REG_S2,222),(r.UC_MIPS_REG_S3,333)]:u.reg_write(reg,value)
            u.mem_write(0x901284,struct.pack('<2I',state,phase));draws.clear();calls.clear()
            u.emu_start(va,0x920000,count=20000)
            expected=state in (4,5) and phase>=3
            assert len(draws)==(4 if expected else 0),(state,phase,draws)
            assert calls[0]=='0x12e640' and calls.count('0x12e640')==1
            assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
            assert [u.reg_read(reg) for reg in (r.UC_MIPS_REG_S0,r.UC_MIPS_REG_S2,r.UC_MIPS_REG_S3)]==[111,222,333]
            if expected:
                assert draws[1]['text']==it.encode('v'+version)[:-1].hex()
                assert draws[3]['text']==it.encode(URL)[:-1].hex()
                assert [x['y'] for x in draws]==[251,250,269,268]
                assert all(400<=x['x']<=626 for x in draws)
            cases.append(dict(state=state,phase=phase,draws=len(draws)))
    out=ROOT/f'work/output/ps2_title_footer_{version}_execution.json'
    out.write_text(json.dumps(dict(version=version,passed=True,cases=cases,native_width_executed=True,
        original_draw_call_preserved=True,callee_saved_registers_preserved=True),indent=2)+'\n',encoding='utf8')
    print('Passed',len(cases),'title state/phase cases')

if __name__=='__main__':
    import sys
    main(*sys.argv[1:])
