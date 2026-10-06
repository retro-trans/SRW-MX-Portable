"""Optional native PSP balance and New Game selection for SLPS-25345.

Uses exact shared-unit database values, never modifies FIX00 in place.
Difficulty is serialized in unused settings-tail bytes before native checksums.
No emulator cheats, texture replacements, save conversion or release publication.
"""
import json
import struct
from pathlib import Path
import keystone
from ps2_font4x import FILE_BIAS
from ps2_translation_native import extend
from static2_extract import sections, strtable
from port_ps2_translations import ROOT, sha
import insert_text as it

TAIL_OFFSET = 0x3e0
MAGIC = 0x4442584d  # MXBD, followed by version 1 and mode 0/1.
VERSION = 1
BUILD_VERSION = '0.1.5'
YESNO_VTABLE = 0x488fa0
YESNO_VTABLE_BYTES = 0xd8  # Includes the four cursor geometry virtual methods.

def balance_data():
    ps2=(ROOT/'work/source/ps2/FIX00.DAT').read_bytes()
    psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    a=sections(ps2,0);b=sections(psp)
    an=strtable(ps2,a['Strg'][0],a['Strg'][2]);bn=strtable(psp,b['Strg'][0],b['Strg'][2])
    hp=[];rewards=[];changes=[]
    for i in range(512):
        x=a['Unit'][0]+12+124*i;y=b['Unit'][0]+12+124*i
        same=an[struct.unpack_from('<H',ps2,x)[0]]==bn[struct.unpack_from('<H',psp,y)[0]]
        old_hp=struct.unpack_from('<I',ps2,x+12)[0];new_hp=struct.unpack_from('<I',psp,y+12)[0]
        old_reward=struct.unpack_from('<H',ps2,x+26)[0];new_reward=struct.unpack_from('<H',psp,y+26)[0]
        hp.append(new_hp if same else old_hp);rewards.append(new_reward if same else old_reward)
        if same and (old_hp!=new_hp or old_reward!=new_reward):
            changes.append(dict(id=i,ps2_hp=old_hp,psp_hp=new_hp,ps2_reward=old_reward,psp_reward=new_reward))
    assert sum(c['ps2_hp']!=c['psp_hp'] for c in changes)==139
    assert sum(c['ps2_reward']!=c['psp_reward'] for c in changes)==294
    assert all(c['psp_hp']*2==c['ps2_hp']*3 for c in changes if c['psp_hp']!=c['ps2_hp'])
    assert all(c['psp_reward']*5==c['ps2_reward']*4 for c in changes if c['psp_reward']!=c['ps2_reward'])
    return hp,rewards,changes

def patch(original,data,metadata):
    hp,rewards,changes=balance_data()
    blob=bytearray(16)
    hp_off=len(blob);blob+=struct.pack('<512I',*hp)
    reward_off=len(blob);blob+=struct.pack('<512H',*rewards)
    table_off=len(blob);blob+=original[YESNO_VTABLE-FILE_BIAS:YESNO_VTABLE-FILE_BIAS+YESNO_VTABLE_BYTES]
    strings={}
    for key,text in [('question','Choose the game balance.'),('details','PSP: enemy HP +50%, funds -20%.'),
                     ('ps2','PS2 - Original'),('psp','PSP - Harder')]:
        strings[key]=len(blob);blob+=it.encode(text)
    data,pool=extend(data,metadata,blob)
    mode=pool;hp_va=pool+hp_off;reward_va=pool+reward_off;vtable=pool+table_off
    strings={k:pool+v for k,v in strings.items()}
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    hooks=[];routines={}

    def asm(name,source):
        current=(int(metadata['segment_va'],16)+metadata['segment_bytes']+15)&~15
        code=bytes(ks.asm('.set noreorder\n'+source,current)[0])
        nonlocal data
        data,va=extend(data,metadata,code);assert va==current
        routines[name]=dict(va=hex(va),bytes=len(code))
        return va

    def hook(name,site,target):
        nonlocal data
        off=site-FILE_BIAS;old=bytes(data[off:off+8])
        # All feature sites must still be original instructions, independent of text hooks.
        assert old==original[off:off+8],hex(site)
        new=struct.pack('<2I',0x08000000|(target>>2),0)
        data[off:off+8]=new
        hooks.append(dict(name=name,va=hex(site),old=old.hex(),new=new.hex(),target=hex(target)))

    for name,site,table,load,field in [('hp',0x332a10,hp_va,'lw',12),('reward',0x332af0,reward_va,'lhu',26)]:
        shift=2 if name=='hp' else 1
        target=asm(name,f'''
            li $at, {mode}
            lw $v0, 0($at)
            addiu $v1, $zero, 1
            bne $v0, $v1, normal
            nop
            sltiu $v0, $a1, 512
            beqz $v0, normal
            nop
            sll $v1, $a1, {shift}
            li $v0, {table}
            addu $v0, $v0, $v1
            jr $ra
            {load} $v0, 0($v0)
        normal:
            sll $v1, $a1, 5
            lw $v0, 0($a0)
            subu $v1, $v1, $a1
            sll $v1, $v1, 2
            addu $v0, $v0, $v1
            jr $ra
            {load} $v0, {12+field}($v0)
        ''')
        hook('difficulty_'+name,site,target)

    # An object-specific copy of the existing two-option window's vtable.
    # Only this New Game box gets a wider opening animation; all Yes/No windows retain theirs.
    # Use numeric $8 for the PS2's fifth argument: Keystone MIPS64 names $t0
    # as register 12 (N64), while this game's calling convention uses register 8.
    opening=asm('opening','''
        addiu $sp, $sp, -16
        move $a3, $a0
        addiu $v0, $zero, -1
        sd $ra, 0($sp)
        sw $v0, 0x26c($a3)
        addiu $a3, $a3, 0x210
        addiu $a1, $zero, 240
        addiu $a2, $zero, 74
        jal 0x14fbc8
        addiu $8, $zero, 5
        ld $ra, 0($sp)
        jr $ra
        addiu $sp, $sp, 16
    ''')
    base=int(metadata['segment_offset'],16)+vtable-int(metadata['segment_va'],16)
    struct.pack_into('<I',data,base+0x44,opening)
    # Change the first prompt's pointer. Its shared Japanese original remains intact.
    for addr,word in [(0x2bd084,0x3c050000|((strings['question']+0x8000)>>16)),
                      (0x2bd090,0x24a50000|(strings['question']&65535))]:
        off=addr-FILE_BIAS;old=bytes(data[off:off+4]);new=struct.pack('<I',word)
        data[off:off+4]=new;hooks.append(dict(name='difficulty_prompt',va=hex(addr),old=old.hex(),new=new.hex()))
    setup=asm('setup',f'''
        addiu $a0, $s4, 0x3e80
        li $a1, {strings['details']}
        jal 0x151a08
        addiu $a2, $zero, 7
        addiu $at, $s4, 0x40c0
        li $v0, {vtable}
        sw $v0, 0x24($at)
        li $v0, {strings['ps2']}
        sw $v0, 0x208($at)
        li $v0, {strings['psp']}
        sw $v0, 0x20c($at)
        addiu $v0, $zero, 200
        sw $v0, 0x9c($at)
        addiu $v0, $zero, 260
        sw $v0, 0xa0($at)
        addiu $v0, $zero, 18
        sw $v0, 0x200($at)
        sw $v0, 0x204($at)
        sw $zero, 0x194($at)
        lw $v0, 0x5694($s4)
        j 0x2bd238
        nop
    ''')
    hook('difficulty_menu_setup',0x2bd120,setup)
    accept=asm('accept',f'''
        lw $v1, 0x5698($s4)
        addiu $v0, $zero, 1
        bne $v1, $v0, resume
        nop
        lw $at, 0x569c($s4)
        sltiu $v0, $at, 2
        beqz $v0, resume
        nop
        li $v0, {mode}
        sw $at, 0($v0)
    resume:
        addiu $v0, $zero, 1
        j 0x2bd1c4
        nop
    ''')
    hook('difficulty_menu_accept',0x2bd1bc,accept)
    cleanup=asm('cleanup','''
        addiu $a0, $s4, 0x40c0
        jal 0x151ea8
        nop
        addiu $at, $s4, 0x40c0
        li $v0, 0x488fa0
        sw $v0, 0x24($at)
        sw $zero, 0x5698($s4)
        lw $v0, -0x50c0($gp)
        j 0x2bd2b4
        nop
    ''')
    hook('difficulty_menu_cleanup',0x2bd2ac,cleanup)

    # Save-tail original fields use [0,0xa4); [0xa4,0x3f8) is unconsumed padding.
    # Serializer callees at 336e50/80/b0/e0 write exactly 0x40/0x40/0x10/0x10.
    stamp=asm('save_stamp',f'''
        li $v0, {MAGIC}
        sw $v0, {TAIL_OFFSET}($s0)
        addiu $v0, $zero, {VERSION}
        sw $v0, {TAIL_OFFSET+4}($s0)
        li $v0, {mode}
        lw $v1, 0($v0)
        sltiu $v0, $v1, 2
        bnez $v0, valid
        nop
        move $v1, $zero
    valid:
        sw $v1, {TAIL_OFFSET+8}($s0)
        ld $s0, 0($sp)
        ld $s1, 8($sp)
        j 0x335ae0
        nop
    ''')
    hook('difficulty_save_stamp',0x335ad8,stamp)
    restore=asm('restore',f'''
        lw $v0, {TAIL_OFFSET}($a1)
        li $v1, {MAGIC}
        bne $v0, $v1, legacy
        nop
        lw $v0, {TAIL_OFFSET+4}($a1)
        addiu $v1, $zero, {VERSION}
        bne $v0, $v1, legacy
        nop
        lw $v1, {TAIL_OFFSET+8}($a1)
        sltiu $v0, $v1, 2
        bnez $v0, store
        nop
    legacy:
        move $v1, $zero
    store:
        li $v0, {mode}
        sw $v1, 0($v0)
        jr $ra
        nop
    ''')
    load=asm('settings_load',f'''
        addiu $sp, $sp, -16
        sd $ra, 0($sp)
        jal {restore}
        nop
        ld $ra, 0($sp)
        addiu $sp, $sp, 16
        addiu $sp, $sp, -80
        sd $s1, 0x38($sp)
        j 0x335eb8
        nop
    ''')
    hook('difficulty_settings_load',0x335eb0,load)
    # Restore before unit deserialization/recalculation, not after it.
    load_early=asm('scenario_load',f'''
        addiu $sp, $sp, -16
        sd $ra, 0($sp)
        ori $a1, $zero, 0xd608
        addu $a1, $a1, $s2
        jal {restore}
        nop
        ld $ra, 0($sp)
        addiu $sp, $sp, 16
        lw $v0, 0x318($s2)
        addiu $v0, $v0, 1
        j 0x13b858
        nop
    ''')
    hook('difficulty_scenario_load_early',0x13b850,load_early)
    metadata['hooks']+=hooks;metadata['target_sha256']=sha(data)
    report=dict(version=BUILD_VERSION,feature='Optional PSP balance at New Game',mode_va=hex(mode),
                hp_table_va=hex(hp_va),reward_table_va=hex(reward_va),vtable_va=hex(vtable),
                vtable_bytes=YESNO_VTABLE_BYTES,
                strings={k:hex(v) for k,v in strings.items()},routines=routines,hooks=hooks,
                balance_changes=changes,enemy_hp_changes=139,reward_changes=294,
                save_tail_offset=hex(TAIL_OFFSET),save_magic=hex(MAGIC),save_version=VERSION,
                original_saves_default='PS2',psp_only_unit_156_excluded=True,
                inputs=dict(ps2_database_sha256=sha((ROOT/'work/source/ps2/FIX00.DAT').read_bytes()),
                            psp_database_sha256=sha((ROOT/'work/build/STATIC2_ADD.orig').read_bytes())),
                scope='Shared enemy base HP and unit funds rewards; original PS2 campaign and one favorite-series selection retained',
                visual_validation='pending',save_reload_gameplay_validation='pending')
    return bytes(data),report

if __name__=='__main__':
    source=ROOT/'work/source/ps2/SLPS_253.45'
    base=ROOT/'work/build/ps2/font_0.1.3'
    out=ROOT/'work/build/ps2'/('difficulty_'+BUILD_VERSION);out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((base/'patch.json').read_text())
    data,report=patch(source.read_bytes(),(base/'SLPS_253.45').read_bytes(),meta)
    (out/'SLPS_253.45').write_bytes(data)
    (out/'patch.json').write_text(json.dumps(meta,indent=2)+'\n')
    (out/'difficulty.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('hooks','routines','balance_changes')},indent=2))
