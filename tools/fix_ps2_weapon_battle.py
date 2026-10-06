"""Correct fixed-size weapon flags and crowded native PS2 battle labels."""
import argparse,json,shutil,struct
import keystone
import insert_text as it
from port_ps2_translations import ROOT,sha
from port_ps2_prologue import save
from ps2_translation_native import extend
from ps2_font4x import FILE_BIAS
from ps2_graphics_port import p2ig_textures,fake_tx48
from ps2_map_label_pixels import decode,encode
from fix_ps2_map_support import render,preview
from redraw_banners import read

VERSION='0.1.16';SOURCE_VERSION='0.1.15'
BASE=ROOT/'work/build/ps2'/f'weapon_battle_{VERSION}'
PREVIOUS=ROOT/'work/build/ps2'/f'map_support_{SOURCE_VERSION}'

def prepare():
 BASE.mkdir(parents=True,exist_ok=True)
 for p in PREVIOUS.iterdir():
  if p.suffix in ('.BIN','.DAT','.45','.json'):shutil.copyfile(p,BASE/p.name)
 data=bytearray((BASE/'SLPS_253.45').read_bytes());meta=json.loads((BASE/'patch.json').read_text())
 changes=dict(version=VERSION,source_build=SOURCE_VERSION,instruction_words=[],storage=[],
              native_font=True,texture_replacement=False,psp_opening_preserved=True)
 def word(va,value,expected):
  o=va-FILE_BIAS;old=struct.unpack_from('<I',data,o)[0];assert old==expected,(hex(va),hex(old),hex(expected))
  struct.pack_into('<I',data,o,value);changes['instruction_words'].append(dict(va=hex(va),old=hex(old),new=hex(value)))
 def storage(va,en,size):
  o=va-FILE_BIAS;raw=it.encode(en);assert len(raw)<=size
  old=bytes(data[o:o+size]);data[o:o+size]=raw+bytes(size-len(raw))
  changes['storage'].append(dict(va=hex(va),english=en,old=old.hex(),new=data[o:o+size].hex()))
 # The table renderer copies a two-byte character plus byte 2 as terminator.
 # "As" occupied four bytes, so byte 2 was a second character's lead byte.
 # Explicitly terminate every flag cell even if the source label later grows.
 word(0x173444,0x00001821,0x90430002) # move v1,zero; retain following stores
 storage(0x4c20e8,'A',8) # assist attack marker; MAP's separate M marker is retained
 storage(0x4c20f8,'S',8) # solid weapon marker (beam remains B)
 # Some cached headers copy the literal instead of following translated pointers.
 storage(0x493020,'Weapons',16);storage(0x4992b0,'Weapons',16)
 storage(0x49af68,'Critical',24)
 current=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
 texts=['Giganos Soldier','Giganos Sldr.'];blob=b''.join(it.encode(t) for t in texts)
 data,ptr=extend(data,meta,blob);assert ptr==current
 full=ptr;short=ptr+len(it.encode(texts[0]))
 def addr(r,a):
  hi=(a+0x8000)>>16;return [f'lui {r},{hi}',f'addiu {r},{r},{a-(hi<<16)}']
 # Restrict abbreviation to the two forecast pilot-name draws. Database and
 # battle dialogue continue to use the complete canonical name.
 src=['.set noreorder','move $14,$a1',*addr('$15',full),'compare:',
      'lbu $t8,0($14)','lbu $t9,0($15)','bne $t8,$t9,draw','nop',
      'beqz $t8,short_name','nop','addiu $14,$14,1','b compare','addiu $15,$15,1',
      'short_name:',*addr('$a1',short),'draw:','j 0x130610','nop']
 asm='\n'.join(src);code_va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
 code=bytes(ks.asm(asm,code_va)[0]);data,actual=extend(data,meta,code);assert actual==code_va
 for site in (0x1799cc,0x17a43c):word(site,0x0c000000|(code_va>>2),0x0c000000|(0x130610>>2))
 changes['forecast']=dict(sites=['0x1799cc','0x17a43c'],wrapper=hex(code_va),full=hex(full),short=hex(short),
                         english=texts[1],full_name_preserved=True,name_x=[345,44],level_x=[517,224])
 (BASE/'forecast_name.asm').write_text(asm,encoding='utf8')
 # Cached labels and battle-generated strings may bypass every static literal
 # reference. Translate complete labels at both CFont drawing entry points;
 # never replace individual kanji used inside names or longer descriptions.
 pairs=[('気力','Will'),('クリティカル','Critical'),('武器選択','Weapons')]
 pool=bytearray();current=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15;records=[]
 for jp,en in pairs:
  source=current+len(pool);pool+=jp.encode('cp932')+b'\0'
  target=current+len(pool);pool+=it.encode(en)
  records.append(dict(source=source,target=target,english=en,jp=jp))
 data,actual=extend(data,meta,pool);assert actual==current
 changes['cached_labels']=[]
 for entry in (0x130610,0x1309b0):
  source=['.set noreorder']
  for i,row in enumerate(records):
   source+=['move $14,$a1',*addr('$15',row['source']),f'label{i}:',
    'lbu $t8,0($14)','lbu $t9,0($15)',f'bne $t8,$t9,next{i}','nop',
    f'beqz $t8,found{i}','nop','addiu $14,$14,1',f'b label{i}','addiu $15,$15,1',
    f'found{i}:',*addr('$a1',row['target']),'b resume','nop',f'next{i}:']
  source+=['resume:']
  prefix=bytes(data[entry-FILE_BIAS:entry-FILE_BIAS+8])
  # Both original prefixes are straight-line prologue instructions.
  from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS64,CS_MODE_LITTLE_ENDIAN
  cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)
  instructions=list(cs.disasm(prefix,entry));assert len(instructions)==2
  assert all(ins.mnemonic in ('addiu','lui','sd','move') for ins in instructions)
  source += [f'{ins.mnemonic} {ins.op_str}' for ins in instructions]
  source += [f'j {entry+8}','nop'];assembly='\n'.join(source)
  va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
  raw=bytes(ks.asm(assembly,va)[0]);data,actual=extend(data,meta,raw);assert actual==va
  word(entry,0x08000000|(va>>2),struct.unpack_from('<I',prefix)[0])
  word(entry+4,0,struct.unpack_from('<I',prefix,4)[0])
  changes['cached_labels'].append(dict(entry=hex(entry),wrapper=hex(va),resume=hex(entry+8),
   original_prefix=prefix.hex(),labels=[dict(english=q['english'],source=hex(q['source']),target=hex(q['target'])) for q in records]))
  (BASE/f'cached_labels_{entry:x}.asm').write_text(assembly,encoding='utf8')
 # Long weapon names share a 182px name column with the fixed power/range
 # columns. Fit only that column, scaling both axes and retaining its baseline.
 source='''.set noreorder
addiu $sp,$sp,-64
sd $ra,56($sp)
sd $a0,0($sp)
sd $a1,8($sp)
sw $a2,16($sp)
sw $a3,20($sp)
sw $8,24($sp)
lw $t8,0($a0)
sw $t8,28($sp)
lw $t8,4($a0)
sw $t8,32($sp)
bnez $s6,draw
nop
jal 0x131ba0
nop
ld $a0,0($sp)
ld $a1,8($sp)
lw $a2,16($sp)
lw $a3,20($sp)
lw $8,24($sp)
lui $at,0x432e
mtc1 $at,$f1
c.ole.s $f0,$f1
bc1t draw
nop
div.s $f2,$f1,$f0
lwc1 $f3,28($sp)
mul.s $f3,$f3,$f2
swc1 $f3,0($a0)
lwc1 $f4,32($sp)
mul.s $f5,$f4,$f2
swc1 $f5,4($a0)
sub.s $f4,$f4,$f5
lui $at,0x3f45
ori $at,$at,0x5555
mtc1 $at,$f6
mul.s $f4,$f4,$f6
cvt.w.s $f4,$f4
mfc1 $t8,$f4
addu $a3,$a3,$t8
draw:
jal 0x130610
nop
ld $t8,0($sp)
lw $t9,28($sp)
sw $t9,0($t8)
lw $t9,32($sp)
sw $t9,4($t8)
ld $ra,56($sp)
jr $ra
addiu $sp,$sp,64
'''
 va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
 raw=bytes(ks.asm(source,va)[0]);data,actual=extend(data,meta,raw);assert actual==va
 word(0x17348c,0x0c000000|(va>>2),0x0c000000|(0x130610>>2))
 changes['weapon_names']=dict(site='0x17348c',wrapper=hex(va),column=0,name_width=182,fit_width=174,
                             uniform_scaling=True,baseline_preserved=True)
 (BASE/'weapon_name_fit.asm').write_text(source,encoding='utf8')
 maps=bytearray((BASE/'MAP.BIN').read_bytes());old=bytes(maps)
 sec=struct.unpack_from('<18I',data,0x37e438);start,end=sec[16]*2048,sec[17]*2048
 r=next(r for r in p2ig_textures(maps[start:end]) if r['name']=='M_19')
 _,w,h,pal,_,_=read(fake_tx48(maps[start:end],r),0);assert (w,h,r['psm'])==(128,32,20)
 off=start+r['offset']+r['pixel_offset'];before=bytes(maps[off:off+2048]);new,layout=render('Critical',pal)
 after=encode(new);assert decode(after)==new;maps[off:off+2048]=after
 out=ROOT/'work/ui/ps2'/f'weapon_battle_{VERSION}';out.mkdir(parents=True,exist_ok=True)
 preview(decode(before),pal).save(out/'critical_original.png');preview(new,pal).save(out/'critical_english.png')
 changes['map_caption']=dict(asset='M_19',english='Critical',pixel_offset=hex(off),bytes=2048,
   source_sha256=sha(before),target_sha256=sha(after),layout=layout,
   source_map_sha256=sha(old),target_map_sha256=sha(maps))
 assert maps[:off]==old[:off] and maps[off+2048:]==old[off+2048:]
 (BASE/'MAP.BIN').write_bytes(maps)
 meta['target_sha256']=sha(data);(BASE/'SLPS_253.45').write_bytes(data);save(BASE/'patch.json',meta)
 inherited=json.loads((BASE/'ui_fix.json').read_text())
 for row in inherited['in_place_ui_strings']:
  if int(row['source'],16)==0x4c20e8:row.update(english='A',bytes=3)
 save(BASE/'ui_fix.json',inherited)
 save(BASE/'weapon_battle.json',changes)
 save(ROOT/'work/translation/en/ps2'/f'weapon_battle_{VERSION}.en.json',changes)
 return changes

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');args=p.parse_args()
 prepare()
 from verify_ps2_weapon_battle import verify
 verify()
 if args.build:
  from verify_ps2_stage30 import verify as verify_campaign
  from verify_ps2_prologue_fix import verify as verify_prologue
  from verify_ps2_ui import verify as verify_ui
  from verify_ps2_ui_details import verify as verify_details
  from verify_ps2_roster_system import verify as verify_roster
  from verify_ps2_setup_save import verify as verify_setup
  from package_ps2_stage30 import build
  for test in (verify_prologue,verify_ui,verify_details,verify_roster,verify_setup):test(BASE,VERSION)
  verify_campaign(BASE,VERSION);build(BASE,VERSION,SOURCE_VERSION)
