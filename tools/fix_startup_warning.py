"""Translate only the native startup-warning background on PSP and PS2."""
import copy
import json
import shutil
import struct
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw, ImageFont
from make_latin_font import FONT
from patch_wnd_headers import file_digest, digest
from port_ps2_translations import sha

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.20'
SPECS = {
    'PS2': dict(previous='0.4.19', prefix='SRWMX_PS2_EN_', asset='/DATA/IM.BIN;1',
                offset=0x27e8000, size=(640,448), visible_width=640, font_size=18,
                width=560, pitch=24, gap=20, source='work/source/ps2/IM.BIN'),
    'PSP': dict(previous='0.4.18', prefix='SRWMX_EN_', asset='/PSP_GAME/USRDIR/IM_ADD.BIN',
                offset=0x14ea000, size=(512,272), visible_width=480, font_size=12,
                width=440, pitch=16, gap=10, source='work/build/IM_ADD.orig'),
}
COMMON = [
    'This game contains sequences that use flashing\nimages and other flash effects.',
    'In rare cases, exposure to bright or flashing lights\nmay cause temporary muscle spasms, loss of\nconsciousness or other symptoms.',
    'If you have experienced these symptoms,\nconsult a doctor before playing this game.',
    'Read the instruction manual carefully\nbefore playing.',
]
FIRST = {
    'PS2': 'When playing this game, keep the room well lit\nand sit as far from the TV screen as possible.',
    'PSP': 'When playing this game, keep as much distance\nas possible from the LCD screen.',
}


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2)+'\n', encoding='utf8')


def colors(data, platform):
    o=SPECS[platform]['offset']; raw=data[o:o+1024]
    indexes=[(v&~24)|((v&8)<<1)|((v&16)>>1) for v in range(256)] if platform=='PS2' else range(256)
    return [tuple(raw[i*4:i*4+3]) for i in indexes]


def picture(data, platform):
    s=SPECS[platform]; w,h=s['size']; o=s['offset']+1024
    pal=colors(data,platform); im=Image.new('RGB',(w,h))
    im.putdata([pal[v] for v in data[o:o+w*h]])
    return im.crop((0,0,s['visible_width'],h))


def render(platform):
    s=SPECS[platform]; scale=4
    font=ImageFont.truetype(FONT,s['font_size']*scale)
    paras=[]
    for text in [FIRST[platform]]+COMMON:
        lines=text.split('\n')
        assert all(font.getlength(line)<=s['width']*scale for line in lines)
        paras.append(lines)
    total=sum(len(p) for p in paras)*s['pitch']+4*s['gap']
    w,h=s['size']; top=(h-total)//2
    assert top>=16 and top+total<=h-16
    mask=Image.new('L',(w*scale,h*scale)); draw=ImageDraw.Draw(mask)
    y=top; layouts=[]
    for lines in paras:
        for text in lines:
            box=font.getbbox(text); width=font.getlength(text)/scale
            x=(s['visible_width']-width)/2
            assert x>=16 and x+width<=s['visible_width']-16
            draw.text((round(x*scale), y*scale-box[1]),text,font=font,fill=255)
            layouts.append(dict(text=text,x=x,y=y,width=width))
            y+=s['pitch']
        y+=s['gap']
    mask=mask.resize((w,h),Image.Resampling.LANCZOS)
    assert mask.getbbox()[0]>=16 and mask.getbbox()[2]<=s['visible_width']-16
    return mask, dict(font='Genei LateGo v2 Medium',font_size=s['font_size'],
                      horizontal_rescaling=False,ink_bounds=mask.getbbox(),lines=layouts,
                      paragraphs=[' '.join(p) for p in paras])


def patch(data, platform):
    s=SPECS[platform]; o=s['offset']; w,h=s['size']; a=o+1024; z=a+w*h
    native=(ROOT/s['source']).read_bytes()
    assert data[o:z]==native[o:z], 'Unexpected warning artwork; preserve unknown revisions'
    mask,layout=render(platform); pal=colors(data,platform)
    ramp=[min(range(256),key=lambda i:sum((pal[i][j]-v)**2 for j in range(3))) for v in range(256)]
    assert max(max(c) for c in pal)==255
    pixels=bytes(ramp[v] for v in mask.tobytes())
    out=data[:a]+pixels+data[z:]
    assert len(out)==len(data) and out[:a]==data[:a] and out[z:]==data[z:]
    return out,dict(platform=platform,palette_offset=hex(o),pixel_offset=hex(a),
        atlas_size=[w,h],visible_width=s['visible_width'],pixel_ranges=[[a,z]],
        source_caption_sha256=sha(data[a:z]),target_caption_sha256=sha(pixels),
        source_resource_sha256=sha(data),target_resource_sha256=sha(out),
        palette_preserved=True,other_pixels_and_data_preserved=True,layout=layout)


def build(platform):
    s=SPECS[platform]; source=ROOT/'work/output'/f"{s['prefix']}{s['previous']}.iso"
    output=ROOT/'work/output'/f"{s['prefix']}{VERSION}.iso"
    assert not output.exists(), 'Preserve versioned images'
    iso=pycdlib.PyCdlib(); iso.open(str(source))
    paths=[folder.rstrip('/')+'/'+name for folder,_,names in iso.walk(iso_path='/') for name in names]
    hashes={p:file_digest(iso,p) for p in paths}
    with iso.open_file_from_iso(iso_path=s['asset']) as f: original=f.read()
    changed,evidence=patch(original,platform)
    record=iso.get_record(iso_path=s['asset']); extent=record.extent_location()*2048
    assert len(changed)==record.data_length
    iso.close()
    ui=ROOT/'work/ui'/platform.lower()/f'startup_warning_{VERSION}';ui.mkdir(parents=True,exist_ok=True)
    for label,d in [('original',original),('english',changed)]:picture(d,platform).save(ui/f'{label}.png')
    save(ui/'layout.json',evidence)
    base=ROOT/'work/build'/platform.lower()/f'startup_warning_{VERSION}';base.mkdir(parents=True,exist_ok=True)
    (base/s['asset'].rsplit('/',1)[-1].split(';')[0]).write_bytes(changed)
    shutil.copyfile(source,output)
    with output.open('r+b') as f:
        for a,z in evidence['pixel_ranges']:f.seek(extent+a);f.write(changed[a:z])
    verify=pycdlib.PyCdlib();verify.open(str(output));checks=[]
    for path in paths:
        actual=file_digest(verify,path);expected=sha(changed) if path==s['asset'] else hashes[path]
        assert actual==expected,path
        checks.append(dict(path=path,sha256=actual,changed=path==s['asset']))
    udf=False
    if platform=='PS2':
        with verify.open_file_from_iso(udf_path='/data/im.bin') as f:assert sha(f.read())==sha(changed)
        udf=True
    with verify.open_file_from_iso(iso_path=s['asset']) as f:assert picture(f.read(),platform).tobytes()==picture(changed,platform).tobytes()
    verify.close()
    allowed=[(extent+a,extent+z) for a,z in evidence['pixel_ranges']]
    with source.open('rb') as a, output.open('rb') as b:
        last=0
        for start,end in allowed+[(source.stat().st_size,source.stat().st_size)]:
            remaining=start-last
            while remaining:
                count=min(8*1024*1024,remaining);assert a.read(count)==b.read(count);remaining-=count
            a.seek(end);b.seek(end);last=end
    assert output.stat().st_size==source.stat().st_size
    license=source.with_name(source.stem+'_FONT_LICENSE.txt')
    assert license.exists();shutil.copyfile(license,output.with_name(output.stem+'_FONT_LICENSE.txt'))
    with output.open('rb') as f: target_sha=digest(f)
    report=dict(version=VERSION,platform=platform,source_version=s['previous'],output=str(output.relative_to(ROOT)),
        output_sha256=target_sha,bytes=output.stat().st_size,warning=evidence,files=checks,
        whole_disc_only_warning_pixels_changed=True,udf_verified=udf,
        extracted_asset_preview_verified=True,in_game_visual_validation='pending',local_build_only=True,github_release=False)
    save(ROOT/'work/output'/f'{platform.lower()}_startup_warning_{VERSION}_verification.json',report)
    save(ROOT/'work/translation/en'/platform.lower()/f'startup_warning_{VERSION}.en.json',
         dict(version=VERSION,platform=platform,paragraphs=evidence['layout']['paragraphs'],asset=s['asset'],palette_offset=hex(s['offset'])))
    if platform=='PS2':
        prior=json.loads((ROOT/'work/output'/f"ps2_font_{s['previous']}_verification.json").read_text())
        aggregate=copy.deepcopy(prior)
        for row in aggregate['files']:
            assert hashes[row['path']]==row['target_sha256']
            if row['path']==s['asset']:row['target_sha256']=sha(changed)
        aggregate.update(version=VERSION,output=report['output'],bytes=report['bytes'],target_sha256=target_sha,
            source_build_version=s['previous'],source_build_sha256=prior['target_sha256'],changed_from_previous=[s['asset']],
            startup_warning=evidence,pcsx2_fresh_boot_verified=False,pcsx2_visual_validation='Startup warning pending',github_release=False)
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',aggregate)
        fontbase=ROOT/'work/build/ps2'/f'font_{VERSION}';fontbase.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'work/build/ps2'/f"font_{s['previous']}"/'SLPS_253.45',fontbase/'SLPS_253.45')
        save(fontbase/'patch.json',aggregate['font'])
    print(json.dumps(dict(platform=platform,output=str(output),sha256=target_sha)),flush=True)
    return report


if __name__=='__main__':
    import sys
    if '--preview' in sys.argv:
        for platform,s in SPECS.items():
            data=(ROOT/s['source']).read_bytes();changed,evidence=patch(data,platform)
            ui=ROOT/'work/ui'/platform.lower()/f'startup_warning_{VERSION}';ui.mkdir(parents=True,exist_ok=True)
            picture(data,platform).save(ui/'original.png');picture(changed,platform).save(ui/'english.png');save(ui/'layout.json',evidence)
            print(platform,json.dumps(evidence['layout']))
    else:
        for platform in SPECS:build(platform)
