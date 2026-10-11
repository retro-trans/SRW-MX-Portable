"""Independently check both library indexes, native widths/getters and layout."""
import struct, unicodedata
from unicorn import UC_HOOK_CODE, mips_const as reg
from port_ps2_translations import ROOT, sha, read_json
from port_ps2_prologue import save
from static2_extract import sections, index, strtable
from verify_ps2_font import machine, verify as verify_font
from fix_ps2_library import sentences, file_offset, TAGS
from ps2_font4x import FILE_BIAS
import insert_text as it

def structural(base):
    report=read_json(base/'library.json');previous=ROOT/report['source_directory']
    data=(base/'SLPS_253.45').read_bytes();old=(previous/'SLPS_253.45').read_bytes()
    fix=(base/'FIX00.DAT').read_bytes();before=(previous/'FIX00.DAT').read_bytes()
    assert sha(data)==report['target_elf_sha256'] and sha(old)==report['source_elf_sha256']
    assert sha(fix)==report['target_fix_sha256'] and sha(before)==report['source_fix_sha256']
    current,ptrs=sentences(fix,data);source,old_ptrs=sentences(before,old)
    a=sections(before,0);b=sections(fix,0)
    assert set(a)==set(b) and len(fix)<=len(before)
    for tag,(off,size,count) in a.items():
        if tag in ('Sent','Fixh','Xunt','XPlt'):continue
        p,n,c=b[tag];assert (n,c)==(size,count) and fix[p:p+n]==before[off:off+size],tag
    # Offsets and sentinel semantics remain valid after compacting text storage.
    directory=struct.unpack_from('<19I',fix,b['Fixh'][0]+8)
    old_directory=struct.unpack_from('<19I',before,a['Fixh'][0]+8)
    assert [{v:k for k,(v,_,_) in b.items()}[v] for v in directory]==[{v:k for k,(v,_,_) in a.items()}[v] for v in old_directory]
    old_indexes={t:index(before,a[t][0],a[t][2]) for t in TAGS}
    indexes={t:index(fix,b[t][0],b[t][2]) for t in TAGS}
    other={n for t in TAGS if t not in ('Xunt','XPlt') for rr in old_indexes[t] for n in rr}
    released=set(report['released_sentence_ids'])
    assert not released&other
    for n,raw in enumerate(source):
        if n not in released:
            assert current[n]==raw,('retained sentence',n)
            if old_ptrs[n]&0x80000000:assert ptrs[n]==old_ptrs[n]
    def words(rows,ids):return ' '.join(it.clean(unicodedata.normalize('NFKC',rows[n][:-1].decode('cp932'))) for n in ids).split()
    assert len(report['description_rows'])==512
    seen=set()
    for row in report['description_rows']:
        t=row['table'];n=row['entry'];seen.add((t,n))
        assert indexes[t][n]==row['sentence_ids']
        assert words(source,old_indexes[t][n])==words(current,indexes[t][n])==row['english'].split(),(t,n)
        assert [it.encode(line) for line in row['lines']]==[current[i] for i in indexes[t][n]]
    for t in ('Xunt','XPlt'):
        assert len(old_indexes[t])==len(indexes[t])
        for n,ids in enumerate(indexes[t]):
            if (t,n) not in seen:assert ids==old_indexes[t][n]
    restored=bytearray(data[:len(old)])
    for r in report['reused_storage']+report['instruction_words']:
        pos=r['offset'];raw=bytes.fromhex(r['after']);prior=bytes.fromhex(r['before'])
        assert len(raw)==len(prior) and data[pos:pos+len(raw)]==raw and old[pos:pos+len(prior)]==prior
        restored[pos:pos+len(raw)]=prior
    for pos,length in [(164,8),(0x100180-FILE_BIAS,4),(0x100188-FILE_BIAS,4)]:restored[pos:pos+length]=old[pos:pos+length]
    assert bytes(restored)==old,'Unexpected pre-existing executable modification'
    for path in previous.iterdir():
        if path.suffix in ('.BIN','.DAT') and path.name!='FIX00.DAT':assert path.read_bytes()==(base/path.name).read_bytes(),path.name
    return report

def verify(base,version):
    report=structural(base);assert report['version']==version
    data=(base/'SLPS_253.45').read_bytes();fix=(base/'FIX00.DAT').read_bytes();meta=read_json(base/'patch.json')
    assert sha(data)==meta['target_sha256'] and int(meta['heap_start'],16)<0x800000
    # Generic MIPS supports TRUNC.W.S; the PS2 EE does not. Check the new
    # wrapper as well as the older font hooks against the native COP1 subset.
    stub=file_offset(data,int(report['metadata_stub_va'],16))
    for word, in struct.iter_unpack('<I',data[stub:]):
        if word>>26==17 and (word>>21)&31==16:
            assert word&63 in (0,1,2,3,4,5,6,7,22,24,25,26,28,29,30,31,36,40,41,48,50,52,54),hex(word)
    u=machine(data);sec=sections(fix,0);u.mem_map(0xb00000,(len(fix)+4095)&~4095);u.mem_write(0xb00000,fix)
    integer=machine(data,reg.UC_CPU_MIPS64_MIPS64R2_GENERIC)
    integer.mem_map(0xb00000,(len(fix)+4095)&~4095);integer.mem_write(0xb00000,fix)
    u.mem_write(0x940000,struct.pack('<I',0xb00000+sec['Sent'][0]));initial=u.context_save()
    def native_width(raw,w=24,h=24):
        if b'#' in raw:
            expanded=it.clean(unicodedata.normalize('NFKC',raw[:-1].decode('cp932'))).replace('#男愛称','あ'*6).replace('#女愛称','あ'*6)
            raw=it.encode(expanded)
        u.context_restore(initial);u.mem_write(0x900000,struct.pack('<2f',w,h)+bytes(64));u.mem_write(0x910000,raw)
        for r,v in ((reg.UC_MIPS_REG_A0,0x900000),(reg.UC_MIPS_REG_A1,0x910000),(reg.UC_MIPS_REG_RA,0x920000)):u.reg_write(r,v)
        u.emu_start(0x131ba0,0x920000,count=200000);assert u.reg_read(reg.UC_MIPS_REG_PC)==0x920000
        return struct.unpack('<f',struct.pack('<I',u.reg_read(reg.UC_MIPS_REG_F0)&0xffffffff))[0]
    line_checks=[];old_clipped=0;buffer_regressions=0
    old=(ROOT/report['source_directory']/'SLPS_253.45').read_bytes();prior_fix=(ROOT/report['source_directory']/'FIX00.DAT').read_bytes()
    old_rows,_=sentences(prior_fix,old);old_s=sections(prior_fix,0)
    for row in report['description_rows']:
        t=row['table'];ident=row['entry']
        for n in index(prior_fix,old_s[t][0],old_s[t][2])[ident]:
            old_clipped+=native_width(old_rows[n])>560;buffer_regressions+=len(old_rows[n])>128
        for line_index,(n,line) in enumerate(zip(row['sentence_ids'],row['lines'])):
            raw=it.encode(line);width=native_width(raw)
            expanded=it.encode(line.replace('#男愛称','あ'*6).replace('#女愛称','あ'*6))
            assert width<=560 and len(expanded)<=128,(t,ident,line,width,len(expanded))
            # The actual 12x24 library context uses the uniform 24px Latin font.
            actual_library_width=native_width(raw,12,24)
            assert actual_library_width<=width
            if b'#' not in raw:assert actual_library_width==width
            u.context_restore(initial)
            u.reg_write(reg.UC_MIPS_REG_A0,0x940000);u.reg_write(reg.UC_MIPS_REG_A1,n);u.reg_write(reg.UC_MIPS_REG_RA,0x920000)
            u.emu_start(0x332518,0x920000,count=100);ptr=u.reg_read(reg.UC_MIPS_REG_V0)
            assert bytes(u.mem_read(ptr,len(raw)))==raw
            # Native page count and line lookup, including every last page.
            obj=0x940100;table=sec[t][0]+0xb00000;integer.mem_write(obj,struct.pack('<I',table))
            integer.reg_write(reg.UC_MIPS_REG_A0,obj);integer.reg_write(reg.UC_MIPS_REG_A1,ident);integer.reg_write(reg.UC_MIPS_REG_RA,0x920000)
            integer.emu_start(0x3319d8,0x920000,count=100);assert integer.reg_read(reg.UC_MIPS_REG_V0)==len(row['lines'])
            integer.reg_write(reg.UC_MIPS_REG_A0,obj);integer.reg_write(reg.UC_MIPS_REG_A1,ident);integer.reg_write(reg.UC_MIPS_REG_A2,line_index);integer.reg_write(reg.UC_MIPS_REG_RA,0x920000)
            integer.emu_start(0x3319f8,0x920000,count=100);assert integer.reg_read(reg.UC_MIPS_REG_V0)==n
            line_checks.append(dict(table=t,entry=ident,sentence=n,width=width,bytes=len(raw)))
    assert old_clipped and buffer_regressions
    # Execute every heading reference through its actual argument setup.
    titles=[]
    def heading(vm,pc,size,user):
        if pc==0x143ac0:vm.emu_stop()
    heading_hook=u.hook_add(UC_HOOK_CODE,heading)
    for label,starts,ends in [('Character Library',[0x161dcc,0x161e1c,0x161e58,0x16324c,0x16329c,0x163344],[0x161dd4,0x161e24,0x161e60,0x163254,0x1632a4,0x16334c]),
                              ('Robot Library',[0x15fd5c,0x15fdac,0x15fe00,0x160fa4,0x160ff4,0x161144],[0x15fd64,0x15fdb4,0x15fe08,0x160fac,0x160ffc,0x16114c])]:
        for start,call in zip(starts,ends):
            u.context_restore(initial);u.emu_start(start,0x920000,count=20)
            # Stop before entering the drawing service after the delay slot.
            ptr=u.reg_read(reg.UC_MIPS_REG_A1)
            assert bytes(u.mem_read(ptr,len(it.encode(label))))==it.encode(label)
            titles.append(dict(site=hex(start),english=label))
    u.hook_del(heading_hook)
    captured=[]
    def draw(vm,pc,size,user):
        if pc!=0x130610:return
        captured.append(struct.unpack('<2f',vm.mem_read(vm.reg_read(reg.UC_MIPS_REG_A0),8)))
        assert vm.reg_read(reg.UC_MIPS_REG_A2)==116 and vm.reg_read(reg.UC_MIPS_REG_A3)==198
        vm.reg_write(reg.UC_MIPS_REG_PC,vm.reg_read(reg.UC_MIPS_REG_RA))
    hook=u.hook_add(UC_HOOK_CODE,draw);cases=[]
    names=strtable(fix,sec['Strg'][0],sec['Strg'][2])
    samples={'Hugo','Hiroki Takahashi','Banpresto Originals'}
    for n in range(sec['Pilt'][2]):
        off=sec['Pilt'][0]+12+184*n
        actor=struct.unpack_from('<H',fix,off+164)[0]
        if actor<len(names):samples.add(unicodedata.normalize('NFKC',names[actor]))
    # Explicitly cover the shrinking branch with a real long series title.
    samples.add('Mobile Suit Gundam: Char\'s Counterattack')
    for text in sorted(samples):
        if any(c not in {g['character'] for g in meta['glyphs']} for c in text):continue
        raw=it.encode(text);width=native_width(raw);u.context_restore(initial);captured.clear()
        u.mem_write(0x900000,struct.pack('<2f',24,24)+bytes(64));u.mem_write(0x910000,raw)
        for r,v in ((reg.UC_MIPS_REG_A0,0x900000),(reg.UC_MIPS_REG_A1,0x910000),(reg.UC_MIPS_REG_A2,116),(reg.UC_MIPS_REG_A3,198),(reg.UC_MIPS_REG_S0,6),(reg.UC_MIPS_REG_T0,0xffffffffffffffff),(reg.UC_MIPS_REG_RA,0x920000)):u.reg_write(r,v)
        u.emu_start(int(report['metadata_stub_va'],16),0x920000,count=200000)
        assert u.reg_read(reg.UC_MIPS_REG_PC)==0x920000 and u.reg_read(reg.UC_MIPS_REG_SP)==0xa00000
        assert bytes(u.mem_read(0x900000,8))==struct.pack('<2f',24,24)
        assert len(captured)==1
        w,h=captured[0];actual=width*min(w,h)/24;assert actual<=302.001,(text,actual)
        cases.append(dict(english=text,font=[w,h],width=actual))
    u.hook_del(hook)
    # Gap before every value, measured with the native font rather than counts.
    for label in ('Nick','Voice','Series'):assert 24+native_width(it.encode(label))<104
    font=verify_font((ROOT/'work/source/ps2/SLPS_253.45').read_bytes(),data,meta)
    result=dict(version=version,passed=True,target_elf_sha256=sha(data),target_fix_sha256=sha(fix),
        source_elf_sha256=report['source_elf_sha256'],source_fix_sha256=report['source_fix_sha256'],
        libraries=512,native_description_line_reads=len(line_checks),native_width_limit=560,
        old_overwide_rows=old_clipped,old_rows_exceeding_buffer=buffer_regressions,heading_cases=titles,
        metadata_draw_cases=cases,line_cases=line_checks,wording_preserved=True,
        all_other_database_sections_identical=True,nonlibrary_sentences_preserved=True,
        previous_executable_changed_only_at_declared_library_sites_and_unused_storage=True,
        resource_budget_preserved=True,font={k:v for k,v in font.items() if not isinstance(v,list)},
        in_game_visual_validation='pending',physical_ps2_validation='pending',github_release=False)
    save(ROOT/'work/output'/f'ps2_library_{version}_execution.json',result)
    print('Library proof passed: '+str(len(line_checks))+' native rows; '+str(old_clipped)+' formerly clipped rows.',flush=True)
    return result
