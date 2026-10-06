"""Correct PSP Prologue opening, defeat retry and native researcher portrait.

Build 0.1.10 from 0.1.9 without replacing any campaign translations.
"""
import copy,json,shutil,struct
import keystone,pycdlib
from PIL import Image
from port_ps2_translations import ROOT,sha
from port_ps2_prologue import save
from ps2_translation_native import extend
import play_order

VERSION='0.1.10'
SOURCE_VERSION='0.1.9'
BASE=ROOT/'work/build/ps2'/f'prologue_fix_{VERSION}'
BIAS=0xff000


def portrait(static,faces):
    psp=(ROOT/'work/build/STATIC2_ADD.orig').read_bytes()
    source=ROOT/'work/source/ps2/prologue/FACEPACK_ADD.BIN'
    if not source.exists():
        iso=pycdlib.PyCdlib();iso.open(str(ROOT/'Super Robot Taisen MX Portable (Japan).iso'))
        iso.get_file_from_iso(local_path=str(source),iso_path='/PSP_GAME/USRDIR/FACEPACK_ADD.BIN');iso.close()
    packed=source.read_bytes();out=bytearray(faces);table=bytearray(static);evidence=[]
    assert table[0x177800+309*60:0x177800+310*60]==bytes(60)
    # ID 2110 = Pilt433's story group 21, portrait 10. PSP has a 128-byte
    # face descriptor; native PS2 has 60 bytes. Port only the used expressions.
    row=struct.unpack_from('<30h',psp,0x140e80)
    assert row[0]==2110 and row[2]==2104 and row[28]==2105
    native=list(row)
    for source_id,target_id,field in ((2104,2998,2),(2105,2999,28)):
        offset=struct.unpack_from('<I',psp,0x134400+source_id*4)[0]
        t,w,h,hs,ps,px,ns=struct.unpack_from('<7I',packed,offset+4)
        assert packed[offset:offset+4]==b'TX48' and (t,w,h,ps,ns)==(1,128,128,1024,16384)
        palette=packed[offset+hs:offset+hs+ps]
        pixels=packed[offset+px:offset+px+ns]
        # Preserve palette/index colours. Double the PSP's 128px native art
        # to the PS2's 256px face format; no emulator replacement texture.
        source_image=Image.frombytes('L',(w,h),pixels)
        pixels=source_image.resize((256,256),Image.Resampling.NEAREST).tobytes()
        # Inverse CSM1 palette permutation is the same involution.
        from ps2_graphics_port import logical_palette
        raw=logical_palette(palette)+pixels
        start=len(out);assert start%2048==0 and len(raw)==0x10400
        assert struct.unpack_from('<I',table,0x174800+target_id*4)[0]==0xffffffff
        struct.pack_into('<I',table,0x174800+target_id*4,start)
        out+=raw+bytes(-len(raw)%2048);native[field]=target_id
        evidence.append(dict(psp_face=source_id,native_face=target_id,offset=start,bytes=len(raw),sha256=sha(raw)))
        im=Image.new('RGBA',(256,256))
        im.putdata([tuple(palette[v*4:v*4+3])+(min(255,palette[v*4+3]*2),) for v in pixels])
        preview=ROOT/'work/ui/ps2/prologue_faces';preview.mkdir(exist_ok=True,parents=True)
        im.save(preview/f'Researcher_native_{target_id}.png')
    struct.pack_into('<30h',table,0x177800+309*60,*native)
    return bytes(table),bytes(out),dict(story_face_id=2110,descriptor_slot=309,assets=evidence,
        native_ps2_face_format=True,source_resolution=[128,128],native_resolution=[256,256],texture_replacement=False)


def retry_patch(elf,meta):
    elf=bytearray(elf);target=(int(meta['segment_va'],16)+meta['segment_bytes']+15)&~15
    # Native Game Over event 0x13d restores the start-of-battle state, then
    # retries only chapter 0/1, group 0. Include added group 4 in that rule.
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS64|keystone.KS_MODE_LITTLE_ENDIAN)
    # A MIPS conditional branch cannot reach the original function from the
    # added segment. Use local branch plus absolute jumps instead.
    code=bytes(ks.asm('''.set noreorder
        lw $v0, -0x4258($v0)
        addiu $at, $zero, -5
        and $v0, $v0, $at
        beqz $v0, retry
        addiu $a1, $zero, 6
        j 0x1f5e48
        nop
    retry:
        j 0x1f5e34
        nop
    ''',target)[0])
    elf,address=extend(elf,meta,code);assert address==target
    old=bytes(elf[0x1f5e28-BIAS:0x1f5e30-BIAS]);assert old==struct.pack('<2I',0x8c42bda8,0x14400006)
    new=struct.pack('<2I',0x08000000|(target>>2),0)
    elf[0x1f5e28-BIAS:0x1f5e30-BIAS]=new
    hook=dict(name='prologue_game_over_retry',va='0x1f5e28',old=old.hex(),new=new.hex())
    meta['hooks'].append(hook);meta['target_sha256']=sha(elf)
    return elf,dict(routine_va=hex(target),routine_bytes=len(code),hook=hook,
        native_game_over_event='0x13d',retry_chapters=[0,1],retry_groups=[0,4])


def prepare():
    BASE.mkdir(parents=True,exist_ok=True)
    previous=ROOT/'work/build/ps2/stage30_0.1.9'
    for name in ('SLPS_253.45','MAP.BIN','STAGE.BIN','FIX00.DAT','D2MAPH.BIN','PACKMAPC.BIN','STATIC.BIN',
                 'patch.json','difficulty.json','prologue.json','stage30.json'):
        shutil.copyfile(previous/name,BASE/name)
    meta=json.loads((BASE/'patch.json').read_text());info=json.loads((BASE/'stage30.json').read_text())
    prologue=json.loads((BASE/'prologue.json').read_text())
    elf=bytearray((BASE/'SLPS_253.45').read_bytes());maps=(BASE/'MAP.BIN').read_bytes()
    assert sha(elf)==meta['target_sha256']
    off=lambda va:int(meta['segment_offset'],16)+va-int(meta['segment_va'],16)
    sec=list(struct.unpack_from('<18I',elf,0x37e438))
    sectors=list(struct.unpack_from('<204I',elf,off(int(info['script_sector_table_va'],16))))
    blocks=[maps[(sec[10]+sectors[i])*2048:(sec[10]+sectors[i+1])*2048] for i in range(203)]
    psp=(ROOT/'work/build/MAP_ADD.orig').read_bytes();boot=(ROOT/'work/source/ps2/prologue/PSP_BOOT.BIN').read_bytes()
    psec=struct.unpack_from('<18I',boot,0x2791f0);ptab=struct.unpack_from('<204I',boot,0x27ca20)
    inventory={r['name']:r['block'] for r in json.loads((ROOT/'work/source/stage_map.json').read_text(encoding='utf8'))}
    changes=[]
    for name,index in (('i00r0b',193),('i00s0b',196)):
        pi=inventory[name];raw=psp[(psec[10]+ptab[pi])*2048:(psec[10]+ptab[pi+1])*2048]
        commands,text=play_order.load(raw,0);assert len(commands)==7 and not text
        changes.append(dict(scene=name,index=index,commands=7,translated_strings=0,target_sha256=sha(raw),
            bytes=len(raw),opening_redirect=False,psp_event_preserved=True))
        blocks[index]=raw
    rebuilt=bytearray(maps[:sec[10]*2048]);rel=[]
    for block in blocks:rel.append(len(rebuilt)//2048-sec[10]);rebuilt+=block
    rel.append(len(rebuilt)//2048-sec[10]);rebuilt+=maps[sec[11]*2048:]
    delta=rel[-1]-sectors[-1]
    for n in range(11,18):sec[n]+=delta
    assert sec[-1]*2048==len(rebuilt)
    struct.pack_into('<18I',elf,0x37e438,*sec)
    struct.pack_into('<193I',elf,0x381f40,*rel[:193])
    for count,table in ((204,info['script_sector_table_va']),(201,prologue['script_sector_table_va'])):
        struct.pack_into(f'<{count}I',elf,off(int(table,16)),*rel[:count])
    for record in prologue['new_scene_blocks']:
        if record['scene'] in ('i00r0b','i00s0b'):
            record.update(next(c for c in changes if c['scene']==record['scene']))
    original_path=ROOT/'work/source/ps2/FACEPACK.BIN'
    if not original_path.exists():
        iso=pycdlib.PyCdlib();iso.open(str(ROOT/'Super Robot Taisen MX (Japan).iso'))
        try:
            iso.get_file_from_iso(local_path=str(original_path),iso_path='/DATA/FACEPACK.BIN;1')
        finally:
            iso.close()
    original=original_path.read_bytes()
    static,faces,face_info=portrait((BASE/'STATIC.BIN').read_bytes(),original)
    elf,retry=retry_patch(elf,meta)
    prologue.update(version=VERSION,source_build=SOURCE_VERSION,opening_redirect=False,
        opening='PSP empty pre-battle event, then Hugo Wolf 1 radio call',researcher_portrait=face_info,game_over_retry=retry)
    info.update(version=VERSION,source_build=SOURCE_VERSION)
    (BASE/'SLPS_253.45').write_bytes(elf);(BASE/'MAP.BIN').write_bytes(rebuilt)
    (BASE/'STATIC.BIN').write_bytes(static);(BASE/'FACEPACK.BIN').write_bytes(faces)
    for name,data in (('patch',meta),('prologue',prologue),('stage30',info)):save(BASE/f'{name}.json',data)
    result=dict(version=VERSION,source_build=SOURCE_VERSION,opening_events=changes,game_over_retry=retry,researcher_portrait=face_info)
    save(BASE/'prologue_fix.json',result)
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');args=parser.parse_args()
    print(json.dumps(prepare(),indent=2))
    if args.build:
        from verify_ps2_stage30 import verify
        from verify_ps2_prologue_fix import verify as verify_fix
        from package_ps2_stage30 import build
        verify(BASE,VERSION);verify_fix();build(BASE,VERSION,SOURCE_VERSION,('FACEPACK.BIN',))
