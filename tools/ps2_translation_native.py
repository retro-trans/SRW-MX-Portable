"""Native PS2 English text pool and checked executable string references."""
from collections import defaultdict
import json
import struct

from port_ps2_translations import ROOT,read_json,sha
from ps2_font4x import FILE_BIAS
import insert_text as it


def extend(data,metadata,payload,alignment=16):
    data=bytearray(data);offset=int(metadata['segment_offset'],16);va=int(metadata['segment_va'],16)
    old=metadata['segment_bytes'];start=(va+old+alignment-1)&~(alignment-1)
    data+=bytes(start-va-old)+payload
    size=start-va+len(payload);end=(va+size+127)&~127
    assert end<0x800000
    struct.pack_into('<2I',data,148+16,size,size)
    hi=(end+0x8000)>>16;lo=end-(hi<<16)
    for address,word in [(0x100180,0x3c040000|hi),(0x100188,0x24840000|(lo&65535))]:
        struct.pack_into('<I',data,address-FILE_BIAS,word)
        for hook in metadata['hooks']:
            if int(hook['va'],16)==address:hook['new']=struct.pack('<I',word).hex()
    metadata.update(segment_bytes=size,heap_start=hex(end),target_sha256=sha(data))
    assert len(data)==offset+size
    return data,start


def written_register(word):
    op=word>>26;rt=(word>>16)&31;rd=(word>>11)&31;fun=word&63
    if op==0:return rd if fun not in (8,17,19,24,25,26,27) else None
    if op in (2,4,5,6,7,20,21,22,23,40,41,42,43,44,45,46,47,56,57,61,63):return None
    if op==3:return 31
    if op==1:return 31 if rt in (16,17,18,19) else None
    if op in (16,17,18):return rt if (word>>21)&31 in (0,1,2) else None
    return rt


def source_registers(word):
    op=word>>26;rs=(word>>21)&31;rt=(word>>16)&31;fun=word&63
    if op==15:return set()
    if op==0:
        if fun in (0,2,3,56,58,59,60,62,63):return {rt}
        return {rs,rt}-{0}
    if op in (2,3):return set()
    if op in (4,5,20,21,40,41,42,43,44,45,46,47,56,57,61,63):return {rs,rt}-{0}
    if op in (16,17,18):return {rt} if (word>>21)&31 in (4,5,6) else set()
    return {rs}-{0}


def patch_ui(original,data,metadata):
    inventory=read_json(ROOT/'work/source/text_inventory/boot_strings.json')
    translations,_=it.boot_translations();by_va={x['va']:x['text'] for x in inventory}
    lookup=defaultdict(set)
    for va,(en,raw) in translations.items():
        if va in by_va:lookup[by_va[va]].add((en,raw))
    # Only original loaded data; never executable bytes, overlay metadata or suffixes.
    matches={};enc={}
    for jp,values in lookup.items():
        if len(values)!=1:continue
        en,raw=next(iter(values));target=it.encode(it.clean(en),raw=raw);needle=jp.encode('cp932')+b'\0';position=0
        while (position:=original.find(needle,position))>=0:
            if 0x2c5e00<=position<0x3c5d00 and (position==0 or original[position-1]==0):
                matches[position+FILE_BIAS]=(jp,en,raw);enc[position+FILE_BIAS]=target
            position+=1
    # One signed-low 64KiB page means shared LUI groups can keep a single high word.
    current=int(metadata['segment_va'],16)+metadata['segment_bytes']
    start=((current+0x8000+0xffff)&~0xffff)-0x8000
    blob=bytearray();pointers={};cache={}
    for va in sorted(matches):
        raw=enc[va]
        if raw not in cache:cache[raw]=start+len(blob);blob+=raw
        pointers[va]=cache[raw]
    assert len(blob)<0x10000
    current=int(metadata['segment_va'],16)+metadata['segment_bytes']
    data,pool=extend(data,metadata,bytes(start-current)+blob,alignment=1)
    assert pool==current
    direct=[];groups=[];changed=set();rejected=[]
    for off in range(0x2c5e00,0x3c5d00,4):
        ptr=struct.unpack_from('<I',original,off)[0]
        if ptr in pointers:
            struct.pack_into('<I',data,off,pointers[ptr]);changed.add(ptr)
            direct.append(dict(site=hex(off+FILE_BIAS),source=hex(ptr),target=hex(pointers[ptr])))
    for off in range(0x1000,0x2bef18,4):
        word=struct.unpack_from('<I',original,off)[0]
        if word>>26!=15 or not 0x3c<=(word&65535)<=0x4c:continue
        register=(word>>16)&31;uses=[];unsafe=False;ended=False;delay_end=None
        for following in range(off+4,min(off+4*65,0x2bef18),4):
            instr=struct.unpack_from('<I',original,following)[0];op=instr>>26;rs=(instr>>21)&31
            if register in source_registers(instr):
                if op in (9,13) and rs==register:
                    low=instr&65535
                    if op==9 and low>=32768:low-=65536
                    address=((word&65535)<<16)+low
                    if address in pointers:uses.append((following,instr,address))
                    else:unsafe=True
                else:unsafe=True
            if written_register(instr)==register:
                ended=True;break
            if delay_end==following:ended=True;break
            if op in (2,3) or (op==0 and instr&63 in (8,9)):
                # A call clobbers temporary registers after its delay slot.
                if register not in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,24,25):unsafe=True
                delay_end=following+4
            elif op in (1,4,5,6,7,20,21,22,23):unsafe=True;break
        if not uses:continue
        if unsafe or not ended:
            rejected.append(dict(site=hex(off+FILE_BIAS),sources=[hex(v[2]) for v in uses]));continue
        high=(start+0x8000)>>16
        assert all((pointers[va]+0x8000)>>16==high for _,_,va in uses)
        struct.pack_into('<I',data,off,(word&0xffff0000)|high)
        for where,instr,va in uses:
            ptr=pointers[va];lo=(ptr-high*65536)&65535
            if instr>>26==13:
                # ORI cannot represent a negative signed low. Switch to ADDIU.
                instr=(instr&0x03ffffff)|(9<<26)
            struct.pack_into('<I',data,where,(instr&0xffff0000)|lo);changed.add(va)
        groups.append(dict(site=hex(off+FILE_BIAS),references=len(uses)))
    # Do not modify the original string storage: all unchanged references remain valid.
    manifest=[dict(source=hex(va),source_sha256=sha(matches[va][0].encode('cp932')),
                   english=matches[va][1],target=hex(pointers[va])) for va in sorted(changed)]
    report=dict(translated_string_locations=len(changed),source_matches=len(matches),
                pointer_words=len(direct),instruction_groups=len(groups),
                deferred_shared_reference_groups=rejected,texts=manifest,direct_references=direct,groups=groups)
    metadata['target_sha256']=sha(data)
    return bytes(data),report


def patch_spirits(original,data,metadata):
    import keystone
    from static2_extract import sections
    fix=(ROOT/'work/source/ps2/FIX00.DAT').read_bytes()
    psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    s=sections(fix,0);p=sections(psp);english=read_json(ROOT/'work/translation/en/static2/spirits.json')
    def names(blob,section):
        off,size,count=section
        return [blob[off+12+i*16:off+24+i*16].split(b'\0')[0].decode('cp932') for i in range(count)]
    lookup={jp:english.get(str(i)) for i,jp in enumerate(names(psp,p['Sprt']))}
    translated=[lookup[jp] or '?'*len(jp) for jp in names(fix,s['Sprt'])]
    blob=bytearray(4*len(translated));rel=[]
    for en in translated:rel.append(len(blob));blob+=it.encode(en)
    data,table=extend(data,metadata,blob)
    offset=int(metadata['segment_offset'],16);segment=int(metadata['segment_va'],16)
    for i,p in enumerate(rel):struct.pack_into('<I',data,offset+table-segment+4*i,table+p)
    site=0x332730
    assert original[site-FILE_BIAS:site+8-FILE_BIAS]==bytes.fromhex('f0ffbd270000bfff')
    hi=(table+0x8000)>>16;lo=table-(hi<<16)
    assembly=f'''.set noreorder
sltiu $at, $a1, {len(translated)}
beqz $at, original_name
nop
sll $at, $a1, 2
lui $v0, {hi}
addu $v0, $v0, $at
lw $v0, {lo}($v0)
jr $ra
nop
original_name:
j 0x332788
nop'''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    current=(int(metadata['segment_va'],16)+metadata['segment_bytes']+15)&~15
    code=bytes(ks.asm(assembly,current)[0]);data,stub=extend(data,metadata,code)
    patch=struct.pack('<2I',0x08000000|(stub>>2),0)
    data[site-FILE_BIAS:site+8-FILE_BIAS]=patch
    metadata['hooks'].append(dict(name='spirit_name',va=hex(site),old=original[site-FILE_BIAS:site+8-FILE_BIAS].hex(),new=patch.hex(),target=hex(stub)))
    metadata['target_sha256']=sha(data)
    return bytes(data),dict(english_names=translated,table_va=hex(table),stub_va=hex(stub))


def patch_sentences(original,data,metadata,fix,overflow):
    """Resolve marked Sent offsets as native pointers; preserve negative dummy behavior."""
    import keystone
    from static2_extract import sections
    blob=b''.join(overflow);data,pool=extend(data,metadata,blob);fix=bytearray(fix)
    off,size,count=sections(fix,0)['Sent'];cursor=pool;pointers=[]
    for text in overflow:pointers.append(cursor);cursor+=len(text)
    for i in range(count):
        value=struct.unpack_from('<I',fix,off+12+4*i)[0]
        if value&0x80000000:
            assert value&0x7fffffff<len(pointers)
            struct.pack_into('<I',fix,off+12+4*i,0x80000000|pointers[value&0x7fffffff])
    site=0x332518;assert original[site-FILE_BIAS:site+8-FILE_BIAS]==bytes.fromhex('0000828c80280500')
    assembly='''.set noreorder
lw $v0, 0($a0)
sll $a1, $a1, 2
addu $a1, $a1, $v0
lw $v1, 0xc($a1)
bgez $v1, normal
nop
lui $at, 0x8000
xor $v0, $v1, $at
lui $at, 0x71
ori $at, $at, 0x5000
sltu $at, $v0, $at
bnez $at, invalid
nop
lui $at, 0x80
sltu $at, $v0, $at
beqz $at, invalid
nop
jr $ra
nop
invalid:
jr $ra
move $v0, $zero
normal:
jr $ra
addu $v0, $v0, $v1'''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    current=(int(metadata['segment_va'],16)+metadata['segment_bytes']+15)&~15
    code=bytes(ks.asm(assembly,current)[0]);data,stub=extend(data,metadata,code)
    patch=struct.pack('<2I',0x08000000|(stub>>2),0);data[site-FILE_BIAS:site+8-FILE_BIAS]=patch
    metadata['hooks'].append(dict(name='sentence_pointer',va=hex(site),old=original[site-FILE_BIAS:site+8-FILE_BIAS].hex(),new=patch.hex(),target=hex(stub)))
    metadata['target_sha256']=sha(data)
    return bytes(data),bytes(fix),dict(pool_va=hex(pool),pool_bytes=len(blob),rows=len(overflow),pointers=pointers,stub_va=hex(stub))
