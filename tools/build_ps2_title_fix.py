"""Versioned PS2 native-title correction over an immutable local candidate."""
import copy
import json
import shutil
import struct
from pathlib import Path
import pycdlib
import ps2_title_footer as footer
from title_footer import ROOT, ranges, render, region, sha
from build_ps2_font import patch_udf, digest_file, files, digest_iso_file
from build_ps2_dialogue import directory_position

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')

def build(base='0.4.25',version='0.4.26'):
    source=ROOT/f'work/output/SRWMX_PS2_EN_{base}.iso'
    output=ROOT/f'work/output/SRWMX_PS2_EN_{version}.iso'
    assert not output.exists()
    prior=json.loads((ROOT/f'work/output/ps2_font_{base}_verification.json').read_text())
    assert digest_file(source)==prior['target_sha256']
    iso=pycdlib.PyCdlib();iso.open(str(source))
    with iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as f:elf=f.read()
    assert sha(elf)==prior['font']['target_sha256']
    elf,evidence,meta=footer.patch(elf,version,prior['font'])
    with iso.open_file_from_iso(iso_path='/DATA/IM.BIN;1') as f:im=f.read()
    native=(ROOT/'work/source/ps2/IM.BIN').read_bytes()
    assert region(im,'PS2')==render(native,'PS2',base)[0]
    restored=bytearray(im)
    for a,z in ranges('PS2'):restored[a:z]=native[a:z]
    position=directory_position(iso,source,'/SLPS_253.45;1')
    extent=iso.get_record(iso_path='/DATA/IM.BIN;1').extent_location()*2048
    shutil.copyfile(source,output)
    with output.open('r+b') as f:
        for a,z in ranges('PS2'):f.seek(extent+a);f.write(restored[a:z])
        f.seek(0,2);sector=f.tell()//2048
        f.write(elf);f.write(bytes(-len(elf)%2048));last=f.tell()//2048
        f.write(bytes(2048));total=last+1
        f.seek(position+2);f.write(struct.pack('<I',sector)+struct.pack('>I',sector))
        f.seek(position+10);f.write(struct.pack('<I',len(elf))+struct.pack('>I',len(elf)))
        descriptor=16
        while True:
            f.seek(descriptor*2048);head=f.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                f.seek(descriptor*2048+80);f.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,f,sector,len(elf),last)
    result=pycdlib.PyCdlib();result.open(str(output));checks=[]
    for path in files(iso):
        before=digest_iso_file(iso,path);after=digest_iso_file(result,path)
        expected=sha(elf) if path=='/SLPS_253.45;1' else sha(restored) if path=='/DATA/IM.BIN;1' else before
        assert after==expected,path
        old=iso.get_record(iso_path=path);new=result.get_record(iso_path=path)
        if path!='/SLPS_253.45;1':assert (old.extent_location(),old.data_length)==(new.extent_location(),new.data_length)
        checks.append(dict(path=path,source_sha256=before,target_sha256=after,bytes=new.data_length,target_sector=new.extent_location()))
    for path,data in [('/SLPS_253.45',elf),('/data/im.bin',restored)]:
        with result.open_file_from_iso(udf_path=path) as f:assert f.read()==data
    footer.verify(elf,version);result.close();iso.close()
    work=ROOT/f'work/build/ps2/font_{version}';work.mkdir(parents=True,exist_ok=True)
    (work/'SLPS_253.45').write_bytes(elf);save(work/'patch.json',meta)
    evidence.update(target_resource_sha256=sha(elf),readback=footer.verify(elf,version),
                    wrong_background_footer_removed=True,restored_background_sha256=sha(restored))
    report=dict(version=version,base_version=base,platform='PS2',footer=evidence,files=checks,
        output=output.relative_to(ROOT).as_posix(),output_sha256=digest_file(output),bytes=output.stat().st_size,
        all_unrelated_game_files_preserved=True,iso9660_and_udf_agree=True,
        in_game_visual_validation='pending',local_build_only=True,github_release=False)
    save(ROOT/f'work/output/ps2_title_footer_{version}_verification.json',report)
    aggregate=copy.deepcopy(prior);lookup={r['path']:r for r in checks}
    for r in aggregate['files']:
        current=lookup[r['path']]
        r.update(target_sha256=current['target_sha256'],bytes=current['bytes'],target_sector=current['target_sector'])
    aggregate.update(version=version,output=report['output'],target_sha256=report['output_sha256'],bytes=report['bytes'],
        font=meta,title_footer=evidence,source_build_version=base,source_build_sha256=prior['target_sha256'],
        changed_from_previous=['/SLPS_253.45;1','/DATA/IM.BIN;1'],
        current_correction_report=f'work/output/ps2_title_footer_{version}_verification.json',
        pcsx2_fresh_boot_verified=False,pcsx2_visual_validation='Native title pending',github_release=False)
    save(ROOT/f'work/output/ps2_font_{version}_verification.json',aggregate)
    save(ROOT/f'work/translation/en/ps2/title_footer_{version}.en.json',report)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),output.with_name(output.stem+'_FONT_LICENSE.txt'))
    print(report['output'],report['output_sha256'],flush=True)

if __name__=='__main__':build()
