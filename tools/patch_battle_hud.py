"""Translate the separate, untagged battle HUD atlas on both editions."""
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from patch_at_field import ROOT, SPECS, palette, sha

VERSION = '0.4.22'
ICON_TERMS = [('ST','Pilot stats reduced'),('WP','Weapon accuracy reduced'),
              ('MB','Mobility reduced'),('AR','Armor reduced'),
              ('DS','Cannot act'),('MV','Movement reduced')]
SMALL_GLYPHS = {
    'S':['01111','10000','10000','01110','00001','00001','11110'],
    'T':['11111','00100','00100','00100','00100','00100','00100'],
    'W':['10001','10001','10001','10101','10101','10101','01010'],
    'P':['11110','10001','10001','11110','10000','10000','10000'],
    'M':['10001','11011','10101','10101','10001','10001','10001'],
    'B':['11110','10001','10001','11110','10001','10001','11110'],
    'A':['01110','10001','10001','11111','10001','10001','10001'],
    'R':['11110','10001','10001','11110','10100','10010','10001'],
    'D':['11110','10001','10001','10001','10001','10001','11110'],
    'V':['10001','10001','10001','10001','10001','01010','00100'],
}


def regions(platform):
    if platform=='PSP':
        rows=[dict(id='will_left',text='Will',box=[2,106,18,116],cap=7,style='badge'),
              dict(id='will_right',text='Will',box=[106,106,122,116],cap=7,style='badge'),
              dict(id='defend',text='Defend',box=[168,152,212,176],cap=18,style='caption')]
        for i,(text,meaning) in zip([0,1,2,3,4,6],ICON_TERMS):
            rows.append(dict(id='status_'+text,text=text,meaning=meaning,
                             box=[16*i+1,89,16*i+14,101],cap=7,style='badge'))
    else:
        rows=[dict(id='will_left',text='Will',box=[50,186,74,198],cap=9,style='badge'),
              dict(id='will_right',text='Will',box=[194,186,218,198],cap=9,style='badge'),
              dict(id='defend',text='Defend',box=[168,152,212,176],cap=18,style='caption')]
        for i,(text,meaning) in zip([0,1,2,3,4,6],ICON_TERMS):
            rows.append(dict(id='status_'+text,text=text,meaning=meaning,
                             box=[24*i+2,50,24*i+19,67],cap=9,style='badge'))
    return rows


def mask_for(text,cap,width,height):
    for size in range(cap,4,-1):
        scale=8; font=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',size*scale*14//10)
        font.set_variation_by_name(b'Bold Condensed')
        bounds=font.getbbox(text);im=Image.new('L',(bounds[2]-bounds[0]+8,bounds[3]-bounds[1]+8))
        ImageDraw.Draw(im).text((4-bounds[0],4-bounds[1]),text,font=font,fill=255)
        im=im.crop(im.getbbox());w=round(im.width*size/im.height)
        if w<=width and size<=height:
            return im.resize((w,size),Image.Resampling.LANCZOS),size
    raise ValueError('Text does not fit '+text)


def picture(data,platform):
    s=SPECS[platform];w,h=s['size'];pal=palette(data,platform)
    im=Image.new('RGBA',(w,h));im.putdata([pal[v] for v in data[s['pixels']:s['pixels']+w*h]])
    return im


def render(old,pal,row):
    x0,y0,x1,y1=row['box'];w=x1-x0;h=y1-y0
    if row['id'].startswith('status_'):
        # Seven native pixels need distinct stems and counters. A sharp 5x7
        # Latin bitmap avoids anti-aliasing joining W/P at this tiny size.
        mask=Image.new('L',(len(row['text'])*6-1,7))
        for i,letter in enumerate(row['text']):
            for y,line in enumerate(SMALL_GLYPHS[letter]):
                for x,v in enumerate(line):
                    if v=='1':mask.putpixel((i*6+x,y),255)
        cap=row['cap'];mask=mask.resize((round(mask.width*cap/7),cap),Image.Resampling.NEAREST)
        assert mask.width<=w-2 and mask.height<=h-2
    else:mask,cap=mask_for(row['text'],row['cap'],w-2,h-2)
    ox=(w-mask.width)//2;oy=(h-mask.height)//2
    ink=Image.new('L',(w,h));ink.paste(mask,(ox,oy))
    if row['style']=='caption':
        art=Image.new('RGBA',(w,h));outline=ink.filter(ImageFilter.MaxFilter(3))
        art.paste((0,0,0,255),(0,0,w,h),outline)
        shadow=Image.new('L',(w,h));shadow.paste(ink,(1,1))
        art.paste((0,0,255,255),(0,0,w,h),shadow)
        art.paste((255,255,255,255),(0,0,w,h),ink)
    else:
        ring=[old[y*w+x] for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)]
        bg=max(set(ring),key=ring.count)
        if row['id'].startswith('status_'):
            red=[i for i in set(old) if pal[i][0]>2*max(pal[i][1],pal[i][2])]
            assert red
            bg=max(red,key=old.count)
        body=max(set(old),key=lambda i:sum(pal[i][:3]));dark=min(set(old),key=lambda i:sum(pal[i][:3]))
        art=Image.new('RGBA',(w,h),pal[bg]);outline=ink.filter(ImageFilter.MaxFilter(3))
        art.paste(pal[dark],(0,0,w,h),outline);art.paste(pal[body],(0,0,w,h),ink)
    cache={}
    def nearest(color):
        if color not in cache:
            cache[color]=min(range(256),key=lambda i:sum((pal[i][j]-color[j])**2 for j in range(4)))
        return cache[color]
    return bytes(nearest(c) for c in art.getdata()),dict(cap_height=cap,ink_bounds=[x0+ox,y0+oy,x0+ox+mask.width,y0+oy+mask.height],horizontal_rescaling=False)


def patch(data,platform,preview=None):
    s=SPECS[platform];w,h=s['size'];off=s['pixels'];pal=palette(data,platform)
    native=(ROOT/('work/build/STATIC2_ADD.orig' if platform=='PSP' else 'work/source/ps2/STATIC.BIN')).read_bytes()
    assert data[s['palette']:s['palette']+1024]==native[s['palette']:s['palette']+1024]
    out=bytearray(data);allowed=[];reports=[]
    for row in regions(platform):
        x0,y0,x1,y1=row['box']
        def crop(d):return b''.join(d[off+y*w+x0:off+y*w+x1] for y in range(y0,y1))
        old=crop(data);original=crop(native);new,layout=render(original,pal,row)
        assert old in (original,new), 'Unknown revised artwork: '+row['id']
        for i,y in enumerate(range(y0,y1)):
            a=off+y*w+x0;z=a+x1-x0;out[a:z]=new[i*(x1-x0):(i+1)*(x1-x0)];allowed.append([a,z])
        reports.append(dict(**row,**layout,source_pixel_sha256=sha(original),target_pixel_sha256=sha(new),already_translated=old==new))
    last=0
    for a,z in sorted(allowed):assert out[last:a]==data[last:a];last=z
    assert out[last:]==data[last:] and len(out)==len(data)
    evidence=dict(platform=platform,regions=reports,pixel_ranges=sorted(allowed),palette_preserved=True,
        source_resource_sha256=sha(data),target_resource_sha256=sha(out),all_other_pixels_and_bytes_preserved=True)
    if preview:
        preview.mkdir(parents=True,exist_ok=True)
        for label,d in [('before',data),('english',out)]:
            pic=picture(d,platform);bg=Image.new('RGBA',pic.size,(40,40,40,255));bg.alpha_composite(pic)
            bg.convert('RGB').resize((w*2,h*2),Image.Resampling.NEAREST).save(preview/f'atlas_{label}.png')
        sheet=Image.new('RGB',(400,30+len(reports)*80),(40,40,40));draw=ImageDraw.Draw(sheet)
        draw.text((0,0),'Original',fill='white');draw.text((200,0),'English',fill='white')
        for i,r in enumerate(reports):
            for x,d in [(0,data),(200,out)]:
                pic=picture(d,platform).crop(r['box']);bg=Image.new('RGBA',pic.size,(40,40,40,255));bg.alpha_composite(pic)
                sheet.paste(bg.convert('RGB').resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST),(x,30+i*80))
        sheet.save(preview/'before_after.png')
        (preview/'layout.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
    return bytes(out),evidence


if __name__=='__main__':
    for p in ('PSP','PS2'):
        native=(ROOT/('work/build/STATIC2_ADD.orig' if p=='PSP' else 'work/source/ps2/STATIC.BIN')).read_bytes()
        _,r=patch(native,p,ROOT/'work/ui'/p.lower()/f'battle_hud_{VERSION}')
        print(p,[(x['text'],x['cap_height'],x['ink_bounds']) for x in r['regions']])
