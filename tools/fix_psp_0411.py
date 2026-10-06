"""Build local PSP 0.4.11 from 0.4.10, preserving unrelated assets."""
import hashlib
import io
import json
import shutil
import struct
from pathlib import Path
import pycdlib
import insert_text as it
import fix_psp_menu_alignment as alignment
from static2_extract import sections
from verify_text_build import overflow_table
from patch_wnd_headers import digest, file_digest

ROOT = Path(__file__).resolve().parents[1]
CHANGED = {'/PSP_GAME/SYSDIR/BOOT.BIN', '/PSP_GAME/SYSDIR/EBOOT.BIN',
           '/PSP_GAME/USRDIR/STATIC2_ADD.BIN'}


def patch_music(boot, static, titles):
    data, static = bytearray(boot), bytearray(static)
    old = overflow_table(data)
    first = struct.unpack_from('<I', data, old + 0x60)[0]
    count = (first - old) // 4
    assert 0 < count < 65536 and first == old + count * 4
    old_ptrs = list(struct.unpack_from(f'<{count}I', data, old + 0x60))
    blob = bytearray((count + len(titles)) * 4)
    positions = []
    for text in titles.values():
        positions.append(len(blob))
        blob += it.encode(text)
    data, new = it.extend_segment(data, blob)
    ptrs = old_ptrs + [new + off for off in positions]
    struct.pack_into(f'<{len(ptrs)}I', data, new + 0x60, *ptrs)
    # Retarget the shared getter stubs' existing paired address relocations.
    sec = it.elf(data)
    off, size = struct.unpack_from('<II', data, sec['.rel.text'] + 16)
    hi, pairs = None, []
    word = lambda va: struct.unpack_from('<I', data, va + 0x60)[0]
    for va, info in struct.iter_unpack('<II', data[off:off + size]):
        if info & 255 == 5:
            hi = va
        elif info & 255 == 6 and hi is not None:
            lo = struct.unpack('<h', struct.pack('<H', word(va) & 65535))[0]
            if ((word(hi) & 65535) << 16) + lo == old:
                pairs.append((hi, va))
    assert len(pairs) == 3, pairs
    h, l = it._hi_lo(new)
    for hv, lv in pairs:
        struct.pack_into('<I', data, hv + 0x60, (word(hv) & 0xFFFF0000) | h)
        struct.pack_into('<I', data, lv + 0x60, (word(lv) & 0xFFFF0000) | (l & 65535))
    data = it.append_relocs(data, [(new + i * 4, 2) for i in range(len(ptrs))])
    start, _, names = sections(static)['Strg']
    for n, idx in enumerate(titles):
        assert int(idx) < names
        struct.pack_into('<I', static, start + 12 + int(idx) * 4, it.OVERFLOW_FLAG + count + n)
    assert overflow_table(data) == new
    return bytes(data), bytes(static), dict(translated_titles=len(titles),
                                           previous_overflow_entries=count, overflow_table=new)


def main():
    source = ROOT / 'work/output/SRWMX_EN_0.4.10.iso'
    output = ROOT / 'work/output/SRWMX_EN_0.4.11.iso'
    assert not output.exists(), 'Preserve existing versioned builds'
    titles = json.loads((ROOT / 'work/translation/en/static2/music.en.json').read_text())['titles']
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = [folder.rstrip('/') + '/' + str(name)
             for folder, _, files in iso.walk(iso_path='/') for name in files]
    before = {p: file_digest(iso, p) for p in paths}
    def read(p):
        stream = io.BytesIO(); iso.get_file_from_iso_fp(stream, iso_path=p)
        return stream.getvalue()
    boot, static, music = patch_music(read('/PSP_GAME/SYSDIR/BOOT.BIN'),
                                     read('/PSP_GAME/USRDIR/STATIC2_ADD.BIN'), titles)
    boot = alignment.patch_boot(boot)
    repl = {p: static if p.endswith('STATIC2_ADD.BIN') else boot for p in CHANGED}
    for p, b in repl.items():
        iso.rm_file(iso_path=p); iso.add_fp(io.BytesIO(b), len(b), iso_path=p)
    iso.write(str(output)); iso.close()
    check = pycdlib.PyCdlib(); check.open(str(output))
    for p in paths:
        assert file_digest(check, p) == (hashlib.sha256(repl[p]).hexdigest() if p in repl else before[p]), p
    check.close()
    names_path = ROOT / 'work/translation/en/static2/names.json'
    names = json.loads(names_path.read_text(encoding='utf-8')); names.update(titles)
    names_path.write_text(json.dumps(names, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    license = source.with_name(source.stem + '_FONT_LICENSE.txt')
    if license.exists():
        shutil.copyfile(license, output.with_name(output.stem + '_FONT_LICENSE.txt'))
    with output.open('rb') as f: sha = digest(f)
    with source.open('rb') as f: base_sha = digest(f)
    report = dict(version='0.4.11', base_iso=source.name, base_sha256=base_sha,
                  output_iso=output.name, output_sha256=sha, local_build_only=True,
                  changed_iso_files=sorted(CHANGED), unchanged_iso_files=len(paths)-3,
                  unchanged_file_sha256={p:h for p,h in before.items() if p not in CHANGED},
                  music=music, alignment_sites={name:hex(site) for name,(site,_) in alignment.SITES.items()},
                  iso_readback_verified=True)
    (ROOT / 'work/output/psp_fixes_0.4.11_verification.json').write_text(json.dumps(report, indent=1))
    (ROOT / 'work/build/psp_ui_0.4.11/BOOT.fixed.BIN').write_bytes(boot)
    (ROOT / 'work/build/psp_ui_0.4.11/STATIC2.fixed.BIN').write_bytes(static)
    print(output, sha, music)


if __name__ == '__main__':
    main()
