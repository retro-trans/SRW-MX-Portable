"""Normalize only verified later name/icon edits for older regression fixtures."""
import json
from port_ps2_translations import sha


def baseline_bytes(base,name):
    from ps2_library_preservation import baseline_bytes as before_library
    raw=before_library(base,name)
    banner_report=base/'battle_banners.json'
    if name=='STATIC.BIN' and banner_report.exists():
        from patch_battle_banners import ROOT, patch
        report=json.loads(banner_report.read_text())
        native=(ROOT/'work/source/ps2/STATIC.BIN').read_bytes()
        restored=bytearray(raw)
        for a,z in report['pixel_ranges']:restored[a:z]=native[a:z]
        assert patch(restored,'PS2')[0]==raw
        raw=bytes(restored)
    hud_report=base/'battle_hud.json'
    if name=='STATIC.BIN' and hud_report.exists():
        from patch_battle_hud import ROOT, patch
        report=json.loads(hud_report.read_text())
        native=(ROOT/'work/source/ps2/STATIC.BIN').read_bytes()
        restored=bytearray(raw)
        for a,z in report['pixel_ranges']:restored[a:z]=native[a:z]
        # Re-applying the independently guarded rectangles must reproduce all
        # current bytes, including any earlier AT Field or unrelated assets.
        assert patch(restored,'PS2')[0]==raw
        raw=bytes(restored)
    atlas_report=base/'at_field.json'
    if name=='STATIC.BIN' and atlas_report.exists():
        from patch_at_field import ROOT, patch, caption
        rec=json.loads(atlas_report.read_text())
        assert sha(caption(raw,'PS2')[1].tobytes())==rec['target_caption_sha256']
        native=(ROOT/'work/source/ps2/STATIC.BIN').read_bytes()
        restored=bytearray(raw)
        for a,z in rec['pixel_ranges']:restored[a:z]=native[a:z]
        assert sha(caption(restored,'PS2')[1].tobytes())==rec['source_caption_sha256']
        assert patch(restored,'PS2')[0]==raw
        raw=bytes(restored)
    path=base/'battle_labels.json'
    if not path.exists() or name not in ('FIX00.DAT','WND.BIN'):return raw
    report=json.loads(path.read_text());rec=report['resources'][name]
    assert sha(raw)==rec['target_sha256']
    restored=bytearray(raw)
    for row in rec['ranges']:
        a=row['offset'];before=bytes.fromhex(row['before']);after=bytes.fromhex(row['after'])
        assert len(before)==len(after) and raw[a:a+len(after)]==after
        restored[a:a+len(before)]=before
    assert sha(restored)==rec['source_sha256']
    return bytes(restored)
