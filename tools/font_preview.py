"""Compare font atlas candidates and retain read-only translation fit results."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import make_latin_font as glyphs
import textfit
import vwf_patch

ROOT = Path(__file__).resolve().parent.parent


def main():
    output = ROOT / 'work/build/font_candidates'
    output.mkdir(exist_ok=True)
    glyphs.FONT = str(ROOT / 'incoming/fonts/GenEiLatin_v2.1/GenEiLatin-Separate_v2.1/GenEiLateGoN_v2.ttf')
    glyphs.VARIATION = None
    source = ROOT / 'work/build/STATIC2_ADD.orig'
    rows = []
    for stage in range(1, 31):
        path = ROOT / ('work/translation/en/script/stage%02d_campaign_full_merged.json' % stage)
        for row in json.loads(path.read_text(encoding='utf-8'))['rows']:
            rows.append((stage, row))
    prologue = json.loads((ROOT / 'work/translation/en/script/prologue_merged.json').read_text(encoding='utf-8'))['rows']
    results = []
    preview = Image.new('RGB', (900, 480), '#171b25')
    draw = ImageDraw.Draw(preview)
    label_font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    samples = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 !?'
    for index, size in enumerate([15, 14, 13, 12]):
        glyphs.SIZE = size
        path = output / ('genei_%d.bin' % size)
        glyphs.main(str(source), str(path))
        tab = vwf_patch.width_table(str(path))
        textfit._W = {code: ((tab[glyphs.slot(code)] & 31) * 16 + 9) // 18
                      if tab[glyphs.slot(code)] & 31 else 16
                      for code in list(textfit.ASCII.values()) + [textfit.QUOTE_OPEN, textfit.QUOTE_CLOSE]}
        def overflow(row):
            if row['kind'] == 'plain':
                return any(textfit.px(line) > 352 for line in row['en'].split('@'))
            return not textfit.fit_dialogue(row['speaker_en'], row['en'], row['kind'] == 'thought')[2]
        failures = [{'stage': stage, 'id': row['id']} for stage, row in rows if overflow(row)]
        prologue_failures = [row['id'] for row in prologue if overflow(row)]
        results.append(dict(size=size, campaign_overflows=failures, prologue_overflows=prologue_failures,
                            widths={char: textfit.px(char) for char in 'iMW01'},
                            atlas_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        font = ImageFont.truetype(glyphs.FONT, size)
        strip = Image.new('L', (440, 36))
        x = 0
        for char in samples:
            pixels = glyphs.render(char, font)
            ink = Image.new('L', (18, 18))
            ink.putdata([value * 17 for line in pixels for value in line])
            entry = tab[glyphs.slot(next(code for code, value in glyphs.CHARS.items() if value == char))]
            width, left = entry & 31, entry >> 5
            strip.paste(ink.crop((left, 0, left + width, 18)), (x, 0))
            x += width
        y = index * 120
        draw.text((15, y + 8), 'Genei LateGo %d px: prologue overflows %d; campaign %d' %
                  (size, len(prologue_failures), len(failures)), font=label_font, fill='white')
        preview.paste(strip.resize((880, 72), Image.NEAREST), (10, y + 40))
    preview.save(ROOT / 'work/ui/font_genei_sizes.png')
    (ROOT / 'work/output/font_genei_candidate_checks.json').write_text(json.dumps(results, indent=1), encoding='utf-8')
    print(json.dumps([{key: value if key not in ['campaign_overflows', 'prologue_overflows'] else len(value)
                      for key, value in result.items()} for result in results], indent=1))


if __name__ == '__main__':
    main()
