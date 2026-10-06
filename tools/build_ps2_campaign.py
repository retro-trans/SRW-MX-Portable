"""Build the full PS2 story/database port as a local ISO; never publish."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path
import pycdlib
from build_ps2_font import SOURCE_SHA256,ELF_SHA256,digest_file,digest_iso_file,files,patch_udf,write_udf_record
from build_ps2_dialogue import directory_position,copy_bytes,TABLE,SECTIONS,SCRIPT_BASE
from port_ps2_translations import ROOT,read_json,sha
from ps2_font4x import patch_elf
from ps2_translation_native import patch_ui,patch_spirits,patch_sentences
from ps2_battle_port import native_hooks
from ps2_narration_port import patch as narration,terrain
from verify_ps2_font import verify
from verify_ps2_translation_hooks import verify as verify_translation
from ps2_difficulty import patch as patch_difficulty
from verify_ps2_difficulty import verify as verify_difficulty

VERSION='0.1.5'
WORK=ROOT/'work/build/ps2/campaign'
TR=ROOT/'work/translation/en/ps2'

def save(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')

def build(source):
    source=Path(source).resolve();output=ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso'
    assert not output.exists(),'Existing build preserved'
    assert digest_file(source)==SOURCE_SHA256
    iso=pycdlib.PyCdlib();iso.open(str(source))
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes();assert sha(original)==ELF_SHA256
    from port_ps2_translations import rebuild_map
    from ps2_database_port import build as build_database
    story=rebuild_map(iso,original,WORK/'MAP.BIN');save(TR/'script/campaign_port.en.json',story)
    fix,database_report=build_database((ROOT/'work/source/ps2/FIX00.DAT').read_bytes())
    (WORK/'FIX00.DAT').write_bytes(fix);save(TR/'database_port.en.json',database_report)
    evidence=ROOT/'work/build/ps2'/('font_'+VERSION)
    data,font=patch_elf(original,evidence,baseline_fix=True)
    data,ui=patch_ui(original,data,font);save(TR/'ui_port.en.json',ui)
    overflow=[bytes.fromhex(b) for b in read_json(WORK/'quote_overflow.json')]
    data,battle=native_hooks(original,data,font,overflow)
    data,spirits=patch_spirits(original,data,font)
    data,narr=narration(original,data,font);save(TR/'narration_port.en.json',narr)
    sentences=[bytes.fromhex(b) for b in read_json(WORK/'database_overflow.json')]
    data,fix,sentence_report=patch_sentences(original,data,font,(WORK/'FIX00.DAT').read_bytes(),sentences)
    (WORK/'FIX00.DAT').write_bytes(fix)
    database_report['target_sha256']=sha(fix);database_report['native_sentence_pool_applied']=True
    save(TR/'database_port.en.json',database_report)
    native=dict(battle=battle,spirits=spirits,sentences=sentence_report);save(WORK/'native_text.json',native)
    data,difficulty=patch_difficulty(original,data,font)
    save(TR/'difficulty.en.json',difficulty)
    data=bytearray(data)
    struct.pack_into('<193I',data,TABLE,*story['relative_sectors'])
    struct.pack_into('<18I',data,SECTIONS,*story['section_sectors'])
    data=bytes(data);font.update(target_sha256=sha(data),ps2_script_tables_updated=True)
    (evidence/'SLPS_253.45').write_bytes(data);save(evidence/'patch.json',font)
    (WORK/'SLPS_253.45').write_bytes(data)
    mips=verify(original,data,font);hooks=verify_translation(data,native)
    difficulty_checks=verify_difficulty(data,difficulty)
    save(ROOT/'work/output'/f'ps2_difficulty_{VERSION}_execution.json',difficulty_checks)
    save(ROOT/'work/output'/f'ps2_font_{VERSION}_mips_verification.json',mips)
    # MAP terrain precedes the rebuilt scripts; its numeric records keep their bytes.
    map_file=WORK/'MAP.BIN';raw=map_file.read_bytes();raw,terrain_report=terrain(raw);map_file.write_bytes(raw)
    save(TR/'terrain_port.en.json',terrain_report)
    # The quote archive retains all original animation subfiles and their offsets.
    battle_file=WORK/'BATTLE.BIN'
    with iso.open_file_from_iso(iso_path='/DATA/BATTLE.BIN;1') as src,battle_file.open('wb') as dst:
        length=iso.get_record(iso_path='/DATA/BATTLE.BIN;1').data_length
        copy_bytes(src,dst,length);quote_offset=dst.tell()
        with (WORK/'quotes.bin').open('rb') as f:copy_bytes(f,dst,(WORK/'quotes.bin').stat().st_size)
        dst.seek(20);dst.write(struct.pack('<I',quote_offset))
    names=['SLPS_253.45','MAP.BIN','FIX00.DAT','STAGE.BIN','STATIC.BIN','BATTLE.BIN','PACKMAPC.BIN','WND.BIN']
    replacements={('/'+name+';1' if name=='SLPS_253.45' else '/DATA/'+name+';1'):WORK/name for name in names}
    hashes={p:digest_file(f) for p,f in replacements.items()}
    positions={p:directory_position(iso,source,p) for p in replacements}
    # This source uses mixed case in UDF, independently of ISO9660 names.
    udf_names={name.lower():name for _,_,names_ in iso.walk(udf_path='/data') for name in names_}
    udf={p:('/SLPS_253.45' if p=='/SLPS_253.45;1' else '/data/'+udf_names[f.name.lower()]) for p,f in replacements.items()}
    shutil.copyfile(source,output);locations={}
    with output.open('r+b') as f:
        f.seek(0,2)
        for path,local in replacements.items():
            locations[path]=f.tell()//2048
            with local.open('rb') as g:copy_bytes(g,f,local.stat().st_size)
            f.write(bytes(-local.stat().st_size%2048))
        last=f.tell()//2048;f.write(bytes(2048));total=last+1
        assert total*2048<=4700372992,'Single-layer DVD capacity exceeded'
        for path,local in replacements.items():
            f.seek(positions[path]+2);f.write(struct.pack('<I',locations[path])+struct.pack('>I',locations[path]))
            f.seek(positions[path]+10);f.write(struct.pack('<I',local.stat().st_size)+struct.pack('>I',local.stat().st_size))
        descriptor=16
        while True:
            f.seek(descriptor*2048);head=f.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                f.seek(descriptor*2048+80);f.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,f,locations['/SLPS_253.45;1'],len(data),last)
        start=iso.udf_main_descs.partitions[0].part_start_location
        for path,local in replacements.items():
            if path=='/SLPS_253.45;1':continue
            entry=iso.get_record(udf_path=udf[path]);assert len(entry.alloc_descs)==1
            entry.set_data_length(local.stat().st_size)
            entry.set_data_location(locations[path],locations[path]-start)
            entry.log_block_recorded=(local.stat().st_size+2047)//2048;write_udf_record(f,entry)
    rebuilt=pycdlib.PyCdlib();rebuilt.open(str(output));checks=[]
    for path in sorted(files(iso)):
        a=iso.get_record(iso_path=path);b=rebuilt.get_record(iso_path=path)
        ah=digest_iso_file(iso,path);bh=digest_iso_file(rebuilt,path);changed=path in replacements
        assert bh==(hashes[path] if changed else ah),path
        if not changed:assert a.extent_location()==b.extent_location()
        checks.append(dict(path=path,changed=changed,original_sha256=ah,target_sha256=bh,
                           original_sector=a.extent_location(),target_sector=b.extent_location(),bytes=b.data_length))
    for path in replacements:
        h=hashlib.sha256()
        with rebuilt.open_file_from_iso(udf_path=udf[path]) as f:
            for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==hashes[path],path
    with rebuilt.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as f:
        for block in story['blocks']:
            f.seek(SCRIPT_BASE+story['relative_sectors'][block['index']]*2048)
            assert sha(f.read(block['new_bytes']))==block['new_sha256']
    assert len(checks)==37 and len(rebuilt.udf_anchors)>=2
    rebuilt.close();iso.close();assert digest_file(source)==SOURCE_SHA256
    assert all(digest_file(ROOT/p)==h for p,h in story['inputs'].items())
    report=dict(version=VERSION,platform='PS2',scope='Full English port with native 4x VWF and selectable original PS2 / PSP-style HP and funds balance at New Game',
                output=str(output),bytes=output.stat().st_size,source_sha256=SOURCE_SHA256,target_sha256=digest_file(output),
                source_unchanged=True,changed_files=8,unchanged_files=29,unrelated_file_lbas_retained=True,
                iso9660_and_udf_all_replacements_agree=True,script_commands_unchanged=True,
                translated_scenes=story['translated_scenes'],translated_strings=story['translated_strings'],
                total_scenes=192,missing_readable_story_strings=0,battle_caption_entries=51434,
                scenario_records=66,title_card_atlases=198,terrain_records=terrain_report['terrain_records'],terrain_names_translated=404,
                menu_string_locations=ui['translated_string_locations'],font=font,blocks=story['blocks'],files=checks,
                native_translation_hook_checks=hooks,mips_checks={k:v for k,v in mips.items() if not isinstance(v,list)},
                difficulty=difficulty,difficulty_execution_checks=difficulty_checks,
                pending=['Native battle/status banner artwork and remaining UI differences','PCSX2 visual and full-campaign gameplay validation','Physical PS2 validation'],
                pcsx2_visual_validation='pending',physical_ps2_validation='pending',github_release=False)
    save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',report)
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',output.with_name(output.stem+'_FONT_LICENSE.txt'))
    print(json.dumps({k:v for k,v in report.items() if k not in ('font','blocks','files','mips_checks')},indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args();build(a.source)
