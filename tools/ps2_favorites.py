"""Three native favorite-series choices, using the existing PS2 save bitset."""
import struct
import keystone
import insert_text as it
from ps2_font4x import FILE_BIAS
from ps2_translation_native import extend
from port_ps2_translations import sha

VERSION = '0.1.18'


def patch(original, data, meta):
    blob = bytearray(32)  # mask, count, ordered carousel indexes; no saved extension.
    strings = {}
    texts = {
        'intro': 'Choose 3 favorite series.',
        'bonus_exp': 'Their characters gain 1.5x EXP in battle,',
        'bonus_upgrades': 'and their units get +2 to every upgrade limit.',
        'confirm': 'Use these 3 favorites?',
        'controls': 'Confirm: pick/remove    Cancel: undo last pick',
        'empty': '--',
        **{f'count{i}': f'Favorite Series: {i} / 3' for i in range(4)},
        **{f'slot{i}': f'{i + 1}.' for i in range(3)},
    }
    for key, text in texts.items():
        strings[key] = len(blob)
        blob += it.encode(text)
    data, state = extend(data, meta, blob)
    strings = {k: state + v for k, v in strings.items()}
    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS64 | keystone.KS_MODE_LITTLE_ENDIAN)
    routines, hooks, words = {}, [], []

    def asm(name, source):
        nonlocal data
        va = (int(meta['segment_va'], 16) + meta['segment_bytes'] + 15) & ~15
        code = bytes(ks.asm('.set noreorder\n' + source, va)[0])
        data, actual = extend(data, meta, code)
        assert actual == va
        routines[name] = dict(va=hex(va), bytes=len(code), assembly=source)
        return va

    def word(site, value, name):
        nonlocal data
        data = bytearray(data)
        off = site - FILE_BIAS
        old = bytes(data[off:off + 4])
        new = struct.pack('<I', value)
        data[off:off + 4] = new
        words.append(dict(va=hex(site), old=old.hex(), new=new.hex(), name=name))

    def hook(site, target, name, call=False):
        off = site - FILE_BIAS
        assert data[off:off + (4 if call else 8)] == original[off:off + (4 if call else 8)]
        before = bytes(data[off:off + (4 if call else 8)])
        word(site, (0x0c000000 if call else 0x08000000) | (target >> 2), name)
        if not call:
            word(site + 4, 0, name + '_delay')
        hooks.append(dict(name=name, va=hex(site), old=before.hex(),
                          new=bytes(data[off:off + len(before)]).hex(), target=hex(target)))

    reset = asm('reset', f'''
        addiu $sp,$sp,-16
        sd $ra,0($sp)
        jal 0x1660d0
        nop
        li $v0,{state}
        sw $zero,0($v0)
        sw $zero,4($v0)
        sw $zero,8($v0)
        sw $zero,12($v0)
        sw $zero,16($v0)
        ld $ra,0($sp)
        jr $ra
        addiu $sp,$sp,16
    ''')
    hook(0x2bde64, reset, 'favorites_reset', True)
    choose = asm('choose', f'''
        addiu $sp,$sp,-32
        sd $ra,0($sp)
        jal 0x1661e0
        move $a0,$s0
        li $t8,{state}
        addiu $t9,$zero,1
        sllv $t9,$t9,$v0
        lw $v1,0($t8)
        lw $a1,4($t8)
        and $a2,$v1,$t9
        bnez $a2,remove
        lw $a0,0x3ac($s0)
        sltiu $a2,$a1,3
        beqz $a2,stay
        nop
        sll $a2,$a1,2
        addu $a2,$a2,$t8
        sw $a0,8($a2)
        addiu $a1,$a1,1
        or $v1,$v1,$t9
        sw $a1,4($t8)
        sw $v1,0($t8)
        addiu $a2,$zero,3
        bne $a1,$a2,stay
        nop
        ld $ra,0($sp)
        addiu $sp,$sp,32
        lw $s1,0x134($s0)
        bnez $s1,complete
        nop
        j 0x165ba0
        nop
    complete:
        j 0x165b84
        nop
    remove:
        nor $t9,$t9,$zero
        and $v1,$v1,$t9
        sw $v1,0($t8)
        move $a2,$zero
    find:
        sll $a3,$a2,2
        addu $a3,$a3,$t8
        lw $v0,8($a3)
        beq $v0,$a0,compact
        nop
        addiu $a2,$a2,1
        sltu $v0,$a2,$a1
        bnez $v0,find
        nop
        b stay
        nop
    compact:
        addiu $a1,$a1,-1
        sw $a1,4($t8)
    shift:
        sltu $v0,$a2,$a1
        beqz $v0,clear
        nop
        lw $v0,12($a3)
        sw $v0,8($a3)
        addiu $a2,$a2,1
        b shift
        addiu $a3,$a3,4
    clear:
        sw $zero,8($a3)
    stay:
        ld $ra,0($sp)
        addiu $sp,$sp,32
        j 0x165ba0
        nop
    ''')
    hook(0x165b78, choose, 'favorites_choose')
    cancel = asm('undo', f'''
        li $t8,{state}
        lw $v0,4($t8)
        beqz $v0,exit_menu
        nop
        addiu $sp,$sp,-32
        sd $ra,0($sp)
        addiu $v0,$v0,-1
        sw $v0,4($t8)
        sll $v1,$v0,2
        addu $v1,$v1,$t8
        lw $v0,8($v1)
        sw $zero,8($v1)
        lw $a1,0x3ac($s0)
        sw $a1,8($sp)
        sw $v0,0x3ac($s0)
        jal 0x1661e0
        move $a0,$s0
        lw $a1,8($sp)
        sw $a1,0x3ac($s0)
        li $t8,{state}
        addiu $v1,$zero,1
        sllv $v1,$v1,$v0
        nor $v1,$v1,$zero
        lw $v0,0($t8)
        and $v0,$v0,$v1
        sw $v0,0($t8)
        ld $ra,0($sp)
        addiu $sp,$sp,32
        lui $a0,0x3d
        j 0x165be0
        nop
    exit_menu:
        lw $a2,0x138($s0)
        lui $a0,0x3d
        bnez $a2,exit_event
        nop
        j 0x165be0
        nop
    exit_event:
        j 0x165bcc
        nop
    ''')
    hook(0x165bc0, cancel, 'favorites_undo')
    commit = asm('commit', f'''
        li $v0,{state}
        lw $v1,4($v0)
        addiu $a2,$zero,3
        bne $v1,$a2,done
        nop
        lw $v0,0($v0)
        lw $v1,0x5e8($a0)
        or $v0,$v0,$v1
        sw $v0,0x5e8($a0)
    done:
        jr $ra
        nop
    ''')
    hook(0x2be484, commit, 'favorites_commit', True)

    # A separate font-fitting helper keeps selected rows left aligned and
    # restores both font dimensions. Width/height scale together only if needed.
    fit = asm('fit_row', '''
        addiu $sp,$sp,-64
        sd $ra,56($sp)
        sd $a0,0($sp)
        sd $a1,8($sp)
        sw $a2,16($sp)
        sw $a3,20($sp)
        lw $t8,0($a0)
        sw $t8,24($sp)
        lw $t8,4($a0)
        sw $t8,28($sp)
        jal 0x131ba0
        nop
        lui $at,0x4406
        mtc1 $at,$f1
        c.ole.s $f0,$f1
        bc1t draw
        nop
        div.s $f2,$f1,$f0
        ld $a0,0($sp)
        lwc1 $f3,24($sp)
        mul.s $f3,$f3,$f2
        swc1 $f3,0($a0)
        lwc1 $f3,28($sp)
        mul.s $f3,$f3,$f2
        swc1 $f3,4($a0)
    draw:
        ld $a0,0($sp)
        ld $a1,8($sp)
        lw $a2,16($sp)
        lw $a3,20($sp)
        jal 0x130610
        addiu $8,$zero,-1
        ld $t8,0($sp)
        lw $t9,24($sp)
        sw $t9,0($t8)
        lw $t9,28($sp)
        sw $t9,4($t8)
        ld $ra,56($sp)
        jr $ra
        addiu $sp,$sp,64
    ''')
    # Render after the existing carousel title (including during scrolling).
    draw = f'''
        addiu $sp,$sp,-64
        sd $ra,56($sp)
        sd $s0,0($sp)
        sd $s1,8($sp)
        sd $s3,16($sp)
        lw $t8,0x190($s2)
        sw $t8,24($sp)
        lw $t8,0x194($s2)
        sw $t8,28($sp)
        move $a0,$s2
        lw $a1,0x9c($s2)
        lw $a2,0xa0($s2)
        addiu $a1,$a1,16
        addiu $a2,$a2,12
        addiu $a3,$zero,608
        jal 0x1438a0
        addiu $8,$zero,124
        li $t8,{state}
        lw $v0,4($t8)
        li $a1,{strings['count0']}
    '''
    for i in range(1,4):
        draw += f'addiu $v1,$zero,{i}\nbne $v0,$v1,count_next{i}\nnop\nli $a1,{strings[f"count{i}"]}\ncount_next{i}:\n'
    draw += f'''
        lui $t8,0x41a0
        sw $t8,0x190($s2)
        sw $t8,0x194($s2)
        addiu $a0,$s2,0x190
        lw $a2,0x9c($s2)
        lw $a3,0xa0($s2)
        addiu $a2,$a2,28
        addiu $a3,$a3,20
        jal {fit}
        nop
        lui $t8,0x4180
        sw $t8,0x190($s2)
        sw $t8,0x194($s2)
    '''
    for i in range(3):
        draw += f'''
        addiu $a0,$s2,0x190
        li $a1,{strings[f'slot{i}']}
        lw $a2,0x9c($s2)
        lw $a3,0xa0($s2)
        addiu $a2,$a2,28
        addiu $a3,$a3,{48+i*20}
        jal {fit}
        nop
        li $t8,{state}
        lw $v0,4($t8)
        sltiu $v0,$v0,{i+1}
        bnez $v0,empty{i}
        li $a1,{strings['empty']}
        lw $v0,{8+i*4}($t8)
        sll $v0,$v0,2
        li $a1,0x470d38
        addu $a1,$a1,$v0
        lw $a1,0($a1)
    empty{i}:
        addiu $a0,$s2,0x190
        lw $a2,0x9c($s2)
        lw $a3,0xa0($s2)
        addiu $a2,$a2,58
        addiu $a3,$a3,{48+i*20}
        jal {fit}
        nop
    '''
    draw += f'''
        lui $t8,0x4160
        sw $t8,0x190($s2)
        sw $t8,0x194($s2)
        addiu $a0,$s2,0x190
        li $a1,{strings['controls']}
        lw $a2,0x9c($s2)
        lw $a3,0xa0($s2)
        addiu $a2,$a2,28
        addiu $a3,$a3,112
        jal {fit}
        nop
        lw $t8,24($sp)
        sw $t8,0x190($s2)
        lw $t8,28($sp)
        sw $t8,0x194($s2)
        ld $s0,0($sp)
        ld $s1,8($sp)
        ld $s3,16($sp)
        ld $ra,56($sp)
        addiu $sp,$sp,64
        ld $s0,0x60($sp)
        ld $s1,0x68($sp)
        j 0x1660b8
        nop
    '''
    renderer = asm('render', draw)
    # 0x166040's scrolling branch targets 0x1660b4, so intercept both paths.
    hook(0x1660b0, renderer, 'favorites_render')

    # Repoint only this dialog's literals; other generic Is this OK? boxes stay.
    for high, low, key in [(0x2bdec8,0x2bdecc,'intro'),
                           (0x2bdedc,0x2bdee0,'bonus_exp'),
                           (0x2bdef0,0x2bdef8,'bonus_upgrades'),
                           (0x2be164,0x2be170,'confirm')]:
        target = strings[key]
        for site, immediate in [(high,(target+0x8000)>>16),(low,target&65535)]:
            old = struct.unpack_from('<I',data,site-FILE_BIAS)[0]
            word(site,(old&0xffff0000)|immediate,'favorites_'+key)
    # Branching to the old second epilogue load would skip the new hook.
    word(0x166040, 0x1440001b, 'favorites_render_while_scrolling')  # bnez v0,1660b0
    meta['hooks'] += hooks
    meta['target_sha256'] = sha(data)
    return bytes(data), dict(version=VERSION, feature='Three favorite series in both balance modes',
        state_va=hex(state), saved_mask_offset='0x5e8', scenario_buffer_offset='0x1008',
        save_format_changed=False, old_saves_preserve_existing_favorites=True,
        new_game_plus='Native favorite union is preserved; three distinct choices per setup.',
        strings={k:dict(va=hex(strings[k]),english=v) for k,v in texts.items()},
        routines=routines, hooks=hooks, instruction_words=words,
        controls='Confirm toggles a series. Third pick opens confirmation. No returns to editing. Cancel undoes last pick; at zero picks it cancels setup.',
        layout=dict(panel=[16,12,624,136],title=[28,20],rows=[[58,48],[58,68],[58,88]],
                    controls=[28,112],row_width=536),
        native_bonuses='Original EXP and upgrade-limit checks read all chosen bits without replacement.',
        visual_validation='pending', github_release=False)
