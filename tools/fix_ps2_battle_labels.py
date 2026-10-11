"""Shorten the AI pilot name and correct native status icons; local PS2 build."""
import argparse,json,shutil,subprocess,sys,struct,unicodedata
from PIL import Image,ImageDraw
from port_ps2_translations import ROOT,sha,read_json
from port_ps2_prologue import save
from static2_extract import sections,strtable
from ps2_graphics_port import p2ig_textures,fake_tx48,STATUS_LABELS,redraw_status_icon
from fix_ps2_forecast_badges import picture
import insert_text as it

VERSION='0.4.14';SOURCE_VERSION='0.4.13'
BASE=ROOT/'work/build/ps2'/f'battle_labels_{VERSION}'
PREVIOUS=ROOT/'work/build/ps2'/f'narration_{SOURCE_VERSION}'


def prepare(dry_run=False):
    report=dict(version=VERSION,source_build=SOURCE_VERSION,resources={},
                executable_unchanged=True,numeric_gameplay_records_unchanged=True,
                labels=[],ai_names=[],github_release=False,visual_validation='asset previews only')
    fix=(PREVIOUS/'FIX00.DAT').read_bytes();data=bytearray(fix);sec=sections(fix,0)
    names=strtable(fix,sec['Strg'][0],sec['Strg'][2]);ranges=[]
    for ident,name in enumerate(names):
        if unicodedata.normalize('NFKC',name)!='Artificial Intelligence':continue
        pos=sec['Strg'][0]+struct.unpack_from('<I',fix,sec['Strg'][0]+12+4*ident)[0]
        z=fix.index(0,pos)+1;raw=it.encode('AI');assert len(raw)<=z-pos
        data[pos:z]=raw+bytes(z-pos-len(raw))
        ranges.append(dict(offset=pos,before=fix[pos:z].hex(),after=data[pos:z].hex()))
        report['ai_names'].append(dict(table='Strg',entry=ident,english='AI',previous='Artificial Intelligence'))
    assert report['ai_names']==[dict(table='Strg',entry=1133,english='AI',previous='Artificial Intelligence')]
    changed_fix=bytes(data)
    report['resources']['FIX00.DAT']=dict(source_sha256=sha(fix),target_sha256=sha(data),ranges=ranges)
    wnd=(PREVIOUS/'WND.BIN').read_bytes();data=bytearray(wnd)
    native=(ROOT/'work/source/ps2/WND.BIN').read_bytes()
    rows={r['name']:r for r in p2ig_textures(native)};ranges=[];previews=[]
    for name in (*STATUS_LABELS,'IM_IC12'):
        row=rows[name];a=row['offset']+row['pixel_offset'];z=a+row['pixel_bytes']
        if name=='IM_IC12':pixels=native[a:z];layout=dict(visible_box=[0,0,21,21],native_hp_restored=True);text='HP'
        else:text=STATUS_LABELS[name];pixels,layout=redraw_status_icon(fake_tx48(native,row),text)
        assert len(pixels)==1024
        before=picture(wnd,row);data[a:z]=pixels;after=picture(data,row)
        ranges.append(dict(offset=a,before=wnd[a:z].hex(),after=pixels.hex()))
        report['labels'].append(dict(asset=name,english=text,pixel_offset=a,pixel_bytes=1024,**layout))
        previews.append((name,text,before,after))
    changed_wnd=bytes(data)
    report['resources']['WND.BIN']=dict(source_sha256=sha(wnd),target_sha256=sha(data),ranges=ranges)
    report['forecast_badges_preserved']=['IM_IC00S','IM_IC01S']
    print('AI: Strg 1133; status labels: '+', '.join(r['english'] for r in report['labels']))
    if dry_run:print('Dry run: no file writes.');return report
    assert not BASE.exists() and not (ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso').exists(),'Existing build preserved'
    BASE.mkdir(parents=True)
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT','.45','.json'):shutil.copyfile(path,BASE/path.name)
    (BASE/'FIX00.DAT').write_bytes(changed_fix);(BASE/'WND.BIN').write_bytes(changed_wnd)
    save(BASE/'battle_labels.json',report)
    save(ROOT/'work/translation/en/ps2'/f'battle_labels_{VERSION}.en.json',report)
    out=ROOT/'work/ui/ps2'/f'battle_labels_{VERSION}';out.mkdir(parents=True,exist_ok=True)
    shutil.copyfile('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-e392e018-3b4b-44df-9e2e-500ae26301e8.png',out/'reported.png')
    sheet=Image.new('RGB',(288,150*len(previews)),(36,36,36));draw=ImageDraw.Draw(sheet)
    for i,(name,text,before,after) in enumerate(previews):
        draw.text((2,i*150),name+' '+text+' before / after',fill='white')
        for im,x in ((before,0),(after,144)):
            enlarged=im.resize((128,128),Image.Resampling.NEAREST);sheet.paste(enlarged,(x,i*150+20),enlarged)
        after.save(out/(name+'.png'))
    sheet.save(out/'status_before_after.png');save(out/'layout.json',{k:v for k,v in report.items() if k!='resources'})
    return report


def regression():
    for module in ('verify_ps2_battle_labels','verify_ps2_narration','verify_ps2_stage30','verify_ps2_favorites',
                   'verify_ps2_prologue_fix','verify_ps2_ui','verify_ps2_ui_details','verify_ps2_roster_system','verify_ps2_setup_save'):
        source=f"import sys;sys.path.insert(0,'tools');from pathlib import Path;from {module} import verify;verify(Path({str(BASE)!r}),{VERSION!r})"
        result=subprocess.run([sys.executable,'-X','utf8','-c',source],capture_output=True,text=True)
        if result.returncode:print(result.stdout);print(result.stderr);raise RuntimeError(module+' failed')
        print(module+': passed',flush=True)
    for tag,suffix in [('weapon_battle','execution'),('map_support','verification'),('forecast_badges','verification')]:
        evidence=read_json(ROOT/'work/output'/f'ps2_{tag}_{SOURCE_VERSION}_{suffix}.json')
        evidence.update(reused_for_build=VERSION,evidence_source_build=SOURCE_VERSION,
                        reuse_reason='Executable and MAP are byte-identical; AT/CT pixel payloads remain exact. Independent battle-label proof confines changes to one name and seven status tiles.')
        save(ROOT/'work/output'/f'ps2_{tag}_{VERSION}_{suffix}.json',evidence)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dry-run',action='store_true');parser.add_argument('--build',action='store_true');parser.add_argument('--verify-existing',action='store_true');args=parser.parse_args()
    if args.verify_existing:report=read_json(BASE/'battle_labels.json')
    else:report=prepare(args.dry_run)
    if args.dry_run:return
    regression()
    if args.build:
        from package_ps2_stage30 import build
        final=build(BASE,VERSION,SOURCE_VERSION,('WND.BIN','FACEPACK.BIN'))
        prior=read_json(ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json');old={r['path']:r['target_sha256'] for r in prior['files']}
        changed=[r['path'] for r in final['files'] if r['target_sha256']!=old[r['path']]]
        assert changed==['/DATA/FIX00.DAT;1','/DATA/WND.BIN;1'],changed
        final.update(battle_label_corrections=report,battle_label_execution_checks=read_json(ROOT/'work/output'/f'ps2_battle_labels_{VERSION}_verification.json'),
                     narration_execution_checks=read_json(ROOT/'work/output'/f'ps2_narration_{VERSION}_execution.json'),
                     changed_from_previous=changed,pcsx2_visual_validation='pending for battle forecast',github_release=False)
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',final)


if __name__=='__main__':main()
