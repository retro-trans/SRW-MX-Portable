"""Incrementally fix PSP narration and Level Up buffers in the 0.4.9 ISO."""
import hashlib
import io
import json
import shutil
import struct
from pathlib import Path
import pycdlib
import insert_text as it
import fix_psp_levelup
from patch_wnd_headers import digest, file_digest

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLES = {'/PSP_GAME/SYSDIR/BOOT.BIN', '/PSP_GAME/SYSDIR/EBOOT.BIN'}


def patch_narration(boot, original):
    _, bt = it.boot_translations()
    slots = it.narration_slots(bt)
    pool, pointers = bytearray(), {}
    for va, (text, raw) in slots.items():
        pointers[va] = len(pool)
        pool += it.encode(text, raw)
    data, base = it.extend_segment(bytearray(boot), pool)
    pointers = {va: base + off for va, off in pointers.items()}
    semantic = bytearray(original)
    it.patch_narration_script(semantic, bt)
    script_end = it.NARRATION_SCRIPT
    while struct.unpack_from('<I', original, script_end + 0x64)[0] == 7:
        script_end += 12
    sec = it.elf(original)
    off, size = struct.unpack_from('<II', original, sec['.rel.data'] + 16)
    changed = 0
    for va, info in struct.iter_unpack('<II', original[off:off + size]):
        if info & 255 != 2:
            continue
        target = struct.unpack_from('<I', semantic, va + 0x60)[0]
        # Blank/end pointers must remain native sentinels even when a record
        # previously contained a translated line. All record timings stay intact.
        if target in pointers or it.NARRATION_SCRIPT <= va < script_end:
            if target not in pointers and target not in (it.NARRATION_BLANK, it.NARRATION_END):
                continue
            struct.pack_into('<I', data, va + 0x60, pointers.get(target, target))
            changed += 1
    # Narration lines are referenced only by relocated data words in this build.
    report = dict(relocated_pointer_words=changed, line_counts={}, maximum_encoded_bytes={})
    for name, paras in bt['narration'].items():
        lines = [line for para in paras for line in it.wrap_narration(para)]
        report['line_counts'][name] = len(lines)
        report['maximum_encoded_bytes'][name] = max(len(it.encode(line)) for line in lines)
    return bytes(data), report


def main():
    source = ROOT / 'work/output/SRWMX_EN_0.4.9.iso'
    output = ROOT / 'work/output/SRWMX_EN_0.4.10.iso'
    assert not output.exists(), 'Preserve existing versioned builds'
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = [folder.rstrip('/') + '/' + str(name)
             for folder, _, files in iso.walk(iso_path='/') for name in files]
    before = {path: file_digest(iso, path) for path in paths}
    stream = io.BytesIO(); iso.get_file_from_iso_fp(stream, iso_path='/PSP_GAME/SYSDIR/BOOT.BIN')
    original = (ROOT / 'work/build/iso/BOOT.BIN').read_bytes()
    boot, narration = patch_narration(stream.getvalue(), original)
    boot = fix_psp_levelup.patch_boot(boot)
    for path in ('/PSP_GAME/SYSDIR/BOOT.BIN', '/PSP_GAME/SYSDIR/EBOOT.BIN'):
        iso.rm_file(iso_path=path); iso.add_fp(io.BytesIO(boot), len(boot), iso_path=path)
    iso.write(str(output)); iso.close()
    check = pycdlib.PyCdlib(); check.open(str(output))
    updated = hashlib.sha256(boot).hexdigest()
    for path in paths:
        assert file_digest(check, path) == (updated if path in EXECUTABLES else before[path]), path
    check.close()
    license = source.with_name(source.stem + '_FONT_LICENSE.txt')
    if license.exists():
        shutil.copyfile(license, output.with_name(output.stem + '_FONT_LICENSE.txt'))
    with output.open('rb') as stream:
        output_sha = digest(stream)
    with source.open('rb') as stream:
        source_sha = digest(stream)
    report = dict(version='0.4.10', base_iso=source.name, base_sha256=source_sha,
                  output_iso=output.name, output_sha256=output_sha, local_build_only=True,
                  changed_iso_files=['BOOT.BIN', 'EBOOT.BIN'], unchanged_iso_files=len(paths)-2,
                  unchanged_file_sha256={p: h for p, h in before.items() if p not in EXECUTABLES},
                  narration=narration, level_up_rows=dict(address=fix_psp_levelup.row_address(boot), rows=6, row_bytes=256),
                  iso_readback_verified=True)
    (ROOT / 'work/output/psp_fixes_0.4.10_verification.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    (ROOT / 'work/build/psp_ui_crash_0.4.10/BOOT.fixed.BIN').write_bytes(boot)
    print(output, output_sha, narration)


if __name__ == '__main__':
    main()
