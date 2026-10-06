"""Read-only font verification against an explicitly selected test PINE port.

Boot the finished ISO in the isolated PCSX2 profile first. This checks native
loaded bytes, not visual rendering. Never use the user's normal emulator port.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
from pcsx2_pine import Pine
from ps2_font4x import ROOT, FILE_BIAS


def verify_runtime(version, port, profile):
    report=json.loads((ROOT/'work/output'/('ps2_font_'+version+'_verification.json')).read_text())
    patch=report['font']
    elf=(ROOT/'work/build/ps2'/('font_'+version)/'SLPS_253.45').read_bytes()
    assert hashlib.sha256(elf).hexdigest()==patch['target_sha256']
    profile=Path(profile)
    settings=configparser.ConfigParser(interpolation=None,strict=False)
    settings.read(profile/'inis/PCSX2.ini',encoding='utf-8-sig')
    assert settings.getboolean('EmuCore','EnablePINE')
    assert settings.getint('EmuCore','PINESlot')==port
    assert not settings.getboolean('EmuCore/GS','LoadTextureReplacements')
    with Pine(port) as p:
        va=int(patch['segment_va'],16);offset=int(patch['segment_offset'],16)
        size=patch['segment_bytes'];ram=p.read(va,size)
        hooks=[]
        for item in patch['hooks']:
            expected=bytes.fromhex(item['new'])
            hooks.append(dict(name=item['name'],va=item['va'],
                              equal=p.read(int(item['va'],16),len(expected))==expected))
        details=report.get('ui_detail_corrections',{})
        for i,item in enumerate(details.get('instruction_words',())):
            expected=int(item['new'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'ui_detail_instruction_{i}',va=item['va'],
                              equal=p.read(int(item['va'],16),4)==expected))
        for i,item in enumerate(details.get('data_references',())):
            expected=int(item['target'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'ui_detail_reference_{i}',va=item['site'],
                              equal=p.read(int(item['site'],16),4)==expected))
        roster=report.get('roster_system_corrections',{})
        for i,item in enumerate(roster.get('instruction_words',())):
            expected=int(item['new'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'roster_system_instruction_{i}',va=item['va'],
                              equal=p.read(int(item['va'],16),4)==expected))
        for i,item in enumerate(roster.get('data_references',())):
            expected=int(item['target'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'roster_system_reference_{i}',va=item['site'],
                              equal=p.read(int(item['site'],16),4)==expected))
        expected=elf[offset:offset+size]
        setup=report.get('setup_save_corrections',{})
        for i,item in enumerate(setup.get('instruction_words',())):
            expected_word=int(item['new'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'setup_save_instruction_{i}',va=item['va'],
                              equal=p.read(int(item['va'],16),4)==expected_word))
        for i,item in enumerate(setup.get('data_references',())):
            expected_word=int(item['target'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'setup_save_reference_{i}',va=item['site'],
                              equal=p.read(int(item['site'],16),4)==expected_word))
        state_offset=int(patch['state_va'],16)-va
        weapon=report.get('weapon_battle_corrections',{})
        for i,item in enumerate(weapon.get('instruction_words',())):
            value=int(item['new'],16).to_bytes(4,'little')
            hooks.append(dict(name=f'weapon_battle_instruction_{i}',va=item['va'],equal=p.read(int(item['va'],16),4)==value))
        for i,item in enumerate(weapon.get('storage',())):
            value=bytes.fromhex(item['new'])
            hooks.append(dict(name=f'weapon_battle_storage_{i}',va=item['va'],equal=p.read(int(item['va'],16),len(value))==value))
        favorites=report.get('favorites',{})
        for i,item in enumerate(favorites.get('instruction_words',())):
            value=bytes.fromhex(item['new'])
            hooks.append(dict(name=f'favorites_instruction_{i}',va=item['va'],equal=p.read(int(item['va'],16),len(value))==value))
        assert 0<=state_offset<=size-8
        # Glyph selection and square-cell size are live renderer state.
        # Compare every immutable byte even after a dialogue has been drawn.
        mutable=[(state_offset,8)]
        if favorites:
            mutable.append((int(favorites['state_va'],16)-va,20))
            mutable.append((int(report['difficulty']['mode_va'],16)-va,4))
        last=0;immutable_equal=True
        for start,length in sorted(mutable):
            assert last<=start and start+length<=size
            immutable_equal &= ram[last:start]==expected[last:start]
            last=start+length
        immutable_equal &= ram[last:]==expected[last:]
        runtime=dict(version=version,platform='PS2',emulator=p.string(8),
                     boot_source=report['output'],iso_sha256=report['target_sha256'],
                     elf_sha256=patch['target_sha256'],game_id=p.string(12),
                     status=p.status(),segment_equal=ram==expected,
                     immutable_segment_equal=immutable_equal,
                     mutable_state_excluded=dict(va=patch['state_va'],bytes=8,
                                                current_bytes=ram[state_offset:state_offset+8].hex()),
                     segment_bytes=size,segment_ram_sha256=hashlib.sha256(ram).hexdigest(),
                     mutable_ranges=[dict(va=hex(va+a),bytes=n,current_bytes=ram[a:a+n].hex()) for a,n in sorted(mutable)],
                     hook_checks=hooks,pine_port=port,texture_replacement=False,
                     pcsx2_render_scale=settings.getfloat('EmuCore/GS','upscale_multiplier'),
                     profile=str(profile.resolve()),visual_validation='pending',
                     physical_ps2_validation='pending')
        if patch.get('ps2_script_tables_updated'):
            for label,offset,length in [('script_sector_table_equal',0x381f40,193*4),
                                         ('map_section_table_equal',0x37e438,18*4)]:
                runtime[label]=p.read(offset+FILE_BIAS,length)==elf[offset:offset+length]
                assert runtime[label],label
    assert runtime['game_id']=='SLPS-25345' and runtime['status']==0
    assert runtime['immutable_segment_equal'] and all(x['equal'] for x in hooks)
    log=(profile/'logs/emulog.txt').read_text(errors='replace')
    runtime['opening_fmv_observed_in_log']='FMV started' in log
    runtime['unknown_cpu_opcode_warnings']=log.count('Unrecognized FPU/COP1')+log.count('Unknown R5900')
    assert runtime['unknown_cpu_opcode_warnings']==0
    runtime['tlb_miss_warnings']=log.count('TLB Miss')
    if version in ('0.1.3','0.1.4','0.1.5'):assert runtime['tlb_miss_warnings']==0
    output=ROOT/'work/output'/('ps2_font_'+version+'_runtime.json')
    if output.exists():
        previous=json.loads(output.read_text(encoding='utf8'))
        if previous.get('iso_sha256')==runtime['iso_sha256'] and previous.get('elf_sha256')==runtime['elf_sha256']:
            for key in ('visual_validation','ui_visual_validation','visual_checks','visual_evidence','visual_blocker'):
                if key in previous:runtime[key]=previous[key]
    output.write_text(json.dumps(runtime,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in runtime.items() if k!='hook_checks'},indent=2))
    return runtime


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('version');p.add_argument('--port',required=True,type=int)
    p.add_argument('--profile',required=True,type=Path)
    a=p.parse_args();verify_runtime(a.version,a.port,a.profile)
