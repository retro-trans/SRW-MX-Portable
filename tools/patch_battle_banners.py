"""Translate registered native battle-animation captions in the shared HUD atlas.

These blue/white captions are separate from the TX48/P2IG map banners.
Only their indexed pixel rectangles change; their existing CLUT is retained.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from patch_at_field import ROOT, SPECS, palette, sha
from patch_battle_hud import picture, render

TERMS = ROOT/'work/translation/en/ui/battle_banners.en.json'


def patch(data, platform, preview=None, region_ids=None):
    spec = SPECS[platform]
    width, height = spec['size']
    pixels = spec['pixels']
    native_path = ROOT/('work/build/STATIC2_ADD.orig' if platform == 'PSP'
                        else 'work/source/ps2/STATIC.BIN')
    native = native_path.read_bytes()
    assert data[spec['palette']:spec['palette']+1024] == native[spec['palette']:spec['palette']+1024]
    pal = palette(data, platform)
    rows = json.loads(TERMS.read_text(encoding='utf-8'))['regions']
    if region_ids is not None:
        requested=set(region_ids)
        assert requested and requested<={row['id'] for row in rows},'Unknown recorded caption IDs'
        rows=[row for row in rows if row['id'] in requested]
    output = bytearray(data)
    ranges, records = [], []
    for row in rows:
        x0, y0, x1, y1 = row['box']
        assert 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
        def crop(resource):
            return b''.join(resource[pixels+y*width+x0:pixels+y*width+x1]
                            for y in range(y0, y1))
        before, original = crop(data), crop(native)
        if row['id']=='god_shadow':
            assert not any(pal[v][0]>2*max(pal[v][1],pal[v][2]) for v in original), \
                'God Shadow rectangle includes the adjacent red EN label'
        translated, layout = render(original, pal, row)
        assert before in (original, translated), 'Unknown caption artwork: '+row['id']
        stride = x1-x0
        for i, y in enumerate(range(y0, y1)):
            start = pixels+y*width+x0
            output[start:start+stride] = translated[i*stride:(i+1)*stride]
            ranges.append([start, start+stride])
        records.append(dict(**row, **layout, source_pixel_sha256=sha(original),
                            target_pixel_sha256=sha(translated), already_translated=before==translated))
    last = 0
    for start, end in sorted(ranges):
        assert output[last:start] == data[last:start]
        last = end
    assert output[last:] == data[last:] and len(output) == len(data)
    evidence = dict(platform=platform, regions=records, pixel_ranges=sorted(ranges),
                    source_resource_sha256=sha(data), target_resource_sha256=sha(output),
                    palette_preserved=True, all_other_pixels_and_bytes_preserved=True)
    if preview:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        column_width = max(row['box'][2]-row['box'][0] for row in rows)*4+16
        sheet = Image.new('RGB', (column_width*2, 36+len(rows)*112), (35, 35, 45))
        draw = ImageDraw.Draw(sheet)
        for column, label, raw in [(0, 'Before', data), (column_width, 'English', output)]:
            draw.text((column+8, 8), label, fill='white')
            for i, row in enumerate(rows):
                image = picture(raw, platform).crop(row['box'])
                bg = Image.new('RGBA', image.size, (35, 35, 45, 255))
                bg.alpha_composite(image)
                sheet.paste(bg.convert('RGB').resize((image.width*4, image.height*4), Image.Resampling.NEAREST),
                            (column+8, 34+i*112))
                draw.text((column+8, 132+i*112), row['english'], fill='white')
        sheet.save(preview/'before_after.png')
        (preview/'layout.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
    return bytes(output), evidence


def verify_iso(path, platform):
    """Reject a release that still contains the Japanese animation artwork."""
    import pycdlib
    asset = '/PSP_GAME/USRDIR/STATIC2_ADD.BIN' if platform == 'PSP' else '/DATA/STATIC.BIN;1'
    iso = pycdlib.PyCdlib()
    iso.open(str(path))
    try:
        with iso.open_file_from_iso(iso_path=asset) as stream:
            raw = stream.read()
        expected, report = patch(raw, platform)
        assert raw == expected, 'Untranslated native battle-animation captions: '+platform
        assert all(row['already_translated'] for row in report['regions'])
        return dict(platform=platform, native_iso_caption_artwork_verified=True,
                    resource_sha256=sha(raw), captions=[row['text'] for row in report['regions']])
    finally:
        iso.close()
