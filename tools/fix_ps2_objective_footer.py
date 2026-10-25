"""Match the Objectives chapter number to its adjacent title's Latin size."""
import struct
from port_ps2_translations import sha

BIAS=0xff000
SITE=0x153e98
OLD=0x3c014180  # LUI AT, float 16.0
NEW=0x3c0141a0  # LUI AT, float 20.0, already used by the title


def patch(elf,meta):
    data=bytearray(elf)
    if 'objective_footer_alignment' in meta:
        assert struct.unpack_from('<I',data,SITE-BIAS)[0]==NEW
        return bytes(data),meta,meta['objective_footer_alignment']
    assert struct.unpack_from('<I',data,SITE-BIAS)[0]==OLD
    struct.pack_into('<I',data,SITE-BIAS,NEW)
    hook=dict(name='objective_footer_alignment',va=hex(SITE),
              old=struct.pack('<I',OLD).hex(),new=struct.pack('<I',NEW).hex())
    assert not any(h['va']==hook['va'] for h in meta['hooks'])
    meta['hooks'].append(hook)
    info=dict(window_class='CWndMission',native_draw=hex(0x153dd8),
              previous_number_cell=[16,24],number_and_title_cell=[20,24],
              actual_latin_size=20,shared_y_offset=264,
              number_x_offset=44,title_x_offset=128,
              chapter_values_and_titles_unchanged=True,hooks=[hook])
    meta['objective_footer_alignment']=info;meta['target_sha256']=sha(data)
    return bytes(data),meta,info
