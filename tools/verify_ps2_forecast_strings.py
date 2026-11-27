"""Reproduce strict-alignment forecast faults and test complete safe copies."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from unicorn import UcError, UC_HOOK_CODE, mips_const as r
from verify_ps2_font import machine
from fix_ps2_forecast_strings import COPY_SITES
import insert_text as it

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ('left_no_counter',0x179720,0x179800),
    ('left_support_def',0x179764,0x179800),
    ('right_support_def',0x17a284,0x17a2f8),
    ('right_original_no_counter',0x17a238,0x17a2f8),
]


def read_string(vm, pointer):
    data=bytes(vm.mem_read(pointer,128))
    return data[:data.index(0)+1]


def run_path(data,start,width_site,dirty,flag):
    vm=machine(data,r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    vm.mem_write(0xa00000,bytes([dirty])*0x300)
    vm.mem_write(0x900282,struct.pack('<h',flag))
    for reg,value in [(r.UC_MIPS_REG_S1,0x900000),(r.UC_MIPS_REG_S2,0x900400),
                      (r.UC_MIPS_REG_S3,7),(r.UC_MIPS_REG_A1,8)]:vm.reg_write(reg,value)
    trace=[]
    vm.hook_add(UC_HOOK_CODE,lambda u,pc,s,_:trace.append(pc))
    try:
        vm.emu_start(start,width_site,count=1000)
        return vm,dict(passed=True,last_pc=hex(trace[-1]))
    except UcError as error:
        return vm,dict(passed=False,error=str(error),last_pc=hex(trace[-1]),
                       source_pointer=hex(vm.reg_read(r.UC_MIPS_REG_V0)))


def verify(directory):
    directory=Path(directory)
    target=(directory/'SLPS_253.45').read_bytes()
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    public=(ROOT/'work/build/hardware_issues_20261126/PS2_ELF_0.9.0.BIN').read_bytes()
    fix=json.loads((directory/'forecast_fix.json').read_text())
    helper=int(fix['helper_va'],16)
    repro=[]
    for name,start,width_site in PATHS[:3]:
        _,stock=run_path(original,start,width_site,0xa5,0)
        _,broken=run_path(public,start,width_site,0xa5,0)
        assert stock['passed'] and not broken['passed'],(name,stock,broken)
        assert 'UC_ERR_READ_UNALIGNED' in broken['error'],broken
        repro.append(dict(path=name,original=stock,public=broken))
    probe_repro=[]
    for kind,version in [('font','0.9.1'),('layout','0.9.2'),('menu','0.9.3')]:
        probe=(ROOT/('work/build/ps2/hardware_%s_probe_%s/SLPS_253.45'%(kind,version))).read_bytes()
        for name,start,width_site in PATHS[:3]:
            _,broken=run_path(probe,start,width_site,0xa5,0)
            assert not broken['passed'] and 'UC_ERR_READ_UNALIGNED' in broken['error']
            probe_repro.append(dict(version=version,path=name,result=broken))
    cases=[]
    for name,start,width_site in PATHS:
        # Read the actual selected source pointer immediately before its copy.
        site=next((row['site'] for row in COPY_SITES if row['name']==name),0x17a28c)
        for dirty in (0,0xa5,0x7f):
            for flag in (0,1):
                vm=machine(target,r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
                vm.mem_write(0xa00000,bytes([dirty])*0x300)
                vm.mem_write(0x900282,struct.pack('<h',flag))
                for reg,value in [(r.UC_MIPS_REG_S1,0x900000),(r.UC_MIPS_REG_S2,0x900400),
                                  (r.UC_MIPS_REG_S3,7),(r.UC_MIPS_REG_A1,8)]:vm.reg_write(reg,value)
                vm.emu_start(start,site,count=40)
                pointer=vm.reg_read(r.UC_MIPS_REG_V0)
                expected=read_string(vm,pointer)
                assert len(expected)<=64
                source=bytes(vm.mem_read(pointer,len(expected)))
                vm.emu_start(site,width_site,count=1000)
                # Unicorn can report the final executed instruction before an
                # end-address JAL. A0 below confirms the native continuation ran.
                assert vm.reg_read(r.UC_MIPS_REG_PC) in (width_site,width_site-4),(name,dirty,flag,hex(vm.reg_read(r.UC_MIPS_REG_PC)))
                assert bytes(vm.mem_read(0xa00000,len(expected)))==expected
                assert bytes(vm.mem_read(0xa00000+len(expected),0x300-len(expected)))==bytes([dirty])*(0x300-len(expected))
                assert bytes(vm.mem_read(pointer,len(source)))==source
                assert vm.reg_read(r.UC_MIPS_REG_SP)==0xa00000
                assert vm.reg_read(r.UC_MIPS_REG_A0)==0x900400
                expected_s3=1 if name=='left_support_def' and flag else 7
                assert vm.reg_read(r.UC_MIPS_REG_S3)==expected_s3
                cases.append(dict(path=name,dirty_byte=dirty,support_flag=flag,
                                  source_alignment=pointer%8,bytes=len(expected),
                                  nul_terminated=True,source_and_stack_guards_preserved=True))
    alignments=[]
    for text in ('No Counter','Support Def','None'):
        raw=it.encode(text)
        for alignment in range(8):
            vm=machine(target,r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
            vm.mem_write(0xa00000,b'\xa5'*128)
            pointer=0x910000+alignment
            vm.mem_write(pointer,raw)
            vm.reg_write(r.UC_MIPS_REG_V0,pointer)
            vm.emu_start(helper,0x920000,count=1000)
            assert bytes(vm.mem_read(0xa00000,len(raw)))==raw
            assert bytes(vm.mem_read(0xa00000+len(raw),128-len(raw)))==b'\xa5'*(128-len(raw))
            assert vm.reg_read(r.UC_MIPS_REG_SP)==0xa00000
            alignments.append(dict(text=text,alignment=alignment,bytes=len(raw)))
    report=dict(passed=True,reproduced_public_faults=repro,failed_probe_reproduction=probe_repro,forecast_path_cases=cases,
                arbitrary_alignment_cases=alignments,heap_boundary_preserved=fix['heap_boundary_preserved'],
                target_elf_sha256=hashlib.sha256(target).hexdigest(),
                scope='Strict MIPS memory alignment and real forecast copy/control paths; physical PS2 test pending.')
    (directory/'forecast_execution.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(passed=True,reproduced_faults=len(repro),forecast_path_cases=len(cases),alignment_cases=len(alignments))))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=ROOT/'work/build/ps2/forecast_strings_0.9.4')
    verify(parser.parse_args().directory)
