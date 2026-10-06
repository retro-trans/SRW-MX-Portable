"""Translate native map support-caption images, preserving counters and layout."""
import argparse, json, shutil, struct
from PIL import Image, ImageDraw, ImageFont
from port_ps2_translations import ROOT, sha
from port_ps2_prologue import save
from ps2_graphics_port import p2ig_textures, fake_tx48
from redraw_banners import read, lum
from ps2_map_label_pixels import decode, encode

VERSION = '0.1.15'
SOURCE_VERSION = '0.1.14'
BASE = ROOT/'work/build/ps2'/f'map_support_{VERSION}'
PREVIOUS = ROOT/'work/build/ps2'/f'setup_save_{SOURCE_VERSION}'
LABELS = {'M_65': 'Support Atk', 'M_66': 'Support Def', 'M_67': 'Assist Atk'}
FONT = 'C:/Windows/Fonts/bahnschrift.ttf'


def render(text, palette):
    scale = 4
    font = ImageFont.truetype(FONT, 26 * scale)
    font.set_variation_by_name(b'Bold Condensed')
    box = font.getbbox(text, anchor='ls')
    mask = Image.new('L', (128 * scale, 32 * scale))
    x = round(63.5 * scale - (box[0] + box[2]) / 2)
    ImageDraw.Draw(mask).text((x, 24 * scale), text, font=font, fill=255, anchor='ls')
    mask = mask.resize((128, 32), Image.Resampling.LANCZOS)
    bounds = mask.point(lambda value: 255 if value >= 40 else 0).getbbox()
    assert bounds and bounds[0] >= 5 and bounds[2] <= 123 and bounds[1] >= 1 and bounds[3] <= 31
    ramp = sorted((i for i, c in enumerate(palette) if c[3]), key=lambda i: lum(palette[i]))
    clear = next(i for i, c in enumerate(palette) if not c[3])
    dark, body = ramp[0], ramp[-1]
    pixels = [clear] * 4096
    ink = {(x, y): mask.getpixel((x, y)) for y in range(32) for x in range(128)
           if mask.getpixel((x, y)) >= 40}
    for x, y in ink:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
            if 0 <= x + dx < 128 and 0 <= y + dy < 32:
                pixels[(y + dy) * 128 + x + dx] = dark
    shades = ramp[1:] or [body]
    for (x, y), coverage in ink.items():
        pixels[y * 128 + x] = shades[round((len(shades)-1)*(coverage-40)/215)]
    return pixels, dict(font='Bahnschrift Bold Condensed',font_size=26,
                        shared_baseline=24,center_x=63.5,ink_bounds=list(bounds),
                        horizontal_rescaling=False)


def preview(pixels, palette):
    pic = Image.new('RGBA', (128, 32))
    pic.putdata([palette[v][:3]+(min(255,palette[v][3]*2),) for v in pixels])
    return pic


def prepare():
    BASE.mkdir(parents=True,exist_ok=True)
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT','.45','.json'):
            shutil.copyfile(path,BASE/path.name)
    elf=(BASE/'SLPS_253.45').read_bytes()
    data=bytearray((BASE/'MAP.BIN').read_bytes()); original=bytes(data)
    sec=struct.unpack_from('<18I',elf,0x37e438)
    start,end=sec[16]*2048,sec[17]*2048
    rows={r['name']:r for r in p2ig_textures(data[start:end])}
    out=ROOT/'work/ui/ps2'/f'map_support_{VERSION}';out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'work/source/ps2/map_graphics_suffix.bin'
    if not source.exists():
        import pycdlib
        native_elf=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
        native_sections=struct.unpack_from('<18I',native_elf,0x37e438)
        iso=pycdlib.PyCdlib();iso.open(str(ROOT/'Super Robot Taisen MX (Japan).iso'))
        with iso.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
            stream.seek(native_sections[11]*2048);source.write_bytes(stream.read())
        iso.close()
    native=source.read_bytes();native_rows={r['name']:r for r in p2ig_textures(native) if r['name'] in LABELS}
    ranges=[];records=[]
    sheet=Image.new('RGB',(768,3*90),(25,25,25));draw=ImageDraw.Draw(sheet)
    for i,(name,english) in enumerate(LABELS.items()):
        r=rows[name];assert (r['width'],r['height'],r['psm'],r['pixel_bytes'])==(128,32,20,2048)
        off=start+r['offset']+r['pixel_offset'];raw=bytes(data[off:off+2048])
        nr=native_rows[name];no=nr['offset']+nr['pixel_offset']
        assert raw==native[no:no+2048],'Source caption changed since original disc'
        fake=fake_tx48(data[start:end],r);_,_,_,palette,_,_=read(fake,0)
        old=decode(raw);assert encode(old)==raw
        new,layout=render(english,palette);changed=encode(new);assert decode(changed)==new
        data[off:off+2048]=changed;ranges.append([off,off+2048])
        before,after=preview(old,palette),preview(new,palette)
        before.save(out/(name+'_original.png'));after.save(out/(name+'_english.png'))
        draw.text((0,i*90),name+' -> '+english,fill='white')
        for pic,x in ((before,0),(after,384)):
            pic=pic.resize((384,72),Image.Resampling.NEAREST);sheet.paste(pic,(x,i*90+18),pic)
        records.append(dict(asset=name,english=english,pixel_offset=hex(off),pixel_bytes=2048,
                            source_sha256=sha(raw),target_sha256=sha(changed),layout=layout,
                            palette_sha256=sha(bytes(v for c in palette for v in c))))
    last=0
    for a,z in sorted(ranges):assert data[last:a]==original[last:a];last=z
    assert data[last:]==original[last:] and len(data)==len(original)
    assert elf==(PREVIOUS/'SLPS_253.45').read_bytes()
    (BASE/'MAP.BIN').write_bytes(data);sheet.save(out/'support_before_after.png')
    report=dict(version=VERSION,source_build=SOURCE_VERSION,labels=records,
                changed_pixel_ranges=ranges,headers_and_palettes_preserved=True,
                counters_and_positions_preserved=True,executable_unchanged=True,
                source_map_sha256=sha(original),target_map_sha256=sha(data),
                native_pixel_edits=True,texture_replacement=False,
                decoded_preview='work/ui/ps2/map_support_0.1.15/support_before_after.png',
                visual_validation='decoded assets verified; in-game confirmation pending',github_release=False)
    save(BASE/'map_support.json',report)
    save(ROOT/'work/translation/en/ps2'/f'map_support_{VERSION}.en.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');args=p.parse_args()
    report=prepare();print(json.dumps(report,indent=2))
    if args.build:
        from verify_ps2_map_support import verify as verify_pixels
        from verify_ps2_stage30 import verify
        from package_ps2_stage30 import build
        verify_pixels(BASE,VERSION)
        verify(BASE,VERSION)
        build(BASE,VERSION,SOURCE_VERSION)
