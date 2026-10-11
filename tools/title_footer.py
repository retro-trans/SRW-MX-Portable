"""Native title-screen credit/version for every numbered PSP and PS2 build."""
import hashlib
import json
import re
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw, ImageFont
from make_latin_font import FONT

ROOT = Path(__file__).resolve().parents[1]
URL = 'github.com/retro-trans'
SPECS = {
    'PSP': dict(asset='/PSP_GAME/USRDIR/OPWND.BIN', offset=0x2d3b40,
                size=(512,256), visible_width=480, box=(285,145,417,173),
                font_size=10, source='work/build/OPWND.orig'),
    'PS2': dict(asset='/DATA/IM.BIN;1', offset=0x298f000,
                size=(640,448), visible_width=640, box=(444,250,626,289),
                font_size=14, source='work/source/ps2/IM.BIN'),
}

def layout_spec(platform,version):
    s=dict(SPECS[platform])
    if platform=='PSP' and version_key(version)>=(0,4,29):
        s.update(box=(243,133,417,173),font_size=14)
    elif platform=='PSP' and version_key(version)>=(0,4,27):
        s.update(box=(0,0,174,40),font_size=14,panel=True)
    return s


def sha(data):
    return hashlib.sha256(data).hexdigest()


def version_key(version):
    assert re.fullmatch(r'0\.\d+\.\d+', version), 'Use a 0.x.y build version'
    return tuple(map(int, version.split('.')))


def colors(data, platform):
    o=SPECS[platform]['offset']; pal=data[o:o+1024]
    order=[(v&~24)|((v&8)<<1)|((v&16)>>1) for v in range(256)] if platform=='PS2' else range(256)
    return [tuple(pal[i*4:i*4+3])+(min(255,pal[i*4+3]*2),) for i in order]


def picture(data, platform):
    s=SPECS[platform]; w,h=s['size']; a=s['offset']+1024
    pal=colors(data,platform); im=Image.new('RGBA',(w,h))
    im.putdata([pal[v] for v in data[a:a+w*h]])
    return im.crop((0,0,s['visible_width'],h))


def ranges(platform,version=None):
    s=layout_spec(platform,version) if version else SPECS[platform]
    w,_=s['size']; x0,y0,x1,y1=s['box']; a=s['offset']+1024
    return [(a+y*w+x0,a+y*w+x1) for y in range(y0,y1)]


def region(data, platform,version=None):
    return b''.join(data[a:z] for a,z in ranges(platform,version))


def restore_legacy_ps2_background(data):
    """Remove only a registered old footer from the unused static background."""
    native=(ROOT/SPECS['PS2']['source']).read_bytes()
    current=region(data,'PS2')
    if current==region(native,'PS2'):return data
    accepted=False
    for path in (ROOT/'work/output').glob('ps2_title_footer_*_verification.json'):
        report=json.loads(path.read_text(encoding='utf8'))
        if version_key(report['version'])>=(0,4,26):continue
        old=report['footer']
        if old.get('target_region_sha256')==sha(current):
            accepted=current==render(native,'PS2',report['version'])[0]
            if accepted:break
    assert accepted,'Unrecognized static background footer; preserve unknown art'
    out=bytearray(data)
    for a,z in ranges('PS2'):out[a:z]=native[a:z]
    return bytes(out)


def render(native, platform, version):
    version_key(version)
    s=layout_spec(platform,version); x0,y0,x1,y1=s['box']; w,h=x1-x0,y1-y0; scale=4
    ink=Image.new('RGBA',(w*scale,h*scale)); draw=ImageDraw.Draw(ink)
    font=ImageFont.truetype(FONT,s['font_size']*scale)
    layouts=[]
    for text,bottom in [('v'+version,h//2),(URL,h)]:
        l,t,r,b=font.getbbox(text,stroke_width=scale)
        assert r-l < w*scale and b-t <= (h//2)*scale, 'Footer text exceeds its slot'
        padding=6 if s.get('panel') else 0
        x=(w-padding)*scale-(r-l); y=(bottom-padding//2)*scale-(b-t)
        draw.text((x-l,y-t),text,font=font,fill=(245,248,255,255),
                  stroke_width=scale,stroke_fill=(8,12,25,255))
        layouts.append(dict(text=text,bounds=[x0+x/scale,y0+y/scale,x1,y0+bottom]))
    tile=picture(native,platform).crop(s['box']).convert('RGBA')
    if s.get('panel'):
        assert tile.getchannel('A').getextrema()==(0,0),'Panel must not cover native logo pixels'
        tile=Image.new('RGBA',(w,h),(4,4,4,255))
    tile.alpha_composite(ink.resize((w,h),Image.Resampling.LANCZOS))
    pal=colors(native,platform); cache={}
    pixels=[]
    for c in tile.getdata():
        if c not in cache:
            cache[c]=min(range(256),key=lambda i:sum((pal[i][j]-c[j])**2 for j in range(3))+3*(pal[i][3]-c[3])**2)
        pixels.append(cache[c])
    return bytes(pixels),layouts


def patch_psp_clear_footer(data, version):
    """Replace only a recognized complete title texture and restore old slots."""
    platform='PSP'; s=layout_spec(platform,version)
    native=(ROOT/s['source']).read_bytes(); w,h=s['size']; o=s['offset']
    pixels,layout=render(native,platform,version)
    spans=ranges(platform,version)
    def texture_for(v):
        expected=bytearray(native[o:o+1024+w*h])
        ink,_=render(native,platform,v)
        for row,(a,z) in enumerate(ranges(platform,v)):
            pitch=z-a
            expected[a-o:z-o]=ink[row*pitch:(row+1)*pitch]
        return bytes(expected)
    actual=data[o:o+1024+w*h]
    accepted=actual in (native[o:o+1024+w*h],texture_for(version))
    if not accepted:
        for p in (ROOT/'work/output').glob('psp_title_footer_*_verification.json'):
            old=json.loads(p.read_text(encoding='utf8'))
            old_version=old['version']
            if sha(region(data,platform,old_version))!=old['footer'].get('target_region_sha256'):
                continue
            if actual==texture_for(old_version):
                accepted=True; break
    assert accepted,'Unknown title artwork: preserve unreviewed pixels'
    # Merge the overlapping old lower-right slot with the new larger slot.
    allowed=[]
    for a,z in sorted(spans+ranges(platform)+ranges(platform,'0.4.27')):
        if allowed and a<=allowed[-1][1]:allowed[-1]=(allowed[-1][0],max(z,allowed[-1][1]))
        else:allowed.append((a,z))
    result=bytearray(data)
    for a,z in allowed:result[a:z]=native[a:z]
    pitch=s['box'][2]-s['box'][0]
    for row,(a,z) in enumerate(spans):result[a:z]=pixels[row*pitch:(row+1)*pitch]
    out=bytes(result)
    assert out[o:o+1024+w*h]==texture_for(version) and len(out)==len(data)
    return out,dict(platform=platform,version=version,credit=URL,asset=s['asset'],
        palette_offset=hex(o),atlas_size=list(s['size']),visible_width=s['visible_width'],
        box=list(s['box']),font='Genei LateGo v2 Medium',font_size=s['font_size'],
        panel=False,lines=layout,pixel_ranges=allowed,
        source_region_sha256=sha(region(data,platform,version)),target_region_sha256=sha(pixels),
        palette_sha256=sha(data[o:o+1024]),source_resource_sha256=sha(data),
        target_resource_sha256=sha(out),palette_preserved=True,
        old_upper_left_panel_removed=True,all_other_pixels_and_data_preserved=True)


def patch(data, platform, version):
    if platform=='PSP' and version_key(version)>=(0,4,29):
        return patch_psp_clear_footer(data,version)
    if platform=='PS2' and version_key(version)>=(0,4,26):
        from ps2_title_footer import patch as native_patch
        result,evidence,_=native_patch(data,version)
        evidence['pixel_ranges']=evidence['byte_ranges']
        evidence.update(source_resource_sha256=sha(data),target_resource_sha256=sha(result))
        return result,evidence
    s=layout_spec(platform,version); native=(ROOT/s['source']).read_bytes(); w,h=s['size']; o=s['offset']
    spans=ranges(platform,version)
    cleanup=ranges(platform) if s.get('panel') else []
    allowed=sorted(spans+cleanup)
    restored=bytearray(data[o:o+1024+w*h])
    for a,z in allowed:restored[a-o:z-o]=native[a:z]
    assert bytes(restored)==native[o:o+1024+w*h], 'Unknown title artwork outside footer'
    current=region(data,platform,version); original=region(native,platform,version)
    pixels,layout=render(native,platform,version)
    accepted=current in (original,pixels)
    if not accepted:
        # Previously stamped candidates are registered by their build reports.
        for p in (ROOT/'work/output').glob(platform.lower()+'_title_footer_*_verification.json'):
            old=json.loads(p.read_text(encoding='utf8'))
            if old['footer'].get('target_region_sha256')==sha(current):
                accepted=current==render(native,platform,old['version'])[0]
                if accepted:break
    assert accepted, 'Unknown existing footer: do not erase unreviewed artwork'
    if cleanup:
        legacy=region(data,platform)
        accepted=legacy==region(native,platform)
        if not accepted:
            for p in (ROOT/'work/output').glob(platform.lower()+'_title_footer_*_verification.json'):
                old=json.loads(p.read_text(encoding='utf8'))
                if version_key(old['version'])>=(0,4,27):continue
                if old['footer'].get('target_region_sha256')==sha(legacy):
                    accepted=legacy==render(native,platform,old['version'])[0]
                    if accepted:break
        assert accepted,'Unrecognized old footer; preserve unknown artwork'
    result=bytearray(data); pitch=s['box'][2]-s['box'][0]
    for a,z in cleanup:result[a:z]=native[a:z]
    for row,(a,z) in enumerate(spans):result[a:z]=pixels[row*pitch:(row+1)*pitch]
    out=bytes(result)
    assert region(out,platform,version)==pixels and len(out)==len(data)
    return out,dict(platform=platform,version=version,credit=URL,asset=s['asset'],
        palette_offset=hex(o),atlas_size=list(s['size']),visible_width=s['visible_width'],
        box=list(s['box']),font='Genei LateGo v2 Medium',font_size=s['font_size'],
        lines=layout,pixel_ranges=allowed,source_region_sha256=sha(current),
        target_region_sha256=sha(pixels),palette_sha256=sha(data[o:o+1024]),
        source_resource_sha256=sha(data),target_resource_sha256=sha(out),
        palette_preserved=True,all_other_pixels_and_data_preserved=True)


def verify_iso(path, platform, version):
    """Read actual disc pixels; do not trust a filename or a manifest alone."""
    version_key(version); s=SPECS[platform]
    native_title=platform=='PS2' and version_key(version)>=(0,4,26)
    asset='/SLPS_253.45;1' if native_title else s['asset']
    iso=pycdlib.PyCdlib();iso.open(str(path))
    try:
        with iso.open_file_from_iso(iso_path=asset) as f:data=f.read()
        if native_title:
            from ps2_title_footer import verify as native_verify
            result=native_verify(data,version)
            with iso.open_file_from_iso(udf_path='/SLPS_253.45') as f:assert f.read()==data
            with iso.open_file_from_iso(iso_path='/DATA/IM.BIN;1') as f:background=f.read()
            assert restore_legacy_ps2_background(background)==background, 'Old footer remains on static background'
            return dict(version=version,credit=URL,actual_iso_footer_verified=True,
                        resource_sha256=sha(data),**result)
        native=(ROOT/s['source']).read_bytes()
        assert region(data,platform,version)==render(native,platform,version)[0], 'Title footer/build version mismatch'
        assert patch(data,platform,version)[0]==data
        if platform=='PS2':
            names=[folder.rstrip('/')+'/'+str(n) for folder,_,files in iso.walk(udf_path='/')
                   for n in files if str(n).lower()==s['asset'].rsplit('/',1)[-1].split(';')[0].lower()]
            assert len(names)==1
            with iso.open_file_from_iso(udf_path=names[0]) as f:assert f.read()==data
        return dict(version=version,credit=URL,actual_iso_pixels_verified=True,resource_sha256=sha(data))
    finally:iso.close()


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('iso',type=Path)
    ap.add_argument('platform',choices=SPECS);ap.add_argument('version');args=ap.parse_args()
    print(json.dumps(verify_iso(args.iso,args.platform,args.version),indent=2))
