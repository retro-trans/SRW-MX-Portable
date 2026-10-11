"""Translate the native battle HUD atlas caption on PSP and PS2."""
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    'PSP': dict(palette=0xf4000, pixels=0xf4400, size=(512, 512), box=(8, 304, 120, 328)),
    'PS2': dict(palette=0x134400, pixels=0x134800, size=(1024, 256), box=(424, 48, 536, 72)),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def palette(data, platform):
    off = SPECS[platform]['palette']
    raw = data[off:off+1024]
    # Native PS2 CSM1 exchanges CLUT address bits 3 and 4.
    indexes = [(v & ~24) | ((v & 8) << 1) | ((v & 16) >> 1) for v in range(256)] if platform == 'PS2' else range(256)
    return [tuple(raw[i*4:i*4+3]) + (min(255, raw[i*4+3]*2),) for i in indexes]


def caption(data, platform):
    s = SPECS[platform]; w, h = s['size']; off = s['pixels']
    indexes = Image.frombytes('L', (w, h), bytes(data[off:off+w*h])).crop(s['box'])
    pal = palette(data, platform)
    pic = Image.new('RGBA', indexes.size)
    pic.putdata([pal[v] for v in indexes.tobytes()])
    return pic, indexes


def render(pal):
    scale = 4
    font = ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf', 24*scale)
    font.set_variation_by_name(b'Regular')
    box = font.getbbox('AT Field')
    mask = Image.new('L', (box[2]-box[0], box[3]-box[1]))
    ImageDraw.Draw(mask).text((-box[0], -box[1]), 'AT Field', font=font, fill=255)
    mask = mask.resize((round(mask.width*18/mask.height), 18), Image.Resampling.LANCZOS)
    assert mask.width <= 108
    ink = Image.new('L', (112, 24))
    ink.paste(mask, ((112-mask.width)//2, 3))
    art = Image.new('RGBA', ink.size)
    outline = ink.filter(ImageFilter.MaxFilter(3))
    art.paste((0, 0, 0, 255), (0, 0, 112, 24), outline)
    shadow = Image.new('L', ink.size); shadow.paste(ink, (1, 1))
    art.paste((0, 0, 255, 255), (0, 0, 112, 24), shadow)
    art.paste((255, 255, 255, 255), (0, 0, 112, 24), ink)
    cache = {}
    def closest(c):
        if c not in cache:
            cache[c] = min(range(256), key=lambda i: sum((pal[i][j]-c[j])**2 for j in range(4)))
        return cache[c]
    return bytes(closest(c) for c in art.getdata()), dict(font='Bahnschrift Regular', cap_height=18,
        body_bounds=list(ink.getbbox()), horizontal_rescaling=False, text='AT Field')


def patch(data, platform):
    s = SPECS[platform]; w, _ = s['size']; x0, y0, x1, y1 = s['box']
    original = (ROOT/('work/build/STATIC2_ADD.orig' if platform == 'PSP' else 'work/source/ps2/STATIC.BIN')).read_bytes()
    before, indexes = caption(data, platform)
    _, native = caption(original, platform)
    new, layout = render(palette(data, platform))
    if indexes.tobytes() == new:
        restored = bytearray(data)
        source_pixels = native.tobytes()
        for row, y in enumerate(range(y0, y1)):
            a = s['pixels']+y*w+x0
            restored[a:a+112] = source_pixels[row*112:(row+1)*112]
        target, report = patch(restored, platform)
        assert target == data
        return bytes(data), {**report, 'already_translated': True}
    assert indexes.tobytes() == native.tobytes(), 'Unexpected source caption; preserve unknown artwork'
    out = bytearray(data); ranges = []
    for row, y in enumerate(range(y0, y1)):
        a = s['pixels'] + y*w + x0; z = a+x1-x0
        out[a:z] = new[row*112:(row+1)*112]; ranges.append([a, z])
    last = 0
    for a, z in ranges:
        assert out[last:a] == data[last:a]; last = z
    assert out[last:] == data[last:] and len(out) == len(data)
    after, target = caption(out, platform)
    assert target.tobytes() == new
    return bytes(out), dict(platform=platform, english='AT Field', palette_offset=hex(s['palette']),
        pixel_offset=hex(s['pixels']), atlas_size=list(s['size']), source_rectangle=list(s['box']),
        pixel_ranges=ranges, source_caption_sha256=sha(indexes.tobytes()), target_caption_sha256=sha(new),
        source_resource_sha256=sha(data), target_resource_sha256=sha(out), palette_preserved=True,
        other_pixels_and_data_preserved=True, layout=layout, in_game_visual_validation='pending')
