"""Reserve persistent storage for PSP s1050 when its normal allocation fails."""
import struct
import insert_text as it

ALLOC_SITE, FREE_SITE = 0xF06F8, 0xF06B8
ALLOC, FREE = 0xB899C, 0xB8B60
BIAS = 0x60
CAPACITY = 0x32800
SCRIPT_INDEX = 190


def jump(va, link=True):
    return ((3 if link else 2) << 26) | (va >> 2)


def stubs(buffer):
    import keystone
    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 | keystone.KS_MODE_LITTLE_ENDIAN)
    # The existing calls already relocate their return addresses. Constant
    # distances from those addresses reach the reserve at any module base.
    da = (buffer - (ALLOC_SITE + 8)) & 0xFFFFFFFF
    df = (buffer - (FREE_SITE + 8)) & 0xFFFFFFFF
    alloc = f'''.set noreorder
.option pic0
lui $t0, 0xd
addu $t0, $s0, $t0
lw $t1, -0x2c58($t0)
lui $t2, 0x3530
ori $t2, $t2, 0x3173
bne $t1, $t2, normal
nop
lhu $t1, -0x2c54($t0)
addiu $t2, $zero, 0x30
bne $t1, $t2, normal
nop
addiu $sp, $sp, -16
sw $ra, 12($sp)
sw $a1, 8($sp)
jal {ALLOC:#x}
nop
lw $ra, 12($sp)
lw $a1, 8($sp)
bnez $v0, done
addiu $sp, $sp, 16
beqz $a1, done
lui $t0, {CAPACITY>>16:#x}
ori $t0, $t0, {CAPACITY&0xffff:#x}
sltu $t0, $t0, $a1
bnez $t0, done
lui $t0, {da>>16:#x}
ori $t0, $t0, {da&0xffff:#x}
jr $ra
addu $v0, $ra, $t0
normal:
j {ALLOC:#x}
nop
done:
jr $ra
nop'''
    free = f'''.set noreorder
.option pic0
lui $t0, {df>>16:#x}
ori $t0, $t0, {df&0xffff:#x}
addu $t0, $ra, $t0
bne $a1, $t0, normal
nop
jr $ra
move $v0, $zero
normal:
j {FREE:#x}
nop'''
    return bytes(ks.asm(alloc)[0]), bytes(ks.asm(free)[0])


def reserved_address(base):
    return (base + sum(map(len, stubs(0))) + 63) & ~63


def patch_boot(boot):
    word = lambda va: struct.unpack_from('<I', boot, va+BIAS)[0]
    calls = word(ALLOC_SITE), word(FREE_SITE)
    if calls != (jump(ALLOC), jump(FREE)):
        base, free_at = ((w & 0x3FFFFFF) << 2 for w in calls)
        buffer = reserved_address(base)
        alloc, free = stubs(buffer)
        assert all(w >> 26 == 3 for w in calls) and free_at == base+len(alloc)
        assert boot[base+BIAS:free_at+BIAS+len(free)] == alloc+free, 'Unknown script allocation hook'
        assert boot[buffer+BIAS:buffer+BIAS+CAPACITY] == bytes(CAPACITY)
        return bytes(boot)
    h = it.elf(boot)['.rel.text']
    start, size = struct.unpack_from('<2I', boot, h+16)
    relocs = dict(struct.iter_unpack('<2I', boot[start:start+size]))
    assert all(relocs.get(va, 0) & 255 == 4 for va in (ALLOC_SITE, FREE_SITE))
    ph = struct.unpack_from('<I', boot, 28)[0]
    memsz = struct.unpack_from('<I', boot, ph+20)[0]
    base = (memsz+63) & ~63
    buffer = reserved_address(base)
    alloc, free = stubs(buffer)
    payload = (alloc+free).ljust(buffer-base,b'\0')+bytes(CAPACITY)
    out, actual = it.extend_segment(boot, payload, align=64)
    assert actual==base
    struct.pack_into('<I', out, ALLOC_SITE+BIAS, jump(base))
    struct.pack_into('<I', out, FREE_SITE+BIAS, jump(base+len(alloc)))
    added = [(base+i*4, 4) for i,(w,) in enumerate(struct.iter_unpack('<I',alloc+free)) if w>>26 in (2,3)]
    assert len(added)==3
    return bytes(it.append_relocs(out, added))
