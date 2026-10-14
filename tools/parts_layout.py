"""Parts-only name alignment and description reflow; preserve gameplay data."""
import json
import struct
from pathlib import Path
import insert_text as it
from static2_extract import sections, index
from verify_text_build import resolver
from ps2_database_port import indices
from fix_ps2_library import rebuild

ROOT=Path(__file__).resolve().parents[1]
DESCRIPTION_WIDTH=224
PSP_NAME_SITE=0x1e5f24
PSP_NAME_X=80


def patch_boot(boot):
    out=bytearray(boot)
    old=0x2466006e; new=0x24660000|PSP_NAME_X
    assert struct.unpack_from('<I',out,PSP_NAME_SITE+0x60)[0] in (old,new)
    struct.pack_into('<I',out,PSP_NAME_SITE+0x60,new)
    site=0x1e5f30;draw=0xaeb08
    call=struct.unpack_from('<I',out,site+0x60)[0]
    import keystone
    asm='''.set noreorder
.option pic0
addiu $sp,$sp,-64
sw $ra,60($sp)
sw $a0,16($sp)
sw $a1,20($sp)
sw $a2,24($sp)
sw $a3,28($sp)
sw $t0,32($sp)
lw $t1,8($a0)
lw $t2,12($a0)
sw $t1,36($sp)
sw $t2,40($sp)
jal 0xb03e4
nop
slti $t1,$v0,163
bnez $t1,draw
nop
mtc1 $v0,$f2
cvt.s.w $f2,$f2
lui $t1,0x4320
mtc1 $t1,$f4
div.s $f2,$f4,$f2
lw $a0,16($sp)
lwc1 $f0,8($a0)
mul.s $f0,$f0,$f2
swc1 $f0,8($a0)
lwc1 $f0,12($a0)
mul.s $f0,$f0,$f2
swc1 $f0,12($a0)
draw:
lw $a0,16($sp)
lw $a1,20($sp)
lw $a2,24($sp)
lw $a3,28($sp)
lw $t0,32($sp)
jal 0xaeb08
nop
lw $a0,16($sp)
lw $t1,36($sp)
lw $t2,40($sp)
sw $t1,8($a0)
sw $t2,12($a0)
lw $ra,60($sp)
jr $ra
addiu $sp,$sp,64'''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm(asm)[0])
    if call!=0x0c000000|(draw>>2):
        destination=(call&0x3ffffff)<<2
        assert call>>26==3 and out[destination+0x60:destination+0x60+len(code)]==code,'Unknown Parts name wrapper'
        return bytes(out)
    out,base=it.extend_segment(out,code)
    struct.pack_into('<I',out,site+0x60,0x0c000000|(base>>2))
    relocations=[(base+off,4) for off in range(0,len(code),4)
                 if struct.unpack_from('<I',code,off)[0]>>26==3]
    return bytes(it.append_relocs(out,relocations))


def lines(metadata=None):
    desc=it.load('static2/descriptions.json')['XPrt']
    if metadata is None:
        result={int(k):it.wrap(it.clean(v),DESCRIPTION_WIDTH) for k,v in desc.items() if v}
        assert all(len(v)<=4 for v in result.values())
    else:
        from ps2_narration_port import native_width
        result={}
        for k,v in desc.items():
            if not v:continue
            output=[];line=''
            for word in it.clean(v).split():
                candidate=(line+' '+word).strip()
                if native_width(candidate,metadata)>258:
                    assert line;output.append(line);line=word
                else:line=candidate
                assert native_width(line,metadata)<=258
            if line:output.append(line)
            result[int(k)]=output
        assert all(len(v)<=5 for v in result.values())
    return result


def pack_sent(offsets, values, flags, limit):
    head=12+4*len(values);payload=bytearray();cache={};new=[]
    for ident,raw in enumerate(values):
        if ident in flags:new.append(offsets[ident]);continue
        if raw not in cache:cache[raw]=head+len(payload);payload+=raw
        new.append(cache[raw])
    size=head+len(payload)
    assert size<=limit,('Sentence allocation',size,limit)
    return b'Sent'+struct.pack('<2I',limit,len(values))+struct.pack(f'<{len(new)}I',*new)+payload+bytes(limit-size)


def psp(static,boot):
    native=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    original=sections(native);slots=it.fixh_slots(bytearray(native),original)
    current={tag:it.VERS+struct.unpack_from('<I',static,slot)[0] for tag,slot in slots.items()}
    so=current['Sent'];size,count=struct.unpack_from('<2I',static,so+4)
    offsets=list(struct.unpack_from(f'<{count}I',static,so+12))
    get=resolver(static,boot);before=[get(so,p) for p in offsets]
    values=[raw+b'\0' for raw in before];flags={i for i,p in enumerate(offsets) if p&0x80000000}
    target=lines();old_parts=index(static,current['XPrt'],38);parts=[]
    for ident,old in enumerate(old_parts):
        if ident not in target:parts.append(old);continue
        ids=[]
        for line in target[ident]:
            ids.append(len(values));values.append(it.encode(line))
        parts.append(ids)
    raw_index=indices('XPrt',parts)
    reserved=min([so+size]+[a for tag,a in current.items() if tag!='Sent' and so<a<so+size])
    new_at=(reserved-len(raw_index))&~15
    packed=pack_sent(offsets,values,flags,new_at-so)
    out=bytearray(static)
    out[so:so+len(packed)]=packed
    # Keep the fixed original section size, including reserved relocated indexes.
    struct.pack_into('<I',out,so+4,size)
    out[new_at:new_at+len(raw_index)]=raw_index
    struct.pack_into('<I',out,slots['XPrt'],new_at-it.VERS)
    result=bytes(out);after_get=resolver(result,boot)
    new_offsets=struct.unpack_from(f'<{len(values)}I',result,so+12)
    assert [after_get(so,p) for p in new_offsets[:count]]==before
    for tag,at in current.items():
        if tag in ('Sent','XPrt'):continue
        n=struct.unpack_from('<I',static,at+4)[0]
        assert result[at:at+n]==static[at:at+n],tag
    for ident,english in target.items():
        ids=index(result,new_at,38)[ident]
        assert [after_get(so,new_offsets[i]) for i in ids]==[it.encode(x)[:-1] for x in english]
    assert len(result)==len(static)
    return result,dict(platform='PSP',description_wrap_width=DESCRIPTION_WIDTH,part_entries=len(target),
        old_sentence_ids_preserved=count,rows=target,numeric_and_other_index_data_preserved=True,
        original_and_target_bytes=len(static),relocated_index=new_at)


def ps2(fix,elf,metadata):
    s=sections(fix,0);so,_,count=s['Sent']
    offsets=list(struct.unpack_from(f'<{count}I',fix,so+12))
    def get(p):
        if p&0x80000000:
            address=p&0x7fffffff
            ph=struct.unpack_from('<I',elf,28)[0];pn=struct.unpack_from('<H',elf,44)[0]
            for n in range(pn):
                kind,off,va,_,size=struct.unpack_from('<5I',elf,ph+n*32)
                if kind==1 and va<=address<va+size:
                    a=off+address-va;return elf[a:elf.index(0,a)]
            raise AssertionError(hex(address))
        a=so+p;return fix[a:fix.index(0,a)]
    before=[get(p) for p in offsets]
    tables={tag:index(fix,a,c) for tag,(a,_,c) in s.items() if tag.startswith('X')}
    protected={i for tag,rows in tables.items() if tag!='XPrt' for row in rows for i in row}
    used={i for rows in tables.values() for row in rows for i in row}
    editable=sorted({i for row in tables['XPrt'][1:] for i in row}-protected)
    editable+=sorted(i for i,raw in enumerate(before) if not raw and i not in used and i not in editable)
    values=[raw+b'\0' for raw in before];flags={i for i,p in enumerate(offsets) if p&0x80000000}
    for ident in editable:values[ident]=b'\0';flags.discard(ident)
    available=iter(editable);cache={};target=lines(metadata);parts=[tables['XPrt'][0]]
    for ident in range(1,38):
        ids=[]
        for line in target[ident]:
            raw=it.encode(line)
            if raw not in cache:
                row=next(available);cache[raw]=row;values[row]=raw
            ids.append(cache[raw])
        parts.append(ids)
    # Fixed heap budget: replace only unshared old part storage, not other rows.
    packed=pack_sent(offsets,values,flags,s['Sent'][1])
    useful=12+4*len(values)+len(b''.join(set(v for i,v in enumerate(values) if i not in flags)))
    packed=packed[:useful]
    struct_size=bytearray(packed);struct.pack_into('<I',struct_size,4,len(packed))
    output=rebuild(fix,{'Sent':bytes(struct_size),'XPrt':indices('XPrt',parts)})
    assert len(output)<=len(fix),('Fixed heap capacity',len(output),len(fix))
    output+=bytes(len(fix)-len(output));ns=sections(output,0)
    no=ns['Sent'][0];new_offsets=struct.unpack_from(f'<{count}I',output,no+12)
    for tag,(a,n,_) in s.items():
        if tag in ('Sent','XPrt','Fixh'):continue
        b,nn,_=ns[tag];assert n==nn and output[b:b+nn]==fix[a:a+n],tag
    for ident in protected:
        if new_offsets[ident]&0x80000000:assert new_offsets[ident]==offsets[ident]
        else:
            a=no+new_offsets[ident];assert output[a:output.index(0,a)]==before[ident]
    for ident,english in target.items():
        ids=index(output,ns['XPrt'][0],38)[ident]
        actual=[]
        for i in ids:
            a=no+new_offsets[i];actual.append(output[a:output.index(0,a)])
        assert actual==[it.encode(x)[:-1] for x in english]
    return output,dict(platform='PS2',description_wrap_width=258,part_entries=len(target),
        protected_sentence_rows_verified=len(protected),rows=target,numeric_and_other_index_data_preserved=True,
        original_and_target_bytes=len(fix),equipped_names_already_on_separate_native_rows=True)
