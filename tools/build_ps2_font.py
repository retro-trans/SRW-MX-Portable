"""Build a native PS2 font-only ISO while retaining every original data LBA.

Append the enlarged ELF and change its directory entry; rebuilding/reordering
the disc would break the game's directly addressed asset archives.
"""
import argparse
import hashlib
import copy
import json
from pathlib import Path
import re
import shutil
import struct
import pycdlib
from ps2_font4x import patch_elf, ROOT
from verify_ps2_font import verify

SOURCE_SHA256='bcc9a6c5e20ffe4afc02aae482819de7b18c8bb1437a6d7a0feff096801934ce'
ELF_SHA256='1a7d24a5482979dda218d8be7d8721c9438ef21ed598f8ff8abdbd71e02f7141'


def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def digest_iso_file(iso,path):
    h=hashlib.sha256()
    with iso.open_file_from_iso(iso_path=path) as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def files(iso):
    for folder,dirs,names in iso.walk(iso_path='/'):
        for name in names:yield folder.rstrip('/')+'/'+name


def write_udf_record(stream, record):
    """Retain this mastered disc's full-sector UDF CRC coverage."""
    raw=record.record()
    body=raw[16:]
    coverage=record.desc_tag.desc_crc_length
    assert 0<=coverage<=2032
    body=body.ljust(coverage,b'\0')
    assert len(body)<=2032
    stream.seek(record.extent_location()*2048)
    stream.write(record.desc_tag.record(body)+body)


def patch_udf(iso, stream, sector, elf_length, last_sector):
    assert len(iso.udf_main_descs.partitions)==1
    partition_start=iso.udf_main_descs.partitions[0].part_start_location
    udf_elf=iso.get_record(udf_path='/SLPS_253.45')
    assert len(udf_elf.alloc_descs)==1
    udf_elf.set_data_length(elf_length)
    udf_elf.set_data_location(sector,sector-partition_start)
    udf_elf.log_block_recorded=(elf_length+2047)//2048
    write_udf_record(stream,udf_elf)
    for sequence in (iso.udf_main_descs,iso.udf_reserve_descs):
        for partition in sequence.partitions:
            partition.part_length=last_sector-partition_start
            write_udf_record(stream,partition)
    integrity=iso.udf_logical_volume_integrity
    integrity.size_tables=[last_sector-partition_start]
    write_udf_record(stream,integrity)
    anchor=copy.deepcopy(iso.udf_anchors[0])
    anchor.set_extent_location(last_sector,anchor.main_vd.extent_location,
                               anchor.reserve_vd.extent_location)
    write_udf_record(stream,anchor)


def build(source,version,verify_existing=False):
    if not re.fullmatch(r'0\.\d+\.\d+',version):raise ValueError('Use version 0.x.y')
    source=Path(source).resolve();output=ROOT/'work/output'/('SRWMX_PS2_EN_'+version+'.iso')
    if output.exists() and not verify_existing:raise FileExistsError('Existing build preserved: '+str(output))
    if verify_existing and not output.exists():raise FileNotFoundError(output)
    actual=digest_file(source)
    if actual!=SOURCE_SHA256:raise ValueError('Unsupported source ISO: '+actual)
    evidence=ROOT/'work/build/ps2'/('font_'+version);evidence.mkdir(parents=True,exist_ok=True)
    iso=pycdlib.PyCdlib();iso.open(str(source));record=iso.get_record(iso_path='/SLPS_253.45;1')
    with iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as f:original=f.read()
    if hashlib.sha256(original).hexdigest()!=ELF_SHA256:raise ValueError('Unexpected executable')
    elf,patch=patch_elf(original,evidence,baseline_fix=False)
    mips=verify(original,elf,patch)
    (evidence/'SLPS_253.45').write_bytes(elf)
    root=record.parent.extent_location()*2048
    with source.open('rb') as f:f.seek(root);directory=f.read(record.parent.data_length)
    pos=0;found=[]
    while pos<len(directory):
        size=directory[pos]
        if not size:pos=(pos+2048)&~2047;continue
        if directory[pos+33:pos+33+directory[pos+32]]==b'SLPS_253.45;1':found.append(root+pos)
        pos+=size
    if len(found)!=1:raise ValueError('Ambiguous root directory entry')
    assert source.stat().st_size%2048==0
    sector=source.stat().st_size//2048
    if not verify_existing:
      output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,output)
      with output.open('r+b') as f:
        f.seek(0,2);f.write(elf);f.write(bytes(-len(elf)%2048))
        # This disc is ISO9660/UDF bridged. Keep both directory views in
        # agreement and put a valid UDF anchor at the enlarged disc's end.
        last_sector=f.tell()//2048;f.write(bytes(2048));total=last_sector+1
        f.seek(found[0]+2);f.write(struct.pack('<I',sector)+struct.pack('>I',sector))
        f.seek(found[0]+10);f.write(struct.pack('<I',len(elf))+struct.pack('>I',len(elf)))
        # Update all primary/supplementary volume descriptors; no paths move.
        descriptor=16
        while True:
            f.seek(descriptor*2048);head=f.read(7)
            if head[1:6]!=b'CD001':raise ValueError('Invalid volume descriptor')
            if head[0]==255:break
            if head[0] in (1,2):
                f.seek(descriptor*2048+80);f.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,f,sector,len(elf),last_sector)
    rebuilt=pycdlib.PyCdlib();rebuilt.open(str(output));file_checks=[]
    for path in sorted(files(iso)):
        a=iso.get_record(iso_path=path);b=rebuilt.get_record(iso_path=path)
        ah=digest_iso_file(iso,path);bh=digest_iso_file(rebuilt,path)
        changed=path=='/SLPS_253.45;1'
        assert bh==patch['target_sha256'] if changed else ah==bh,path
        if not changed:assert a.extent_location()==b.extent_location(),path
        file_checks.append(dict(path=path,original_sha256=ah,target_sha256=bh,
                               original_sector=a.extent_location(),target_sector=b.extent_location(),
                               bytes=b.data_length,changed=changed))
    # Read the appended executable independently through the UDF view too.
    with rebuilt.open_file_from_iso(udf_path='/SLPS_253.45') as f:
        assert hashlib.sha256(f.read()).hexdigest()==patch['target_sha256']
    udf_anchor_count=len(rebuilt.udf_anchors)
    assert udf_anchor_count>=2
    assert len(file_checks)==37
    rebuilt.close();iso.close()
    final_source=digest_file(source);assert final_source==actual
    report=dict(version=version,platform='PS2',scope='Native 4x VWF font only; story/UI translations pending',
                source_sha256=actual,target_sha256=digest_file(output),bytes=output.stat().st_size,
                output=str(output),source_unchanged=True,all_original_asset_lbas_retained=True,
                unchanged_files=36,changed_files=1,files=file_checks,font=patch,
                iso9660_and_udf_executable_agree=True,udf_anchor_count=udf_anchor_count,
                mips_checks={k:v for k,v in mips.items() if not isinstance(v,list)},
                pcsx2_visual_validation='pending',physical_ps2_validation='pending')
    (ROOT/'work/output'/('ps2_font_'+version+'_verification.json')).write_text(
        json.dumps(report,indent=2)+'\n',encoding='utf8')
    (ROOT/'work/output'/('ps2_font_'+version+'_mips_verification.json')).write_text(
        json.dumps(mips,indent=2)+'\n',encoding='utf8')
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',output.with_name(output.stem+'_FONT_LICENSE.txt'))
    ui=ROOT/'work/ui/ps2';ui.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(evidence/'atlas.png',ui/('font_atlas_'+version+'.png'))
    print(json.dumps({k:v for k,v in report.items() if k not in ('font','files','mips_checks')},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('version')
    p.add_argument('--verify-existing',action='store_true',help='Read-only verification of a previously built ISO')
    a=p.parse_args();build(a.source,a.version,a.verify_existing)
