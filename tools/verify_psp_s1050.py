"""Exercise the exact PSP allocator, fallback and release against captured pools."""
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as r
from fix_psp_s1050 import ALLOC_SITE, FREE_SITE, reserved_address, patch_boot
from insert_text import elf
from verify_text_build import read_iso

ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/'work/build/next_stage_crash_055/map_ram.bin'
BASE=0x08000000
CTL=0x08D19480
BIG=CTL+0x38
SMALL=CTL+0x10040
SCENE=CTL+0xCD3A8
SPAN=0x10008
SP=0x701000


def verify(original, patched, capture):
    assert patched==patch_boot(original) and patched==patch_boot(patched)
    ph=struct.unpack_from('<I',original,28)[0]
    size=struct.unpack_from('<I',original,ph+16)[0]
    before=original[0x60:0x60+size];after=patched[0x60:0x60+size]
    allowed={i for va in (ALLOC_SITE,FREE_SITE) for i in range(va,va+4)}
    assert {i for i,(a,b) in enumerate(zip(before,after)) if a!=b}<=allowed
    def relocs(boot):
        h=elf(boot)['.rel.text'];a,n=struct.unpack_from('<2I',boot,h+16)
        return boot[a:a+n]
    old_rel,new_rel=relocs(original),relocs(patched)
    assert new_rel.startswith(old_rel) and len(new_rel)==len(old_rel)+24
    pools=[capture[p-BASE:p-BASE+SPAN] for p in (BIG,SMALL)]
    assert all(len(h)==SPAN for h in pools)
    reserve=reserved_address((struct.unpack_from('<I',patched,ALLOC_SITE+0x60)[0]&0x3ffffff)<<2)

    def setup(boot):
        u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
        u.mem_map(0,0x800000);u.mem_map(BASE,0x2000000)
        ph=struct.unpack_from('<I',boot,28)[0];size=struct.unpack_from('<I',boot,ph+16)[0]
        u.mem_write(0,boot[0x60:0x60+size])
        # Silence the original allocator's diagnostic print. The allocator
        # and free routines themselves execute without substitution.
        u.mem_write(0x258180,bytes.fromhex('0800e00300000000'))
        for p,data in zip((BIG,SMALL),pools):u.mem_write(p,data)
        return u

    def call(u,site,argument):
        for reg,val in [(r.UC_MIPS_REG_S0,CTL),(r.UC_MIPS_REG_A0,SMALL),
                        (r.UC_MIPS_REG_A1,argument),(r.UC_MIPS_REG_AT,0x10040),
                        (r.UC_MIPS_REG_SP,SP)]:u.reg_write(reg,val)
        u.emu_start(site,site+8,count=200000)
        assert u.reg_read(r.UC_MIPS_REG_PC)==site+8 and u.reg_read(r.UC_MIPS_REG_SP)==SP
        assert u.reg_read(r.UC_MIPS_REG_S0)==CTL
        return u.reg_read(r.UC_MIPS_REG_V0)

    def table(u,p):return bytes(u.mem_read(p,SPAN))

    def inside(u,p,ptr):
        a,z=struct.unpack('<II',u.mem_read(p,8))
        return a<=ptr<a+z

    def has(u,p,ptr):return ptr in struct.unpack('<8192I',u.mem_read(p+8,0x8000))

    def run(label,boot,scene,size,owner=None,full=False,cycles=1):
        u=setup(boot)
        if full:
            a,z=struct.unpack('<II',u.mem_read(BIG,8))
            h=bytearray(SPAN);struct.pack_into('<III',h,0,a,z,a);struct.pack_into('<I',h,0x8008,z)
            u.mem_write(BIG,bytes(h))
        start=[table(u,p) for p in (BIG,SMALL)]
        results=[]
        for _ in range(cycles):
            u.mem_write(SCENE,scene.encode().ljust(16,b'\0'))
            ptr=call(u,ALLOC_SITE,size);results.append(ptr)
            if owner:
                if owner=='reserve':
                    assert ptr==reserve and not any(inside(u,p,ptr) for p in (BIG,SMALL))
                    assert [table(u,p) for p in (BIG,SMALL)]==start
                else:
                    assert inside(u,SMALL,ptr) and has(u,SMALL,ptr),(label,hex(ptr))
                    assert table(u,BIG)==start[0]
                # The next scenario can already be named when old storage is freed.
                u.mem_write(SCENE,b's1060\0')
                call(u,FREE_SITE,ptr)
            else:assert ptr==0,(label,hex(ptr))
            assert [table(u,p) for p in (BIG,SMALL)]==start,label
        return dict(case=label,scene=scene,request=size,returns=results,
                    owner='reserve' if owner=='reserve' else 'script' if owner==SMALL else None,
                    cycles=cycles,pool_tables_restored=True)

    return dict(passed=True,native_allocator_and_free_executed=True,
                original_loaded_code_and_data_preserved_except_two_calls=True,
                original_relocations_preserved=True,cases=[
        run('original failure',original,'s1050',0x32800),
        run('corrected fallback and repeated cleanup',patched,'s1050',0x32800,'reserve',cycles=3),
        run('target fits normal pool',patched,'s1050',0x25000,SMALL),
        run('other scene normal allocation',patched,'s1060',0x27000,SMALL),
        run('other scene failed allocation does not fall back',patched,'s1060',0x32800),
        run('different name with same prefix does not fall back',patched,'s10501',0x32800),
        run('both pools full',patched,'s1050',0x32800,'reserve',full=True),
        run('request above reserve capacity is rejected',patched,'s1050',0x33000),
        run('zero byte request is rejected',patched,'s1050',0)])


if __name__=='__main__':
    boot=read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.55.iso'),['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    result=verify(boot,patch_boot(boot),CAPTURE.read_bytes())
    (ROOT/'work/output/psp_s1050_0.4.57_native_execution.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Passed',len(result['cases']),'native allocation/release cases')
