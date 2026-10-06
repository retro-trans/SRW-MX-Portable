"""Execute native scene/deployment loaders and campaign progression for the port."""
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as reg
from verify_ps2_font import machine
from verify_ps2_difficulty import run, put, word
from static2_extract import sections, strtable
from port_ps2_prologue import ROOT, VERSION, SCENES
from port_ps2_translations import sha


def verify(version=VERSION, base=None, added_units=(), added_pilots=()):
    base=base or ROOT/'work/build/ps2'/f'prologue_{version}'
    elf=(base/'SLPS_253.45').read_bytes();maps=(base/'MAP.BIN').read_bytes()
    stage=(base/'STAGE.BIN').read_bytes();fix=(base/'FIX00.DAT').read_bytes()
    meta=json.loads((base/'prologue.json').read_text(encoding='utf8'))
    u=machine(elf);obj=0x810000;stage_va=0x820000;name_va=0x880000;dest=0x890000
    u.mem_write(stage_va,stage);put(u,obj,stage_va);put(u,obj+4,stage_va)
    sec=struct.unpack_from('<18I',elf,0x37e438)
    table=int(meta['script_sector_table_va'],16)
    scripts=struct.unpack('<201I',u.mem_read(table,804))
    observations=[];pending={}
    for addr in (0x36af24,0x36accc,0x1a02e0):u.mem_write(addr,struct.pack('<2I',0x03e00008,0))
    def cstring(vm,ptr):
        out=bytearray()
        while True:
            value=vm.mem_read(ptr+len(out),1)
            if value==b'\0':return bytes(out)
            out+=value;assert len(out)<256
    def service(vm,pc,size,data):
        a0=vm.reg_read(reg.UC_MIPS_REG_A0);a1=vm.reg_read(reg.UC_MIPS_REG_A1)
        if pc==0x36af24:vm.reg_write(reg.UC_MIPS_REG_V0,len(cstring(vm,a0)))
        elif pc==0x36accc:
            x=cstring(vm,a0);y=cstring(vm,a1);vm.reg_write(reg.UC_MIPS_REG_V0,(x>y)-(x<y))
        elif pc==0x1a02e0:
            offset=vm.reg_read(reg.UC_MIPS_REG_A3)*2048
            length=vm.reg_read(reg.UC_MIPS_REG_T0)
            assert cstring(vm,a1)==b'\\DATA\\MAP.BIN;1'
            raw=maps[offset:offset+length];assert len(raw)==length
            vm.mem_write(vm.reg_read(reg.UC_MIPS_REG_A2),raw)
            pending.update(offset=offset,bytes=length,sha256=sha(raw))
            vm.reg_write(reg.UC_MIPS_REG_V0,1)
    handle=u.hook_add(UC_HOOK_CODE,service)
    # Use each actual native lookup, size routine, allocator-facing read routine.
    for index,name in enumerate(SCENES,192):
        u.mem_write(name_va,name.encode()+b'\0')
        for pc,expected in [(0x339730,index),(0x339550,(scripts[index+1]-scripts[index])*2048)]:
            u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,name_va)
            run(u,pc);assert u.reg_read(reg.UC_MIPS_REG_V0)==expected,(name,hex(pc))
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,dest);u.reg_write(reg.UC_MIPS_REG_A2,name_va)
        run(u,0x339668);assert u.reg_read(reg.UC_MIPS_REG_V0)==1
        assert pending['offset']==(sec[10]+scripts[index])*2048
        assert u.mem_read(dest,4)==b'SRWL';observations.append(dict(scene=name,**pending))
    units=[]
    for chapter,name in [(0,'s00r00'),(1,'s00s00')]:
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,chapter);u.reg_write(reg.UC_MIPS_REG_A2,4)
        run(u,0x3392c8);assert u.reg_read(reg.UC_MIPS_REG_V0)==2048
        u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,dest)
        u.reg_write(reg.UC_MIPS_REG_A2,chapter);u.reg_write(reg.UC_MIPS_REG_A3,4)
        run(u,0x3393b0);assert u.reg_read(reg.UC_MIPS_REG_V0)==1
        raw=bytes(u.mem_read(dest,2048));assert raw[24:32].split(b'\0')[0].decode()==name
        assert struct.unpack_from('<2I',raw,4)==(910,390)
        assert struct.unpack_from('<I',raw,40)[0]==2
        units.append(dict(scene=name,**pending))
    u.hook_del(handle)
    # Campaign selectors read the added first location, then both original maps.
    routes=[]
    save_round_trips=0
    for chapter,groups in [(0,[4,0,2]),(1,[4,0,2])]:
        put(u,obj+0x3a8,chapter);u.mem_write(obj+12,bytes(16));u.mem_write(obj+28,bytes(16*56))
        selected=[]
        for location,expected in enumerate(groups):
            for function in (0x346e90,0x346f88):
                u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,location)
                run(u,function)
                if function==0x346e90:
                    selected.append(u.reg_read(reg.UC_MIPS_REG_V0));assert selected[-1]==expected
            # Increment this location's clear count, as stored by native campaign state.
            u.mem_write(obj+28+chapter*56+location,b'\x01')
        routes.append(dict(chapter=chapter,selected_groups=selected))
        # Run native campaign save/load getters, including all seven location slots.
        for getter,setter,length,target in [(0x347198,0x3470a0,16,obj+12),
                                            (0x3471c8,0x3470d0,1024,obj+28),
                                            (0x347250,0x347150,256,obj+0x3b0)]:
            serialized=0x870000;prior=bytes(u.mem_read(target,16 if length==16 else 896 if length==1024 else 256))
            u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,serialized)
            run(u,getter)
            u.mem_write(target,bytes(len(prior)))
            u.reg_write(reg.UC_MIPS_REG_A0,obj);u.reg_write(reg.UC_MIPS_REG_A1,serialized)
            run(u,setter)
            assert bytes(u.mem_read(target,len(prior)))==prior,(chapter,hex(getter))
            save_round_trips+=1
    # Fixh uses absolute subfile offsets; retain all existing gameplay rows/IDs.
    old=(ROOT/'work/build/ps2/campaign/FIX00.DAT').read_bytes();a=sections(old,0);b=sections(fix,0)
    directory=struct.unpack_from('<19I',fix,b['Fixh'][0]+8);assert all(v in [o for o,n,c in b.values()] for v in directory)
    reflowed_text=('Sent','XSkl','Xabl') if (base/'ui_details.json').exists() else ()
    for tag,(off,size,count) in a.items():
        target,nn,cc=b[tag]
        if tag=='Pilt':
            for ident in range(512):
                if ident not in (433,*added_pilots):assert old[off+12+ident*184:off+12+(ident+1)*184]==fix[target+12+ident*184:target+12+(ident+1)*184]
        elif tag=='Unit' and added_units:
            for ident in range(512):
                if ident not in added_units:assert old[off+12+ident*124:off+12+(ident+1)*124]==fix[target+12+ident*124:target+12+(ident+1)*124]
        elif tag not in ('Strg','Fixh',*reflowed_text):assert old[off:off+size]==fix[target:target+nn],tag
    names=strtable(fix,b['Strg'][0],b['Strg'][2]);assert len(names)==a['Strg'][2]+1
    assert names[:-1]==strtable(old,a['Strg'][0],a['Strg'][2])
    r=b['Pilt'][0]+12+433*184;name=struct.unpack_from('<H',fix,r)[0]
    assert names[name]==names[-1] and struct.unpack_from('<H',fix,r+14)[0]==65535
    report=dict(version=version,native_script_loads=observations,native_deployment_loads=units,
                route_progression=routes,fix_directory_valid=True,existing_gameplay_rows_preserved=True,
                new_researcher_row_valid=True,gameplay_clear_and_save_validation='pending')
    report['native_campaign_save_field_round_trips']=save_round_trips
    if reflowed_text:report['reflowed_text_verified_separately']=list(reflowed_text)
    (ROOT/'work/output'/f'ps2_prologue_{version}_execution.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':verify()
