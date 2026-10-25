"""Give CWndTurnMoney's proportional numeric rows one shared right edge."""
import struct
import keystone
from ps2_translation_native import extend
from port_ps2_translations import sha

BIAS=0xff000
ANCHOR=188
DRAW_SITES=(0x152824,0x152868)
X_SITES=((0x152820,122),(0x152864,58))


def renderer():
    k=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    asm='''
        addiu $sp,$sp,-64
        sd $ra,48($sp)
        sd $a0,0($sp)
        sd $a1,8($sp)
        sd $a2,16($sp)
        sd $a3,24($sp)
        sd $8,32($sp)
        jal 0x131a88
        nop
        ld $a0,0($sp)
        ld $a1,8($sp)
        ld $a2,16($sp)
        ld $a3,24($sp)
        ld $8,32($sp)
        subu $a2,$a2,$v0
        ld $ra,48($sp)
        j 0x130d78
        addiu $sp,$sp,64
    '''
    return bytes(k.asm('.set noreorder\n'+asm)[0])


def patch(elf,meta):
    data=bytearray(elf)
    if 'turn_funds_alignment' in meta:
        info=meta['turn_funds_alignment'];va=int(info['renderer_va'],16)
        off=int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
        assert data[off:off+len(renderer())]==renderer()
        for row in info['hooks']:
            a=int(row['va'],16)-BIAS;assert data[a:a+4]==bytes.fromhex(row['new'])
        return bytes(data),meta,info
    for a,old in X_SITES:
        assert struct.unpack_from('<I',data,a-BIAS)[0]==0x24c60000|old
    for a in DRAW_SITES:
        assert struct.unpack_from('<I',data,a-BIAS)[0]==0x0c000000|(0x130d78>>2)
    data,va=extend(data,meta,renderer())
    hooks=[]
    for a,new in [(a,0x24c60000|ANCHOR) for a,_ in X_SITES]+[(a,0x0c000000|(va>>2)) for a in DRAW_SITES]:
        old=bytes(data[a-BIAS:a-BIAS+4]);raw=struct.pack('<I',new)
        data[a-BIAS:a-BIAS+4]=raw
        hook=dict(name='turn_funds_alignment',va=hex(a),old=old.hex(),new=raw.hex())
        hooks.append(hook);assert not any(h['va']==hex(a) for h in meta['hooks'])
        meta['hooks'].append(hook)
    info=dict(window_class='CWndTurnMoney',renderer_va=hex(va),renderer_bytes=len(renderer()),
        right_edge=ANCHOR,old_turn_x=122,old_funds_x=58,labels_x=12,
        row_y=[6,32],font_width=16,font_height=24,format_strings_unchanged=True,
        numeric_values_unchanged=True,hooks=hooks)
    meta['turn_funds_alignment']=info;meta['target_sha256']=sha(data)
    return bytes(data),meta,info
