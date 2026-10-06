"""Execute real PS2 favorite selection, native bonus and save-field paths."""
import itertools,json,struct,unicodedata
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
from verify_ps2_font import machine
from verify_ps2_difficulty import put,word,run
from port_ps2_translations import ROOT,sha
from port_ps2_prologue import save


def verify(base,version):
    data=(base/'SLPS_253.45').read_bytes();meta=json.loads((base/'patch.json').read_text())
    feature=json.loads((base/'favorites.json').read_text());assert sha(data)==meta['target_sha256']
    state=int(feature['state_va'],16);u=machine(data,r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    obj=0x940000;manager=0x930000;buf=0x900000
    put(u,obj+0xb4,1);put(u,obj+0x88,0x2000);put(u,obj+0x8c,0x4000)
    put(u,obj+0x134,1);put(u,obj+0x138,2);put(u,obj+0xbc,0x812300)
    u.reg_write(r.UC_MIPS_REG_GP,0x4c84f0)
    input_key={'key':None};events=[];draws=[];boxes=[];lookup={'series':0,'base':10}
    def text(ptr):
        raw=bytes(u.mem_read(ptr,512)).split(b'\0')[0]
        return unicodedata.normalize('NFKC',raw.decode('cp932'))
    def services(vm,pc,size,user):
        if pc in (0x146318,0x1a1060,0x143250,0x143460,0x1433f0):
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
        elif pc in (0x12f070,0x12f180):
            mask=vm.reg_read(r.UC_MIPS_REG_A1)
            vm.reg_write(r.UC_MIPS_REG_V0,int((input_key['key']=='confirm' and mask==0x2000) or
                                            (input_key['key']=='cancel' and mask==0x4000)))
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
        elif pc==0x12ef30:
            events.append((vm.reg_read(r.UC_MIPS_REG_A2),vm.reg_read(r.UC_MIPS_REG_A3)))
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
        elif pc==0x130610:
            font=struct.unpack('<2f',vm.mem_read(vm.reg_read(r.UC_MIPS_REG_A0),8))
            draws.append(dict(text=text(vm.reg_read(r.UC_MIPS_REG_A1)),font=font,
                              x=vm.reg_read(r.UC_MIPS_REG_A2),y=vm.reg_read(r.UC_MIPS_REG_A3)))
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
        elif pc==0x1438a0:
            boxes.append([vm.reg_read(getattr(r,'UC_MIPS_REG_'+str(i))) for i in (5,6,7,8)])
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
        elif pc==0x30c038:
            field=vm.reg_read(r.UC_MIPS_REG_A1)
            vm.reg_write(r.UC_MIPS_REG_V0,lookup['series'] if field==6 else 1 if field==0x18 else lookup['base'])
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
        elif pc==0x15e4d0:
            vm.reg_write(r.UC_MIPS_REG_V0,len(text(vm.reg_read(r.UC_MIPS_REG_A1)))*24)
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
    u.hook_add(UC_HOOK_CODE,services)
    def reset():
        u.mem_write(state,bytes(20));events.clear();input_key['key']=None
        put(u,obj+0x3b4,0);put(u,obj+0x3ac,0)
    def key(kind,index):
        put(u,obj+0x3ac,index);input_key['key']=kind
        u.reg_write(r.UC_MIPS_REG_A0,obj);run(u,0x165b30)
        assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
    ids=[]
    for index in range(18):
        put(u,obj+0x3ac,index);u.reg_write(r.UC_MIPS_REG_A0,obj);run(u,0x1661e0)
        ids.append(u.reg_read(r.UC_MIPS_REG_V0))
    assert len(set(ids))==18 and max(ids)<32
    # All triples, all 18 candidates, in each balance mode. A third distinct
    # pick is the only confirm event; duplicates toggle off, never add a slot.
    mode=int(json.loads((base/'difficulty.json').read_text())['mode_va'],16)
    combinations=0;membership=0
    for difficulty in (0,1):
        put(u,mode,difficulty)
        for triple in itertools.combinations(range(18),3):
            reset();put(u,manager+0x5e8,0)
            for n,index in enumerate(triple):
                key('confirm',index)
                assert word(u,state+4)==n+1
                assert events==([] if n<2 else [(1,ids[index])])
            expected=sum(1<<ids[i] for i in triple)
            assert word(u,state)==expected
            u.reg_write(r.UC_MIPS_REG_A0,manager);run(u,int(feature['routines']['commit']['va'],16))
            assert word(u,manager+0x5e8)==expected
            for series in ids:
                u.reg_write(r.UC_MIPS_REG_A0,manager);u.reg_write(r.UC_MIPS_REG_A1,series)
                run(u,0x336970);assert u.reg_read(r.UC_MIPS_REG_V0)==int(bool(expected&(1<<series)))
                membership+=1
            # Native scenario serializer and deserializer instructions.
            u.reg_write(r.UC_MIPS_REG_S4,manager);u.reg_write(r.UC_MIPS_REG_S2,buf)
            run(u,0x335808,0x335810);assert word(u,buf+0x1008)==expected
            put(u,manager+0x5e8,0);u.reg_write(r.UC_MIPS_REG_S3,buf)
            run(u,0x335ca8,0x335cb0);assert word(u,manager+0x5e8)==expected
            assert word(u,mode)==difficulty
            combinations+=1
    # Back out after any number of picks, remove any position, then repick.
    for remove in range(3):
        reset()
        for index in (1,7,17):key('confirm',index)
        events.clear();key('confirm',(1,7,17)[remove])
        wanted=[i for n,i in enumerate((1,7,17)) if n!=remove]
        assert word(u,state+4)==2 and events==[]
        assert list(struct.unpack('<2I',u.mem_read(state+8,8)))==wanted
        key('confirm',5);assert word(u,state+4)==3 and len(events)==1
    for count in range(4):
        reset()
        for index in range(count):key('confirm',index)
        events.clear();key('cancel',17)
        assert word(u,state+4)==max(0,count-1)
        assert events==([(2,0)] if count==0 else [])
        assert word(u,obj+0x3ac)==17
    reset();key('confirm',5);key('confirm',5)
    assert word(u,state)==word(u,state+4)==0 and events==[]
    # No in the final dialog leaves temporary picks editable and writes no
    # manager bits. Canceling at zero publishes the existing exit event.
    reset();put(u,manager+0x5e8,1<<ids[17])
    for index in (0,1,2):key('confirm',index)
    assert word(u,manager+0x5e8)==1<<ids[17]
    flow=0x880000
    put(u,flow+0x5698,99);put(u,flow+0x569c,99)
    u.reg_write(r.UC_MIPS_REG_S4,flow);u.reg_write(r.UC_MIPS_REG_V1,0)
    run(u,0x2be498,0x2be56c)
    assert word(u,flow+0x5694)==7 and word(u,flow+0x5698)==word(u,flow+0x569c)==0
    assert word(u,state+4)==3 and word(u,manager+0x5e8)==1<<ids[17]
    # Fourth choices cannot grow or corrupt the three-slot buffer.
    events.clear();before=bytes(u.mem_read(state,32));key('confirm',3)
    assert bytes(u.mem_read(state,32))==before and events==[]
    put(u,flow+0x3ab0+0x3ac,2)
    u.reg_write(r.UC_MIPS_REG_S4,flow);u.reg_write(r.UC_MIPS_REG_S0,manager)
    run(u,0x2be478,0x2be48c)
    inherited=(1<<ids[17])|sum(1<<ids[i] for i in (0,1,2))
    assert word(u,manager+0x5e8)==inherited
    # Returning to setup starts from zero temporary choices, without clearing
    # the game's inherited favorite bitset.
    u.reg_write(r.UC_MIPS_REG_A0,obj);run(u,int(feature['routines']['reset']['va'],16))
    assert bytes(u.mem_read(state,20))==bytes(20) and word(u,manager+0x5e8)==inherited
    # Legacy single-favorite save fields continue to load untouched.
    put(u,buf+0x1008,1<<ids[7]);u.reg_write(r.UC_MIPS_REG_S3,buf);u.reg_write(r.UC_MIPS_REG_S4,manager)
    run(u,0x335ca8,0x335cb0);assert word(u,manager+0x5e8)==1<<ids[7]
    # Native EXP branch: f20 is 100, f21 is 10; selected membership gives 150.
    put(u,0x3c8cb4,manager);put(u,manager+0x5e8,sum(1<<ids[i] for i in (0,7,17)))
    bonuses=[]
    for series in ids:
        u.reg_write(r.UC_MIPS_REG_V0,series);u.reg_write(r.UC_MIPS_REG_S3,0)
        u.reg_write(r.UC_MIPS_REG_F20,struct.unpack('<I',struct.pack('<f',100))[0])
        u.reg_write(r.UC_MIPS_REG_F21,struct.unpack('<I',struct.pack('<f',10))[0])
        run(u,0x25bf60,0x25bf90)
        actual=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_MIPS_REG_F20)&0xffffffff))[0]
        assert actual==(150 if series in (ids[0],ids[7],ids[17]) else 100),(series,actual)
        bonuses.append(dict(series=series,exp=actual))
    upgrade_cases=0
    for series in ids:
        lookup['series']=series
        for base_limit in (10,14,15):
            lookup['base']=base_limit
            for entry in (0x318980,0x318a10,0x318aa0,0x318b30,0x318bc0):
                u.reg_write(r.UC_MIPS_REG_A0,obj);u.reg_write(r.UC_MIPS_REG_A1,0)
                run(u,entry)
                expected=min(15,base_limit+(2 if series in (ids[0],ids[7],ids[17]) else 0))
                assert u.reg_read(r.UC_MIPS_REG_V0)==expected,(hex(entry),series,base_limit)
                upgrade_cases+=1
    # Draw all three slots with every series at the actual 16px font. Native
    # VWF measurement is executed; only GS drawing is captured.
    pointers=struct.unpack('<18I',u.mem_read(0x470d38,72));renders=[]
    renderer=int(feature['routines']['render']['va'],16)
    for index in range(18):
        reset();put(u,state+4,3)
        for slot in range(3):put(u,state+8+4*slot,index)
        draws.clear();boxes.clear();put(u,obj+0x9c,0);put(u,obj+0xa0,0)
        u.mem_write(obj+0x190,struct.pack('<2f',24,24))
        sp=0xa00000-0x90;u.reg_write(r.UC_MIPS_REG_SP,sp)
        u.mem_write(sp+0x80,struct.pack('<Q',0x920000));u.reg_write(r.UC_MIPS_REG_S2,obj)
        run(u,renderer)
        assert len(draws)==8 and boxes==[[16,12,608,124]],(draws,boxes)
        assert draws[0]['text']=='Favorite Series: 3 / 3'
        assert [draws[i]['text'] for i in (2,4,6)]==[text(pointers[index])]*3
        assert [draws[i]['y'] for i in (2,4,6)]==[48,68,88]
        assert bytes(u.mem_read(obj+0x190,8))==struct.pack('<2f',24,24)
        assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
        renders.append(dict(index=index,draws=list(draws)))
        for row in draws:
            import insert_text as it
            u.mem_write(0x910000,it.encode(row['text']))
            u.mem_write(0x911000,struct.pack('<2f',*row['font'])+bytes(64))
            u.reg_write(r.UC_MIPS_REG_A0,0x911000);u.reg_write(r.UC_MIPS_REG_A1,0x910000)
            run(u,0x131ba0)
            width=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_MIPS_REG_F0)&0xffffffff))[0]
            assert row['x']+width<=624 and row['y']+row['font'][1]<=136,(row,width)
    for scrolling in (0,1):
        draws.clear();boxes.clear();put(u,obj+0x3b4,scrolling);put(u,obj+0x3ac,17)
        sp=0xa00000-0x90;u.reg_write(r.UC_MIPS_REG_SP,sp)
        u.mem_write(sp+0x80,struct.pack('<Q',0x920000));u.reg_write(r.UC_MIPS_REG_S2,obj)
        run(u,0x16603c)
        assert len(draws)==(9 if scrolling==0 else 8)
        assert any(d['text']=='Favorite Series: 3 / 3' for d in draws)
        assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
    # Preserve all immutable resources and limit earlier executable edits to
    # declared hooks, literals, ELF segment size and heap boundary words.
    from fix_ps2_favorites import PREVIOUS
    before=(PREVIOUS/'SLPS_253.45').read_bytes()
    ranges=[(164,172),(0x100180-0xff000,0x100184-0xff000),(0x100188-0xff000,0x10018c-0xff000)]
    ranges += [(int(v['va'],16)-0xff000,int(v['va'],16)-0xff000+4) for v in feature['instruction_words']]
    last=0
    for a,z in sorted(ranges):assert data[last:a]==before[last:a],(last,a);last=z
    assert data[last:len(before)]==before[last:]
    preserved=[]
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT'):
            assert path.read_bytes()==(base/path.name).read_bytes();preserved.append(path.name)
    result=dict(version=version,passed=True,series_ids=ids,triple_mode_cases=combinations,
        membership_checks=membership,native_save_field_roundtrips=combinations,
        native_exp_cases=bonuses,native_upgrade_limit_cases=upgrade_cases,rendered_series_cases=renders,
        toggle_remove_and_compact=True,cancel_undo=True,fourth_pick_rejected=True,
        commit_only_after_confirmation=True,native_yes_no_flow=True,inherited_favorites_preserved=True,
        legacy_single_favorite_preserved=True,temporary_choices_reset=True,
        difficulty_independent=True,save_format_unchanged=True,unchanged_resources=preserved,
        scrolling_render_hook=True,all_text_within_panel=True,
        visual_validation='pending',physical_console_validation='pending')
    save(ROOT/'work/output'/f'ps2_favorites_{version}_execution.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rendered_series_cases','native_exp_cases','unchanged_resources')}))
    return result


if __name__=='__main__':
    from fix_ps2_favorites import BASE,VERSION
    verify(BASE,VERSION)
