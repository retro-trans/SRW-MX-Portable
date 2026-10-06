"""Build a new local version from a verified campaign disc and corrected ELF."""
import argparse
import hashlib
import json
import shutil
import struct
import pycdlib
from port_ps2_translations import ROOT,sha
from build_ps2_font import digest_file,patch_udf
from build_ps2_dialogue import directory_position
from verify_ps2_font import verify as verify_font
from verify_ps2_translation_hooks import verify as verify_text
from verify_ps2_difficulty import verify as verify_difficulty

def save(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-version',default='0.1.4')
    p.add_argument('--version',default='0.1.5')
    p.add_argument('--feature',choices=['difficulty','prologue'],default='difficulty')
    args=p.parse_args()
    report_path=ROOT/'work/output'/f'ps2_font_{args.version}_verification.json'
    report=json.loads((ROOT/'work/output'/f'ps2_font_{args.source_version}_verification.json').read_text())
    source=ROOT/report['output'];output=ROOT/'work/output'/f'SRWMX_PS2_EN_{args.version}.iso'
    assert report['version']==args.source_version and not report['github_release']
    assert not output.exists(),'Existing build preserved'
    assert digest_file(source)==report['target_sha256']
    base=ROOT/'work/build/ps2'/(args.feature+'_'+args.version)
    data=(base/'SLPS_253.45').read_bytes();font=json.loads((base/'patch.json').read_text())
    feature=json.loads((base/(args.feature+'.json')).read_text())
    difficulty=(feature if args.feature=='difficulty' else report['difficulty'])
    assert sha(data)==font['target_sha256']
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    mips=verify_font(original,data,font)
    native=json.loads((ROOT/'work/build/ps2/campaign/native_text.json').read_text())
    text_checks=verify_text(data,native);difficulty_checks=verify_difficulty(data,difficulty)
    if args.feature=='prologue':
        from verify_ps2_prologue_entry import verify as verify_entry
        from verify_ps2_prologue import verify as verify_prologue
        entry_checks=verify_entry(data,(base/'STAGE.BIN').read_bytes())
        prologue_checks=verify_prologue(args.version)
        if 'chapter_numbering' in feature:
            from verify_ps2_prologue_numbering import verify as verify_numbering
            numbering_checks=verify_numbering(data)
    iso=pycdlib.PyCdlib();iso.open(str(source))
    with iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as f:old=f.read()
    assert sha(old)==report['font']['target_sha256']
    # Only known feature sites and InitHeap may differ before the feature payload.
    boundary=(int(difficulty['mode_va'],16)-int(font['segment_va'],16)+int(font['segment_offset'],16)
              if args.feature=='difficulty' else len(old))
    allowed=set()
    for x in feature['hooks']:
        address=int(x['va'],16)-0xff000;allowed.update(range(address,address+len(bytes.fromhex(x['new']))))
    allowed.update(range(0x100180-0xff000,0x100184-0xff000))
    allowed.update(range(0x100188-0xff000,0x10018c-0xff000))
    allowed.update(range(164,172))  # ELF segment filesz/memsz.
    unexpected=[i for i in range(boundary) if old[i]!=data[i] and i not in allowed]
    assert not unexpected,unexpected[:20]
    before={x['path']:(iso.get_record(iso_path=x['path']).extent_location(),iso.get_record(iso_path=x['path']).data_length) for x in report['files']}
    pos=directory_position(iso,source,'/SLPS_253.45;1')
    shutil.copyfile(source,output)
    with output.open('r+b') as f:
        f.seek(0,2);sector=f.tell()//2048;assert f.tell()%2048==0
        f.write(data);f.write(bytes(-len(data)%2048));last=f.tell()//2048;f.write(bytes(2048));total=last+1
        assert total*2048<=4700372992
        f.seek(pos+2);f.write(struct.pack('<I',sector)+struct.pack('>I',sector))
        f.seek(pos+10);f.write(struct.pack('<I',len(data))+struct.pack('>I',len(data)))
        descriptor=16
        while True:
            f.seek(descriptor*2048);head=f.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                f.seek(descriptor*2048+80);f.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,f,sector,len(data),last)
    iso.close();checked=pycdlib.PyCdlib();checked.open(str(output))
    for path in ('iso','udf'):
        with checked.open_file_from_iso(**({'iso_path':'/SLPS_253.45;1'} if path=='iso' else {'udf_path':'/SLPS_253.45'})) as f:
            assert sha(f.read())==sha(data)
    for item in report['files']:
        path=item['path'];record=checked.get_record(iso_path=path)
        if path=='/SLPS_253.45;1':item.update(target_sha256=sha(data),target_sector=sector,bytes=len(data))
        else:
            assert (record.extent_location(),record.data_length)==before[path]
            with checked.open_file_from_iso(iso_path=path) as f:
                h=hashlib.sha256()
                while chunk:=f.read(8*1024*1024):h.update(chunk)
                assert h.hexdigest()==item['target_sha256'],path
    checked.close()
    report.update(version=args.version,output=str(output.relative_to(ROOT)),bytes=output.stat().st_size,target_sha256=digest_file(output),font=font,difficulty=difficulty,
                  difficulty_execution_checks=difficulty_checks,native_translation_hook_checks=text_checks,
                  mips_checks={k:v for k,v in mips.items() if not isinstance(v,list)},
                  source_build_version=args.source_version,source_build_sha256=report['target_sha256'],
                  preserved_candidate_resource_hashes=True,all_preserved_resources_rehashed=True,iso9660_and_udf_executable_agree=True)
    evidence=ROOT/'work/build/ps2'/('font_'+args.version);evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'SLPS_253.45').write_bytes(data);save(evidence/'patch.json',font)
    if args.feature=='difficulty':
        report['native_menu_opening_fixed']=True
        (ROOT/'work/build/ps2/campaign/SLPS_253.45').write_bytes(data)
        save(ROOT/'work/translation/en/ps2/difficulty.en.json',difficulty)
    else:
        report.update(prologue=feature,prologue_execution_checks=prologue_checks,
                      prologue_new_game_entry_checks=entry_checks,new_game_prologue_entry_fixed=True)
        save(ROOT/'work/translation/en/ps2/prologue_port.en.json',feature)
        save(ROOT/'work/output'/f'ps2_prologue_{args.version}_entry_execution.json',entry_checks)
        if 'chapter_numbering' in feature:
            report['prologue_numbering_checks']=numbering_checks
            save(ROOT/'work/output'/f'ps2_prologue_{args.version}_numbering_execution.json',numbering_checks)
    save(ROOT/'work/output'/f'ps2_difficulty_{args.version}_execution.json',difficulty_checks)
    save(ROOT/'work/output'/f'ps2_font_{args.version}_mips_verification.json',mips);save(report_path,report)
    print(json.dumps(dict(bytes=report['bytes'],sha256=report['target_sha256'],all_english_resources_preserved=True,heap_start=font['heap_start']),indent=2))

if __name__=='__main__':main()
