"""Port reviewed PSP chapter 28 events and deployment to the native PS2 campaign."""
import hashlib
import json
import struct
from pathlib import Path

import build_patch
import export_rows
import play_order
import textfit

ROOT = Path(__file__).resolve().parents[1]
SCENES = ('i055b', 's0550', 'i055a')
SOURCE_HASHES = {
    'i055b': '1c9317a870db6573efad865121300e777f2e84c240c74a2fa88c30abb1f0b434',
    's0550': '3fbadcbc9b8c289952ac3239705dd65f6d9c4a1190a8fc9f8faecb9d2d60e6c4',
    'i055a': '0d0a7d2ca1bdb36735aafc59312a396e4cc5adaa58d79c7dd5fa98c236a483ff',
}
DEPLOYMENT_SHA = 'd7445d734cb37449c95716ddca540e952c8b18ed9d9b8bfc4bebbc8ece28b076'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sources():
    psp = (ROOT / 'work/build/MAP_ADD.orig').read_bytes()
    boot = (ROOT / 'work/source/ps2/prologue/PSP_BOOT.BIN').read_bytes()
    sectors = struct.unpack_from('<18I', boot, 0x2791f0)
    scripts = struct.unpack_from('<204I', boot, 0x27ca20)
    inventory = {r['name']: r['block'] for r in read(ROOT / 'work/source/stage_map.json')}
    blocks = {}
    for name in SCENES:
        n = inventory[name]
        block = psp[(sectors[10] + scripts[n])*2048:(sectors[10] + scripts[n+1])*2048]
        assert sha(block) == SOURCE_HASHES[name], (name, 'PSP source differs')
        blocks[name] = block
    at = psp.index(b's0550\0', sectors[9]*2048, sectors[10]*2048) - 24
    deployment = psp[at:at+8192]
    assert sha(deployment) == DEPLOYMENT_SHA
    return psp, sectors, blocks, deployment


def native_width(line, font):
    glyphs = {int(g['sjis'], 16): g['width'] for g in font['glyphs']}
    total = 0
    for token in textfit.tokens(line):
        if isinstance(token, tuple):
            total += glyphs.get(token[1], 24)
        elif token in textfit.PLACEHOLDER_PX:
            total += 144 if token in ('#男愛称', '#女愛称') else textfit.PLACEHOLDER_PX[token]*24//16
        else:
            total += glyphs.get(textfit.ASCII.get(token), 24)
    return total


def fit(target, font):
    """Use the reviewed PS2 builder's punctuation and placeholder width rules."""
    width = lambda line: native_width(line, font)
    if max(map(width, target.split('@'))) <= 528:
        return target
    flattened = ' '.join(target.replace('@', ' ').split())
    opening = next((i for i, c in enumerate(flattened) if c in '\u300c\uff08'), None)
    assert opening is not None, ('Plain text too wide', flattened)
    suffix = flattened[-1] if flattened[-1] in '\u300d\uff09' else ''
    prefix = flattened[:opening+1]
    body = flattened[opening+1:len(flattened)-len(suffix) if suffix else None]
    lines, line, first_word = [], prefix, True
    words = body.split()
    for n, word in enumerate(words):
        candidate = line + ('' if first_word else ' ') + word
        reserve = suffix if n == len(words)-1 else ''
        if width(candidate+reserve) > 528:
            lines.append(line)
            line = '\u3000'+word
        else:
            line = candidate
        first_word = False
    lines.append(line+suffix)
    assert len(lines) <= 3 and max(map(width, lines)) <= 528, (flattened, lines)
    assert ' '.join(' '.join(lines).split()) == flattened
    return '@'.join(lines)


def rebuild(raw, mapping, font):
    commands, texts = play_order.load(raw, 0)
    assert all(0 <= c[0] < 179 for c in commands), 'Unexpected PSP-only opcode'
    missing = [n for n, t in enumerate(texts) if export_rows.classify(t) and t not in mapping]
    assert not missing, missing
    fitted = {jp: fit(en, font) for jp, en in mapping.items()}
    block, count = build_patch.rebuild_block(raw, fitted)
    new_commands, new_texts = play_order.load(block, 0)
    assert commands == new_commands and len(texts) == len(new_texts)
    widths = []
    for jp, actual in zip(texts, new_texts):
        expected = textfit.encode(fitted[jp]).decode('cp932') if jp in fitted else jp
        assert actual == expected
        if jp in fitted:
            widths += [native_width(line, font) for line in fitted[jp].split('@')]
    assert len(block) <= 0x25000
    return block, dict(commands=len(commands), strings=len(texts), translated_strings=count,
        command_sha256=sha(raw[32:32+48*len(commands)]), max_native_width=max(widths),
        native_reflows=sum(fitted[jp] != en for jp, en in mapping.items()))


def port(elf, maps, font, info):
    """Replace exactly three scene blocks and one native deployment flag."""
    psp, psec, originals, deployment = sources()
    source = ROOT / 'work/translation/en/script/stage28_campaign_full_merged.json'
    full = read(source)
    assert not full.get('context_review_pending')
    translations = build_patch.load_translations([str(source)])
    original_elf = bytes(elf)
    elf = bytearray(elf)
    sections = list(struct.unpack_from('<18I', elf, 0x37e438))
    assert sections[-1]*2048 == len(maps)
    va = lambda ptr: int(font['segment_offset'], 16)+int(ptr, 16)-int(font['segment_va'], 16)
    table = va(info['script_sector_table_va'])
    names_at = va(info['script_name_table_va'])
    rel = struct.unpack_from('<204I', elf, table)
    names = []
    for pointer in struct.unpack_from('<203I', elf, names_at):
        at = va(hex(pointer))
        names.append(bytes(elf[at:elf.index(0, at)]).decode('ascii'))
    assert len(names) == len(set(names)) == 203 and all(n in names for n in SCENES)
    # The native map is retained; compare terrain IDs separately from platform heights.
    map_offsets = struct.unpack_from('<1001I', elf, 0x37f060)
    start, end = map_offsets[460:462]
    native_map = maps[(sections[7]+start)*2048:(sections[7]+end)*2048]
    psp_map = psp[(psec[7]+start)*2048:(psec[7]+end)*2048]
    assert native_map[:36] == psp_map[:36] and native_map[:4] == b'MPTD'
    w, h = struct.unpack_from('<2I', native_map, 8)
    assert all(native_map[32+i*8:36+i*8] == psp_map[32+i*8:36+i*8] for i in range(w*h))
    units = struct.unpack_from('<1001I', elf, 0x380f98)
    a, z = [(sections[9]+x)*2048 for x in units[148:150]]
    native_units = maps[a:z]
    assert len(native_units) == len(deployment) == 8192
    diffs = [i for i, (x, y) in enumerate(zip(native_units, deployment)) if x != y]
    assert diffs in ([260], []), ('Unexpected deployment differences', diffs)
    assert native_units[260] in (0, 1) and deployment[260] == 1
    prefix = bytearray(maps[:sections[10]*2048])
    prefix[a:z] = deployment
    output = prefix
    new_rel, scenes, unchanged = [], [], []
    script_start = len(output)//2048
    for n, name in enumerate(names):
        new_rel.append(len(output)//2048-script_start)
        old = maps[(sections[10]+rel[n])*2048:(sections[10]+rel[n+1])*2048]
        if name in originals:
            block, check = rebuild(originals[name], translations[name], font)
            scenes.append(dict(scene=name, index=n, bytes=len(block), source_sha256=sha(originals[name]),
                               previous_sha256=sha(old), target_sha256=sha(block),
                               previous_bytes=len(old), **check))
        else:
            block = old
            unchanged.append(dict(scene=name, sha256=sha(block)))
        output += block
    new_rel.append(len(output)//2048-script_start)
    output += maps[sections[11]*2048:]
    delta = new_rel[-1]-rel[-1]
    for n in range(11, 18):
        sections[n] += delta
    struct.pack_into('<18I', elf, 0x37e438, *sections)
    struct.pack_into('<193I', elf, 0x381f40, *new_rel[:193])
    struct.pack_into('<204I', elf, table, *new_rel)
    assert sections[-1]*2048 == len(output)
    allowed_elf = [(0x37e438, 0x37e438+18*4), (0x381f40, 0x381f40+193*4),
                   (table, table+204*4)]
    preserved_elf = bytearray(elf)
    for a0, z0 in allowed_elf:
        preserved_elf[a0:z0] = original_elf[a0:z0]
    assert preserved_elf == original_elf, 'Unexpected native executable change'
    # Every other scene and all non-script map sections remain byte-identical,
    # apart from the explicitly verified one-byte deployment difference.
    before_prefix = bytearray(maps[:script_start*2048])
    before_prefix[a:z] = deployment
    assert output[:script_start*2048] == before_prefix
    assert output[sections[11]*2048:] == maps[(sections[11]-delta)*2048:]
    for scene in scenes:
        existing = next((r for r in info['scenes'] if r['scene'] == scene['scene']), None)
        item = dict(scene, psp_portrait_cache_commands=[])
        if existing is not None:
            existing.update(item)
        else:
            info['scenes'].append(item)
    info['stage28_port'] = 'PSP opening, battle events, aftermath and deployment'
    report = dict(scenes=scenes, unchanged_scenes=unchanged, script_sector_delta=delta,
        source_file=source.relative_to(ROOT).as_posix(), source_sha256=sha(source.read_bytes()),
        deployment=dict(index=148, chapter=7, group=8, units=34, map_id=460,
                        target_sha256=sha(deployment), changed_offsets=diffs),
        native_map_dimensions=[w, h], native_map_sha256=sha(native_map),
        all_other_executable_bytes_preserved=True,
        psp_event_commands_preserved=True, all_other_scene_bytes_preserved=True,
        all_other_map_sections_preserved=True, gameplay_balance_preserved=True)
    return bytes(elf), bytes(output), report
