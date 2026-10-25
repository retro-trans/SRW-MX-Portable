"""Run the post-v0.4.38 fixes against the actual current release executables."""
import copy
import json
import struct
from pathlib import Path
import pycdlib
from verify_ps2_rename import verify as rename
from verify_ps2_turn_funds import verify as money
from verify_ps2_stage30_transition import verify as transition
from verify_ps2_objective_footer import verify as footer
from verify_psp_dendoh_popup import verify as dendoh

ROOT=Path(__file__).resolve().parents[1]


def main(version='0.4.47'):
    aggregate=json.loads((ROOT/f'work/output/ps2_font_{version}_verification.json').read_text(encoding='utf8'))
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/f'work/output/SRWMX_PS2_EN_{version}.iso'))
    with iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as stream:elf=stream.read()
    with iso.open_file_from_iso(iso_path='/DATA/STAGE.BIN;1') as stream:stage=stream.read()
    meta,info=aggregate['font'],aggregate['stage30']
    off=lambda va:int(meta['segment_offset'],16)+int(va,16)-int(meta['segment_va'],16)
    rel=struct.unpack_from('<204I',elf,off(info['script_sector_table_va']))
    names=[]
    for va in struct.unpack_from('<203I',elf,off(info['script_name_table_va'])):
        a=off(hex(va));names.append(elf[a:elf.index(0,a)].decode('ascii'))
    n=names.index('i056a');start=struct.unpack_from('<18I',elf,0x37e438)[10]
    with iso.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
        stream.seek((start+rel[n])*2048);closing=stream.read((rel[n+1]-rel[n])*2048)
    iso.close()
    def old(v):return (ROOT/f'work/build/ps2/font_{v}/SLPS_253.45').read_bytes()
    checks={}
    for name,fn,v in [('ps2_rename',rename,'0.4.41'),('ps2_turn_funds',money,'0.4.43'),
                       ('ps2_objective_footer',footer,'0.4.45')]:
        checks[name]=fn(old(v),elf,copy.deepcopy(meta));assert checks[name]['passed']
        print('Current executable regression passed:',name,flush=True)
    checks['ps2_transition']=transition(old('0.4.44'),elf,copy.deepcopy(meta),stage,closing)
    assert checks['ps2_transition']['passed']
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/f'work/output/SRWMX_EN_{version}.iso'))
    with iso.open_file_from_iso(iso_path='/PSP_GAME/SYSDIR/BOOT.BIN') as stream:boot=stream.read()
    iso.close()
    checks['psp_dendoh']=dendoh((ROOT/'work/build/psp/sortie_popup_audit/BOOT.BIN').read_bytes(),boot)
    assert checks['psp_dendoh']['passed']
    report=dict(version=version,passed=True,actual_current_iso_executables_used=True,checks=checks,
        user_confirmed_prior_ps2_fixes=dict(chapter30_transition='Earth Chapter31 reached; user confirmed working',
            objective_footer='User confirmed v0.4.46 works great'),
        new_branding_live_playback='pending')
    (ROOT/f'work/output/release_{version}_native_regressions.json').write_text(json.dumps(report,indent=2)+'\n')
    print('All additional release regressions passed',flush=True)
    return report


if __name__=='__main__':
    import sys
    main(*sys.argv[1:2])
