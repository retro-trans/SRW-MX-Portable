"""Build the PSP screenshot corrections on top of the released 0.4.12 ISO."""
import hashlib
import io
import json
import shutil
import struct
from pathlib import Path

import pycdlib
import build_patch as build
import insert_text as it
import patch_chapter_cards as cards
from patch_wnd_headers import digest, file_digest
from psp_spirit_footer import FOOTER_PATCHES

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.13'
BASE = ROOT / 'work/build/psp_ui_0.4.13'
OLD_OBJECTIVE = '1. Shoot down Zeorymer of the Heavens'
NEW_OBJECTIVE = '1. Zeorymer of the Heavens is shot down.'


def patch_boot(boot):
    data = bytearray(boot)
    for va, old, new in FOOTER_PATCHES:
        assert struct.unpack_from('<I', data, va + 0x60)[0] == old, hex(va)
        struct.pack_into('<I', data, va + 0x60, new)
    return bytes(data)


def patch_objectives(boot, data):
    offsets = struct.unpack_from('<204I', boot, build.BLOCK_TABLE)
    names = {r['block']: r['name'] for r in json.loads(
        (ROOT / 'work/source/stage_map.json').read_text(encoding='utf8'))}
    changes, output = [], bytearray(data)
    old_text, new_text = it.encode(OLD_OBJECTIVE)[:-1], it.encode(NEW_OBJECTIVE)[:-1]
    for block in range(203):
        start = (build.SCRIPT_SECTOR + offsets[block]) * 2048
        end = (build.SCRIPT_SECTOR + offsets[block+1]) * 2048
        raw = data[start:end]
        ncmd, n, tab = struct.unpack_from('<3I', raw, 4)
        pointers = struct.unpack_from(f'<{n}I', raw, tab)
        slots = {c[2] for c in struct.iter_unpack('<12i', raw[32:32+48*ncmd])
                 if c[0] == 0x58 and c[1] == 1}
        trans = {}
        for slot in slots:
            p = pointers[slot]
            if raw[p:raw.index(b'\0', p)] == old_text:
                trans[old_text.decode('cp932')] = NEW_OBJECTIVE
                changes.append(dict(block=block, scene=names[block], slot=slot,
                                    old=OLD_OBJECTIVE, en=NEW_OBJECTIVE))
        if trans:
            updated, count = build.rebuild_block(raw, trans)
            assert count == 1 and len(updated) <= len(raw), names[block]
            updated += bytes(len(raw) - len(updated))
            assert updated[:32+48*ncmd] == raw[:32+48*ncmd]
            new_ptrs = struct.unpack_from(f'<{n}I', updated, tab)
            for slot, (a, b) in enumerate(zip(pointers, new_ptrs)):
                old = raw[a:raw.index(b'\0', a)]
                new = updated[b:updated.index(b'\0', b)]
                assert new == (new_text if slot in slots and old == old_text else old)
            output[start:end] = updated
    assert {(r['scene'], r['slot']) for r in changes} == {('s0150', 207), ('s0430', 207)}
    return bytes(output), changes


def patch_cards(data):
    specs = json.loads((ROOT / 'work/translation/en/ui/all_chapter_cards.json').read_text(encoding='utf8'))
    selected = [dict(r, needs_translation=True) for r in specs['cards'] if r['en'] == 'do justice to']
    assert len(selected) == 3
    return cards.patch_archive(data, {'cards': selected}, ROOT / 'work/ui/psp/0.4.13/title_atlases')


def main():
    source = ROOT / 'work/output/SRWMX_EN_0.4.12.iso'
    output = ROOT / f'work/output/SRWMX_EN_{VERSION}.iso'
    assert not output.exists(), 'Preserve existing versioned builds'
    BASE.mkdir(parents=True, exist_ok=True)
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = [folder.rstrip('/') + '/' + str(name)
             for folder, _, files in iso.walk(iso_path='/') for name in files]
    before = {p: file_digest(iso, p) for p in paths}
    boot = patch_boot(build.iso_read(iso, '/PSP_GAME/SYSDIR/BOOT.BIN'))
    map_data, objectives = patch_objectives(boot, build.iso_read(iso, '/PSP_GAME/USRDIR/MAP_ADD.BIN'))
    archive, titles = patch_cards(build.iso_read(iso, '/PSP_GAME/USRDIR/PACKMAPC2_ADD.BIN'))
    repl = {'/PSP_GAME/SYSDIR/BOOT.BIN': boot, '/PSP_GAME/SYSDIR/EBOOT.BIN': boot,
            '/PSP_GAME/USRDIR/MAP_ADD.BIN': map_data, '/PSP_GAME/USRDIR/PACKMAPC2_ADD.BIN': archive}
    for p, data in repl.items():
        (BASE / p.rsplit('/', 1)[-1]).write_bytes(data)
        iso.rm_file(iso_path=p); iso.add_fp(io.BytesIO(data), len(data), iso_path=p)
    iso.write(str(output)); iso.close()
    check = pycdlib.PyCdlib(); check.open(str(output))
    for p in paths:
        assert file_digest(check, p) == (hashlib.sha256(repl[p]).hexdigest() if p in repl else before[p]), p
    check.close()
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),
                    output.with_name(output.stem+'_FONT_LICENSE.txt'))
    with output.open('rb') as f: sha = digest(f)
    report = dict(version=VERSION, base_version='0.4.12', local_build_only=True,
                  output_iso=output.name, output_sha256=sha, changed_iso_files=sorted(repl),
                  unchanged_iso_files=len(paths)-len(repl), iso_readback_verified=True,
                  objectives=objectives, titles=titles,
                  footer_patches=[dict(va=hex(va), old=hex(old), new=hex(new))
                                  for va, old, new in FOOTER_PATCHES])
    (ROOT / f'work/output/psp_ui_{VERSION}_verification.json').write_text(json.dumps(report, indent=1))
    print(output, sha)


if __name__ == '__main__':
    main()
