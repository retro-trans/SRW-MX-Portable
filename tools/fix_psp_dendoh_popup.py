"""Widen only the PSP Dendoh form-choice window; native centering is retained."""
import struct

SITE = 0x1b19a0
OLD_WIDTH = 128
NEW_WIDTH = 176


def patch_boot(boot):
    data = bytearray(boot)
    old, new = 0x24020000 | OLD_WIDTH, 0x24020000 | NEW_WIDTH
    word = struct.unpack_from('<I', data, SITE+0x60)[0]
    assert word in (old,new), 'Unexpected Dendoh popup width instruction'
    struct.pack_into('<I', data, SITE+0x60, new)
    return bytes(data)


def report():
    return dict(instruction_va=hex(SITE),old_width=OLD_WIDTH,new_width=NEW_WIDTH,
        native_horizontal_centering_retained=True,font_size_unchanged=True,
        names_choices_and_input_logic_unchanged=True,object_and_save_layout_unchanged=True)
