"""Execute normal and overflow battle pointer paths and every spirit getter."""
import struct
from unicorn import mips_const as reg
from verify_ps2_font import machine
from ps2_battle_port import SITES
from port_ps2_translations import ROOT,read_json
import insert_text as it

def verify(data,native):
    u=machine(data);initial=u.context_save();checks=0
    table=int(native['battle']['overflow_table_va'],16)
    overflow=read_json(ROOT/'work/build/ps2/campaign/quote_overflow.json')
    for i,(site,base,off,dest,next_) in enumerate(SITES):
        for n in [-1,0,len(overflow)-1]:
            u.context_restore(initial)
            u.reg_write(reg.UC_MIPS_REG_16,0x940000);u.reg_write(reg.UC_MIPS_REG_17,0x940100)
            u.reg_write(reg.UC_MIPS_REG_V1,0x940200)
            u.mem_write(0x940034,struct.pack('<I',0x11223344))
            u.mem_write(0x940134,struct.pack('<I',0x55667788))
            u.reg_write(getattr(reg,'UC_MIPS_REG_'+str(base)),0x930000)
            u.reg_write(getattr(reg,'UC_MIPS_REG_'+str(off)),0x20 if n<0 else 0x8000+n)
            wanted=0x930020 if n<0 else struct.unpack('<I',u.mem_read(table+4*n,4))[0]
            end=0x920000 if next_ is None else site+8
            u.emu_start(site,end,count=100)
            assert u.reg_read(reg.UC_MIPS_REG_PC)==end
            assert u.reg_read(getattr(reg,'UC_MIPS_REG_'+str(dest)))==wanted,(i,n)
            assert u.reg_read(reg.UC_MIPS_REG_RA)==0x920000
            if i==0:assert u.reg_read(reg.UC_MIPS_REG_A1)==0x11223344
            if i==1:assert u.reg_read(reg.UC_MIPS_REG_A2)==0x55667788
            if i==2:assert struct.unpack('<I',u.mem_read(0x940230,4))[0]==wanted
            checks+=1
    spirits=native['spirits'];table=int(spirits['table_va'],16)
    for i,en in enumerate(spirits['english_names']):
        u.context_restore(initial);u.reg_write(reg.UC_MIPS_REG_A1,i)
        u.emu_start(0x332730,0x920000,count=100)
        ptr=u.reg_read(reg.UC_MIPS_REG_V0);encoded=it.encode(en)
        assert bytes(u.mem_read(ptr,len(encoded)))==encoded
        assert ptr==struct.unpack('<I',u.mem_read(table+4*i,4))[0]
        checks+=1
    u.context_restore(initial);u.reg_write(reg.UC_MIPS_REG_A1,32)
    u.emu_start(0x332730,0x332788,count=100)
    assert u.reg_read(reg.UC_MIPS_REG_PC)==0x332788
    result=dict(battle_normal_and_overflow_cases=12,spirit_names=32,spirit_out_of_range_fallback=True,cases=checks+1)
    if 'sentences' in native:
        from static2_extract import sections,index
        fix=(ROOT/'work/build/ps2/campaign/FIX00.DAT').read_bytes();s=sections(fix,0)
        u.mem_write(0xa00000,fix);u.mem_write(0x940000,struct.pack('<I',0xa00000+s['Sent'][0]))
        initial=u.context_save();rows=0;external=0
        report=read_json(ROOT/'work/translation/en/ps2/database_port.en.json')
        names_checked=0
        for item in report['texts']:
            if item['table']!='Strg':continue
            # The untouched getter's MOVN in a JR delay slot is unsupported by
            # this Unicorn build. Read back its original offset-table format.
            ptr=struct.unpack_from('<I',fix,s['Strg'][0]+12+4*item['entry'])[0]
            encoded=it.encode(it.clean(item['english']))
            assert fix[s['Strg'][0]+ptr:s['Strg'][0]+ptr+len(encoded)]==encoded,('Strg',item['entry'])
            names_checked+=1
        indexes={tag:index(fix,s[tag][0],s[tag][2]) for tag in ('Xunt','XPlt','XSpr','XSkl','Xabl','XPrt','XHlp')}
        for item in report['texts']:
            if item['table']=='Strg':continue
            ids=indexes[item['table']][item['entry']];assert len(ids)==len(item['lines'])
            for ident,line in zip(ids,item['lines']):
                u.context_restore(initial);u.reg_write(reg.UC_MIPS_REG_A0,0x940000);u.reg_write(reg.UC_MIPS_REG_A1,ident)
                u.emu_start(0x332518,0x920000,count=100);ptr=u.reg_read(reg.UC_MIPS_REG_V0);encoded=it.encode(line)
                assert bytes(u.mem_read(ptr,len(encoded)))==encoded,(item['table'],item['entry'],ident)
                external+=int(ptr<0x800000);rows+=1
        # Original negative sentinel still returns a null pointer.
        u.mem_write(0xa00000+s['Sent'][0]+12,struct.pack('<I',0xffffffff))
        u.context_restore(initial);u.reg_write(reg.UC_MIPS_REG_A0,0x940000);u.reg_write(reg.UC_MIPS_REG_A1,0)
        u.emu_start(0x332518,0x920000,count=100);assert u.reg_read(reg.UC_MIPS_REG_V0)==0
        result.update(database_names_readback=names_checked,database_description_rows=rows,database_external_row_reads=external,sentence_negative_sentinel_preserved=True)
    return result
