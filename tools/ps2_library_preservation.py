"""Use independently checked library changes with historical regression fixtures.

Native checks execute the current ELF. Only historical byte/row comparisons
receive the verified pre-library snapshot; structural() proves every unrelated
section, executable byte, external sentence and resource remains exact.
"""
from port_ps2_translations import ROOT, read_json

def baseline_bytes(base,name):
    raw=(base/name).read_bytes()
    if name not in ('FIX00.DAT','SLPS_253.45') or not (base/'library.json').exists():return raw
    from verify_ps2_library import structural
    report=structural(base)
    return (ROOT/report['source_directory']/name).read_bytes()
