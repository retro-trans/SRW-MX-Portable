"""Incremental native PS2 roster columns and System options correction."""
import argparse,json,shutil,struct
import keystone
import insert_text as it
from port_ps2_translations import ROOT,sha
from port_ps2_prologue import save
from ps2_translation_native import extend
from ps2_font4x import FILE_BIAS

VERSION='0.1.13'
SOURCE_VERSION='0.1.12'
BASE=ROOT/'work/build/ps2'/f'roster_system_{VERSION}'
PREVIOUS=ROOT/'work/build/ps2'/f'ui_details_{SOURCE_VERSION}'
# These labels belong to the native scrolling roster, not weapon-detail panels.
ROSTER={0x48f8b0:'Wpn',0x4c0ba0:'Cost',0x4c0bf0:'Und',
        0x4c0bf8:'Rng',0x4c0c00:'P.Rng',0x4c0c08:'Atk'}
SYSTEM={0x492e90:'Grid',0x492ea0:'Sound',0x492eb0:'BGM Source',
        0x492ec8:'BGM Switch',0x492ee0:'Rumble',0x492ef8:'Unit Display',
        0x492f08:'Cursor',0x492f20:'Rotation',0x492f30:'Stereo',
        0x492f40:'Mono',0x4c1a48:'Each',0x492f50:'Unit',0x492f60:'Pilot',
        0x4c1a50:'Fixed',0x4c1a58:'Switch',0x4c1a60:'Std',
        0x4c1a68:'Type',0x4c1a70:'Blink',0x4c1a78:'Screen',
        0x4c1a80:'Map',0x492f70:'90 deg',0x4c1a88:'Free'}
SYSTEM_SITES=(0x154ebc,0x154f50,0x154fe8,0x1550b0,0x155148,
              0x1551e0,0x1552a8,0x155340,0x1553d8)

def prepare():
    BASE.mkdir(parents=True,exist_ok=True)
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT','.45','.json'):
            shutil.copyfile(path,BASE/path.name)
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    data=bytearray((BASE/'SLPS_253.45').read_bytes())
    meta=json.loads((BASE/'patch.json').read_text())
    assert sha(data)==meta['target_sha256']
    changes=dict(version=VERSION,source_build=SOURCE_VERSION,data_references=[],
                 instruction_words=[],draw_mappings=[],native_font=True,
                 texture_replacement=False,psp_opening_preserved=True)
    current=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    blob=bytearray();targets={}
    for en in dict.fromkeys([*ROSTER.values(),*SYSTEM.values(),'Objectives']):
        targets[en]=current+len(blob);blob+=it.encode(en)
    data,actual=extend(data,meta,blob);assert actual==current
    for off in range(0x2c5e00,0x3c5d00,4):
        source=struct.unpack_from('<I',original,off)[0]
        if source not in ROSTER or not 0x3c5600<=off+FILE_BIAS<0x3c6600:continue
        en=ROSTER[source];old=struct.unpack_from('<I',data,off)[0]
        struct.pack_into('<I',data,off,targets[en])
        changes['data_references'].append(dict(site=hex(off+FILE_BIAS),source=hex(source),
                                              old=hex(old),target=hex(targets[en]),english=en))
    # Preserve preceding checks while replacing only their overridden references.
    inherited=json.loads((BASE/'ui_fix.json').read_text())
    updates={r['site']:r for r in changes['data_references']}
    for row in inherited['text_references']:
        if row['site'] in updates:
            row.update(target=updates[row['site']]['target'],english=updates[row['site']]['english'])
    inherited.update(version=VERSION,source_build=SOURCE_VERSION)
    save(BASE/'ui_fix.json',inherited)

    # Native option labels are often formed in branch delay slots, and several
    # choices share a LUI with ON/OFF. Translate at the local draw calls instead
    # of changing shared high halves. No option state or control flow is changed.
    lookup={**SYSTEM,0x4c0ba0:'Cost'}
    table=b''.join(struct.pack('<2I',source,targets[en]) for source,en in lookup.items())+bytes(8)
    data,table_va=extend(data,meta,table)
    changes['draw_mappings']=[dict(source=hex(s),target=hex(targets[e]),english=e) for s,e in lookup.items()]
    code_va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    assembly=f'''
.set noreorder
lui $t8,{(table_va+0x8000)>>16}
addiu $t8,$t8,{table_va-(((table_va+0x8000)>>16)<<16)}
loop:
lw $t9,0($t8)
beqz $t9,draw
nop
beq $a1,$t9,found
nop
b loop
addiu $t8,$t8,8
found:
lw $a1,4($t8)
draw:
j 0x130610
nop
'''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm(assembly,code_va)[0]);data,actual=extend(data,meta,code);assert actual==code_va
    (BASE/'roster_system.asm').write_text(assembly,encoding='utf8')
    for site in (*SYSTEM_SITES,0x1159b0,0x115cb4):
        old=struct.unpack_from('<I',data,site-FILE_BIAS)[0]
        assert old==0x0c000000|(0x130610>>2),hex(site)
        new=0x0c000000|(code_va>>2);struct.pack_into('<I',data,site-FILE_BIAS,new)
        changes['instruction_words'].append(dict(va=hex(site),old=hex(old),new=hex(new)))
    # The objective screen has a second literal after a nonzero structure
    # field. Its ADDIU is the header call's delay slot; menu-label translation
    # alone does not cover it. This LUI has no other uses.
    objective=targets['Objectives'];hi=(objective+0x8000)>>16
    for site,expected,new in ((0x153b4c,0x3c050049,0x3c050000|hi),
                            (0x153b58,0x24a52a88,0x24a50000|(objective&65535))):
        old=struct.unpack_from('<I',data,site-FILE_BIAS)[0];assert old==expected
        struct.pack_into('<I',data,site-FILE_BIAS,new)
        changes['instruction_words'].append(dict(va=hex(site),old=hex(old),new=hex(new)))
    changes['draw_wrapper']=dict(va=hex(code_va),bytes=len(code),table_va=hex(table_va),
        system_sites=[hex(x) for x in SYSTEM_SITES],repair_sites=['0x1159b0','0x115cb4'])
    widths={r['character']:r['width'] for r in meta['glyphs']}
    changes['roster_columns']=[dict(source=hex(s),english=e,font_size=24,
        width=sum(widths[c] for c in e),minimum_spacing=60) for s,e in ROSTER.items()]
    # Original scrolling columns intentionally reveal partial adjacent columns.
    # Their scroll/page controls and all row values are preserved.
    changes['system_layout']=dict(label_x=28,first_option_x=172,
        labels=[dict(english=SYSTEM[s],width=sum(widths[c] for c in SYSTEM[s]))
                for s in list(SYSTEM)[:8]],row_spacing=26)
    changes['retained_headers']=dict(roster='Allied Units',objectives='Objectives',
        roster_branch=hex(0x147ed8),objective_text_setup=hex(0x153b4c))
    meta['target_sha256']=sha(data)
    (BASE/'SLPS_253.45').write_bytes(data);save(BASE/'patch.json',meta)
    save(BASE/'roster_system.json',changes)
    save(ROOT/'work/translation/en/ps2'/f'roster_system_{VERSION}.en.json',changes)
    return changes

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
    info=prepare();print(json.dumps(dict(version=VERSION,references=len(info['data_references']),
                                       draw_sites=len(info['instruction_words']))))
    if a.build:
        from verify_ps2_roster_system import verify as verify_new
        from verify_ps2_stage30 import verify
        from verify_ps2_prologue_fix import verify as verify_prologue_fix
        from verify_ps2_ui import verify as verify_ui
        from verify_ps2_ui_details import verify as verify_details
        from package_ps2_stage30 import build
        verify_new(BASE,VERSION);verify(BASE,VERSION);verify_prologue_fix(BASE,VERSION)
        verify_ui(BASE,VERSION);verify_details(BASE,VERSION)
        build(BASE,VERSION,SOURCE_VERSION,('FACEPACK.BIN',))
