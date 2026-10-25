"""Build the guarded PS2 unit-rename fix over local v0.4.41, without a release."""
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path

import pycdlib
import fix_ps2_rename
import title_footer
from build_ps2_dialogue import directory_position
from build_ps2_font import digest_file,digest_iso_file,files,patch_udf
from port_ps2_translations import sha
from verify_ps2_rename import verify as verify_rename

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.4.43'
SOURCE=ROOT/'work/output/SRWMX_PS2_EN_0.4.41.iso'
TARGET=ROOT/f'work/output/SRWMX_PS2_EN_{VERSION}.iso'
BASE=ROOT/f'work/build/ps2/font_{VERSION}'


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def build():
    assert not TARGET.exists() and not BASE.exists(),'Preserve existing builds'
    previous=read(ROOT/'work/output/ps2_font_0.4.38_verification.json')
    baseline=read(ROOT/'work/output/ps2_sortie_header_0.4.41_verification.json')
    stat=SOURCE.stat()
    assert stat.st_size==baseline['bytes']
    print('Checking complete local v0.4.41 baseline',flush=True)
    assert digest_file(SOURCE)==baseline['output_sha256']
    title_footer.verify_iso(SOURCE,'PS2','0.4.41')
    iso=pycdlib.PyCdlib();iso.open(str(SOURCE))
    path='/SLPS_253.45;1'
    with iso.open_file_from_iso(iso_path=path) as stream:original=stream.read()
    # Builds 39-41 only replace native caption/header artwork and the footer;
    # the registered English font segment and hooks keep their layout.
    meta=copy.deepcopy(previous['font'])
    assert int(meta['segment_offset'],16)+meta['segment_bytes']==len(original)
    for h in meta['hooks']:
        va=int(h['va'],16)
        a=(int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
           if va>=int(meta['segment_va'],16) else va-fix_ps2_rename.BIAS)
        assert original[a:a+len(bytes.fromhex(h['new']))]==bytes.fromhex(h['new']),h
    meta['target_sha256']=sha(original)
    elf,meta,info=fix_ps2_rename.patch(original,meta)
    elf,footer=title_footer.patch(elf,'PS2',VERSION)
    meta['target_sha256']=sha(elf)
    # Reject any executable change outside the registered fix, segment sizing,
    # heap start and regenerated native footer.
    allowed_elf=[(int(h['va'],16)-fix_ps2_rename.BIAS,
                  int(h['va'],16)-fix_ps2_rename.BIAS+4) for h in info['instruction_words']]
    allowed_elf += [(164,172),(0x100180-fix_ps2_rename.BIAS,0x100184-fix_ps2_rename.BIAS),
        (0x100188-fix_ps2_rename.BIAS,0x10018c-fix_ps2_rename.BIAS)]
    allowed_elf += [tuple(row) for row in footer['byte_ranges']]
    masked=bytearray(elf[:len(original)])
    for a,z in allowed_elf:masked[a:z]=original[a:z]
    assert masked==original,'Unrelated executable bytes changed'
    print('Executing rename, editing, layout and font checks',flush=True)
    native=verify_rename(original,elf,meta)
    from verify_ps2_font import verify as verify_font
    font_checks=verify_font((ROOT/'work/source/ps2/SLPS_253.45').read_bytes(),elf,meta)
    BASE.mkdir(parents=True)
    (BASE/'SLPS_253.45').write_bytes(elf);save(BASE/'patch.json',meta)
    save(BASE/'unit_rename.json',info)
    save(BASE/'native_rename.json',native)
    save(ROOT/f'work/output/ps2_font_{VERSION}_mips_verification.json',font_checks)
    from verify_ps2_title_footer import main as verify_title
    verify_title(VERSION)
    sector=stat.st_size//2048
    last=sector+(len(elf)+2047)//2048;total=last+1
    assert total*2048<=4700372992,'Single-layer DVD capacity'
    position=directory_position(iso,SOURCE,path)
    allowed=[(position+2,position+18)]
    for entry in [iso.get_record(udf_path='/SLPS_253.45'),iso.udf_logical_volume_integrity,
                  *iso.udf_main_descs.partitions,*iso.udf_reserve_descs.partitions]:
        a=entry.extent_location()*2048;allowed.append((a,a+2048))
    print('Creating local PS2 v'+VERSION,flush=True)
    shutil.copyfile(SOURCE,TARGET)
    with TARGET.open('r+b') as dst:
        dst.seek(0,2);dst.write(elf);dst.write(bytes(-len(elf)%2048));dst.write(bytes(2048))
        dst.seek(position+2);dst.write(struct.pack('<I',sector)+struct.pack('>I',sector))
        dst.seek(position+10);dst.write(struct.pack('<I',len(elf))+struct.pack('>I',len(elf)))
        n=16
        while True:
            dst.seek(n*2048);head=dst.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                a=n*2048+80;dst.seek(a);dst.write(struct.pack('<I',total)+struct.pack('>I',total))
                allowed.append((a,a+8))
            n+=1
        patch_udf(iso,dst,sector,len(elf),last)
    print('Verifying all disc bytes, resources and both filesystems',flush=True)
    digest=hashlib.sha256()
    with SOURCE.open('rb') as src,TARGET.open('rb') as dst:
        at=0
        while raw:=src.read(8*1024*1024):
            current=dst.read(len(raw));assert len(current)==len(raw);digest.update(current)
            mask=bytearray(current)
            for a,z in allowed:
                left,right=max(at,a),min(at+len(raw),z)
                if left<right:mask[left-at:right-at]=raw[left-at:right-at]
            assert mask==raw,('Unrelated disc bytes changed',at)
            at+=len(raw)
        extra=dst.read();padded=elf+bytes(-len(elf)%2048)
        assert len(extra)==len(padded)+2048 and extra[:-2048]==padded
        digest.update(extra)
    checked=pycdlib.PyCdlib();checked.open(str(TARGET));records=[]
    old_records={r['path']:r for r in previous['files']}
    for p in sorted(files(iso)):
        a,b=iso.get_record(iso_path=p),checked.get_record(iso_path=p)
        actual=digest_iso_file(checked,p)
        assert actual==(sha(elf) if p==path else digest_iso_file(iso,p)),p
        if p!=path:assert a.extent_location()==b.extent_location() and a.data_length==b.data_length,p
        records.append(dict(path=p,bytes=b.data_length,changed=p==path,target_sha256=actual,
            original_sha256=old_records[p]['original_sha256'],original_sector=old_records[p]['original_sector'],
            target_sector=b.extent_location()))
    assert len(records)==37 and any(a.extent_location()==last for a in checked.udf_anchors)
    for key in ('iso_path','udf_path'):
        with checked.open_file_from_iso(**{key:path if key=='iso_path' else '/SLPS_253.45'}) as stream:
            actual_elf=stream.read();assert actual_elf==elf
    checked.close();iso.close()
    assert (SOURCE.stat().st_size,SOURCE.stat().st_mtime_ns)==(stat.st_size,stat.st_mtime_ns)
    assert TARGET.stat().st_size==total*2048
    assert verify_rename(original,actual_elf,meta)==native
    footer['readback']=title_footer.verify_iso(TARGET,'PS2',VERSION)
    result=dict(version=VERSION,platform='PS2',base_version='0.4.41',
        source_sha256=baseline['output_sha256'],output=TARGET.relative_to(ROOT).as_posix(),
        output_sha256=digest.hexdigest(),bytes=TARGET.stat().st_size,unit_rename_fix=info,
        native_execution=native,font_execution={k:v for k,v in font_checks.items() if not isinstance(v,list)},
        footer=footer,files=records,iso9660_and_udf_readback=True,
        all_other_disc_bytes_preserved=True,all_other_resource_locations_preserved=True,
        source_unchanged=True,pcsx2_visual_validation='pending',local_build_only=True,github_release=False)
    save(ROOT/f'work/output/ps2_rename_{VERSION}_verification.json',result)
    save(ROOT/f'work/translation/en/ps2/rename_{VERSION}.en.json',result)
    save(ROOT/f'work/output/ps2_title_footer_{VERSION}_verification.json',dict(version=VERSION,footer=footer))
    aggregate=copy.deepcopy(previous)
    aggregate.update(version=VERSION,output=result['output'],bytes=result['bytes'],target_sha256=result['output_sha256'],
        source_build_version='0.4.41',source_build_sha256=result['source_sha256'],files=records,font=meta,
        title_footer=footer,unit_rename_fix=info,current_correction_report=f'work/output/ps2_rename_{VERSION}_verification.json',
        unit_rename_native_execution=native,mips_checks=result['font_execution'],
        pcsx2_fresh_boot_verified=False,github_release=False)
    save(ROOT/f'work/output/ps2_font_{VERSION}_verification.json',aggregate)
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',TARGET.with_name(TARGET.stem+'_FONT_LICENSE.txt'))
    print('Verified local PS2',VERSION,result['output_sha256'],flush=True)


if __name__=='__main__':build()
