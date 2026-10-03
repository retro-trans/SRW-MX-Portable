"""Translate every native chapter-title atlas, preserving existing English art.

python tools/patch_chapter_cards.py base.iso 0.4.2
The metadata guards each original title area and palette; non-title pixels and
all other ISO files are preserved. No emulator texture replacements are used.
"""
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont
import pycdlib
import build_patch
import make_latin_font

ROOT = Path(__file__).resolve().parents[1]
ASSET = '/PSP_GAME/USRDIR/PACKMAPC2_ADD.BIN'
WIDTH, HEIGHT, TITLE_HEIGHT = 256, 256, 52


def render_title(text):
    words = text.split()
    protected = {('La', 'Mu'), ('Getter', 'Robo'), ('Viper', 'Squad'), ('Demon', 'God')}
    candidates = [[text]] + [[' '.join(words[:i]), ' '.join(words[i:])] for i in range(1, len(words))
                           if (words[i-1].rstrip(','), words[i].rstrip(',')) not in protected]
    for size in range(20, 13, -1):
        font = ImageFont.truetype(make_latin_font.FONT, size * 4)
        fits = []
        for lines in candidates:
            masks = []
            for line in lines:
                box = font.getbbox(line)
                mask = Image.new('L', (box[2] - box[0] + 8, box[3] - box[1] + 8))
                ImageDraw.Draw(mask).text((4 - box[0], 4 - box[1]), line, font=font, fill=255)
                masks.append(mask.crop(mask.getbbox()))
            widths = [round(im.width / 4) for im in masks]
            heights = [round(im.height / 4) for im in masks]
            height = sum(heights) + 3 * (len(lines) - 1)
            if max(widths) <= 248 and height <= 48:
                fits.append((len(lines), max(widths) - min(widths), lines, masks, widths, heights, height))
        if fits:
            _, _, lines, masks, widths, heights, height = min(fits, key=lambda row: row[:2])
            title = Image.new('L', (WIDTH, TITLE_HEIGHT))
            y = 2 + (48 - height) // 2
            for mask, width, line_height in zip(masks, widths, heights):
                mask = mask.resize((width, line_height), Image.Resampling.LANCZOS)
                title.paste(mask, ((WIDTH - width) // 2, y))
                y += line_height + 3
            assert title.getbbox()[2] <= 252 and title.getbbox()[3] <= 50
            return title, {'font_size': size, 'lines': lines, 'bounds': list(title.getbbox())}
    raise ValueError('Title does not fit: ' + text)


def indexed_title(mask, palette):
    # Some original atlases have only ~20 useful colors; their byte indices
    # are not luminance. Keep every palette byte and map English to its colors.
    colors = [tuple(palette[i*4:i*4+4]) for i in range(256)]
    opaque = [i for i, color in enumerate(colors) if color[3] == 128]
    assert colors[0][3] == 0 and opaque
    table = [0]
    for value in range(1, 256):
        table.append(min(opaque, key=lambda i: sum((c-value)**2 for c in colors[i][:3])))
    return bytes(table[value] for value in mask.tobytes())


def patch_archive(data, specs, preview):
    output = bytearray(data)
    results = []
    preview.mkdir(parents=True, exist_ok=True)
    masks = {}
    allowed = []
    for row in specs['cards']:
        offset = row['pixel_offset']
        palette = data[offset-1024:offset]
        pixels = data[offset:offset+WIDTH*HEIGHT]
        assert hashlib.sha256(palette).hexdigest() == row['palette_sha256'], row['id']
        # The single 0.4.1 Super card is already English; accept that exact
        # published title area too, then rewrite it to the common layout.
        old = pixels[:WIDTH*TITLE_HEIGHT]
        assert hashlib.sha256(old).hexdigest() in row['accepted_title_sha256'], row['id']
        if row['needs_translation']:
            if row['en'] not in masks:
                masks[row['en']] = render_title(row['en'])
            mask, layout = masks[row['en']]
            encoded = indexed_title(mask, palette)
            output[offset:offset+len(encoded)] = encoded
            allowed.append((offset, offset+len(encoded)))
            assert output[offset+len(encoded):offset+WIDTH*HEIGHT] == pixels[len(encoded):]
            image = Image.frombytes('P', (WIDTH, TITLE_HEIGHT), encoded)
            image.putpalette(bytes(c for color in [palette[i*4:i*4+4] for i in range(256)] for c in color[:3]))
            image.convert('RGB').save(preview / (row['id'] + '.png'))
            results.append(dict(id=row['id'], translated=True, en=row['en'], **layout))
        else:
            assert output[offset:offset+WIDTH*HEIGHT] == pixels
            results.append(dict(id=row['id'], translated=False, en=row['en'], preserved_native_english=True))
    # Prove nothing outside the explicitly enumerated title rectangles changed.
    last = 0
    for start, end in sorted(allowed):
        assert output[last:start] == data[last:start]
        last = end
    assert output[last:] == data[last:]
    assert len(output) == len(data)
    return bytes(output), results


def digest_iso_file(iso, path):
    digest = hashlib.sha256()
    with iso.open_file_from_iso(iso_path=path) as stream:
        while True:
            part = stream.read(4*1024*1024)
            if not part:
                break
            digest.update(part)
    return digest.hexdigest()


def main(source, version):
    source = Path(source).resolve()
    output = ROOT / 'work/output' / ('SRWMX_EN_%s.iso' % version)
    if output.exists() or output.resolve() == source:
        raise FileExistsError('Choose a new version/output; existing builds are preserved.')
    specs = json.loads((ROOT / 'work/translation/en/ui/all_chapter_cards.json').read_text(encoding='utf8'))
    assert len(specs['cards']) == 205
    iso = pycdlib.PyCdlib()
    iso.open(str(source))
    archive = build_patch.iso_read(iso, ASSET)
    updated, results = patch_archive(archive, specs, ROOT / 'work/build/chapter_cards/english')
    paths = []
    for folder, directories, files in iso.walk(iso_path='/'):
        paths.extend(folder.rstrip('/') + '/' + str(name) for name in files)
    before = {path: digest_iso_file(iso, path) for path in paths if path != ASSET}
    iso.rm_file(iso_path=ASSET)
    iso.add_fp(io.BytesIO(updated), len(updated), iso_path=ASSET)
    iso.write(str(output))
    iso.close()
    check = pycdlib.PyCdlib()
    check.open(str(output))
    assert build_patch.iso_read(check, ASSET) == updated
    for path, digest in before.items():
        assert digest_iso_file(check, path) == digest, path
    check.close()
    shutil.copyfile(ROOT / 'incoming/fonts/FONT_LICENSE.txt', output.with_name(output.stem + '_FONT_LICENSE.txt'))
    report = dict(version=version, base_iso=source.name, native_asset_patch=True,
                  texture_replacement=False, title_atlases_covered=len(results),
                  translated_atlases=sum(row['translated'] for row in results),
                  native_english_atlases_preserved=sum(not row['translated'] for row in results),
                  scenario_titles_covered=67, unchanged_iso_files=len(before),
                  changed_iso_files=[ASSET], archive_sha256=hashlib.sha256(updated).hexdigest(), cards=results)
    (output.parent / ('chapter_cards_%s_verification.json' % version)).write_text(json.dumps(report, indent=1), encoding='utf8')
    print('Written and verified:', output)
    print('Coverage:', report['title_atlases_covered'], 'atlases;', report['translated_atlases'], 'translated;',
          report['native_english_atlases_preserved'], 'native English preserved;', len(before), 'other files unchanged.')


if __name__ == '__main__':
    main(*sys.argv[1:])
