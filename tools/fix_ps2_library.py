"""Reflow both PS2 libraries inside the existing resource budget; local build."""
import argparse, json, shutil, struct, subprocess, sys, unicodedata
from pathlib import Path
import keystone
from port_ps2_translations import ROOT, sha, read_json
from port_ps2_prologue import save
from ps2_translation_native import extend
from ps2_font4x import FILE_BIAS
from ps2_database_port import indices
from ps2_narration_port import wrap_native
from static2_extract import sections, index
import insert_text as it

VERSION='0.4.15'; SOURCE_VERSION='0.4.14'
BASE=ROOT/'work/build/ps2'/f'library_{VERSION}'
PREVIOUS=ROOT/'work/build/ps2'/f'battle_labels_{SOURCE_VERSION}'
TAGS=('Xunt','XPlt','XSpr','XSkl','Xabl','XPrt','XHlp')

def file_offset(data, va):
    for n in range(struct.unpack_from('<H',data,44)[0]):
        kind,off,start,_,size,*_=struct.unpack_from('<8I',data,52+32*n)
        if kind==1 and start<=va<start+size:return off+va-start
    raise AssertionError(hex(va))

def sentences(fix, elf):
    off,_,count=sections(fix,0)['Sent']; rows=[]; ptrs=[]
    for n in range(count):
        ptr=struct.unpack_from('<I',fix,off+12+4*n)[0];ptrs.append(ptr)
        if ptr&0x80000000:
            a=file_offset(elf,ptr&0x7fffffff);blob=elf
        else:a=off+ptr;blob=fix
        rows.append(blob[a:blob.index(0,a)+1])
    return rows,ptrs

def rebuild(fix,replacements):
    sec=sections(fix,0);out=bytearray();positions={}
    for tag,(off,size,count) in sec.items():
        positions[tag]=len(out);out+=replacements.get(tag,fix[off:off+size]);out+=bytes(-len(out)%4)
    reverse={o:t for t,(o,_,_) in sec.items()}
    directory=struct.unpack_from('<19I',fix,sec['Fixh'][0]+8)
    struct.pack_into('<19I',out,positions['Fixh']+8,*(positions[reverse[o]] for o in directory))
    return bytes(out)

def prepare():
    assert not BASE.exists() and not (ROOT/'work/output'/f'SRWMX_PS2_EN_{VERSION}.iso').exists()
    old=(PREVIOUS/'SLPS_253.45').read_bytes();data=bytearray(old)
    meta=read_json(PREVIOUS/'patch.json');fix=(PREVIOUS/'FIX00.DAT').read_bytes();sec=sections(fix,0)
    rows,ptrs=sentences(fix,old)
    tables={t:index(fix,sec[t][0],sec[t][2]) for t in TAGS}
    other={i for t in TAGS if t not in ('Xunt','XPlt') for rr in tables[t] for i in rr}
    library={i for t in ('Xunt','XPlt') for rr in tables[t] for i in rr}
    released=library-other
    native=read_json(ROOT/'work/build/ps2/campaign/native_text.json')['sentences']
    pool_start=int(native['pool_va'],16);pool_end=pool_start+native['pool_bytes']
    # Reuse only unreferenced library strings. All other external strings keep
    # their original address and bytes, including skill/ability descriptions.
    protected=set(ptrs[i]&0x7fffffff for i in range(len(rows)) if i not in released and ptrs[i]&0x80000000)
    free=[]
    for i in released:
        ptr=ptrs[i]&0x7fffffff
        if ptrs[i]&0x80000000 and pool_start<=ptr<pool_end and ptr not in protected:
            free.append((ptr,ptr+len(rows[i])))
        rows[i]=b'\0';ptrs[i]=0
    merged=[]
    for a,z in sorted(set(free)):
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(z,merged[-1][1]))
        else:merged.append((a,z))
    free=merged
    records=[];cache={};new_ids=[]
    manifest=read_json(ROOT/'work/translation/en/ps2/database_port.en.json')['texts']
    for item in manifest:
        tag=item['table']
        if tag not in ('Xunt','XPlt'):continue
        english=it.clean(item['english']);lines=[]
        for paragraph in english.split('\n'):
            lines+=wrap_native(paragraph,meta) if paragraph.strip() else ['']
        assert ' '.join(lines).split()==english.split()
        ids=[]
        for line in lines:
            raw=it.encode(line)
            if raw not in cache:
                cache[raw]=len(rows);new_ids.append(len(rows));rows.append(raw);ptrs.append(0)
            ids.append(cache[raw])
        tables[tag][item['entry']]=ids
        records.append(dict(table=tag,entry=item['entry'],english=english,lines=lines,sentence_ids=ids))
    # Native indexed sentence lookup uses signed LH, so IDs must fit int16.
    assert len(records)==512 and len(rows)<32768
    external={i:ptrs[i] for i in range(len(rows)) if ptrs[i]&0x80000000}
    payload_patches=[];spill=bytearray();spill_ids={}
    def sent_section():
        head=12+4*len(rows);payload=bytearray();offsets=[];dedup={}
        for i,raw in enumerate(rows):
            if i in external:offsets.append(external[i]);continue
            if raw not in dedup:dedup[raw]=head+len(payload);payload+=raw
            offsets.append(dedup[raw])
        return b'Sent'+struct.pack('<2I',head+len(payload),len(rows))+struct.pack('<%dI'%len(rows),*offsets)+payload
    replacements={t:indices(t,tables[t]) for t in ('Xunt','XPlt')}
    # Keep FIX00 no larger than 0.4.14. This matters to the native fixed heap.
    for i in sorted(new_ids,key=lambda i:len(rows[i]),reverse=True):
        replacements['Sent']=sent_section()
        if len(rebuild(fix,replacements))<=len(fix):break
        raw=rows[i];selected=next((n for n,(a,z) in enumerate(free) if z-a>=len(raw)),None)
        if selected is not None:
            a,z=free[selected];where=file_offset(data,a);before=bytes(data[where:where+len(raw)])
            data[where:where+len(raw)]=raw;free[selected]=(a+len(raw),z)
            payload_patches.append(dict(offset=where,before=before.hex(),after=raw.hex()))
            external[i]=0x80000000|a
        else:
            spill_ids[i]=len(spill);spill+=raw
            external[i]=0x80000000 # Size computation only; resolved below.
    if spill:
        data,address=extend(data,meta,spill)
        for i,off in spill_ids.items():external[i]=0x80000000|(address+off)
    replacements['Sent']=sent_section();changed_fix=rebuild(fix,replacements)
    assert len(changed_fix)<=len(fix)
    patches=[]
    def word(va,value,label):
        off=va-FILE_BIAS;before=bytes(data[off:off+4]);after=struct.pack('<I',value)
        assert before!=after;data[off:off+4]=after
        patches.append(dict(va=hex(va),offset=off,before=before.hex(),after=after.hex(),purpose=label))
    for label,sites in [('Character Library',[(0x161dcc,0x161dd8),(0x161e1c,0x161e28),(0x161e58,0x161e64),(0x16324c,0x163258),(0x16329c,0x1632a8),(0x163344,0x163348)]),
                        ('Robot Library',[(0x15fd5c,0x15fd68),(0x15fdac,0x15fdb8),(0x15fe00,0x15fe0c),(0x160fa4,0x160fb0),(0x160ff4,0x161000),(0x161144,0x161148)])]:
        data,ptr=extend(data,meta,it.encode(label),alignment=4);hi=(ptr+0x8000)>>16;lo=ptr&65535
        for a,b in sites:
            assert struct.unpack_from('<I',data,a-FILE_BIAS)[0]==0x3c050049
            assert struct.unpack_from('<I',data,b-FILE_BIAS)[0] in (0x24a55d38,0x24a55d28)
            word(a,0x3c050000|hi,label);word(b,0x24a50000|lo,label)
    # Align nickname, actor and series values, leaving a clear label gap.
    for row in (4,5,6):word(0x4963f0+12*row+4,104,'Character detail value column')
    # Fit unusually long metadata to the area left of the portrait. The full
    # label remains available; context dimensions are restored after drawing.
    asm='''.set noreorder
addiu $sp,$sp,-80
sd $ra,0($sp)
sd $a0,8($sp)
sd $a1,16($sp)
sd $a2,24($sp)
sd $a3,32($sp)
sd $t0,40($sp)
ld $t1,0($a0)
sd $t1,48($sp)
sltiu $t1,$s0,5
bnez $t1,draw
nop
jal 0x131ba0
nop
cvt.w.s $f2,$f0
mfc1 $t1,$f2
slti $t1,$t1,302
bnez $t1,draw
nop
lui $t1,0x4397
mtc1 $t1,$f2
div.s $f2,$f2,$f0
ld $a0,8($sp)
lwc1 $f0,0($a0)
lwc1 $f1,4($a0)
mul.s $f0,$f0,$f2
mul.s $f1,$f1,$f2
swc1 $f0,0($a0)
swc1 $f1,4($a0)
draw:
ld $a0,8($sp)
ld $a1,16($sp)
ld $a2,24($sp)
ld $a3,32($sp)
ld $t0,40($sp)
jal 0x130610
nop
ld $a0,8($sp)
ld $t1,48($sp)
sd $t1,0($a0)
ld $ra,0($sp)
jr $ra
addiu $sp,$sp,80'''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    address=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    code=bytes(ks.asm(asm,address)[0]);data,address=extend(data,meta,code)
    assert struct.unpack_from('<I',data,0x162968-FILE_BIAS)[0]==0x0c04c184
    word(0x162968,0x0c000000|(address>>2),'Fit character metadata before portrait')
    meta['target_sha256']=sha(data)
    report=dict(version=VERSION,source_build=SOURCE_VERSION,source_directory=str(PREVIOUS.relative_to(ROOT)),
                source_elf_sha256=sha(old),target_elf_sha256=sha(data),source_fix_sha256=sha(fix),target_fix_sha256=sha(changed_fix),
                instruction_words=patches,reused_storage=payload_patches,metadata_stub_va=hex(address),
                width_limit=560,row_bytes=128,metadata_width_limit=302,metadata_value_x=104,
                released_sentence_ids=sorted(released),description_rows=records,
                external_spill_bytes=len(spill),fix_bytes=len(changed_fix),previous_fix_bytes=len(fix),
                github_release=False,visual_validation='pending')
    BASE.mkdir(parents=True)
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT','.45','.json'):shutil.copyfile(path,BASE/path.name)
    (BASE/'SLPS_253.45').write_bytes(data);(BASE/'FIX00.DAT').write_bytes(changed_fix)
    save(BASE/'patch.json',meta);save(BASE/'library.json',report)
    narration=read_json(BASE/'narration.json');narration['target_sha256']=sha(data);save(BASE/'narration.json',narration)
    save(ROOT/'work/translation/en/ps2'/f'library_{VERSION}.en.json',report)
    out=ROOT/'work/ui/ps2'/f'library_{VERSION}';out.mkdir(parents=True)
    shutil.copyfile('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-6bb6e0c4-507b-442a-8944-44ab8dc56434.png',out/'reported.png')
    save(out/'layout.json',dict(version=VERSION,viewport=[160,0,960,720],native_resolution=[640,448],
        character_header='Character Library',robot_header='Robot Library',value_column=104,
        description_x=32,description_width=560,portrait_left=418,metadata_max_width=302,
        font=[12,24],latin_render_size=24,description_buffer_bytes=128))
    print(json.dumps({k:report[k] for k in ('version','fix_bytes','previous_fix_bytes','external_spill_bytes')}),flush=True)
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');parser.add_argument('--verify-existing',action='store_true');args=parser.parse_args()
    if not args.verify_existing:prepare()
    from verify_ps2_library import verify
    report=verify(BASE,VERSION)
    for module in ('verify_ps2_narration','verify_ps2_stage30','verify_ps2_favorites','verify_ps2_prologue_fix','verify_ps2_ui','verify_ps2_ui_details','verify_ps2_roster_system','verify_ps2_setup_save'):
        source=f"import sys;sys.path.insert(0,'tools');from pathlib import Path;from {module} import verify;verify(Path({str(BASE)!r}),{VERSION!r})"
        result=subprocess.run([sys.executable,'-X','utf8','-c',source],capture_output=True,text=True)
        if result.returncode:print(result.stdout);print(result.stderr);raise RuntimeError(module+' failed')
        print(module+': passed',flush=True)
    for tag,suffix in [('battle_labels','verification'),('weapon_battle','execution'),('map_support','verification'),('forecast_badges','verification')]:
        evidence=read_json(ROOT/'work/output'/f'ps2_{tag}_{SOURCE_VERSION}_{suffix}.json')
        evidence.update(reused_for_build=VERSION,evidence_source_build=SOURCE_VERSION,reuse_reason='Independent library proof preserves every asset except FIX00 library text and the checked library executable sites/storage. All prior battle code and pixel payloads are exact.')
        save(ROOT/'work/output'/f'ps2_{tag}_{VERSION}_{suffix}.json',evidence)
    if args.build:
        from package_ps2_stage30 import build
        final=build(BASE,VERSION,SOURCE_VERSION,('WND.BIN','FACEPACK.BIN'))
        prior=read_json(ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json');old={r['path']:r['target_sha256'] for r in prior['files']}
        changed=[r['path'] for r in final['files'] if r['target_sha256']!=old[r['path']]]
        assert changed==['/DATA/FIX00.DAT;1','/SLPS_253.45;1'],changed
        final.update(library_execution_checks=report,changed_from_previous=changed,pcsx2_visual_validation='pending for library screens',github_release=False)
        save(ROOT/'work/output'/f'ps2_font_{VERSION}_verification.json',final)

if __name__=='__main__':main()
