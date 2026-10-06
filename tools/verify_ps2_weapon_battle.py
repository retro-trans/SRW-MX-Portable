"""Execute copied flags against dirty stack buffers and both forecast draws."""
import json,struct,unicodedata
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from fix_ps2_weapon_battle import ROOT,BASE,PREVIOUS,VERSION,SOURCE_VERSION,sha
from port_ps2_prologue import save
from verify_ps2_font import machine
from ps2_map_label_pixels import encode,decode

def verify(base=BASE,version=VERSION):
 data=(base/'SLPS_253.45').read_bytes();meta=json.loads((base/'patch.json').read_text())
 c=json.loads((base/'weapon_battle.json').read_text());assert sha(data)==meta['target_sha256']
 before_elf=(PREVIOUS/'SLPS_253.45').read_bytes()
 ranges=[(164,172),(0x100180-0xff000,0x100184-0xff000),(0x100188-0xff000,0x10018c-0xff000)]
 ranges += [(int(row['va'],16)-0xff000,int(row['va'],16)-0xff000+4) for row in c['instruction_words']]
 ranges += [(int(row['va'],16)-0xff000,int(row['va'],16)-0xff000+len(bytes.fromhex(row['new']))) for row in c['storage']]
 last=0
 for a,z in sorted(ranges):
  assert data[last:a]==before_elf[last:a],(last,a)
  last=z
 assert data[last:len(before_elf)]==before_elf[last:] and len(data)>len(before_elf)
 for row in c['instruction_words']:
  assert struct.unpack_from('<I',data,int(row['va'],16)-0xff000)[0]==int(row['new'],16)
 for row in c['storage']:
  a=int(row['va'],16)-0xff000;assert data[a:a+len(bytes.fromhex(row['new']))]==bytes.fromhex(row['new'])
 u=machine(data,r.UC_CPU_MIPS64_MIPS64R2_GENERIC);initial=u.context_save();captured=[];captured_fonts=[]
 def draw(vm,pc,size,user):
  if pc!=0x130610:return
  ptr=vm.reg_read(r.UC_MIPS_REG_A1)
  text=unicodedata.normalize('NFKC',bytes(vm.mem_read(ptr,512)).split(b'\0')[0].decode('cp932'))
  captured.append(dict(english=text,x=vm.reg_read(r.UC_MIPS_REG_A2),y=vm.reg_read(r.UC_MIPS_REG_A3),
                       limit=vm.reg_read(r.UC_MIPS_REG_T0)))
  captured_fonts.append(struct.unpack('<2f',vm.mem_read(vm.reg_read(r.UC_MIPS_REG_A0),8)))
  vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
 u.hook_add(UC_HOOK_CODE,draw)
 flags=[]
 # Execute the actual three-byte copy with a long weapon name still in the
 # stack buffer. Verify it cannot appear in the subsequent draw.
 for address,en in [(0x4c20e8,'A'),(0x4c20f8,'S'),(0x4c20e0,'M'),(0x4c20f0,'G')]:
  for stale in ('Beam Gun','Multiple Missile Launcher'):
   u.context_restore(initial);u.mem_write(0xa00290,it.encode(stale))
   u.reg_write(r.UC_MIPS_REG_V0,address);u.emu_start(0x173444,0x17345c,count=20)
   actual=bytes(u.mem_read(0xa00290,3));assert actual==it.encode(en),(en,actual.hex())
   flags.append(dict(marker=en,previous_buffer=stale,terminated=True))
 widths={g['character']:g['width'] for g in meta['glyphs']};names=[]
 assert sum(widths[x] for x in 'Giganos Sldr.')<=160
 for site,x in zip((0x1799cc,0x17a43c),(345,44)):
  for en in ('Giganos Soldier','Giganos Soldier X','Giganos Guard','Ple Two','Hugo'):
   u.context_restore(initial);captured.clear();u.mem_write(0x910000,it.encode(en))
   for reg,value in [(r.UC_MIPS_REG_A0,0x900000),(r.UC_MIPS_REG_A1,0x910000),
                     (r.UC_MIPS_REG_A2,x),(r.UC_MIPS_REG_A3,164 if site==0x1799cc else 0),
                     (r.UC_MIPS_REG_S2,0x900000),(r.UC_MIPS_REG_T0,0xffffffffffffffff)]:
    u.reg_write(reg,value)
   u.emu_start(site,site+8,count=1000)
   expected='Giganos Sldr.' if en=='Giganos Soldier' else en
   assert captured==[dict(english=expected,x=x,y=164,limit=0xffffffffffffffff)],captured
   assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
   assert bytes(u.mem_read(0x910000,len(it.encode(en))))==it.encode(en)
   names.append(captured[0])
 fitted=[]
 for fw,fh in ((12,24),(24,24)):
  for en in ('Beam Gun','Multiple Missile Launcher','Anti-Air Laser Cannon','Lg. Mega Particle Cannon','Hyper Mega Part. Cannon'):
   for col in (0,1):
    u.context_restore(initial);captured.clear();captured_fonts.clear()
    u.mem_write(0x900000,struct.pack('<2f',fw,fh)+bytes(64));u.mem_write(0x910000,it.encode(en))
    for reg,value in [(r.UC_MIPS_REG_A0,0x900000),(r.UC_MIPS_REG_A1,0x910000),(r.UC_MIPS_REG_A2,42),
                      (r.UC_MIPS_REG_A3,100),(r.UC_MIPS_REG_T0,182),(r.UC_MIPS_REG_S6,col)]:u.reg_write(reg,value)
    u.emu_start(0x17348c,0x173494,count=10000)
    w,h=captured_fonts[0];natural=sum(widths[x] for x in en)
    assert captured[0]['english']==en and captured[0]['x']==42 and captured[0]['limit']==182
    if col==0:
     assert abs(w/fw-h/fh)<0.00001
     assert natural*h/24<=174.0001
     assert abs(captured[0]['y']+h*74/96-(64+fh*74/96))<=0.51
    else:assert (w,h)==(fw,fh) and captured[0]['y']==64
    assert bytes(u.mem_read(0x900000,8))==struct.pack('<2f',fw,fh)
    assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
    fitted.append(dict(english=en,column=col,original_size=[fw,fh],draw_size=[w,h],draw_width=natural*h/24))
 # Run each real integer/float CFont prefix up to its unmodified body. Cases
 # include stack-cached Japanese labels and longer strings that must pass through.
 cached=[]
 for row in c['cached_labels']:
  for jp,en in [('気力','Will'),('クリティカル','Critical'),('武器選択','Weapons'),('気力減少',None),('Ple Two',None)]:
   u.context_restore(initial)
   raw=jp.encode('cp932')+b'\0' if en or jp=='気力減少' else it.encode(jp)
   u.mem_write(0x910000,raw)
   u.reg_write(r.UC_MIPS_REG_A0,0x900000);u.reg_write(r.UC_MIPS_REG_A1,0x910000)
   # Start inside the wrapper to avoid the draw-capture service above.
   u.emu_start(int(row['wrapper'],16),int(row['resume'],16),count=1000)
   actual=bytes(u.mem_read(u.reg_read(r.UC_MIPS_REG_A1),128)).split(b'\0')[0]
   assert actual==(it.encode(en)[:-1] if en else raw[:-1])
   assert bytes(u.mem_read(0x910000,len(raw)))==raw
   cached.append(dict(entry=row['entry'],translated=bool(en),english=en))
 maps=(base/'MAP.BIN').read_bytes();old=(PREVIOUS/'MAP.BIN').read_bytes();m=c['map_caption'];a=int(m['pixel_offset'],16);z=a+m['bytes']
 assert sha(maps)==m['target_map_sha256'] and sha(old)==m['source_map_sha256']
 assert maps[:a]==old[:a] and maps[z:]==old[z:] and len(maps)==len(old)
 assert sha(maps[a:z])==m['target_sha256'] and encode(decode(maps[a:z]))==maps[a:z]
 preserved=[]
 for p in PREVIOUS.iterdir():
  if p.suffix not in ('.BIN','.DAT','.45') or p.name in ('SLPS_253.45','MAP.BIN'):continue
  assert p.read_bytes()==(base/p.name).read_bytes(),p.name;preserved.append(p.name)
 support=json.loads((base/'map_support.json').read_text())
 for row in support['labels']:
  a=int(row['pixel_offset'],16);assert sha(maps[a:a+row['pixel_bytes']])==row['target_sha256']
 save(ROOT/'work/output'/f'ps2_map_support_{version}_verification.json',dict(version=version,
  labels=support['labels'],preserved_from_build=SOURCE_VERSION,
  exact_caption_hashes_preserved=True,additional_map_edits=['M_19 Critical'],visual_validation='asset previews only'))
 result=dict(version=version,passed=True,native_dirty_stack_flag_cases=flags,
  native_forecast_draw_cases=names,native_cached_label_cases=cached,native_weapon_name_cases=fitted,
  forecast_name_width=sum(widths[x] for x in 'Giganos Sldr.'),
  map_image_roundtrip=True,only_critical_pixels_changed=True,preserved_resources=preserved,
  all_previous_support_captions_preserved=True,only_declared_executable_ranges_changed=True,
  visual_validation='in-game confirmation pending',github_release=False)
 save(ROOT/'work/output'/f'ps2_weapon_battle_{version}_execution.json',result);print(json.dumps(result,indent=2));return result

if __name__=='__main__':verify()
