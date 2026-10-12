"""Execute a captured PSP equip callback with its actual save-loaded memory."""
import collections
import json
from pathlib import Path
import struct
import capstone
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_INVALID
from unicorn import mips_const as mc

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/build/parts_crash_test_0.4.30'


def main():
    regs=json.loads((OUT/'equip_handler.json').read_text())['regs']
    ram=(OUT/'equip_memory.bin').read_bytes()
    u=Uc(UC_ARCH_MIPS, UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0x08000000,len(ram));u.mem_write(0x08000000,ram)
    for name,value in regs.items():
        key='UC_MIPS_REG_'+name.upper()
        if hasattr(mc,key):u.reg_write(getattr(mc,key),value)
    history=collections.deque(maxlen=100)
    copies=[];invalid=[];calls=[]
    base=0x08804000
    def code(u,pc,size,_):
        history.append(pc)
        if pc in (base+0x259438,base+0x259020):
            a0=u.reg_read(mc.UC_MIPS_REG_A0);a1=u.reg_read(mc.UC_MIPS_REG_A1)
            value=bytes(u.mem_read(a1,256)).split(b'\0')[0]
            copies.append(dict(pc=hex(pc-base),ra=hex(u.reg_read(mc.UC_MIPS_REG_RA)-base),
                               dest=hex(a0),src=hex(a1),bytes=len(value)+1,text=value.decode('cp932','replace')))
        raw=struct.unpack('<I',u.mem_read(pc,4))[0]
        if raw>>26==3: calls.append(hex(((raw&0x3ffffff)<<2)|((pc+4)&0xf0000000)))
    def fault(u,access,address,size,value,_):
        invalid.append(dict(access=access,address=hex(address),size=size,value=value));return False
    u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_INVALID,fault)
    error=None
    try:u.emu_start(regs['pc'],regs['ra'],count=2000000)
    except Exception as e:error=str(e)
    md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
    instructions=[]
    for pc in history:
        if 0x08000000<=pc<0x0a000000:
            ins=list(md.disasm(bytes(u.mem_read(pc,4)),pc))
            instructions.append(hex(pc-base)+' '+(ins[0].mnemonic+' '+ins[0].op_str if ins else 'unknown'))
    result=dict(error=error,pc=hex(u.reg_read(mc.UC_MIPS_REG_PC)),invalid=invalid,copies=copies,
        calls=calls[-100:],registers={n:hex(u.reg_read(getattr(mc,'UC_MIPS_REG_'+n.upper()))) for n in regs if hasattr(mc,'UC_MIPS_REG_'+n.upper())},instructions=instructions)
    (OUT/'native_equip_trace.json').write_text(json.dumps(result,indent=1,ensure_ascii=False))
    print(json.dumps({k:result[k] for k in ['error','pc','invalid','copies']},ensure_ascii=False))
    print('\n'.join(instructions[-30:]))


if __name__=='__main__':main()
