"""Compact local PS2 stage-30 ISO: original disc plus current English assets."""
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path
import pycdlib
from build_ps2_font import SOURCE_SHA256, digest_file, digest_iso_file, files, patch_udf, write_udf_record
from build_ps2_dialogue import directory_position, copy_bytes
from port_ps2_stage30 import ROOT, BASE, VERSION, SOURCE_VERSION
from port_ps2_prologue import save


def build(base=BASE, version=VERSION, source_version=SOURCE_VERSION, extra_files=()):
    # Also supports incremental corrections while preserving older builds.
    BASE, VERSION, SOURCE_VERSION = base, version, source_version
    original=ROOT/'Super Robot Taisen MX (Japan).iso'
    previous=json.loads((ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json').read_text())
    source=ROOT/previous['output'];output=ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso'
    assert not output.exists(),'Existing build preserved'
    assert digest_file(original)==SOURCE_SHA256
    assert digest_file(source)==previous['target_sha256']
    execution=json.loads((ROOT/'work/output'/f'ps2_stage30_{VERSION}_execution.json').read_text())
    info=json.loads((BASE/'stage30.json').read_text());font=json.loads((BASE/'patch.json').read_text())
    replacements={row['path']:None for row in previous['files'] if row['original_sha256']!=row['target_sha256']}
    for name in ('SLPS_253.45','MAP.BIN','STAGE.BIN','FIX00.DAT','D2MAPH.BIN','PACKMAPC.BIN','STATIC.BIN',*extra_files):
        path='/'+name+';1' if name=='SLPS_253.45' else '/DATA/'+name+';1'
        replacements[path]=BASE/name
    records={row['path']:row for row in previous['files']}
    sizes={path:local.stat().st_size if local else records[path]['bytes'] for path,local in replacements.items()}
    hashes={path:digest_file(local) if local else records[path]['target_sha256'] for path,local in replacements.items()}
    projected=original.stat().st_size+sum((n+2047)//2048*2048 for n in sizes.values())+2048
    assert projected<=4700372992,'Single-layer DVD capacity exceeded before creating output'
    iso=pycdlib.PyCdlib();iso.open(str(original));old=pycdlib.PyCdlib();old.open(str(source))
    positions={path:directory_position(iso,original,path) for path in replacements}
    udf_names={name.lower():name for _,_,names in iso.walk(udf_path='/data') for name in names}
    udf={p:('/SLPS_253.45' if p=='/SLPS_253.45;1' else '/data/'+udf_names[p.rsplit('/',1)[-1].split(';')[0].lower()]) for p in replacements}
    shutil.copyfile(original,output);locations={}
    with output.open('r+b') as dst:
        dst.seek(0,2)
        for path,local in replacements.items():
            locations[path]=dst.tell()//2048
            if local:
                with local.open('rb') as src:copy_bytes(src,dst,sizes[path])
            else:
                with old.open_file_from_iso(iso_path=path) as src:copy_bytes(src,dst,sizes[path])
            dst.write(bytes(-sizes[path]%2048))
        last=dst.tell()//2048;dst.write(bytes(2048));total=last+1
        assert total*2048==projected
        for path in replacements:
            dst.seek(positions[path]+2);dst.write(struct.pack('<I',locations[path])+struct.pack('>I',locations[path]))
            dst.seek(positions[path]+10);dst.write(struct.pack('<I',sizes[path])+struct.pack('>I',sizes[path]))
        descriptor=16
        while True:
            dst.seek(descriptor*2048);head=dst.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                dst.seek(descriptor*2048+80);dst.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,dst,locations['/SLPS_253.45;1'],sizes['/SLPS_253.45;1'],last)
        start=iso.udf_main_descs.partitions[0].part_start_location
        for path in replacements:
            if path=='/SLPS_253.45;1':continue
            entry=iso.get_record(udf_path=udf[path]);assert len(entry.alloc_descs)==1
            entry.set_data_length(sizes[path]);entry.set_data_location(locations[path],locations[path]-start)
            entry.log_block_recorded=(sizes[path]+2047)//2048;write_udf_record(dst,entry)
    checked=pycdlib.PyCdlib();checked.open(str(output));checks=[]
    for path in sorted(files(iso)):
        a=iso.get_record(iso_path=path);b=checked.get_record(iso_path=path)
        actual=digest_iso_file(checked,path);expected=hashes.get(path,records[path]['target_sha256'])
        assert actual==expected,path
        if path not in replacements:assert a.extent_location()==b.extent_location()
        checks.append(dict(path=path,changed=path in replacements,original_sha256=records[path]['original_sha256'],
            target_sha256=actual,original_sector=a.extent_location(),target_sector=b.extent_location(),bytes=b.data_length))
    for path in replacements:
        h=hashlib.sha256()
        with checked.open_file_from_iso(udf_path=udf[path]) as src:
            for chunk in iter(lambda:src.read(8*1024*1024),b''):h.update(chunk)
        assert h.hexdigest()==hashes[path],path
    assert len(checks)==37 and len(checked.udf_anchors)>=2
    checked.close();old.close();iso.close()
    assert digest_file(original)==SOURCE_SHA256 and digest_file(source)==previous['target_sha256']
    evidence=ROOT/'work/build/ps2'/f'font_{VERSION}';evidence.mkdir(exist_ok=True)
    shutil.copyfile(BASE/'SLPS_253.45',evidence/'SLPS_253.45');save(evidence/'patch.json',font)
    report=copy.deepcopy(previous)
    report.update(version=VERSION,source_build_version=SOURCE_VERSION,source_build_sha256=previous['target_sha256'],
        output=str(output.relative_to(ROOT)),bytes=projected,target_sha256=digest_file(output),font=font,files=checks,
        difficulty=json.loads((BASE/'difficulty.json').read_text()),prologue=json.loads((BASE/'prologue.json').read_text()),
        stage30=info,stage30_execution_checks=execution,scenario_records=69,total_scenes=203,translated_scenes=197,
        title_card_atlases=200,scope='English PS2 campaign with both PSP extra scenarios, native 4x VWF and selectable balance; new games only',
        source_unchanged=True,source_build_unchanged=True,changed_files=len(replacements),unchanged_files=37-len(replacements),
        compact_disc_rebuilt_from_original=True,all_preserved_resources_rehashed=True,
        iso9660_and_udf_all_replacements_agree=True,script_commands_unchanged=False,
        script_command_changes='Nine PSP portrait-cache commands adapted to native PS2 no-op 178; all operands and event indexes retained',
        native_translation_hook_checks=execution['translations'],mips_checks=execution['font'],
        difficulty_execution_checks=execution['difficulty'],prologue_execution_checks=execution['prologue'],
        prologue_new_game_entry_checks=execution['new_game'],prologue_numbering_checks=execution['numbering'],
        pcsx2_visual_validation='pending for stage 29/30',physical_ps2_validation='pending',github_release=False,
        pending=['Stage 29/30 full battle clear and memory-card save/load in PCSX2','Physical PS2 validation','Existing campaign save migration is not implemented'])
    # Previous totals refer to the replaced original three scenes. Recount
    # readable string slots directly instead of retaining a stale aggregate.
    import play_order,export_rows
    elf=(BASE/'SLPS_253.45').read_bytes();maps=(BASE/'MAP.BIN').read_bytes()
    seg=int(font['segment_offset'],16);va=int(font['segment_va'],16)
    table=seg+int(info['script_sector_table_va'],16)-va
    sectors=struct.unpack_from('<204I',elf,table);base=struct.unpack_from('<18I',elf,0x37e438)[10]*2048
    report['translated_strings']=sum(sum(bool(export_rows.classify(t)) for t in play_order.load(maps[base+sectors[i]*2048:base+sectors[i+1]*2048],0)[1]) for i in range(203))
    report['translated_scenes']=sum(any(export_rows.classify(t) for t in play_order.load(maps[base+sectors[i]*2048:base+sectors[i+1]*2048],0)[1]) for i in range(203))
    old_blocks={x['index']:x for x in report['blocks']};new_scenes={x['index']:x for x in info['scenes']}
    names=[]
    for ptr in struct.unpack_from('<203I',elf,seg+int(info['script_name_table_va'],16)-va):
        off=seg+ptr-va;names.append(elf[off:elf.index(0,off)].decode())
    report['blocks']=[]
    for index in range(203):
        raw=maps[base+sectors[index]*2048:base+sectors[index+1]*2048]
        commands,texts=play_order.load(raw,0);block=copy.deepcopy(old_blocks.get(index,{}))
        block.update(scene=names[index],index=index,commands=len(commands),new_bytes=len(raw),
            new_sha256=hashlib.sha256(raw).hexdigest(),commands_sha256=hashlib.sha256(raw[32:32+len(commands)*48]).hexdigest(),
            relative_sector=sectors[index],translated_strings=sum(bool(export_rows.classify(t)) for t in texts))
        if index in new_scenes:
            block.update(translated_strings=new_scenes[index]['translated_strings'],source_sha256=new_scenes[index]['source_sha256'],
                psp_portrait_cache_commands=new_scenes[index]['psp_portrait_cache_commands'])
        report['blocks'].append(block)
    correction=BASE/'prologue_fix.json'
    if correction.exists():
        report['prologue_corrections']=json.loads(correction.read_text())
        report['prologue_correction_execution_checks']=json.loads((ROOT/'work/output'/f'ps2_prologue_fix_{VERSION}_execution.json').read_text())
    ui_fix=BASE/'ui_fix.json'
    if ui_fix.exists():
        report['ui_corrections']=json.loads(ui_fix.read_text())
        report['ui_correction_execution_checks']=json.loads((ROOT/'work/output'/f'ps2_ui_{VERSION}_execution.json').read_text())
    ui_details=BASE/'ui_details.json'
    if ui_details.exists():
        report['ui_detail_corrections']=json.loads(ui_details.read_text())
        report['ui_detail_execution_checks']=json.loads((ROOT/'work/output'/f'ps2_ui_details_{VERSION}_execution.json').read_text())
    roster_system=BASE/'roster_system.json'
    if roster_system.exists():
        report['roster_system_corrections']=json.loads(roster_system.read_text())
        report['roster_system_execution_checks']=json.loads((ROOT/'work/output'/f'ps2_roster_system_{VERSION}_execution.json').read_text())
    setup_save=BASE/'setup_save.json'
    if setup_save.exists():
        report['setup_save_corrections']=json.loads(setup_save.read_text())
        report['setup_save_execution_checks']=json.loads((ROOT/'work/output'/f'ps2_setup_save_{VERSION}_execution.json').read_text())
    map_support=BASE/'map_support.json'
    if map_support.exists():
        report['map_support_corrections']=json.loads(map_support.read_text())
        report['map_support_pixel_checks']=json.loads((ROOT/'work/output'/f'ps2_map_support_{VERSION}_verification.json').read_text())
    weapon_battle=BASE/'weapon_battle.json'
    if weapon_battle.exists():
        report['weapon_battle_corrections']=json.loads(weapon_battle.read_text())
        report['weapon_battle_execution_checks']=json.loads((ROOT/'work/output'/f'ps2_weapon_battle_{VERSION}_execution.json').read_text())
    forecast_badges=BASE/'forecast_badges.json'
    if forecast_badges.exists():
        report['forecast_badge_corrections']=json.loads(forecast_badges.read_text())
        report['forecast_badge_pixel_checks']=json.loads((ROOT/'work/output'/f'ps2_forecast_badges_{VERSION}_verification.json').read_text())
    # Screenshots from an earlier disc never validate a newly built executable.
    for key in ('ui_visual_validation','visual_checks','visual_evidence','visual_blocker'):
        report.pop(key,None)
    save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',report)
    save(ROOT/'work/translation/en/ps2/stage30_port.en.json',info)
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',output.with_name(output.stem+'_FONT_LICENSE.txt'))
    print(json.dumps(dict(version=VERSION,bytes=projected,sha256=report['target_sha256'],files_verified=37,
        all_english_resources_preserved=True,single_layer_dvd=True,github_release=False),indent=2))
    return report


if __name__=='__main__':build()
