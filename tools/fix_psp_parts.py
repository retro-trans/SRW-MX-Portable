"""Use the Parts draw function's existing 256-byte scratch row for unit names.

The embedded panel ends at +0x810. Its old name field at +0x7dc is only
52 bytes long and sits immediately before its parent's child-menu pointer.
All six name writer/reader references are inside one draw invocation; the
scratch row at sp+0x50 is reused for numeric rows only after the name is drawn.
No class size, menu pointer, equipment logic, translation or stack size changes.
"""
import struct

SITES = (0x1e5a1c, 0x1e5a38, 0x1e5a54, 0x1e5a74, 0x1e5a90, 0x1e5ab8)
NAME_STACK_OFFSET = 0x50
NAME_CAPACITY = 0x100


def patch_boot(boot):
    data=bytearray(boot)
    for site in SITES:
        destination=4 if site==0x1e5a90 else 5
        old=0x24000000 | (17<<21) | (destination<<16) | 0x7dc
        new=0x24000000 | (29<<21) | (destination<<16) | NAME_STACK_OFFSET
        word=struct.unpack_from('<I',data,site+0x60)[0]
        assert word in (old,new), (hex(site),hex(word))
        struct.pack_into('<I',data,site+0x60,new)
    return bytes(data)


def report():
    return dict(sites=[hex(x) for x in SITES],old_object_offset='0x7dc',
                old_capacity=52,new_stack_offset=hex(NAME_STACK_OFFSET),
                new_capacity=NAME_CAPACITY,existing_stack_size='0x2e0',
                class_size_and_equipment_logic_unchanged=True,
                full_unit_names_preserved=True)
