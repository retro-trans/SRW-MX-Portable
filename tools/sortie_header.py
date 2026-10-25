"""Translate only the native Sortie Prep header's flat text rectangle."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
import redraw_wnd as wnd

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {'PSP': '/PSP_GAME/USRDIR/WND.BIN', 'PS2': '/DATA/WND.BIN;1'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def texture(data, platform):
    if platform == 'PSP':
        off = wnd.textures(data)[39]
        return off, data[off:], None
    from ps2_graphics_port import p2ig_textures, fake_tx48
    row = next(r for r in p2ig_textures(data) if r['name'] == 'IM_W10')
    assert row['psm'] == 19
    return row['offset'], fake_tx48(data, row), row


def patch(data, platform, preview=None):
    entry = json.loads((ROOT/'work/translation/en/ui/textures.json').read_text(encoding='utf8'))['WND.BIN']['39']
    if platform == 'PS2':
        entry = dict(entry, native_text_box=[20,4,194,32],
                     native_text_origin=[26,6], native_cap_height=22)
    native_path = ROOT/('work/build/iso/WND.BIN' if platform == 'PSP' else 'work/source/ps2/WND.BIN')
    native = native_path.read_bytes()
    off, fake, row = texture(data, platform)
    old_off, original, old_row = texture(native, platform)
    assert off == old_off and row == old_row
    pal, (kind,w,h,px) = wnd.palette(fake, 0)
    native_pal, layout = wnd.palette(original, 0)
    assert kind == 1 and pal == native_pal and layout == (kind,w,h,px)
    pixels = fake[px:px+w*h]
    original_pixels = original[px:px+w*h]
    expected, _, _ = wnd.redraw_header(original, 0, entry)
    x0,y0,x1,y1 = entry['native_text_box']
    crop = lambda raw: b''.join(raw[y*w+x0:y*w+x1] for y in range(y0,y1))
    before, source, after = crop(pixels), crop(original_pixels), crop(expected)
    assert before in (source, after), 'Unrecognized Sortie Prep header artwork'
    mask = wnd.render_text(entry['en'], entry['native_cap_height'], 1000, wnd.HEADER_FONT)
    assert mask.width <= x1-entry['native_text_origin'][0]-2, 'Avoid horizontal text squeezing'
    start = off+(px if platform == 'PSP' else row['pixel_offset'])
    output = bytearray(data)
    ranges = []
    for y in range(y0,y1):
        a,z = start+y*w+x0, start+y*w+x1
        output[a:z] = expected[y*w+x0:y*w+x1]
        ranges.append([a,z])
    last = 0
    for a,z in ranges:
        assert output[last:a] == data[last:a]
        last = z
    assert output[last:] == data[last:] and len(output) == len(data)
    record = dict(id='sortie_prep', text=entry['en'], box=entry['native_text_box'],
        origin=entry['native_text_origin'], cap_height=entry['native_cap_height'],
        horizontal_rescaling=False, texture_offset=off, texture_dimensions=[w,h],
        source_pixel_sha256=sha(source), target_pixel_sha256=sha(after),
        already_translated=before == after)
    evidence = dict(platform=platform, regions=[record], pixel_ranges=ranges,
        source_resource_sha256=sha(data), target_resource_sha256=sha(output),
        palette_preserved=True, all_other_pixels_and_bytes_preserved=True)
    if preview:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        sheet = Image.new('RGB',(min(w,512)*2, h*4+32),(40,40,40))
        draw = ImageDraw.Draw(sheet)
        for i, (label, raw) in enumerate((('Before', pixels), ('English', bytes(output[start:start+w*h])))):
            pic = Image.new('RGBA',(w,h))
            pic.putdata([pal[v][:3]+(min(255,pal[v][3]*2),) for v in raw])
            bg = Image.new('RGBA',pic.size,(40,40,40,255))
            bg.alpha_composite(pic)
            draw.text((0,i*(h*2+16)),label,fill='white')
            sheet.paste(bg.convert('RGB').crop((0,0,min(w,512),h)).resize((min(w,512)*2,h*2)),(0,i*(h*2+16)+16))
        sheet.save(preview/'before_after.png')
        (preview/'layout.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
    return bytes(output), evidence


def verify_iso(path, platform):
    import pycdlib
    iso = pycdlib.PyCdlib()
    iso.open(str(path))
    try:
        with iso.open_file_from_iso(iso_path=ASSETS[platform]) as stream:
            raw = stream.read()
        expected, report = patch(raw, platform)
        assert expected == raw and report['regions'][0]['already_translated']
        return dict(platform=platform, native_iso_header_verified=True,
                    resource_sha256=sha(raw), text=report['regions'][0]['text'])
    finally:
        iso.close()
