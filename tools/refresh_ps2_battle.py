"""Refresh changed PS2 English battle captions inside their existing native blocks."""
import json
from pathlib import Path
import struct

import battle_quotes as bq
from verify_battle_release import normalized, elf_offset

ROOT = Path(__file__).resolve().parents[1]


def refresh(path, static, elf):
    meta = json.loads((ROOT/'work/source/battle/unique.json').read_text(encoding='utf8'))
    english = bq.require_complete_translations(meta)
    by_raw = {v['raw']: k for k, v in meta.items()}
    orig = (ROOT/'work/source/ps2/battle_quotes.bin').read_bytes()
    old_static = (ROOT/'work/source/ps2/STATIC.BIN').read_bytes()
    old_table = struct.unpack_from('<512I', old_static, 0x1b8174)
    table = struct.unpack_from('<512I', static, 0x1b8174)
    offsets = sorted(set(off for off in table if off != 0xffffffff))
    seen = set(); changed = []; allocations = 0
    j = struct.unpack_from('<I', elf, elf_offset(elf, 0x2b53fc))[0]
    stub = (j & 0x3ffffff) << 2
    hi = struct.unpack_from('<I', elf, elf_offset(elf, stub+16))[0] & 65535
    lo = struct.unpack_from('<h', elf, elf_offset(elf, stub+24))[0]
    overflow_table = (hi << 16) + lo
    with Path(path).open('r+b') as stream:
        stream.seek(20); base = struct.unpack('<I', stream.read(4))[0]
        stream.seek(base); quotes = bytearray(stream.read())
        before = bytes(quotes)
        for pid, old in enumerate(old_table):
            if old == 0xffffffff:
                continue
            off = table[pid]
            if off in seen:
                continue
            seen.add(off)
            source_secs = struct.unpack_from('<10H', orig, old+8)
            secs = struct.unpack_from('<10H', quotes, off+8)
            n = (secs[8]-secs[7]) // 2
            assert n == (source_secs[8]-source_secs[7]) // 2
            original_offsets = struct.unpack_from('<%dH' % n, orig, old+source_secs[7])
            current_offsets = struct.unpack_from('<%dH' % n, quotes, off+secs[7])
            replacements = {}; values = {}
            for entry, (old_rel, rel) in enumerate(zip(original_offsets, current_offsets)):
                at = old+source_secs[-1]+old_rel
                ident = by_raw[orig[at:orig.index(0, at)].decode('cp932')]
                wanted, fits = bq.encode_quote(english[ident], meta[ident]); assert fits, ident
                wanted = wanted.replace(b'/', b'@')
                if rel & 0x8000:
                    ptr = struct.unpack_from('<I', elf, elf_offset(elf, overflow_table+4*(rel & 0x7fff)))[0]
                    at = elf_offset(elf, ptr); actual = elf[at:elf.index(0, at)]
                else:
                    at = off+secs[-1]+rel; actual = bytes(quotes[at:quotes.index(0, at)])
                    values[rel] = actual
                if normalized(actual) != normalized(wanted):
                    assert not rel & 0x8000, 'Changed overflow quote requires an explicit pool refresh: ' + ident
                    assert rel not in replacements or replacements[rel] == wanted
                    replacements[rel] = wanted
                    changed.append(dict(pilot=pid, entry=entry, id=ident))
            if not replacements:
                continue
            allocations += len(replacements)
            blob = bytearray(); new_offsets = {}; dedup = {}
            for rel, value in values.items():
                value = replacements.get(rel, value)
                if value not in dedup:
                    dedup[value] = len(blob); blob += value + b'\0'
                new_offsets[rel] = dedup[value]
            head = bytearray(quotes[off:off+secs[-1]])
            struct.pack_into('<%dH' % n, head, secs[7],
                *(rel if rel & 0x8000 else new_offsets[rel] for rel in current_offsets))
            updated = head + blob + b'\0'
            index = offsets.index(off)
            next_off = offsets[index+1] if index+1 < len(offsets) else len(quotes)
            capacity = min(next_off-off, bq.BLOCK_MAX)
            assert len(updated) <= capacity, (pid, len(updated), capacity)
            quotes[off:off+capacity] = updated + bytes(capacity-len(updated))
            assert quotes[off:off+secs[7]] == before[off:off+secs[7]]
            assert quotes[off+secs[8]:off+secs[-1]] == before[off+secs[8]:off+secs[-1]]
        assert len(quotes) == len(before)
        stream.seek(base); stream.write(quotes)
    return dict(changed_references=changed, native_references_updated=len(changed),
        stored_allocations_updated=allocations, overflow_allocations_updated=0,
        archive_length_preserved=True, native_records_flags_and_ids_preserved=True,
        pilot_table_preserved=True, untouched_animation_subfiles_preserved=True)
