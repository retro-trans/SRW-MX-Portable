"""Verify the installed font atlas, VWF hooks and packaged test ISO."""
import hashlib
import io
import json
import struct
from pathlib import Path
import pycdlib
from PIL import Image, ImageDraw, ImageFont
import make_latin_font as glyphs
import textfit
import vwf_patch

ROOT = Path(__file__).resolve().parent.parent


def main(version, native=False):
    build = ROOT / 'work/build'
    original = (build / 'STATIC2_ADD.orig').read_bytes()
    atlas_path = build / 'STATIC2_ADD.BIN'
    atlas = atlas_path.read_bytes()
    assert len(original) == len(atlas)
    masks = {}
    for code in glyphs.CHARS:
        row, col = divmod(glyphs.slot(code), 14)
        for y in range(18):
            for x in range(18):
                px = col * 18 + x
                offset = glyphs.ATLAS + (row * 18 + y) * 128 + px // 2
                masks[offset] = masks.get(offset, 0) | (0xF0 if px & 1 else 0x0F)
    assert all(not ((before ^ after) & (~masks.get(index, 0) & 255))
               for index, (before, after) in enumerate(zip(original, atlas)))
    font = ImageFont.truetype(glyphs.FONT, glyphs.SIZE)
    ascent, _ = font.getmetrics()
    for char in glyphs.CHARS.values():
        canvas = Image.new('L', (40, 40))
        ImageDraw.Draw(canvas).text((11, 10 + glyphs.BASELINE - ascent), char, font=font, fill=255)
        bounds = canvas.point(lambda value: 255 if value >= 40 else 0).getbbox()
        assert not bounds or (bounds[0] >= 10 and bounds[1] >= 10 and bounds[2] <= 28 and bounds[3] <= 28), char
    iso = pycdlib.PyCdlib()
    iso_path = ROOT / ('work/output/SRWMX_EN_%s.iso' % version)
    iso.open(str(iso_path))
    def read(path):
        stream = io.BytesIO()
        iso.get_file_from_iso_fp(stream, iso_path=path)
        return stream.getvalue()
    assert read('/PSP_GAME/USRDIR/STATIC2_ADD.BIN') == atlas
    boot = read('/PSP_GAME/SYSDIR/BOOT.BIN')
    assert read('/PSP_GAME/SYSDIR/EBOOT.BIN') == boot
    table = vwf_patch.width_table(str(atlas_path))
    native_details = {}
    if native:
        import native_font4x
        layout = json.loads((build / 'native_font4x/layout.json').read_text())
        high, index, _ = native_font4x.atlas()
        code, hooks, relocs, _ = native_font4x.assemble(
            layout['table_va'], layout['index_va'], layout['atlas_va'], layout['code_va'])
        for va, expected in [(layout['table_va'], table), (layout['index_va'], index),
                             (layout['atlas_va'], high), (layout['code_va'], code)]:
            assert boot[0x60 + va:0x60 + va + len(expected)] == expected
        assert boot[0x60 + layout['original_filesz']:0x60 + layout['original_memsz']] == bytes(
            layout['original_memsz'] - layout['original_filesz'])
        phoff = struct.unpack_from('<I', boot, 28)[0]
        assert struct.unpack_from('<2I', boot, phoff + 16) == (layout['new_size'], layout['new_size'])
        shoff = struct.unpack_from('<I', boot, 32)[0]
        shsize, count, str_index = struct.unpack_from('<3H', boot, 46)
        strings = struct.unpack_from('<I', boot, shoff + str_index * shsize + 16)[0]
        found = set()
        for n in range(count):
            header = shoff + n * shsize
            name = struct.unpack_from('<I', boot, header)[0]
            if boot[strings + name:strings + name + 10] == b'.rel.text\0':
                off, size = struct.unpack_from('<2I', boot, header + 16)
                found = {struct.unpack_from('<2I', boot, off + k) for k in range(0, size, 8)}
        assert set(relocs).issubset(found)
        assert {(call, 4) for call in native_font4x.GLYPH_CALLS}.issubset(found)
        native_details = dict(native_font_scale=4, vector_render_size=60, cell_size=72,
                              upload_size=[512,128], native_atlas_bytes=len(high),
                              native_atlas_sha256=hashlib.sha256(high).hexdigest(),
                              additional_game_memory=layout['new_size']-layout['original_memsz'],
                              original_bss_retained=True, native_relocations_verified=True,
                              full_high_resolution_glyph_masks_verified=True,
                              texture_replacement_required=False)
    else:
        assert boot[0x60 + vwf_patch.TABLE:0x60 + vwf_patch.TABLE + len(table)] == table
        code, hooks, _ = vwf_patch.assemble(0)
        assert boot[0x60 + vwf_patch.CODE:0x60 + vwf_patch.CODE + len(code)] == code
    for offset, hook in hooks:
        assert boot[0x60 + offset:0x60 + offset + len(hook)] == hook
    iso.close()
    rows_checked, overflows = 0, []
    for stage in range(0, 31):
        filename = 'prologue_merged.json' if stage == 0 else 'stage%02d_campaign_full_merged.json' % stage
        rows = json.loads((ROOT / 'work/translation/en/script' / filename).read_text(encoding='utf-8'))['rows']
        for row in rows:
            rows_checked += 1
            if row['kind'] == 'plain':
                ok = all(textfit.px(line) <= 352 for line in row['en'].split('@'))
            else:
                ok = textfit.fit_dialogue(row['speaker_en'], row['en'], row['kind'] == 'thought')[2]
            if not ok:
                overflows.append(dict(stage=stage, id=row['id']))
    result = dict(version=version, font='Genei LateGo v2 Medium', size=glyphs.SIZE,
                  shadow=glyphs.SHADOW, font_sha256=hashlib.sha256(Path(glyphs.FONT).read_bytes()).hexdigest(),
                  atlas_sha256=hashlib.sha256(atlas).hexdigest(),
                  widths={char: textfit.px(char) for char in 'iMW01'},
                  non_latin_cells_unchanged=True, glyph_clipping=False,
                  iso_atlas_verified=True, vwf_table_and_eight_hooks_verified=True,
                  checked_rows=rows_checked, overflows=overflows,
                  emulator_boot_verified=False)
    result.update(native_details)
    (ROOT / ('work/output/font_%s_verification.json' % version)).write_text(json.dumps(result, indent=1), encoding='utf-8')
    print(json.dumps(result, indent=1))
    assert not overflows


if __name__ == '__main__':
    import sys
    main(sys.argv[1], '--native-font4x' in sys.argv[2:])
