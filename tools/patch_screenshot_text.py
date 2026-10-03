"""Incrementally patch the requested save-message line and stage 1 Super title card.

Usage: py -3 -X utf8 tools/patch_screenshot_text.py <base ISO> <version>
Preserves the base build's fonts, code, campaign dialogue, UI and battle quotes.
The title bitmap is a native game asset; no emulator texture replacement is used.
"""
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys

from PIL import Image, ImageDraw, ImageFont
import pycdlib
import build_patch
import make_latin_font
import textfit

ROOT = Path(__file__).resolve().parents[1]
CARD_HASH = '3210d1e3571d759e7935ef33590c3e76e330177796b4acd0feb74fc8ecaaee19'


def card_patch(data, preview_dir):
    spec = json.loads((ROOT/'work/translation/en/ui/chapter_cards.json').read_text(encoding='utf8'))['1_super']
    offset = spec['pixel_offset']
    width, height = spec['texture_width'], spec['texture_height']
    original = data[offset:offset+width*height]
    assert hashlib.sha256(original).hexdigest() == CARD_HASH, 'Unexpected title atlas: use the unmodified base asset.'
    original_image = Image.frombytes('L', (width, height), original)
    before = original_image.copy()
    x0, y0, x1, y1 = spec['title_rectangle']
    # Rasterize at 4x and filter down to the native bitmap's existing slot.
    scale = 4
    font = ImageFont.truetype(make_latin_font.FONT, spec['font_size']*scale)
    temporary = Image.new('L', (2048, 256))
    ImageDraw.Draw(temporary).text((8, 8), spec['en'], font=font, fill=255)
    bounds = temporary.getbbox()
    assert bounds and bounds[2] < temporary.width and bounds[3] < temporary.height
    ink = temporary.crop(bounds)
    ink = ink.resize((round(ink.width/scale), round(ink.height/scale)), Image.Resampling.LANCZOS)
    assert ink.width <= x1-x0-8 and ink.height <= y1-y0-4, 'Title does not fit.'
    ImageDraw.Draw(original_image).rectangle((x0,y0,x1-1,y1-1), fill=0)
    original_image.paste(ink, (x0+(x1-x0-ink.width)//2, y0+(y1-y0-ink.height)//2))
    patched = original_image.tobytes()
    assert patched[(y1*width):] == original[(y1*width):], 'Another atlas region was modified.'
    result = bytearray(data)
    result[offset:offset+len(patched)] = patched
    assert len(result) == len(data)
    assert result[:offset] == data[:offset] and result[offset+width*height:] == data[offset+width*height:]
    preview_dir.mkdir(parents=True, exist_ok=True)
    before.save(preview_dir/'chapter_card_atlas_before.png')
    original_image.save(preview_dir/'chapter_card_atlas_after.png')
    return bytes(result), spec


def dialogue_patch(map_data, boot):
    english = json.loads((ROOT/'work/translation/en/script/save_message_kaine_merged.en.json').read_text(encoding='utf8'))['rows'][0]
    base = build_patch.SCRIPT_SECTOR*2048
    oldtab = struct.unpack_from('<204I', boot, build_patch.BLOCK_TABLE)
    offset = base+oldtab[2]*2048
    count, table = struct.unpack_from('<2I', map_data, offset+8)
    pointers = struct.unpack_from('<%dI'%count, map_data, offset+table)
    source = []
    for i in (21,26,31):
        start = offset+pointers[i]
        source.append(map_data[start:map_data.index(b'\0',start)].decode('cp932'))
    assert source[0] == source[1] == source[2], 'Kaine line indices no longer agree.'
    _, lines, fits = textfit.fit_dialogue(english['speaker_en'], english['en'])
    assert fits
    # Read Japanese from the user's base ISO; source script stays out of committed tools.
    result, newboot = build_patch.patch_map_add(map_data, boot, {'end_mes': {source[0]: '@'.join(lines)}})
    newtab = struct.unpack_from('<204I', newboot, build_patch.BLOCK_TABLE)
    changed = [i for i in range(203) if
               map_data[base+oldtab[i]*2048:base+oldtab[i+1]*2048] !=
               result[base+newtab[i]*2048:base+newtab[i+1]*2048]]
    assert changed == [2], changed
    assert result[:base] == map_data[:base]
    assert result[base+newtab[-1]*2048:] == map_data[base+oldtab[-1]*2048:]
    # Every replacement must decode to the exact wrapped translation.
    new_offset = base+newtab[2]*2048
    new_table = struct.unpack_from('<I', result, new_offset+12)[0]
    for i in (21,26,31):
        start = new_offset+struct.unpack_from('<I',result,new_offset+new_table+4*i)[0]
        assert result[start:result.index(b'\0',start)] == textfit.encode('@'.join(lines))
    return result, newboot, lines


def main(base_iso, version):
    source = Path(base_iso).resolve()
    output = ROOT/'work/output'/('SRWMX_EN_%s.iso'%version)
    assert output != source
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    boot = build_patch.iso_read(iso, '/PSP_GAME/SYSDIR/BOOT.BIN')
    assert boot == build_patch.iso_read(iso, '/PSP_GAME/SYSDIR/EBOOT.BIN')
    map_data = build_patch.iso_read(iso, '/PSP_GAME/USRDIR/MAP_ADD.BIN')
    pack = build_patch.iso_read(iso, '/PSP_GAME/USRDIR/PACKMAPC2_ADD.BIN')
    newmap, newboot, lines = dialogue_patch(map_data,boot)
    newpack, spec = card_patch(pack, ROOT/'work/ui')
    replacements = {'/PSP_GAME/SYSDIR/BOOT.BIN':newboot, '/PSP_GAME/SYSDIR/EBOOT.BIN':newboot,
                    '/PSP_GAME/USRDIR/MAP_ADD.BIN':newmap, '/PSP_GAME/USRDIR/PACKMAPC2_ADD.BIN':newpack}
    for name, data in replacements.items():
        iso.rm_file(iso_path=name)
        iso.add_fp(io.BytesIO(data),len(data),iso_path=name)
    output.parent.mkdir(parents=True,exist_ok=True)
    iso.write(str(output));iso.close()
    # Reopen the finished ISO to ensure the written files match the prepared patch.
    verify = pycdlib.PyCdlib();verify.open(str(output))
    for name,data in replacements.items():
        assert build_patch.iso_read(verify,name)==data, name
    verify.close()
    license_source = source.with_name(source.stem+'_FONT_LICENSE.txt')
    if license_source.exists(): shutil.copyfile(license_source, output.with_name(output.stem+'_FONT_LICENSE.txt'))
    report = dict(version=version,base_build=source.name,dialogue_uses=['end_mes:21','end_mes:26','end_mes:31'],
                  dialogue_lines=lines,unchanged_script_blocks=202,title=spec['en'],
                  title_bitmap_offset=spec['pixel_offset'],changed_atlas_rectangle=spec['title_rectangle'],
                  native_asset_patch=True,texture_replacement=False,
                  file_hashes={name:hashlib.sha256(data).hexdigest() for name,data in replacements.items()})
    (output.parent/('screenshot_text_%s_verification.json'%version)).write_text(json.dumps(report,indent=1),encoding='utf8')
    print('Written and verified:',output)


if __name__=='__main__': main(*sys.argv[1:])
