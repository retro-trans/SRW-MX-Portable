"""Build the local PSP Dendoh window fix without relocating any ISO resource."""
import hashlib
import shutil
from pathlib import Path

import pycdlib
import title_footer
from build_title_footer import save
from fix_psp_dendoh_popup import SITE, patch_boot, report
from verify_psp_dendoh_popup import verify
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = '0.4.41'
VERSION = '0.4.42'


def build():
    source = ROOT/f'work/output/SRWMX_EN_{BASE}.iso'
    target = ROOT/f'work/output/SRWMX_EN_{VERSION}.iso'
    assert not target.exists(), 'Preserve existing versioned test images'
    baseline = json.loads((ROOT/f'work/output/psp_sortie_header_{BASE}_verification.json').read_text(encoding='utf8'))
    stat = (source.stat().st_size, source.stat().st_mtime_ns)
    assert stat[0] == baseline['bytes']
    title_footer.verify_iso(source, 'PSP', BASE)
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = sorted(folder.rstrip('/')+'/'+str(n) for folder, _, names in iso.walk(iso_path='/') for n in names)
    records = {p: (iso.get_record(iso_path=p).extent_location(), iso.get_record(iso_path=p).data_length) for p in paths}
    def asset(p):
        with iso.open_file_from_iso(iso_path=p) as f: return f.read()
    boot_paths = ('/PSP_GAME/SYSDIR/BOOT.BIN', '/PSP_GAME/SYSDIR/EBOOT.BIN')
    original = asset(boot_paths[0])
    assert original == asset(boot_paths[1])
    boot = patch_boot(original)
    execution = verify(original, boot)
    assert len(boot) == len(original)
    edits = {}
    for p in boot_paths:
        at = records[p][0]*2048+SITE+0x60
        edits[at] = (original[SITE+0x60:SITE+0x64], boot[SITE+0x60:SITE+0x64])
    footer_path = '/PSP_GAME/USRDIR/OPWND.BIN'
    old_footer = asset(footer_path)
    new_footer, footer = title_footer.patch(old_footer, 'PSP', VERSION)
    assert len(new_footer) == len(old_footer)
    for a, z in footer['pixel_ranges']:
        edits[records[footer_path][0]*2048+a] = (old_footer[a:z], new_footer[a:z])
    iso.close()
    edits = sorted((at, old, new) for at, (old, new) in edits.items())
    assert all(len(old) == len(new) for _, old, new in edits)
    assert all(a+len(b) <= c for (a,b,_),(c,_,_) in zip(edits, edits[1:]))
    prepared = ROOT/f'work/build/psp/dendoh_popup_{VERSION}'
    prepared.mkdir(parents=True, exist_ok=True)
    (prepared/'BOOT.BIN').write_bytes(boot)
    save(prepared/'native_execution.json', execution)
    source_hash = hashlib.sha256(); expected_hash = hashlib.sha256(); position = 0
    print('Writing PSP v0.4.42 with centered Dendoh popup and regenerated native footer', flush=True)
    with source.open('rb') as src, target.open('xb') as dst:
        while raw := src.read(8*1024*1024):
            source_hash.update(raw); changed = bytearray(raw); end = position+len(raw)
            for at, old, new in edits:
                left, right = max(position,at), min(end,at+len(old))
                if left < right:
                    assert raw[left-position:right-position] == old[left-at:right-at]
                    changed[left-position:right-position] = new[left-at:right-at]
            dst.write(changed); expected_hash.update(changed); position = end
    assert source_hash.hexdigest() == baseline['output_sha256']
    assert (source.stat().st_size,source.stat().st_mtime_ns) == stat
    assert target.stat().st_size == stat[0]
    print('Verifying complete output and native executable/footer readback', flush=True)
    with target.open('rb') as f: actual = hashlib.file_digest(f, 'sha256').hexdigest()
    assert actual == expected_hash.hexdigest()
    check = pycdlib.PyCdlib(); check.open(str(target))
    for p in paths:
        rec = check.get_record(iso_path=p)
        assert (rec.extent_location(),rec.data_length) == records[p]
    for p in boot_paths:
        with check.open_file_from_iso(iso_path=p) as f: assert f.read() == boot
    with check.open_file_from_iso(iso_path=footer_path) as f: assert f.read() == new_footer
    check.close()
    footer['readback'] = title_footer.verify_iso(target, 'PSP', VERSION)
    result = dict(version=VERSION, base_version=BASE, platform='PSP',
        output=target.relative_to(ROOT).as_posix(), bytes=target.stat().st_size,
        source_sha256=source_hash.hexdigest(), output_sha256=actual,
        popup=report(), native_execution=execution, footer=footer,
        complete_output_hash_verified=True, actual_iso_executable_readback_verified=True,
        iso_resource_layout_unchanged=True, all_other_disc_bytes_preserved=True,
        allowed_disc_ranges=[[at,at+len(old)] for at,old,_ in edits],
        fresh_in_game_visual_check='pending', github_release=False, local_build_only=True)
    save(ROOT/f'work/output/psp_dendoh_popup_{VERSION}_verification.json', result)
    save(ROOT/f'work/translation/en/psp/dendoh_popup_{VERSION}.en.json', result)
    save(ROOT/f'work/output/psp_title_footer_{VERSION}_verification.json', dict(version=VERSION,platform='PSP',footer=footer))
    save(ROOT/'work/ui/sortie_popup_2026_10_24/layout.json', dict(platform='PSP',
        screenshot='reported.png', screen=[480,272], popup_class='CWndDendohChoice',
        before=execution['before'], after=execution['after'], font_size_unchanged=True,
        coordinate_source='Native setup and draw execution; not a simulated screenshot',
        in_game_validation='pending'))
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    print('Verified PSP', VERSION, actual, flush=True)


if __name__ == '__main__': build()
