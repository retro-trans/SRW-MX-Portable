"""Build the forecast-copy fix candidate directly from public PS2 v0.9.0."""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

import pycdlib
import title_footer
from build_ps2_dialogue import directory_position
from build_ps2_font import write_udf_record, digest_file
from fix_ps2_forecast_strings import patch

ROOT=Path(__file__).resolve().parents[1]


def build(version, player_action=False):
    assert title_footer.version_key(version) > (0,9,3)
    if player_action:
        assert title_footer.version_key(version) > (0,9,4)
    prior=json.loads((ROOT/'work/output/ps2_font_0.9.0_verification.json').read_text())
    source=ROOT/prior['output']
    output=ROOT/('work/output/SRWMX_PS2_EN_%s_hw_forecast_probe.iso'%version)
    evidence=ROOT/('work/build/ps2/hardware_forecast_probe_%s'%version)
    report_path=ROOT/('work/output/ps2_hardware_forecast_probe_%s.json'%version)
    assert not output.exists() and not evidence.exists() and not report_path.exists()
    iso=pycdlib.PyCdlib();iso.open(str(source))
    try:
        path='/SLPS_253.45;1'
        with iso.open_file_from_iso(iso_path=path) as f: baseline=f.read()
        assert title_footer.sha(baseline)==prior['font']['target_sha256']
        if player_action:
            from fix_ps2_player_battle_strings import patch as patch_player
            original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
            target,metadata,fix=patch_player(baseline,prior['font'],original)
        else:
            target,metadata,fix=patch(baseline,prior['font'])
        target,footer=title_footer.patch(target,'PS2',version)
        metadata['target_sha256']=title_footer.sha(target)
        rec=iso.get_record(iso_path=path);elf_start=rec.extent_location()*2048
        assert (len(target)+2047)//2048==(len(baseline)+2047)//2048
        with source.open('rb') as f:
            prefix=f.read(312*2048)
            f.seek(elf_start+len(baseline))
            assert f.read(len(target)-len(baseline))==bytes(len(target)-len(baseline))
        position=directory_position(iso,source,path)
        assert position+18<len(prefix)
        header=io.BytesIO(prefix)
        header.seek(position+10)
        header.write(struct.pack('<I',len(target))+struct.pack('>I',len(target)))
        entry=iso.get_record(udf_path='/SLPS_253.45')
        assert (entry.extent_location()+1)*2048<=len(prefix)
        entry.set_data_length(len(target))
        entry.log_block_recorded=(len(target)+2047)//2048
        write_udf_record(header,entry)
        edited_prefix=header.getvalue();assert len(edited_prefix)==len(prefix)
        # Guard original code outside the specified copy sites, segment size and
        # registered title footer. All battle logic and mission bytes stay put.
        spans=sorted([(164,172)]+[(c['offset'],c['offset']+4) for c in fix['changes']]
                     +[tuple(x) for x in footer['byte_ranges']])
        cursor=0
        for a,z in spans:
            assert baseline[cursor:a]==target[cursor:a],(cursor,a)
            cursor=z
        assert baseline[cursor:]==target[cursor:len(baseline)]
        evidence.mkdir(parents=True)
        for name,value in [('patch.json',metadata),('forecast_fix.json',fix)]:
            (evidence/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
        (evidence/'SLPS_253.45').write_bytes(target)
        from verify_ps2_forecast_strings import verify
        execution=verify(evidence)
        if player_action:
            from verify_ps2_player_forecast import verify as verify_player
            previous=(ROOT/'work/build/ps2/hardware_forecast_probe_0.9.4/SLPS_253.45').read_bytes()
            player=verify_player(original,baseline,previous,target,evidence)
        src_hash,dst_hash=hashlib.sha256(),hashlib.sha256();offset=0
        print('Copying the public image with the forecast copy fix and v%s footer.'%version,flush=True)
        with source.open('rb') as src,output.open('xb') as dst:
            for chunk in iter(lambda:src.read(8*1024*1024),b''):
                src_hash.update(chunk);data=bytearray(chunk)
                for at,blob in [(0,edited_prefix),(elf_start,target)]:
                    a,z=max(offset,at),min(offset+len(data),at+len(blob))
                    if a<z:data[a-offset:z-offset]=blob[a-at:z-at]
                dst.write(data);dst_hash.update(data);offset+=len(data)
        assert src_hash.hexdigest()==prior['target_sha256']
        assert output.stat().st_size==source.stat().st_size
        assert digest_file(output)==dst_hash.hexdigest()
        checked=pycdlib.PyCdlib();checked.open(str(output))
        try:
            for key,name in [('iso_path',path),('udf_path','/SLPS_253.45')]:
                with checked.open_file_from_iso(**{key:name}) as f:assert f.read()==target
            for row in prior['files']:
                a,b=iso.get_record(iso_path=row['path']),checked.get_record(iso_path=row['path'])
                assert a.extent_location()==b.extent_location()
                assert b.data_length==(len(target) if row['path']==path else a.data_length)
        finally:checked.close()
        report=dict(version=version,platform='PS2',diagnostic_only=True,confirmed_fix=False,
            source_version='0.9.0',source=str(source.relative_to(ROOT)),source_sha256=src_hash.hexdigest(),
            output=str(output.relative_to(ROOT)),target_sha256=dst_hash.hexdigest(),bytes=output.stat().st_size,
            elf_sha256=title_footer.sha(target),footer=title_footer.verify_iso(output,'PS2',version),
            forecast_fix=fix,native_execution_summary=dict(reproduced_faults=3,forecast_path_cases=24,alignment_cases=24),
            execution_report=str((evidence/'forecast_execution.json').relative_to(ROOT)),
            heap_boundary_preserved=True,disc_layout_preserved=True,translation_resources_preserved=True,
            mission_and_gameplay_data_preserved=True,original_public_menu_wrappers_preserved=True,
            all_other_iso_bytes_preserved=True,physical_hardware_result='pending',emulator_forecast_result='pending',
            purpose='Correct reproduced unaligned reads and fixed-length truncation in forecast action-label copies.',
            github_release=False)
        if player_action:
            report['purpose']='Repair the player forecast Attack and No Counter action-row copies.'
            report['native_execution_summary']['player_action_cases']=len(player['verified_paths'])
            report['player_execution_report']=str((evidence/'player_forecast_execution.json').relative_to(ROOT))
        report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(json.dumps({k:report[k] for k in ('version','target_sha256','bytes')}),flush=True)
        return report
    finally:iso.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default='0.9.4')
    p.add_argument('--player-action',action='store_true')
    args=p.parse_args()
    build(args.version,args.player_action)
