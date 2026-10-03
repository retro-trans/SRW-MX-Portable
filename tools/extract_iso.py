"""Extract the files the tools need from the original ISO into work/build/iso/ (git-ignored).

usage: python extract_iso.py "<Super Robot Taisen MX Portable (Japan).iso>" [out dir]
Writes BOOT.BIN, MAP_ADD.BIN, STATIC2_ADD.BIN (and WND.BIN, OPWND.BIN for the UI textures).
"""
import os, sys
import pycdlib

FILES = {'/PSP_GAME/SYSDIR/BOOT.BIN': 'BOOT.BIN', '/PSP_GAME/USRDIR/MAP_ADD.BIN': 'MAP_ADD.BIN',
         '/PSP_GAME/USRDIR/STATIC2_ADD.BIN': 'STATIC2_ADD.BIN', '/PSP_GAME/USRDIR/WND.BIN': 'WND.BIN',
         '/PSP_GAME/USRDIR/OPWND.BIN': 'OPWND.BIN'}


def main(iso_path, out=None):
    out = out or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'build', 'iso')
    os.makedirs(out, exist_ok=True)
    iso = pycdlib.PyCdlib()
    iso.open(iso_path)
    for src, name in FILES.items():
        iso.get_file_from_iso(os.path.join(out, name), iso_path=src)
        print(name, os.path.getsize(os.path.join(out, name)))
    iso.close()


if __name__ == '__main__':
    main(*sys.argv[1:3])
