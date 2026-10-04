"""Build a patched ISO of SRW MX Portable (ULJS00041).

usage: python build_patch.py <original.iso> <version> [--scenes-file <merged.json> ...] [--native-font4x] [--text] [--battle] [--chapter-cards]
  --text  also insert the non-dialogue translations (BOOT.BIN strings, STATIC2_ADD.BIN, PARAM.SFO; insert_text.py)

Steps
  1. STATIC2_ADD.BIN : Latin glyphs drawn into the font atlas            (make_latin_font.py)
  2. BOOT.BIN        : VWF patch                                         (vwf_patch.py)
  3. MAP_ADD.BIN     : translated SRWL script blocks; the script area (sector 0x579C, 203 blocks)
                       is repacked, the block table in BOOT.BIN (0x27CA20, 204 x u32 sectors,
                       size = next - this) is rewritten and the MAP_ADD section table
                       (BOOT 0x2791F0, entries 11..17) is shifted by the growth   (docs/stage_map.md)
  4. ISO             : EBOOT.BIN = patched BOOT.BIN (plain ELF), files replaced, written to
                       work/output/SRWMX_EN_<version>.iso
"""
import glob, io, json, os, re, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pycdlib
import make_latin_font, vwf_patch, textfit

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SCRIPT_SECTOR = 0x579C
BLOCK_TABLE = 0x27CA20          # BOOT file offset
NBLOCKS = 203
SECTION_TABLE = 0x2791F0        # BOOT file offset, MAP_ADD sections
SCRIPT_SECTION = 10
SECTION_END = 17                # entry 17 = end of MAP_ADD (sectors)
MAX_BLOCK = 0x25000             # largest original block
# Script blocks are allocated at their exact size. The native map loader uses the scene
# controller's heap at +0x10040 (0x40000 bytes); other live allocations share that pool.
# The module+0x2F0E70 resource heap is unrelated. HARD_MAX_BLOCK is a build ceiling,
# not a guarantee of free space: native allocation/loading checks are required for growth.
# All five enlarged blocks in local 0.4.3 passed actual replacement allocation and ISO reads.
HARD_MAX_BLOCK = 0x40000
BIG_BLOCKS = []


def iso_read(iso, path):
    f = io.BytesIO()
    iso.get_file_from_iso_fp(f, iso_path=path)
    return f.getvalue()


def load_translations(files):
    """-> {scene name: {jp string: final game text}} from merged files with rows[].en filled.
    A row is applied only in the scenes listed in its `uses` (other blocks stay untouched: the
    game loads a script into a pool of unknown capacity, so blocks are not grown needlessly)."""
    out = {}
    for fn in files:
        d = json.load(open(fn, encoding='utf-8'))
        for r in d['rows']:
            en = r.get('en') or ''
            if not en.strip():
                continue
            jp = r['jp']
            if r['kind'] in ('dialogue', 'thought'):
                spk = r.get('speaker_en') or r.get('speaker_jp') or ''
                tail = jp.rstrip('@　 ')            # some lines carry a stray '@　' after the bracket
                close = tail[-1] if tail and tail[-1] in '」）' else ''
                o = '（' if r['kind'] == 'thought' else '「'
                lines, ok = textfit.wrap(spk + o, en, close)
                if not ok:
                    raise ValueError(f"{fn} row {r['id']} does not fit: {len(lines)} lines")
                text = '@'.join(lines)
            else:
                text = en
            for use in r.get('uses') or []:
                out.setdefault(use.split(':')[0], {})[jp] = text
    return out


def rebuild_block(raw, trans):
    """raw = original SRWL block bytes (padded). Returns new bytes (padded to 0x800) and count."""
    n, tab = struct.unpack_from('<2I', raw, 8)
    ptrs = struct.unpack_from(f'<{n}I', raw, tab)
    if not n:
        return raw, 0
    first = min(ptrs)
    strs = [raw[p:raw.index(b'\0', p)] for p in ptrs]
    head = bytearray(raw[:first])
    data, newp, done = bytearray(), [], 0
    for s in strs:
        jp = s.decode('cp932')
        if jp in trans:
            s = textfit.encode(trans[jp])
            done += 1
        newp.append(first + len(data))
        data += s + b'\0'
    struct.pack_into(f'<{n}I', head, tab, *newp)
    blk = bytes(head + data)
    blk += b'\0' * (-len(blk) % 0x800)
    if len(blk) > HARD_MAX_BLOCK:
        raise ValueError(f'block grew to {len(blk):#x} > {HARD_MAX_BLOCK:#x}')
    if len(blk) > MAX_BLOCK:
        BIG_BLOCKS.append(len(blk))
    return blk, done


def patch_map_add(map_add, boot, trans):
    b = bytearray(boot)
    rel = list(struct.unpack_from(f'<{NBLOCKS + 1}I', b, BLOCK_TABLE))
    base = SCRIPT_SECTOR * 0x800
    area = bytearray()
    newrel, total = [], 0
    names = {r['block']: r['name'] for r in json.load(
        open(os.path.join(ROOT, 'work/source/stage_map.json'), encoding='utf-8'))}
    for i in range(NBLOCKS):
        raw = map_add[base + rel[i] * 0x800: base + rel[i + 1] * 0x800]
        t = trans.get(names[i])
        nbig = len(BIG_BLOCKS)
        blk, done = rebuild_block(raw, t) if t else (raw, 0)
        if len(BIG_BLOCKS) > nbig:
            print(f'  NOTE scene {names[i]}: {len(blk):#x} bytes, above the largest original block '
                  f'({MAX_BLOCK:#x}; was {len(raw):#x})')
        total += done
        newrel.append(len(area) // 0x800)
        area += blk
    newrel.append(len(area) // 0x800)
    delta = newrel[-1] - rel[-1]
    old_end = base + rel[-1] * 0x800
    new = bytes(map_add[:base]) + bytes(area) + bytes(map_add[old_end:])
    struct.pack_into(f'<{NBLOCKS + 1}I', b, BLOCK_TABLE, *newrel)
    sec = list(struct.unpack_from(f'<{SECTION_END + 1}I', b, SECTION_TABLE))
    for k in range(SCRIPT_SECTION + 1, SECTION_END + 1):
        sec[k] += delta
    struct.pack_into(f'<{SECTION_END + 1}I', b, SECTION_TABLE, *sec)
    assert sec[SECTION_END] * 0x800 == len(new), (hex(sec[SECTION_END] * 0x800), hex(len(new)))
    print(f'script strings replaced: {total}; script area grew by {delta} sectors')
    return new, bytes(b)


def main(iso_path, version, *rest):
    out = os.path.join(ROOT, 'work', 'output', f'SRWMX_EN_{version}.iso')
    if os.path.exists(out):
        raise FileExistsError('Choose a new version/output; existing builds are preserved.')
    files = [rest[i + 1] for i in range(len(rest)) if rest[i] == '--scenes-file']
    if not files:
        files = sorted(glob.glob(os.path.join(ROOT, 'work/translation/en/script/*_merged.json')))
    iso = pycdlib.PyCdlib()
    iso.open(iso_path)
    boot = iso_read(iso, '/PSP_GAME/SYSDIR/BOOT.BIN')
    static2 = iso_read(iso, '/PSP_GAME/USRDIR/STATIC2_ADD.BIN')
    map_add = iso_read(iso, '/PSP_GAME/USRDIR/MAP_ADD.BIN')

    build = os.path.join(ROOT, 'work', 'build')
    os.makedirs(build, exist_ok=True)
    open(os.path.join(build, 'STATIC2_ADD.orig'), 'wb').write(static2)
    make_latin_font.main(os.path.join(build, 'STATIC2_ADD.orig'), os.path.join(build, 'STATIC2_ADD.BIN'))
    static2_new = open(os.path.join(build, 'STATIC2_ADD.BIN'), 'rb').read()

    trans = load_translations(files)
    map_new, boot = patch_map_add(map_add, boot, trans)

    if '--native-font4x' in rest:
        import native_font4x
        boot_new = native_font4x.patch_boot(boot, os.path.join(build, 'STATIC2_ADD.BIN'),
                                          os.path.join(build, 'native_font4x'))
    else:
        boot_new = vwf_patch.patch_boot(boot, os.path.join(build, 'STATIC2_ADD.BIN'))

    repl = {}
    if '--text' in rest:                            # non-dialogue text (tools/insert_text.py)
        import insert_text
        boot_new = insert_text.patch_boot(boot_new)
        static2_new, overflow = insert_text.patch_static2(static2_new)
        boot_new = insert_text.patch_overflow(boot_new, overflow)
        boot_new = insert_text.patch_centering(boot_new)
        repl['/PSP_GAME/PARAM.SFO'] = insert_text.patch_sfo(iso_read(iso, '/PSP_GAME/PARAM.SFO'))
        import redraw_banners                       # battle / status-effect banners, both copies
        static2_new = redraw_banners.patch(static2_new, 'STATIC2_ADD.BIN', os.path.join(build, 'banners.png'))
        assert len(redraw_banners.textures(map_new)) == len(redraw_banners.textures(map_add)), 'MAP_ADD textures moved'
        map_new = redraw_banners.patch(map_new, 'MAP_ADD.BIN')
        import insert_tiles                         # map cursor terrain names
        map_new = insert_tiles.patch(map_new)
        import redraw_wnd                           # battle / status icons (English letters)
        repl['/PSP_GAME/USRDIR/WND.BIN'] = redraw_wnd.patch_wnd(iso_read(iso, '/PSP_GAME/USRDIR/WND.BIN'),
                                                                os.path.join(build, 'wnd_icons.png'))

    big = {}
    if '--battle' in rest:                          # battle quotes (tools/battle_quotes.py)
        import battle_quotes
        src = os.path.join(build, 'BATTLE2.orig')
        if not os.path.exists(src) or os.path.getsize(src) != iso.get_record(
                iso_path='/PSP_GAME/USRDIR/BATTLE2.BIN').data_length:
            iso.get_file_from_iso(src, iso_path='/PSP_GAME/USRDIR/BATTLE2.BIN')
        dst = os.path.join(build, 'BATTLE2.BIN')
        static2_new, quote_overflow = battle_quotes.patch_battle2(src, dst, static2_new)
        boot_new = battle_quotes.patch_boot_quotes(boot_new, quote_overflow)
        big['/PSP_GAME/USRDIR/BATTLE2.BIN'] = dst

    chapter_results = None
    if '--chapter-cards' in rest:
        import patch_chapter_cards
        specs = json.load(open(os.path.join(ROOT, 'work/translation/en/ui/all_chapter_cards.json'), encoding='utf-8'))
        archive, chapter_results = patch_chapter_cards.patch_archive(
            iso_read(iso, patch_chapter_cards.ASSET), specs,
            patch_chapter_cards.ROOT / 'work/build/chapter_cards/english')
        repl[patch_chapter_cards.ASSET] = archive

    repl.update({'/PSP_GAME/SYSDIR/EBOOT.BIN': boot_new, '/PSP_GAME/SYSDIR/BOOT.BIN': boot_new,
                 '/PSP_GAME/USRDIR/STATIC2_ADD.BIN': static2_new, '/PSP_GAME/USRDIR/MAP_ADD.BIN': map_new})
    for path, data in repl.items():
        iso.rm_file(iso_path=path)
        iso.add_fp(io.BytesIO(data), len(data), iso_path=path)
    handles = []
    for path, local in big.items():                 # large files are streamed from disk
        iso.rm_file(iso_path=path)
        handles.append(open(local, 'rb'))
        iso.add_fp(handles[-1], os.path.getsize(local), iso_path=path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    iso.write(out)
    iso.close()
    for h in handles:
        h.close()
    if chapter_results is not None:
        report = dict(version=version, native_asset_patch=True, texture_replacement=False,
                      title_atlases_covered=len(chapter_results),
                      translated_atlases=sum(r['translated'] for r in chapter_results),
                      native_english_atlases_preserved=sum(not r['translated'] for r in chapter_results),
                      scenario_titles_covered=67, cards=chapter_results)
        with open(os.path.join(ROOT, 'work/output', f'chapter_cards_{version}_build.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=1)
    if '--native-font4x' in rest:
        import shutil
        shutil.copyfile(os.path.join(ROOT, 'incoming/fonts/FONT_LICENSE.txt'),
                        out[:-4] + '_FONT_LICENSE.txt')
    print('written', out)


if __name__ == '__main__':
    main(*sys.argv[1:])
