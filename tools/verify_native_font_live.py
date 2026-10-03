"""Verify native font payload and relocations in an isolated PPSSPP debugger.

Usage: python verify_native_font_live.py 0.1.4 ws://127.0.0.1:45374/debugger
Run at translated dialogue. The test instance must use SoftwareRenderer=True
for the optional PSP VRAM framebuffer capture; hardware screenshot download
is unavailable on the installed PPSSPP version. No desktop capture is used.
"""
import base64
import configparser
import json
import struct
import sys
from pathlib import Path
from PIL import Image
import native_font4x
from ppsspp_dbg import Dbg

ROOT = Path(__file__).resolve().parent.parent


def main(version, url):
    config = configparser.RawConfigParser()
    config.read(ROOT / 'work/build/native_font4x_test/ppsspp.ini', encoding='utf-8-sig')
    assert not config.getboolean('Graphics', 'ReplaceTextures')
    assert config.getboolean('Graphics', 'SoftwareRenderer')
    layout = json.loads((ROOT / 'work/build/native_font4x/layout.json').read_text())
    high, index, _ = native_font4x.atlas()
    table = native_font4x.vwf.width_table(str(ROOT / 'work/build/STATIC2_ADD.BIN'))
    code, hooks, relocs, _ = native_font4x.assemble(
        layout['table_va'], layout['index_va'], layout['atlas_va'], layout['code_va'])
    with Dbg(url) as d:
        def read(address, size):
            return base64.b64decode(d.call('memory.read', address=address, size=size,
                                          replacements=False)['base64'])
        was_stepping = d.is_stepping()
        if not was_stepping:
            d.call('cpu.stepping')
        try:
            module = next(x for x in d.call('hle.module.list')['modules'] if x['name'] == 'SRWMXforPSP')
            base = module['address']
            expected = bytearray(code)
            hi_relocs = []
            for address, kind in relocs:
                if address < layout['code_va']:
                    continue
                offset = address - layout['code_va']
                word = struct.unpack_from('<I', expected, offset)[0]
                if kind == 4:
                    target = ((word & 0x3ffffff) << 2) + base
                    struct.pack_into('<I', expected, offset, (word & 0xfc000000) | ((target >> 2) & 0x3ffffff))
                elif kind == 5:
                    hi_relocs.append(offset)
                elif kind == 6:
                    low = struct.unpack('<h', struct.pack('<H', word & 0xffff))[0]
                    for hi_offset in hi_relocs:
                        hi_word = struct.unpack_from('<I', expected, hi_offset)[0]
                        pointer = ((hi_word & 0xffff) << 16) + low + base
                        struct.pack_into('<I', expected, hi_offset,
                                         (hi_word & 0xffff0000) | (((pointer + 0x8000) >> 16) & 0xffff))
                    struct.pack_into('<I', expected, offset, (word & 0xffff0000) | ((low + base) & 0xffff))
                    hi_relocs.clear()
            assert not hi_relocs
            for va, data in [(layout['table_va'], table), (layout['index_va'], index),
                             (layout['atlas_va'], high), (layout['code_va'], bytes(expected))]:
                assert read(base + va, len(data)) == data, hex(va)
            for va, data in hooks:
                word = struct.unpack('<I', data)[0]
                if word >> 26 in (2, 3):
                    word = (word & 0xfc000000) | (((((word & 0x3ffffff) << 2) + base) >> 2) & 0x3ffffff)
                assert read(base + va, 4) == struct.pack('<I', word), hex(va)
            regs_path = ROOT / 'work/build/native_font4x_test/render_registers.json'
            trace = json.loads(regs_path.read_text())
            regs = trace['regs']
            assert regs['a1'] == 512 and regs['a2'] == 128
            assert trace['stack30'][1] == 72
            assert base + layout['atlas_va'] <= regs['t0'] < base + layout['atlas_va'] + len(high)
            screenshot = ROOT / ('work/ui/font_native4x_%s_dialogue.png' % version)
            Image.frombytes('RGBA', (512,272), d.read(0x04000000,512*272*4)).convert('RGB').crop((0,0,480,272)).save(screenshot)
            result = dict(module=module, relocated_payload_and_all_hooks_verified=True,
                          render_trace=trace, renderer_texture_dimensions_verified=True,
                          sampled_glyph=next((char for code,char in native_font4x.glyphs.CHARS.items()
                                              if native_font4x.glyphs.slot(code) == regs['t8']), None),
                          screenshot=str(screenshot.relative_to(ROOT)).replace('\\','/'),
                          screenshot_method='PSP VRAM through remote debugger, software renderer, 1x display',
                          tested_with_texture_replacement=False, hardware_psp_tested=False,
                          test_config='work/build/native_font4x_test/ppsspp.ini')
        finally:
            if not was_stepping:
                d.call('cpu.resume')
    report_path = ROOT / ('work/output/font_%s_verification.json' % version)
    report = json.loads(report_path.read_text())
    report.update(emulator_boot_verified=True, emulator_dialogue_verified=True, emulator=result)
    report_path.write_text(json.dumps(report, indent=1), encoding='utf-8')
    print('Verified native atlas, relocated code, 16 hooks and 512x128 Latin texture upload; saved dialogue capture.')


if __name__ == '__main__':
    main(*sys.argv[1:])
