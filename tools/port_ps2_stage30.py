"""Port PSP chapter 29/30 events onto the native PS2 campaign; local builds only."""
import argparse
import copy
import json
import struct
from pathlib import Path

import pycdlib
import keystone
import build_patch
import export_rows
import insert_text as it
import play_order
import patch_chapter_cards as cards
from ps2_graphics_port import logical_palette
from ps2_translation_native import extend
from static2_extract import sections, strtable
from port_ps2_prologue import raw_strings, save
from port_ps2_translations import ROOT, sha

VERSION = '0.1.9'
SOURCE_VERSION = '0.1.8'
SCENES = ('i056a', 'i056b', 's0560', 'i057a', 'i057b', 's0570')
BASE = ROOT/'work/build/ps2'/('stage30_'+VERSION)
BIAS = 0xff000


def patch_stage(original, psp):
    offsets = list(struct.unpack_from('<5I', original)) + [len(original)]
    parts = [bytearray(original[a:b]) for a, b in zip(offsets, offsets[1:])]
    assert len(parts[2]) == 68*136 and len(parts[3]) == 68*128
    # Seven native location slots already exist; use the final slot, without
    # growing campaign state or shifting any existing scenario IDs.
    chapter = 7*88+56
    assert struct.unpack_from('<8I', parts[1], chapter) == (6,29,30,31,32,33,34,0)
    struct.pack_into('<8I', parts[1], chapter, 7,29,30,31,32,33,68,34)
    loc = bytearray(psp[0x1fd3f0+66*136:0x1fd3f0+67*136])
    loc[4:68] = it.encode('Desert').ljust(64,b'\0')
    loc[84:96] = it.encode('Land').ljust(12,b'\0')
    assert struct.unpack_from('<4I', loc, 96) == (66,1,66,0)
    struct.pack_into('<4I', loc, 96, 68,1,68,0)
    parts[2] += loc
    rec = bytearray(psp[0x1ff898+66*128:0x1ff898+67*128])
    assert struct.unpack_from('<4I',rec) == (7,7,12,13)
    for start in (16,72):
        rec[start:start+56] = it.encode('What Gnaws at the "Heart"').ljust(56,b'\0')
        parts[3][34*128+start:34*128+start+56] = it.encode('Zeorymer Sorties at Dawn').ljust(56,b'\0')
    parts[3] += rec
    summaries = parts[4]
    assert struct.unpack_from('<I',summaries)[0] == 68
    texts = [bytes(summaries[p:summaries.index(0,p)+1])
             for p in struct.unpack_from('<68I',summaries,4)]
    tr = json.loads((ROOT/'work/translation/en/static2/scenario.json').read_text(encoding='utf8'))
    for ident in (34,66):
        lines = it.wrap(it.clean(tr['summaries'][str(ident)]),448)
        assert len(lines)<=4
        raw = it.encode('＠'.join(lines))
        if ident==34: texts[34]=raw
        else: texts.append(raw)
    blob=bytearray();ptrs=[]
    for raw in texts:ptrs.append(4+69*4+len(blob));blob+=raw
    parts[4] = struct.pack('<I',69)+struct.pack('<69I',*ptrs)+blob
    out=bytearray(20);new=[]
    for part in parts:new.append(len(out));out+=part
    struct.pack_into('<5I',out,0,*new)
    return bytes(out)


def deployments(psp, sec, original_fix):
    result={}
    for name,index in [('s0560',150),('s0570',152)]:
        matches=[];at=sec[9]*2048
        while (at:=psp.find(b'UNTD',at,sec[10]*2048))>=0:
            if struct.unpack_from('<I',psp,at+4)[0]==910 and psp[at+24:at+32].split(b'\0')[0]==name.encode():
                n=struct.unpack_from('<I',psp,at+40)[0]
                end=at+((44+n*192+2047)//2048)*2048
                matches.append(psp[at:end])
            at+=4
        assert len(matches)==1,name
        raw=matches[0];assert struct.unpack_from('<2I',raw,4)==(910,90)
        result[index]=raw
    # Database IDs in deployment records are native on both platforms. Only
    # the previously empty enemy Dragoon row 156 requires an added PS2 row.
    pfix=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    ps=sections(pfix);ns=sections(original_fix,0)
    pnames=strtable(pfix,ps['Strg'][0],ps['Strg'][2])
    nnames=strtable(original_fix,ns['Strg'][0],ns['Strg'][2])
    for raw in result.values():
        for i in range(struct.unpack_from('<I',raw,40)[0]):
            unit,pilot=struct.unpack_from('<I',raw,44+i*192)[0],struct.unpack_from('<i',raw,44+i*192+32)[0]
            for tag,size,ident in [('Unit',124,unit),('Pilt',184,pilot)]:
                if ident<0:continue
                assert ident<512
                a=struct.unpack_from('<H',pfix,ps[tag][0]+12+ident*size)[0]
                b=struct.unpack_from('<H',original_fix,ns[tag][0]+12+ident*size)[0]
                assert pnames[a]==nnames[b] or (tag,ident) in [('Unit',156),('Pilt',431),('Pilt',432),('Pilt',433)],(tag,ident)
    return result


def enemy_dragoon(fix):
    data=bytearray(fix);sec=sections(data,0);start=sec['Unit'][0]+12
    assert data[start+156*124:start+157*124]==bytes(124)
    # PS2 enemy Dragoon 69 has the same model and weapon definitions. PSP's
    # duplicate refers to PSP attack-animation IDs, so use the native record.
    data[start+156*124:start+157*124] = data[start+69*124:start+70*124]
    psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes();ps=sections(psp)
    start=sec['Pilt'][0]+12
    template=bytes(data[start+315*184:start+316*184])
    for ident in (431,432):
        assert data[start+ident*184:start+(ident+1)*184]==bytes(184)
        rec=bytearray(psp[ps['Pilt'][0]+12+ident*184:ps['Pilt'][0]+12+(ident+1)*184])
        # Full/short/reading/call-sign references use existing native Aqua
        # strings; portrait, library and voice IDs already match PS2 Aqua.
        for field in (0,2,16,164):rec[field:field+2]=template[field:field+2]
        assert rec[14:16]==template[14:16] and rec[166:168]==template[166:168]
        data[start+ident*184:start+(ident+1)*184]=rec
    return bytes(data)


def native_extras(elf,meta,difficulty):
    hooks=[]
    def word(site,value,name):
        off=site-BIAS;old=bytes(elf[off:off+4]);new=struct.pack('<I',value)
        elf[off:off+4]=new;hooks.append(dict(name=name,va=hex(site),old=old.hex(),new=new.hex()))
    # Card index 166 is unused and below the native player's 200-entry limit.
    elf,pointer=extend(elf,meta,struct.pack('<8i',129,130,131,132,133,134,166,-1))
    assert struct.unpack_from('<I',elf,0x4826cc-BIAS)[0]==0x4bcf10
    word(0x4826cc,pointer,'stage30_chapter_card_list')
    # Objective callers use deployment group/2, whereas history already uses
    # the actual location index. Remap these two callers only.
    target=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm('''.set noreorder
        lw $v0, 0x3a8($a0)
        sltiu $v1, $v0, 2
        beqz $v1, later
        nop
        addiu $v1, $zero, 2
        beq $a1, $v1, prologue
        nop
        addiu $a1, $a1, 1
        j 0x3473d0
        nop
    prologue:
        j 0x3473d0
        move $a1, $zero
    later:
        addiu $v1, $zero, 7
        bne $v0, $v1, done
        nop
        addiu $v1, $zero, 6
        beq $a1, $v1, before
        nop
        addiu $v1, $zero, 5
        bne $a1, $v1, done
        nop
        addiu $a1, $zero, 6
        b done
        nop
    before:
        addiu $a1, $zero, 5
    done:
        j 0x3473d0
        nop
    ''',target)[0])
    elf,va=extend(elf,meta,code);assert va==target
    for site in (0x224f18,0x2fe7d0):
        assert struct.unpack_from('<I',elf,site-BIAS)[0]==0x0c000000|(0x3473d0>>2)
        word(site,0x0c000000|(target>>2),'stage30_objective_title_lookup')
    # The new enemy has native PS2 stats in FIX00 and its exact PSP rewards
    # in the optional balance tables. Other 511 rows keep their values.
    psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes();s=sections(psp)
    off=s['Unit'][0]+12+156*124
    fields={}
    for key,size,offset,fmt in [('hp_table_va',4,12,'I'),('reward_table_va',2,26,'H')]:
        value=struct.unpack_from('<'+fmt,psp,off+offset)[0]
        at=int(meta['segment_offset'],16)+int(difficulty[key],16)-int(meta['segment_va'],16)+156*size
        old=bytes(elf[at:at+size]);new=struct.pack('<'+fmt,value);elf[at:at+size]=new
        hooks.append(dict(name='stage30_dragoon_balance',va=hex(int(difficulty[key],16)+156*size),old=old.hex(),new=new.hex()))
        fields['psp_hp' if size==4 else 'psp_reward']=value
    difficulty['psp_only_unit_156_excluded']=False
    difficulty['added_enemy_dragoon']=dict(id=156,native_template_id=69,**fields)
    assert not any(row['id']==156 for row in difficulty['balance_changes'])
    difficulty['balance_changes'].append(dict(id=156,ps2_hp=3900,psp_hp=fields['psp_hp'],ps2_reward=2500,psp_reward=fields['psp_reward']))
    difficulty['reward_changes']+=1
    difficulty['scope']='Shared enemy base HP and funds rewards, including added Dragoon 156; both PSP extra scenarios present'
    meta['hooks']+=hooks;meta['target_sha256']=sha(elf)
    return elf,hooks,dict(objective_title_wrapper_va=hex(target),**fields)


def title_graphics(pack,static):
    data=bytearray(pack);table=bytearray(static)
    desc=list(struct.unpack_from('<11I',table,0x1a6e78+134*44))
    end=struct.unpack_from('<I',table,0x1a6e78+135*44)[0]
    assert desc[0]==0x2ee0000 and end==0x2f62000
    clone=bytearray(pack[desc[0]:end]);start=len(data)
    assert start%2048==0
    def title(buffer,offset,text):
        mask,layout=cards.render_title(text)
        palette=logical_palette(buffer[offset-1024:offset])
        encoded=cards.indexed_title(mask,palette)
        buffer[offset:offset+len(encoded)]=encoded
        return layout
    layouts=[]
    for absolute in (0x2f20400,0x2f51c00):
        layouts.append(title(clone,absolute-desc[0],'What Gnaws at the "Heart"'))
    data+=clone
    assert bytes(table[0x1a6e78+166*44:0x1a6e78+167*44])==b'\xff'*44
    relocated=[start+value-desc[0] if value!=0xffffffff else value for value in desc]
    struct.pack_into('<11I',table,0x1a6e78+166*44,*relocated)
    # The new Aqua variants reuse her native, translated battle caption bank.
    for ident in (431,432):
        assert struct.unpack_from('<I',table,0x1b8174+ident*4)[0]==0xffffffff
        table[0x1b8174+ident*4:0x1b8174+(ident+1)*4]=table[0x1b8174+315*4:0x1b8174+316*4]
    for absolute in (0x2f20400,0x2f51c00,0x4261c00):
        title(data,absolute,'Zeorymer Sorties at Dawn')
    return bytes(data),bytes(table),dict(animation_id=166,animation_bytes=len(clone),
        animation_offset=start,descriptor=relocated,english='What Gnaws at the "Heart"',
        stage30_english='Zeorymer Sorties at Dawn',title_layouts=layouts,
        texture_replacement=False,native_ps2_animation=True)


def prepare():
    BASE.mkdir(parents=True,exist_ok=True)
    previous=json.loads((ROOT/'work/output'/f'ps2_font_{SOURCE_VERSION}_verification.json').read_text(encoding='utf8'))
    source=ROOT/previous['output'];iso=pycdlib.PyCdlib();iso.open(str(source))
    def read(path):
        with iso.open_file_from_iso(iso_path=path) as f:return f.read()
    meta=copy.deepcopy(previous['font']);difficulty=copy.deepcopy(previous['difficulty'])
    elf=bytearray(read('/SLPS_253.45;1'));assert sha(elf)==meta['target_sha256']
    maps=read('/DATA/MAP.BIN;1');sec=list(struct.unpack_from('<18I',elf,0x37e438))
    psp=(ROOT/'work/build/MAP_ADD.orig').read_bytes();boot=(ROOT/'work/source/ps2/prologue/PSP_BOOT.BIN').read_bytes()
    psec=struct.unpack_from('<18I',boot,0x2791f0);pscripts=struct.unpack_from('<204I',boot,0x27ca20)
    pfix=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    native_fix=(ROOT/'work/source/ps2/FIX00.DAT').read_bytes()
    new_units=deployments(psp,psec,native_fix)
    map_table=struct.unpack_from('<1001I',elf,0x37f060)
    a=maps[(sec[7]+map_table[90])*2048:(sec[7]+map_table[91])*2048]
    b=psp[(psec[7]+map_table[90])*2048:(psec[7]+map_table[91])*2048]
    assert a[:36]==b[:36] and struct.unpack_from('<2I',a,8)==(24,32)
    assert all(a[32+i*8:36+i*8]==b[32+i*8:36+i*8] for i in range(24*32))
    # Native heights belong to the PS2 map renderer. Retain all map bytes.
    units=struct.unpack_from('<1001I',elf,0x380f98);deploy=bytearray();unit_offsets=[]
    for i in range(1000):
        unit_offsets.append(len(deploy)//2048)
        raw=maps[(sec[9]+units[i])*2048:(sec[9]+units[i+1])*2048]
        if i==152:assert not raw
        deploy+=new_units.get(i,raw)
    unit_offsets.append(len(deploy)//2048)
    deploy+=maps[(sec[9]+units[-1])*2048:sec[10]*2048]
    struct.pack_into('<1001I',elf,0x380f98,*unit_offsets)
    old_report=previous['prologue']
    def offset(va):return int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
    old_table=int(old_report['script_sector_table_va'],16)
    old_names=int(old_report['script_name_table_va'],16)
    rel=struct.unpack_from('<201I',elf,offset(old_table));ptrs=struct.unpack_from('<200I',elf,offset(old_names))
    names=[bytes(elf[offset(p):elf.index(0,offset(p))]).decode('ascii') for p in ptrs]
    blocks=[maps[(sec[10]+rel[i])*2048:(sec[10]+rel[i+1])*2048] for i in range(200)]
    inventory={r['name']:r['block'] for r in json.loads((ROOT/'work/source/stage_map.json').read_text(encoding='utf8'))}
    translations=build_patch.load_translations([str(ROOT/'work/translation/en/script'/f'stage{n}_campaign_full_merged.json') for n in (29,56)])
    scenes=[]
    # PSP opcode 179 switches/waits for the BFACEPAK portrait cache. Its
    # function pointer is an ELF virtual address (file offset = VA + 0x60).
    # PS2 uses its own resident portrait assets; the added Aqua rows reuse
    # native portrait 315. Use the actual PS2 no-op 178, never opcode 0,
    # which waits on the dialogue window and can stall event progression.
    assert struct.unpack_from('<I',boot,0x280a24+179*12)[0]==0xae3b8
    assert b'BFACEPAK_ADD.BIN' in boot[0x27f314:0x27f350]
    assert elf[0x306a84-BIAS:0x306a90-BIAS]==struct.pack('<3I',0x24020002,0x03e00008,0x27bd0030)
    for name in SCENES:
        i=inventory[name];raw=psp[(psec[10]+pscripts[i])*2048:(psec[10]+pscripts[i+1])*2048]
        commands,texts=play_order.load(raw,0)
        missing=[j for j,t in enumerate(texts) if export_rows.classify(t) and t not in translations.get(name,{})]
        assert not missing,(name,missing)
        block,count=build_patch.rebuild_block(raw,translations.get(name,{}));block=bytearray(block)
        noops=[]
        for j,command in enumerate(commands):
            if command[0]==179:
                # Keep all event/jump indexes and every operand unchanged.
                struct.pack_into('<I',block,32+j*48,178);noops.append(j)
            else:assert 0<=command[0]<179
        current,_=play_order.load(block,0)
        assert all(new[1:]==old[1:] and new[0]==(178 if old[0]==179 else old[0]) for new,old in zip(current,commands))
        assert len(block)<=0x25000
        if name in names:blocks[names.index(name)]=bytes(block)
        else:names.append(name);blocks.append(bytes(block))
        scenes.append(dict(scene=name,index=names.index(name),commands=len(commands),bytes=len(block),
                           translated_strings=count,source_sha256=sha(raw),target_sha256=sha(block),
                           psp_portrait_cache_commands=noops))
    result=bytearray(maps[:sec[9]*2048]);result+=deploy;script_base=len(result)//2048;new_rel=[]
    for block in blocks:new_rel.append(len(result)//2048-script_base);result+=block
    new_rel.append(len(result)//2048-script_base);result+=maps[sec[11]*2048:]
    growth=len(deploy)//2048-(sec[10]-sec[9]);scripts_growth=new_rel[-1]-(sec[11]-sec[10])
    sec[10]+=growth
    for i in range(11,18):sec[i]+=growth+scripts_growth
    assert sec[-1]*2048==len(result)
    struct.pack_into('<18I',elf,0x37e438,*sec)
    struct.pack_into('<193I',elf,0x381f40,*new_rel[:193])
    pool=bytearray(struct.pack('<204I',*new_rel));name_offset=len(pool);pool+=bytes(204*4)
    start=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    pointers=[]
    for name in names:pointers.append(start+len(pool));pool+=name.encode()+b'\0'
    struct.pack_into('<204I',pool,name_offset,*pointers,0)
    elf,table=extend(elf,meta,pool);assert table==start
    hooks=[]
    def address(hi_site,lo_site,target,label):
        for site,half in [(hi_site,(target+0x8000)>>16),(lo_site,target&65535)]:
            off=site-BIAS;old=bytes(elf[off:off+4]);v=struct.unpack('<I',old)[0]
            new=struct.pack('<I',(v&0xffff0000)|half);elf[off:off+4]=new
            hooks.append(dict(name=label,va=hex(site),old=old.hex(),new=new.hex()))
    for hi,lo,target,label in [(0x339754,0x33975c,table+name_offset,'stage30_script_names'),
        (0x339588,0x339594,table,'stage30_script_sizes'),(0x3396f4,0x3396fc,table,'stage30_script_reads'),
        (0x306bdc,0x306bec,table+name_offset,'stage30_debug_names')]:address(hi,lo,target,label)
    meta['hooks']+=hooks
    elf,extra_hooks,native=native_extras(elf,meta,difficulty);hooks+=extra_hooks
    thumbs=bytearray(read('/DATA/D2MAPH.BIN;1'))
    thumbs[(7*32+12)*16:(7*32+13)*16]=thumbs[(7*32+10)*16:(7*32+11)*16]
    pack,static,graphics=title_graphics(read('/DATA/PACKMAPC.BIN;1'),read('/DATA/STATIC.BIN;1'))
    resources={'/SLPS_253.45;1':bytes(elf),'/DATA/MAP.BIN;1':bytes(result),
        '/DATA/STAGE.BIN;1':patch_stage(read('/DATA/STAGE.BIN;1'),pfix),
        '/DATA/FIX00.DAT;1':enemy_dragoon(read('/DATA/FIX00.DAT;1')),
        '/DATA/D2MAPH.BIN;1':bytes(thumbs),'/DATA/PACKMAPC.BIN;1':pack,'/DATA/STATIC.BIN;1':static}
    iso.close()
    for path,data in resources.items():(BASE/path.rsplit('/',1)[-1].split(';')[0]).write_bytes(data)
    # Superseded table-pointer hooks retain their original baseline bytes but
    # verify the current value, rather than both the old and new pointers.
    merged={}
    for hook in meta['hooks']:
        key=hook['va']
        if key in merged:
            original=merged[key]['old'];merged[key]=dict(hook,old=original)
        else:merged[key]=hook
    meta['hooks']=list(merged.values())
    meta['target_sha256']=sha(elf)
    prologue=copy.deepcopy(previous['prologue'])
    prologue.update(version=VERSION,script_sector_table_va=hex(table),script_name_table_va=hex(table+name_offset),
                    stage30_port='included with PSP reworked stage 29',objective_footer_titles_fixed=True)
    save(BASE/'prologue.json',prologue)
    save(BASE/'patch.json',meta);save(BASE/'difficulty.json',difficulty)
    report=dict(version=VERSION,source_build=SOURCE_VERSION,scene_count=203,scenes=scenes,
        script_sector_table_va=hex(table),script_name_table_va=hex(table+name_offset),
        scenario_id=68,location_id=68,chapter=7,location_order=[29,30,31,32,33,68,34],
        story_order=[dict(number=29,group=12,scene='s0570',title='What Gnaws at the "Heart"'),
                     dict(number=30,group=10,scene='s0560',title='Zeorymer Sorties at Dawn')],
        native_map_id=90,native_map_dimensions=[24,32],all_terrain_ids_match=True,
        ps2_map_bytes_preserved=True,psp_portrait_cache_adapted_without_changing_jump_indexes=True,
        deployments=[dict(scene='s0570',chapter=7,group=12,units=132),dict(scene='s0560',chapter=7,group=10,units=46)],
        added_unit=dict(id=156,template_id=69,name='Dragoon',native_weapons=[301,302,303,304]),
        added_pilots=[dict(id=431,name='Aqua',native_portrait=315,native_caption_bank=315),
                      dict(id=432,name='Aqua',native_portrait=315,native_caption_bank=315)],
        original_scenario_ids_preserved=True,prologue_preserved=True,graphics=graphics,
        native=native,hooks=hooks,existing_save_migration='not implemented; new games only',
        gameplay_validation='pending',github_release=False)
    save(BASE/'stage30.json',report)
    print(json.dumps(dict(prepared=True,version=VERSION,scenes=203,heap_start=meta['heap_start'],new_map_bytes=len(result)),indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    prepare()
    if not args.prepare_only:
        from verify_ps2_stage30 import verify
        verify()
        from package_ps2_stage30 import build
        build()
