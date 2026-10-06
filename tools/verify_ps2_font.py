"""Execute the packaged PS2 VWF hooks and width functions in a MIPS emulator.

This verifies arithmetic, fallback paths, glyph pointers and upload parameters.
It does not replace PCSX2/physical PS2 rendering and gameplay validation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as reg
from ps2_font4x import SITES, CELL, GLYPH_BYTES, FILE_BIAS


def machine(data, cpu_model=None):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS64|UC_MODE_LITTLE_ENDIAN)
    if cpu_model is not None:u.ctl_set_cpu_model(cpu_model)
    u.mem_map(0x100000,0xa00000)
    for n in range(struct.unpack_from('<H',data,44)[0]):
        kind,off,va,pa,fs,ms,flags,align=struct.unpack_from('<8I',data,52+n*32)
        if kind==1:u.mem_write(va,data[off:off+fs])
    u.reg_write(reg.UC_MIPS_REG_SP,0xa00000)
    u.reg_write(reg.UC_MIPS_REG_RA,0x920000)
    return u


def verify(original, patched, metadata):
    # Unicorn accepts wider MIPS encodings than the EE. Reject unsupported
    # COP1 operations before emulation so generic MIPS C.LT cannot slip in.
    code_offset=int(metadata['segment_offset'],16)+int(metadata['code_va'],16)-int(metadata['segment_va'],16)
    code=patched[code_offset:code_offset+metadata['code_bytes']]
    for word, in struct.iter_unpack('<I',code):
        if word>>26==0x11 and (word>>21)&31==16:
            assert word&63 in (0,1,2,3,4,5,6,7,22,24,25,26,28,29,30,31,36,40,41,48,50,52,54),hex(word)
    baseline=machine(original);u=machine(patched);initial=u.context_save()
    table=bytes(u.mem_read(int(metadata['table_va'],16),384*4))
    # The real GS packet uses an absolute right UV. Every nontransparent
    # atlas sample must lie within that interval, including narrow letters.
    for g in metadata['glyphs']:
        bitmap=bytes(u.mem_read(int(metadata['atlas_va'],16)+(g['index']-1)*GLYPH_BYTES,GLYPH_BYTES))
        for offset,packed in enumerate(bitmap):
            for half,value in enumerate((packed&15,packed>>4)):
                if value:
                    pixel=offset*2+half;x=pixel%96;y=pixel//96
                    assert g['left']*4<=x<g['width']*4 and g['left']*4<=y<96,(g['character'],x,y)
    baseline_cases=0
    if metadata.get('font_revision')=='shared_high_resolution_baseline':
        bottoms=[]
        for g in metadata['glyphs']:
            if g['character']==' ':continue
            bounds=g['ink_bounds'];source=g['source_bounds']
            assert g['baseline']==74 and not g['vertical_rescaling']
            assert bounds[1]==source[1] and bounds[3]==source[3],g['character']
            assert bounds[3]<=94,(g['character'],'descender bottom guard')
            if g['character'] in 'ABCEFHIKLMNPRSTUVWXYZabcefhiklmnorstuvwxz':bottoms.append(bounds[3])
            baseline_cases+=1
        # The font's natural overshoot is a quarter of one original pixel,
        # rather than the full pixel variation introduced by 20px hinting.
        assert max(bottoms)-min(bottoms)<=1,bottoms
    widths=[]
    def width(entry, raw, w, h, flag=0, base=False):
        m=baseline if base else u
        m.context_restore(baseline_initial if base else initial)
        m.mem_write(0x900000,struct.pack('<2f',w,h)+bytes(0x30)+struct.pack('<I',flag))
        m.mem_write(0x910000,raw+b'\0')
        m.reg_write(reg.UC_MIPS_REG_A0,0x900000)
        m.reg_write(reg.UC_MIPS_REG_A1,0x910000)
        m.emu_start(entry,0x920000,count=20000)
        assert m.reg_read(reg.UC_MIPS_REG_PC)==0x920000
        if entry in (0x131ba0,0x131c60):
            return struct.unpack('<f',struct.pack('<I',m.reg_read(reg.UC_MIPS_REG_F0)&0xffffffff))[0]
        return m.reg_read(reg.UC_MIPS_REG_V0)
    baseline_initial=baseline.context_save()
    entries=[(0x1319c0,False,False),(0x131a88,True,False),
             (0x131ba0,False,True),(0x131c60,True,True)]
    for entry,ascii_,floating in entries:
        chars=list(range(32,127)) if ascii_ else [int(g['sjis'],16) for g in metadata['glyphs']]
        for c in chars:
            sjis=struct.unpack_from('<H',original,0x470250-FILE_BIAS+c*2)[0] if ascii_ else c
            slot=sjis-0x8140;slot-= (slot>>8)*64
            if not 0<=slot<384:continue
            advance=table[slot*4]
            if not advance:continue
            raw=bytes([c]) if ascii_ else sjis.to_bytes(2,'big')
            for w,h in [(24,24),(16,24),(32,24),(20,24),(20,30),(20,20),(12,24),(6,12)]:
                size=(h if w*2==h else min(w,h)) if metadata.get('latin_uniform_aspect') else h if w/h<10/13 or w>h else w
                expected=advance*size/24
                if not floating:expected=int(expected)
                actual=width(entry,raw,w,h)
                assert abs(actual-expected)<0.0001,(hex(entry),hex(sjis),w,h,actual,expected)
                widths.append(dict(entry=hex(entry),code=hex(sjis),size=[w,h],actual=actual))
    fallbacks=[]
    for entry in (0x1319c0,0x131ba0):
        for code in (0x82a0,0x8341,0x889f,0x8141,0x8175):
            raw=code.to_bytes(2,'big')
            for flag in (0,1):
                a=width(entry,raw,24,24,flag,True);b=width(entry,raw,24,24,flag)
                assert a==b,(hex(entry),hex(code),flag,a,b)
                fallbacks.append(dict(entry=hex(entry),code=hex(code),flag=flag,width=b))
    # Execute renderer stubs to their original continuation, inspect advance and UV cropping.
    renderers=[]
    for site in SITES[:4]:
        renderer_cells=[(24,24),(12,24)] if metadata.get('latin_uniform_aspect') else [(24,24)]
        for g,w,h in [(g,w,h) for g in metadata['glyphs'] for w,h in renderer_cells]:
            u.context_restore(initial)
            u.mem_write(0x900000,struct.pack('<2f',w,h)+bytes(0x30)+struct.pack('<I',0))
            u.reg_write(getattr(reg,'UC_MIPS_REG_'+site['ctx'][1:].upper()),0x900000)
            raw=int(g['sjis'],16).to_bytes(2,'big')
            if isinstance(site['code'],int):u.mem_write(0xa00000+site['code'],raw)
            else:
                u.mem_write(0x910000,raw)
                u.reg_write(getattr(reg,'UC_MIPS_REG_'+site['code'][1:].upper()),0x910000)
            u.emu_start(site['hook'],site['resume'],count=1000)
            assert u.reg_read(reg.UC_MIPS_REG_PC)==site['resume']
            out=getattr(reg,'UC_MIPS_REG_'+site['out'][1:].upper())
            actual=u.reg_read(out)
            if site['kind']=='float':actual=struct.unpack('<f',struct.pack('<I',actual&0xffffffff))[0]
            assert actual==g['width'],(site['name'],g,actual)
            assert u.reg_read(getattr(reg,'UC_MIPS_REG_'+site['crop'][1:].upper()))==g['width']*4
            assert u.reg_read(getattr(reg,'UC_MIPS_REG_'+site['height'][1:].upper()))==96
            if metadata.get('latin_uniform_aspect'):
                assert struct.unpack('<f',u.mem_read(int(metadata['state_va'],16)+4,4))[0]==24
            renderers.append(dict(renderer=site['name'],code=g['sjis'],advance=actual,native_cell=[w,h]))
    pointers=[]
    for g in metadata['glyphs']:
        u.context_restore(initial);u.mem_write(0x910000,int(g['sjis'],16).to_bytes(2,'big'))
        u.reg_write(reg.UC_MIPS_REG_A0,0x900000);u.reg_write(reg.UC_MIPS_REG_A1,0x910000)
        u.emu_start(0x131d78,0x920000,count=1000)
        pointer=u.reg_read(reg.UC_MIPS_REG_V0)
        assert pointer==int(metadata['atlas_va'],16)+(g['index']-1)*GLYPH_BYTES
        u.reg_write(reg.UC_MIPS_REG_A1,pointer);u.reg_write(reg.UC_MIPS_REG_A2,24)
        u.emu_start(0x12f718,0x12f720,count=1000)
        assert u.reg_read(reg.UC_MIPS_REG_A2)==96
        pointers.append(dict(code=g['sjis'],pointer=hex(pointer)))
    geometry=[]
    if metadata.get('latin_uniform_aspect'):
        # Exercise the actual sprite hook with the tall dialogue cell. The
        # upload remains 96px; only Latin's on-screen rectangle becomes square.
        def write_float(n,value):
            u.reg_write(getattr(reg,'UC_MIPS_REG_F'+str(n)),struct.unpack('<I',struct.pack('<f',value))[0])
        def read_float(n):
            return struct.unpack('<f',struct.pack('<I',u.reg_read(getattr(reg,'UC_MIPS_REG_F'+str(n)))&0xffffffff))[0]
        for w,h in ((20,30),(24,24),(16,24),(32,24),(12,24),(6,12)):
            for latin in (False,True):
                u.context_restore(initial)
                size=h if w*2==h else min(w,h)
                u.mem_write(int(metadata['state_va'],16),struct.pack('<If',int(latin),size))
                for n,value in ((12,10),(13,50),(14,10+w),(15,50+h),
                                (16,12),(17,52),(18,12+w),(19,52+h)):
                    write_float(n,value)
                u.reg_write(reg.UC_MIPS_REG_A1,24)
                u.emu_start(0x12f8b8,0x12f8c0,count=1000)
                assert u.reg_read(reg.UC_MIPS_REG_PC)==0x12f8c0
                expected=size if latin else h
                assert read_float(15)-read_float(13)==expected
                assert read_float(19)-read_float(17)==expected
                assert read_float(14)==10+w and read_float(18)==12+w
                assert u.reg_read(reg.UC_MIPS_REG_A1)==(96 if latin else 24)
                geometry.append(dict(native_cell=[w,h],latin=latin,height=expected))
    return dict(pass_=True,baseline_cases=baseline_cases,atlas_uv_cases=len(metadata['glyphs']),width_cases=len(widths),japanese_fallback_cases=len(fallbacks),
                renderer_cases=len(renderers),glyph_upload_cases=len(pointers),
                sprite_geometry_cases=len(geometry),sprite_geometry=geometry,
                original_sha256=hashlib.sha256(original).hexdigest(),
                patched_sha256=hashlib.sha256(patched).hexdigest(),
                widths=widths,fallbacks=fallbacks,renderers=renderers,pointers=pointers,
                runtime_scope='MIPS execution of hooks; PCSX2 GIF/rendering checked separately')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('original','patched','metadata','output'):p.add_argument(n)
    a=p.parse_args();result=verify(Path(a.original).read_bytes(),Path(a.patched).read_bytes(),
                                 json.loads(Path(a.metadata).read_text()))
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)},indent=2))
