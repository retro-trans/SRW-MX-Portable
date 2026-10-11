"""Build only the reviewed text corrections on the local PSP 0.4.13 ISO."""
import hashlib
import io
import json
import shutil
import struct
from pathlib import Path
import pycdlib
import build_patch as build
import textfit
from fix_psp_0411 import patch_music
from patch_wnd_headers import digest,file_digest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/build/psp_text_0.4.14'


def patch_dialogue(boot,data,manifest):
    offsets=struct.unpack_from('<204I',boot,build.BLOCK_TABLE)
    scenes=json.loads((ROOT/'work/source/stage_map.json').read_text(encoding='utf8'))
    blocks={r['name']:r['block'] for r in scenes}
    targets={};results=[]
    for edit in manifest['dialogue']:
        source=json.loads((ROOT/edit['source_file']).read_text(encoding='utf8'))
        row=next(r for r in source['rows'] if r['id']==edit['id'])
        assert row['en']==edit['en']
        tail=row['jp'].rstrip('@　 ');close=tail[-1] if tail[-1] in '」）' else ''
        opening='（' if edit['kind']=='thought' else '「'
        lines,ok=textfit.wrap(edit['speaker']+opening,edit['en'],close)
        assert ok,(edit['id'],lines)
        text='@'.join(lines)
        for use in edit['uses']:
            scene,slot=use.split(':');targets.setdefault(blocks[scene],{})[int(slot)]=(edit,text)
    out=bytearray(data)
    for block,edits in targets.items():
        start=(build.SCRIPT_SECTOR+offsets[block])*2048
        end=(build.SCRIPT_SECTOR+offsets[block+1])*2048
        raw=data[start:end];ncmd,n,tab=struct.unpack_from('<3I',raw,4)
        pointers=struct.unpack_from(f'<{n}I',raw,tab);trans={}
        for slot,(edit,text) in edits.items():
            old=raw[pointers[slot]:raw.index(b'\0',pointers[slot])]
            # Confirm its baseline wording, independently of line wrapping.
            plain=old.decode('cp932').replace('@','').replace('　',' ')
            import unicodedata
            plain=unicodedata.normalize('NFKC',plain).replace('’',"'")
            body=plain.split('「',1)[1].rstrip('」')
            assert ' '.join(body.split())==' '.join(edit['old_en'].split()),(slot,plain)
            trans[old.decode('cp932')]=text
            results.append(dict(block=block,slot=slot,en=edit['en'],
                                row_widths=[textfit.px(line) for line in text.split('@')]))
        replacement,count=build.rebuild_block(raw,trans)
        assert count==len(edits) and len(replacement)<=len(raw),(block,len(replacement),len(raw))
        replacement+=bytes(len(raw)-len(replacement))
        assert replacement[:32+48*ncmd]==raw[:32+48*ncmd]
        newp=struct.unpack_from(f'<{n}I',replacement,tab)
        for slot,(a,b) in enumerate(zip(pointers,newp)):
            old=raw[a:raw.index(b'\0',a)];new=replacement[b:replacement.index(b'\0',b)]
            assert new==(textfit.encode(edits[slot][1]) if slot in edits else old)
        out[start:end]=replacement
    assert len(results)==6
    return bytes(out),results


def main():
    manifest=json.loads((ROOT/'work/translation/en/ui/psp_0.4.14.en.json').read_text(encoding='utf8'))
    source=ROOT/'work/output/SRWMX_EN_0.4.13.iso'
    output=ROOT/'work/output/SRWMX_EN_0.4.14.iso'
    assert not output.exists(),'Preserve existing versioned images'
    BASE.mkdir(parents=True,exist_ok=True)
    iso=pycdlib.PyCdlib();iso.open(str(source))
    paths=[folder.rstrip('/')+'/'+str(name) for folder,_,files in iso.walk(iso_path='/') for name in files]
    before={p:file_digest(iso,p) for p in paths}
    boot=build.iso_read(iso,'/PSP_GAME/SYSDIR/BOOT.BIN')
    data,dialogue=patch_dialogue(boot,build.iso_read(iso,'/PSP_GAME/USRDIR/MAP_ADD.BIN'),manifest)
    boot,static,table=patch_music(boot,build.iso_read(iso,'/PSP_GAME/USRDIR/STATIC2_ADD.BIN'),
                                {**manifest['name'],**manifest['music']})
    repl={'/PSP_GAME/SYSDIR/BOOT.BIN':boot,'/PSP_GAME/SYSDIR/EBOOT.BIN':boot,
          '/PSP_GAME/USRDIR/MAP_ADD.BIN':data,'/PSP_GAME/USRDIR/STATIC2_ADD.BIN':static}
    for p,b in repl.items():
        (BASE/p.rsplit('/',1)[-1]).write_bytes(b)
        iso.rm_file(iso_path=p);iso.add_fp(io.BytesIO(b),len(b),iso_path=p)
    iso.write(str(output));iso.close()
    check=pycdlib.PyCdlib();check.open(str(output))
    for p in paths:
        assert file_digest(check,p)==(hashlib.sha256(repl[p]).hexdigest() if p in repl else before[p]),p
    check.close()
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),output.with_name(output.stem+'_FONT_LICENSE.txt'))
    with output.open('rb') as f:sha=digest(f)
    result=dict(version='0.4.14',base_version='0.4.13',local_build_only=True,
                dialogue=dialogue,new_name=manifest['name'],music_titles=manifest['music'],overflow=table,
                iso_readback_verified=True,changed_iso_files=sorted(repl),unchanged_iso_files=len(paths)-4,
                output_iso=output.name,output_bytes=output.stat().st_size,output_sha256=sha,
                hardware_psp_verified=False,affected_screen_playthrough_verified=False)
    (ROOT/'work/output/psp_text_0.4.14_verification.json').write_text(json.dumps(result,indent=1),encoding='utf8')
    print(output,sha)


if __name__=='__main__':main()
