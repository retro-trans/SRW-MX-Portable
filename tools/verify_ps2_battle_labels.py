"""Verify exact label-only resources, native AI drawing and status crop bounds."""
import json,struct,unicodedata
from pathlib import Path
from unicorn import UC_HOOK_CODE,mips_const as reg
from port_ps2_translations import ROOT,sha,read_json
from port_ps2_prologue import save
from ps2_battle_label_preservation import baseline_bytes
from ps2_graphics_port import p2ig_textures,redraw_forecast_badge,fake_tx48
from fix_ps2_forecast_badges import picture
from static2_extract import sections,strtable
from verify_ps2_font import machine
import insert_text as it


def verify(base,version):
    previous=ROOT/'work/build/ps2/narration_0.4.13';report=read_json(base/'battle_labels.json')
    assert report['version']==version
    for name in ('FIX00.DAT','WND.BIN'):
        assert baseline_bytes(base,name)==(previous/name).read_bytes()
    for path in previous.iterdir():
        if path.suffix in ('.BIN','.DAT','.45') and path.name not in report['resources']:
            assert path.read_bytes()==(base/path.name).read_bytes(),path.name
    old=(previous/'FIX00.DAT').read_bytes();fix=(base/'FIX00.DAT').read_bytes()
    assert set(report['resources'])=={'FIX00.DAT','WND.BIN'}
    old_sections=sections(old,0);new_sections=sections(fix,0);assert old_sections==new_sections
    names=strtable(fix,new_sections['Strg'][0],new_sections['Strg'][2]);before=strtable(old,old_sections['Strg'][0],old_sections['Strg'][2])
    assert [i for i,(a,b) in enumerate(zip(before,names)) if a!=b]==[1133]
    assert unicodedata.normalize('NFKC',names[1133])=='AI'
    name_offset=new_sections['Strg'][0]+struct.unpack_from('<I',old,new_sections['Strg'][0]+12+1133*4)[0]
    name_length=old.index(0,name_offset)+1-name_offset
    assert [(r['offset'],len(bytes.fromhex(r['after']))) for r in report['resources']['FIX00.DAT']['ranges']]==[(name_offset,name_length)]
    for tag,(offset,size,count) in new_sections.items():
        if tag!='Strg':assert fix[offset:offset+size]==old[offset:offset+size],tag
    pointer_table=new_sections['Strg'][0]+12
    assert fix[pointer_table:pointer_table+4*len(names)]==old[pointer_table:pointer_table+4*len(names)]
    wnd=(base/'WND.BIN').read_bytes();original=(ROOT/'work/source/ps2/WND.BIN').read_bytes()
    current_rows=p2ig_textures(wnd);assert current_rows==p2ig_textures(original)
    rows={r['name']:r for r in current_rows};cases=[]
    expected={'IM_IC07':'ST','IM_IC08':'WP','IM_IC09':'MB','IM_IC10':'AR',
              'IM_IC11':'DS','IM_IC12':'HP','IM_IC13':'MV'}
    assert {r['asset']:r['english'] for r in report['labels']}==expected
    expected_ranges=sorted((rows[name]['offset']+rows[name]['pixel_offset'],1024) for name in expected)
    assert sorted((r['offset'],len(bytes.fromhex(r['after']))) for r in report['resources']['WND.BIN']['ranges'])==expected_ranges
    for record in report['labels']:
        name=record['asset'];row=rows[name];a=row['offset']+row['pixel_offset'];n=row['pixel_bytes']
        assert record['pixel_offset']==a and record['pixel_bytes']==n
        assert n==1024 and picture(wnd,row).getbbox()==(0,0,21,21)
        assert wnd[row['offset']:a]==original[row['offset']:a]
        if name=='IM_IC12':assert wnd[a:a+n]==original[a:a+n]
        else:
            x0,y0,x1,y1=record['inner_box'];assert [x0,y0,x1,y1]==[2,3,19,19]
            for y in range(32):
                for x in range(32):
                    if not (x0<=x<x1 and y0<=y<y1):assert wnd[a+y*32+x]==original[a+y*32+x]
            ix0,iy0,ix1,iy1=record['ink_box'];assert x0<ix0<ix1<x1 and y0<iy0<iy1<y1
        cases.append(dict(asset=name,english=expected[name],frame_and_padding_match_original=True,visible_size=[21,21]))
    badges=[]
    for name,text in (('IM_IC00S','AT'),('IM_IC01S','CT')):
        row=rows[name];a=row['offset']+row['pixel_offset'];z=a+row['pixel_bytes']
        assert wnd[a:z]==(previous/'WND.BIN').read_bytes()[a:z]
        pixels,layout=redraw_forecast_badge(fake_tx48(original,row),text)
        assert wnd[a:z]==pixels and picture(wnd,row).getbbox()==(0,0,24,24)
        badges.append(dict(asset=name,english=text,visible_size=[24,24],corrected_frame_and_padding_preserved=True))
    elf=(base/'SLPS_253.45').read_bytes();assert elf==(previous/'SLPS_253.45').read_bytes()
    meta=read_json(base/'patch.json');assert sha(elf)==meta['target_sha256']
    u=machine(elf);initial=u.context_save();captured=[]
    def draw(vm,pc,size,user):
        if pc!=0x130610:return
        text=bytes(vm.mem_read(vm.reg_read(reg.UC_MIPS_REG_A1),128)).split(b'\0')[0]
        captured.append((text,vm.reg_read(reg.UC_MIPS_REG_A2)))
        vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,draw);draw_cases=[]
    for site,x in ((0x1799cc,345),(0x17a43c,44)):
        for name,expected_name in (('AI','AI'),('Giganos Soldier','Giganos Sldr.'),('Hugo','Hugo')):
            u.context_restore(initial);captured.clear();u.mem_write(0x910000,it.encode(name))
            for r,v in ((reg.UC_MIPS_REG_A0,0x900000),(reg.UC_MIPS_REG_A1,0x910000),
                        (reg.UC_MIPS_REG_A2,x),(reg.UC_MIPS_REG_A3,164),(reg.UC_MIPS_REG_S2,0x900000),
                        (reg.UC_MIPS_REG_T0,0xffffffffffffffff)):u.reg_write(r,v)
            u.emu_start(site,site+8,count=1000)
            assert captured==[(it.encode(expected_name)[:-1],x)]
            assert u.reg_read(reg.UC_MIPS_REG_SP)==0xa00000
            draw_cases.append(dict(site=hex(site),english=expected_name,x=x))
    widths={g['character']:g['width'] for g in meta['glyphs']};assert sum(widths[c] for c in 'AI')<160
    result=dict(version=version,passed=True,source_build='0.4.13',ai_name_entry=1133,
                ai_native_width=sum(widths[c] for c in 'AI'),native_forecast_draw_cases=draw_cases,
                status_icons=cases,forecast_badges=badges,executable_byte_identical=True,
                all_numeric_database_records_identical=True,all_string_offsets_identical=True,
                only_declared_resource_ranges_changed=True,unchanged_resources=[p.name for p in previous.iterdir() if p.suffix in ('.BIN','.DAT','.45') and p.name not in report['resources']],
                visual_validation='native asset previews only',github_release=False)
    save(ROOT/'work/output'/f'ps2_battle_labels_{version}_verification.json',result)
    print(json.dumps(dict(version=version,passed=True,status_icons=len(cases),badge_checks=len(badges),ai_draws=len(draw_cases))))
    return result
