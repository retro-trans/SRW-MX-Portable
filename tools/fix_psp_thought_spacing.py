"""Add the speaker separator to existing PSP thought dialogue without retranslating.

Rebuild only affected SRWL string tables; commands and unrelated strings stay
byte-identical. Rewrap only when the added space exceeds the native row width.
"""
import argparse
import hashlib
import io
import json
import shutil
import struct
from pathlib import Path
import pycdlib
import build_patch as build
import textfit
from patch_wnd_headers import digest, file_digest

ROOT = Path(__file__).resolve().parents[1]
SPACE = textfit.encode(' ')
OPEN = '（'.encode('cp932')
QUOTE = '「'.encode('cp932')


def width(raw):
    widths, total, pos = textfit._widths(), 0, 0
    placeholders = [(p.encode('cp932'), n) for p,n in textfit.PLACEHOLDER_PX.items()]
    while pos < len(raw):
        ph = next(((p,n) for p,n in placeholders if raw.startswith(p,pos)),None)
        if ph:
            pos += len(ph[0]); total += ph[1]; continue
        assert raw[pos] >= 0x80, 'Unexpected raw ASCII/control in thought row'
        code = int.from_bytes(raw[pos:pos+2], 'big')
        total += widths.get(code, textfit.SIZE); pos += 2
    return total


def split(raw):
    pos = raw.find(OPEN)
    # A parenthesis within a spoken line or another row is not a thought prefix.
    if pos < 1 or QUOTE in raw[:pos] or '@' in raw[:pos].decode('cp932'):
        return None
    speaker = raw[:pos]
    if not speaker.decode('cp932').strip('　 '):
        return None
    return speaker, raw[pos+len(OPEN):]


def body_words(body):
    return [word.encode('cp932') for row in body.decode('cp932').split('@')
            for word in row.split('　') if word]


def line_bytes(raw):
    # 0x40 is also the second byte of SJIS spaces and other glyphs.
    # Split the decoded control character, never its byte inside a glyph.
    return [row.encode('cp932') for row in raw.decode('cp932').split('@')]


def fix_string(raw):
    parts = split(raw)
    if parts is None:
        return raw, False
    speaker, body = parts
    # Remove complete space tokens rather than bytes belonging to SJIS glyphs.
    while speaker.endswith(SPACE):
        speaker = speaker[:-len(SPACE)]
    prefix = speaker + SPACE + OPEN
    updated = prefix + body
    rewrapped = False
    if any(width(row) > textfit.LINE_PX for row in line_bytes(updated)):
        rows, current = [], prefix
        for word in body_words(body):
            candidate = current + (b'' if current in (prefix,SPACE) else SPACE) + word
            if width(candidate) <= textfit.LINE_PX:
                current = candidate
            else:
                rows.append(current); current = SPACE + word
        rows.append(current); updated = b'@'.join(rows); rewrapped = True
    assert len(line_bytes(updated)) <= textfit.MAX_LINES
    assert all(width(row) <= textfit.LINE_PX for row in line_bytes(updated))
    assert body_words(split(updated)[1]) == body_words(body), 'Thought wording changed'
    return updated, rewrapped


def patch_block(raw, block):
    n, table = struct.unpack_from('<II',raw,8)
    pointers = struct.unpack_from(f'<{n}I',raw,table)
    edits, strings = [], []
    for slot, p in enumerate(pointers):
        old = raw[p:raw.index(b'\0',p)]
        new, rewrapped = fix_string(old)
        strings.append(new)
        if new != old:
            edits.append(dict(block=block,slot=slot,rewrapped=rewrapped,
                              old_sha256=hashlib.sha256(old).hexdigest(),
                              new_sha256=hashlib.sha256(new).hexdigest(),
                              row_widths=[width(row) for row in line_bytes(new)]))
    if not edits:
        return raw, edits
    first = min(pointers); head = bytearray(raw[:first]); payload = bytearray(); newp = []
    for s in strings:
        newp.append(first+len(payload)); payload += s+b'\0'
    struct.pack_into(f'<{n}I',head,table,*newp)
    output = bytes(head+payload); output += bytes(-len(output)%2048)
    assert len(output) <= build.HARD_MAX_BLOCK
    commands = struct.unpack_from('<I',raw,4)[0]
    assert output[:32+48*commands] == raw[:32+48*commands], 'Commands changed'
    for slot,p in enumerate(newp):
        assert output[p:output.index(b'\0',p)] == strings[slot]
    return output, edits


def patch_map(boot, data):
    boot = bytearray(boot)
    old = struct.unpack_from('<204I',boot,build.BLOCK_TABLE)
    base = build.SCRIPT_SECTOR*2048
    area, new, edits, blocks = bytearray(), [], [], []
    for block in range(203):
        raw = data[base+old[block]*2048:base+old[block+1]*2048]
        replacement, changes = patch_block(raw,block)
        new.append(len(area)//2048); area += replacement; edits += changes
        if changes:
            blocks.append(dict(block=block,old_bytes=len(raw),new_bytes=len(replacement),rows=len(changes)))
    new.append(len(area)//2048)
    output = data[:base]+area+data[base+old[-1]*2048:]
    struct.pack_into('<204I',boot,build.BLOCK_TABLE,*new)
    sections = list(struct.unpack_from('<18I',boot,build.SECTION_TABLE))
    for i in range(build.SCRIPT_SECTION+1,build.SECTION_END+1):
        sections[i] += new[-1]-old[-1]
    struct.pack_into('<18I',boot,build.SECTION_TABLE,*sections)
    assert sections[-1]*2048 == len(output)
    assert output[:base] == data[:base] and output[base+new[-1]*2048:] == data[base+old[-1]*2048:]
    return bytes(boot),bytes(output),dict(rows_changed=len(edits),rows_rewrapped=sum(r['rewrapped'] for r in edits),
                                          affected_blocks=blocks,edits=edits,growth_sectors=new[-1]-old[-1])


def main(write=False):
    source = ROOT/'work/output/SRWMX_EN_0.4.11.iso'
    output = ROOT/'work/output/SRWMX_EN_0.4.12.iso'
    if write: assert not output.exists(), 'Preserve existing builds'
    iso = pycdlib.PyCdlib(); iso.open(str(source))
    def read(path):
        f=io.BytesIO();iso.get_file_from_iso_fp(f,iso_path=path);return f.getvalue()
    original_boot = read('/PSP_GAME/SYSDIR/BOOT.BIN')
    boot,map_data,report = patch_map(original_boot,read('/PSP_GAME/USRDIR/MAP_ADD.BIN'))
    report.update(version='0.4.12',base_version='0.4.11',local_build_only=True)
    folder=ROOT/'work/build/psp_spacing_0.4.12';folder.mkdir(exist_ok=True)
    if write:
        paths=[folder.rstrip('/')+'/'+str(name) for folder,_,files in iso.walk(iso_path='/') for name in files]
        before={p:file_digest(iso,p) for p in paths}
        replacements={'/PSP_GAME/USRDIR/MAP_ADD.BIN':map_data}
        if boot != original_boot:
            replacements.update({'/PSP_GAME/SYSDIR/BOOT.BIN':boot,'/PSP_GAME/SYSDIR/EBOOT.BIN':boot})
        for p,b in replacements.items():
            iso.rm_file(iso_path=p);iso.add_fp(io.BytesIO(b),len(b),iso_path=p)
        iso.write(str(output));iso.close()
        check=pycdlib.PyCdlib();check.open(str(output))
        for p in paths:
            assert file_digest(check,p)==(hashlib.sha256(replacements[p]).hexdigest() if p in replacements else before[p]),p
        check.close()
        with output.open('rb') as f:report['output_sha256']=digest(f)
        report['changed_iso_files']=sorted(replacements)
        report['unchanged_iso_files']=len(paths)-len(replacements)
        report['iso_readback_verified']=True
        shutil.copyfile(source.with_name(source.stem+'_FONT_LICENSE.txt'),output.with_name(output.stem+'_FONT_LICENSE.txt'))
        (folder/'BOOT.fixed.BIN').write_bytes(boot);(folder/'MAP.fixed.BIN').write_bytes(map_data)
        (ROOT/'work/output/psp_spacing_0.4.12_verification.json').write_text(json.dumps(report,indent=1))
    else:
        iso.close();(folder/'inspection.json').write_text(json.dumps(report,indent=1))
    print(json.dumps({k:v for k,v in report.items() if k not in ('edits','affected_blocks')},indent=1))
    print('Affected blocks:',len(report['affected_blocks']))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');main(p.parse_args().build)
