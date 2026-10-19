"""Audit current ISO candidates without claiming fresh emulator/playthrough tests."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import pycdlib
import title_footer
import verify_battle_release
import patch_battle_banners
import verify_parts_layout
import verify_psp_rename
from build_reviewed_ps2 import refresh_story
from verify_ps2_stage30 import native_checks
from verify_ps2_font import verify as verify_font
from verify_ps2_difficulty import verify as verify_difficulty
from verify_ps2_title_footer import main as verify_title
from fix_uniform_chapter_cards import MANIFEST, patch_archive

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def assets(path, names):
    iso = pycdlib.PyCdlib()
    iso.open(str(path))
    try:
        result = {}
        for name in names:
            with iso.open_file_from_iso(iso_path=name) as stream:
                result[name] = stream.read()
        return result
    finally:
        iso.close()


def main(version):
    output = ROOT/f'work/output/release_{version}_build_tests.json'
    audit = ROOT/f'work/build/release_validation_{version}'
    audit.mkdir(parents=True, exist_ok=True)
    result = dict(version=version, outputs={}, native_iso_footer_readback={},
        campaign_proofreading_included=True, fresh_emulator_visual_validation='pending',
        full_stage28_battle_clear='pending', physical_console_tested=False,
        complete_playthrough_tested=False, checks={})
    paths = {p: ROOT/f'work/output/{prefix}{version}.iso' for p, prefix in
             [('PSP', 'SRWMX_EN_'), ('PS2', 'SRWMX_PS2_EN_')]}
    psp = read(ROOT/f'work/output/campaign_{version}_verification.json')
    assert psp['all_story_strings_verified'] and psp['script_blocks'] == 203
    assert psp['original_readable_uses_verified'] == 51366 and not psp['problems']
    text = read(ROOT/f'work/output/psp_text_{version}_verification.json')
    native = read(ROOT/f'work/output/psp_native_{version}_execution.json')
    assert text['passed'] and native['passed']
    result['checks']['psp_story'] = psp
    result['checks']['psp_text'] = text
    result['checks']['psp_native'] = native
    boot = assets(paths['PSP'], ['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    baseline = assets(ROOT/'work/output/SRWMX_EN_0.4.33.iso',
                      ['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    result['checks']['psp_rename'] = verify_psp_rename.verify(boot, baseline)
    result['checks']['psp_parts'] = verify_parts_layout.psp(boot)
    print('PSP current story, UI, native rename and Parts checks pass', flush=True)

    aggregate = read(ROOT/f'work/output/ps2_font_{version}_verification.json')
    names = ['/SLPS_253.45;1', '/DATA/MAP.BIN;1', '/DATA/STAGE.BIN;1',
             '/DATA/STATIC.BIN;1', '/DATA/PACKMAPC.BIN;1']
    data = assets(paths['PS2'], names)
    for name, raw in data.items():
        row = next(r for r in aggregate['files'] if r['path'] == name)
        assert hashlib.sha256(raw).hexdigest() == row['target_sha256'], name
    elf, maps, stage, static, pack = (data[n] for n in names)
    meta, info = aggregate['font'], copy.deepcopy(aggregate['stage30'])
    rebuilt_elf, rebuilt_map, story = refresh_story(elf, maps, meta, info)
    assert rebuilt_elf == elf and rebuilt_map == maps
    assert story['total_scenes'] == 203 and story['translated_strings'] == 51146
    assert story['changed_string_slots'] == 0 and story['missing_readable_strings'] == 0
    result['checks']['ps2_story'] = {k: v for k, v in story.items() if k != 'texts'}
    result['checks']['ps2_native_campaign'] = native_checks(elf, maps, stage, info, static, pack)
    assert len(result['checks']['ps2_native_campaign']['native_script_loads']) == 9
    assert len(result['checks']['ps2_native_campaign']['native_deployments']) == 3
    original = assets(ROOT/'Super Robot Taisen MX (Japan).iso', ['/SLPS_253.45;1'])['/SLPS_253.45;1']
    result['checks']['ps2_font'] = verify_font(original, elf, meta)
    result['checks']['ps2_difficulty'] = verify_difficulty(elf, aggregate['difficulty'])
    result['checks']['ps2_parts'] = verify_parts_layout.ps2(elf, meta)
    assert (ROOT/f'work/build/ps2/font_{version}/SLPS_253.45').read_bytes() == elf
    verify_title(version)
    result['checks']['ps2_title'] = read(ROOT/f'work/output/ps2_title_footer_{version}_execution.json')
    assert result['checks']['ps2_title']['passed']
    print('PS2 all 203 current scene blocks reproduce exactly; native campaign/font/Parts checks pass', flush=True)

    cards = read(MANIFEST)['rows']
    graphics = info['graphics']
    for off in (0x2f20400, 0x2f51c00, 0x4261c00):
        cards['PS2'].append(dict(pixel_offset=off, english=graphics['stage30_english'], previous_en=graphics['stage30_english']))
    for off in (0x2f20400, 0x2f51c00):
        cards['PS2'].append(dict(pixel_offset=graphics['animation_offset']+off-0x2ee0000,
            english=graphics['english'], previous_en=graphics['english']))
    import patch_chapter_cards
    for platform, path in paths.items():
        print('Auditing current native battle captions and all chapter cards:', platform, flush=True)
        result['checks'][platform+'_battle'] = verify_battle_release.verify(path, platform)
        result['checks'][platform+'_banners'] = patch_battle_banners.verify_iso(path, platform)
        raw = pack if platform == 'PS2' else assets(path, [patch_chapter_cards.ASSET])[patch_chapter_cards.ASSET]
        preview = audit/platform
        preview.mkdir(exist_ok=True)
        expected, rows, changed = patch_archive(raw, platform, cards[platform], preview)
        assert expected == raw and not changed
        result['checks'][platform+'_chapter_cards'] = dict(copies_verified=len(rows), all_uniform_renderer_matches=True)
        result['native_iso_footer_readback'][platform] = title_footer.verify_iso(path, platform, version)
        actual = digest(path)
        expected_hash = psp['iso_sha256'] if platform == 'PSP' else aggregate['target_sha256']
        assert actual == expected_hash
        result['outputs'][platform] = dict(file=path.name, bytes=path.stat().st_size, sha256=actual)
    assert native['iso_sha256'] == result['outputs']['PSP']['sha256']
    result['all_artifact_checks_passed'] = True
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('All artifact checks passed:', output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    main(parser.parse_args().version)
