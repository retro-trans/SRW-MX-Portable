"""Build a local PS2 chapter-28 port over the verified v0.4.36 image."""
import copy
import hashlib
import json
import shutil
import struct
import unicodedata
from pathlib import Path

import pycdlib
import play_order
import ps2_stage28
import title_footer
from build_ps2_dialogue import directory_position
from build_ps2_font import digest_file, digest_iso_file, files, write_udf_record
from patch_battle_banners import verify_iso as verify_banners
from verify_ps2_stage30 import native_checks
from verify_ps2_prologue_numbering import chapter_card

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.37'
BASE_VERSION = '0.4.36'
BASE = ROOT / f'work/build/ps2/stage28_{VERSION}'
SOURCE = ROOT / f'work/output/SRWMX_PS2_EN_{BASE_VERSION}.iso'
TARGET = ROOT / f'work/output/SRWMX_PS2_EN_{VERSION}.iso'
HISTORICAL = ROOT / 'work/build/ps2/reviewed_0.4.33'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', value).replace('@', ' ').split())


def register_full_builder_baseline(result):
    """Keep this incremental candidate usable by the normal PS2 full builder."""
    original = pycdlib.PyCdlib()
    original.open(str(ROOT / 'Super Robot Taisen MX (Japan).iso'))
    current = pycdlib.PyCdlib()
    current.open(str(TARGET))
    records = []
    for row in result['files']:
        path = row['path']
        records.append(dict(path=path, original_sha256=digest_iso_file(original, path),
            target_sha256=row['sha256'], bytes=row['bytes'],
            original_sector=original.get_record(iso_path=path).extent_location(),
            target_sector=current.get_record(iso_path=path).extent_location()))
    original.close()
    current.close()
    prologue = read(HISTORICAL / 'prologue.json')
    prologue['version'] = VERSION
    # Table addresses are unchanged; only script sectors were rewritten.
    info = read(BASE / 'stage30.json')
    font = read(BASE / 'patch.json')
    elf = (BASE / 'SLPS_253.45').read_bytes()
    maps = (BASE / 'MAP.BIN').read_bytes()
    offset = int(font['segment_offset'], 16)+int(info['script_sector_table_va'], 16)-int(font['segment_va'], 16)
    rel = struct.unpack_from('<204I', elf, offset)
    name_table = int(font['segment_offset'], 16)+int(info['script_name_table_va'], 16)-int(font['segment_va'], 16)
    names = []
    for ptr in struct.unpack_from('<203I', elf, name_table):
        at = int(font['segment_offset'], 16)+ptr-int(font['segment_va'], 16)
        names.append(elf[at:elf.index(0, at)].decode('ascii'))
    start = struct.unpack_from('<18I', elf, 0x37e438)[10]
    for scene in prologue['new_scene_blocks']:
        n = names.index(scene['scene'])
        raw = maps[(start+rel[n])*2048:(start+rel[n+1])*2048]
        scene.update(bytes=len(raw), target_sha256=ps2_stage28.sha(raw))
    save(BASE / 'prologue.json', prologue)
    aggregate = dict(version=VERSION, output=result['output'], bytes=result['bytes'],
        target_sha256=result['output_sha256'], source_build_version=BASE_VERSION,
        source_build_sha256=result['source_sha256'], files=records, font=font,
        stage30=info, prologue=prologue, difficulty=read(HISTORICAL/'difficulty.json'),
        library_corrections_manifest=(HISTORICAL/'library.json').relative_to(ROOT).as_posix(),
        library_preservation_reference=HISTORICAL.relative_to(ROOT).as_posix(),
        ui_detail_corrections=read(HISTORICAL/'ui_details.json'),
        battle_label_corrections=read(HISTORICAL/'battle_labels.json'),
        title_footer=result['footer'], stage28=result['stage28'],
        stage28_execution_checks=result['native_execution'],
        current_correction_report=f'work/output/ps2_stage28_{VERSION}_verification.json',
        pcsx2_fresh_boot_verified=False, full_stage28_battle_clear='pending', github_release=False)
    save(ROOT / f'work/output/ps2_font_{VERSION}_verification.json', aggregate)


def verify_story(elf, maps, report, info):
    font = read(BASE / 'patch.json')
    originals = ps2_stage28.sources()[2]
    translations = ps2_stage28.build_patch.load_translations([str(ROOT / report['source_file'])])
    sectors = struct.unpack_from('<18I', elf, 0x37e438)
    table = int(font['segment_offset'], 16)+int(info['script_sector_table_va'], 16)-int(font['segment_va'], 16)
    rel = struct.unpack_from('<204I', elf, table)
    records = []
    for scene in report['scenes']:
        index, name = scene['index'], scene['scene']
        raw = maps[(sectors[10]+rel[index])*2048:(sectors[10]+rel[index+1])*2048]
        assert ps2_stage28.sha(raw) == scene['target_sha256']
        source_commands, source_texts = play_order.load(originals[name], 0)
        commands, texts = play_order.load(raw, 0)
        assert commands == source_commands
        for jp, target in zip(source_texts, texts):
            if jp in translations[name]:
                expected = ps2_stage28.textfit.encode(translations[name][jp]).decode('cp932')
                assert normalize(target) == normalize(expected), (name, normalize(target), normalize(expected))
            else:
                assert target == jp and not ps2_stage28.export_rows.classify(jp)
        calls = [texts[c[1]] for c in commands if c[0] == 109]
        if name == 's0550':
            assert calls == ['i055b', 'i055a']
            full = read(ROOT / report['source_file'])
            for entry, slot in [(497, 400), (520, 427)]:
                row = next(r for r in full['rows'] if r['id'] == entry)
                expected = ps2_stage28.textfit.encode('Ritsu\u300c'+row['en']+'\u300d').decode('cp932')
                assert normalize(texts[slot]) == normalize(expected), (entry, texts[slot])
        records.append(dict(scene=name, exact_psp_commands=True, complete_english_readback=True,
                            scene_calls=calls, translated_strings=scene['translated_strings']))
    assert sum(r['translated_strings'] for r in records) == 1007
    return records


def build():
    assert not TARGET.exists() and not BASE.exists(), 'Preserve existing builds'
    baseline = read(ROOT / f'work/output/ps2_battle_banners_{BASE_VERSION}_verification.json')
    stats = SOURCE.stat()
    assert stats.st_size == baseline['bytes']
    print('Checking complete v0.4.36 baseline hash', flush=True)
    assert digest_file(SOURCE) == baseline['output_sha256']
    title_footer.verify_iso(SOURCE, 'PS2', BASE_VERSION)
    iso = pycdlib.PyCdlib()
    iso.open(str(SOURCE))
    def asset(path):
        with iso.open_file_from_iso(iso_path=path) as stream:
            return stream.read()
    old_elf = asset('/SLPS_253.45;1')
    old_maps = asset('/DATA/MAP.BIN;1')
    font = read(ROOT / f'work/build/ps2/font_{BASE_VERSION}/patch.json')
    assert ps2_stage28.sha(old_elf) == font['target_sha256']
    info = read(HISTORICAL / 'stage30.json')
    # Refresh evidence to the actual current blocks before appending stage 28.
    rel_at = int(font['segment_offset'], 16)+int(info['script_sector_table_va'], 16)-int(font['segment_va'], 16)
    rel = struct.unpack_from('<204I', old_elf, rel_at)
    sections = struct.unpack_from('<18I', old_elf, 0x37e438)
    for scene in info['scenes']:
        n = scene['index']
        block = old_maps[(sections[10]+rel[n])*2048:(sections[10]+rel[n+1])*2048]
        scene.update(bytes=len(block), target_sha256=ps2_stage28.sha(block))
    info['version'] = VERSION
    elf, maps, report = ps2_stage28.port(old_elf, old_maps, font, info)
    same_elf, same_maps, _ = ps2_stage28.port(elf, maps, font, copy.deepcopy(info))
    assert same_elf == elf and same_maps == maps, 'Port must be idempotent'
    elf, footer = title_footer.patch(elf, 'PS2', VERSION)
    font['target_sha256'] = ps2_stage28.sha(elf)
    assert len(elf) == len(old_elf) and len(maps) < len(old_maps)
    BASE.mkdir(parents=True)
    resources = {'/SLPS_253.45;1': elf, '/DATA/MAP.BIN;1': maps}
    for path, data in resources.items():
        (BASE / path.rsplit('/', 1)[-1].split(';')[0]).write_bytes(data)
    for name in ('STAGE.BIN', 'STATIC.BIN', 'PACKMAPC.BIN'):
        (BASE / name).write_bytes(asset('/DATA/'+name+';1'))
    save(BASE / 'patch.json', font)
    save(BASE / 'stage30.json', info)
    save(BASE / 'stage28.json', report)
    story_checks = verify_story(elf, maps, report, info)
    print('Executing native scene loaders, deployment and campaign progression', flush=True)
    execution = native_checks(elf, maps, (BASE/'STAGE.BIN').read_bytes(), info,
                              (BASE/'STATIC.BIN').read_bytes(), (BASE/'PACKMAPC.BIN').read_bytes())
    assert len(execution['native_script_loads']) == 9
    for entry in (0x348588, 0x348908):
        before = chapter_card(old_elf, 7, 8, 28, entry)
        after = chapter_card(elf, 7, 8, 28, entry)
        assert before == after and after['number'] == 28
    save(BASE / 'native_execution.json', execution)
    print('Creating local PS2 test image', flush=True)
    shutil.copyfile(SOURCE, TARGET)
    allowed = []
    with TARGET.open('r+b') as stream:
        for path, data in resources.items():
            record = iso.get_record(iso_path=path)
            start = record.extent_location()*2048
            assert len(data) <= record.data_length
            stream.seek(start)
            stream.write(data)
            stream.write(bytes(record.data_length-len(data)))
            allowed.append((start, start+record.data_length))
            if len(data) != record.data_length:
                position = directory_position(iso, SOURCE, path)
                stream.seek(position+10)
                stream.write(struct.pack('<I', len(data))+struct.pack('>I', len(data)))
                allowed.append((position+10, position+18))
                udf_path = '/data/map.bin'
                entry = iso.get_record(udf_path=udf_path)
                assert len(entry.alloc_descs) == 1
                entry.set_data_length(len(data))
                entry.set_data_location(record.extent_location(), record.extent_location()-iso.udf_main_descs.partitions[0].part_start_location)
                entry.log_block_recorded = (len(data)+2047)//2048
                write_udf_record(stream, entry)
                allowed.append((entry.extent_location()*2048, (entry.extent_location()+1)*2048))
    print('Verifying complete image, unchanged disc bytes and both filesystems', flush=True)
    # Byte-level comparison also protects unused disc areas and old allocations.
    target_hash = hashlib.sha256()
    with SOURCE.open('rb') as before, TARGET.open('rb') as after:
        position = 0
        while raw := before.read(8*1024*1024):
            current = after.read(len(raw))
            assert len(current) == len(raw)
            target_hash.update(current)
            masked = bytearray(current)
            for a, z in allowed:
                left, right = max(position, a), min(position+len(raw), z)
                if left < right:
                    masked[left-position:right-position] = raw[left-position:right-position]
            assert masked == raw, ('Unrelated disc bytes changed', position)
            position += len(raw)
        assert not after.read(1)
    check = pycdlib.PyCdlib()
    check.open(str(TARGET))
    file_checks = []
    for path in sorted(files(iso)):
        old_rec, new_rec = iso.get_record(iso_path=path), check.get_record(iso_path=path)
        assert new_rec.extent_location() == old_rec.extent_location(), path
        expected = ps2_stage28.sha(resources[path]) if path in resources else digest_iso_file(iso, path)
        actual = digest_iso_file(check, path)
        assert actual == expected, path
        assert new_rec.data_length == (len(resources[path]) if path in resources else old_rec.data_length)
        file_checks.append(dict(path=path, sha256=actual, bytes=new_rec.data_length, changed=path in resources))
    for path, data in resources.items():
        udf_path = '/SLPS_253.45' if path == '/SLPS_253.45;1' else '/data/map.bin'
        with check.open_file_from_iso(udf_path=udf_path) as stream:
            assert stream.read() == data
    with check.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
        actual_map = stream.read()
    with check.open_file_from_iso(iso_path='/SLPS_253.45;1') as stream:
        actual_elf = stream.read()
    verify_story(actual_elf, actual_map, report, info)
    check.close()
    iso.close()
    assert (SOURCE.stat().st_size, SOURCE.stat().st_mtime_ns) == (stats.st_size, stats.st_mtime_ns)
    assert digest_file(ROOT / report['source_file']) == report['source_sha256']
    footer['readback'] = title_footer.verify_iso(TARGET, 'PS2', VERSION)
    font_dir = ROOT / f'work/build/ps2/font_{VERSION}'
    font_dir.mkdir()
    (font_dir / 'SLPS_253.45').write_bytes(elf)
    save(font_dir / 'patch.json', font)
    from verify_ps2_title_footer import main as verify_title
    verify_title(VERSION)
    result = dict(version=VERSION, platform='PS2', base_version=BASE_VERSION,
        output=TARGET.relative_to(ROOT).as_posix(), bytes=TARGET.stat().st_size,
        output_sha256=target_hash.hexdigest(), source_sha256=baseline['output_sha256'],
        stage28=report, story_readback=story_checks, native_execution=execution,
        footer=footer, files=file_checks, iso9660_and_udf_readback=True,
        all_other_disc_bytes_preserved=True, all_other_scene_bytes_preserved=True,
        native_banners_preserved=verify_banners(TARGET, 'PS2'),
        full_stage28_battle_clear='pending', local_build_only=True, github_release=False)
    save(ROOT / f'work/output/ps2_stage28_{VERSION}_verification.json', result)
    save(ROOT / f'work/translation/en/ps2/stage28_{VERSION}.en.json', result)
    save(ROOT / f'work/output/ps2_title_footer_{VERSION}_verification.json', dict(version=VERSION, footer=footer))
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt', TARGET.with_name(TARGET.stem+'_FONT_LICENSE.txt'))
    register_full_builder_baseline(result)
    print('Verified PS2', VERSION, result['output_sha256'], flush=True)


if __name__ == '__main__':
    build()
