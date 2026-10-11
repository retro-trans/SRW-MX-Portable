"""Execute native narration widths and verify wording, timing and preservation."""
import json
import struct
import unicodedata
from unicorn import mips_const as reg
from verify_ps2_font import machine
from port_ps2_translations import ROOT,read_json,sha
from port_ps2_prologue import save
from ps2_font4x import FILE_BIAS
from ps2_narration_port import TABLES,BLANK,END,LINE_PX,ROW_BYTES
import insert_text as it


def verify(base,version):
    data=(base/'SLPS_253.45').read_bytes();meta=read_json(base/'patch.json')
    old=(ROOT/'work/build/ps2/favorites_0.1.18/SLPS_253.45').read_bytes()
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    report=read_json(base/'narration.json')
    assert sha(data)==meta['target_sha256']==report['target_sha256']
    assert sha(old)==report['source_sha256']
    def off(blob,va):
        for n in range(struct.unpack_from('<H',blob,44)[0]):
            kind,pos,addr,_,size,*_=struct.unpack_from('<8I',blob,52+n*32)
            if kind==1 and addr<=va<addr+size:return pos+va-addr
        raise AssertionError(hex(va))
    def raw(blob,va):
        start=off(blob,va);return blob[start:blob.index(0,start)]
    def decoded(blob,va):
        return it.clean(unicodedata.normalize('NFKC',raw(blob,va).decode('cp932')))
    u=machine(data);initial=u.context_save()
    def native_width(text):
        # Maximum editable nicknames, six native full-width glyphs each.
        expanded=text.replace('#男愛称','あ'*6).replace('#女愛称','あ'*6)
        encoded=it.encode(expanded)
        u.context_restore(initial)
        u.mem_write(0x900000,struct.pack('<2f',24,24)+bytes(0x34))
        u.mem_write(0x910000,encoded)
        u.reg_write(reg.UC_MIPS_REG_A0,0x900000)
        u.reg_write(reg.UC_MIPS_REG_A1,0x910000)
        u.reg_write(reg.UC_MIPS_REG_RA,0x920000)
        u.emu_start(0x131ba0,0x920000,count=200000)
        assert u.reg_read(reg.UC_MIPS_REG_PC)==0x920000
        return struct.unpack('<f',struct.pack('<I',u.reg_read(reg.UC_MIPS_REG_F0)&0xffffffff))[0]
    allowed=set(range(164,172))
    allowed.update(range(0x100180-FILE_BIAS,0x100184-FILE_BIAS))
    allowed.update(range(0x100188-FILE_BIAS,0x10018c-FILE_BIAS))
    groups={};native_cases=[];previous_clipped=[]
    for name,(first,after) in TABLES.items():
        source=[struct.unpack_from('<iII',original,o) for o in range(first,after,12)]
        before=[struct.unpack_from('<iII',old,o) for o in range(first,after,12)]
        current=[struct.unpack_from('<iII',data,o) for o in range(first,after,12)]
        assert [r[:2] for r in source]==[r[:2] for r in before]==[r[:2] for r in current]
        assert current[-1][2]==source[-1][2]==END
        for o in range(first,after-12,12):allowed.update(range(o+8,o+12))
        texts=[decoded(data,r[2]) for r in current[:-1] if r[2]!=BLANK]
        old_texts=[decoded(old,r[2]) for r in before[:-1] if r[2]!=BLANK]
        assert ' '.join(texts)==' '.join(old_texts),'Narration wording/placeholder changed'
        assert texts==[r['english'] for r in report[name]['lines']]
        for row in report[name]['lines']:
            assert raw(data,int(row['pointer'],16))==it.encode(row['english'])[:-1]
            width=native_width(row['english'])
            assert width==row['native_width_px'] and width<=LINE_PX,(name,row,width)
            assert row['encoded_bytes']==len(it.encode(row['english']))<=ROW_BYTES
            native_cases.append(dict(group=name,english=row['english'],native_width=width,encoded_bytes=row['encoded_bytes']))
        for text in old_texts:
            width=native_width(text)
            if width>LINE_PX:previous_clipped.append(dict(group=name,english=text,width=width))
        groups[name]=dict(records=len(current),translated_lines=len(texts),
                         unchanged_commands_and_delays=True,unchanged_end_record=True,
                         wording_and_placeholders_unchanged=True,
                         maximum_width=max(r['native_width_px'] for r in report[name]['lines']))
    from ps2_library_preservation import baseline_bytes as before_library
    comparison=before_library(base,'SLPS_253.45')
    unexpected=[i for i in range(len(old)) if old[i]!=comparison[i] and i not in allowed]
    assert not unexpected,unexpected[:20]
    # All prior assets and corrections are exact copies; no campaign rebuilding.
    prior=ROOT/'work/build/ps2/favorites_0.1.18'
    preserved={}
    for path in prior.iterdir():
        if path.suffix in ('.BIN','.DAT'):
            from ps2_battle_label_preservation import baseline_bytes
            a=path.read_bytes();b=baseline_bytes(base,path.name);assert a==b,path.name
            preserved[path.name]=sha(b)
    assert previous_clipped,'Regression fixture must reproduce the reported clipping'
    result=dict(version=version,source_public_version='0.4.12',font_size=24,
                native_text_x=68,safe_right_edge=628,screen_width=640,
                maximum_line_width=LINE_PX,native_width_execution_cases=len(native_cases),
                previous_overwide_lines=len(previous_clipped),previous_overwide_examples=previous_clipped,
                groups=groups,native_width_cases=native_cases,
                prior_executable_unchanged_except_pointer_tables_and_heap_sizes=True,
                preserved_resources=preserved,source_sha256=sha(old),target_sha256=sha(data),
                visual_validation='pending',physical_ps2_validation='pending')
    save(ROOT/'work/output'/f'ps2_narration_{version}_execution.json',result)
    print(json.dumps(dict(version=version,passed=True,native_lines=len(native_cases),old_clipped=len(previous_clipped),groups=groups),indent=2))
    return result
