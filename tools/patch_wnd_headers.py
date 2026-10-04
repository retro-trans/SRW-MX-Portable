"""Patch configured native WND headers in an existing ISO, preserving other assets.

Usage: python tools/patch_wnd_headers.py <base.iso> <new-version>
"""
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import pycdlib
from PIL import Image
import redraw_wnd

ROOT = Path(__file__).resolve().parent.parent
ASSET = '/PSP_GAME/USRDIR/WND.BIN'


def digest(stream):
    result = hashlib.sha256()
    while True:
        chunk = stream.read(4*1024*1024)
        if not chunk:
            return result.hexdigest()
        result.update(chunk)


def file_digest(iso, path):
    with iso.open_file_from_iso(iso_path=path) as stream:
        return digest(stream)


def patch_headers(data, preview=None):
    entries = json.loads((ROOT/'work/translation/en/ui/textures.json').read_text(encoding='utf-8'))['WND.BIN']
    out = bytearray(data)
    offsets = redraw_wnd.textures(data)
    results, allowed = [], set()
    previews = []
    for key, entry in sorted(entries.items(), key=lambda item: int(item[0])):
        if entry['kind'] != 'screen header' or 'native_text_box' not in entry:
            continue
        offset = offsets[int(key)]
        pixels, (t, w, h, start), palette = redraw_wnd.redraw_header(data, offset, entry)
        out[offset+start:offset+start+len(pixels)] = pixels
        x0, y0, x1, y1 = entry['native_text_box']
        allowed.update(offset+start+y*w+x for y in range(y0,y1) for x in range(x0,x1))
        results.append(dict(texture_index=int(key), en=entry['en'], texture_offset=offset,
                            text_box=entry['native_text_box'], text_origin=entry['native_text_origin'],
                            cap_height=entry['native_cap_height'], texture_dimensions=[w,h],
                            palette_preserved=True, background_and_decoration_preserved=True))
        if preview:
            im = Image.new('RGBA',(w,h))
            im.putdata([palette[i][:3]+(min(255,palette[i][3]*2),) for i in pixels])
            previews.append(im)
    assert results, 'No configured headers'
    changed = [i for i,(a,b) in enumerate(zip(data,out)) if a != b]
    assert changed and all(i in allowed for i in changed)
    assert len(out) == len(data)
    if preview:
        sheet = Image.new('RGBA',(512,len(previews)*36),(3,3,25,255))
        for n,im in enumerate(previews):
            sheet.alpha_composite(im,(0,n*36))
        sheet.convert('RGB').resize((1024,len(previews)*72),Image.NEAREST).save(str(preview))
    return bytes(out), results, len(changed)


def main(source, version):
    source = Path(source).resolve()
    output = ROOT/'work/output'/('SRWMX_EN_%s.iso'%version)
    if output.exists() or source == output.resolve():
        raise FileExistsError('Choose a new version/output; existing builds are preserved.')
    iso = pycdlib.PyCdlib()
    iso.open(str(source))
    stream = io.BytesIO()
    iso.get_file_from_iso_fp(stream,iso_path=ASSET)
    data = stream.getvalue()
    updated, headers, changed = patch_headers(data,ROOT/'work/ui'/('wnd_headers_%s_preview.png'%version))
    paths = [folder.rstrip('/')+'/'+str(name) for folder, _, files in iso.walk(iso_path='/') for name in files]
    before = {path:file_digest(iso,path) for path in paths if path != ASSET}
    iso.rm_file(iso_path=ASSET)
    iso.add_fp(io.BytesIO(updated),len(updated),iso_path=ASSET)
    iso.write(str(output))
    iso.close()
    check = pycdlib.PyCdlib()
    check.open(str(output))
    assert file_digest(check,ASSET) == hashlib.sha256(updated).hexdigest()
    for path,original in before.items():
        assert file_digest(check,path) == original,path
    check.close()
    license_path = source.with_name(source.stem+'_FONT_LICENSE.txt')
    if license_path.exists():
        shutil.copyfile(str(license_path),str(output.with_name(output.stem+'_FONT_LICENSE.txt')))
    with source.open('rb') as stream:
        source_sha = digest(stream)
    with output.open('rb') as stream:
        output_sha = digest(stream)
    report = dict(version=version,base_iso=source.name,base_sha256=source_sha,
                  output_iso=output.name,output_sha256=output_sha,local_build_only=True,
                  native_asset_patch=True,texture_replacement=False,headers=headers,
                  changed_pixel_bytes=changed,changed_iso_files=[ASSET],unchanged_iso_files=len(before),
                  unchanged_file_sha256=before,wnd_sha256=hashlib.sha256(updated).hexdigest(),
                  outside_header_text_boxes_preserved=True,iso_readback_verified=True,
                  in_game_verified=False)
    (output.parent/('wnd_headers_%s_verification.json'%version)).write_text(json.dumps(report,indent=1),encoding='utf-8')
    print('Written and verified:',output)
    print(len(headers),'headers;',len(before),'other ISO files unchanged; SHA-256',output_sha)


if __name__ == '__main__':
    main(*sys.argv[1:])
