"""Read back new text and independently preserve earlier script/table data."""
import json
import struct
from pathlib import Path
import insert_text as it
import verify_psp_0413 as previous
import verify_psp_0410 as native
from psp_spirit_footer import FOOTER_PATCHES
from static2_extract import sections
from verify_text_build import read_iso,resolver,overflow_table
import build_patch as build

ROOT=Path(__file__).resolve().parents[1]


def main():
    paths=['/PSP_GAME/SYSDIR/BOOT.BIN','/PSP_GAME/USRDIR/MAP_ADD.BIN','/PSP_GAME/USRDIR/STATIC2_ADD.BIN']
    old=read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.13.iso'),paths)
    new=read_iso(str(ROOT/'work/output/SRWMX_EN_0.4.14.iso'),paths)
    boot=new[paths[0]];static=new[paths[2]];get=resolver(static,boot)
    manifest=json.loads((ROOT/'work/translation/en/ui/psp_0.4.14.en.json').read_text(encoding='utf8'))
    start,_,count=sections(static)['Strg'];changed={int(k) for k in [*manifest['name'],*manifest['music']]}
    masked=bytearray(static)
    for i in range(count):
        if i in changed:
            masked[start+12+i*4:start+16+i*4]=old[paths[2]][start+12+i*4:start+16+i*4]
        else:
            off=struct.unpack_from('<I',static,start+12+i*4)[0]
            oldoff=struct.unpack_from('<I',old[paths[2]],start+12+i*4)[0]
            assert get(start,off)==resolver(old[paths[2]],old[paths[0]])(start,oldoff)
    assert bytes(masked)==old[paths[2]],'Only three Strg pointers may change'
    for idx,text in {**manifest['name'],**manifest['music']}.items():
        off=struct.unpack_from('<I',static,start+12+int(idx)*4)[0]
        assert get(start,off)==it.encode(text)[:-1]
    info=json.loads((ROOT/'work/output/psp_text_0.4.14_verification.json').read_text())['overflow']
    n=info['previous_overflow_entries']
    a,b=overflow_table(old[paths[0]]),overflow_table(boot)
    assert boot[b+96:b+96+n*4]==old[paths[0]][a+96:a+96+n*4]
    targets=set()
    scenes={r['name']:r['block'] for r in json.loads((ROOT/'work/source/stage_map.json').read_text(encoding='utf8'))}
    for e in manifest['dialogue']:
        for use in e['uses']:
            scene,slot=use.split(':');targets.add((scenes[scene],int(slot)))
    offsets=struct.unpack_from('<204I',boot,build.BLOCK_TABLE)
    assert offsets==struct.unpack_from('<204I',old[paths[0]],build.BLOCK_TABLE)
    seen=[]
    for block in range(203):
        lo,hi=[(build.SCRIPT_SECTOR+offsets[i])*2048 for i in (block,block+1)]
        before,after=old[paths[1]][lo:hi],new[paths[1]][lo:hi]
        cmds,slots,tab=struct.unpack_from('<3I',before,4)
        assert before[:32+48*cmds]==after[:32+48*cmds]
        p,q=[struct.unpack_from(f'<{slots}I',x,tab) for x in (before,after)]
        for slot,(x,y) in enumerate(zip(p,q)):
            v,w=before[x:before.index(b'\0',x)],after[y:after.index(b'\0',y)]
            if (block,slot) in targets:
                assert v!=w;seen.append((block,slot))
            else:assert v==w,(block,slot)
            assert it.encode('DeSand')[:-1] not in w,(block,slot)
    assert set(seen)==targets
    for va,_,word in FOOTER_PATCHES:assert struct.unpack_from('<I',boot,va+96)[0]==word
    foot=previous.footer(boot,['Bless','Focus','Trust','????','Cheer','????'],[35,15,25,0,70,0])
    previous.check_footer(foot)
    result=dict(version='0.4.14',name_and_two_music_titles_verified=True,
        old_overflow_pointers_preserved=n,all_other_static_bytes_preserved=True,
        changed_script_slots=seen,all_script_commands_and_other_strings_preserved=True,
        old_surname_absent_in_all_203_script_tables=True,
        previous_footer=foot,previous_level_up=previous.level_up_draw(boot),
        previous_narration=native.narration(boot),affected_screen_playthrough_verified=False)
    (ROOT/'work/output/psp_text_0.4.14_execution.json').write_text(json.dumps(result,indent=1),encoding='utf8')
    print('Six dialogue slots, three names, all earlier tables and UI/crash regressions pass.')


if __name__=='__main__':main()
