"""Verify exact native image-bank edits and preserve all unrelated resources."""
import json, struct
from fix_ps2_map_support import ROOT, BASE, PREVIOUS, VERSION, SOURCE_VERSION, LABELS
from port_ps2_translations import sha
from port_ps2_prologue import save
from ps2_map_label_pixels import decode, encode, ORDER
from ps2_graphics_port import p2ig_textures


def verify(base=BASE,version=VERSION):
    report=json.loads((base/'map_support.json').read_text())
    maps=(base/'MAP.BIN').read_bytes();old=(PREVIOUS/'MAP.BIN').read_bytes()
    assert sha(maps)==report['target_map_sha256'] and sha(old)==report['source_map_sha256']
    unchanged=[]
    for path in PREVIOUS.iterdir():
        if path.suffix in ('.BIN','.DAT','.45') and path.name!='MAP.BIN':
            before=path.read_bytes();after=(base/path.name).read_bytes()
            assert before==after,path.name
            unchanged.append(dict(name=path.name,sha256=sha(after)))
    elf=(base/'SLPS_253.45').read_bytes();sections=struct.unpack_from('<18I',elf,0x37e438)
    start,end=sections[16]*2048,sections[17]*2048
    rows={r['name']:r for r in p2ig_textures(maps[start:end])}
    checked=[]
    for record in report['labels']:
        row=rows[record['asset']];offset=start+row['offset']+row['pixel_offset']
        assert offset==int(record['pixel_offset'],16)
        before,after=old[offset:offset+2048],maps[offset:offset+2048]
        assert sha(before)==record['source_sha256'] and sha(after)==record['target_sha256']
        assert encode(decode(before))==before and encode(decode(after))==after
        a=start+row['offset'];z=a+row['pixel_offset']
        assert maps[a:z]==old[a:z]  # Header, dimensions and palette.
        checked.append(dict(asset=record['asset'],english=record['english'],
                            native_bank_relative_offset=hex(row['offset']),
                            native_upload_roundtrip=True,header_palette_equal=True))
    last=0
    for a,z in report['changed_pixel_ranges']:
        assert maps[last:a]==old[last:a];last=z
    assert maps[last:]==old[last:] and len(maps)==len(old)
    assert sorted(ORDER)==list(range(4096))
    # Native instruction/control-flow evidence is carried forward explicitly:
    # this build only replaces three image payloads and preserves all code/data.
    carried=[]
    for tag in ('prologue_fix','ui','ui_details','roster_system','setup_save'):
        source=ROOT/'work/output'/f'ps2_{tag}_{SOURCE_VERSION}_execution.json'
        evidence=json.loads(source.read_text())
        evidence.update(reused_for_build=version, evidence_source_build=SOURCE_VERSION,
                        reuse_reason='Executable and all non-MAP resources byte-identical; MAP differs only in three caption image payloads')
        save(ROOT/'work/output'/f'ps2_{tag}_{version}_execution.json',evidence)
        carried.append(source.name)
    result=dict(version=version,native_image_bank=16,labels=checked,
                exact_changed_ranges=report['changed_pixel_ranges'],unchanged_resources=unchanged,
                native_psmt4_psmct32_pixel_permutation_bijective=True,
                source_counters_and_layout_code_unchanged=True,
                carried_execution_evidence=carried,visual_validation='decoded assets pass; in-game pending',
                github_release=False)
    save(ROOT/'work/output'/f'ps2_map_support_{version}_verification.json',result)
    print(json.dumps(dict(version=version,labels_verified=len(checked),unrelated_resources_preserved=len(unchanged))))
    return result


if __name__=='__main__':verify()
