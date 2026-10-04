"""Redraw the battle / status-effect banners (援護攻撃, パイロット気力減少 …) with English.

The same 58 banners exist twice: STATIC2_ADD.BIN TX48 #15-79 and MAP_ADD.BIN TX48 #23-87
(mapping in work/translation/en/ui/textures.json). Each is a 4-bit TX48 with its own 16-colour ramp:
0 = transparent, then colours from black (outline) to the brightest text colour.

The English is drawn in Bahnschrift Bold Condensed (squeezed further if needed) inside the box the
Japanese occupied, centred on the same point, using the banner's own palette: the brightest colour
for the body, the ramp for anti-aliasing, and the darkest colour as a 1 px outline plus a 1 px drop
shadow, like the originals.

usage: python redraw_banners.py <STATIC2_ADD.BIN> [preview.png]   (preview only)
"""
import json
import os
import re
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONT = r'C:\Windows\Fonts\bahnschrift.ttf'
VARIANT = b'Bold Condensed'


def textures(data):
    return [m.start() for m in re.finditer(b'TX48', data)]


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def read(data, o):
    t, w, h, hs, ps, do, ds = struct.unpack_from('<7I', data, o + 4)
    pal = [tuple(data[o + hs + 4 * i:o + hs + 4 * i + 4]) for i in range(ps // 4)]
    raw = data[o + do:o + do + ds]
    if t == 0:
        px = [(raw[i >> 1] >> (4 * (i & 1))) & 15 for i in range(w * h)]
    else:
        px = list(raw[:w * h])
    return t, w, h, pal, px, do


def write(data, o, t, w, h, px, do):
    if t == 0:
        b = bytearray(w * h // 2)
        for i, v in enumerate(px):
            b[i >> 1] |= v << (4 * (i & 1))
    else:
        b = bytes(px)
    data[o + do:o + do + len(b)] = b


def render_mask(text, height, max_w):
    scale = 4
    font = ImageFont.truetype(FONT, height * scale * 13 // 10)
    font.set_variation_by_name(VARIANT)
    box = font.getbbox(text)
    im = Image.new('L', (box[2] - box[0] + 16, box[3] - box[1] + 16))
    ImageDraw.Draw(im).text((8 - box[0], 8 - box[1]), text, font=font, fill=255)
    im = im.crop(im.getbbox())
    w = round(im.width * height / im.height)
    return im.resize((min(w, max_w), height), Image.LANCZOS)


def redraw(data, o, text):
    t, w, h, pal, px, do = read(data, o)
    used = [i for i in range(len(pal)) if pal[i][3] > 0]
    text_rows = 36 if h > 32 else h                             # 64-tall banners: text on top, arrow below
    ink = [(i % w, i // w) for i, v in enumerate(px) if pal[v][3] > 0 and i // w < text_rows]
    x0, x1 = min(p[0] for p in ink), max(p[0] for p in ink)
    y0, y1 = min(p[1] for p in ink), max(p[1] for p in ink)
    ramp = sorted(set(px[y * w + x] for x, y in ink), key=lambda i: lum(pal[i]))
    dark, body = ramp[0], ramp[-1]
    clear = next(i for i in range(len(pal)) if pal[i][3] == 0)
    cx = (x0 + x1) / 2
    room = int(2 * min(cx, w - 1 - cx)) - 2                     # keep it centred where the Japanese was
    text_h = max(8, (y1 - y0 + 1) - 4)                          # leave room for outline + shadow
    mask = render_mask(text, text_h, room)
    a = mask.load()
    ox = round(cx - mask.width / 2)
    oy = y0 + 1
    out = [clear] * (w * text_rows) + list(px[w * text_rows:])   # keep everything below the text
    cov = {}
    for x in range(mask.width):
        for y in range(mask.height):
            if a[x, y] >= 40:
                cov[(ox + x, oy + y)] = a[x, y]
    shade = ramp[1:] or [body]                                  # dark to bright, without the outline colour
    for (x, y) in cov:                                          # outline + drop shadow
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (2, 2), (1, 2), (2, 1)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < w and 0 <= q[1] < text_rows:
                out[q[1] * w + q[0]] = dark
    for (x, y), v in cov.items():
        if 0 <= x < w and 0 <= y < text_rows:
            k = round((len(shade) - 1) * (v - 40) / 215)
            out[y * w + x] = shade[k] if v < 230 else body
    write(data, o, t, w, h, out, do)
    return (t, w, h, pal, out)


def patch(data, which, preview=None):
    """which: 'STATIC2_ADD.BIN' or 'MAP_ADD.BIN'. Returns new bytes."""
    tj = json.load(open(os.path.join(ROOT, 'work/translation/en/ui/textures.json'), encoding='utf-8'))
    st = tj['STATIC2_ADD.BIN']
    if which == 'STATIC2_ADD.BIN':
        targets = {int(k): v['en'] for k, v in st.items()}
    else:
        m = tj['MAP_ADD.BIN']['map']
        targets = {}
        for k, v in m.items():
            if '-' in k:
                a, b = map(int, k.split('-'))
                c = int(v.split('-')[0])
                for i in range(a, b + 1):
                    if str(c + i - a) in st:
                        targets[i] = st[str(c + i - a)]['en']
            elif v in st:
                targets[int(k)] = st[v]['en']
    out = bytearray(data)
    offs = textures(data)
    shots = []
    for idx, text in sorted(targets.items()):
        shots.append(redraw(out, offs[idx], text))
    if preview:
        H = sum(s[2] + 2 for s in shots)
        sheet = Image.new('RGB', (256 * 2, H * 2), (40, 40, 60))
        y = 0
        for t, w, h, pal, px in shots:
            im = Image.new('RGBA', (w, h))
            im.putdata([pal[v][:3] + (min(255, pal[v][3] * 2),) for v in px])
            bg = Image.new('RGBA', (w, h), (40, 40, 60, 255))
            bg.alpha_composite(im)
            sheet.paste(bg.convert('RGB').resize((w * 2, h * 2), Image.NEAREST), (0, y))
            y += (h + 2) * 2
        sheet.save(preview)
    print(f'{which}: {len(targets)} banners redrawn')
    return bytes(out)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    patch(d, 'STATIC2_ADD.BIN', sys.argv[2] if len(sys.argv) > 2 else None)
