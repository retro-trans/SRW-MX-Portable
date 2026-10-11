"""Verify the Hau Dragon follow-up through the actual shared story loaders."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import build_patch
import campaign_dialogue_layout
import port_ps2_translations
import textfit
import insert_text
from ps2_narration_port import native_width

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(path.read_text(encoding='utf8'))


def main():
    script=ROOT/'work/translation/en/script'
    edits=[e for e in read(script/'screenshot_proofread_followups.en.json')['edits']
           if e.get('review_tag')=='hau_dragon_2026_10_11']
    assert len(edits)==54
    paths=sorted({script/('stage%02d_campaign_full_merged.json'%loc[0])
                  for e in edits for loc in e['appearances']})
    current={(int(p.name[5:7]),r['id']):r for p in paths for r in read(p)['rows']}
    scenes=build_patch.load_translations([str(p) for p in paths])
    mappings,manifest,methods,sources=port_ps2_translations.story_mappings()
    ps2_by_source=defaultdict(list)
    for scene,mapping in mappings.items():
        for jp,en in mapping.items():
            ps2_by_source[port_ps2_translations.normalize(jp)].append(en)
    font=read(ROOT/'work/build/ps2/font_0.4.23/patch.json')
    checks=[]
    for edit in edits:
        for loc in edit['appearances']:
            row=current[tuple(loc)]
            assert row['en']==edit['after'] and 'Tekkoryu' not in row['en']
            assert hashlib.sha256(row['jp'].encode('utf8')).hexdigest()==edit['source_sha256']
            opening,closing=('（','）') if row['kind']=='thought' else ('「','」')
            default,ok=textfit.wrap(row['speaker_en']+opening,row['en'],closing)
            lines=campaign_dialogue_layout.apply(row['speaker_en'],row['en'],row['kind'],default)
            flatten=lambda ls:' '.join(' '.join(ls).split())
            assert ok and flatten(lines)==flatten(default),loc
            if row['kind']=='thought':assert lines[0].startswith(row['speaker_en']+' （'),loc
            widths=[native_width(''.join(c for c in l.replace('　',' ') if c not in '「」（）'),font)
                    +24*sum(l.count(c) for c in '「」（）') for l in lines]
            assert len(lines)<=3 and max(map(textfit.px,lines))<=352 and max(widths)<=528,loc
            rendered='@'.join(lines)
            for use in row['uses']:assert scenes[use.split(':')[0]][row['jp']]==rendered,loc
            # The PS2 porter may map the same line in a differently named scene.
            normalized=port_ps2_translations.normalize(row['jp'])
            hits=ps2_by_source[normalized]
            assert all(en==rendered for en in hits),(loc,len(hits))
            checks.append(dict(chapter=loc[0],full_id=loc[1],ps2_matches=len(hits),
                psp_widths=list(map(textfit.px,lines)),ps2_widths=widths,words_preserved=True))
    report=dict(date='2026-10-11',scope='Hau Dragon source follow-up',iso_rebuilt=False,
        checked_occurrences=len(checks),checked_chapters=len(paths),
        ps2_matching_occurrences=sum(bool(c['ps2_matches']) for c in checks),
        psp_only_source_occurrences=[dict(chapter=c['chapter'],full_id=c['full_id'])
                                     for c in checks if not c['ps2_matches']],
        shared_loader_verified=True,ps2_story_mapping_verified=True,checks=checks)
    library=read(ROOT/'work/translation/en/library.json')
    library_edits=read(ROOT/'work/translation/en/ui/hau_dragon_library_followup.en.json')
    primary=next(f for f in library_edits['files'] if f['source'].endswith('/library.json'))
    library_checks=[]
    for change in primary['changes']:
        matches=[r for collection in library.values() for r in collection.values()
                 if r['entry']==change['entry'] and r['en']==change['after']
                 and hashlib.sha256(r['jp'].encode('utf8')).hexdigest()==change['source_sha256']]
        assert len(matches)==1 and change['after']==change['before'].replace('Tekkoryu','Hau Dragon')
        lines=insert_text.wrap(insert_text.clean(change['after']),496)
        assert len(lines)<=25 and max(map(textfit.px,lines))<=496
        library_checks.append(dict(entry=change['entry'],lines=len(lines),maximum_width=max(map(textfit.px,lines))))
    assert len(library_checks)==7
    report['library_checks']=library_checks
    output=ROOT/'work/output/hau_dragon_followup_validation.json'
    output.write_text(json.dumps(report,indent=1)+'\n',encoding='utf8')
    print('Both story loaders and font limits pass for %d occurrences across %d chapters.'%(len(checks),len(paths)))


if __name__=='__main__':main()
