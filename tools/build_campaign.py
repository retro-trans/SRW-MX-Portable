"""Check all reviewed story inputs, then optionally build a complete local test ISO.

python tools/build_campaign.py original.iso 0.4.3 [--build]
No release, tag, upload or external catalog changes are performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import pycdlib
import build_patch
import export_rows
import play_order
import textfit
from record_campaign_context_review import fingerprint

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(original, version):
    folder = ROOT/'work/translation/en/script'
    files = [folder/'prologue_merged.json'] + [folder/f'stage{n:02d}_campaign_full_merged.json' for n in range(1,59)]
    reviews = {}
    for name in ('campaign_context_reviews.json', 'stages31_end_context_reviews.json'):
        path = ROOT/'work/output'/name
        if path.exists():
            reviews.update(read(path)['stages'])
    all_uses = {}
    for n, path in enumerate(files):
        data = read(path)
        if n:
            assert not data['context_review_pending'], (n, 'context review pending')
            actual = fingerprint(data['rows'])
            # Public final files carry their review fingerprint. Restoring the
            # original source from an owned ISO reproduces it without requiring
            # ignored local coordinator journals from another checkout.
            assert actual == data['context_review']['fingerprint'], (n, 'embedded review fingerprint')
            if str(n) in reviews:
                assert actual == reviews[str(n)]['fingerprint'], (n, 'coordinator review fingerprint')
        for row in data['rows']:
            assert row['en'].strip(), (n, row['id'], 'empty translation')
            if row['kind'] == 'plain':
                assert row['en'].count('@') == row['jp'].count('@'), (n, row['id'], 'plain segment shape')
                assert all(textfit.px(s) <= 352 for s in row['en'].split('@')), (n, row['id'], 'plain fit')
            else:
                assert textfit.fit_dialogue(row['speaker_en'], row['en'], row['kind']=='thought')[2], (n, row['id'], 'dialogue fit')
            for use in row['uses']:
                value = (row['jp'], row['kind'], row['speaker_en'], row['en'])
                assert use not in all_uses or all_uses[use] == value, (use, 'conflicting translation inputs')
                all_uses[use] = value
    trans = build_patch.load_translations([str(p) for p in files])
    iso = pycdlib.PyCdlib()
    iso.open(str(original))
    map_data = build_patch.iso_read(iso, '/PSP_GAME/USRDIR/MAP_ADD.BIN')
    boot = build_patch.iso_read(iso, '/PSP_GAME/SYSDIR/BOOT.BIN')
    iso.close()
    assert map_data == (ROOT/'work/build/MAP_ADD.orig').read_bytes(), 'Original MAP source differs'
    scenes = read(ROOT/'work/source/stage_map.json')
    assert len(scenes) == build_patch.NBLOCKS == 203
    covered = set()
    for scene in scenes:
        _, strings = play_order.load(map_data, scene['offset'])
        for index, text in enumerate(strings):
            use = f"{scene['name']}:{index}"
            if export_rows.classify(text) is None:
                assert use not in all_uses, (use, 'technical label scheduled for translation')
                continue
            assert use in all_uses, (use, 'readable source omitted')
            assert all_uses[use][0] == text, (use, 'original source differs')
            assert text in trans[scene['name']], (use, 'not scheduled for insertion')
            covered.add(use)
    assert covered == set(all_uses) and len(covered) == 51366
    rel = struct.unpack_from('<204I', boot, build_patch.BLOCK_TABLE)
    base = build_patch.SCRIPT_SECTOR*0x800
    blocks = []
    build_patch.BIG_BLOCKS.clear()
    for scene in sorted(scenes, key=lambda x:x['block']):
        i = scene['block']
        raw = map_data[base+rel[i]*0x800:base+rel[i+1]*0x800]
        rebuilt, count = build_patch.rebuild_block(raw, trans.get(scene['name'], {}))
        blocks.append(dict(scene=scene['name'], block=i, original_size=len(raw), translated_size=len(rebuilt), translated_strings=count))
    assert len(blocks) == 203
    result = dict(version=version, local_build_only=True, source_files=[str(p.relative_to(ROOT)).replace('\\','/') for p in files],
                  input_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  reviewed_stages=58, covered_original_readable_uses=len(covered), blocks=blocks,
                  original_map_sha256=hashlib.sha256(map_data).hexdigest(),
                  font_sha256=hashlib.sha256((ROOT/'work/build/STATIC2_ADD.BIN').read_bytes()).hexdigest(),
                  larger_than_original_limit=[b for b in blocks if b['translated_size']>build_patch.MAX_BLOCK],
                  map_terrain_translated=True, configured_wnd_headers_translated=True,
                  runtime_heap_verified=False, problems=[])
    return files, result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original', type=Path)
    ap.add_argument('version')
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--verify-existing', action='store_true', help='Recover the input manifest for an existing ISO; independent readback is still required')
    args = ap.parse_args()
    assert not (args.build and args.verify_existing), 'Choose build or existing-file verification'
    files, report = prepare(args.original, args.version)
    print(json.dumps({k:v for k,v in report.items() if k not in ('blocks','input_sha256','source_files')}, indent=1))
    if not (args.build or args.verify_existing):
        return
    if args.build:
        build_patch.BIG_BLOCKS.clear()
        argv = []
        for path in files:
            argv += ['--scenes-file', str(path)]
        report['build_status'] = 'building'
        (ROOT/f'work/output/campaign_{args.version}_inputs.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
        build_patch.main(str(args.original), args.version, *argv, '--native-font4x', '--text', '--battle', '--chapter-cards')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in report['input_sha256'].items()), 'Inputs changed during build'
    report['iso'] = f'work/output/SRWMX_EN_{args.version}.iso'
    report['iso_sha256'] = file_sha256(ROOT/report['iso'])
    report['build_status'] = 'existing_file_requires_readback' if args.verify_existing else 'built_requires_readback'
    (ROOT/f'work/output/campaign_{args.version}_inputs.json').write_text(json.dumps(report, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
