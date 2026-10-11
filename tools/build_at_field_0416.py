"""Local 0.4.16 builds: one native atlas caption, both platforms."""
import json
import copy
import shutil
import sys
from pathlib import Path
import pycdlib
from PIL import Image, ImageDraw
from patch_at_field import ROOT, patch, caption, sha
from patch_wnd_headers import file_digest, digest

VERSION = '0.4.16'


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2)+'\n', encoding='utf8')


def build(platform, verify_existing=False):
    previous = '0.4.14' if platform == 'PSP' else '0.4.15'
    prefix = 'SRWMX_EN_' if platform == 'PSP' else 'SRWMX_PS2_EN_'
    source = ROOT/'work/output'/f'{prefix}{previous}.iso'
    output = ROOT/'work/output'/f'{prefix}{VERSION}.iso'
    assert output.exists() if verify_existing else not output.exists(), 'Preserve existing versioned images'
    path = '/PSP_GAME/USRDIR/STATIC2_ADD.BIN' if platform == 'PSP' else '/DATA/STATIC.BIN;1'
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    paths = [folder.rstrip('/')+'/'+str(name) for folder, _, names in iso.walk(iso_path='/') for name in names]
    before_hashes = {p: file_digest(iso, p) for p in paths}
    with iso.open_file_from_iso(iso_path=path) as f: original = f.read()
    changed, evidence = patch(original, platform)
    assert not evidence.get('already_translated')
    record = iso.get_record(iso_path=path); extent = record.extent_location()*2048
    assert record.data_length == len(changed)
    ui = ROOT/'work/ui'/platform.lower()/f'at_field_{VERSION}'; ui.mkdir(parents=True, exist_ok=True)
    for label, data in [('original', original), ('english', changed)]:
        pic, _ = caption(data, platform); pic.save(ui/f'{label}.png')
    sheet = Image.new('RGB', (696, 100), (30, 30, 30)); draw = ImageDraw.Draw(sheet)
    for x, label, data in [(0, 'Original', original), (360, 'English', changed)]:
        pic, _ = caption(data, platform); pic = pic.resize((336, 72), Image.Resampling.NEAREST)
        draw.text((x, 0), label, fill='white'); sheet.paste(pic, (x, 22), pic)
    sheet.save(ui/'before_after.png')
    iso.close()
    if not verify_existing:
        shutil.copyfile(source, output)
        with output.open('r+b') as f:
            for a, z in evidence['pixel_ranges']:
                f.seek(extent+a); f.write(changed[a:z])
    verify = pycdlib.PyCdlib(); verify.open(str(output)); checks = []
    for p in paths:
        actual = file_digest(verify, p); expected = sha(changed) if p == path else before_hashes[p]
        assert actual == expected, p
        checks.append(dict(path=p, sha256=actual, changed=p == path))
    udf_verified = False
    if platform == 'PS2':
        udf = '/data/'+next(n for _, _, names in verify.walk(udf_path='/data') for n in names if str(n).lower() == 'static.bin')
        # UDF's file-entry location is distinct from its allocation extent.
        # Read through the actual UDF allocation descriptors independently.
        with verify.open_file_from_iso(udf_path=udf) as f: assert sha(f.read()) == sha(changed)
        udf_verified = True
    verify.close()
    # Prove the entire disc differs only at the caption's declared pixel bytes.
    allowed = [(extent+a, extent+z) for a, z in evidence['pixel_ranges']]
    with source.open('rb') as a, output.open('rb') as b:
        last = 0
        for start, end in allowed+[(source.stat().st_size, source.stat().st_size)]:
            remaining = start-last
            while remaining:
                count = min(8*1024*1024, remaining); assert a.read(count) == b.read(count); remaining -= count
            a.seek(end); b.seek(end); last = end
    license = source.with_name(source.stem+'_FONT_LICENSE.txt')
    if license.exists(): shutil.copyfile(license, output.with_name(output.stem+'_FONT_LICENSE.txt'))
    with output.open('rb') as f: output_sha = digest(f)
    report = dict(version=VERSION, platform=platform, source_version=previous, output=str(output.relative_to(ROOT)),
        output_sha256=output_sha, bytes=output.stat().st_size, caption=evidence, files=checks,
        whole_disc_only_caption_pixels_changed=True, udf_verified=udf_verified, local_build_only=True,
        github_release=False, in_game_visual_validation='pending')
    base = ROOT/'work/build'/('psp_at_field_0.4.16' if platform == 'PSP' else 'ps2/at_field_0.4.16')
    base.mkdir(parents=True, exist_ok=True); (base/path.rsplit('/', 1)[-1].split(';')[0]).write_bytes(changed)
    save(base/'at_field.json', evidence); save(ui/'layout.json', evidence)
    save(ROOT/'work/output'/f'{platform.lower()}_at_field_{VERSION}_verification.json', report)
    save(ROOT/'work/translation/en'/platform.lower()/f'at_field_{VERSION}.en.json', report)
    if platform == 'PS2':
        prior = json.loads((ROOT/'work/output'/f'ps2_font_{previous}_verification.json').read_text())
        aggregate = copy.deepcopy(prior)
        expected = {r['path']:r['target_sha256'] for r in prior['files']}
        assert [r['path'] for r in checks if r['sha256'] != expected[r['path']]] == [path]
        for row in aggregate['files']:
            if row['path'] == path: row['target_sha256'] = evidence['target_resource_sha256']
        aggregate.update(version=VERSION, output=str(output.relative_to(ROOT)), bytes=output.stat().st_size,
            source_build_version=previous, source_build_sha256=prior['target_sha256'], target_sha256=output_sha,
            changed_from_previous=[path], at_field_correction=evidence,
            at_field_verification=str((ROOT/'work/output'/f'ps2_at_field_{VERSION}_verification.json').relative_to(ROOT)),
            inherited_execution_checks_from_version=previous,
            inherited_check_preservation_reason='Every executable, gameplay, script and other resource byte is identical; only the verified caption pixel spans change.',
            pcsx2_fresh_boot_verified=False, pcsx2_visual_validation='AT Field activation pending; earlier screen evidence belongs to its recorded older build',
            github_release=False)
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json', aggregate)
        fontbase = ROOT/'work/build/ps2'/f'font_{VERSION}'; fontbase.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'work/build/ps2/library_0.4.15/SLPS_253.45',fontbase/'SLPS_253.45')
        save(fontbase/'patch.json',aggregate['font'])
    print(json.dumps(dict(platform=platform, output=str(output), sha256=output_sha)), flush=True)
    return report


if __name__ == '__main__':
    terms = json.loads((ROOT/'work/glossary/akurasu_terms.json').read_text(encoding='utf8'))
    assert any(r['en'] == 'AT Field' and r['page'] == 'Mech Abilities' for r in terms)
    existing = '--verify-existing' in sys.argv
    psp = build('PSP', existing); ps2 = build('PS2', existing)
    # Both source captions have identical visible silhouettes.
    for p in [psp, ps2]: assert len(p['caption']['pixel_ranges']) == 24
