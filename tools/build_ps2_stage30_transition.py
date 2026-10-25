"""Build the PS2 chapter-30 completion and saved-state recovery correction."""
import struct
import pycdlib
from build_ps2_turn_funds import ROOT,read,build
from fix_ps2_stage30_transition import patch
from verify_ps2_stage30_transition import verify


def main():
    previous=read(ROOT/'work/output/ps2_font_0.4.44_verification.json')
    reference=read(ROOT/'work/output/ps2_font_0.4.38_verification.json')
    for path in ('/DATA/STAGE.BIN;1','/DATA/MAP.BIN;1'):
        get=lambda r:next(f['target_sha256'] for f in r['files'] if f['path']==path)
        assert get(previous)==get(reference)
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/'work/output/SRWMX_PS2_EN_0.4.44.iso'))
    with iso.open_file_from_iso(iso_path='/DATA/STAGE.BIN;1') as stream:stage=stream.read()
    with iso.open_file_from_iso(iso_path='/SLPS_253.45;1') as stream:elf=stream.read()
    meta,info=previous['font'],previous['stage30']
    off=lambda va:int(meta['segment_offset'],16)+int(va,16)-int(meta['segment_va'],16)
    rel=struct.unpack_from('<204I',elf,off(info['script_sector_table_va']))
    names=[]
    for va in struct.unpack_from('<203I',elf,off(info['script_name_table_va'])):
        a=off(hex(va));names.append(elf[a:elf.index(0,a)].decode('ascii'))
    n=names.index('i056a');start=struct.unpack_from('<18I',elf,0x37e438)[10]
    with iso.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
        stream.seek((start+rel[n])*2048);closing=stream.read((rel[n+1]-rel[n])*2048)
    iso.close()
    build('0.4.45','0.4.44','stage30_transition',patch,
          lambda original,changed,font:verify(original,changed,font,stage,closing))


if __name__=='__main__':main()
