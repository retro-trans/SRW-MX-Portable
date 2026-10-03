"""Compare the actual packaged 4x atlas before and after the descender fix."""
import io
import json
from pathlib import Path
import pycdlib
from PIL import Image, ImageDraw, ImageFont
import make_latin_font as glyphs

ROOT = Path(__file__).resolve().parent.parent


def packaged_atlas(version):
    layout = json.loads((ROOT / 'work/build/native_font4x/layout.json').read_text())
    iso = pycdlib.PyCdlib()
    iso.open(str(ROOT / ('work/output/SRWMX_EN_%s.iso' % version)))
    stream = io.BytesIO()
    iso.get_file_from_iso_fp(stream, iso_path='/PSP_GAME/SYSDIR/BOOT.BIN')
    iso.close()
    offset = 0x60 + layout['atlas_va']
    data = stream.getvalue()[offset:offset + layout['atlas_bytes']]
    pixels = bytes(v * 17 for byte in data for v in (byte & 15, byte >> 4))
    return Image.frombytes('L', (512, len(pixels) // 512), pixels)


def main():
    before, after = packaged_atlas('0.1.4'), packaged_atlas('0.1.5')
    def cell(image, number):
        x, y = number % 7 * 72, number // 7 * 72
        return image.crop((x, y, x + 72, y + 72))
    changed = [char for n, char in enumerate(glyphs.CHARS.values())
               if cell(before, n).tobytes() != cell(after, n).tobytes()]
    assert 'g' in changed
    assert set(changed).issubset(set('gjpqy,;'))
    chars = list('gjpqy,;')
    canvas = Image.new('RGB', (7*84+16, 242), '#101525')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 16)
    numbers = {char: n for n, char in enumerate(glyphs.CHARS.values())}
    for row, (label, image) in enumerate([('Before: 0.1.4', before), ('Fixed: 0.1.5', after)]):
        top = row * 120
        draw.text((8, top+2), label, font=font, fill='white')
        for col, char in enumerate(chars):
            draw.text((12+col*84, top+24), char, font=font, fill='#75e6df')
            canvas.paste(cell(image, numbers[char]).convert('RGB'), (8+col*84, top+48))
    output = ROOT / 'work/ui/font_descenders_0.1.5.png'
    canvas.save(output)
    report = dict(before='0.1.4', after='0.1.5', changed_glyphs=changed,
                  all_other_glyphs_identical=True, preview=str(output.relative_to(ROOT)).replace('\\','/'))
    (ROOT / 'work/output/font_0.1.5_descender_check.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
