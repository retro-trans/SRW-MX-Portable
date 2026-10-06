"""Source-based PSP to PS2 translation transfer; preserve PS2 commands and IDs.

Japanese source text stays in ignored work/source; distributable manifests use
source hashes and English. Similarity is never used to select a translation.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct

import build_patch
import export_rows
import play_order
from build_ps2_dialogue import (ROOT, TABLE, SECTIONS, NAMES, COUNT,
                               SCRIPT_BASE, SCRIPT_SECTION, copy_bytes)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def normalize(text):
    return re.sub(r'[@\s\u3000]', '', text)


def campaign_sources():
    manifest=read_json(ROOT/'work/output/campaign_0.4.9_inputs.json')
    paths=[ROOT/p for p in manifest['source_files']]
    assert len(paths)==59
    for path in paths:
        data=read_json(path)
        assert not data.get('stage_context_review_pending',False),path
        assert all(r.get('en') for r in data['rows']),path
    return paths


def story_mappings():
    sources=campaign_sources()
    scenes=build_patch.load_translations([str(p) for p in sources])
    global_text=defaultdict(set);normalized=defaultdict(set)
    for mapping in scenes.values():
        for jp,en in mapping.items():
            global_text[jp].add(en);normalized[normalize(jp)].add(en)
    variants={r['source_sha256']:r['english'] for r in read_json(
        ROOT/'work/translation/en/ps2/script/campaign_ps2_variants.en.json')['rows']}
    scoped=read_json(ROOT/'work/translation/en/ps2/script/stage1_ps2_differences.en.json')['rows']
    overrides={}
    for row in scoped:
        opening,closing=('（','）') if row['kind']=='thought' else ('「','」')
        lines,ok=build_patch.textfit.wrap(row['speaker_en']+opening,row['en'],closing)
        assert ok
        for use in row['uses']:overrides[use]=(row['source_sha256'],'@'.join(lines))
    mappings={};manifest=[];missing=[];counts=defaultdict(int)
    blocks=read_json(ROOT/'work/source/ps2/script_comparison.json')['ps2_blocks']
    for block in blocks:
        name=block['name'];mapping={}
        for slot,jp in enumerate(block['strings']):
            key=sha(jp.encode('cp932'));use=name+':'+str(slot)
            if use in overrides:
                expected,en=overrides[use];assert expected==key;method='reviewed_stage1'
            elif jp in scenes.get(name,{}):en=scenes[name][jp];method='same_scene_exact'
            elif key in variants:en=variants[key];method='translated_ps2_variant'
            elif len(global_text[jp])==1:en=next(iter(global_text[jp]));method='cross_scene_exact'
            elif len(normalized[normalize(jp)])==1:
                en=next(iter(normalized[normalize(jp)]));method='linebreak_only_difference'
            elif use=='i056a:209':
                # Amuro asks where to assign Hugo/Aqua, immediately before a choice.
                en="Bright「Let's see...」";method='reviewed_context'
            else:
                if export_rows.classify(jp):missing.append(dict(scene=name,slot=slot,source_sha256=key))
                continue
            mapping[jp]=en;counts[method]+=1
            manifest.append(dict(scene=name,slot=slot,source_sha256=key,english=en,method=method))
        mappings[name]=mapping
    assert not missing,missing[:20]
    return mappings,manifest,dict(counts),sources


def rebuild_map(iso,original,destination):
    mappings,texts,methods,sources=story_mappings()
    relative=struct.unpack_from('<193I',original,TABLE)
    section=list(struct.unpack_from('<18I',original,SECTIONS))
    record=iso.get_record(iso_path='/DATA/MAP.BIN;1')
    new_relative=[];blocks=[]
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with iso.open_file_from_iso(iso_path='/DATA/MAP.BIN;1') as source,destination.open('wb') as output:
        copy_bytes(source,output,SCRIPT_BASE)
        for i in range(COUNT):
            pointer=struct.unpack_from('<I',original,NAMES+i*4)[0]-0xff000
            name=original[pointer:original.index(b'\0',pointer)].decode('ascii')
            raw=source.read((relative[i+1]-relative[i])*2048)
            commands,strings=play_order.load(raw,0)
            changed,n=build_patch.rebuild_block(raw,mappings[name])
            new_commands,new_strings=play_order.load(changed,0)
            assert commands==new_commands
            assert raw[32:32+48*len(commands)]==changed[32:32+48*len(commands)]
            assert len(strings)==len(new_strings)
            for slot,(jp,en) in enumerate(zip(strings,new_strings)):
                target=mappings[name].get(jp)
                assert en==(build_patch.textfit.encode(target).decode('cp932') if target else jp),(name,slot)
                assert target or export_rows.classify(jp) is None,(name,slot)
            new_relative.append((output.tell()-SCRIPT_BASE)//2048)
            output.write(changed)
            blocks.append(dict(scene=name,index=i,commands=len(commands),original_bytes=len(raw),
                               new_bytes=len(changed),translated_strings=n,
                               commands_sha256=sha(raw[32:32+48*len(commands)]),new_sha256=sha(changed)))
        new_relative.append((output.tell()-SCRIPT_BASE)//2048)
        assert source.tell()==SCRIPT_BASE+relative[-1]*2048
        copy_bytes(source,output,record.data_length-source.tell())
    delta=new_relative[-1]-relative[-1]
    for i in range(SCRIPT_SECTION+1,18):section[i]+=delta
    assert section[-1]*2048==destination.stat().st_size
    report=dict(scope='All readable original PS2 SRWL scenes',total_scenes=COUNT,
                translated_scenes=sum(bool(b['translated_strings']) for b in blocks),
                translated_strings=sum(b['translated_strings'] for b in blocks),
                original_commands_preserved=True,missing_readable_strings=0,methods=methods,
                largest_original=max(b['original_bytes'] for b in blocks),
                largest_english=max(b['new_bytes'] for b in blocks),blocks=blocks,
                inputs={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for p in sources},
                relative_sectors=new_relative,section_sectors=section,texts=texts)
    return report


if __name__=='__main__':
    import pycdlib
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare-story',action='store_true')
    a=p.parse_args()
    if a.prepare_story:
        iso=pycdlib.PyCdlib();iso.open(str(ROOT/'Super Robot Taisen MX (Japan).iso'))
        original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
        report=rebuild_map(iso,original,ROOT/'work/build/ps2/campaign/MAP.BIN');iso.close()
        (ROOT/'work/translation/en/ps2/script/campaign_port.en.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('blocks','texts','inputs','relative_sectors','section_sectors')},indent=2))
