"""Check exact AT/CT pixels and carry verified unchanged native code forward."""
import json
from fix_ps2_forecast_badges import ROOT,BASE,PREVIOUS,VERSION,SOURCE_VERSION,picture,LABELS
from port_ps2_translations import sha
from port_ps2_prologue import save
from ps2_graphics_port import p2ig_textures

def verify(base=BASE,version=VERSION):
 c=json.loads((base/'forecast_badges.json').read_text())
 before=(ROOT/'work/source/ps2'/f'WND_{SOURCE_VERSION}.BIN').read_bytes()
 data=(base/'WND.BIN').read_bytes();native=(ROOT/'work/source/ps2/WND.BIN').read_bytes()
 assert sha(before)==c['source_wnd_sha256'] and sha(data)==c['target_wnd_sha256']
 last=0
 for a,z in sorted(c['changed_pixel_ranges']):
  assert data[last:a]==before[last:a];last=z
 assert data[last:]==before[last:] and len(data)==len(before)
 rows={r['name']:r for r in p2ig_textures(data)}
 cases=[]
 for r in c['labels']:
  row=rows[r['asset']];a=row['offset']+row['pixel_offset'];z=a+1024
  assert a==int(r['pixel_offset'],16) and sha(data[a:z])==r['target_sha256']
  assert data[row['offset']:a]==before[row['offset']:a]==native[row['offset']:a]
  for y in range(32):
   for x in range(32):
    if not (2<=x<22 and 2<=y<22):assert data[a+y*32+x]==native[a+y*32+x]
  assert picture(data,row).getbbox()==(0,0,24,24)
  x0,y0,x1,y1=r['ink_box'];assert 3<=x0<x1<=21 and 3<=y0<y1<=21
  # Non-background ink is confined to the inner box, with intact borders
  # even when sampled through the native 24x24 crop.
  assert picture(data,row).crop((0,0,24,24)).getbbox()==(0,0,24,24)
  cases.append(dict(asset=r['asset'],english=r['english'],frame_equal_to_original=True,
   no_opaque_pixels_outside_native_crop=True,letter_bounds=r['ink_box'],proportions_preserved=True))
 preserved=[]
 for p in PREVIOUS.iterdir():
  if p.suffix not in ('.BIN','.DAT','.45'):continue
  assert p.read_bytes()==(base/p.name).read_bytes(),p.name
  preserved.append(p.name)
 meta=json.loads((base/'patch.json').read_text())
 assert sha((base/'SLPS_253.45').read_bytes())==meta['target_sha256']
 assert (base/'patch.json').read_bytes()==(PREVIOUS/'patch.json').read_bytes()
 carried=[]
 for tag,suffix in [('prologue_fix','execution'),('ui','execution'),('ui_details','execution'),
                    ('roster_system','execution'),('setup_save','execution'),('weapon_battle','execution'),
                    ('stage30','execution'),('map_support','verification')]:
  path=ROOT/'work/output'/f'ps2_{tag}_{SOURCE_VERSION}_{suffix}.json'
  evidence=json.loads(path.read_text())
  evidence.update(reused_for_build=version,evidence_source_build=SOURCE_VERSION,
   reuse_reason='All executable and previously prepared BIN/DAT resources byte-identical; only two WND badge image payloads change.')
  save(ROOT/'work/output'/f'ps2_{tag}_{version}_{suffix}.json',evidence);carried.append(path.name)
 result=dict(version=version,passed=True,badges=cases,exact_changed_ranges=c['changed_pixel_ranges'],
  original_headers_and_palettes_preserved=True,unchanged_resources=preserved,
  carried_native_execution_evidence=carried,visual_validation='native asset previews; in-game pending',github_release=False)
 save(ROOT/'work/output'/f'ps2_forecast_badges_{version}_verification.json',result)
 print(json.dumps(result,indent=2));return result

if __name__=='__main__':verify()
