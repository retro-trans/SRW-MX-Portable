"""Copy translated forecast action labels by bytes, through their terminator.

Original LD copies assume aligned eight-byte Japanese labels. English UI pool
strings have arbitrary byte alignment and may exceed that fixed copy length.
"""
import copy
import struct

import keystone
from ps2_font4x import FILE_BIAS
from ps2_translation_native import extend

COPY_SITES = [
    dict(name='left_no_counter', site=0x17972c, clear=[0x179730,0x179734,0x17973c],
         resume=0x1797fc, source=0x779ada),
    dict(name='left_support_def', site=0x179774, clear=[0x179778,0x17977c,0x179784],
         resume=0x1797f8, source=0x779a9b),
    dict(name='right_action', site=0x17a28c, clear=[0x17a290,0x17a294,0x17a29c],
         resume=0x17a2f4, source=0x779a9b),
]


def patch(data, metadata):
    data, metadata = bytes(data), copy.deepcopy(metadata)
    source_data = data
    old_heap = metadata['heap_start']
    ks = keystone.Ks(keystone.KS_ARCH_MIPS,
                     keystone.KS_MODE_MIPS64 | keystone.KS_MODE_LITTLE_ENDIAN)
    # V0/A0/V1 are scratch results of the replaced native copy. A1 (support
    # status), saved registers, SP and the original source bytes are preserved.
    assembly = '''.set noreorder
.option pic0
move $a0,$sp
copy:
lbu $v1,0($v0)
sb $v1,0($a0)
addiu $v0,$v0,1
bnez $v1,copy
addiu $a0,$a0,1
jr $ra
nop
'''
    va = (int(metadata['segment_va'],16)+metadata['segment_bytes']+15)&~15
    code = bytes(ks.asm(assembly,va)[0])
    assert len(code) == 32
    data, actual = extend(data,metadata,code)
    assert va == actual
    data = bytearray(data)
    changes = []
    for row in COPY_SITES:
        site = row['site']
        # Guard the complete native copy sequence; branch/conditional behavior
        # remains unchanged while all partial stores are removed.
        wanted = [0x90430008,0xdc440000,0xa3a30008] if row['name'] != 'left_support_def' else [0x90440008,0xdc430000,0xa3a40008]
        assert list(struct.unpack_from('<3I',source_data,site-FILE_BIAS)) == wanted
        assert struct.unpack_from('<I',source_data,row['clear'][-1]-FILE_BIAS)[0] == (0xffa30000 if row['name']=='left_support_def' else 0xffa40000)
        for address,value in [(site,0x0c000000|(va>>2))]+[(a,0) for a in row['clear']]:
            offset = address-FILE_BIAS
            old = bytes(data[offset:offset+4])
            new = struct.pack('<I',value)
            data[offset:offset+4] = new
            changes.append(dict(va=hex(address),offset=offset,before=old.hex(),after=new.hex()))
    # The helper fits existing final-segment alignment padding; it does not
    # consume any additional heap address space in the released v0.9.0 layout.
    assert metadata['heap_start'] == old_heap
    return bytes(data), metadata, dict(helper_va=hex(va),helper_bytes=len(code),
        helper_assembly=assembly,sites=COPY_SITES,changes=changes,
        heap_boundary_preserved=True,terminated_full_string_copy=True,
        source_alignment_required=1,maximum_expected_bytes=64)
