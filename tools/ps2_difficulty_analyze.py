"""Bounded ELF disassembly and address references for the native difficulty port."""
import argparse
import struct
from pathlib import Path
import capstone

ROOT = Path(__file__).resolve().parent.parent
BIAS = 0xff000

def references(data, target):
    for off in range(0x1000, 0x2bef18, 4):
        word = struct.unpack_from('<I', data, off)[0]
        if word >> 26 in (2, 3) and (word & 0x3ffffff) * 4 == target:
            print(f'call {off+BIAS:08x}')
        if word >> 26 != 15:
            continue
        register = word >> 16 & 31
        for pos in range(off+4, min(off+80, 0x2bef18), 4):
            low = struct.unpack_from('<I', data, pos)[0]
            if low >> 26 in (9, 13) and low >> 21 & 31 == register:
                imm = low & 65535
                if low >> 26 == 9 and imm >= 32768:
                    imm -= 65536
                if ((word & 65535) << 16) + imm == target:
                    print(f'address {off+BIAS:08x} {pos+BIAS:08x}')
    needle = struct.pack('<I', target)
    for off in range(0x2c5e00, len(data)-3, 4):
        if data[off:off+4] == needle:
            print(f'pointer {off+BIAS:08x}')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('address', type=lambda s:int(s, 16))
    p.add_argument('--end', type=lambda s:int(s, 16))
    p.add_argument('--refs', action='store_true')
    p.add_argument('--elf', type=Path, default=ROOT/'work/source/ps2/SLPS_253.45')
    args = p.parse_args()
    data = args.elf.read_bytes()
    if args.refs:
        references(data, args.address)
    else:
        c = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 | capstone.CS_MODE_LITTLE_ENDIAN)
        end = args.end or args.address+256
        # Decode one instruction at a time: EE-specific instructions cannot stop the listing.
        for addr in range(args.address, end, 4):
            raw=data[addr-BIAS:addr-BIAS+4]
            ins=list(c.disasm(raw,addr))
            print(f'{addr:08x} '+(f'{ins[0].mnemonic} {ins[0].op_str}' if ins else f'.word {int.from_bytes(raw,"little"):08x}'))

if __name__ == '__main__':
    main()
