import json,struct,sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS64,CS_MODE_LITTLE_ENDIAN
from ps2_font4x import FILE_BIAS
ROOT=Path(__file__).resolve().parents[1]
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)
from ps2_translation_native import written_register
o=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
p=(ROOT/'work/build/ps2/roster_system_0.1.13/SLPS_253.45').read_bytes()
if len(sys.argv)>1:
 for a in range(int(sys.argv[1],16),int(sys.argv[2],16),4):
  ins=list(md.disasm(p[a-FILE_BIAS:a-FILE_BIAS+4],a))
  print(hex(a),' '.join(f'{i.mnemonic} {i.op_str}' for i in ins))
 sys.exit()
needles=['データを調べています','システムデータを上書き','セーブ中','主人公設定','歳','設定を変更する','設定を終了する','ツェントル','接近戦','射撃戦','はい','いいえ']
found={}
for needle in needles:
 pos=0
 while (pos:=o.find(needle.encode('cp932'),pos))>=0:
  off=pos;pos+=1
  if not 0x2c5e00<=off<0x3c5d00:continue
  while off>0x2c5e00 and o[off-1]!=0:off-=1
  found[off+FILE_BIAS]=o[off:o.index(0,off)].decode('cp932',errors='replace')
words=struct.unpack_from('<%dI'%((0x2bef18-0x1000)//4),o,0x1000)
codes={v:[] for v in found};refs={v:[] for v in found}
for off in range(0x2c5e00,0x3c5d00,4):
 v=struct.unpack_from('<I',o,off)[0]
 if v in refs:refs[v].append(hex(off+FILE_BIAS))
for i,w in enumerate(words):
 op=w>>26;rs=w>>21&31
 if op not in (9,13):continue
 lo=w&65535
 if op==9 and lo>=32768:lo-=65536
 if rs==28:
  v=0x4c84f0+lo
  if v in codes:codes[v].append([hex(0x100000+i*4),'GP'])
  continue
 for j in range(i-1,max(i-65,-1),-1):
  if written_register(words[j])!=rs:continue
  if words[j]>>26==15:
   v=((words[j]&65535)<<16)+lo
   if v in codes:codes[v].append([hex(0x100000+i*4),hex(0x100000+j*4)])
  break
ui=json.loads((ROOT/'work/translation/en/ps2/ui_port.en.json').read_text())
for v,text in found.items():
 print(hex(v),repr(text),'refs',refs[v],'code',codes[v],'english',[(r['english'],r['target']) for r in ui['texts'] if int(r['source'],16)==v])
