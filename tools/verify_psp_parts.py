"""Execute the actual save-loaded native name lookup/copy path in old/new code."""
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_MEM_INVALID
from unicorn import mips_const as mc
import fix_psp_parts as fix

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'work/build/parts_crash_test_0.4.30'
BASE=0x08804000


def execute(fixed):
    memory=bytearray((FIXTURE/'event_list_fault.bin').read_bytes())
    regs=json.loads((FIXTURE/'event_list_fault.json').read_text())['regs']
    panel=struct.unpack_from('<I',memory,regs['sp']-0x08000000+8)[0]
    assert panel==0x08c22bd0
    panel+=0x3e90
    child_pointer=panel+0x810
    correct_pointer=0x08bbf480
    struct.pack_into('<I',memory,child_pointer-0x08000000,correct_pointer)
    if fixed:
        for site in fix.SITES:
            dst=4 if site==0x1e5a90 else 5
            struct.pack_into('<I',memory,BASE+site-0x08000000,
                             0x24000000|(29<<21)|(dst<<16)|fix.NAME_STACK_OFFSET)
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0x08000000,len(memory));u.mem_write(0x08000000,bytes(memory))
    for name,value in regs.items():
        key='UC_MIPS_REG_'+name.upper()
        if hasattr(mc,key):u.reg_write(getattr(mc,key),value)
    u.reg_write(mc.UC_MIPS_REG_S1,panel)
    for reg,slot in ((mc.UC_MIPS_REG_S0,0x08b04e80),
                     (mc.UC_MIPS_REG_S2,0x08b04e7c),
                     (mc.UC_MIPS_REG_S7,0x08b04e84)):
        u.reg_write(reg,struct.unpack('<I',u.mem_read(slot,4))[0])
    faults=[]
    def invalid(u,access,address,size,value,_):
        faults.append(dict(address=hex(address),size=size));return False
    u.hook_add(UC_HOOK_MEM_INVALID,invalid)
    u.emu_start(BASE+0x1e59bc,BASE+0x1e5a94,count=200000)
    assert not faults and u.reg_read(mc.UC_MIPS_REG_PC)==BASE+0x1e5a94
    destination=regs['sp']+fix.NAME_STACK_OFFSET if fixed else panel+0x7dc
    text=bytes(u.mem_read(destination,256)).split(b'\0')[0]
    expected='Full Armor Hyaku Shiki Kai'
    import textfit
    assert text==textfit.encode(expected)
    pointer=struct.unpack('<I',u.mem_read(child_pointer,4))[0]
    assert pointer==(correct_pointer if fixed else correct_pointer&~255)
    return dict(fixed=fixed,native_lookup_and_copy_completed=True,name=expected,
                encoded_bytes_including_terminator=len(text)+1,
                neighboring_pointer_before=hex(correct_pointer),
                neighboring_pointer_after=hex(pointer),name_preserved=True,
                pointer_preserved=pointer==correct_pointer,invalid_memory_accesses=faults)


def main():
    result=dict(regression_reproduced=True,old=execute(False),fixed=execute(True),
                scope='Actual name getter and copy path from the supplied 21-clear save; live menu exit tested separately.')
    path=ROOT/'work/output/psp_parts_native_regression_0.4.31.json'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
