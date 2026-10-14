"""Create local banner-only candidates, preserving every other disc byte.

Both native title footers are regenerated before the final output is hashed.
No release is published. Complete ISO readback checks the streaming transform.
"""
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path
import pycdlib
import title_footer
from patch_at_field import ROOT, sha
from patch_battle_banners import patch, verify_iso as verify_banners
from build_title_footer import save


def build(platform, base, version):
    assert title_footer.version_key(version) > title_footer.version_key(base)
    prefix = 'SRWMX_EN_' if platform == 'PSP' else 'SRWMX_PS2_EN_'
    source = ROOT/f'work/output/{prefix}{base}.iso'
    target = ROOT/f'work/output/{prefix}{version}.iso'
    assert source.exists() and not target.exists(), 'Preserve existing builds'
    source_stat = (source.stat().st_size, source.stat().st_mtime_ns)
    manifest_path = ROOT/f'work/output/release-v{base}/BUILD-MANIFEST.json'
    if not manifest_path.exists():
        manifest_path = ROOT/f'work/build/battle_banners_baseline_{base}/BUILD-MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert manifest['version'] == base
    baseline = next(p for p in manifest['patches'] if p['platform'] == platform)
    assert source_stat[0] == baseline['target_bytes']
    path = '/PSP_GAME/USRDIR/STATIC2_ADD.BIN' if platform == 'PSP' else '/DATA/STATIC.BIN;1'
    footer_path = '/PSP_GAME/USRDIR/OPWND.BIN' if platform == 'PSP' else '/SLPS_253.45;1'
    iso = pycdlib.PyCdlib()
    iso.open(str(source))
    paths = sorted(folder.rstrip('/')+'/'+str(n) for folder, _, names in iso.walk(iso_path='/') for n in names)
    layouts = {p: (iso.get_record(iso_path=p).extent_location(), iso.get_record(iso_path=p).data_length) for p in paths}
    with iso.open_file_from_iso(iso_path=path) as f:
        original = f.read()
    ui = ROOT/f'work/ui/{platform.lower()}/battle_banners_{version}'
    changed, evidence = patch(original, platform, ui)
    assert patch(changed, platform)[0] == changed
    assert all(not r['already_translated'] for r in evidence['regions'])
    with iso.open_file_from_iso(iso_path=footer_path) as f:
        original_footer = f.read()
    # Output reports can be cleaned independently of immutable ISOs. Restore
    # registration only after exact native baseline-footer readback succeeds.
    baseline_footer = title_footer.verify_iso(source, platform, base)
    footer_registration = ROOT/f'work/output/{platform.lower()}_title_footer_{base}_verification.json'
    if platform == 'PSP' and not footer_registration.exists():
        save(footer_registration, dict(version=base, platform=platform,
             restored_from_verified_iso=True, footer=dict(readback=baseline_footer,
             target_region_sha256=sha(title_footer.region(original_footer, platform, base)))))
    new_footer, footer = title_footer.patch(original_footer, platform, version)
    assert len(new_footer) == len(original_footer)
    assert title_footer.patch(new_footer, platform, version)[0] == new_footer
    footer['disc_extent'] = layouts[footer_path][0]*2048
    resources = {path: (original, changed, evidence['pixel_ranges']),
                 footer_path: (original_footer, new_footer, footer['pixel_ranges'])}
    edits = []
    for asset, (old, new, spans) in resources.items():
        extent = layouts[asset][0]*2048
        for start, end in spans:
            edits.append((extent+start, old[start:end], new[start:end]))
    edits.sort()
    assert all(a[0]+len(a[1]) <= b[0] for a, b in zip(edits, edits[1:]))
    iso.close()
    source_hash, expected_hash = hashlib.sha256(), hashlib.sha256()
    position = 0
    print(platform, 'copying verified baseline with two caption rectangles and new footer', flush=True)
    with source.open('rb') as src, target.open('xb') as dst:
        while raw := src.read(8*1024*1024):
            source_hash.update(raw)
            result = bytearray(raw)
            end = position+len(raw)
            for start, old, new in edits:
                left, right = max(position, start), min(end, start+len(old))
                if left < right:
                    a, z = left-position, right-position
                    c, d = left-start, right-start
                    assert raw[a:z] == old[c:d]
                    result[a:z] = new[c:d]
            dst.write(result)
            expected_hash.update(result)
            position = end
    assert source_hash.hexdigest() == baseline['target_sha256'], 'Published baseline mismatch'
    assert target.stat().st_size == source_stat[0]
    print(platform, 'verifying complete output hash and native asset readback', flush=True)
    with target.open('rb') as stream:
        actual_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual_hash == expected_hash.hexdigest()
    assert (source.stat().st_size, source.stat().st_mtime_ns) == source_stat
    check = pycdlib.PyCdlib()
    check.open(str(target))
    files = []
    for p in paths:
        record = check.get_record(iso_path=p)
        assert (record.extent_location(), record.data_length) == layouts[p]
        files.append(dict(path=p, layout_preserved=True, changed=p in resources))
    udf = {}
    for p, (_, new, _) in resources.items():
        with check.open_file_from_iso(iso_path=p) as stream:
            assert stream.read() == new
        if platform == 'PS2':
            name = p.rsplit('/', 1)[-1].split(';')[0].lower()
            matches = [folder.rstrip('/')+'/'+str(n) for folder, _, names in check.walk(udf_path='/')
                       for n in names if str(n).lower() == name]
            assert len(matches) == 1
            with check.open_file_from_iso(udf_path=matches[0]) as stream:
                assert stream.read() == new
            udf[p] = True
    with check.open_file_from_iso(iso_path=path) as stream:
        actual = stream.read()
    # Generate previews from actual ISO data, rather than only prepared artwork.
    assert patch(actual, platform, ui/'iso_readback')[0] == actual
    check.close()
    footer['readback'] = title_footer.verify_iso(target, platform, version)
    banner_readback = verify_banners(target, platform)
    save(ROOT/f'work/output/{platform.lower()}_title_footer_{version}_verification.json',
         dict(version=version, platform=platform, footer=footer))
    license = source.with_name(source.stem+'_FONT_LICENSE.txt')
    if not license.exists():
        license = ROOT/'incoming/fonts/FONT_LICENSE.txt'
    shutil.copyfile(license, target.with_name(target.stem+'_FONT_LICENSE.txt'))
    prepared = ROOT/f'work/build/{platform.lower()}/battle_banners_{version}'
    prepared.mkdir(parents=True, exist_ok=True)
    (prepared/path.rsplit('/', 1)[-1].split(';')[0]).write_bytes(changed)
    (prepared/footer_path.rsplit('/', 1)[-1].split(';')[0]).write_bytes(new_footer)
    save(prepared/'battle_banners.json', evidence)
    report = dict(version=version, base_version=base, platform=platform,
                  source_sha256=source_hash.hexdigest(), output=target.relative_to(ROOT).as_posix(),
                  output_sha256=actual_hash, bytes=position, banner_artwork=evidence,
                  footer=footer, caption_readback=banner_readback, files=files, udf_readback=udf,
                  complete_output_hash_verified=True, all_other_disc_bytes_preserved=True,
                  idempotence_verified=True, iso_caption_readback_verified=True,
                  visual_validation='Actual ISO artwork previews pass; fresh in-game display pending',
                  local_build_only=True, github_release=False)
    save(ROOT/f'work/output/{platform.lower()}_battle_banners_{version}_verification.json', report)
    save(ROOT/f'work/translation/en/{platform.lower()}/battle_banners_{version}.en.json', report)
    if platform == 'PS2':
        font = ROOT/f'work/build/ps2/font_{version}'
        font.mkdir(parents=True, exist_ok=True)
        (font/'SLPS_253.45').write_bytes(new_footer)
        meta = json.loads((ROOT/f'work/build/ps2/font_{base}/patch.json').read_text(encoding='utf-8'))
        meta['target_sha256'] = sha(new_footer)
        save(font/'patch.json', meta)
    previous_report = ROOT/f'work/output/ps2_font_{base}_verification.json'
    if platform == 'PS2' and previous_report.exists():
        previous = json.loads(previous_report.read_text(encoding='utf-8'))
        aggregate = copy.deepcopy(previous)
        for row in aggregate['files']:
            if row['path'] in resources:
                row['target_sha256'] = sha(resources[row['path']][1])
        aggregate['font']['target_sha256'] = sha(new_footer)
        aggregate.update(version=version, output=report['output'], target_sha256=actual_hash,
                         bytes=position, source_build_version=base,
                         source_build_sha256=baseline['target_sha256'], title_footer=footer,
                         battle_banners=evidence, current_correction_report=f'work/output/ps2_battle_banners_{version}_verification.json',
                         changed_from_previous=sorted(resources), inherited_execution_checks_from_version=base,
                         inherited_execution_checks_reason='Only two HUD caption rectangles and native title footer version bytes change; all remaining disc bytes read back exactly.',
                         pcsx2_fresh_boot_verified=False, pcsx2_visual_validation='Two battle banners pending', github_release=False)
        save(ROOT/f'work/output/ps2_font_{version}_verification.json', aggregate)
        save(font/'patch.json', aggregate['font'])
    print(platform, version, 'verified', actual_hash, flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='0.4.33')
    parser.add_argument('--version', default='0.4.34')
    parser.add_argument('--platform', choices=['PSP', 'PS2'])
    args = parser.parse_args()
    for platform in ([args.platform] if args.platform else ['PSP', 'PS2']):
        build(platform, args.base, args.version)
