"""Edit original PS2 card and P2IG UI pixels; no emulator replacements."""
import json
import struct
from PIL import Image
import patch_chapter_cards as cards
import redraw_wnd as wnd
from port_ps2_translations import ROOT,read_json,sha


def logical_palette(palette):
    assert len(palette)==1024
    return b''.join(palette[(v&~24|((v&8)<<1)|((v&16)>>1))*4:
                           (v&~24|((v&8)<<1)|((v&16)>>1))*4+4] for v in range(256))


def chapter_cards(original):
    rows=read_json(ROOT/'work/source/ps2/chapter_mapping.json')['matched']
    for off in (0x2f20400,0x2f51c00,0x4261c00):
        rows.append(dict(pixel_offset=off,english='Hades Sorties at Dawn',needs_translation=True,
                         palette_sha256=sha(original[off-1024:off]),title_sha256=sha(original[off:off+52*256])))
    rows.sort(key=lambda r:r['pixel_offset']);assert len(rows)==198
    assert len(set(r['english'] for r in rows))==66
    output=bytearray(original);allowed=[];results=[];masks={}
    preview=ROOT/'work/ui/ps2/cards_english';preview.mkdir(parents=True,exist_ok=True)
    for n,row in enumerate(rows):
        off=row['pixel_offset'];pal=original[off-1024:off]
        assert sha(pal)==row['palette_sha256']
        assert sha(original[off:off+52*256])==row['title_sha256']
        result=dict(pixel_offset=off,english=row['english'],translated=row['needs_translation'])
        if row['needs_translation']:
            mask,layout=masks.setdefault(row['english'],cards.render_title(row['english']))
            encoded=cards.indexed_title(mask,logical_palette(pal));output[off:off+len(encoded)]=encoded
            allowed.append((off,off+len(encoded)));result.update(layout)
            im=Image.new('RGBA',(256,52));lp=logical_palette(pal)
            im.putdata([tuple(lp[v*4:v*4+3])+(min(255,lp[v*4+3]*2),) for v in encoded]);im.save(preview/f'{n:03}.png')
        results.append(result)
    last=0
    for a,z in allowed:assert output[last:a]==original[last:a];last=z
    assert output[last:]==original[last:] and len(output)==len(original)
    return bytes(output),dict(scenario_titles=66,title_atlases=198,translated_atlases=153,
                             native_english_atlases_preserved=45,palettes_preserved=True,
                             non_title_pixels_preserved=True,cards=results,target_sha256=sha(output))


def p2ig_textures(data):
    rows=[];position=0
    while (position:=data.find(b'P2IG',position))>=0:
        if position+128>len(data):break
        wl,hl=struct.unpack_from('<2H',data,position+32);psm=struct.unpack_from('<I',data,position+36)[0]
        pa,ps,px,ns=struct.unpack_from('<4I',data,position+64)
        if wl<=11 and hl<=11 and psm in (19,20) and ps==(1024 if psm==19 else 64) and px+ns+position<=len(data):
            rows.append(dict(offset=position,name=data[position+16:position+24].split(b'\0')[0].decode('cp932',errors='replace'),
                             width=1<<wl,height=1<<hl,psm=psm,palette_offset=pa,palette_bytes=ps,pixel_offset=px,pixel_bytes=ns))
        position+=4
    return rows


def fake_tx48(data,row):
    off=row['offset'];pal=data[off+row['palette_offset']:off+row['palette_offset']+row['palette_bytes']]
    if row['psm']==19:pal=logical_palette(pal)
    px=data[off+row['pixel_offset']:off+row['pixel_offset']+row['pixel_bytes']]
    header=b'TX48'+struct.pack('<7I',1 if row['psm']==19 else 0,row['width'],row['height'],32,len(pal),32+len(pal),len(px))
    return header+pal+px


def redraw_forecast_badge(fake,text):
    """Native AT/CT tiles are 24x24 inside a padded 32x32 texture."""
    assert text in ('AT','CT')
    pal,(kind,w,h,offset)=wnd.palette(fake,0)
    assert (kind,w,h)==(1,32,32)
    raw=fake[offset:offset+w*h]
    visible=Image.new('L',(w,h));visible.putdata([255 if pal[v][3] else 0 for v in raw])
    assert visible.getbbox()==(0,0,24,24)
    cap=12
    while wnd.render_text(text,cap,1000).width>18:cap-=1
    assert cap>=10
    boxes=wnd.BOXES
    try:
        wnd.BOXES={**boxes,'small':(2,2,22,22,cap)}
        pixels,_,_=wnd.redraw(fake,0,text,'small')
    finally:wnd.BOXES=boxes
    mask=wnd.render_text(text,cap,1000)
    ox=2+(20-mask.width)//2;oy=2+(20-mask.height)//2
    return pixels,dict(cap_height=cap,ink_box=[ox,oy,ox+mask.width,oy+mask.height],
                       visible_box=[0,0,24,24],inner_box=[2,2,22,22],horizontal_rescaling=False)


def window_graphics(original):
    rows=p2ig_textures(original);by_name={r['name']:r for r in rows};output=bytearray(original);results=[];ranges=[]
    entries=read_json(ROOT/'work/translation/en/ui/textures.json')['WND.BIN']
    # Most icons use doubled PSP boxes; AT/CT use their native 24px bounds.
    mapping={50:'IM_IC00',51:'IM_IC01',52:'IM_IC02',53:'IM_IC03',54:'IM_IC04',55:'IM_IC05',
             57:'IM_IC07',59:'IM_IC08',60:'IM_IC09',61:'IM_IC10',63:'IM_IC12',
             84:'IM_IC26',85:'IM_IC27',90:'IM_IC00S',91:'IM_IC01S',92:'IM_IC02S',
             93:'IM_IC03S',94:'IM_IC04S',95:'IM_IC05S',97:'IM_IC26S',98:'IM_IC27S'}
    boxes=dict(wnd.BOXES)
    try:
        wnd.BOXES={k:tuple(v*2 for v in box) for k,box in boxes.items()}
        for key,name in mapping.items():
            row=by_name[name];assert row['psm']==19
            entry=entries[str(key)];kind=wnd.kind_of(entry);text=entry.get('en_icon') or entry['en']
            fake=fake_tx48(original,row)
            if name in ('IM_IC00S','IM_IC01S'):
                px,_=redraw_forecast_badge(fake,text)
            else:px,_,pal=wnd.redraw(fake,0,text,kind)
            offset=row['offset']+row['pixel_offset'];output[offset:offset+len(px)]=px;ranges.append((offset,offset+len(px)))
            results.append(dict(asset=name,english=text,kind=kind))
    finally:wnd.BOXES=boxes
    row=by_name['IM_W00_0'];fake=fake_tx48(original,row)
    entry=dict(en='INTERMISSION',native_text_box=[10,4,202,32],native_text_origin=[18,6],native_cap_height=22,native_background_index=1)
    px,_,pal=wnd.redraw_header(fake,0,entry);offset=row['offset']+row['pixel_offset'];output[offset:offset+len(px)]=px
    ranges.append((offset,offset+len(px)));results.append(dict(asset=row['name'],english=entry['en'],kind='header'))
    preview=ROOT/'work/ui/ps2/wnd_english';preview.mkdir(parents=True,exist_ok=True)
    for result in results:
        row=by_name[result['asset']];fake=fake_tx48(output,row);palette,(_,w,h,px)=wnd.palette(fake,0)
        im=Image.new('RGBA',(w,h));im.putdata([palette[v][:3]+(min(255,palette[v][3]*2),) for v in fake[px:px+w*h]])
        im.save(preview/(row['name']+'.png'))
    last=0
    for a,z in sorted(ranges):assert output[last:a]==original[last:a];last=z
    assert output[last:]==original[last:] and len(output)==len(original)
    return bytes(output),dict(native_pixel_edits=results,palettes_and_headers_preserved=True,target_sha256=sha(output))


if __name__=='__main__':
    reports={}
    for name,patch in [('PACKMAPC.BIN',chapter_cards),('WND.BIN',window_graphics)]:
        data,report=patch((ROOT/'work/source/ps2'/name).read_bytes())
        (ROOT/'work/build/ps2/campaign'/name).write_bytes(data);reports[name]=report
    (ROOT/'work/translation/en/ps2/graphics_port.en.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf8')
    print({k:{n:v for n,v in r.items() if n not in ('cards','native_pixel_edits')} for k,r in reports.items()})
