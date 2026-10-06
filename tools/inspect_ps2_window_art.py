from ps2_graphics_port import *
from PIL import ImageDraw
d=(ROOT/'work/source/ps2/WND.BIN').read_bytes()
rows=[r for r in p2ig_textures(d) if r['name'].startswith(('IM_FW','IM_W0','IM_W1','WIN_SUB'))]
im=Image.new('RGB',(1024,sum(r['height']+24 for r in rows)),(20,20,20))
y=0;dr=ImageDraw.Draw(im)
for r in rows:
    dr.text((0,y),r['name'],fill='white');y+=24
    fake=fake_tx48(d,r);pal,(_,w,h,off)=wnd.palette(fake,0)
    px=fake[off:off+r['pixel_bytes']]
    if r['psm']==20:px=bytes(v for b in px for v in (b&15,b>>4))
    pic=Image.new('RGBA',(w,h));pic.putdata([pal[v][:3]+(min(255,pal[v][3]*2),) for v in px[:w*h]])
    im.paste(pic,(0,y),pic);y+=h
im.save(ROOT/'work/ui/ps2/roster_asset_inventory.png')
