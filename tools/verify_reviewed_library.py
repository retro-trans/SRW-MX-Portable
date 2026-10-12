"""Validate a reviewed library refresh before using historical regression data."""
import struct
from pathlib import Path
from unicorn import mips_const as reg
import insert_text as it
from fix_ps2_library import sentences
from port_ps2_translations import ROOT, read_json, sha
from static2_extract import sections,index
from verify_ps2_font import machine


def structural(base):
    report=read_json(base/'library_refresh.json')
    prior=ROOT/report['baseline_directory']
    old=(prior/'SLPS_253.45').read_bytes();before=(prior/'FIX00.DAT').read_bytes()
    data=(base/'SLPS_253.45').read_bytes();fix=(base/'FIX00.DAT').read_bytes()
    for raw,key in [(old,'source_elf_sha256'),(before,'source_fix_sha256'),(data,'target_elf_sha256'),(fix,'target_fix_sha256')]:
        assert sha(raw)==report[key],key
    # All prior instructions/font/UI strings remain exact outside declared
    # table, segment-size/heap and native title-footer changes.
    restored=bytearray(data[:len(old)])
    for first,last in report['elf_ranges']:
        assert 0<=first<last<=len(old)
        restored[first:last]=old[first:last]
    assert restored==old,'Unrelated executable bytes changed'
    a=sections(before,0);b=sections(fix,0);assert set(a)==set(b) and len(fix)<=len(before)
    for tag,(off,size,count) in a.items():
        if tag in ('Sent','Fixh','Xunt','XPlt'):continue
        at,n,c=b[tag];assert (n,c)==(size,count) and before[off:off+size]==fix[at:at+n],tag
    old_rows,old_ptrs=sentences(before,old);rows,ptrs=sentences(fix,data)
    released=set(report['released_sentence_ids'])
    for n,raw in enumerate(old_rows):
        if n not in released:assert rows[n]==raw and (not old_ptrs[n]&0x80000000 or ptrs[n]==old_ptrs[n]),n
    tags=('Xunt','XPlt','XSpr','XSkl','Xabl','XPrt','XHlp')
    old_tables={t:index(before,a[t][0],a[t][2]) for t in tags}
    tables={t:index(fix,b[t][0],b[t][2]) for t in tags}
    protected={n for t in tags if t not in ('Xunt','XPlt') for ids in old_tables[t] for n in ids}
    assert not released&protected
    library=read_json(base/'library.json');assert len(library['description_rows'])==512
    for row in library['description_rows']:
        ids=tables[row['table']][row['entry']];assert ids==row['sentence_ids']
        assert [rows[n] for n in ids]==[it.encode(line) for line in row['lines']]
        assert ' '.join(row['lines']).split()==row['english'].split()
    changed={(r['table'],r['entry']) for r in report['changed_entries']}
    for t in ('Xunt','XPlt'):
        assert len(tables[t])==len(old_tables[t])
        for n,ids in enumerate(old_tables[t]):
            if (t,n) not in changed:assert tables[t][n]==ids,(t,n)
    # Execute the current native width routine for every newly written row.
    u=machine(data);state=u.context_save();checks=0
    for row in library['description_rows']:
        if (row['table'],row['entry']) not in changed:continue
        for line in row['lines']:
            expanded=line.replace('#男愛称','\u3042'*6).replace('#女愛称','\u3042'*6)
            encoded=it.encode(expanded);assert len(encoded)<=128
            u.context_restore(state);u.mem_write(0x900000,struct.pack('<2f',24,24)+bytes(64));u.mem_write(0x910000,encoded)
            for register,value in [(reg.UC_MIPS_REG_A0,0x900000),(reg.UC_MIPS_REG_A1,0x910000),(reg.UC_MIPS_REG_RA,0x920000)]:u.reg_write(register,value)
            u.emu_start(0x131ba0,0x920000,count=200000)
            assert u.reg_read(reg.UC_MIPS_REG_PC)==0x920000
            width=struct.unpack('<f',struct.pack('<I',u.reg_read(reg.UC_MIPS_REG_F0)&0xffffffff))[0]
            assert width<=560,(row['table'],row['entry'],width);checks+=1
    # Independently retain the strict original reflow proof before returning
    # its pre-library fixture to tests for the older gameplay port.
    from verify_ps2_library import structural as original_structural
    historical=original_structural(ROOT/report['historical_reflow_directory'])
    return dict(source_directory=historical['source_directory'],numeric_gameplay_records_preserved=True,
                native_width_rows=checks,changed_entries=len(changed),unrelated_elf_bytes_preserved=True)
