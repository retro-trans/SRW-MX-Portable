"""Render a proportional Latin glyph set into the game's font atlas (STATIC2_ADD.BIN +0x40000).

Style copied from the original glyphs: body levels 0xC-0xE with anti-aliased edges (6-0xB),
baseline row 15 of the 18x18 cell. Latin drop shadow is disabled.
Glyphs are drawn left-aligned (x=1) so the VWF patch (vwf_patch.py) can crop them.

FONT: Genei LateGo v2, Medium, from the official v2.1 separate-TTF package.
Latin letters have proportional widths; Japanese atlas cells are retained.
SIL OFL 1.1 copyright/licence notices accompany the derived SRW MX Latin atlas.

usage: python make_latin_font.py <STATIC2_ADD.BIN in> <out> [preview.png]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'incoming', 'fonts',
                    'GenEiLatin_v2.1', 'GenEiLatin-Separate_v2.1', 'GenEiLateGoN_v2.ttf')
VARIATION = None     # static Medium font; Latin is proportional in the normal N edition
SIZE = 15            # px em size
SHADOW = False       # the original glyphs carry a 1 px drop shadow (level 5); off since 0.1.2
BASELINE = 15        # baseline row inside the 18px cell
# Digits are tabular: every digit gets the same advance (DIGIT_W of 18, VWF entry fixed in
# vwf_patch.width_table) and is stretched DIGIT_STRETCH wide and centred in that box. Genei LateGo's
# proportional lining figures looked condensed next to the game's full-width numbers and broke
# column alignment ("1" was 6, "4" was 10). Since 0.2.1.
DIGITS = '0123456789'
DIGIT_W = 10
DIGIT_LEFT = 1
DIGIT_STRETCH = 1.0   # 1.2 in 0.2.1; the squeeze was the narrow ASCII font, fixed in vwf_patch (hctx)
ATLAS = 0x40000

# SJIS full-width code -> character to draw
CHARS = {0x8140: ' '}
for i, ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    CHARS[0x8260 + i] = ch
for i, ch in enumerate('abcdefghijklmnopqrstuvwxyz'):
    CHARS[0x8281 + i] = ch
for i, ch in enumerate('0123456789'):
    CHARS[0x824F + i] = ch
# English punctuation uses codes Japanese text rarely needs, so remaining Japanese stays intact:
# ， ． (not 、 。), － (not ー), ’ “ ” for quotes. ！ ？ ： ； are shared with Japanese.
PUNCT = {0x8143: ',', 0x8144: '.', 0x8146: ':', 0x8147: ';', 0x8148: '?', 0x8149: '!',
         0x815E: '/', 0x8160: '~', 0x8166: "'", 0x8167: '"', 0x8168: '"', 0x8169: '(',
         0x816A: ')', 0x816D: '[', 0x816E: ']', 0x817B: '+', 0x817C: '-', 0x8181: '=',
         0x8190: '$', 0x8193: '%', 0x8194: '#', 0x8195: '&', 0x8196: '*'}
CHARS.update(PUNCT)


def slot(code):
    v = code - 0x8140
    return v - (v >> 8) * 64


def render(ch, font):
    """-> 18x18 list of nibble values."""
    im = Image.new('L', (18, 18), 0)
    dr = ImageDraw.Draw(im)
    asc, _ = font.getmetrics()
    if ch in DIGITS:
        wide = Image.new('L', (36, 18), 0)
        ImageDraw.Draw(wide).text((4, BASELINE - asc), ch, fill=255, font=font)
        x0, _, x1, _ = wide.getbbox()
        ink = wide.crop((x0, 0, x1, 18))
        ink = ink.resize((max(1, round((x1 - x0) * DIGIT_STRETCH)), 18), Image.LANCZOS)
        assert ink.width <= DIGIT_W - 1, ch
        im.paste(ink, (DIGIT_LEFT + (DIGIT_W - 1 - ink.width) // 2, 0))
    else:
        dr.text((1, BASELINE - asc), ch, fill=255, font=font)
    a = [[im.getpixel((x, y)) for x in range(18)] for y in range(18)]
    out = [[0] * 18 for _ in range(18)]
    for y in range(18):
        for x in range(18):
            v = a[y][x]
            if v >= 40:
                out[y][x] = max(6, min(14, 6 + (v * 9) // 255))     # 6..14 (0xE)
    for y in range(17, -1, -1):                                       # drop shadow
        for x in range(17, -1, -1):
            if SHADOW and out[y][x] == 0 and ((x > 0 and out[y][x - 1] > 5) or (y > 0 and out[y - 1][x] > 5)
                                              or (x > 0 and y > 0 and out[y - 1][x - 1] > 5)):
                out[y][x] = 5
    return out


def main(src, dst, preview=None):
    d = bytearray(open(src, 'rb').read())
    font = ImageFont.truetype(FONT, SIZE)
    if VARIATION:
        font.set_variation_by_name(VARIATION)
    for code, ch in CHARS.items():
        g = render(ch, font) if ch != ' ' else [[0] * 18 for _ in range(18)]
        row, col = divmod(slot(code), 14)
        for y in range(18):
            for x in range(18):
                px = col * 18 + x
                o = ATLAS + (row * 18 + y) * 128 + px // 2
                if px & 1:
                    d[o] = (d[o] & 0x0F) | (g[y][x] << 4)
                else:
                    d[o] = (d[o] & 0xF0) | g[y][x]
    open(dst, 'wb').write(d)
    if preview:
        im = Image.new('L', (256, 18 * 40))
        px = []
        for b in d[ATLAS:ATLAS + 128 * 18 * 40]:
            px += [(b & 15) * 17, (b >> 4) * 17]
        im.putdata(px)
        im.resize((512, im.height * 2), Image.NEAREST).save(preview)
    print('font written to', dst)


if __name__ == '__main__':
    main(*sys.argv[1:4])
