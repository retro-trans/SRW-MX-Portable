"""Advance the completed PSP chapter on PS2, including already-stuck saves."""
import struct
import keystone
from ps2_translation_native import extend
from port_ps2_translations import sha

BIAS=0xff000
SITES={0x3000f0:bytes.fromhex('c0ffbd272d108000'),
       0x1c4ba8:bytes.fromhex('b0ffbd273d00023c')}


def assemble(va):
    k=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    common='''
        addiu $sp,$sp,-32
        sd $ra,24($sp)
        sd $s0,0($sp)
        lui $v0,0x3d
        lw $s0,-0x7344($v0)
        beqz $s0,no
        nop
        lw $v0,0($s0)
        beqz $v0,no
        nop
        lw $v0,0x3a8($s0)
        addiu $v1,$zero,7
        bne $v0,$v1,no
        nop
        lw $v0,0x3a0($s0)
        addiu $v1,$zero,5
        bne $v0,$v1,no
        nop
        lw $v0,0x3ac($s0)
        addiu $v1,$zero,10
        bne $v0,$v1,no
        nop
        lw $v0,0x39c($s0)
        addiu $v1,$zero,127
        bne $v0,$v1,no
        nop
        lbu $v0,0x12($s0)
        sltiu $v0,$v0,2
        beqz $v0,no
        nop
        jal 0x347558
        move $a0,$s0
        addiu $v1,$zero,7
        bne $v0,$v1,no
        nop
        jal 0x346f38
        move $a0,$s0
        addiu $v0,$zero,1
        b done
        nop
    no:
        move $v0,$zero
    done:
        ld $s0,0($sp)
        ld $ra,24($sp)
        jr $ra
        addiu $sp,$sp,32
    '''
    blob=bytearray(k.asm('.set noreorder\n'+common,va)[0]);wrappers={}
    for site in SITES:
        blob+=bytes(-len(blob)%16);wrappers[site]=va+len(blob)
        guard='''
            lui $v0,1
            addu $v0,$v0,$a0
            lw $v0,-0x7e74($v0)
            sll $v0,$v0,2
            addu $v0,$v0,$a0
            lw $v0,0x2fec($v0)
            bnez $v0,skip
            nop
        ''' if site==0x3000f0 else ''
        relocated=('addiu $sp,$sp,-64\nmove $v0,$a0' if site==0x3000f0
                   else 'addiu $sp,$sp,-80\nlui $v0,0x3d')
        src=f'''.set noreorder
            addiu $sp,$sp,-32
            sd $ra,24($sp)
            sd $a0,0($sp)
            sd $a1,8($sp)
            {guard}
            jal {va}
            nop
        skip:
            ld $a0,0($sp)
            ld $a1,8($sp)
            ld $ra,24($sp)
            addiu $sp,$sp,32
            {relocated}
            j {site+8}
            nop
        '''
        blob+=bytes(k.asm(src,wrappers[site])[0])
    return bytes(blob),wrappers


def patch(elf,meta):
    data=bytearray(elf)
    if 'stage30_transition_fix' in meta:
        info=meta['stage30_transition_fix'];va=int(info['helper_va'],16);blob,wrappers=assemble(va)
        at=int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
        assert data[at:at+len(blob)]==blob
        for h in info['hooks']:
            a=int(h['va'],16)-BIAS;assert data[a:a+8]==bytes.fromhex(h['new'])
        return bytes(data),meta,info
    for a,old in SITES.items():assert data[a-BIAS:a-BIAS+8]==old,(hex(a),data[a-BIAS:a-BIAS+8].hex())
    start=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    blob,wrappers=assemble(start);data,actual=extend(data,meta,blob);assert actual==start
    hooks=[]
    for site,va in wrappers.items():
        raw=struct.pack('<2I',0x08000000|(va>>2),0)
        data[site-BIAS:site-BIAS+8]=raw
        h=dict(name='stage30_transition',va=hex(site),old=SITES[site].hex(),new=raw.hex())
        assert not any(hh['va']==h['va'] for hh in meta['hooks'])
        hooks.append(h);meta['hooks'].append(h)
    info=dict(helper_va=hex(start),payload_bytes=len(blob),hooks=hooks,
        normal_ending_hook='0x3000f0',stage_select_population_hook='0x1c4ba8',
        guards=dict(chapter_index=7,scene_index=5,deployment_group=10,clear_mask=127,
                    route_values=[0,1],native_location_count=7),
        native_chapter_advance='0x346f38',save_layout_unchanged=True,
        dialogue_and_map_commands_unchanged=True,recovers_already_completed_save=True)
    meta['stage30_transition_fix']=info;meta['target_sha256']=sha(data)
    return bytes(data),meta,info
