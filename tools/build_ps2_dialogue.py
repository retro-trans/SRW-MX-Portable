"""Port the PS2 opening and both stage-1 routes from reviewed PSP English.

Keep original PS2 commands, scene IDs, gameplay data and every unrelated file.
The rebuilt MAP archive and native-font ELF are appended, with both ISO9660
and UDF entries updated. No release or save conversion is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import pycdlib
import build_patch
import export_rows
import play_order
from build_ps2_font import (SOURCE_SHA256, ELF_SHA256, digest_file,
                            digest_iso_file, files, patch_udf, write_udf_record)
from ps2_font4x import ROOT, patch_elf
from verify_ps2_font import verify

MAP_PATH='/DATA/MAP.BIN;1'
ELF_PATH='/SLPS_253.45;1'
UDF_PATHS={ELF_PATH:'/SLPS_253.45',MAP_PATH:'/data/map.bin'}
TABLE=0x381f40
SECTIONS=0x37e438
SCRIPT_SECTION=10
SCRIPT_BASE=0x622a000
COUNT=192
NAMES=0x37b5f8


def copy_bytes(source,target,count):
    while count:
        chunk=source.read(min(count,4*1024*1024))
        if not chunk:raise EOFError('Short source read')
        target.write(chunk);count-=len(chunk)


def directory_position(iso, source, path):
    record=iso.get_record(iso_path=path)
    sector=record.parent.extent_location()
    with source.open('rb') as f:
        f.seek(sector*2048);raw=f.read(record.parent.data_length)
    position=0;found=[]
    while position<len(raw):
        length=raw[position]
        if not length:position=(position+2048)&~2047;continue
        identifier=raw[position+33:position+33+raw[position+32]]
        if identifier==path.rsplit('/',1)[1].encode('ascii'):found.append(sector*2048+position)
        position+=length
    assert len(found)==1,path
    return found[0]


def prepare(iso, original, version):
    sources=[ROOT/'work/translation/en/script'/name for name in
             ('prologue_merged.json','stage01_campaign_full_merged.json')]
    translations=build_patch.load_translations([str(p) for p in sources])
    differences=ROOT/'work/translation/en/ps2/script/stage1_ps2_differences.en.json'
    reviewed=json.loads(differences.read_text(encoding='utf8'))['rows']
    overrides={use:row for row in reviewed for use in row['uses']}
    expected={'i001b','i00r1a','i00s1a','s00r10','s00s10'}
    relative=struct.unpack_from('<193I',original,TABLE)
    assert relative[0]==0 and all(a<b for a,b in zip(relative,relative[1:]))
    section=list(struct.unpack_from('<18I',original,SECTIONS))
    assert section[SCRIPT_SECTION]*2048==SCRIPT_BASE
    record=iso.get_record(iso_path=MAP_PATH)
    assert section[-1]*2048==record.data_length
    work=ROOT/'work/build/ps2'/('dialogue_'+version);work.mkdir(parents=True,exist_ok=True)
    map_output=work/'MAP.BIN';new_relative=[];blocks=[];english=[];changed=set()
    largest_original=max(b-a for a,b in zip(relative,relative[1:]))*2048
    with iso.open_file_from_iso(iso_path=MAP_PATH) as source,map_output.open('wb') as output:
        copy_bytes(source,output,SCRIPT_BASE)
        for index in range(COUNT):
            pointer=struct.unpack_from('<I',original,NAMES+index*4)[0]-0xff000
            name=original[pointer:original.index(b'\0',pointer)].decode('ascii')
            raw=source.read((relative[index+1]-relative[index])*2048)
            assert raw[:4]==b'SRWL'
            commands,strings=play_order.load(raw,0)
            mapping=dict(translations.get(name,{})) if name in expected else {}
            for slot,jp in enumerate(strings):
                override=overrides.get(name+':'+str(slot))
                if override:
                    assert hashlib.sha256(jp.encode('cp932')).hexdigest()==override['source_sha256']
                    opening,closing=('（','）') if override['kind']=='thought' else ('「','」')
                    lines,ok=build_patch.textfit.wrap(override['speaker_en']+opening,override['en'],closing)
                    assert ok,(name,slot,'PS2 variant does not fit')
                    mapping[jp]='@'.join(lines)
            if mapping:
                block,replaced=build_patch.rebuild_block(raw,mapping);changed.add(name)
            else:block,replaced=raw,0
            new_commands,new_strings=play_order.load(block,0)
            assert commands==new_commands and len(strings)==len(new_strings)
            assert block[32:32+48*len(commands)]==raw[32:32+48*len(commands)]
            assert len(block)<=largest_original,(name,'exceeds largest original PS2 allocation')
            untouched=0
            for slot,(jp,actual) in enumerate(zip(strings,new_strings)):
                if jp in mapping:
                    wanted=build_patch.textfit.encode(mapping[jp]).decode('cp932')
                    assert actual==wanted,(name,slot)
                    english.append(dict(scene=name,string_index=slot,
                                        source_sha256=hashlib.sha256(jp.encode('cp932')).hexdigest(),
                                        english=mapping[jp]))
                else:
                    assert jp==actual,(name,slot,'untranslated string changed');untouched+=1
                    if mapping:assert export_rows.classify(jp) is None,(name,slot,'readable text missing')
            new_relative.append((output.tell()-SCRIPT_BASE)//2048)
            output.write(block)
            blocks.append(dict(scene=name,index=index,original_bytes=len(raw),new_bytes=len(block),
                               translated_strings=replaced,unchanged_strings=untouched,
                               commands=len(commands),commands_sha256=hashlib.sha256(raw[32:32+48*len(commands)]).hexdigest(),
                               original_sha256=hashlib.sha256(raw).hexdigest(),new_sha256=hashlib.sha256(block).hexdigest()))
        new_relative.append((output.tell()-SCRIPT_BASE)//2048)
        old_end=SCRIPT_BASE+relative[-1]*2048
        assert source.tell()==old_end
        copy_bytes(source,output,record.data_length-old_end)
    assert changed==expected
    delta=new_relative[-1]-relative[-1]
    for index in range(SCRIPT_SECTION+1,18):section[index]+=delta
    assert section[-1]*2048==map_output.stat().st_size
    evidence=ROOT/'work/build/ps2'/('font_'+version)
    elf,font=patch_elf(original,evidence,baseline_fix=version!='0.1.1');elf=bytearray(elf)
    struct.pack_into('<193I',elf,TABLE,*new_relative)
    struct.pack_into('<18I',elf,SECTIONS,*section)
    elf=bytes(elf);font['target_sha256']=hashlib.sha256(elf).hexdigest()
    font['ps2_script_tables_updated']=True
    (evidence/'SLPS_253.45').write_bytes(elf)
    (evidence/'patch.json').write_text(json.dumps(font,indent=2)+'\n',encoding='utf8')
    mips=verify(original,elf,font)
    inputs={str(p.relative_to(ROOT)).replace('\\','/'):digest_file(p) for p in sources}
    inputs[str(differences.relative_to(ROOT)).replace('\\','/')]=digest_file(differences)
    destination=ROOT/'work/translation/en/ps2/script';destination.mkdir(parents=True,exist_ok=True)
    manifest=dict(version=version,scope='PS2 opening and stage 1, both routes',
                  source_files=inputs,translated_scenes=sorted(changed),texts=english)
    (destination/('opening_stage1_'+version+'.en.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return elf,font,map_output,blocks,new_relative,section,mips,inputs


def build(source,version,verify_existing=False):
    assert version in ('0.1.1','0.1.2'),'Supported local PS2 opening/stage-1 builds: 0.1.1, 0.1.2'
    source=Path(source).resolve();output=ROOT/'work/output'/('SRWMX_PS2_EN_'+version+'.iso')
    if output.exists() and not verify_existing:raise FileExistsError(output)
    if verify_existing and not output.exists():raise FileNotFoundError(output)
    assert digest_file(source)==SOURCE_SHA256,'Unexpected original disc'
    iso=pycdlib.PyCdlib();iso.open(str(source))
    with iso.open_file_from_iso(iso_path=ELF_PATH) as f:original=f.read()
    assert hashlib.sha256(original).hexdigest()==ELF_SHA256
    elf,font,map_output,blocks,relative,section,mips,inputs=prepare(iso,original,version)
    replacements={ELF_PATH:(len(elf),font['target_sha256']),
                  MAP_PATH:(map_output.stat().st_size,digest_file(map_output))}
    positions={p:directory_position(iso,source,p) for p in replacements}
    if not verify_existing:
        output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,output)
        locations={}
        with output.open('r+b') as f:
            f.seek(0,2);locations[ELF_PATH]=f.tell()//2048
            f.write(elf);f.write(bytes(-len(elf)%2048))
            locations[MAP_PATH]=f.tell()//2048
            with map_output.open('rb') as local:copy_bytes(local,f,map_output.stat().st_size)
            last=f.tell()//2048;f.write(bytes(2048));total=last+1
            for path,(length,sha) in replacements.items():
                f.seek(positions[path]+2);f.write(struct.pack('<I',locations[path])+struct.pack('>I',locations[path]))
                f.seek(positions[path]+10);f.write(struct.pack('<I',length)+struct.pack('>I',length))
            descriptor=16
            while True:
                f.seek(descriptor*2048);head=f.read(7)
                assert head[1:6]==b'CD001'
                if head[0]==255:break
                if head[0] in (1,2):
                    f.seek(descriptor*2048+80);f.write(struct.pack('<I',total)+struct.pack('>I',total))
                descriptor+=1
            patch_udf(iso,f,locations[ELF_PATH],len(elf),last)
            start=iso.udf_main_descs.partitions[0].part_start_location
            entry=iso.get_record(udf_path=UDF_PATHS[MAP_PATH])
            assert len(entry.alloc_descs)==1
            entry.set_data_length(replacements[MAP_PATH][0])
            entry.set_data_location(locations[MAP_PATH],locations[MAP_PATH]-start)
            entry.log_block_recorded=replacements[MAP_PATH][0]//2048
            write_udf_record(f,entry)
    rebuilt=pycdlib.PyCdlib();rebuilt.open(str(output));checks=[]
    for path in sorted(files(iso)):
        a=iso.get_record(iso_path=path);b=rebuilt.get_record(iso_path=path)
        original_hash=digest_iso_file(iso,path);target_hash=digest_iso_file(rebuilt,path)
        changed=path in replacements
        assert target_hash==(replacements[path][1] if changed else original_hash),path
        if not changed:assert a.extent_location()==b.extent_location(),path
        checks.append(dict(path=path,changed=changed,original_sha256=original_hash,target_sha256=target_hash,
                           original_sector=a.extent_location(),target_sector=b.extent_location(),bytes=b.data_length))
    for path,(length,sha) in replacements.items():
        h=hashlib.sha256()
        with rebuilt.open_file_from_iso(udf_path=UDF_PATHS[path]) as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==sha,path
    with rebuilt.open_file_from_iso(iso_path=MAP_PATH) as f:
        for block in blocks:
            f.seek(SCRIPT_BASE+relative[block['index']]*2048)
            assert hashlib.sha256(f.read(block['new_bytes'])).hexdigest()==block['new_sha256']
    assert len(checks)==37 and len(rebuilt.udf_anchors)>=2
    rebuilt.close();iso.close();assert digest_file(source)==SOURCE_SHA256
    assert all(digest_file(ROOT/p)==sha for p,sha in inputs.items())
    report=dict(version=version,platform='PS2',scope='Opening and stage 1, both routes; native 4x VWF',
                source_sha256=SOURCE_SHA256,target_sha256=digest_file(output),output=str(output),bytes=output.stat().st_size,
                source_unchanged=True,changed_files=2,unchanged_files=35,unrelated_file_lbas_retained=True,
                iso9660_and_udf_executable_agree=True,iso9660_and_udf_map_agree=True,
                script_commands_unchanged=True,translated_scenes=5,translated_strings=sum(x['translated_strings'] for x in blocks),
                total_scenes=COUNT,remaining_scenes=COUNT-5,stage_coverage=[1],both_stage1_routes=True,
                font=font,blocks=blocks,files=checks,input_sha256=inputs,
                mips_checks={k:v for k,v in mips.items() if not isinstance(v,list)},
                pcsx2_visual_validation='pending',physical_ps2_validation='pending')
    (ROOT/'work/output'/('ps2_font_'+version+'_verification.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    (ROOT/'work/output'/('ps2_font_'+version+'_mips_verification.json')).write_text(json.dumps(mips,indent=2)+'\n',encoding='utf8')
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',output.with_name(output.stem+'_FONT_LICENSE.txt'))
    print(json.dumps({k:v for k,v in report.items() if k not in ('font','blocks','files','input_sha256','mips_checks')},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('version')
    p.add_argument('--verify-existing',action='store_true',help='Read-only verification of an existing ISO')
    a=p.parse_args();build(a.source,a.version,a.verify_existing)
