"""Keep full PS2 unit names inside the existing 48-byte rename editor area."""
import struct
import keystone
from pathlib import Path
import insert_text as it
from ps2_translation_native import extend

ROOT=Path(__file__).resolve().parents[1]
BIAS=0xff000
CAP_SITE=0x15aa6c
FULL=(0x15ac18,0x15b1e0,0x15b5b4,0x15b648,0x15b7c8,0x15b8d8,
      0x15bc1c,0x15bcc4,0x15bd40,0x15be00,0x15c5f0)
READ=(0x15ac28,0x15b1d0,0x15b5bc,0x15b65c,0x15b7bc,0x15b8cc,
      0x15bc28,0x15bcd8,0x15bd2c,0x15bdec,0x15c5d8)
FULL_PX=(0x15ac20,0x15b1e8,0x15b5e0,0x15b64c,0x15b7d8,0x15b8e8,
         0x15bc4c,0x15bcc8,0x15bd48,0x15be08,0x15c5f4)
READ_PX=(0x15ac2c,0x15b1d8,0x15b5dc,0x15b664,0x15b7c4,0x15b8d4,
         0x15bc48,0x15bce0,0x15bd30,0x15bdf0,0x15c600)
CHAINS=((0x15af38,0x15af50,0x15af5c),(0x15b230,0x15b238,0x15b240),
 (0x15b268,0x15b270,0x15b278),(0x15b5c0,0x15b5c8,0x15b5d0),
 (0x15b650,0x15b658,0x15b660),(0x15b7cc,0x15b7d4,0x15b7dc),
 (0x15b8dc,0x15b8e4,0x15b8ec),(0x15b934,0x15b93c,0x15b944),
 (0x15b964,0x15b968,0x15b970),(0x15b990,0x15b998,0x15b9a0),
 (0x15bb7c,0x15bb84,0x15bb8c),(0x15bbdc,0x15bbe0,0x15bbe8),
 (0x15bc2c,0x15bc34,0x15bc3c),(0x15bccc,0x15bcd4,0x15bcdc),
 (0x15bd34,0x15bd3c,0x15bd44),(0x15bd7c,0x15bd84,0x15bd8c),
 (0x15bdf4,0x15bdfc,0x15be04),(0x15be3c,0x15be44,0x15be4c),
 (0x15c5c0,0x15c5c8,0x15c5d0))


def cap_stub():
    return it._words(0x24080010,0x16a00002,0,0x2408001e,
        0x00884021,0xa1000000,0x08000000|(0x36af24>>2),0)


def width_stub():
    # Fifteen cells need compact spacing. Keep the editor's logical
    # 14/16/20-unit cell sizes private instead of changing shared constants.
    asm='''
        lbu $v0,0($a1)
        addiu $v1,$zero,0x82
        bne $v0,$v1,normal
        sltiu $a0,$v0,0x88
        lbu $v0,1($a1)
        sltiu $v1,$v0,0x59
        sltiu $v0,$v0,0x4f
        bnez $v0,normal
        nop
        lui $at,0x4180
        bnez $v1,done
        mtc1 $at,$f0
    normal:
        lui $at,0x41a0
        beqz $a0,done
        mtc1 $at,$f0
        lui $at,0x4160
        mtc1 $at,$f0
    done:
        jr $ra
        nop
    '''
    k=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    return bytes(k.asm('.set noreorder\n'+asm)[0])


def changes():
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    word=lambda a:struct.unpack_from('<I',original,a-BIAS)[0]
    edits={}
    def imm(a,old,new):
        w=word(a);assert w&65535==old,hex(a)
        edits[a]=(w,(w&0xffff0000)|new)
    for sites,old,new in ((FULL,22,30),(READ,12,16),(FULL_PX,154,210),(READ_PX,84,112),
        ((0x15a808,0x15aaac,0x15aab8),23,31),
        ((0x15aa20,0x15aa58),0x64b,0x653),
        ((0x15bb6c,),20,28),((0x15bb70,),10,14),
        ((0x15bb98,),0x648,0x650),((0x15bb9c,),0x63e,0x642),
        ((0x15a7d0,0x15aa98),11,15),((0x15a7d4,0x15aa9c),6,8)):
        for a in sites:imm(a,old,new)
    for a,b,c in CHAINS:
        w,x,y=word(a),word(b),word(c)
        assert w>>26==0 and w&63==0 and (w>>6)&31==1
        assert x>>26==0 and x&63==33 and (x>>11)&31==(w>>11)&31
        assert y>>26==0 and y&63==0 and (y>>6)&31==3
        edits[a]=(w,(w&~(31<<6))|(5<<6));edits[b]=(x,0);edits[c]=(y,0)
    # The underline draw's scheduled multiply spans its draw loop.
    assert word(0x15ab88)==0x0012a840 and word(0x15ac0c)==0x02b28021
    edits[0x15ab88]=(word(0x15ab88),0x0012a940)
    edits[0x15ac0c]=(word(0x15ac0c),0x02a08021)
    assert word(0x15ac14)==0x001080c0
    edits[0x15ac14]=(word(0x15ac14),0)
    # Deletion's first multiply instruction is in the loop branch delay slot.
    assert word(0x15bb78)==0x00061040
    edits[0x15bb78]=(word(0x15bb78),0x00061140)
    for a in (0x15bb40,0x15bb44):edits[a]=(word(a),0)
    # Value origins move as a pair with their underline draws. Labels stay put.
    for a,old,new in ((0x495784,92,116),(0x495790,456,476)):
        assert word(a)==old;edits[a]=(old,new)
    return edits


def patch(elf,meta):
    data=bytearray(elf);edits=changes()
    for va,(old,new) in edits.items():
        current=struct.unpack_from('<I',data,va-BIAS)[0]
        assert current in (old,new),('Unexpected PS2 rename instruction',hex(va),hex(current))
        struct.pack_into('<I',data,va-BIAS,new)
    if 'unit_rename_fix' in meta:
        info=meta['unit_rename_fix'];va=int(info['cap_stub_va'],16)
        at=int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
        assert data[at:at+32]==cap_stub()
        assert struct.unpack_from('<I',data,CAP_SITE-BIAS)[0]==0x0c000000|(va>>2)
        width=int(info['width_stub_va'],16)
        at=int(meta['segment_offset'],16)+width-int(meta['segment_va'],16)
        assert data[at:at+len(width_stub())]==width_stub()
        assert struct.unpack_from('<I',data,0x15ab90-BIAS)[0]==0x0c000000|(width>>2)
        assert struct.unpack_from('<I',data,0x47d354-BIAS)[0]==va+32
        return bytes(data),meta,info
    ptr=struct.unpack_from('<I',data,0x47d354-BIAS)[0]
    at=int(meta['segment_offset'],16)+ptr-int(meta['segment_va'],16)
    assert bytes(data[at:data.index(0,at)+1])==it.encode('Cerberus Ignited')
    payload=(cap_stub()+it.encode('Cerberus Ignite')).ljust(64,b'\0')+width_stub()
    data,start=extend(data,meta,payload)
    old_call=struct.unpack_from('<I',data,CAP_SITE-BIAS)[0]
    assert old_call==0x0c000000|(0x36af24>>2)
    struct.pack_into('<I',data,CAP_SITE-BIAS,0x0c000000|(start>>2))
    struct.pack_into('<I',data,0x47d354-BIAS,start+32)
    old_width=struct.unpack_from('<I',data,0x15ab90-BIAS)[0]
    assert old_width==0x0c000000|(0x157fb8>>2)
    struct.pack_into('<I',data,0x15ab90-BIAS,0x0c000000|((start+64)>>2))
    hooks=[dict(name='unit_rename_field',va=hex(a),old=struct.pack('<I',old).hex(),new=struct.pack('<I',new).hex()) for a,(old,new) in edits.items()]
    hooks += [dict(name='unit_rename_cap',va=hex(CAP_SITE),old=struct.pack('<I',old_call).hex(),new=struct.pack('<I',0x0c000000|(start>>2)).hex()),
        dict(name='unit_rename_default',va=hex(0x47d354),old=struct.pack('<I',ptr).hex(),new=struct.pack('<I',start+32).hex()),
        dict(name='unit_rename_width',va=hex(0x15ab90),old=struct.pack('<I',old_width).hex(),new=struct.pack('<I',0x0c000000|((start+64)>>2)).hex())]
    # A historical translated pointer hook is superseded by the shorter default.
    for hook in hooks:
        previous=next((h for h in meta['hooks'] if h['va']==hook['va']),None)
        if previous:previous['new']=hook['new']
        else:meta['hooks'].append(hook)
    info=dict(full_name_offset='0x634',reading_offset='0x653',control_words_offset='0x664',
        editor_bytes=48,full_name_characters=15,reading_characters=8,save_field_bytes=32,
        save_layout_unchanged=True,cap_stub_va=hex(start),width_stub_va=hex(start+64),
        editable_upgraded_defaults=['Garmraid Blaze','Cerberus Ignite'],
        name_value_x=116,reading_value_x=476,instruction_words=hooks)
    meta['unit_rename_fix']=info
    from port_ps2_translations import sha
    meta['target_sha256']=sha(data)
    return bytes(data),meta,info
