"""Local native title-resource investigation (no game-memory mutations)."""
import struct
from pathlib import Path
import pycdlib
from PIL import Image, ImageDraw
from ps2_graphics_port import p2ig_textures, fake_tx48
import redraw_wnd as wnd

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'work/build/ps2_title_footer_test_0.4.26'

def main():
    ram=(DEST/'title_ram.bin').read_bytes()
    rows=p2ig_textures(ram)
    big=[r for r in rows if r['width']>=256 and r['height']>=128]
    canvas=Image.new('RGB',(640,((len(big)+3)//4)*128),(30,30,30))
    draw=ImageDraw.Draw(canvas)
    for n,r in enumerate(big):
        fake=fake_tx48(ram,r);pal,(kind,w,h,off)=wnd.palette(fake,0)
        raw=fake[off:]
        if kind==0: raw=bytes(v for b in raw for v in (b&15,b>>4))
        im=Image.new('RGBA',(w,h));im.putdata([pal[v] for v in raw[:w*h]])
        im.thumbnail((158,105));x=(n%4)*160;y=(n//4)*128
        canvas.paste(im.convert('RGB'),(x,y))
        draw.text((x,y+106),hex(r['offset'])+' '+r['name'][:10],fill='white')
    canvas.save(DEST/'ram_textures.png')
    print('Large native RAM textures:',len(big))
    # Detect contiguous loaded source pages; this also identifies stripped headers.
    iso=pycdlib.PyCdlib();iso.open(str(ROOT/'Super Robot Taisen MX (Japan).iso'))
    for name in ('IM.BIN','D2MAP.BIN','STATIC.BIN','STRM.BIN'):
        length=iso.get_record(iso_path='/DATA/'+name+';1').data_length
        with iso.open_file_from_iso(iso_path='/DATA/'+name+';1') as f:
            data=f.read(min(length,40*1024*1024))
        matches=[]
        for off in range(0,len(data)-512,2048):
            key=data[off:off+512]
            if len(set(key))<32:continue
            at=ram.find(key)
            if at>=0:matches.append((hex(off),hex(at)))
        print(name,matches[:40], 'count',len(matches),flush=True)
    iso.close()

if __name__=='__main__':main()
