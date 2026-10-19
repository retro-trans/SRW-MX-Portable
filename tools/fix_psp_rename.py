"""Fit full English robot names in the existing unit-rename object's 48 bytes.

Native save fields already hold 32 bytes each. Only the editor packs its two
fields at a 23-byte stride. Use 31 bytes for Name and the remaining 17 for
Reading, without moving the control words at +0x644 or changing save layout.
"""
import struct

DEFAULT = 'Cerberus Ignite'
CAP_SITE = 0x1c3580


def cap_stub():
    import insert_text as it
    i,r=it._i,it._r
    return it._words(i(9,0,8,16),i(5,18,0,2),0,i(9,0,8,30),
                     r(4,8,8,0,33),i(40,8,0,0),(2<<26)|(0x2594d0>>2),0)

FULL_LIMITS = (0x1c33b0,0x1c35b0,0x1c3764,0x1c3c34,0x1c3db8,0x1c427c,
    0x1c438c,0x1c4790,0x1c4824,0x1c4b38,0x1c4bcc,0x1c4e4c,0x1c4ea4,
    0x1c4fec,0x1c5114,0x1c5af0)
READ_LIMITS = (0x1c33ac,0x1c35ac,0x1c3760,0x1c3c38,0x1c3dbc,0x1c4280,
    0x1c4388,0x1c4794,0x1c4828,0x1c4b3c,0x1c4bd0,0x1c4e48,0x1c4ea8,
    0x1c4ff0,0x1c5110,0x1c5af4)
FULL_BUDGETS = (0x1c3770,0x1c3c44,0x1c3dc8,0x1c428c,0x1c4398,0x1c476c,
    0x1c4834,0x1c4b14,0x1c4bdc,0x1c4ffc,0x1c5120,0x1c5b00)
READ_BUDGETS = (0x1c3774,0x1c3c48,0x1c3dcc,0x1c4290,0x1c439c,0x1c4770,
    0x1c4838,0x1c4b18,0x1c4be0,0x1c5000,0x1c5124,0x1c5b04)
MULTIPLY_SITES = (0x1c366c,0x1c39e0,0x1c3c4c,0x1c3dd0,0x1c4294,0x1c43a0,
    0x1c4774,0x1c47c0,0x1c47ec,0x1c483c,0x1c4b1c,0x1c4b68,0x1c4b94,
    0x1c4be4,0x1c4eb0,0x1c5004,0x1c5128,0x1c5b30,0x1c5b8c)


def changes(original):
    patches = {}
    def word(site):
        return struct.unpack_from('<I',original,site+0x60)[0]
    def immediate(site, old, new):
        current = word(site)
        assert current >> 26 == 9 and current & 65535 == old, hex(site)
        patches[site] = (current, (current & 0xffff0000) | new)
    for sites, old, new in [(FULL_LIMITS,22,30),(READ_LIMITS,12,16),
            (FULL_BUDGETS,154,210),(READ_BUDGETS,84,112),
            ((0x1c3464,0x1c35dc),23,31)]:
        for site in sites:
            immediate(site,old,new)
    for site in MULTIPLY_SITES:
        a,b,c,d = struct.unpack_from('<4I',original,site+0x60)
        index,tmp = (a>>16)&31,(a>>11)&31
        assert a == (index<<16 | tmp<<11 | 1<<6)
        assert b == (tmp<<21 | index<<16 | tmp<<11 | 33)
        assert c == (tmp<<16 | tmp<<11 | 3<<6)
        assert d == (tmp<<21 | index<<16 | tmp<<11 | 35)
        for offset,old,new in [(0,a,(a&~(31<<6))|(5<<6)),(4,b,0),(8,c,0)]:
            patches[site+offset] = old,new
    # Three compiler-scheduled variants of the same index*23 operation.
    special = {
        0x1c4e98:(0x00061040,0x00061140),
        0x1c4e5c:(0x00461021,0), 0x1c4e60:(0x000210c0,0),
        0x1c4f4c:(0x00052040,0x00052140),
        0x1c4f54:(0x00851021,0x00801021), 0x1c4f58:(0x000210c0,0),
        0x1c5bdc:(0x00054840,0x00054940),
        0x1c5be0:(0x01254821,0), 0x1c5be4:(0x000948c0,0),
    }
    for site,pair in special.items():
        assert word(site) == pair[0], (hex(site),hex(word(site)))
        patches[site] = pair
    return patches


def patch_boot(boot):
    # Derive expected native instructions from the immutable original, allowing
    # guarded idempotence on already-corrected executables too.
    from pathlib import Path
    original = (Path(__file__).resolve().parents[1]/'work/build/iso/BOOT.BIN').read_bytes()
    patches = changes(original)
    result = bytearray(boot)
    for site,(old,new) in patches.items():
        value = struct.unpack_from('<I',result,site+0x60)[0]
        assert value in (old,new), ('Unexpected rename code',hex(site),hex(value))
        struct.pack_into('<I',result,site+0x60,new)
    # The historical translated default is 16 glyphs, one beyond the native
    # 32-byte save slot. Use Akurasu's Pilot Database spelling for this editable
    # default; keep the separate Mech List database names unchanged.
    import insert_text as it
    pointer=struct.unpack_from('<I',result,0x27f1bc+0x60)[0]+0x60
    old=it.encode('Cerberus Ignited')
    new=it.encode(DEFAULT)
    current_text=bytes(result[pointer:result.index(0,pointer)+1])
    assert current_text in (old,new)
    if current_text==old:
        result[pointer:pointer+len(old)]=new.ljust(len(old),b'\0')
    # Existing saves can still contain the old overlong default. Terminate the
    # editor's loaded field at its new bound before native strlen/padding.
    current=struct.unpack_from('<I',result,CAP_SITE+0x60)[0]
    old_call=(3<<26)|(0x2594d0>>2)
    if current==old_call:
        result,base=it.extend_segment(result,cap_stub())
        struct.pack_into('<I',result,CAP_SITE+0x60,(3<<26)|(base>>2))
        result=it.append_relocs(result,[(base+24,4)])
    else:
        assert current>>26==3
        base=(current&0x3ffffff)<<2
        assert bytes(result[base+0x60:base+0x60+32])==cap_stub()
    return bytes(result)


def report():
    return dict(full_name_characters=15,reading_characters=8,
        full_name_offset='0x614',reading_offset='0x633',control_words_offset='0x644',
        editor_bytes=48,save_field_bytes=32,save_layout_unchanged=True,
        original_editor_stride=23,new_editor_stride=31,
        existing_valid_names_preserved=True,editable_default=DEFAULT,
        old_overlong_saved_names_safely_capped=True)
