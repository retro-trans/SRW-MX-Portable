"""Local, native PS2 Prologue candidate using the reviewed PSP scripts.

Keep existing campaign IDs, graphics and translations. No release publication.
All source scripts stay under ignored work/source and translation working paths.
"""
import argparse
import copy
import json
import shutil
import struct
from pathlib import Path

import pycdlib
import build_patch
import export_rows
import play_order
import insert_text as it
from build_ps2_font import digest_file, digest_iso_file, patch_udf, write_udf_record
from build_ps2_dialogue import directory_position, copy_bytes
from ps2_database_port import strings
from ps2_translation_native import extend
from static2_extract import sections, strtable
from port_ps2_translations import ROOT, sha

VERSION = '0.1.8'
BIAS = 0xff000
SCENES = ('i00r0a', 'i00r0b', 'i00r1b', 'i00s0a', 'i00s0b', 'i00s1b', 's00r00', 's00s00')


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')


def raw_strings(raw, replacements):
    count, table = struct.unpack_from('<2I', raw, 8)
    pointers = struct.unpack_from(f'<{count}I', raw, table)
    first = min(pointers)
    header = bytearray(raw[:first]); blob = bytearray(); new = []
    for pointer in pointers:
        old = raw[pointer:raw.index(b'\0', pointer)]
        new.append(first + len(blob)); blob += replacements.get(old, old) + b'\0'
    struct.pack_into(f'<{count}I', header, table, *new)
    result = header + blob
    return bytes(result) + bytes(-len(result) % 2048)


def stage_records(data):
    offsets = list(struct.unpack_from('<5I', data)) + [len(data)]
    parts = [bytearray(data[a:b]) for a, b in zip(offsets, offsets[1:])]
    assert len(parts[1]) == 14*88 and len(parts[2]) == 66*136 and len(parts[3]) == 66*128
    source=(ROOT/'work/source/ps2/STAGE.BIN').read_bytes()
    for chapter in range(14):
        base=chapter*88
        parts[1][base+56:base+88]=source[416+base+56:416+base+88]
    for chapter, location, scenario, template in ((0,66,66,0),(1,67,67,2)):
        base = chapter*88
        assert struct.unpack_from('<3I', parts[1], base+56) == (2, template, template+1)
        struct.pack_into('<4I', parts[1], base+56, 3, location, template, template+1)
        loc = bytearray(parts[2][template*136:(template+1)*136])
        loc[4:68] = it.encode('Testing Facility').ljust(64,b'\0')
        struct.pack_into('<I', loc, 0x68, scenario)
        parts[2] += loc
        record = bytearray(parts[3][template*128:(template+1)*128])
        struct.pack_into('<4I', record, 0, chapter, chapter, 4, 5)
        record[16:72] = it.encode('Prologue').ljust(56,b'\0')
        record[72:128] = it.encode('Prologue').ljust(56,b'\0')
        parts[3] += record
    n = struct.unpack_from('<I', parts[4])[0]; assert n == 66
    old = bytes(parts[4]); pointers = struct.unpack_from('<66I',old,4)
    text = [old[p:old.index(b'\0',p)+1] for p in pointers]
    text += [it.encode('Hugo and Aqua test their new machine at the facility.')]*2
    new = bytearray(); offsets = []
    for value in text:
        offsets.append(4+68*4+len(new));new += value
    parts[4] = struct.pack('<I',68)+struct.pack('<68I',*offsets)+new
    offsets=[];out=bytearray(20)
    for part in parts:
        offsets.append(len(out));out += part
    struct.pack_into('<5I',out,0,*offsets)
    return bytes(out)


def researcher(data):
    s=sections(data,0);psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes();p=sections(psp)
    names=strtable(data,s['Strg'][0],s['Strg'][2]);index=len(names)
    new={}
    raw=[data[s['Strg'][0]+off:data.index(b'\0',s['Strg'][0]+off)+1]
         for off in struct.unpack_from(f'<{len(names)}I',data,s['Strg'][0]+12)]
    new['Strg']=strings('Strg',raw+[it.encode('Researcher')])
    pilot=bytearray(data[s['Pilt'][0]:s['Pilt'][0]+s['Pilt'][1]])
    off=12+433*184;assert pilot[off:off+184]==bytes(184)
    pilot[off:off+184]=psp[p['Pilt'][0]+off:p['Pilt'][0]+off+184]
    # Names/reading refer to PS2 Strg. The battle face is absent; the story
    # bust-up (Pilt bytes 4/5 -> face ID 2110) is a separate native asset.
    for at in (0,2,16):struct.pack_into('<H',pilot,off+at,index)
    assert struct.unpack_from('<H',pilot,off+14)[0]==0xffff
    new['Pilt']=bytes(pilot)
    out=bytearray();new_offsets={}
    for tag,(pos,size,count) in s.items():
        new_offsets[tag]=len(out)
        out += new.get(tag,data[pos:pos+size]);out += bytes(-len(out)%4)
    directory=struct.unpack_from('<19I',data,s['Fixh'][0]+8)
    tags={pos:tag for tag,(pos,size,count) in s.items()}
    struct.pack_into('<19I',out,new_offsets['Fixh']+8,*(new_offsets[tags[pos]] for pos in directory))
    end=max(pos+((size+3)&~3) for pos,size,count in s.values())
    out += data[end:]
    return bytes(out)


def prepare(iso, work):
    def read(path):
        with iso.open_file_from_iso(iso_path=path) as stream:return stream.read()
    elf=bytearray(read('/SLPS_253.45;1'))
    meta=json.loads((ROOT/'work/build/ps2/font_0.1.5/patch.json').read_text(encoding='utf8'))
    assert sha(elf)==meta['target_sha256']
    original=bytes(elf);m=read('/DATA/MAP.BIN;1');sec=list(struct.unpack_from('<18I',elf,0x37e438))
    old_units=list(struct.unpack_from('<1001I',elf,0x380f98));assert old_units[-1]<=sec[10]-sec[9]
    psp=(ROOT/'work/build/MAP_ADD.orig').read_bytes();boot=(ROOT/'work/source/ps2/prologue/PSP_BOOT.BIN').read_bytes()
    psec=struct.unpack_from('<18I',boot,0x2791f0)
    inventory={row['name']:row for row in json.loads((ROOT/'work/source/stage_map.json').read_text(encoding='utf8'))}
    translations=build_patch.load_translations([str(ROOT/'work/translation/en/script/prologue_merged.json'),
                                               str(ROOT/'work/translation/en/script/stage01_campaign_full_merged.json')])
    # The exact 40x40 test battlefield and terrain table already exist on PS2.
    maps=struct.unpack_from('<1001I',elf,0x37f060)
    a=(sec[7]+maps[390])*2048;b=(sec[7]+maps[391])*2048
    c=(psec[7]+maps[390])*2048;d=(psec[7]+maps[391])*2048
    assert m[a:b]==psp[c:d] and m[a:a+4]==b'MPTD'
    with (ROOT/'work/source/ps2/map_prefix.bin').open('rb') as stream:
        stream.seek(sec[8]*2048);terrain=stream.read((sec[9]-sec[8])*2048)
    assert terrain==psp[psec[8]*2048:psec[9]*2048]
    units={}
    for name in ('s00r00','s00s00'):
        needle=name.encode()+b'\0';pos=psp.index(needle,psec[9]*2048,psec[10]*2048)-24
        raw=psp[pos:pos+2048];assert raw[:4]==b'UNTD'
        assert struct.unpack_from('<2I',raw,4)==(910,390)
        units[4 if name=='s00r00' else 24]=raw
    deployments=bytearray();new_units=[]
    for index in range(1000):
        new_units.append(len(deployments)//2048)
        raw=m[(sec[9]+old_units[index])*2048:(sec[9]+old_units[index+1])*2048]
        if index in units:assert not raw;raw=units[index]
        deployments += raw
    new_units.append(len(deployments)//2048)
    deployments += m[(sec[9]+old_units[-1])*2048:sec[10]*2048]
    struct.pack_into('<1001I',elf,0x380f98,*new_units)
    names=[];blocks=[];rel=list(struct.unpack_from('<193I',elf,0x381f40));evidence=[]
    for i in range(192):
        ptr=struct.unpack_from('<I',elf,0x37b5f8+i*4)[0]-BIAS
        name=bytes(elf[ptr:elf.index(0,ptr)]).decode('ascii');names.append(name)
        raw=m[(sec[10]+rel[i])*2048:(sec[10]+rel[i+1])*2048]
        if name in ('s00r10','s00s10'):
            label='i00r1b' if name=='s00r10' else 'i00s1b'
            raw=raw_strings(raw,{b'i001b':label.encode()})
        blocks.append(raw)
    ptable=struct.unpack_from('<204I',boot,0x27ca20)
    for name in SCENES:
        i=inventory[name]['block'];raw=psp[(psec[10]+ptable[i])*2048:(psec[10]+ptable[i+1])*2048]
        if name.endswith('0b'):
            # PSP has an empty pre-battle event here. Its first dialogue is
            # Hugo's radio call on the map, not the original PS2 lab scene.
            block=raw;replaced=0
            assert play_order.load(raw,0)[1]==[]
        else:
            block,replaced=build_patch.rebuild_block(raw,translations.get(name,{}))
            commands,source=play_order.load(raw,0);new_commands,text=play_order.load(block,0)
            assert commands==new_commands
            missing=[j for j,t in enumerate(source) if export_rows.classify(t) and t not in translations.get(name,{})]
            assert not missing,(name,missing)
        commands,text=play_order.load(block,0)
        assert all(0<=v[0]<179 for v in commands)
        assert len(block)<=0x25000
        names.append(name);blocks.append(block)
        evidence.append(dict(scene=name,commands=len(commands),bytes=len(block),translated_strings=replaced,
                             target_sha256=sha(block),opening_redirect=False))
    result=bytearray(m[:sec[9]*2048]);result += deployments
    new_script_base=len(result)//2048;new_rel=[]
    for block in blocks:
        new_rel.append(len(result)//2048-new_script_base);result += block
    new_rel.append(len(result)//2048-new_script_base)
    result += m[sec[11]*2048:]
    unit_growth=len(deployments)//2048-(sec[10]-sec[9])
    script_growth=new_rel[-1]-(sec[11]-sec[10])
    sec[10]+=unit_growth
    for i in range(11,18):sec[i]+=unit_growth+script_growth
    assert sec[-1]*2048==len(result)
    struct.pack_into('<18I',elf,0x37e438,*sec)
    # Original fixed table remains a checked prefix, while native loaders use the extended copy.
    struct.pack_into('<193I',elf,0x381f40,*new_rel[:193])
    pool=bytearray(struct.pack('<201I',*new_rel));names_offset=len(pool);pool += bytes(201*4)
    start=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    pointers=[]
    for name in names:pointers.append(start+len(pool));pool += name.encode()+b'\0'
    struct.pack_into('<201I',pool,names_offset,*pointers,0)
    elf,table=extend(elf,meta,pool);assert table==start;name_table=table+names_offset
    hooks=[]
    def word(site,value,label):
        off=site-BIAS;old=bytes(elf[off:off+4]);new=struct.pack('<I',value)
        elf[off:off+4]=new;hooks.append(dict(name=label,va=hex(site),old=old.hex(),new=new.hex()))
    def address(hi_site,lo_site,target,label):
        hi=struct.unpack_from('<I',elf,hi_site-BIAS)[0];lo=struct.unpack_from('<I',elf,lo_site-BIAS)[0]
        word(hi_site,(hi&0xffff0000)|((target+0x8000)>>16),label)
        word(lo_site,(lo&0xffff0000)|(target&65535),label)
    address(0x339754,0x33975c,name_table,'prologue_script_names')
    address(0x339588,0x339594,table,'prologue_script_size_table')
    address(0x3396f4,0x3396fc,table,'prologue_script_read_table')
    address(0x306bdc,0x306bec,name_table,'prologue_debug_scene_names')
    meta['hooks']+=hooks;meta['target_sha256']=sha(elf)
    from ps2_prologue_entry import patch as patch_entry
    elf, entry = patch_entry(elf, meta)
    hooks += entry['hooks']
    from ps2_prologue_numbering import patch as patch_numbering
    elf, numbering = patch_numbering(elf, meta)
    hooks += numbering['hooks']
    # The same 40x40 battlefield also has a native 640x640 selection picture.
    # Existing scenario s03s40 (chapter 4, group 6) uses battlefield 390.
    thumbs=bytearray(read('/DATA/D2MAPH.BIN;1'))
    picture=bytes(thumbs[(4*32+6)*16:(4*32+7)*16])
    assert struct.unpack('<4I',picture)==(17860608,640,640,0)
    for chapter in (0,1):
        first=chapter*32*16;thumbs[first+4*16:first+5*16]=picture
    resources={'/SLPS_253.45;1':bytes(elf),'/DATA/MAP.BIN;1':bytes(result),
               '/DATA/STAGE.BIN;1':stage_records(read('/DATA/STAGE.BIN;1')),
               '/DATA/FIX00.DAT;1':researcher(read('/DATA/FIX00.DAT;1')),
               '/DATA/D2MAPH.BIN;1':bytes(thumbs)}
    for path,data in resources.items():(work/path.rsplit('/',1)[-1].split(';')[0]).write_bytes(data)
    save(work/'patch.json',meta)
    report=dict(version=VERSION,source_build='0.1.5',new_scene_blocks=evidence,scene_count=200,
                script_sector_table_va=hex(table),script_name_table_va=hex(name_table),
                unit_groups=[dict(chapter=0,group=4,scene='s00r00'),dict(chapter=1,group=4,scene='s00s00')],
                native_map_id=390,exact_native_battlefield=True,terrain_table_identical=True,
                scenario_ids=[66,67],location_ids=[66,67],original_scenario_ids_preserved=True,
                chapter_progression_fields_repaired=True,
                original_stage1_intro_replaced=True,opening_runs_before_prologue=True,
                researcher_pilot_id=433,researcher_has_no_portrait=True,
                map_selection_thumbnails='Matching native battlefield 390 image, 640x640',
                visual_validation='pending',gameplay_clear_and_save_validation='pending',
                existing_save_migration='not implemented; new games only',
                stage30_port='not included',github_release=False,hooks=hooks,new_game_entry=entry,
                chapter_numbering=numbering)
    save(work/'prologue.json',report)
    return resources,meta,report


def build(prepare_only=False,resume_packaging=False):
    source=ROOT/'work/output/SRWMX_PS2_EN_0.1.5.iso';out=ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso'
    assert not out.exists() or resume_packaging,'Existing build preserved'
    if resume_packaging:
        assert out.exists() and not (ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json').exists(),'Only incomplete packaging may resume'
    previous=json.loads((ROOT/'work/output/ps2_font_0.1.5_verification.json').read_text(encoding='utf8'))
    if not prepare_only:assert digest_file(source)==previous['target_sha256']
    work=ROOT/'work/build/ps2'/f'prologue_{VERSION}';work.mkdir(parents=True,exist_ok=True)
    iso=pycdlib.PyCdlib();iso.open(str(source));resources,meta,report=prepare(iso,work)
    from verify_ps2_prologue_entry import verify as verify_entry
    entry_checks=verify_entry(resources['/SLPS_253.45;1'],resources['/DATA/STAGE.BIN;1'])
    save(ROOT/'work/output'/f'ps2_prologue_{VERSION}_entry_execution.json',entry_checks)
    from verify_ps2_prologue_numbering import verify as verify_numbering
    numbering_checks=verify_numbering(resources['/SLPS_253.45;1'])
    save(ROOT/'work/output'/f'ps2_prologue_{VERSION}_numbering_execution.json',numbering_checks)
    if prepare_only:
        iso.close();print(json.dumps(dict(version=VERSION,prepared=True,heap_start=meta['heap_start']),indent=2));return
    positions={p:directory_position(iso,source,p) for p in resources}
    udf_names={name.lower():name for _,_,names in iso.walk(udf_path='/data') for name in names}
    udf_paths={p:('/SLPS_253.45' if p=='/SLPS_253.45;1' else '/data/'+udf_names[p.rsplit('/',1)[-1].split(';')[0].lower()]) for p in resources}
    before={p:(iso.get_record(iso_path=p).extent_location(),iso.get_record(iso_path=p).data_length)
            for p in [x['path'] for x in previous['files']] if p not in resources}
    if not resume_packaging:shutil.copyfile(source,out)
    locations={}
    with out.open('r+b') as stream:
        expected_bytes=source.stat().st_size+sum((len(v)+2047)//2048*2048 for v in resources.values())+2048
        if resume_packaging:
            assert out.stat().st_size==expected_bytes,'Incomplete payload copy cannot resume'
            stream.seek(source.stat().st_size)
            for path,data in resources.items():
                prior=stream.read(len(data))
                if path=='/DATA/D2MAPH.BIN;1':
                    prior=bytearray(prior)
                    for chapter in (0,1):
                        off=(chapter*32+4)*16;prior[off:off+16]=data[off:off+16]
                assert sha(prior)==sha(data),'Resume payload differs'
                stream.seek(-len(data)%2048,1)
        stream.seek(source.stat().st_size)
        for path,data in resources.items():
            locations[path]=stream.tell()//2048;stream.write(data);stream.write(bytes(-len(data)%2048))
        last=stream.tell()//2048;stream.write(bytes(2048));total=last+1
        assert total*2048<=4700372992
        for path,data in resources.items():
            stream.seek(positions[path]+2);stream.write(struct.pack('<I',locations[path])+struct.pack('>I',locations[path]))
            stream.seek(positions[path]+10);stream.write(struct.pack('<I',len(data))+struct.pack('>I',len(data)))
            if path!='/SLPS_253.45;1':
                record=iso.get_record(udf_path=udf_paths[path])
                record.set_data_length(len(data));record.set_data_location(locations[path],locations[path]-iso.udf_main_descs.partitions[0].part_start_location)
                record.log_block_recorded=(len(data)+2047)//2048;write_udf_record(stream,record)
        descriptor=16
        while True:
            stream.seek(descriptor*2048);head=stream.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                stream.seek(descriptor*2048+80);stream.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,stream,locations['/SLPS_253.45;1'],len(resources['/SLPS_253.45;1']),last)
    iso.close();checked=pycdlib.PyCdlib();checked.open(str(out))
    for path,data in resources.items():
        assert digest_iso_file(checked,path)==sha(data)
        udf=udf_paths[path]
        with checked.open_file_from_iso(udf_path=udf) as stream:assert sha(stream.read())==sha(data)
    for path,pair in before.items():
        rec=checked.get_record(iso_path=path);assert (rec.extent_location(),rec.data_length)==pair
    checked.close()
    previous.update(version=VERSION,output=str(out.relative_to(ROOT)),bytes=out.stat().st_size,
                    source_build_version='0.1.5',source_build_sha256=previous['target_sha256'],
                    scope='English PS2 campaign, native 4x VWF, selectable balance and both PSP Prologue routes; new games only',
                    base_campaign_translated_scenes=previous['translated_scenes'],
                    base_campaign_translated_strings=previous['translated_strings'],
                    prologue_scene_string_slots=sum(x['translated_strings'] for x in report['new_scene_blocks']),
                    translated_scenes=previous['translated_scenes']+len(report['new_scene_blocks']),
                    translated_strings=previous['translated_strings']+sum(x['translated_strings'] for x in report['new_scene_blocks']),
                    total_scenes=report['scene_count'],scenario_records=68,
                    target_sha256=digest_file(out),font=meta,prologue=report,github_release=False,
                    prologue_new_game_entry_checks=entry_checks,new_game_prologue_entry_fixed=True)
    for path,data in resources.items():
        row=next((x for x in previous['files'] if x['path']==path),None)
        fields=dict(path=path,target_sha256=sha(data),target_sector=locations[path],bytes=len(data))
        if row:row.update(fields)
        else:previous['files'].append(fields)
    evidence=ROOT/'work/build/ps2'/f'font_{VERSION}';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'SLPS_253.45').write_bytes(resources['/SLPS_253.45;1']);save(evidence/'patch.json',meta)
    save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',previous)
    save(ROOT/'work/translation/en/ps2/prologue_port.en.json',report)
    print(json.dumps(dict(version=VERSION,output=str(out),bytes=out.stat().st_size,
                          sha256=previous['target_sha256'],scenes=200,heap_start=meta['heap_start']),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--resume-packaging',action='store_true');args=parser.parse_args()
    build(args.prepare_only,args.resume_packaging)
