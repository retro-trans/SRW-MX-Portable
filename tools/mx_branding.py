"""English native title textures and source-preserving copyright captions."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from make_latin_font import FONT

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'work/ui/title_credits_0.4.47'
PSP_PIXELS=ASSETS/'PSP_logo_native.png'
COPYRIGHT=[
    '© ASHI PRODUCTIONS',
    '© GAINAX / Project Eva. / TV Tokyo',
    '© 1997 GAINAX / EVA Production Committee',
    '© SUNRISE / TV Tokyo',
    '© XEBEC / Nadesico Production Committee',
    '© XEBEC / 1998 NADESICO Production Committee',
    '© Sotsu Agency / SUNRISE',
    '© Dynamic Production',
    '© Chimi Moriwo / AIC',
    '© TOEI',
    '© TOHOKUSHINSHA',
    '© 2001 BONES / Yutaka Izubuchi / Rahxephon project',
]


def palette(data,off,platform,alpha=True):
    order=[(v&~24)|((v&8)<<1)|((v&16)>>1) for v in range(256)] if platform=='PS2' else range(256)
    return [tuple(data[off+i*4:off+i*4+3])+(min(255,data[off+i*4+3]*2),) if alpha else tuple(data[off+i*4:off+i*4+3])+(255,) for i in order]


def indexed(image,colors):
    a=np.asarray(image.convert('RGBA')).reshape(-1,4).astype(np.int32)
    pal=np.asarray(colors,np.int32);out=[]
    # Native texture compilation; alpha remains the existing game's palette.
    for start in range(0,len(a),2048):
        delta=a[start:start+2048,None,:]-pal[None,:,:]
        error=(delta*delta*np.array([1,1,1,3])).sum(axis=2)
        out.append(error.argmin(axis=1).astype(np.uint8).tobytes())
    return b''.join(out)


def decoded(raw,w,h,colors):
    im=Image.new('RGBA',(w,h));im.putdata([colors[v] for v in raw]);return im


def logo(platform):
    im=Image.open(ASSETS/f'{platform}_logo_english_master.png').convert('RGBA')
    assert im.getchannel('A').getextrema()==(0,255),'True generated alpha required'
    return im.crop(im.getchannel('A').getbbox())


def prepare():
    data=(ROOT/'work/build/OPWND.orig').read_bytes();off=0x2d3b40
    colors=palette(data,off,'PSP')
    im=Image.new('RGBA',(512,256));im.alpha_composite(logo('PSP').resize((370,171),Image.Resampling.LANCZOS),(0,0))
    raw=indexed(im,colors)
    p=Image.frombytes('P',(512,256),raw);p.putpalette([c for row in colors for c in row[:3]])
    p.save(PSP_PIXELS)
    decoded(raw,512,256,colors).save(ASSETS/'PSP_logo_native_preview.png')
    # Clean source frame precedes the original movie's title lettering.
    clean=Image.open(ASSETS/'PS2_title_clean.png').convert('RGBA')
    clean.alpha_composite(logo('PS2').resize((548,254),Image.Resampling.LANCZOS),(46,8))
    clean.save(ASSETS/'PS2_title_english.png')
    for platform,source,off,w,h,visible in [
        ('PS2','work/source/ps2/IM.BIN',0x298f000,640,448,640),
        ('PSP','work/build/IM_ADD.orig',0x15b9000,512,272,480)]:
        data=(ROOT/source).read_bytes();colors=palette(data,off,platform,alpha=False)
        if platform=='PS2':scene=clean
        else:
            scene=Image.new('RGBA',(w,h),(0,0,0,255))
            scene.alpha_composite(Image.open(ASSETS/'PS2_title_clean.png').convert('RGBA').resize((480,272),Image.Resampling.LANCZOS))
            scene.alpha_composite(logo('PSP').resize((370,171),Image.Resampling.LANCZOS),(55,5))
        raw=indexed(scene,colors)
        p=Image.frombytes('P',(w,h),raw);p.putpalette([c for row in colors for c in row[:3]])
        p.save(ASSETS/f'{platform}_title_native.png')
        decoded(raw,w,h,colors).crop((0,0,visible,h)).save(ASSETS/f'{platform}_title_native_preview.png')
    return dict(PSP=dict(native_size=[512,256],logo_box=[0,0,370,171],palette_preserved=True),
                PS2=dict(native_size=[640,448],logo_box=[46,8,594,262]))


def psp_title_base(native,version):
    if tuple(map(int,version.split('.')))<(0,4,47):return native
    im=Image.open(PSP_PIXELS);assert im.mode=='P' and im.size==(512,256)
    raw=im.tobytes();a=0x2d3f40
    return native[:a]+raw+native[a+len(raw):]


def background(data,platform):
    off=0x15b9000 if platform=='PSP' else 0x298f000
    im=Image.open(ASSETS/f'{platform}_title_native.png');raw=im.tobytes();a=off+1024;z=a+len(raw)
    native=(ROOT/('work/build/IM_ADD.orig' if platform=='PSP' else 'work/source/ps2/IM.BIN')).read_bytes()
    assert data[off:z] in (native[off:z],native[off:a]+raw)
    return data[:a]+raw+data[z:],dict(pixel_ranges=[[a,z]],palette_preserved=True,
        source_sha256=hashlib.sha256(data[a:z]).hexdigest(),target_sha256=hashlib.sha256(raw).hexdigest())


def copyright(data,platform):
    off=0x150c800 if platform=='PSP' else 0x282e800
    w,h,visible,size,pitch=(512,272,480,12,17) if platform=='PSP' else (640,448,640,17,27)
    colors=palette(data,off,platform,alpha=False)
    lines=COPYRIGHT+[f'© BANPRESTO {2005 if platform=="PSP" else 2004}']
    scale=4;font=ImageFont.truetype(FONT,size*scale)
    mask=Image.new('L',(w*scale,h*scale));draw=ImageDraw.Draw(mask);top=(h-pitch*len(lines))//2
    boxes=[]
    for n,text in enumerate(lines):
        l,t,r,b=font.getbbox(text);x=(visible*scale-(r-l))//2;y=(top+n*pitch)*scale
        assert x>=12*scale and x+r-l<=(visible-12)*scale,text
        draw.text((x-l,y-t),text,font=font,fill=255)
        boxes.append(dict(text=text,box=[x/scale,y/scale,(x+r-l)/scale,(y+b-t)/scale]))
    mask=mask.resize((w,h),Image.Resampling.LANCZOS)
    ramp=[min(range(256),key=lambda i:sum((colors[i][c]-value)**2 for c in range(3))) for value in range(256)]
    raw=bytes(ramp[v] for v in mask.tobytes());a=off+1024;z=a+w*h
    native=(ROOT/('work/build/IM_ADD.orig' if platform=='PSP' else 'work/source/ps2/IM.BIN')).read_bytes()
    assert data[off:z] in (native[off:z],native[off:a]+raw),'Unknown copyright artwork'
    out=data[:a]+raw+data[z:]
    decoded(raw,w,h,colors).crop((0,0,visible,h)).save(ASSETS/f'{platform}_copyright_english.png')
    return out,dict(offset=hex(off),pixel_ranges=[[a,z]],palette_preserved=True,lines=boxes,
                    source_sha256=hashlib.sha256(data[a:z]).hexdigest(),target_sha256=hashlib.sha256(raw).hexdigest())


if __name__=='__main__':
    result=prepare()
    for p,source in [('PSP','work/build/IM_ADD.orig'),('PS2','work/source/ps2/IM.BIN')]:
        _,report=copyright((ROOT/source).read_bytes(),p);result[p]['copyright']=report
    (ASSETS/'layout.en.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Prepared native English logo and copyright previews for both platforms')
