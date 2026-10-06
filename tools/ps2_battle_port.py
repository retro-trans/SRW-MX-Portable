"""Port PSP English captions to all original PS2 pilot quote blocks."""
import json
import struct
import keystone

import battle_quotes as bq
from port_ps2_translations import ROOT,read_json,sha
from ps2_translation_native import extend
from ps2_font4x import FILE_BIAS

PILOT_TABLE=0x1b8174
# Three result-pointer stores, plus the direct pointer-returning getter.
SITES=[(0x2b53fc,4,6,4,0x8e050034),(0x2b58c0,4,7,4,0x8e260034),
       (0x2b5ae4,4,5,4,0xac640030),(0x2b5e10,6,2,2,None)]


def prepare():
    quotes=(ROOT/'work/source/ps2/battle_quotes.bin').read_bytes()
    static=(ROOT/'work/source/ps2/STATIC.BIN').read_bytes()
    saved=bq.PILOT_TABLE
    try:
        bq.PILOT_TABLE=PILOT_TABLE
        new,changed,overflow,message=bq.build_subfile(quotes,static)
    finally:bq.PILOT_TABLE=saved
    assert changed[:PILOT_TABLE]==static[:PILOT_TABLE]
    assert changed[PILOT_TABLE+2048:]==static[PILOT_TABLE+2048:]
    report=dict(original_bytes=len(quotes),english_bytes=len(new),native_read_limit=bq.BLOCK_MAX,
                pilot_blocks=370,translated_entries=51434,overflow_strings=len(overflow),
                overflow_bytes=sum(map(len,overflow)),message=message,
                original_quote_sha256=sha(quotes),english_quote_sha256=sha(new),
                static_sha256=sha(changed),numeric_gameplay_data_unchanged=True)
    return new,changed,overflow,report


def native_hooks(original,data,metadata,overflow):
    # Keep the native 0x4800 read; high-bit offsets resolve into the ELF pool.
    size=4*len(overflow);blob=bytearray(size);rel=[]
    for text in overflow:rel.append(len(blob));blob+=text
    data,table=extend(data,metadata,blob)
    offset=int(metadata['segment_offset'],16);segment=int(metadata['segment_va'],16)
    for i,p in enumerate(rel):struct.pack_into('<I',data,offset+table-segment+4*i,table+p)
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    hooks=[]
    for i,(site,base,off,dest,following) in enumerate(SITES):
        if following is None:
            assert struct.unpack_from('<2I',original,site-FILE_BIAS)==(0x03e00008,0x00c21021)
        else:
            wanted=(base<<21)|(off<<16)|(dest<<11)|33
            assert struct.unpack_from('<I',original,site-FILE_BIAS)[0]==wanted,hex(site)
            assert struct.unpack_from('<I',original,site+4-FILE_BIAS)[0]==following,hex(site)
        high=(table+0x8000)>>16;low=table-(high<<16)
        assembly=[f'andi $at, ${off}, 0x8000',f'beqz $at, normal{i}',
                  f'andi $at, ${off}, 0x7fff','sll $at, $at, 2',
                  f'lui ${dest}, {high}',f'addu ${dest}, ${dest}, $at',f'lw ${dest}, {low}(${dest})']
        if following is None:
            assembly+=['jr $ra','nop',f'normal{i}:','jr $ra',f'addu ${dest}, ${base}, ${off}']
        else:
            # Preserve the overwritten second instruction in both exit delay slots.
            # It is a load for sites 1/2, and the actual result-pointer store for site 3.
            original_second=['lw $a1, 0x34($s0)','lw $a2, 0x34($s1)','sw $a0, 0x30($v1)'][i]
            assembly+=[f'j {site+8}',original_second,f'normal{i}:',
                       f'addu ${dest}, ${base}, ${off}',f'j {site+8}',original_second]
        current=int(metadata['segment_va'],16)+metadata['segment_bytes'];current=(current+15)&~15
        code=bytes(ks.asm('.set noreorder\n'+'\n'.join(assembly),current)[0]);data,stub=extend(data,metadata,code)
        assert stub==current
        patch=struct.pack('<2I',0x08000000|(stub>>2),0);old=bytes(data[site-FILE_BIAS:site+8-FILE_BIAS])
        data[site-FILE_BIAS:site+8-FILE_BIAS]=patch
        hooks.append(dict(name='battle_quote_pointer_'+str(i),va=hex(site),old=old.hex(),new=patch.hex(),target=hex(stub)))
    metadata['hooks']+=hooks;metadata['target_sha256']=sha(data)
    return bytes(data),dict(overflow_table_va=hex(table),native_pointer_hooks=hooks)


if __name__=='__main__':
    data,static,overflow,report=prepare()
    out=ROOT/'work/build/ps2/campaign';out.mkdir(parents=True,exist_ok=True)
    (out/'quotes.bin').write_bytes(data);(out/'STATIC.BIN').write_bytes(static)
    (out/'quote_overflow.json').write_text(json.dumps([b.hex() for b in overflow]),encoding='utf8')
    (ROOT/'work/translation/en/ps2/battle_port.en.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
