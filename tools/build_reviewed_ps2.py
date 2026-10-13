"""Refresh all reviewed story text over a verified PS2 port, preserving its fixes."""
import argparse
import copy
import hashlib
import json
import shutil
import struct
import unicodedata
from pathlib import Path

import pycdlib
import build_patch
import export_rows
import insert_text as it
import play_order
import textfit
import title_footer
from build_ps2_dialogue import copy_bytes, directory_position
from build_ps2_font import SOURCE_SHA256, digest_file, digest_iso_file, files, patch_udf, write_udf_record
from fix_ps2_library import rebuild as rebuild_database, sentences, file_offset
from ps2_database_port import indices
from ps2_narration_port import wrap_native
from ps2_translation_native import extend
from static2_extract import sections, index
from port_ps2_translations import campaign_sources, story_mappings
from port_ps2_prologue import SCENES as PROLOGUE_SCENES
from port_ps2_stage30 import SCENES as EXTRA_SCENES

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rebuild_slots(raw, replacements):
    count, table = struct.unpack_from('<2I', raw, 8)
    if not count:
        assert not replacements
        return raw
    pointers = struct.unpack_from(f'<{count}I', raw, table)
    first = min(pointers)
    header, payload, new = bytearray(raw[:first]), bytearray(), []
    for slot, pointer in enumerate(pointers):
        before = raw[pointer:raw.index(0, pointer)]
        new.append(first + len(payload))
        payload += replacements.get(slot, before) + b'\0'
    struct.pack_into(f'<{count}I', header, table, *new)
    result = bytes(header + payload)
    result += bytes(-len(result) % 2048)
    assert len(result) <= build_patch.HARD_MAX_BLOCK
    return result


def refresh_story(elf, maps, meta, info):
    mappings, _, _, sources = story_mappings()
    layout_path=ROOT/'work/translation/en/ps2/script/reviewed_layout.en.json'
    layout_rows=read(layout_path)['rows']
    layouts={(row['scene'],row['slot']):row for row in layout_rows}
    applied_layouts=[]
    psp_trans = build_patch.load_translations([str(path) for path in sources])
    originals = {r['name']: r['strings'] for r in read(ROOT/'work/source/ps2/script_comparison.json')['ps2_blocks']}
    original_psp = (ROOT/'work/build/MAP_ADD.orig').read_bytes()
    for row in read(ROOT/'work/source/stage_map.json'):
        if row['name'] in set(PROLOGUE_SCENES) | set(EXTRA_SCENES):
            originals[row['name']] = play_order.load(original_psp, row['offset'])[1]
    segment, va = int(meta['segment_offset'], 16), int(meta['segment_va'], 16)
    offset = lambda address: segment + int(address, 16) - va
    table = offset(info['script_sector_table_va'])
    names_table = offset(info['script_name_table_va'])
    old_sectors = struct.unpack_from('<204I', elf, table)
    names = []
    for pointer in struct.unpack_from('<203I', elf, names_table):
        at = segment + pointer - va
        names.append(elf[at:elf.index(0, at)].decode('ascii'))
    sectors = list(struct.unpack_from('<18I', elf, 0x37e438))
    start = sectors[10] * 2048
    output = bytearray(maps[:start])
    new_sectors, blocks, records = [], [], []
    changed = 0
    # Measure native Latin advances once; native punctuation takes a 24px cell.
    glyphs = {int(g['sjis'], 16): g['width'] for g in meta['glyphs']}
    def width(line):
        total = 0
        for token in textfit.tokens(line):
            if isinstance(token, tuple):
                total += glyphs.get(token[1], 24)
            elif token in textfit.PLACEHOLDER_PX:
                total += 144 if token in ('#男愛称', '#女愛称') else textfit.PLACEHOLDER_PX[token]*24//16
            else:
                # Untranslated native symbols use the ordinary fullwidth cell.
                total += glyphs.get(it.textfit.ASCII.get(token), 24)
        return total
    reflows = []
    overflow = []
    def fit(target, name, slot):
        if max(width(line) for line in target.split('@')) <= 528:
            return target
        flattened = ' '.join(target.replace('@', ' ').split())
        opening = next((i for i,c in enumerate(flattened) if c in '\u300c\uff08'), None)
        if opening is None:
            # Plain options/objectives retain their authored segment boundaries.
            raise AssertionError(('PS2 plain line too wide', name, slot, flattened))
        suffix = flattened[-1] if flattened[-1] in '\u300d\uff09' else ''
        prefix = flattened[:opening+1]
        body = flattened[opening+1:len(flattened)-len(suffix) if suffix else None]
        lines=[]; line=prefix; words=body.split(); first_word=True
        for n,word in enumerate(words):
            candidate=line+('' if first_word else ' ')+word
            reserve=suffix if n==len(words)-1 else ''
            if width(candidate+reserve)>528:
                lines.append(line)
                line='\u3000'+word
            else:
                line=candidate
            first_word=False
        lines.append(line+suffix)
        if len(lines)>3 or max(width(line) for line in lines)>528:
            overflow.append(dict(scene=name, slot=slot, english=flattened, lines=lines))
            return target
        assert ' '.join(' '.join(lines).split()) == flattened
        reflows.append(dict(scene=name, slot=slot, native_widths=[width(line) for line in lines]))
        return '@'.join(lines)
    for n, name in enumerate(names):
        raw = maps[start+old_sectors[n]*2048:start+old_sectors[n+1]*2048]
        commands, before_strings = play_order.load(raw, 0)
        original_strings = originals[name]
        assert len(original_strings) == len(before_strings), name
        trans = psp_trans.get(name, {}) if name in set(PROLOGUE_SCENES)|set(EXTRA_SCENES) else mappings[name]
        replacements = {}
        for slot, jp in enumerate(original_strings):
            if export_rows.classify(jp) is None:
                continue
            assert jp in trans, (name, slot, 'readable translation missing')
            rendered = trans[jp]
            if (name,slot) in layouts:
                row=layouts[name,slot]
                assert sha(jp.encode('cp932'))==row['source_sha256']
                assert ' '.join(rendered.replace('@',' ').split())==row['expected_english']
                rendered=row['english'];applied_layouts.append(row)
            # Existing shipped layouts retain their original behavior. Check
            # newly changed text without expanding the scope to old layouts.
            same_words=lambda value:' '.join(unicodedata.normalize('NFKC',value).replace('@',' ').replace('’',"'").split())
            if same_words(rendered)==same_words(before_strings[slot]):
                rendered=before_strings[slot]
            elif textfit.encode(rendered) != before_strings[slot].encode('cp932'):
                rendered = fit(rendered, name, slot)
            encoded = textfit.encode(rendered)
            replacements[slot] = encoded
            changed += encoded != before_strings[slot].encode('cp932')
            records.append(dict(scene=name, slot=slot, source_sha256=sha(jp.encode('cp932')), english=rendered))
        block = rebuild_slots(raw, replacements)
        new_commands, new_strings = play_order.load(block, 0)
        assert commands == new_commands and len(before_strings) == len(new_strings), name
        for slot, before in enumerate(before_strings):
            assert new_strings[slot].encode('cp932') == replacements.get(slot, before.encode('cp932'))
        new_sectors.append((len(output)-start)//2048)
        output += block
        blocks.append(dict(scene=name, index=n, commands=len(commands), new_bytes=len(block),
                           new_sha256=sha(block), commands_sha256=sha(block[32:32+48*len(commands)]),
                           translated_strings=len(replacements), relative_sector=new_sectors[-1]))
    if overflow:
        save(ROOT/'work/output/ps2_review_wrap_overflows.json', overflow)
        raise AssertionError(('PS2 dialogue wrapping needs review', len(overflow)))
    assert len(applied_layouts)==len(layouts)
    new_sectors.append((len(output)-start)//2048)
    output += maps[start+old_sectors[-1]*2048:]
    assert len(names)==203 and len(new_sectors)==204
    delta = new_sectors[-1]-old_sectors[-1]
    for n in range(11,18): sectors[n] += delta
    assert len(output)==sectors[-1]*2048
    struct.pack_into('<18I', elf, 0x37e438, *sectors)
    struct.pack_into('<193I', elf, 0x381f40, *new_sectors[:193])
    struct.pack_into('<204I', elf, table, *new_sectors)
    for scene in info['scenes']:
        block=blocks[scene['index']]
        scene.update(bytes=block['new_bytes'], target_sha256=block['new_sha256'],
                     translated_strings=block['translated_strings'])
    return bytes(elf), bytes(output), dict(blocks=blocks, texts=records, changed_string_slots=changed,
        total_scenes=203, translated_scenes=sum(bool(b['translated_strings']) for b in blocks),
        translated_strings=len(records), missing_readable_strings=0, commands_preserved_from_verified_port=True,
        non_script_map_bytes_preserved=True, native_linebreak_reflows=reflows,
        native_layout_wording=applied_layouts,layout_inputs={str(layout_path.relative_to(ROOT)):digest_file(layout_path)},
        inputs={str(p.relative_to(ROOT)).replace('\\','/'):digest_file(p) for p in sources})


def refresh_library(elf, fix, meta, base, previous):
    library = read(ROOT/Path(previous['library_corrections_manifest']))
    library['description_rows'] = copy.deepcopy(library['description_rows'])
    rows, pointers = sentences(fix, elf)
    sec = sections(fix, 0)
    tags = ('Xunt','XPlt','XSpr','XSkl','Xabl','XPrt','XHlp')
    tables = {tag:index(fix, sec[tag][0], sec[tag][2]) for tag in tags}
    english = read(ROOT/'work/translation/en/library.json')
    targets = {(tag,int(entry)):row['en'] for group,tag in [('units','Xunt'),('pilots','XPlt')]
               for entry,row in english[group].items()}
    assert len(targets)==512, ('Library schema changed', len(targets))
    edited = [item for item in library['description_rows']
              if it.clean(targets[item['table'],item['entry']]) != it.clean(item['english'])]
    assert len(edited) <= 512, len(edited)
    old_ids={ident for item in edited for ident in tables[item['table']][item['entry']]}
    protected={ident for tag in tags for n, ids in enumerate(tables[tag])
               if (tag,n) not in {(item['table'],item['entry']) for item in edited} for ident in ids}
    for ident in old_ids-protected:
        rows[ident]=b'\0'; pointers[ident]=0
    external={ident:pointer for ident,pointer in enumerate(pointers) if pointer&0x80000000}
    for item in edited:
        en=it.clean(targets[item['table'],item['entry']]); lines=[]
        for para in en.split('\n'): lines += wrap_native(para,meta) if para.strip() else ['']
        ids=[]
        for line in lines:
            elf, address=extend(elf,meta,it.encode(line),alignment=4)
            ids.append(len(rows)); external[len(rows)]=0x80000000|address; rows.append(b'\0')
        tables[item['table']][item['entry']]=ids
        item.update(english=en, lines=lines, sentence_ids=ids)
    assert len(rows)<32768
    head=12+4*len(rows); payload=bytearray(); offsets=[]; cache={}
    for ident,row in enumerate(rows):
        if ident in external: offsets.append(external[ident]); continue
        if row not in cache: cache[row]=head+len(payload); payload+=row
        offsets.append(cache[row])
    sent=b'Sent'+struct.pack('<2I',head+len(payload),len(rows))+struct.pack(f'<{len(rows)}I',*offsets)+payload
    replacements={'Sent':sent, **{tag:indices(tag,tables[tag]) for tag in ('Xunt','XPlt')}}
    updated=rebuild_database(fix,replacements)
    assert len(updated)<=len(fix), ('Fixed database heap budget',len(updated),len(fix))
    # Preserve gameplay records and every non-library category.
    current=sections(updated,0)
    for tag,(off,size,_) in sec.items():
        if tag not in {'Sent','Fixh','Xunt','XPlt'}:
            a,b,_=current[tag]; assert updated[a:a+b]==fix[off:off+size],tag
    save(base/'library.json',library)
    save(base/'ui_details.json',previous['ui_detail_corrections'])
    save(base/'battle_labels.json',previous['battle_label_corrections'])
    return bytes(elf),updated,dict(changed_entries=len(edited),numeric_gameplay_records_preserved=True,
        edited=[dict(table=r['table'],entry=r['entry']) for r in edited],released_sentence_ids=sorted(old_ids-protected),
        old_bytes=len(fix),new_bytes=len(updated),signed_row_ids_verified=True)


def refresh_evidence(base,old_elf,old_fix,meta,footer,info,library,previous):
    prior=base/'baseline';prior.mkdir(exist_ok=True)
    (prior/'SLPS_253.45').write_bytes(old_elf);(prior/'FIX00.DAT').write_bytes(old_fix)
    segment=int(meta['segment_offset'],16);va=int(meta['segment_va'],16)
    table=segment+int(info['script_sector_table_va'],16)-va
    ranges=[[164,172],[0x100180-0xff000,0x100184-0xff000],[0x100188-0xff000,0x10018c-0xff000],
            [0x37e438,0x37e438+18*4],[0x381f40,0x381f40+193*4],[table,table+204*4],*footer['byte_ranges']]
    save(base/'library_refresh.json',dict(baseline_directory=str(prior.relative_to(ROOT)),
        historical_reflow_directory=previous.get('library_preservation_reference',str(Path(previous['library_corrections_manifest']).parent)),
        source_elf_sha256=sha(old_elf),source_fix_sha256=sha(old_fix),
        target_elf_sha256=sha((base/'SLPS_253.45').read_bytes()),target_fix_sha256=sha((base/'FIX00.DAT').read_bytes()),
        released_sentence_ids=library['released_sentence_ids'],changed_entries=library['edited'],elf_ranges=ranges))


def build(version, source_version, resume_prepared=False):
    import battle_quotes
    battle_quotes.require_complete_translations()
    base=ROOT/f'work/build/ps2/reviewed_{version}'
    output=ROOT/f'work/output/SRWMX_PS2_EN_{version}.iso'
    assert not output.exists() and (resume_prepared or not base.exists() or not any(base.iterdir())), 'Preserve existing builds'
    base.mkdir(parents=True, exist_ok=True)
    previous=read(ROOT/f'work/output/ps2_font_{source_version}_verification.json')
    source=ROOT/previous['output']; original=ROOT/'Super Robot Taisen MX (Japan).iso'
    source_stats={p:(p.stat().st_size,p.stat().st_mtime_ns) for p in (source,original)}
    print('Verifying complete baseline and Japanese source image hashes',flush=True)
    hash_cache_path=base/'source_hashes.json'
    hash_cache=read(hash_cache_path) if hash_cache_path.exists() else {}
    for path,expected in [(source,previous['target_sha256']),(original,SOURCE_SHA256)]:
        cached=hash_cache.get(str(path))
        if cached!=dict(sha256=expected,bytes=source_stats[path][0],mtime_ns=source_stats[path][1]):
            assert digest_file(path)==expected
            hash_cache[str(path)]=dict(sha256=expected,bytes=source_stats[path][0],mtime_ns=source_stats[path][1])
            save(hash_cache_path,hash_cache)
    old=pycdlib.PyCdlib(); old.open(str(source))
    def asset(name):
        path='/SLPS_253.45;1' if name=='SLPS_253.45' else '/DATA/'+name+';1'
        with old.open_file_from_iso(iso_path=path) as stream:return stream.read()
    if resume_prepared:
        checkpoint=read(base/'prepared.json')
        assert all(digest_file(base/name)==h for name,h in checkpoint['files'].items()), 'Prepared assets changed'
        assert all(digest_file(ROOT/name)==h for name,h in checkpoint['inputs'].items()), 'Prepared source text changed'
        elf=(base/'SLPS_253.45').read_bytes();maps=(base/'MAP.BIN').read_bytes();fix=(base/'FIX00.DAT').read_bytes()
        meta=read(base/'patch.json');info=read(base/'stage30.json');story=read(base/'campaign_review.json')
        assert sha(elf)==meta['target_sha256'];library=checkpoint['library'];count=checkpoint['inline_copies']
        external_count=checkpoint['external_copies'];before_uses=[None]*checkpoint['quote_references']
        from ps2_title_footer import patch as patch_title
        same,footer,same_meta=patch_title(elf,version,meta);assert same==elf and same_meta==meta
    else:
        elf=bytearray(asset('SLPS_253.45')); meta=copy.deepcopy(previous['font'])
        assert sha(elf)==meta['target_sha256']
        info=copy.deepcopy(previous['stage30']); info['version']=version
        elf,maps,story=refresh_story(elf,asset('MAP.BIN'),meta,info)
        print('Story refreshed:',story['changed_string_slots'],'changed slots;',len(story['native_linebreak_reflows']),'native linebreak reflows',flush=True)
        elf,fix,library=refresh_library(elf,asset('FIX00.DAT'),meta,base,previous)
        battle_path=base/'BATTLE.BIN'
        with old.open_file_from_iso(iso_path='/DATA/BATTLE.BIN;1') as stream,battle_path.open('wb') as dst:
            copy_bytes(stream,dst,old.get_record(iso_path='/DATA/BATTLE.BIN;1').data_length)
        static=asset('STATIC.BIN')
        from refresh_ps2_battle import refresh as refresh_battle
        battle_review=refresh_battle(battle_path,static,elf)
        save(base/'battle_review.json',battle_review)
        count=battle_review['stored_allocations_updated'];external_count=0
        before_uses=battle_review['changed_references']
        from ps2_title_footer import patch as patch_title
        elf,footer,meta=patch_title(elf,version,meta)
        meta['target_sha256']=sha(elf)
        for name,data in [('SLPS_253.45',elf),('MAP.BIN',maps),('FIX00.DAT',fix),
                          ('STAGE.BIN',asset('STAGE.BIN')),('STATIC.BIN',asset('STATIC.BIN')),
                          ('PACKMAPC.BIN',asset('PACKMAPC.BIN'))]: (base/name).write_bytes(data)
        save(base/'patch.json',meta);save(base/'stage30.json',info)
        save(base/'prologue.json',previous['prologue']);save(base/'difficulty.json',previous['difficulty'])
        save(base/'campaign_review.json',story)
        refresh_evidence(base,asset('SLPS_253.45'),asset('FIX00.DAT'),meta,footer,info,library,previous)
        save(base/'prepared.json',dict(files={p.name:digest_file(p) for p in base.iterdir() if p.is_file()},inputs={**story['inputs'],**story['layout_inputs']},library=library,inline_copies=count,external_copies=external_count,quote_references=len(before_uses)))
    from verify_ps2_stage30 import verify
    execution=verify(base,version)
    prologue=read(base/'prologue.json');prologue['version']=version
    current_blocks={r['scene']:r for r in story['blocks']}
    for row in prologue['new_scene_blocks']:
        block=current_blocks[row['scene']]
        row.update(bytes=block['new_bytes'],target_sha256=block['new_sha256'],translated_strings=block['translated_strings'])
    save(base/'prologue.json',prologue)
    checkpoint=read(base/'prepared.json');checkpoint['files']['prologue.json']=digest_file(base/'prologue.json');save(base/'prepared.json',checkpoint)
    # Repack from the original disc, reusing every other verified English asset.
    replacements={row['path']:None for row in previous['files'] if row['original_sha256']!=row['target_sha256']}
    for name in ('SLPS_253.45','MAP.BIN','FIX00.DAT','BATTLE.BIN'):
        replacements['/SLPS_253.45;1' if name=='SLPS_253.45' else '/DATA/'+name+';1']=base/name
    records={row['path']:row for row in previous['files']}
    sizes={p:local.stat().st_size if local else records[p]['bytes'] for p,local in replacements.items()}
    hashes={p:digest_file(local) if local else records[p]['target_sha256'] for p,local in replacements.items()}
    iso=pycdlib.PyCdlib();iso.open(str(original))
    append={p for p,n in sizes.items() if n>iso.get_record(iso_path=p).data_length}
    projected=original.stat().st_size+sum((sizes[p]+2047)//2048*2048 for p in append)+2048
    assert projected<=4700372992, 'Single-layer DVD capacity'
    positions={p:directory_position(iso,original,p) for p in replacements}
    udf_names={str(name).lower():str(name) for _,_,names in iso.walk(udf_path='/data') for name in names}
    udf={p:('/SLPS_253.45' if p=='/SLPS_253.45;1' else '/data/'+udf_names[p.rsplit('/',1)[-1].split(';')[0].lower()]) for p in replacements}
    shutil.copyfile(original,output);locations={}
    with output.open('r+b') as dst:
        for p,local in replacements.items():
            if p in append:dst.seek(0,2)
            else:dst.seek(iso.get_record(iso_path=p).extent_location()*2048)
            locations[p]=dst.tell()//2048
            if local:
                with local.open('rb') as stream:copy_bytes(stream,dst,sizes[p])
            else:
                with old.open_file_from_iso(iso_path=p) as stream:copy_bytes(stream,dst,sizes[p])
            dst.write(bytes(-sizes[p]%2048))
        dst.seek(0,2);last=dst.tell()//2048;dst.write(bytes(2048));total=last+1
        assert total*2048==projected
        for p in replacements:
            dst.seek(positions[p]+2);dst.write(struct.pack('<I',locations[p])+struct.pack('>I',locations[p]))
            dst.seek(positions[p]+10);dst.write(struct.pack('<I',sizes[p])+struct.pack('>I',sizes[p]))
        descriptor=16
        while True:
            dst.seek(descriptor*2048);header=dst.read(7);assert header[1:6]==b'CD001'
            if header[0]==255:break
            if header[0] in (1,2):
                dst.seek(descriptor*2048+80);dst.write(struct.pack('<I',total)+struct.pack('>I',total))
            descriptor+=1
        patch_udf(iso,dst,locations['/SLPS_253.45;1'],sizes['/SLPS_253.45;1'],last)
        partition=iso.udf_main_descs.partitions[0].part_start_location
        for p in replacements:
            if p=='/SLPS_253.45;1':continue
            entry=iso.get_record(udf_path=udf[p]);assert len(entry.alloc_descs)==1
            entry.set_data_length(sizes[p]);entry.set_data_location(locations[p],locations[p]-partition)
            entry.log_block_recorded=(sizes[p]+2047)//2048;write_udf_record(dst,entry)
    checked=pycdlib.PyCdlib();checked.open(str(output));checks=[]
    for p in sorted(files(iso)):
        record=checked.get_record(iso_path=p);actual=digest_iso_file(checked,p)
        assert actual==hashes.get(p,records[p]['target_sha256']),p
        checks.append(dict(path=p,changed=p in replacements,original_sha256=records[p]['original_sha256'],
            target_sha256=actual,original_sector=records[p]['original_sector'],
            target_sector=record.extent_location(),bytes=record.data_length))
    for p in replacements:
        with checked.open_file_from_iso(udf_path=udf[p]) as stream:
            digest=hashlib.sha256()
            for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
            assert digest.hexdigest()==hashes[p],p
    with checked.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as stream:
        script_start=struct.unpack_from('<18I',elf,0x37e438)[10]*2048
        for block in story['blocks']:
            stream.seek(script_start+block['relative_sector']*2048)
            assert sha(stream.read(block['new_bytes']))==block['new_sha256']
    checked.close();iso.close();old.close()
    assert all((p.stat().st_size,p.stat().st_mtime_ns)==stat for p,stat in source_stats.items()), 'Source images changed during build'
    assert all(digest_file(ROOT/p)==h for p,h in {**story['inputs'],**story['layout_inputs']}.items()), 'Story inputs changed'
    report=copy.deepcopy(previous)
    report.update(version=version,source_build_version=source_version,source_build_sha256=previous['target_sha256'],
        output=str(output.relative_to(ROOT)),bytes=projected,target_sha256=digest_file(output),font=meta,files=checks,
        stage30=info,prologue=prologue,stage30_execution_checks=execution,blocks=story['blocks'],translated_strings=story['translated_strings'],
        library_corrections_manifest=str((base/'library.json').relative_to(ROOT)),
        library_preservation_reference=read(base/'library_refresh.json')['historical_reflow_directory'],
        translated_scenes=story['translated_scenes'],campaign_proofreading_included=True,campaign_review=story,
        library_source_followup=library,battle_screenshot_copies_updated=count+external_count,
        battle_quote_inline_copies=count,battle_quote_external_copies=external_count,pcsx2_fresh_boot_verified=False,
        battle_quote_native_references_updated=len(before_uses),
        compact_disc_rebuilt_from_original=True,all_preserved_resources_rehashed=True,
        pcsx2_visual_validation='pending for this version',github_release=False,
        source_unchanged=True,source_build_unchanged=True,iso9660_and_udf_all_replacements_agree=True,
        original_allocations_reused=sorted(set(replacements)-append),appended_resources=sorted(append),
        native_translation_hook_checks=execution['translations'],mips_checks=execution['font'])
    for key in ('ui_visual_validation','visual_checks','visual_evidence','visual_blocker','library_runtime_checks'):
        report.pop(key,None)
    report['title_footer']=footer
    report['title_footer']['readback']=title_footer.verify_iso(output,'PS2',version)
    save(ROOT/f'work/output/ps2_font_{version}_verification.json',report)
    save(ROOT/f'work/output/ps2_title_footer_{version}_verification.json',dict(version=version,footer=report['title_footer']))
    evidence=ROOT/f'work/build/ps2/font_{version}';evidence.mkdir()
    shutil.copyfile(base/'SLPS_253.45',evidence/'SLPS_253.45');save(evidence/'patch.json',meta)
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',output.with_name(output.stem+'_FONT_LICENSE.txt'))
    print('Verified PS2',version,report['target_sha256'],'all 37 files and both directory views',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version');parser.add_argument('--source-version',default='0.4.30')
    parser.add_argument('--resume-prepared',action='store_true')
    args=parser.parse_args();build(args.version,args.source_version,args.resume_prepared)
