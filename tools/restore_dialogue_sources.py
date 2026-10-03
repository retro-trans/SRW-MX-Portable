"""Restore ignored bilingual final dialogue files from a user's original ISO.

Only English rows and scene:string-index references are distributed by the repo.
usage: python tools/restore_dialogue_sources.py original.iso [--overwrite]
"""
import argparse
import copy
import io
import json
from pathlib import Path
import struct

import pycdlib

ROOT = Path(__file__).resolve().parents[1]


def restore(original, output_root=ROOT, overwrite=False):
    iso = pycdlib.PyCdlib()
    iso.open(str(original))
    try:
        data = {}
        for key, path in [('boot', '/PSP_GAME/SYSDIR/BOOT.BIN'),
                          ('map', '/PSP_GAME/USRDIR/MAP_ADD.BIN')]:
            stream = io.BytesIO()
            iso.get_file_from_iso_fp(stream, iso_path=path)
            data[key] = stream.getvalue()
    finally:
        iso.close()
    boot, archive = data['boot'], data['map']
    sectors = struct.unpack_from('<204I', boot, 0x27CA20)
    pointers = struct.unpack_from('<203I', boot, 0x27D3A8)
    scenes, blocks = {}, []
    for block, pointer in enumerate(pointers):
        p = pointer + 0x60
        name = boot[p:boot.index(b'\0', p)].decode('ascii')
        offset = 0x579C * 2048 + sectors[block] * 2048
        raw = archive[offset:0x579C * 2048 + sectors[block + 1] * 2048]
        count, table = struct.unpack_from('<2I', raw, 8)
        entries = struct.unpack_from('<%dI' % count, raw, table)
        scenes[name] = [raw[p:raw.index(b'\0', p)].decode('cp932') for p in entries]
        blocks.append({'block': block, 'offset': offset, 'name': name, 'strings': count})
    script = ROOT / 'work/translation/en/script'
    paths = [script / 'prologue_merged.en.json']
    paths += sorted(script.glob('stage[0-9][0-9]_campaign_full_merged.en.json'))
    paths += [script / 'save_message_kaine_merged.en.json']
    outputs = []
    for path in paths:
        content = copy.deepcopy(json.loads(path.read_text(encoding='utf8')))
        for row in content['rows']:
            originals = []
            for use in row['uses']:
                name, index = use.rsplit(':', 1)
                originals.append(scenes[name][int(index)])
            if not originals or any(value != originals[0] for value in originals):
                raise ValueError('Conflicting or missing source locations in %s row %s' % (path.name, row['id']))
            row['jp'] = originals[0]
        relative = path.relative_to(ROOT)
        destination = Path(output_root) / relative.with_name(path.name.replace('.en.json', '.json'))
        outputs.append((destination, content))
    destinations = [path for path, _ in outputs] + [Path(output_root) / 'work/source/stage_map.json']
    if not overwrite and any(path.exists() for path in destinations):
        raise FileExistsError('Local source files already exist; use --overwrite only if replacement is intended.')
    for destination, content in outputs + [(destinations[-1], blocks)]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(content, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
    print('Restored %d final dialogue files from your ISO; all output stays local.' % len(outputs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--output-root', type=Path, default=ROOT)
    args = parser.parse_args()
    restore(args.original, args.output_root, args.overwrite)
