import json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS64,CS_MODE_LITTLE_ENDIAN
from ps2_translation_native import written_register
from ps2_font4x import FILE_BIAS
ROOT=Path(__file__).resolve().parents[1]
o=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
p=(ROOT/'work/build/ps2/ui_details_0.1.12/SLPS_253.45').read_bytes()
ui=json.loads((ROOT/'work/translation/en/ps2/ui_port.en.json').read_text())
labels=['味方部隊表','作戦目的','武器改造','修理費','射程','Ｐ射程','気力','グリッド表示','サウンド','サウンドBGM設定','サウンドBGM変更','バイブレーション','ユニット表示','カーソル移動方式','画面の回転','ステレオ','モノラル','個別','ユニット','パイロット','固定','切替え','標準','属性','点滅','画面','マップ','90度きざみ','任意']
words=struct.unpack_from('<%dI'%((0x2bef18-0x1000)//4),o,0x1000)
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS64|CS_MODE_LITTLE_ENDIAN)
if len(__import__('sys').argv)>1:
    a=int(__import__('sys').argv[1],16);b=int(__import__('sys').argv[2],16)
    for off in range(a-FILE_BIAS,b-FILE_BIAS,4):
        ins=list(md.disasm(p[off:off+4],off+FILE_BIAS))
        print(' '.join([hex(off+FILE_BIAS),*(f'{i.mnemonic} {i.op_str}' for i in ins)]))
    raise SystemExit
for jp in labels:
    needle=jp.encode('cp932')+b'\0';start=0
    while (start:=o.find(needle,start))>=0:
        off=start;start+=1
        if not 0x2c5e00<=off<0x3c5d00:continue
        va=off+FILE_BIAS
        refs=[hex(i+FILE_BIAS) for i in range(0x2c5e00,0x3c5d00,4) if struct.unpack_from('<I',o,i)[0]==va]
        codes=[]
        for i,w in enumerate(words):
            op=w>>26;rs=w>>21&31
            if op not in (9,13):continue
            lo=w&65535
            if op==9 and lo>=32768:lo-=65536
            if rs==28:
                if 0x4c84f0+lo==va:codes.append(hex(0x100000+i*4)+' GP')
                continue
            for j in range(i-1,max(i-65,-1),-1):
                if written_register(words[j])!=rs:continue
                if words[j]>>26==15 and ((words[j]&65535)<<16)+lo==va:
                    codes.append(hex(0x100000+i*4)+' LUI '+hex(0x100000+j*4))
                break
        en=[(r['english'],r['target']) for r in ui['texts'] if int(r['source'],16)==va]
        now=p[off:p.index(0,off)].decode('cp932',errors='replace')
        print(jp,hex(va),'now',now,'english',en,'refs',refs,'code',codes)
