"""Redraw the battle and status icons in WND.BIN with English (work/translation/en/ui/textures.json).

The icons are 8-bit TX48 textures (own 256-colour palette each, linear pixels):
- large battle icons (攻 反 援 同 戦 支 避 防): 28x28 square in a 32x32 texture, 2 px gold border,
  24x24 navy inside, yellow glyph with a black outline.
- small battle icons: 18x18 square, 14x14 inside, same style (a second set: 16x16, 1 px border).
- status icons (能 武 動 装 行 移, and HP which is already Latin): 15x15 brown square, grey glyph.
The frame is kept; the inside is refilled with its background colour and the English is drawn in the
icon's own palette: a body colour (the brightest glyph colour), a black or dark outline, and the
background. Large icons take 3 letters, the small and status icons 2 (3 letters do not fit 14 px).

usage: python redraw_wnd.py <WND.BIN in> <WND.BIN out> [preview.png]
"""
import json
import os
import re
import struct
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONT = r'C:\Windows\Fonts\arialbd.ttf'
# kind -> (inner box x0, y0, x1, y1 (exclusive), letter cap height in px)
BOXES = {'large': (2, 2, 26, 26, 11), 'small': (2, 2, 16, 16, 8), 'small2': (1, 1, 15, 15, 8), 'status': (1, 2, 14, 13, 7)}


def kind_of(entry):
    k = entry['kind']
    if k.startswith('battle icon, large'):
        return 'large'
    if k.startswith('battle icon, small (second set)'):
        return 'small2'                              # 16x16 square, 1 px border
    if k.startswith('battle icon, small'):
        return 'small'
    if k.startswith('status icon'):
        return 'status'
    return None


def textures(data):
    return [m.start() for m in re.finditer(b'TX48', data)]


def palette(data, o):
    t, w, h, hs, ps, do, ds = struct.unpack_from('<7I', data, o + 4)
    pal = data[o + hs:o + hs + ps]
    return [tuple(pal[i * 4:i * 4 + 4]) for i in range(ps // 4)], (t, w, h, do)


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def render_text(text, cap, max_w):
    """Anti-aliased mask (L) of `text` with cap height `cap`, squeezed to max_w if needed."""
    scale = 8
    font = ImageFont.truetype(FONT, cap * scale * 100 // 72)
    bbox = font.getbbox(text)
    im = Image.new('L', (bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8))
    ImageDraw.Draw(im).text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=255)
    im = im.crop(im.getbbox())
    h = cap
    w = round(im.width * h / im.height)
    w = min(w, max_w)
    return im.resize((w, h), Image.LANCZOS)


def redraw(data, o, text, kind):
    pal, (t, w, h, do) = palette(data, o)
    assert t == 1, 'expected an 8-bit texture'
    px = bytearray(data[o + do:o + do + w * h])
    x0, y0, x1, y1, cap = BOXES[kind]
    inside = [px[y * w + x] for y in range(y0, y1) for x in range(x0, x1)]
    used = sorted(set(inside))
    # background: the most common colour on the ring just inside the frame (the glyph rarely
    # touches it); body: the brightest inside colour; outline: the darkest
    ring = [px[y * w + x] for y in range(y0, y1) for x in range(x0, x1)
            if x in (x0, x1 - 1) or y in (y0, y1 - 1)]
    bg = max(set(ring), key=ring.count)
    body = max(used, key=lambda i: lum(pal[i]))
    outline = min(used, key=lambda i: lum(pal[i]))
    mid = min(used, key=lambda i: abs(lum(pal[i]) - (lum(pal[body]) + lum(pal[bg])) / 2))
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[y * w + x] = bg
    mask = render_text(text, cap, x1 - x0 - (1 if kind == 'status' else 2))
    ox = x0 + (x1 - x0 - mask.width) // 2
    oy = y0 + (y1 - y0 - mask.height) // 2
    a = mask.load()
    solid = {(ox + x, oy + y): a[x, y] for x in range(mask.width) for y in range(mask.height) if a[x, y] >= 96}
    for (x, y), v in solid.items():
        px[y * w + x] = body if v >= 170 else mid
    for (x, y) in list(solid):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in solid and x0 <= q[0] < x1 and y0 <= q[1] < y1:
                    px[q[1] * w + q[0]] = outline
    return bytes(px), (t, w, h, do), pal


def patch_wnd(data, preview=None):
    tr = json.load(open(os.path.join(ROOT, 'work/translation/en/ui/textures.json'), encoding='utf-8'))['WND.BIN']
    out = bytearray(data)
    offs = textures(data)
    shots = []
    done = 0
    for idx, e in sorted(tr.items(), key=lambda kv: int(kv[0])):
        kind = kind_of(e)
        if not kind:
            continue
        o = offs[int(idx)]
        text = e.get('en_icon') or e['en']
        px, (t, w, h, do), pal = redraw(data, o, text, kind)
        out[o + do:o + do + w * h] = px
        done += 1
        if preview:
            im = Image.new('RGBA', (w, h))
            im.putdata([pal[i][:3] + (min(255, pal[i][3] * 2),) for i in px])
            shots.append(im)
    if preview and shots:
        sheet = Image.new('RGB', (len(shots) * 36 * 4, 36 * 4), (60, 60, 80))
        for n, im in enumerate(shots):
            bg = Image.new('RGBA', im.size, (60, 60, 80, 255))
            bg.alpha_composite(im)
            sheet.paste(bg.convert('RGB').resize((im.width * 4, im.height * 4), Image.NEAREST), (n * 36 * 4, 0))
        sheet.save(preview)
    print(f'WND.BIN: {done} icons redrawn')
    return bytes(out)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    open(sys.argv[2], 'wb').write(patch_wnd(d, sys.argv[3] if len(sys.argv) > 3 else None))
