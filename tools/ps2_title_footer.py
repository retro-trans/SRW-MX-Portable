"""Native PS2 title renderer footer, independent of the animated background."""
import copy
import struct
import keystone
import insert_text as it
from ps2_font4x import FILE_BIAS
from ps2_translation_native import extend

MAGIC = b'MX_TITLE_CREDIT1'
SIZE = 1536
SITE = 0x2c1e28
ORIGINAL = struct.pack('<I',0x0c000000 | (0x12e640 >> 2))
URL = 'github.com/retro-trans'

def locate(data):
    a=data.find(MAGIC)
    if a<0:return None
    assert data.find(MAGIC,a+1)<0
    return a,struct.unpack_from('<I',data,a+16)[0]

def block(va, version):
    payload=bytearray(SIZE)
    payload[:16]=MAGIC
    struct.pack_into('<I',payload,16,va)
    payload[32:32+len(it.encode('v'+version))]=it.encode('v'+version)
    payload[96:96+len(it.encode(URL))]=it.encode(URL)
    assert len(it.encode('v'+version))<=64 and len(it.encode(URL))<=64
    # One private native font context: no shared menu-font state is modified.
    ctx=va+160
    asm=f'''
        addiu $sp,$sp,-64
        sd $ra,56($sp)
        sd $s0,0($sp)
        sd $s2,8($sp)
        sd $s3,16($sp)
        jal 0x12e640
        nop
        lw $v0,0x1284($s1)
        addiu $v1,$zero,4
        beq $v0,$v1,visible
        addiu $v1,$zero,5
        bne $v0,$v1,finish
        nop
    visible:
        lw $v0,0x1288($s1)
        slti $v1,$v0,3
        bnez $v1,finish
        nop
        li $s0,{ctx}
        jal 0x130498
        move $a0,$s0
        jal 0x1305d8
        move $a0,$s0
        lui $t8,0x4180
        sw $t8,0($s0)
        sw $t8,4($s0)
        li $s2,{va+32}
        addiu $s3,$zero,250
        jal line
        nop
        li $s2,{va+96}
        addiu $s3,$zero,268
        jal line
        nop
    finish:
        ld $s0,0($sp)
        ld $s2,8($sp)
        ld $s3,16($sp)
        ld $ra,56($sp)
        jr $ra
        addiu $sp,$sp,64
    line:
        addiu $sp,$sp,-32
        sd $ra,24($sp)
        move $a0,$s0
        jal 0x1319c0
        move $a1,$s2
        addiu $t8,$zero,626
        subu $t8,$t8,$v0
        sw $t8,0($sp)
        li $t8,0x800a0a0a
        sw $t8,8($s0)
        sw $t8,12($s0)
        sw $t8,16($s0)
        sw $t8,20($s0)
        move $a0,$s0
        move $a1,$s2
        lw $a2,0($sp)
        addiu $a2,$a2,1
        addiu $a3,$s3,1
        jal 0x130610
        addiu $8,$zero,-1
        li $t8,0x80ffffff
        sw $t8,8($s0)
        sw $t8,12($s0)
        sw $t8,16($s0)
        sw $t8,20($s0)
        move $a0,$s0
        move $a1,$s2
        lw $a2,0($sp)
        move $a3,$s3
        jal 0x130610
        addiu $8,$zero,-1
        ld $ra,24($sp)
        jr $ra
        addiu $sp,$sp,32
    '''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    # Explicit direct calls keep this independent of assembler PIC defaults
    # affected by other native libraries loaded in the verifier process.
    code=bytes(ks.asm('.set noreorder\n.option pic0\n'+asm,va+256)[0])
    assert len(code)<=SIZE-256
    payload[256:256+len(code)]=code
    return bytes(payload),asm

def patch(data,version,metadata=None):
    data=bytes(data);found=locate(data);meta=copy.deepcopy(metadata)
    before=data[SITE-FILE_BIAS:SITE-FILE_BIAS+4]
    if found:
        offset,va=found
        # Only the registered version fields and runtime-private context vary.
        expected,_=block(va,version)
        restored=bytearray(data[offset:offset+SIZE])
        restored[32:160]=expected[32:160]
        assert bytes(restored)==expected,'Unknown title renderer revision'
        assert before==struct.pack('<I',0x0c000000 | ((va+256)>>2))
        out=bytearray(data);out[offset:offset+SIZE]=expected
    else:
        assert before==ORIGINAL,'Unexpected native title draw call'
        if meta is None:
            kind,offset,va,_,size,*_=struct.unpack_from('<8I',data,148)
            assert kind==1 and offset+size==len(data)
            meta=dict(segment_offset=hex(offset),segment_va=hex(va),segment_bytes=size,hooks=[])
        va=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
        payload,_=block(va,version)
        out,actual=extend(data,meta,payload);assert actual==va
        offset=len(out)-SIZE
        struct.pack_into('<I',out,SITE-FILE_BIAS,0x0c000000 | ((va+256)>>2))
        hook=dict(name='title_footer',va=hex(SITE),old=before.hex(),
                  new=bytes(out[SITE-FILE_BIAS:SITE-FILE_BIAS+4]).hex(),target=hex(va+256))
        meta['hooks'].append(hook)
    assert len(out)==len(data) or len(out)>=len(data)+SIZE
    if meta is not None:
        from title_footer import sha
        meta['target_sha256']=sha(out)
    return bytes(out),dict(version=version,credit=URL,asset='/SLPS_253.45;1',
        mechanism='Native title draw callback',block_offset=offset,block_va=hex(va),block_bytes=SIZE,
        hook_va=hex(SITE),renderer_va=hex(va+256),private_context_va=hex(va+160),
        private_context_bytes=96,font_size=16,right_edge=626,line_y=[250,268],
        byte_ranges=[[SITE-FILE_BIAS,SITE-FILE_BIAS+4],[offset,offset+SIZE]],
        footer_strings=['v'+version,URL]),meta

def verify(data,version):
    found=locate(data);assert found,'Missing native title renderer footer'
    a,va=found;expected,_=block(va,version)
    assert data[a:a+SIZE]==expected,'Native title footer/build version mismatch'
    assert data[SITE-FILE_BIAS:SITE-FILE_BIAS+4]==struct.pack('<I',0x0c000000 | ((va+256)>>2))
    return dict(renderer_va=hex(va+256),block_va=hex(va),block_offset=a,
                native_title_hook_verified=True,footer_strings=['v'+version,URL])
