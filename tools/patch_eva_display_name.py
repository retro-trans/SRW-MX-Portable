"""Shorten the shared Mass-produced EVA status name in the native database."""
import json
import struct

import textfit
from name_consistency_055 import line_width
from patch_at_field import sha
from static2_extract import sections
from verify_text_build import read_iso

ENTRY = 435
OLD = 'Mass-produced EVA'
NEW = 'MP EVA'
ASSETS = {'PSP': '/PSP_GAME/USRDIR/STATIC2_ADD.BIN', 'PS2': '/DATA/FIX00.DAT;1'}


def patch(data, platform, preview=None):
    tables = sections(data) if platform == 'PSP' else sections(data, 0)
    start, size, count = tables['Strg']
    offsets = struct.unpack_from(f'<{count}I', data, start + 12)
    offset = offsets[ENTRY]
    old = textfit.encode(OLD) + b'\0'
    new = textfit.encode(NEW) + b'\0'
    assert offsets.count(offset) == 1 and 12 + 4 * count <= offset <= size - len(old)
    assert len(new) < len(old)
    new = new.ljust(len(old), b'\0')
    start += offset
    end = start + len(old)
    before = data[start:end]
    assert before in (old, new), 'Unexpected Mass-produced EVA string allocation'

    pilot, _, _ = tables['Pilt']
    unit, _, _ = tables['Unit']
    pilot_ids = (49, 430)
    unit_ids = (214, 337)
    for index in pilot_ids:
        assert struct.unpack_from('<2H', data, pilot + 12 + index * 184) == (ENTRY, ENTRY)
    for index in unit_ids:
        assert struct.unpack_from('<H', data, unit + 12 + index * 124)[0] == ENTRY

    result = data[:start] + new + data[end:]
    old_width, new_width = line_width(OLD, platform), line_width(NEW, platform)
    report = dict(platform=platform, entry=ENTRY, pilot_ids=pilot_ids, unit_ids=unit_ids,
                  regions=[dict(id='mp_eva', english=NEW, text=NEW, old_name=OLD,
                                already_translated=before == new, offset=hex(start),
                                old_width=old_width, new_width=new_width)],
                  byte_ranges=[[start, end]], native_pointers_preserved=True,
                  source_resource_sha256=sha(data), target_resource_sha256=sha(result))
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        (preview / 'layout.en.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return result, report


def verify_iso(path, platform):
    asset = ASSETS[platform]
    data = read_iso(str(path), [asset])[asset]
    expected, report = patch(data, platform)
    assert expected == data and report['regions'][0]['already_translated']
    return report
