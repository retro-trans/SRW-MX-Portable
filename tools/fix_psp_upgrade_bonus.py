"""Keep temporary unit names out of PSP upgrade-bonus window storage.

Both draw routines finish consuming their stack-local label tables before
looking up the unit name. Reuse those tables for the name until its immediate
draw, just as the Parts fix reuses a dead numeric scratch row. No stack frame,
class allocation, name, save data or bonus selection instruction changes.
"""
import struct

SCRATCH = 0x20
OLD_NAME = 0xb0c
MENUS = {
    'unit': dict(start=0x1dd74c, end=0x1dd9d8, capacity=112,
                 sites=(0x1dd8e4,0x1dd900,0x1dd91c,0x1dd93c,0x1dd958,0x1dd990),
                 copy_destination_site=0x1dd958),
    'weapon': dict(start=0x1de764, end=0x1de9e8, capacity=128,
                   sites=(0x1de8f8,0x1de914,0x1de930,0x1de950,0x1de96c,0x1de9a0),
                   copy_destination_site=0x1de96c),
}


def patch_boot(boot):
    out=bytearray(boot)
    for menu in MENUS.values():
        for site in menu['sites']:
            dest=4 if site==menu['copy_destination_site'] else 5
            old=0x24000000|(16<<21)|(dest<<16)|OLD_NAME
            new=0x24000000|(29<<21)|(dest<<16)|SCRATCH
            got=struct.unpack_from('<I',out,site+0x60)[0]
            assert got in (old,new),(hex(site),hex(got),hex(old))
            struct.pack_into('<I',out,site+0x60,new)
    return bytes(out)


def report():
    return dict(old_object_name_offset=hex(OLD_NAME),old_name_bytes_before_next_window=52,
                temporary_name_stack_offset=hex(SCRATCH),
                menus={k:dict(draw_start=hex(m['start']),draw_end=hex(m['end']),
                              scratch_bytes=m['capacity'],sites=[hex(s) for s in m['sites']])
                       for k,m in MENUS.items()},
                name_reader_writer_refs_only=True,stack_frame_and_class_layout_unchanged=True,
                bonus_selection_and_save_format_unchanged=True)
