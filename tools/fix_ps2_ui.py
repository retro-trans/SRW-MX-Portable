"""Correct native Latin aspect and remaining PS2 battle/status UI labels."""
import argparse, json, shutil, struct
from port_ps2_translations import ROOT, sha
from port_ps2_prologue import save
from ps2_translation_native import extend
from ps2_font4x import assemble, FILE_BIAS, SITES
import insert_text as it
import keystone

VERSION='0.1.11'
SOURCE_VERSION='0.1.10'
BASE=ROOT/'work/build/ps2'/f'ui_fix_{VERSION}'

# Compact labels use the same terms as the reviewed PSP UI. Japanese here
# contains only UI terms; story source remains in ignored working files.
LABELS={'移動':'Move','能力':'Status','修理費':'Repair','性格':'Type',
        '格闘':'Mel','射撃':'Rng','命中':'Acc','回避':'Eva','技量':'Skl',
        '防御':'Def','精神コマンド':'Spirits','地形':'Ter',
        '空':'A','陸':'L','宇':'Sp','海':'W','地':'U','支':'As'}


def prepare():
    previous=ROOT/'work/build/ps2/prologue_fix_0.1.10'
    BASE.mkdir(parents=True,exist_ok=True)
    for name in ('SLPS_253.45','MAP.BIN','STAGE.BIN','FIX00.DAT','D2MAPH.BIN',
                 'PACKMAPC.BIN','STATIC.BIN','FACEPACK.BIN','patch.json',
                 'difficulty.json','prologue.json','stage30.json','prologue_fix.json'):
        shutil.copyfile(previous/name,BASE/name)
    old=(BASE/'SLPS_253.45').read_bytes();data=bytearray(old)
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    meta=json.loads((BASE/'patch.json').read_text());assert sha(data)==meta['target_sha256']
    reusable_code_va=int(meta['code_va'],16)
    code_va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    code,entries,hooks,source=assemble(int(meta['table_va'],16),int(meta['atlas_va'],16),
        int(meta['state_va'],16),code_va,meta['glyph_count'],uniform_aspect=True)
    data,actual=extend(data,meta,code);assert actual==code_va
    for va,new,name in hooks:
        record=next(h for h in meta['hooks'] if h['name']==name)
        assert data[va-FILE_BIAS:va-FILE_BIAS+8]==bytes.fromhex(record['new'])
        data[va-FILE_BIAS:va-FILE_BIAS+8]=new
        record.update(new=new.hex(),target=hex(entries[name]))
    meta.update(code_va=hex(code_va),code_bytes=len(code),latin_uniform_aspect=True,
                latin_size_rule='native_height for half-width ASCII cells; otherwise min(native_width,native_height)',
                japanese_cell_dimensions_preserved=True)
    (BASE/'font_aspect.asm').write_text(source,encoding='utf8')
    targets={};blob=bytearray();current=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    for en in dict.fromkeys([*LABELS.values(),'Mv','Power','Hit']):
        targets[en]=current+len(blob);blob+=it.encode(en)
    data,pool=extend(data,meta,blob);assert pool==current
    reference_changes=[];storage_changes=[]
    for jp,default_en in LABELS.items():
        raw=jp.encode('cp932')+b'\0';start=0
        while (start:=original.find(raw,start))>=0:
            off=start;start+=1
            if not 0x2c5e00<=off<0x3c5d00 or original[off-1]!=0:continue
            va=off+FILE_BIAS;refs=[]
            # Terrain movement mode has only 40px before the first grade.
            en='Mv' if va==0x4c1d58 else default_en
            for site in range(0x2c5e00,0x3c5d00,4):
                if struct.unpack_from('<I',original,site)[0]==va:
                    before=struct.unpack_from('<I',data,site)[0]
                    struct.pack_into('<I',data,site,targets[en]);refs.append(hex(site+FILE_BIAS))
                    reference_changes.append(dict(site=hex(site+FILE_BIAS),source=hex(va),old=hex(before),
                                                  target=hex(targets[en]),english=en))
            # Some one-letter markers and headings are addressed directly in
            # branch delay slots. Replace within their original padded slot;
            # executable code and neighboring strings remain untouched.
            encoded=it.encode(en);after=(off+len(raw)+3)&~3
            while after<off+32 and after<len(original) and original[after]==0:after+=1
            if len(encoded)<=after-off and not any(original[off+len(raw):off+len(encoded)]):
                assert data[off:off+len(raw)]==original[off:off+len(raw)]
                data[off:off+len(encoded)]=encoded
                if len(encoded)<len(raw):data[off+len(encoded):off+len(raw)]=bytes(len(raw)-len(encoded))
                storage_changes.append(dict(source=hex(va),english=en,bytes=len(encoded)))
    # The weapon table's Attack label shares an English pool entry with the
    # Attack command. Repoint only the source-specific data references.
    for va,en in ((0x4c2028,'Power'),(0x4c2500,'Power'),(0x4c2508,'Hit')):
        for off in range(0x2c5e00,0x3c5d00,4):
            if struct.unpack_from('<I',original,off)[0]==va:
                before=struct.unpack_from('<I',data,off)[0];struct.pack_into('<I',data,off,targets[en])
                reference_changes.append(dict(site=hex(off+FILE_BIAS),source=hex(va),old=hex(before),
                                              target=hex(targets[en]),english=en))
    previous_ui=json.loads((ROOT/'work/translation/en/ps2/ui_port.en.json').read_text())
    # Accuracy in the weapon header has a context-specific label. Retain only
    # the final target for any reference overridden by that narrower context.
    final_references={}
    for row in reference_changes:
        if row['site'] in final_references:row['old']=final_references[row['site']]['old']
        final_references[row['site']]=row
    reference_changes=list(final_references.values())
    footer=[]
    for record in previous_ui['texts']:
        short={'Will Needed':'Will','Skill Needed':'Skill','Critical Bonus':'Critical'}.get(record['english'])
        if not short:continue
        va=int(record['target'],16);off=int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
        before=it.encode(record['english']);after=it.encode(short)
        assert data[off:off+len(before)]==before
        data[off:off+len(before)]=after+bytes(len(before)-len(after))
        footer.append(dict(target=hex(va),old_english=record['english'],english=short))
    # The retired 4x font code is no longer reachable after repointing all
    # 19 hooks. Reuse its space for a local Pilot Stats name-fit wrapper.
    # Long Spirit names scale uniformly, keeping their baseline and aspect.
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    wrapper='''
.set noreorder
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
sltiu $t8,$s2,2
bnez $t8,draw
nop
sltiu $t8,$s2,8
beqz $t8,draw
nop
jal 0x131ba0
nop
ld $a0,0($sp)
ld $a1,8($sp)
lw $a2,16($sp)
lw $a3,20($sp)
lw $8,24($sp)
lui $at,0x4298
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
    native=bytes(ks.asm(wrapper,reusable_code_va)[0]);assert len(native)<512
    off=int(meta['segment_offset'],16)+reusable_code_va-int(meta['segment_va'],16)
    data[off:off+len(native)]=native
    (BASE/'spirit_layout.asm').write_text(wrapper,encoding='utf8')
    hook=0x170914;before=bytes(data[hook-FILE_BIAS:hook-FILE_BIAS+4])
    assert before==struct.pack('<I',0x0c000000|(0x130610>>2))
    new=struct.pack('<I',0x0c000000|(reusable_code_va>>2))
    data[hook-FILE_BIAS:hook-FILE_BIAS+4]=new
    layout=[]
    def write_layout(va,value,expected,kind):
        off=va-FILE_BIAS;old_value=struct.unpack_from('<I',data,off)[0]
        assert old_value==expected,(hex(va),hex(old_value),hex(expected))
        struct.pack_into('<I',data,off,value)
        layout.append(dict(va=hex(va),old=hex(old_value),new=hex(value),kind=kind))
    for row in range(6):
        write_layout(0x4989c4+row*24,292,268,'spirit_cost_open_x')
        write_layout(0x4989d0+row*24,346,318,'spirit_cost_close_x')
    write_layout(0x1703e0,0x24080132,0x2408011a,'spirit_cost_value_x')
    meta['target_sha256']=sha(data);(BASE/'SLPS_253.45').write_bytes(data);save(BASE/'patch.json',meta)
    result=dict(version=VERSION,source_build=SOURCE_VERSION,font_aspect=meta['latin_size_rule'],
                text_references=reference_changes,in_place_ui_strings=storage_changes,footer=footer,
                layout=layout,spirit_name_width=76,spirit_name_uniform_fit=True,
                spirit_hook=dict(va=hex(hook),old=before.hex(),new=new.hex(),target=hex(reusable_code_va),bytes=len(native)),
                native_font=True,texture_replacement=False,psp_opening_preserved=True,
                scripts_unchanged=sha((BASE/'MAP.BIN').read_bytes())==sha((previous/'MAP.BIN').read_bytes()))
    assert result['scripts_unchanged']
    save(BASE/'ui_fix.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');args=p.parse_args()
    info=prepare();print(json.dumps(dict(version=VERSION,references=len(info['text_references']),storage=len(info['in_place_ui_strings']))))
    if args.build:
        from verify_ps2_stage30 import verify
        from verify_ps2_prologue_fix import verify as verify_prologue_fix
        from verify_ps2_ui import verify as verify_ui
        from package_ps2_stage30 import build
        verify(BASE,VERSION);verify_prologue_fix(BASE,VERSION);verify_ui()
        build(BASE,VERSION,SOURCE_VERSION,('FACEPACK.BIN',))
