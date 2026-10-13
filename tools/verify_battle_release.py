"""Read every native battle quote reference in a PSP or PS2 ISO against English sources."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import unicodedata

import pycdlib
import battle_quotes as bq
import textfit

ROOT = Path(__file__).resolve().parents[1]


def elf_offset(data, address):
    start = struct.unpack_from('<I', data, 28)[0]
    size, count = struct.unpack_from('<2H', data, 42)
    for i in range(count):
        typ, offset, va, _, filesz = struct.unpack_from('<5I', data, start + size*i)
        if typ == 1 and va <= address < va + filesz:
            return offset + address - va
    raise ValueError('Unmapped ELF address: ' + hex(address))


def normalized(raw):
    return ' '.join(unicodedata.normalize('NFKC', raw.decode('cp932')).replace('/', ' ').replace('@', ' ').split())


def verify(path, platform, strict=True):
    meta = json.loads((ROOT/'work/source/battle/unique.json').read_text(encoding='utf8'))
    english = bq.require_complete_translations(meta)
    by_raw = {v['raw']: k for k, v in meta.items()}
    ps2 = platform == 'PS2'
    table_at = 0x1b8174 if ps2 else bq.PILOT_TABLE
    orig = (ROOT/'work/source/ps2/battle_quotes.bin').read_bytes() if ps2 else bq.subfile()
    old_static = (ROOT/'work/source/ps2/STATIC.BIN').read_bytes() if ps2 else bq.static2()
    old_table = struct.unpack_from('<512I', old_static, table_at)
    static_path = '/DATA/STATIC.BIN;1' if ps2 else '/PSP_GAME/USRDIR/STATIC2_ADD.BIN'
    battle_path = '/DATA/BATTLE.BIN;1' if ps2 else '/PSP_GAME/USRDIR/BATTLE2.BIN'
    elf_path = '/SLPS_253.45;1' if ps2 else '/PSP_GAME/SYSDIR/BOOT.BIN'
    iso = pycdlib.PyCdlib(); iso.open(str(path))
    def get(name):
        with iso.open_file_from_iso(iso_path=name) as stream:
            return stream.read()
    static, elf = get(static_path), get(elf_path)
    table = struct.unpack_from('<512I', static, table_at)
    site = 0x2b53fc if ps2 else bq.QUOTE_SITES[0][0]
    j = struct.unpack_from('<I', elf, elf_offset(elf, site))[0]
    stub = (j & 0x3ffffff) << 2
    hi_at, lo_at = (16, 24) if ps2 else (32, 40)
    hi = struct.unpack_from('<I', elf, elf_offset(elf, stub+hi_at))[0] & 65535
    lo = struct.unpack_from('<h', elf, elf_offset(elf, stub+lo_at))[0]
    overflow_table = (hi << 16) + lo
    checked = overflow_reads = japanese = format_differences = 0
    mismatches = []; unique = set()
    with iso.open_file_from_iso(iso_path=battle_path) as stream:
        stream.seek(20); base = struct.unpack('<I', stream.read(4))[0]
        for pid, old in enumerate(old_table):
            if old == 0xffffffff:
                continue
            assert table[pid] != 0xffffffff, (platform, pid, 'missing battle block')
            old_secs = struct.unpack_from('<10H', orig, old+8)
            n = (old_secs[8] - old_secs[7]) // 2
            offsets = struct.unpack_from('<%dH' % n, orig, old+old_secs[7])
            stream.seek(base+table[pid]); block = stream.read(bq.BLOCK_MAX)
            secs = struct.unpack_from('<10H', block, 8)
            assert (secs[8]-secs[7])//2 == n
            new_offsets = struct.unpack_from('<%dH' % n, block, secs[7])
            # Only the offset table and strings may change; situation records,
            # flags and text IDs must retain their original byte representation.
            assert block[:secs[7]] == orig[old:old+old_secs[7]]
            assert block[secs[8]:secs[-1]] == orig[old+old_secs[8]:old+old_secs[-1]]
            for i, (old_off, new_off) in enumerate(zip(offsets, new_offsets)):
                at = old+old_secs[-1]+old_off
                raw = orig[at:orig.index(0, at)]
                ident = by_raw[raw.decode('cp932')]
                unique.add(ident)
                wanted, fits = bq.encode_quote(english[ident], meta[ident]); assert fits, ident
                if ps2:
                    wanted = wanted.replace(b'/', b'@')
                if new_off & bq.OVERFLOW_BIT:
                    ptr_at = elf_offset(elf, overflow_table+4*(new_off & 0x7fff))
                    ptr = struct.unpack_from('<I', elf, ptr_at)[0]
                    at = elf_offset(elf, ptr)
                    actual = elf[at:elf.index(0, at)]
                    overflow_reads += 1
                else:
                    at = secs[-1]+new_off
                    actual = block[at:block.index(0, at)]
                checked += 1
                if actual != wanted:
                    if normalized(actual) == normalized(wanted):
                        format_differences += 1
                    else:
                        is_japanese = actual == raw or actual == raw.replace(b'/', b'@')
                        japanese += int(is_japanese)
                        mismatches.append(dict(pilot=pid, entry=i, id=ident,
                            japanese_fallback=is_japanese, actual_hex=actual.hex(), expected_hex=wanted.hex()))
    iso.close()
    report = dict(platform=platform, iso=str(path), native_references_checked=checked,
        distinct_source_quotes_checked=len(unique), english_source_quotes=len(english),
        overflow_reads=overflow_reads, original_records_flags_and_text_ids_preserved=True,
        layout_only_differences=format_differences, japanese_fallbacks=japanese,
        content_mismatches=len(mismatches), mismatches=mismatches,
        passed=not mismatches)
    print(platform, 'battle references:', checked, 'Japanese:', japanese, 'content mismatches:', len(mismatches), flush=True)
    if strict:
        assert not mismatches, (platform, 'native battle translation differs', len(mismatches))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path); parser.add_argument('platform', choices=['PSP','PS2'])
    parser.add_argument('--audit', action='store_true'); parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = verify(args.iso, args.platform, strict=False)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    if not args.audit:
        assert report['passed'], 'Native battle translation readback failed'
