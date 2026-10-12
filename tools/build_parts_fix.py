"""Create and audit a local PSP 0.4.31 candidate over 0.4.30."""
import json
import shutil
from pathlib import Path
import pycdlib
import fix_psp_parts as fix
from build_title_footer import stamp_existing
from build_patch import iso_read
from fix_uniform_chapter_cards import compare_discs
from title_footer import verify_iso
import hashlib

ROOT=Path(__file__).resolve().parents[1]
BASE,VERSION='0.4.30','0.4.31'


def main():
    source=ROOT/f'work/output/SRWMX_EN_{BASE}.iso'
    target=ROOT/f'work/output/SRWMX_EN_{VERSION}.iso'
    assert source.exists() and not target.exists(), 'Preserve versioned builds'
    iso=pycdlib.PyCdlib();iso.open(str(source))
    boot=iso_read(iso,'/PSP_GAME/SYSDIR/BOOT.BIN')
    assert boot==iso_read(iso,'/PSP_GAME/SYSDIR/EBOOT.BIN')
    updated=fix.patch_boot(boot)
    assert len(updated)==len(boot) and fix.patch_boot(updated)==updated
    allowed=[]
    for site in fix.SITES:
        a=site+0x60;allowed.append((a,a+4))
    last=0
    for a,z in sorted(allowed):assert boot[last:a]==updated[last:a];last=z
    assert boot[last:]==updated[last:]
    shutil.copyfile(source,target)
    disc_ranges=[]
    with target.open('r+b') as f:
        for path in ('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN'):
            extent=iso.get_record(iso_path=path).extent_location()*2048
            for a,z in allowed:
                f.seek(extent+a);assert f.read(z-a)==boot[a:z]
                f.seek(extent+a);f.write(updated[a:z]);disc_ranges.append((extent+a,extent+z))
    footer=stamp_existing(target,'PSP',VERSION)
    disc_ranges.extend((footer['disc_extent']+a,footer['disc_extent']+z) for a,z in footer['pixel_ranges'])
    verify=pycdlib.PyCdlib();verify.open(str(target))
    for path in ('/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/SYSDIR/EBOOT.BIN'):
        assert iso_read(verify,path)==updated
    for folder,_,files in iso.walk(iso_path='/'):
        for name in files:
            path=folder.rstrip('/')+'/'+str(name)
            a,b=iso.get_record(iso_path=path),verify.get_record(iso_path=path)
            assert (a.extent_location(),a.data_length)==(b.extent_location(),b.data_length)
    iso.close();verify.close()
    oldhash,newhash=compare_discs(source,target,disc_ranges)
    prior=json.loads((ROOT/f'work/output/psp_chapter_cards_{BASE}_verification.json').read_text())
    assert oldhash==prior['output_sha256']
    assert verify_iso(target,'PSP',VERSION)==footer['readback']
    shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),target.with_name(target.stem+'_FONT_LICENSE.txt'))
    report=dict(version=VERSION,base_version=BASE,platform='PSP',output=target.relative_to(ROOT).as_posix(),
                source_sha256=oldhash,output_sha256=newhash,bytes=target.stat().st_size,
                boot_sha256=hashlib.sha256(updated).hexdigest(),fix=fix.report(),footer=footer,
                executable_words_changed=6,identical_boot_and_eboot=True,
                iso_readback_verified=True,all_other_disc_bytes_preserved=True,
                file_positions_and_sizes_preserved=True,story_and_names_unchanged=True,
                local_build_only=True,github_release=False,in_game_validation='pending')
    output=ROOT/f'work/output/psp_parts_{VERSION}_verification.json'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    local=ROOT/f'work/build/psp_parts_{VERSION}';local.mkdir(parents=True,exist_ok=True)
    (local/'BOOT.fixed.BIN').write_bytes(updated)
    safe=ROOT/f'work/translation/en/ui/parts_buffer_{VERSION}.en.json'
    safe.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(target,newhash,flush=True)


if __name__=='__main__':main()
