"""Fit the native AT/CT forecast badges to their actual 24-pixel crop."""
import argparse,json,shutil
from PIL import Image,ImageDraw
import pycdlib
import redraw_wnd as wnd
from ps2_graphics_port import p2ig_textures,fake_tx48,redraw_forecast_badge
from port_ps2_translations import ROOT,sha
from port_ps2_prologue import save

VERSION='0.1.17';SOURCE_VERSION='0.1.16'
BASE=ROOT/'work/build/ps2'/f'forecast_badges_{VERSION}'
PREVIOUS=ROOT/'work/build/ps2'/f'weapon_battle_{SOURCE_VERSION}'
LABELS={'IM_IC00S':'AT','IM_IC01S':'CT'}

def picture(raw,row):
 pal,(kind,w,h,offset)=wnd.palette(fake_tx48(raw,row),0)
 pixels=raw[row['offset']+row['pixel_offset']:row['offset']+row['pixel_offset']+row['pixel_bytes']]
 im=Image.new('RGBA',(w,h))
 im.putdata([pal[v][:3]+(min(255,pal[v][3]*2),) for v in pixels])
 return im

def prepare():
 BASE.mkdir(parents=True,exist_ok=True)
 for p in PREVIOUS.iterdir():
  if p.suffix in ('.BIN','.DAT','.45','.json'):shutil.copyfile(p,BASE/p.name)
 original=(ROOT/'work/source/ps2/WND.BIN').read_bytes()
 source=ROOT/'work/source/ps2'/f'WND_{SOURCE_VERSION}.BIN'
 report=json.loads((ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json').read_text())
 if not source.exists():
  iso=pycdlib.PyCdlib();iso.open(str(ROOT/report['output']))
  iso.get_file_from_iso(local_path=str(source),iso_path='/DATA/WND.BIN;1');iso.close()
 prior=source.read_bytes()
 expected=next(x for x in report['files'] if x['path']=='/DATA/WND.BIN;1')
 assert sha(prior)==expected['target_sha256'] and sha(original)==expected['original_sha256']
 data=bytearray(prior);rows={r['name']:r for r in p2ig_textures(prior)}
 native={r['name']:r for r in p2ig_textures(original)}
 out=ROOT/'work/ui/ps2'/f'forecast_badges_{VERSION}';out.mkdir(parents=True,exist_ok=True)
 # Screenshot evidence is separate from editable native disc data.
 shutil.copy2('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-1d0132ac-a18d-47d2-aeb2-044bc5e8a096.png',out/'user_before.png')
 sheet=Image.new('RGB',(512,2*154),(25,25,25));draw=ImageDraw.Draw(sheet)
 records=[]
 for i,(name,text) in enumerate(LABELS.items()):
  row=rows[name];nr=native[name]
  assert row==nr and (row['width'],row['height'],row['psm'],row['pixel_bytes'])==(32,32,19,1024)
  a=row['offset']+row['pixel_offset'];z=a+row['pixel_bytes'];fake=fake_tx48(original,nr)
  pal,(kind,w,h,pixel)=wnd.palette(fake,0);old_pixels=fake[pixel:pixel+w*h]
  # The 32-pixel texture contains a 24-pixel opaque frame, plus padding.
  assert picture(original,nr).getbbox()==(0,0,24,24)
  pixels,layout=redraw_forecast_badge(fake,text);cap=layout['cap_height']
  # Restore frame and transparent padding from the original asset, rather
  # than preserving the previous overlarge edit which erased the frame.
  for y in range(32):
   for x in range(32):
    if not (2<=x<22 and 2<=y<22):assert pixels[y*32+x]==old_pixels[y*32+x]
  before=picture(prior,row);data[a:z]=pixels;after=picture(data,row)
  mask=wnd.render_text(text,cap,1000)
  ox=2+(20-mask.width)//2;oy=2+(20-mask.height)//2
  records.append(dict(asset=name,english=text,pixel_offset=hex(a),pixel_bytes=1024,
   source_sha256=sha(prior[a:z]),target_sha256=sha(pixels),native_original_sha256=sha(old_pixels),
   texture_size=[32,32],visible_box=[0,0,24,24],inner_box=[2,2,22,22],
   ink_box=[ox,oy,ox+mask.width,oy+mask.height],cap_height=cap,horizontal_rescaling=False,
   frame_and_padding_restored=True))
  before.save(out/f'{name}_before.png');after.save(out/f'{name}_after.png')
  draw.text((0,i*154),text+' before / after (native asset preview)',fill='white')
  for pic,x in ((before,0),(after,256)):
   pic=pic.resize((128,128),Image.Resampling.NEAREST);sheet.paste(pic,(x,i*154+20),pic)
 sheet.save(out/'badges_before_after.png')
 (BASE/'WND.BIN').write_bytes(data)
 changes=dict(version=VERSION,source_build=SOURCE_VERSION,labels=records,
  source_wnd_sha256=sha(prior),target_wnd_sha256=sha(data),
  changed_pixel_ranges=[[int(r['pixel_offset'],16),int(r['pixel_offset'],16)+1024] for r in records],
  executable_and_other_resources_unchanged=True,headers_palettes_and_uvs_unchanged=True,
  native_pixel_edits=True,texture_replacement=False,github_release=False,
  visual_validation='native asset previews checked; in-game confirmation pending')
 save(BASE/'forecast_badges.json',changes)
 save(ROOT/'work/translation/en/ps2'/f'forecast_badges_{VERSION}.en.json',changes)
 save(out/'source_capture.json',dict(version=VERSION,source='user screenshot of actual game',
  screenshot='user_before.png',native_badge_size=[24,24],native_texture_size=[32,32],
  issue='Letters extended past the sampled badge area; lower/right frame erased',
  assets=records,new_gameplay_capture=False))
 return changes

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');args=p.parse_args()
 prepare()
 from verify_ps2_forecast_badges import verify
 verify()
 if args.build:
  from package_ps2_stage30 import build
  build(BASE,VERSION,SOURCE_VERSION,extra_files=('WND.BIN',))
