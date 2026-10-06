"""Execute native save/setup branches and every series selector title."""
import json,struct,unicodedata
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from fix_ps2_setup_save import ROOT,BASE,VERSION,PREVIOUS,PAIRS,sha
from port_ps2_prologue import save
from verify_ps2_font import machine

def verify(base=BASE,version=VERSION):
 data=(base/'SLPS_253.45').read_bytes();meta=json.loads((base/'patch.json').read_text())
 c=json.loads((base/'setup_save.json').read_text());assert sha(data)==meta['target_sha256']
 def off(va):
  for n in range(struct.unpack_from('<H',data,44)[0]):
   k,o,a,_,size,*_=struct.unpack_from('<8I',data,52+n*32)
   if k==1 and a<=va<a+size:return o+va-a
  raise AssertionError(hex(va))
 def raw(va):
  o=off(va);return data[o:data.index(0,o)]
 widths={g['character']:g['width'] for g in meta['glyphs']}
 def width(text):return sum(widths[x] for x in text)
 for row in c['strings']:assert raw(int(row['target'],16))==it.encode(row['english'])[:-1]
 for row in c['data_references']:
  ptr=struct.unpack_from('<I',data,off(int(row['site'],16)))[0]
  assert ptr==int(row['target'],16) and raw(ptr)==it.encode(row['english'])[:-1]
 for row in c['instruction_words']:assert struct.unpack_from('<I',data,off(int(row['va'],16)))[0]==int(row['new'],16)
 for row in c['storage']:assert data[off(int(row['va'],16)):off(int(row['va'],16))+8]==bytes.fromhex(row['new'])
 u=machine(data,r.UC_CPU_MIPS64_MIPS64R2_GENERIC);initial=u.context_save();draws=[];selection=0
 def text(vm,ptr):return unicodedata.normalize('NFKC',bytes(vm.mem_read(ptr,512)).split(b'\0')[0].decode('cp932'))
 def hook(vm,pc,size,user):
  if pc in (0x131958,0x169a10,0x336690,0x3366f0,0x36ae10):
   if pc==0x169a10:vm.reg_write(r.UC_MIPS_REG_V0,selection)
   elif pc in (0x336690,0x3366f0):vm.mem_write(vm.reg_read(r.UC_MIPS_REG_A1),it.encode('Hugo Medio' if pc==0x336690 else 'Aqua Centrum'))
   elif pc==0x36ae10:vm.mem_write(vm.reg_read(r.UC_MIPS_REG_A0),it.encode('Hugo' if selection==0 else 'Aqua'))
   vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA));return
  if pc==0x130610:
   ctx=vm.reg_read(r.UC_MIPS_REG_A0)
   draws.append(dict(english=text(vm,vm.reg_read(r.UC_MIPS_REG_A1)),x=vm.reg_read(r.UC_MIPS_REG_A2),
                     y=vm.reg_read(r.UC_MIPS_REG_A3),font=list(struct.unpack('<2f',vm.mem_read(ctx,8))),
                     color_limit=vm.reg_read(r.UC_MIPS_REG_T0)))
   vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
 u.hook_add(UC_HOOK_CODE,hook)
 def reset():
  u.context_restore(initial);draws.clear();u.mem_write(0x940000,bytes(0x4000))
  u.mem_write(0x94009c,struct.pack('<2I',15,40))
  u.mem_write(0x941000,struct.pack('<2f',24,24)+bytes(64))
  u.reg_write(r.UC_MIPS_REG_GP,0x4c84f0)
  u.reg_write(r.UC_MIPS_REG_S0,0x940000);u.reg_write(r.UC_MIPS_REG_S2,0x941000)
 # Actual protagonist header setup reaches the native header routine.
 reset();u.reg_write(r.UC_MIPS_REG_S0,0x940000)
 u.emu_start(0x16a670,0x143ac0,count=20)
 assert text(u,u.reg_read(r.UC_MIPS_REG_A1))=='Protagonist Setup'
 # Local save strings: execute real argument setup and native GS call or
 # native line registration. Progress bars and save-state control are intact.
 branches=[]
 ends={0x49d4f0:0x197460,0x49d530:0x197484,0x49d460:0x196ea0,0x49d4a0:0x196ec4,
       0x4a5c68:0x25d064,0x4a5ca0:0x25d078,0x4a9108:0x2c0874,0x4a9148:0x2c08d4,
       0x4a5fa8:0x25df48}
 for source,(high,low) in PAIRS.items():
  if source==0x4975a8:continue
  reset();u.reg_write(r.UC_MIPS_REG_S1,0x940000)
  if source in (0x4a5c68,0x4a5ca0,0x4a9108,0x4a9148):u.reg_write(r.UC_MIPS_REG_S0,0x940000)
  u.emu_start(high,ends[source],count=2000)
  expected=next(row['english'] for row in c['strings'] if int(row['source'],16)==source)
  if draws:
   assert len(draws)==1 and draws[0]['english']==expected,(hex(source),draws)
   assert draws[0]['x']+width(expected)<=15+500,(hex(source),draws)
   branches.append(dict(source=hex(source),draw=draws[0]))
  else:
   ptr=struct.unpack('<I',u.mem_read(0x940220,4))[0]
   assert text(u,ptr)==expected,(hex(source),hex(ptr))
   assert struct.unpack('<H',u.mem_read(0x940204,2))[0]==1
   branches.append(dict(source=hex(source),registered=expected))
 # Actual yes/no initializer: both positions must have the same left edge.
 reset();u.reg_write(r.UC_MIPS_REG_A0,0x940000);u.emu_start(0x151ea8,0x920000,count=50)
 yes,no=struct.unpack('<2I',u.mem_read(0x940200,8));assert yes==no==26
 assert text(u,struct.unpack('<I',u.mem_read(0x940208,4))[0])=='Yes'
 assert text(u,struct.unpack('<I',u.mem_read(0x94020c,4))[0])=='No'
 # Name/nickname/age value loop for both protagonists, using real native age
 # copies, all branches and fixed value X. String getter services supply names.
 names=[]
 for selection in (0,1):
  reset();u.mem_write(0x94026c,struct.pack('<I',selection))
  u.mem_write(0x9401f8,struct.pack('<2f',24,24)+bytes(64))
  u.reg_write(r.UC_MIPS_REG_S1,0x9401f8);u.reg_write(r.UC_MIPS_REG_A0,0x940000)
  u.emu_start(0x16a268,0x16a39c,count=4000)
  assert [d['english'] for d in draws]==(['Hugo Medio','Hugo','20'] if selection==0 else ['Aqua Centrum','Aqua','23'])
  assert all(d['x']==155 for d in draws)
  assert 15+54+width('Name')+8<=155
  names.append(dict(protagonist=selection,draws=list(draws)))
 # Six actual description rows, no Japanese suffixes or clipped portrait.
 descriptions=[]
 for selection,row in enumerate(c['description_tables']):
  reset();u.reg_write(r.UC_MIPS_REG_S1,0x941000)
  u.reg_write(r.UC_MIPS_REG_S2,0x497610);u.reg_write(r.UC_MIPS_REG_S3,0x497628)
  u.reg_write(r.UC_MIPS_REG_S4,5);u.reg_write(r.UC_MIPS_REG_S5,0)
  u.emu_start(0x16a940,0x16a990,count=3000)
  assert [d['english'] for d in draws]==row['lines'],(row,draws)
  for i,d in enumerate(draws):
   assert d['x']==43 and d['y']==100+i*26
   assert width(d['english'])<=300 and d['x']+width(d['english'])<=343
  descriptions.append(dict(unit=row['unit'],draws=list(draws)))
 # Final setup confirmation copies two original 16-byte descriptors and
 # draws their repointed text without changing selected-button behavior.
 confirmations=[]
 for chosen in (0,1):
  reset();u.reg_write(r.UC_MIPS_REG_S2,0x940000);u.reg_write(r.UC_MIPS_REG_V0,0x4a0000)
  u.emu_start(0x195410,0x195454,count=50)
  u.mem_write(0x9402cc,struct.pack('<I',chosen));u.mem_write(0x940190,struct.pack('<2f',24,24)+bytes(64))
  u.reg_write(r.UC_MIPS_REG_S5,0x940190);u.reg_write(r.UC_MIPS_REG_S7,0xa00004);u.reg_write(r.UC_MIPS_REG_S6,0xa00008)
  u.emu_start(0x195538,0x1955d4,count=1000)
  assert [d['english'] for d in draws]==['Change Settings','Finish Setup']
  assert [d['x'] for d in draws]==[107,411] and all(d['y']==368 for d in draws)
  assert draws[0]['x']+width(draws[0]['english'])+8<draws[1]['x']
  assert struct.unpack('<I',u.mem_read(0x9402cc,4))[0]==chosen
  confirmations.append(dict(selected=chosen,draws=list(draws)))
 # Execute the title wrapper for all 18 original series entries, varying
 # context sizes and window origin. Long and Japanese fallback cases exercise
 # uniform fitting, baseline preservation and the bounded box.
 titles=[]
 pointers=struct.unpack_from('<18I',data,off(0x470d38))
 for ptr in (*pointers,0x910000,0x910100):
  for fw,fh in ((24,24),(20,30)):
   reset();u.mem_write(0x910000,it.encode('A very long series title '*4));u.mem_write(0x910100,'機動戦士ガンダム'.encode('cp932')+b'\0')
   u.mem_write(0x941000,struct.pack('<2f',fw,fh)+bytes(64));u.reg_write(r.UC_MIPS_REG_S2,0x940000)
   for reg,value in ((r.UC_MIPS_REG_A0,0x941000),(r.UC_MIPS_REG_A1,ptr),
                    (r.UC_MIPS_REG_A2,0xfffffffffffffff0),(r.UC_MIPS_REG_A3,380),
                    (r.UC_MIPS_REG_T0,0xffffffffffffffff)):u.reg_write(reg,value)
   # Measure actual native width before draw, including JP fallback.
   u.emu_start(0x131ba0,0x920000,count=20000)
   natural=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_MIPS_REG_F0)&0xffffffff))[0]
   u.reg_write(r.UC_MIPS_REG_A0,0x941000);u.reg_write(r.UC_MIPS_REG_A1,ptr)
   u.reg_write(r.UC_MIPS_REG_A3,380);u.reg_write(r.UC_MIPS_REG_T0,0xffffffffffffffff)
   u.emu_start(0x1660a8,0x1660b0,count=20000)
   assert len(draws)==1;d=draws[0];factor=d['font'][0]/fw;draw_width=natural*factor
   assert abs(d['font'][1]/fh-factor)<1e-5
   assert draw_width<=456.001 and d['x']>=107-0.51 and d['x']+draw_width<=563+0.51,(natural,d)
   assert abs(d['x']+draw_width/2-335)<=0.76,(natural,d,draw_width)
   assert abs(d['y']+min(d['font'])*74/96-(380+min(fw,fh)*74/96))<=0.51
   assert bytes(u.mem_read(0x941000,8))==struct.pack('<2f',fw,fh)
   assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
   titles.append(dict(**d,natural_width=natural,draw_width=draw_width))
 preserved=[]
 for p in PREVIOUS.iterdir():
  if p.suffix not in ('.BIN','.DAT'):continue
  from ps2_resource_preservation import check
  check(base,PREVIOUS,p.name)
  preserved.append(p.name)
 result=dict(version=version,passed=True,save_branches=branches,yes_no_x=[yes,no],
             protagonist_header='Protagonist Setup',
             protagonist_values=names,unit_descriptions=descriptions,series_titles=titles,
             final_confirmation=confirmations,
             all_campaign_resources_unchanged=preserved,visual_validation='pending')
 save(ROOT/'work/output'/f'ps2_setup_save_{version}_execution.json',result)
 print(json.dumps(dict(version=version,passed=True,save_branches=len(branches),series_cases=len(titles))))
 return result

if __name__=='__main__':verify()
