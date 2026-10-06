"""Native save dialogs, new-game setup and bounded series-title layout."""
import argparse,json,shutil,struct
import keystone
import insert_text as it
from port_ps2_translations import ROOT,sha
from port_ps2_prologue import save
from ps2_translation_native import extend
from ps2_font4x import FILE_BIAS

VERSION='0.1.14';SOURCE_VERSION='0.1.13'
BASE=ROOT/'work/build/ps2'/f'setup_save_{VERSION}'
PREVIOUS=ROOT/'work/build/ps2'/f'roster_system_{SOURCE_VERSION}'
TEXT={
 0x49d4f0:'Checking data. Do not insert or remove',
 0x49d530:'the memory card (PS2) or controller.',
 0x4a5c68:'Checking data. Do not insert or remove',
 0x4a5ca0:'the memory card (PS2) or controller.',
 0x4a9108:'Checking data. Do not insert or remove',
 0x4a9148:'the memory card (PS2) or controller.',
 0x4a5fa8:'Overwrite system data?',
 0x49d460:'Saving. Do not insert or remove',
 0x49d4a0:'the memory card (PS2) or controller.',
 0x4975a8:'Protagonist Setup',
 0x49d3a0:'Change Settings',0x49d3b0:'Finish Setup',
 0x497400:'Tsentr Project prototype:',
 0x497428:'A humanoid mobile weapon',
 0x497450:'powered by Terminus Energy.',
 0x497478:'Garmraid specializes in',
 0x4974a0:'close-range melee combat.',
 0x4974e0:'Cerberus specializes in',
 0x497508:'high-mobility combat and',
 0x497528:'long-range bombardment.',
}
# Each high/low pair is local to a single literal. Branch delay slots remain
# intact. Unit description pointers are replaced in every original UI table.
PAIRS={0x49d4f0:(0x19743c,0x19744c),0x49d530:(0x197460,0x197470),
 0x4a5c68:(0x25d050,0x25d058),0x4a5ca0:(0x25d064,0x25d06c),
 0x4a9108:(0x2c0860,0x2c0868),0x4a9148:(0x2c0874,0x2c0878),
 0x4a5fa8:(0x25df34,0x25df38),0x49d460:(0x196e7c,0x196e8c),
 0x49d4a0:(0x196ea0,0x196eb0),0x4975a8:(0x16a670,0x16a678)}

def prepare():
 BASE.mkdir(parents=True,exist_ok=True)
 for p in PREVIOUS.iterdir():
  if p.suffix in ('.BIN','.DAT','.45','.json'):shutil.copyfile(p,BASE/p.name)
 data=bytearray((BASE/'SLPS_253.45').read_bytes());original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
 meta=json.loads((BASE/'patch.json').read_text());assert sha(data)==meta['target_sha256']
 c=dict(version=VERSION,source_build=SOURCE_VERSION,native_font=True,texture_replacement=False,
        psp_opening_preserved=True,data_references=[],instruction_words=[],strings=[],storage=[])
 cursor=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
 blob=bytearray();targets={}
 for text in dict.fromkeys(TEXT.values()):targets[text]=cursor+len(blob);blob+=it.encode(text)
 data,start=extend(data,meta,blob);assert start==cursor
 def word(site,new,kind,expected=None):
  old=struct.unpack_from('<I',data,site-FILE_BIAS)[0]
  if expected is not None:assert old==expected,(hex(site),hex(old),hex(expected))
  struct.pack_into('<I',data,site-FILE_BIAS,new)
  c['instruction_words'].append(dict(va=hex(site),old=hex(old),new=hex(new),kind=kind))
 for source,text in TEXT.items():
  target=targets[text];c['strings'].append(dict(source=hex(source),target=hex(target),english=text))
  for off in range(0x2c5e00,0x3c5d00,4):
   if struct.unpack_from('<I',original,off)[0]!=source:continue
   old=struct.unpack_from('<I',data,off)[0];struct.pack_into('<I',data,off,target)
   c['data_references'].append(dict(site=hex(off+FILE_BIAS),old=hex(old),target=hex(target),english=text))
  if source in PAIRS:
   high,low=PAIRS[source];hi=(target+0x8000)>>16
   for site,imm in ((high,hi),(low,target&65535)):
    old=struct.unpack_from('<I',data,site-FILE_BIAS)[0]
    expected=struct.unpack_from('<I',original,site-FILE_BIAS)[0]
    assert old==expected,(hex(site),hex(old),hex(expected))
    word(site,(old&0xffff0000)|imm,'literal')
 # Age is copied by value (seven bytes), not passed by pointer. Preserve the
# original fixed copy size and the age number, removing only the JP suffix.
 for source,text in ((0x4c1ce0,'20'),(0x4c1ce8,'23')):
  off=source-FILE_BIAS;before=bytes(data[off:off+8]);raw=it.encode(text)
  assert len(raw)<=8;data[off:off+8]=raw+bytes(8-len(raw))
  c['storage'].append(dict(va=hex(source),old=before.hex(),new=bytes(data[off:off+8]).hex(),english=text))
 word(0x16a380,0x24c6008c,'name_value_x',0x24c6006c)
 word(0x151ebc,0x2405001a,'yes_left_alignment',0x24050012)
 # Replace the series selector's fixed 24px character-count centering at
# its final draw. Measure the real VWF, fit uniformly within 456px, preserve
# baseline, and restore the font context. The menu and selection are untouched.
 code_va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
 asm='''
.set noreorder
addiu $sp,$sp,-80
sd $ra,72($sp)
sd $a0,0($sp)
sd $a1,8($sp)
sw $a3,16($sp)
sw $8,20($sp)
lw $t8,0($a0)
sw $t8,24($sp)
lw $t8,4($a0)
sw $t8,28($sp)
jal 0x131ba0
nop
lui $at,0x43e4
mtc1 $at,$f1
c.ole.s $f0,$f1
bc1t center
nop
div.s $f2,$f1,$f0
ld $a0,0($sp)
lwc1 $f3,24($sp)
mul.s $f3,$f3,$f2
swc1 $f3,0($a0)
lwc1 $f4,28($sp)
mul.s $f5,$f4,$f2
swc1 $f5,4($a0)
lwc1 $f4,24($sp)
lwc1 $f6,28($sp)
c.ole.s $f4,$f6
bc1t glyph_height
nop
mov.s $f4,$f6
glyph_height:
mul.s $f5,$f4,$f2
sub.s $f4,$f4,$f5
lui $at,0x3f45
ori $at,$at,0x5555
mtc1 $at,$f6
mul.s $f4,$f4,$f6
cvt.w.s $f4,$f4
mfc1 $t8,$f4
lw $a3,16($sp)
addu $a3,$a3,$t8
sw $a3,16($sp)
mov.s $f0,$f1
center:
cvt.w.s $f0,$f0
mfc1 $t8,$f0
addiu $a2,$zero,640
subu $a2,$a2,$t8
sra $a2,$a2,1
lw $t8,0x9c($s2)
addu $a2,$a2,$t8
ld $a0,0($sp)
ld $a1,8($sp)
lw $a3,16($sp)
lw $8,20($sp)
jal 0x130610
nop
ld $t8,0($sp)
lw $t9,24($sp)
sw $t9,0($t8)
lw $t9,28($sp)
sw $t9,4($t8)
ld $ra,72($sp)
jr $ra
addiu $sp,$sp,80
'''
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
 code=bytes(ks.asm(asm,code_va)[0]);data,actual=extend(data,meta,code);assert actual==code_va
 word(0x1660a8,0x0c000000|(code_va>>2),'series_title_fit',0x0c000000|(0x130610>>2))
 (BASE/'series_title.asm').write_text(asm)
 c['series_title']=dict(hook='0x1660a8',wrapper=hex(code_va),bytes=len(code),width=456,
                       box=[80,560],padding=12,center=320,baseline=74/96,uniform_fit=True)
 c['setup_layout']=dict(label_x=54,value_x=140,description_x=28,description_max_width=300,
                        yes_x=26,no_x=26,age_suffix_removed=True)
 c['description_tables']=[dict(unit='Garmraid',va='0x497610',lines=[TEXT[s] for s in
                         (0x497400,0x497428,0x497450,0x497478,0x4974a0)]+[' ']),
                          dict(unit='Cerberus',va='0x497628',lines=[TEXT[s] for s in
                         (0x497400,0x497428,0x497450,0x4974e0,0x497508,0x497528)])]
 meta['target_sha256']=sha(data);(BASE/'SLPS_253.45').write_bytes(data)
 save(BASE/'patch.json',meta);save(BASE/'setup_save.json',c)
 save(ROOT/'work/translation/en/ps2'/f'setup_save_{VERSION}.en.json',c)
 return c

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
 c=prepare();print(json.dumps(dict(version=VERSION,references=len(c['data_references']),instructions=len(c['instruction_words']))))
 if a.build:
  from verify_ps2_setup_save import verify as verify_new
  from verify_ps2_stage30 import verify
  from verify_ps2_prologue_fix import verify as prologue
  from verify_ps2_ui import verify as ui
  from verify_ps2_ui_details import verify as details
  from verify_ps2_roster_system import verify as roster
  from package_ps2_stage30 import build
  verify_new(BASE,VERSION);verify(BASE,VERSION);prologue(BASE,VERSION)
  ui(BASE,VERSION);details(BASE,VERSION);roster(BASE,VERSION)
  build(BASE,VERSION,SOURCE_VERSION,('FACEPACK.BIN',))
