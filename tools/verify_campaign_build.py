"""Read back every story string, command and native font hook from a complete ISO.

python tools/verify_campaign_build.py original.iso 0.4.3
This verifies the disk artifact; live loading/playtesting is separate evidence.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct

import pycdlib
import build_patch
import insert_text
import make_latin_font
import native_font4x
import patch_chapter_cards
import play_order
import redraw_banners
import redraw_wnd
import insert_tiles
import textfit

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def iso_bytes(iso, path):
    stream = io.BytesIO()
    iso.get_file_from_iso_fp(stream, iso_path=path)
    return stream.getvalue()


def digest_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify(original, version):
    report = read(ROOT/f'work/output/campaign_{version}_inputs.json')
    files = [ROOT/p for p in report['source_files']]
    assert len(files) == 59
    for name, expected in report['input_sha256'].items():
        assert digest_file(ROOT/name) == expected, ('changed source input', name)
    translated = build_patch.load_translations([str(p) for p in files])
    old = pycdlib.PyCdlib()
    new = pycdlib.PyCdlib()
    old.open(str(original))
    path = ROOT/f'work/output/SRWMX_EN_{version}.iso'
    new.open(str(path))
    oboot = iso_bytes(old, '/PSP_GAME/SYSDIR/BOOT.BIN')
    boot = iso_bytes(new, '/PSP_GAME/SYSDIR/BOOT.BIN')
    assert boot == iso_bytes(new, '/PSP_GAME/SYSDIR/EBOOT.BIN')
    omap = iso_bytes(old, '/PSP_GAME/USRDIR/MAP_ADD.BIN')
    mmap = iso_bytes(new, '/PSP_GAME/USRDIR/MAP_ADD.BIN')
    oldrel = struct.unpack_from('<204I', oboot, build_patch.BLOCK_TABLE)
    newrel = struct.unpack_from('<204I', boot, build_patch.BLOCK_TABLE)
    assert newrel[0] == 0 and all(a < b for a,b in zip(newrel,newrel[1:]))
    base = build_patch.SCRIPT_SECTOR*0x800
    scenes = sorted(read(ROOT/'work/source/stage_map.json'), key=lambda x:x['block'])
    checked = changed = preserved = commands = 0
    all_uses = {u for p in files for r in read(p)['rows'] for u in r['uses']}
    seen = set()
    blocks = []
    for scene in scenes:
        n = scene['block']
        oldoff, newoff = base+oldrel[n]*0x800, base+newrel[n]*0x800
        ocmds, ostrings = play_order.load(omap, oldoff)
        ncmds, nstrings = play_order.load(mmap, newoff)
        assert ocmds == ncmds, (scene['name'], 'script commands changed')
        assert len(ostrings) == len(nstrings)
        commands += len(ocmds)
        for index, (before, after) in enumerate(zip(ostrings, nstrings)):
            want = translated.get(scene['name'], {}).get(before)
            actual = after.encode('cp932')
            expected = textfit.encode(want) if want is not None else before.encode('cp932')
            assert actual == expected, (scene['name'], index, 'stored text differs')
            checked += 1
            changed += actual != before.encode('cp932')
            preserved += want is None
            use = f"{scene['name']}:{index}"
            if use in all_uses:
                assert want is not None
                seen.add(use)
        blocks.append(dict(scene=scene['name'], commands=len(ocmds), strings=len(ostrings),
                           translated_size=(newrel[n+1]-newrel[n])*0x800))
    assert seen == all_uses and len(seen) == 51366
    delta = newrel[-1]-oldrel[-1]
    orig_sec = struct.unpack_from('<18I', oboot, build_patch.SECTION_TABLE)
    new_sec = struct.unpack_from('<18I', boot, build_patch.SECTION_TABLE)
    assert new_sec == tuple(x+(delta if i>build_patch.SCRIPT_SECTION else 0) for i,x in enumerate(orig_sec))
    assert new_sec[-1]*0x800 == len(mmap)
    # The local build also contains the existing native English banner work.
    # Compare all non-script bytes against that explicitly scoped asset patch.
    banner_map = redraw_banners.patch(omap, 'MAP_ADD.BIN')
    if report.get('map_terrain_translated'):
        banner_map = insert_tiles.patch(banner_map)
    assert mmap[:base] == banner_map[:base], 'Unexpected pre-script asset changes'
    assert mmap[base+newrel[-1]*0x800:] == banner_map[base+oldrel[-1]*0x800:], 'Unexpected post-script asset changes'
    del banner_map

    static = iso_bytes(new, '/PSP_GAME/USRDIR/STATIC2_ADD.BIN')
    fixture = (ROOT/'work/build/STATIC2_ADD.BIN').read_bytes()
    assert digest_file(ROOT/'work/build/STATIC2_ADD.BIN') == report['font_sha256']
    assert len(static) == len(fixture) == 3576512
    # Only compare the font atlas here; other STATIC2 sections contain native UI translations.
    font_end = make_latin_font.ATLAS + 128*40*18
    assert static[make_latin_font.ATLAS:font_end] == fixture[make_latin_font.ATLAS:font_end]
    layout = read(ROOT/'work/build/native_font4x/layout.json')
    high, index, _ = native_font4x.atlas()
    width = native_font4x.vwf.width_table(str(ROOT/'work/build/STATIC2_ADD.BIN'))
    code, hooks, relocs, _ = native_font4x.assemble(layout['table_va'], layout['index_va'], layout['atlas_va'], layout['code_va'])
    for va, expected in [(layout['table_va'], width), (layout['index_va'], index), (layout['atlas_va'],high), (layout['code_va'],code), *hooks]:
        assert boot[0x60+va:0x60+va+len(expected)] == expected, ('native font payload/hook', hex(va))
    sections = insert_text.elf(boot)
    offset, size = struct.unpack_from('<2I', boot, sections['.rel.text']+16)
    installed_relocs = {struct.unpack_from('<2I',boot, offset+k) for k in range(0,size,8)}
    assert set(relocs).issubset(installed_relocs)
    assert {(call,4) for call in native_font4x.GLYPH_CALLS}.issubset(installed_relocs)
    assert boot[0x60+layout['original_filesz']:0x60+layout['original_memsz']] == bytes(layout['original_memsz']-layout['original_filesz'])
    phoff = struct.unpack_from('<I',boot,28)[0]
    filesz, memsz = struct.unpack_from('<2I',boot,phoff+16)
    assert filesz == memsz and filesz >= layout['new_size']

    specs = read(ROOT/'work/translation/en/ui/all_chapter_cards.json')
    expected_cards, cards = patch_chapter_cards.patch_archive(iso_bytes(old,patch_chapter_cards.ASSET), specs, ROOT/'work/build/chapter_cards/verification')
    assert iso_bytes(new,patch_chapter_cards.ASSET) == expected_cards
    if report.get('configured_wnd_headers_translated'):
        expected_wnd = redraw_wnd.patch_wnd(iso_bytes(old, '/PSP_GAME/USRDIR/WND.BIN'))
        assert iso_bytes(new, '/PSP_GAME/USRDIR/WND.BIN') == expected_wnd
    changed_files, unchanged_files = [], []
    for folder, _, names in old.walk(iso_path='/'):
        for name in names:
            asset = folder.rstrip('/')+'/'+str(name)
            if patch_chapter_cards.digest_iso_file(old,asset) == patch_chapter_cards.digest_iso_file(new,asset):
                unchanged_files.append(asset)
            else:
                changed_files.append(asset)
    allowed = {'/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN','/PSP_GAME/USRDIR/STATIC2_ADD.BIN',
               '/PSP_GAME/USRDIR/MAP_ADD.BIN','/PSP_GAME/USRDIR/BATTLE2.BIN','/PSP_GAME/USRDIR/WND.BIN',
               '/PSP_GAME/PARAM.SFO',patch_chapter_cards.ASSET}
    assert set(changed_files) <= allowed, ('Unexpected ISO changes', changed_files)
    old.close()
    new.close()
    assert digest_file(path) == report['iso_sha256']
    result = dict(version=version, all_story_strings_verified=True, source_files=59,
                  original_readable_uses_verified=len(seen), string_records_checked=checked,
                  translated_string_records=changed, untouched_technical_records=preserved,
                  script_blocks=203, raw_commands_preserved=commands, blocks=blocks,
                  relocated_block_and_section_tables_verified=True,
                  non_script_map_assets_verified=True,
                  native_banner_translation_verified=True,
                  map_terrain_translated=bool(report.get('map_terrain_translated')),
                  configured_wnd_headers_verified=bool(report.get('configured_wnd_headers_translated')),
                  native_font4x_payload_and_hooks_verified=True, native_font_relocations_verified=True,
                  high_resolution_descender_masks_verified=True, native_atlas_sha256=hashlib.sha256(high).hexdigest(),
                  native_font_hook_count=len(hooks), texture_replacement_required=False,
                  chapter_atlases_verified=len(cards), scenario_titles_covered=67,
                  changed_iso_files=changed_files, unchanged_iso_files=unchanged_files,
                  iso_sha256=report['iso_sha256'], emulator_loading_verified=False, problems=[])
    (ROOT/f'work/output/campaign_{version}_verification.json').write_text(json.dumps(result,indent=1), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='blocks'},indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original',type=Path)
    ap.add_argument('version')
    args = ap.parse_args()
    verify(args.original,args.version)
