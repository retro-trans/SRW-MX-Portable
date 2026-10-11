"""Read back library code and the loaded FIX00 in an isolated emulator only."""
import argparse, configparser, struct
from pathlib import Path
from pcsx2_pine import Pine
from port_ps2_translations import ROOT, read_json, sha
from port_ps2_prologue import save
from static2_extract import sections

def verify(base,version,port,profile):
    settings=configparser.ConfigParser(interpolation=None,strict=False)
    settings.read(profile/'inis/PCSX2.ini',encoding='utf-8-sig')
    assert settings.getboolean('EmuCore','EnablePINE') and settings.getint('EmuCore','PINESlot')==port
    assert 'ps2_library_test_' in str(profile.resolve())
    boot=read_json(ROOT/'work/output'/f'ps2_font_{version}_runtime.json')
    report=read_json(base/'library.json');fix=(base/'FIX00.DAT').read_bytes()
    assert boot['elf_sha256']==report['target_elf_sha256'] and boot['immutable_segment_equal']
    with Pine(port) as p:
        assert p.string(12)=='SLPS-25345' and p.status()==0
        words=[]
        for row in report['instruction_words']:
            expected=bytes.fromhex(row['after']);actual=p.read(int(row['va'],16),len(expected))
            assert expected==actual,row
            words.append(dict(va=row['va'],purpose=row['purpose'],equal=True))
        manager=struct.unpack('<I',p.read(0x3c8cac,4))[0]
        assert 0x800000<=manager<0x2000000,hex(manager)
        sent=struct.unpack('<I',p.read(manager+0x18c,4))[0]
        address=sent-sections(fix,0)['Sent'][0]
        assert 0x800000<=address<0x2000000-len(fix),(hex(address),hex(sent))
        actual=p.read(address,len(fix));assert sha(actual)==sha(fix),'Loaded database differs'
    result=dict(version=version,passed=True,pine_port=port,profile=str(profile.resolve()),
        library_executable_words=words,loaded_fix_va=hex(address),fix_bytes=len(fix),
        loaded_fix_sha256=sha(actual),target_fix_sha256=report['target_fix_sha256'],
        iso_sha256=boot['iso_sha256'],elf_sha256=boot['elf_sha256'],
        immutable_text_segment_equal=True,loaded_database_exact=True,
        library_visual_validation='pending',physical_ps2_validation='pending')
    save(ROOT/'work/output'/f'ps2_library_{version}_runtime.json',result)
    print('Runtime library code and FIX00 match: '+str(len(words))+' words, '+str(len(fix))+' bytes.')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('version');parser.add_argument('--base',type=Path,required=True);parser.add_argument('--port',type=int,required=True);parser.add_argument('--profile',type=Path,required=True);args=parser.parse_args()
    verify(args.base,args.version,args.port,args.profile)
