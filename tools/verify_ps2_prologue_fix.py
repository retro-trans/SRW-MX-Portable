"""Execute native Game Over dispatch/retry and researcher archive loading."""
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from fix_ps2_prologue import ROOT,BASE,VERSION,SOURCE_VERSION
from verify_ps2_font import machine
from verify_ps2_difficulty import run,put,word
from verify_ps2_stage30 import cstring
from port_ps2_translations import sha
from port_ps2_prologue import save
from static2_extract import sections
import play_order


def game_over(elf,chapter,group):
    u=machine(elf);battle=0x810000;resources=0x970000;hero=0x980000;campaign=0x990000
    put(u,battle+0x39b4,resources);put(u,resources+0x2014,hero);put(u,resources+0x2010,hero+0x2000)
    put(u,battle+0xcbda4,chapter);put(u,battle+0xcbda8,group)
    services=[]
    # The two native snapshot services are recorded here; their data depends
    # on a live roster. Core dispatch, chapter/group gate and retry are real.
    def service(vm,pc,size,unused):
        if pc in (0x336608,0x30d468,0x12efc0,0x12eec8):
            services.append((pc,vm.reg_read(reg.UC_MIPS_REG_A0),vm.reg_read(reg.UC_MIPS_REG_A1),vm.reg_read(reg.UC_MIPS_REG_A2)))
            vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    u.reg_write(reg.UC_MIPS_REG_A0,battle);u.reg_write(reg.UC_MIPS_REG_A1,0x13d);u.reg_write(reg.UC_MIPS_REG_A2,0)
    stack=u.reg_read(reg.UC_MIPS_REG_SP);run(u,0x1f56c0)
    assert u.reg_read(reg.UC_MIPS_REG_SP)==stack
    assert [s[0] for s in services[:2]]==[0x336608,0x30d468]
    event=next((s for s in services if s[0]==0x12efc0),None)
    if event:
        assert event[1:]==(battle,6,1)
        parent=0x940000;put(u,parent+0x30,resources);put(u,parent+0x34,battle)
        put(u,resources+0x201c,campaign);put(u,campaign+0x3a8,chapter);put(u,campaign+0x3ac,group)
        for addr in (0x12eec8,0x12ee18,0x143318):u.mem_write(addr,struct.pack('<2I',0x03e00008,0))
        u.reg_write(reg.UC_MIPS_REG_A0,parent);u.reg_write(reg.UC_MIPS_REG_A1,6);u.reg_write(reg.UC_MIPS_REG_A2,1)
        run(u,0x134b40)
        assert word(u,battle+0xcbda4)==chapter and word(u,battle+0xcbda8)==group
        assert word(u,campaign+0x3a8)==chapter and word(u,campaign+0x3ac)==group
        return True
    assert services[-1][0]==0x12eec8
    return False


def verify(base=BASE,version=VERSION):
    BASE, VERSION = base, version
    elf=(BASE/'SLPS_253.45').read_bytes();static=(BASE/'STATIC.BIN').read_bytes();faces=(BASE/'FACEPACK.BIN').read_bytes()
    old=(ROOT/'work/build/ps2/stage30_0.1.9/SLPS_253.45').read_bytes()
    native_faces=(ROOT/'work/source/ps2/FACEPACK.BIN').read_bytes()
    assert faces[:len(native_faces)]==native_faces
    prior_static=(ROOT/'work/build/ps2/stage30_0.1.9/STATIC.BIN').read_bytes()
    allowed=[(0x174800+2998*4,0x174800+3000*4),(0x177800+309*60,0x177800+310*60)]
    last=0
    for a,b in allowed:assert static[last:a]==prior_static[last:a];last=b
    assert static[last:]==prior_static[last:]
    checks=[]
    for chapter in range(14):
        for group in range(0,14,2):
            prior=game_over(old,chapter,group);current=game_over(elf,chapter,group)
            assert prior==(chapter<2 and group==0)
            assert current==(chapter<2 and group in (0,4))
            checks.append(dict(chapter=chapter,group=group,automatic_retry=current))
    u=machine(elf);u.mem_write(0x800000,static)
    # Run native Pilt story group getters, rather than assuming +14 (the
    # separate battle-face field) controls these dialogue bust-ups.
    fix=(BASE/'FIX00.DAT').read_bytes();s=sections(fix,0);obj=0x9d0000
    u.mem_write(0x890000,fix[s['Pilt'][0]:s['Pilt'][0]+s['Pilt'][1]])
    put(u,obj,0x890000);v=[]
    for fn in (0x331cc8,0x331ce8):
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,433);run(u,fn)
        v.append(u.reg_read(reg.UC_MIPS_REG_V0))
    assert v==[21,10]
    manager=0x3e0640;u.reg_write(reg.UC_MIPS_REG_A0,manager);run(u,0x273288)
    for pc,ident in ((0x277b08,2110),(0x277b08,2106)):
        u.reg_write(reg.UC_MIPS_REG_A0,manager);u.reg_write(reg.UC_MIPS_REG_A1,ident);run(u,pc)
        assert u.reg_read(reg.UC_MIPS_REG_V0)==(309 if ident==2110 else 305)
    reads=[]
    def service(vm,pc,size,unused):
        if pc==0x2771a8:
            # EE MOVN is unsupported by Unicorn's MIPS64 backend.
            op=word(vm,pc);assert op&63==11
            if vm.reg_read(reg.UC_MIPS_REG_V0):vm.reg_write(reg.UC_MIPS_REG_A3,vm.reg_read(reg.UC_MIPS_REG_V1))
            vm.reg_write(reg.UC_MIPS_REG_PC,pc+4)
        if pc==0x1a02e0:
            assert cstring(vm,vm.reg_read(reg.UC_MIPS_REG_A1))==b'\\DATA\\FACEPACK.BIN;1'
            start=vm.reg_read(reg.UC_MIPS_REG_A3)*2048;n=vm.reg_read(reg.UC_MIPS_REG_T0)
            data=faces[start:start+n];assert n==0x10400 and len(data)==n
            vm.mem_write(vm.reg_read(reg.UC_MIPS_REG_A2),data);vm.reg_write(reg.UC_MIPS_REG_V0,n)
            reads.append(dict(offset=start,bytes=n,sha256=sha(data)))
            vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,service)
    for expression in (0,26):
        u.reg_write(reg.UC_MIPS_REG_A0,manager);u.reg_write(reg.UC_MIPS_REG_A1,2110)
        u.reg_write(reg.UC_MIPS_REG_A2,expression);u.reg_write(reg.UC_MIPS_REG_A3,0);run(u,0x2770d0)
    assert [r['offset'] for r in reads]==[142061568,142129152]
    previous=json.loads((ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json').read_text())
    info=json.loads((BASE/'stage30.json').read_text());meta=json.loads((BASE/'patch.json').read_text());m=(BASE/'MAP.BIN').read_bytes()
    table=int(meta['segment_offset'],16)+int(info['script_sector_table_va'],16)-int(meta['segment_va'],16)
    rel=struct.unpack_from('<204I',elf,table);sec=struct.unpack_from('<18I',elf,0x37e438);changed=[]
    for r in previous['blocks']:
        i=r['index'];raw=m[(sec[10]+rel[i])*2048:(sec[10]+rel[i+1])*2048]
        if sha(raw)!=r['new_sha256']:changed.append(i)
    assert changed==[193,196]
    for i in (193,196):assert play_order.load(m[(sec[10]+rel[i])*2048:(sec[10]+rel[i+1])*2048],0)[1]==[]
    first=[]
    for i in (198,199):
        commands,text=play_order.load(m[(sec[10]+rel[i])*2048:(sec[10]+rel[i+1])*2048],0)
        message=next(c for c in commands[320:] if c[0]==11)
        assert message[3]==322 and 'Wolf 1' in __import__('unicodedata').normalize('NFKC',text[message[2]])
        first.append(dict(scene='s00r00' if i==198 else 's00s00',speaker='Hugo',first_line='This is Wolf 1'))
    report=dict(version=VERSION,native_defeat_route_cases=checks,old_prologue_defeat_fallthrough_reproduced=True,
        snapshot_services='Recorded; live roster rollback not simulated',native_researcher_archive_reads=reads,
        native_pilot_story_mapping=v,native_mitar_mapping_preserved=True,
        all_original_native_portrait_bytes_preserved=True,static_changes_confined_to_unused_portrait_slots=True,
        only_two_empty_opening_blocks_changed=changed,other_201_script_blocks_identical=True,first_dialogue=first)
    save(ROOT/'work/output'/f'ps2_prologue_fix_{VERSION}_execution.json',report)
    print(json.dumps(dict(version=VERSION,defeat_cases=len(checks),portrait_reads=reads,preserved_script_blocks=201)))
    return report


if __name__=='__main__':verify()
