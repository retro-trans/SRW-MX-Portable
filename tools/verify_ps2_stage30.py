"""Execute PS2 campaign, loaders, cards and regression checks for PSP stage 30.

Native EE routines execute in Unicorn with only disc and drawing services
supplied by fixtures. These checks do not claim a complete in-game battle clear.
"""
import json
import struct
import unicodedata
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from verify_ps2_font import machine, verify as verify_font
from verify_ps2_difficulty import run, put, word, verify as verify_balance
from verify_ps2_translation_hooks import verify as verify_text
from verify_ps2_prologue import verify as verify_prologue
from verify_ps2_prologue_entry import verify as verify_entry
from verify_ps2_prologue_numbering import verify as verify_numbers, chapter_card
from port_ps2_stage30 import BASE, ROOT, VERSION, SCENES
from port_ps2_translations import sha
from port_ps2_prologue import save
from static2_extract import sections


def cstring(vm, ptr):
    raw=bytearray()
    while True:
        byte=vm.mem_read(ptr+len(raw),1)
        if byte==b'\0':return bytes(raw)
        raw+=byte;assert len(raw)<2048


def native_checks(elf, maps, stage, info, static, pack):
    u=machine(elf);obj=0x810000;stage_va=0x820000;name_va=0x880000;dest=0x890000
    # Unicorn's MIPS64 backend rejects these EE conditional moves. Supply
    # their documented register semantics without substituting any routine.
    conditional_moves=[]
    def ee_move(vm,pc,size,unused):
        if pc not in (0x3476c0,0x3476f8,0x34774c,0x2e31c8,0x2e322c):return
        op=word(vm,pc);assert op>>26==0 and op&63 in (10,11)
        rs=(op>>21)&31;rt=(op>>16)&31;rd=(op>>11)&31
        value=vm.reg_read(reg.UC_MIPS_REG_0+rt)
        if (value==0)==(op&63==10):vm.reg_write(reg.UC_MIPS_REG_0+rd,vm.reg_read(reg.UC_MIPS_REG_0+rs))
        conditional_moves.append(pc);vm.reg_write(reg.UC_MIPS_REG_PC,pc+4)
    u.hook_add(UC_HOOK_CODE,ee_move)
    u.mem_write(stage_va,stage);put(u,obj,stage_va);put(u,obj+4,stage_va)
    sec=struct.unpack_from('<18I',elf,0x37e438)
    table=int(info['script_sector_table_va'],16)
    scripts=struct.unpack('<204I',u.mem_read(table,816))
    reads=[]
    for pc in (0x36af24,0x36accc,0x1a02e0):u.mem_write(pc,struct.pack('<2I',0x03e00008,0))
    def service(vm,pc,size,unused):
        a0=vm.reg_read(reg.UC_MIPS_REG_A0);a1=vm.reg_read(reg.UC_MIPS_REG_A1)
        if pc==0x36af24:vm.reg_write(reg.UC_MIPS_REG_V0,len(cstring(vm,a0)))
        elif pc==0x36accc:
            x=cstring(vm,a0);y=cstring(vm,a1);vm.reg_write(reg.UC_MIPS_REG_V0,(x>y)-(x<y))
        elif pc==0x1a02e0:
            assert cstring(vm,a1)==b'\\DATA\\MAP.BIN;1'
            offset=vm.reg_read(reg.UC_MIPS_REG_A3)*2048;length=vm.reg_read(reg.UC_MIPS_REG_T0)
            raw=maps[offset:offset+length];assert len(raw)==length
            vm.mem_write(vm.reg_read(reg.UC_MIPS_REG_A2),raw);vm.reg_write(reg.UC_MIPS_REG_V0,1)
            reads.append(dict(offset=offset,bytes=length,sha256=sha(raw)))
    handle=u.hook_add(UC_HOOK_CODE,service)
    script_checks=[]
    for scene in info['scenes']:
        name=scene['scene'];index=scene['index'];u.mem_write(name_va,name.encode()+b'\0')
        for pc,expected in [(0x339730,index),(0x339550,(scripts[index+1]-scripts[index])*2048)]:
            u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,name_va)
            run(u,pc);assert u.reg_read(reg.UC_MIPS_REG_V0)==expected,(name,hex(pc))
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,dest);u.reg_write(reg.UC_MIPS_REG_A2,name_va)
        run(u,0x339668);assert u.reg_read(reg.UC_MIPS_REG_V0)==1
        assert reads[-1]['sha256']==scene['target_sha256'];assert u.mem_read(dest,4)==b'SRWL'
        script_checks.append(dict(scene=name,**reads[-1]))
    deployments=[]
    for group,name,count in [(12,'s0570',132),(10,'s0560',46)]:
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,7);u.reg_write(reg.UC_MIPS_REG_A2,group)
        run(u,0x3392c8);length=u.reg_read(reg.UC_MIPS_REG_V0);assert length==(44+192*count+2047)//2048*2048
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,dest)
        u.reg_write(reg.UC_MIPS_REG_A2,7);u.reg_write(reg.UC_MIPS_REG_A3,group);run(u,0x3393b0)
        raw=bytes(u.mem_read(dest,length));assert struct.unpack_from('<2I',raw,4)==(910,90)
        assert raw[24:32].split(b'\0')[0]==name.encode();assert struct.unpack_from('<I',raw,40)[0]==count
        deployments.append(dict(scene=name,units=count,**reads[-1]))
    u.hook_del(handle)
    put(u,obj+0x3a0,5);put(u,obj+0x3a8,7);put(u,obj+0x3a4,0)
    groups=[0,2,4,6,8,12,10];selected=[]
    for location,group in enumerate(groups):
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,location);run(u,0x346e90)
        assert u.reg_read(reg.UC_MIPS_REG_V0)==group
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,location);run(u,0x346f88)
        assert word(u,obj+0x3ac)==group
        history=bytes(u.mem_read(obj+0x3b0+2*(location+1),2));assert history==bytes((7,location))
        u.mem_write(obj+28+7*56+location,b'\x01');selected.append(dict(location=location,group=group,history=list(history)))
    u.reg_write(reg.UC_MIPS_REG_A0,obj);run(u,0x347558);assert u.reg_read(reg.UC_MIPS_REG_V0)==7
    # Completion only covers all seven locations after bit 6 is included.
    for cleared in range(8):
        put(u,obj+0x39c,(1<<cleared)-1);u.reg_write(reg.UC_MIPS_REG_A0,obj);run(u,0x347248)
        assert u.reg_read(reg.UC_MIPS_REG_V0)==(1<<cleared)-1
        u.reg_write(reg.UC_MIPS_REG_A0,obj);run(u,0x347590)
        # Locations 1..3 are the original parallel branch, then sequential
        # locations 4, 5 (new) and 6. Preserve that native branch behavior.
        assert u.reg_read(reg.UC_MIPS_REG_V0)==[1,4,4,4,5,6,7,7][cleared],(cleared,u.reg_read(reg.UC_MIPS_REG_V0))
    saves=0
    for getter,setter,length,target in [(0x347198,0x3470a0,16,obj+12),(0x3471c8,0x3470d0,896,obj+28),(0x347250,0x347150,256,obj+0x3b0)]:
        before=bytes(u.mem_read(target,length));buffer=0x870000
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,buffer);run(u,getter)
        u.mem_write(target,bytes(length));u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,buffer);run(u,setter)
        assert bytes(u.mem_read(target,length))==before;saves+=1
    wrapper=int(info['native']['objective_title_wrapper_va'],16);titles=[]
    # A selected, not-yet-cleared location has variant index zero. Reset the
    # prior save-round-trip fixture's clear counters before title lookup.
    u.mem_write(obj+28,bytes(896))
    expected_titles=['Prologue','Pursuer','D and E','Prologue','Visitors from the Beyond',
        'Indestructible Getter Robo','What Gnaws at the \u201cHeart\u201d','Zeorymer Sorties at Dawn']
    for ident,(chapter,group,location) in enumerate([(0,4,0),(0,0,1),(0,2,2),(1,4,0),(1,0,1),(1,2,2),(7,12,5),(7,10,6)]):
        put(u,obj+0x3a8,chapter)
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,location);run(u,0x3473d0)
        correct=u.reg_read(reg.UC_MIPS_REG_V0)
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,group//2);run(u,wrapper)
        assert u.reg_read(reg.UC_MIPS_REG_V0)==correct
        title=unicodedata.normalize('NFKC',cstring(u,correct).decode('cp932'));assert title==expected_titles[ident],(chapter,group,title)
        titles.append(dict(chapter=chapter,group=group,title=title))
    cards=[]
    for group,number,animation in [(12,29,166),(10,30,134)]:
        for function in (0x348588,0x348908):
            actual=chapter_card(elf,7,group,number,function);assert actual==dict(animation=animation,number=number)
            cards.append(dict(group=group,function=hex(function),**actual))
    # The adapted cache command must advance without window/portrait side
    # effects, including when its old PSP mode operand is zero.
    for mode in (0,1):
        u.mem_write(dest,struct.pack('<12I',178,mode,*([0]*10)))
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,dest)
        stack=u.reg_read(reg.UC_MIPS_REG_SP);before=bytes(u.mem_read(obj,0x500))
        run(u,0x306a20);assert u.reg_read(reg.UC_MIPS_REG_V0)==2
        assert u.reg_read(reg.UC_MIPS_REG_SP)==stack and bytes(u.mem_read(obj,0x500))==before
    # Exercise the real animation player's disc read path, not a synthetic
    # descriptor lookup. Stop after native loading, before drawing/digit work.
    animation_reads=[]
    u.mem_map(0xb00000,0x500000)
    u.mem_write(0x800000,static);anim=0xb00000
    put(u,anim+0x2ec00,0x800000+0x1a6e78);put(u,anim+0x2ec04,0xc00000)
    for i in range(10):put(u,anim+0x2d324+24*i,0xd00000+i*0x11000)
    def animation_service(vm,pc,size,unused):
        if pc==0x2e3030:vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
        elif pc==0x1a02e0:
            assert cstring(vm,vm.reg_read(reg.UC_MIPS_REG_A1))==b'\\DATA\\PACKMAPC.BIN;1'
            offset=vm.reg_read(reg.UC_MIPS_REG_A3)*2048;length=vm.reg_read(reg.UC_MIPS_REG_T0)
            raw=pack[offset:offset+length];assert len(raw)==length
            vm.mem_write(vm.reg_read(reg.UC_MIPS_REG_A2),raw);vm.reg_write(reg.UC_MIPS_REG_V0,length)
            animation_reads.append(dict(offset=offset,bytes=length))
        elif pc==0x2e32bc:vm.emu_stop()
    u.hook_add(UC_HOOK_CODE,animation_service)
    u.reg_write(reg.UC_MIPS_REG_A0,anim);u.reg_write(reg.UC_MIPS_REG_A1,166);u.reg_write(reg.UC_MIPS_REG_A2,0)
    u.reg_write(reg.UC_MIPS_REG_A3,29);u.reg_write(reg.UC_MIPS_REG_T0,0);u.reg_write(reg.UC_MIPS_REG_T1,0)
    u.emu_start(0x2e3158,0x920000,count=10000);assert u.reg_read(reg.UC_MIPS_REG_PC)==0x2e32bc
    descriptor=info['graphics']['descriptor']
    assert [r['offset'] for r in animation_reads]==[d for d in descriptor if d!=0xffffffff]
    return dict(native_script_loads=script_checks,native_deployments=deployments,
        native_campaign_locations=selected,native_save_round_trips=saves,
        native_availability_masks_checked=8,objective_titles=titles,native_card_cases=cards,
        native_card_archive_reads=animation_reads,portrait_cache_adaptation_modes_checked=2,
        ee_conditional_move_instructions_modelled=sorted(set(hex(pc) for pc in conditional_moves)))


def verify(base=BASE, version=VERSION):
    BASE, VERSION = base, version
    elf=(BASE/'SLPS_253.45').read_bytes();maps=(BASE/'MAP.BIN').read_bytes();stage=(BASE/'STAGE.BIN').read_bytes()
    fix=(BASE/'FIX00.DAT').read_bytes();static=(BASE/'STATIC.BIN').read_bytes();pack=(BASE/'PACKMAPC.BIN').read_bytes()
    meta=json.loads((BASE/'patch.json').read_text());info=json.loads((BASE/'stage30.json').read_text())
    assert sha(elf)==meta['target_sha256']
    checks=native_checks(elf,maps,stage,info,static,pack)
    s=sections(fix,0);row=lambda tag,ident,size:fix[s[tag][0]+12+ident*size:s[tag][0]+12+(ident+1)*size]
    assert row('Unit',156,124)==row('Unit',69,124)
    for ident in (431,432):
        rec=row('Pilt',ident,184);aqua=row('Pilt',315,184)
        for field in (0,2,14,16,164,166):assert rec[field:field+2]==aqua[field:field+2]
        assert struct.unpack_from('<I',static,0x1b8174+ident*4)[0]==struct.unpack_from('<I',static,0x1b8174+315*4)[0]
    checks['native_additional_asset_references_valid']=True
    original=(ROOT/'work/source/ps2/SLPS_253.45').read_bytes()
    mips=verify_font(original,elf,meta);checks['font']={k:v for k,v in mips.items() if not isinstance(v,list)}
    checks['translations']=verify_text(elf,json.loads((ROOT/'work/build/ps2/campaign/native_text.json').read_text()))
    checks['difficulty']=verify_balance(elf,json.loads((BASE/'difficulty.json').read_text()))
    checks['prologue']=verify_prologue(VERSION,BASE,(156,),(431,432))
    checks['new_game']=verify_entry(elf,stage);checks['numbering']=verify_numbers(elf)
    checks.update(version=VERSION,full_battle_clear='pending',physical_ps2_validation='pending')
    save(ROOT/'work/output'/f'ps2_stage30_{VERSION}_execution.json',checks)
    print(json.dumps(dict(version=VERSION,passed=True,scenes=len(checks['native_script_loads']),locations=7,new_card=166)))
    return checks


if __name__=='__main__':verify()
