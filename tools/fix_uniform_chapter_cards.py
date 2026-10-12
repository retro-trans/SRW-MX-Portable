"""Redraw and audit every chapter card in local PSP/PS2 incremental builds."""
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

import pycdlib
from PIL import Image, ImageDraw
import patch_chapter_cards as cards
from ps2_graphics_port import logical_palette
from build_title_footer import stamp_existing
from title_footer import verify_iso
import strip_jp

ROOT=Path(__file__).resolve().parents[1]
VERSION,BASE='0.4.30','0.4.29'
MANIFEST=ROOT/f'work/translation/en/ui/uniform_chapter_cards_{VERSION}.en.json'

def read(path):return json.loads(path.read_text(encoding='utf8'))
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
def sha(data):return hashlib.sha256(data).hexdigest()

def inputs():
    if MANIFEST.exists():return
    path=ROOT/'work/translation/en/ui/all_chapter_cards.json';spec=read(path)
    mapping=ROOT/'work/source/ps2/chapter_mapping.json';ps2=read(mapping)
    rows={'PSP':[],'PS2':[]}
    for row in spec['cards']:
        before=row['en'];row['en']={'Strange bait':'Strange Bait'}.get(before,before)
        rows['PSP'].append(dict(strip_jp.clean(row),previous_en=before))
        row.update(needs_translation=True,lettering_policy='uniform',
                   layout_note='0.4.30: redraw all chapter titles, including native English artwork.')
    titles={r['id']:r['en'] for r in spec['cards']}
    for row in ps2['matched']:
        before=row['english'];row['english']=titles[row['psp_id']]
        rows['PS2'].append(dict(strip_jp.clean(row),previous_en=before))
        row.update(needs_translation=True,lettering_policy='uniform')
    save(path,spec);save(path.with_name(path.stem+'.en.json'),strip_jp.clean(spec))
    save(mapping,ps2)
    save(MANIFEST,dict(version=VERSION,base_version=BASE,
        reason='Remove language-based chapter-art exemptions and audit every story/gallery copy.',rows=rows))

def picture(pixels,palette):
    im=Image.frombytes('P',(256,52),pixels)
    im.putpalette(bytes(c for i in range(256) for c in palette[i*4:i*4+3]))
    return im.convert('RGB')

def patch_archive(data,platform,rows,ui):
    output=bytearray(data);results=[];changed=[];masks={};previews={}
    for row in rows:
        off=row['pixel_offset'];title=row.get('en',row.get('english'));previous=row['previous_en']
        palette=data[off-1024:off];old=data[off:off+256*52]
        if 'palette_sha256' in row:assert sha(palette)==row['palette_sha256']
        lp=palette if platform=='PSP' else logical_palette(palette)
        for text in (title,previous):
            if text not in masks:masks[text]=cards.render_title(text)
        mask,layout=masks[title];expected=cards.indexed_title(mask,lp)
        old_render=cards.indexed_title(masks[previous][0],lp)
        native=row.get('accepted_title_sha256',[row.get('title_sha256')])
        assert old in (expected,old_render) or sha(old) in native,(platform,off,title,'unrecognized artwork')
        output[off:off+len(expected)]=expected
        assert output[off-1024:off]==palette
        assert output[off+256*52:off+256*256]==data[off+256*52:off+256*256]
        differs=old!=expected
        if differs:
            changed.append((off,off+len(expected)))
            if title not in previews:
                previews[title]=(picture(old,lp),picture(expected,lp))
                if title=='Strange Bait':
                    previews[title][0].save(ui/'chapter20_before.png')
                    previews[title][1].save(ui/'chapter20_after.png')
        results.append(dict(id=row.get('id',row.get('psp_id','additional_card')),pixel_offset=off,
            en=title,changed=differs,uniform_renderer_match=True,palette_preserved=True,
            title_sha256=sha(expected),**layout))
    last=0
    for a,z in sorted(changed):assert output[last:a]==data[last:a];last=z
    assert output[last:]==data[last:] and len(output)==len(data)
    # Every copy must agree, including PS2's permuted palette-index encoding.
    for title in {r['en'] for r in results}:
        copies=[r for r in results if r['en']==title]
        assert len({r['title_sha256'] for r in copies})==1,title
    sheet=Image.new('RGB',(540,max(1,len(previews))*86),(24,24,28));draw=ImageDraw.Draw(sheet)
    for i,(title,(before,after)) in enumerate(previews.items()):
        y=i*86;draw.text((8,y+5),title,fill='white')
        sheet.paste(before,(8,y+27));sheet.paste(after,(276,y+27))
    sheet.save(ui/'remaining_titles_before_after.png')
    return bytes(output),results,changed

def compare_discs(source,target,allowed):
    left_hash,right_hash=hashlib.sha256(),hashlib.sha256()
    with source.open('rb') as left,target.open('rb') as right:
        cursor=0
        for start,end in sorted(allowed)+[(source.stat().st_size,source.stat().st_size)]:
            assert cursor<=start<=end
            for length,equal in [(start-cursor,True),(end-start,False)]:
                while length:
                    take=min(length,8*1024*1024);a=left.read(take);b=right.read(take)
                    assert len(a)==len(b)==take
                    if equal:assert a==b,'Undeclared disc change'
                    left_hash.update(a);right_hash.update(b);length-=take
            cursor=end
        assert not left.read(1) and not right.read(1)
    return left_hash.hexdigest(),right_hash.hexdigest()

def build(platform,verify_existing=False):
    inputs();prefix='SRWMX_EN_' if platform=='PSP' else 'SRWMX_PS2_EN_'
    source=ROOT/f'work/output/{prefix}{BASE}.iso';target=source.with_name(prefix+VERSION+'.iso')
    assert source.exists() and (target.exists() if verify_existing else not target.exists()),'Preserve existing versioned builds'
    rows=copy.deepcopy(read(MANIFEST)['rows'][platform])
    if platform=='PS2':
        graphics=read(ROOT/f'work/output/ps2_font_{BASE}_verification.json')['stage30']['graphics']
        for off in (0x2f20400,0x2f51c00,0x4261c00):
            rows.append(dict(pixel_offset=off,english=graphics['stage30_english'],previous_en=graphics['stage30_english']))
        for off in (0x2f20400,0x2f51c00):
            rows.append(dict(pixel_offset=graphics['animation_offset']+off-0x2ee0000,
                english=graphics['english'],previous_en=graphics['english']))
    assert len(rows)==(205 if platform=='PSP' else 200)
    ui=ROOT/f'work/ui/{platform.lower()}/chapter_cards_{VERSION}';ui.mkdir(parents=True,exist_ok=True)
    asset=cards.ASSET if platform=='PSP' else '/DATA/PACKMAPC.BIN;1'
    iso=pycdlib.PyCdlib();iso.open(str(source))
    with iso.open_file_from_iso(iso_path=asset) as f:data=f.read()
    updated,results,changed=patch_archive(data,platform,rows,ui)
    extent=iso.get_record(iso_path=asset).extent_location()*2048
    print(platform,'audited',len(results),'cards; redrawing',len(changed),'copies',flush=True)
    if verify_existing:
        footer=read(ROOT/f'work/output/{platform.lower()}_title_footer_{VERSION}_verification.json')['footer']
        assert verify_iso(target,platform,VERSION)==footer['readback']
    else:
        shutil.copyfile(source,target)
        with target.open('r+b') as f:
            for a,z in changed:f.seek(extent+a);f.write(updated[a:z])
        footer=stamp_existing(target,platform,VERSION)
    check=pycdlib.PyCdlib();check.open(str(target))
    with check.open_file_from_iso(iso_path=asset) as f:assert f.read()==updated
    for folder,_,files in iso.walk(iso_path='/'):
        for name in files:
            path=folder.rstrip('/')+'/'+str(name);a=iso.get_record(iso_path=path);b=check.get_record(iso_path=path)
            assert (a.extent_location(),a.data_length)==(b.extent_location(),b.data_length),path
    if platform=='PS2':
        matches=[folder.rstrip('/')+'/'+str(n) for folder,_,files in check.walk(udf_path='/')
                 for n in files if str(n).lower()=='packmapc.bin']
        assert len(matches)==1
        with check.open_file_from_iso(udf_path=matches[0]) as f:assert f.read()==updated
    iso.close();check.close()
    allowed=[(extent+a,extent+z) for a,z in changed]
    allowed.extend((footer['disc_extent']+a,footer['disc_extent']+z) for a,z in footer['pixel_ranges'])
    source_hash,target_hash=compare_discs(source,target,allowed)
    manifest=read(ROOT/f'work/output/release-v{BASE}/BUILD-MANIFEST.json')
    assert source_hash==next(r['target_sha256'] for r in manifest['patches'] if r['platform']==platform)
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    report=dict(version=VERSION,base_version=BASE,platform=platform,
        output=target.relative_to(ROOT).as_posix(),source_sha256=source_hash,output_sha256=target_hash,
        bytes=target.stat().st_size,asset=asset,archive_sha256=sha(updated),
        changed_copies=len(changed),changed_title_designs=len({r['en'] for r in results if r['changed']}),
        title_atlases_audited=len(results),distinct_titles_audited=len({r['en'] for r in results}),
        every_title_matches_uniform_renderer=True,all_duplicate_and_gallery_copies_agree=True,
        palettes_and_non_title_pixels_preserved=True,all_other_disc_bytes_preserved=True,
        file_positions_and_sizes_preserved=True,story_commands_and_text_unchanged=True,
        footer=footer,cards=results,local_build_only=True,github_release=False,
        in_game_chapter20_visual_validation='pending',later_campaign_proofreading_included=False)
    save(ROOT/f'work/output/{platform.lower()}_chapter_cards_{VERSION}_verification.json',report)
    if platform=='PS2':
        aggregate=read(ROOT/f'work/output/ps2_font_{BASE}_verification.json')
        for row in aggregate['files']:
            if row['path']==asset:row['target_sha256']=sha(updated)
            elif row['path']==footer['asset']:row['target_sha256']=footer['target_resource_sha256']
        aggregate['font']['target_sha256']=footer['target_resource_sha256']
        aggregate.update(version=VERSION,target_sha256=target_hash,output=report['output'],
            source_build_version=BASE,source_build_sha256=source_hash,title_footer=footer,
            changed_from_previous=[asset,footer['asset']],github_release=False,
            pcsx2_fresh_boot_verified=False,chapter_cards_uniform=report,
            current_correction_report=f'work/output/ps2_chapter_cards_{VERSION}_verification.json',
            inherited_execution_checks_from_version=BASE,
            inherited_execution_checks_reason='Chapter pixels and exact footer version only; all gameplay and script bytes preserved.')
        save(ROOT/f'work/output/ps2_font_{VERSION}_verification.json',aggregate)
        font=ROOT/f'work/build/ps2/font_{VERSION}';font.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/f'work/build/ps2/title_footer_{VERSION}/SLPS_253.45',font/'SLPS_253.45')
        save(font/'patch.json',aggregate['font'])
    print(platform,'verified',VERSION,target_hash,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--platform',choices=['PSP','PS2'])
    p.add_argument('--verify-existing',action='store_true',help='Read-only verification of an already constructed local candidate')
    p.add_argument('--inputs',action='store_true');args=p.parse_args()
    if args.inputs:inputs()
    else:
        for platform in ([args.platform] if args.platform else ['PSP','PS2']):build(platform,args.verify_existing)
