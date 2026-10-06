"""Execute the real System rows, option branches and roster label paths."""
import json,struct,unicodedata
from collections import deque
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as r
import insert_text as it
from fix_ps2_roster_system import ROOT,BASE,VERSION,PREVIOUS,SYSTEM_SITES,sha
from verify_ps2_font import machine
from port_ps2_prologue import save

def verify(base=BASE,version=VERSION):
    data=(base/'SLPS_253.45').read_bytes();meta=json.loads((base/'patch.json').read_text())
    c=json.loads((base/'roster_system.json').read_text());assert sha(data)==meta['target_sha256']
    def off(va):
        for n in range(struct.unpack_from('<H',data,44)[0]):
            kind,o,a,_,size,*_=struct.unpack_from('<8I',data,52+n*32)
            if kind==1 and a<=va<a+size:return o+va-a
        raise AssertionError(hex(va))
    def text(ptr):
        start=off(ptr);return data[start:data.index(0,start)]
    widths={g['character']:g['width'] for g in meta['glyphs']}
    for rec in c['data_references']:
        ptr=struct.unpack_from('<I',data,off(int(rec['site'],16)))[0]
        assert ptr==int(rec['target'],16) and text(ptr)==it.encode(rec['english'])[:-1]
    for rec in c['instruction_words']:
        assert struct.unpack_from('<I',data,off(int(rec['va'],16)))[0]==int(rec['new'],16)
    for rec in c['roster_columns']:
        assert sum(widths[x] for x in rec['english'])==rec['width']
        assert rec['width']+8<=rec['minimum_spacing']
    # The default R4000 backend rejects EE MOVN/MOVZ, including delay slots.
    # Use a backend implementing those instructions for this integer-only path.
    u=machine(data,cpu_model=r.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    initial=u.context_save();captured=[];trace=deque(maxlen=12)
    def draw(vm,address,size,user):
        trace.append(hex(address))
        if address in (0x131958,0x37c170,0x37c1d0):
            vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA));return
        if address!=0x130610:return
        ptr=vm.reg_read(r.UC_MIPS_REG_A1)
        raw=bytes(vm.mem_read(ptr,128)).split(b'\0')[0]
        name=unicodedata.normalize('NFKC',raw.decode('cp932'))
        captured.append(dict(english=name,x=vm.reg_read(r.UC_MIPS_REG_A2),y=vm.reg_read(r.UC_MIPS_REG_A3),
            font=list(struct.unpack('<2f',vm.mem_read(vm.reg_read(r.UC_MIPS_REG_A0),8)))))
        vm.reg_write(r.UC_MIPS_REG_PC,vm.reg_read(r.UC_MIPS_REG_RA))
    hook=u.hook_add(UC_HOOK_CODE,draw)
    # Eight rows, every selected setting and legal value. Actual option branches
    # and the translation wrapper run; only palette/GS services are intercepted.
    legal=(2,2,3,2,2,3,2,2);system_cases=[]
    expected=['Grid','Sound','BGM Source','BGM Switch','Rumble','Unit Display','Cursor','Rotation',
              'ON','OFF','Stereo','Mono','Each','Unit','Pilot','Fixed','Switch',
              'ON','OFF','Std','Type','Blink','Screen','Map','90 deg','Free']
    for row,count in enumerate(legal):
        for value in range(count):
            u.context_restore(initial);captured.clear()
            u.mem_write(0x940000,bytes(0x2000));u.mem_write(0x940194,struct.pack('<I',row))
            for i,n in enumerate(legal):u.mem_write(0x940200+i*4,struct.pack('<I',value if i==row else 0))
            u.mem_write(0x9401a8,struct.pack('<2f',24,24)+bytes(64))
            u.mem_write(0xa00010,struct.pack('<8I',*(13 if i==row else 19 for i in range(8))))
            u.reg_write(r.UC_MIPS_REG_S1,0);u.reg_write(r.UC_MIPS_REG_S2,0x940000)
            u.reg_write(r.UC_MIPS_REG_S5,0x9401a8);u.reg_write(r.UC_MIPS_REG_V0,row)
            before=bytes(u.mem_read(0x940200,32))
            try:u.emu_start(0x154dd0,0x1553ec,count=10000)
            except Exception as error:raise AssertionError((hex(u.reg_read(r.UC_MIPS_REG_PC)),row,value,captured,list(trace))) from error
            assert u.reg_read(r.UC_MIPS_REG_PC)==0x1553ec
            assert [v['english'] for v in captured]==expected,(row,value,captured)
            assert bytes(u.mem_read(0x940200,32))==before
            for i,label in enumerate(captured[:8]):
                assert label['x']==28 and label['y']==24+i*26
                first=next(v for v in captured[8:] if v['y']==label['y'])
                assert label['x']+sum(widths[x] for x in label['english'])+8<=first['x']
            for y in range(24,24+8*26,26):
                group=[x for x in captured[8:] if x['y']==y]
                for a,b in zip(group,group[1:]):
                    assert a['x']+sum(widths[x] for x in a['english'])+8<=b['x'],(a,b)
            system_cases.append(dict(selected_row=row,selected_value=value,draws=list(captured)))
    # Local repair hooks must retain font, position, color and native return.
    repairs=[]
    for site in (0x1159b0,0x115cb4):
        u.context_restore(initial);captured.clear()
        for reg,v in ((r.UC_MIPS_REG_A0,0x900000),(r.UC_MIPS_REG_A1,0x4c0ba0),
                      (r.UC_MIPS_REG_A2,100),(r.UC_MIPS_REG_A3,200)):
            u.reg_write(reg,v)
        u.mem_write(0x900000,struct.pack('<2f',24,24))
        u.emu_start(site,site+8,count=300)
        assert len(captured)==1 and captured[0]['english']=='Cost'
        assert (captured[0]['x'],captured[0]['y'])==(100,200)
        assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
        repairs.append(dict(site=hex(site),**captured[0]))
    # Run native scrolling-header draw with each changed actual descriptor.
    column_draws=[]
    for row in c['data_references']:
        u.context_restore(initial);captured.clear()
        site=int(row['site'],16)
        u.mem_write(0x940000,bytes(0x2000))
        u.mem_write(0x9415d8,struct.pack('<2f',24,24)+bytes(64))
        u.reg_write(r.UC_MIPS_REG_A0,0x940000);u.reg_write(r.UC_MIPS_REG_A1,site)
        u.reg_write(r.UC_MIPS_REG_A2,0);u.reg_write(r.UC_MIPS_REG_A3,20)
        u.emu_start(0x1117b0,0x920000,count=1000)
        assert len(captured)==1 and captured[0]['english']==row['english']
        assert u.reg_read(r.UC_MIPS_REG_SP)==0xa00000
        column_draws.append(dict(site=row['site'],**captured[0]))
    u.hook_del(hook)
    # The actual objective screen's title call, including its delay slot.
    actual=[]
    def header(vm,address,size,user):
        if address!=0x143a00:return
        ptr=vm.reg_read(r.UC_MIPS_REG_A1)
        actual.append(bytes(vm.mem_read(ptr,64)).split(b'\0')[0]);vm.emu_stop()
    h=u.hook_add(UC_HOOK_CODE,header);u.context_restore(initial)
    u.reg_write(r.UC_MIPS_REG_S0,0x940000);u.emu_start(0x153b4c,0x920000,count=10)
    assert actual==[it.encode('Objectives')[:-1]]
    u.hook_del(h)
    # Unknown pointers pass through; changing labels must not alter option values.
    unmapped=[]
    for source in (0x4c1a38,0x4c1a40,0x910000):
        u.context_restore(initial);u.mem_write(0x910000,it.encode('Test'))
        u.reg_write(r.UC_MIPS_REG_A1,source);u.reg_write(r.UC_MIPS_REG_RA,0x920000)
        u.emu_start(int(c['draw_wrapper']['va'],16),0x130610,count=500)
        assert u.reg_read(r.UC_MIPS_REG_A1)==source
        unmapped.append(hex(source))
    preserved=[]
    for path in PREVIOUS.iterdir():
        if path.suffix not in ('.DAT','.BIN'):continue
        from ps2_resource_preservation import check
        check(base,PREVIOUS,path.name)
        preserved.append(path.name)
    result=dict(version=version,passed=True,data_reference_checks=len(c['data_references']),
        instruction_checks=len(c['instruction_words']),native_system_cases=system_cases,
        native_repair_cases=repairs,native_roster_column_draws=column_draws,
        native_objective_header='Objectives',unmapped_pointers_preserved=unmapped,
        roster_widths=c['roster_columns'],option_values_unchanged=True,preserved_assets=preserved,
        native_font=True,texture_replacement=False,visual_validation='pending')
    save(ROOT/'work/output'/f'ps2_roster_system_{version}_execution.json',result)
    print(json.dumps(dict(version=version,passed=True,system_cases=len(system_cases),
        roster_columns=len(column_draws),repair_cases=len(repairs),objective_header='Objectives')))
    return result

if __name__=='__main__':verify()
