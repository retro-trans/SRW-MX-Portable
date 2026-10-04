"""Probe the original script allocator/reader in an isolated PPSSPP instance.

Run at a native-font renderer breakpoint (module base + 0xAED64), before
its call instruction. This invokes the game's size, allocation, ISO-read and
free functions; it does not execute map events or prove a full playthrough.
Find the controller from a map-loader allocation breakpoint at module+0xF06F4:
controller = a0 - 0x10040. Addresses vary by run. Example from the 0.4.3 test:
python tools/verify_scene_loading_live.py 0.4.3 ws://127.0.0.1:45379/debugger 0x8d19480
Append a comma-separated scene list to probe other blocks, e.g. i106a,end_mes.
"""
import hashlib
import io
import json
from pathlib import Path
import struct
import sys

import pycdlib
from ppsspp_dbg import Dbg

ROOT = Path(__file__).resolve().parents[1]


def main(version, url, controller, extra_scenes=''):
    controller = int(controller, 0)
    inputs = json.loads((ROOT/f'work/output/campaign_{version}_inputs.json').read_text())
    iso = pycdlib.PyCdlib()
    iso.open(str(ROOT/inputs['iso']))
    stream = io.BytesIO()
    iso.get_file_from_iso_fp(stream, iso_path='/PSP_GAME/USRDIR/MAP_ADD.BIN')
    mmap = stream.getvalue()
    iso.close()
    selected = inputs['larger_than_original_limit']
    if extra_scenes:
        wanted = extra_scenes.split(',')
        selected = [next(b for b in inputs['blocks'] if b['scene']==name) for name in wanted]
    results = []
    with Dbg(url) as d:
        assert d.is_stepping(), 'Pause at the renderer breakpoint first'
        module = next(m for m in d.call('hle.module.list')['modules'] if m['name']=='SRWMXforPSP')
        base = module['address']
        categories = d.call('cpu.getAllRegs')['categories']
        regs = dict(zip(categories[0]['registerNames'], categories[0]['uintValues']))
        assert regs['pc'] == base+0xaed64, 'Expected instruction before native glyph call'
        marker = regs['pc']
        stack_address = regs['sp']-0x1000
        stack = d.read(stack_address, 0x1000)
        # The actual map-loader at module+0xF06F4 passes controller+0x10040
        # to the allocator. Its script-owner pointer is controller+0xCD3B8.
        # The module+0x2F0E70 resource heap is unrelated to this allocator.
        heap = controller+0x10040
        heap_before = d.read(heap, 0x10008)
        heap_base, capacity = struct.unpack_from('<II', heap_before)
        assert capacity == 0x40000
        original_pointer = struct.unpack('<I', d.read(controller+0xcd3b8, 4))[0]
        original_slot = next(i for i in range(8192)
                             if struct.unpack_from('<I',heap_before,8+i*4)[0]==original_pointer)
        original_size = struct.unpack_from('<I',heap_before,0x8008+original_slot*4)[0]
        original_script = d.read(original_pointer, original_size)
        assert original_script[:4]==b'SRWL'
        sectors = struct.unpack('<204I', d.read(base+0x27c9c0, 204*4))
        names = struct.unpack('<203I', d.read(base+0x27d348, 203*4))
        original_scene = next(item['scene'] for item in inputs['blocks']
                              if mmap[(0x579c+sectors[item['block']])*0x800:
                                      (0x579c+sectors[item['block']+1])*0x800] == original_script)

        def restore():
            d.write(stack_address, stack)
            for category in categories:
                for index, value in enumerate(category['uintValues']):
                    if category['id']==0 and index in (0,32):
                        continue
                    reply=d.call('cpu.setReg', category=category['id'], register=index, value=value)
                    assert reply['event']!='error', reply
            d.call('cpu.setReg', name='pc', value=marker)

        def invoke(function, arguments):
            assert d.is_stepping()
            for index, value in enumerate(arguments):
                d.call('cpu.setReg', name='a%d'%index, value=value)
            d.call('cpu.setReg', name='ra', value=marker)
            d.call('cpu.setReg', name='pc', value=base+function)
            d.call('cpu.resume')
            d.wait_event('cpu.stepping', timeout=25)
            got=d.regs()
            assert got['pc']==marker, ('unexpected stop', got)
            value=got['v0']
            restore()
            return value

        allocated = None
        original_freed = False
        read_pending = False
        try:
            invoke(0xb8b60,[heap,original_pointer])
            original_freed = True
            replacement_baseline = d.read(heap,0x10008)
            for item in selected:
                block = item['block']
                name_pointer = names[block]
                assert d.read(name_pointer, 16).split(b'\0')[0].decode('ascii')==item['scene']
                expected = mmap[(0x579c+sectors[block])*0x800:(0x579c+sectors[block+1])*0x800]
                size = invoke(0x553d8, [0,name_pointer])
                assert size == len(expected) == item['translated_size']
                allocated = invoke(0xb899c, [heap,size,0])
                assert allocated and heap_base<=allocated and allocated+size<=heap_base+capacity, (item['scene'],allocated)
                # Poison the newly allocated, otherwise unused buffer, so an
                # incomplete ISO read cannot accidentally pass the byte comparison.
                d.write(allocated, b'\xa5'*size)
                read_pending = True
                loaded = invoke(0x553e0, [0,allocated,name_pointer])
                # 0x553E0 queues the read. The synchronous archive wrapper
                # 0x55364 calls this native completion wait before using bytes.
                invoke(0x227230, [base+0x31ac80])
                read_pending = False
                assert loaded==1, (item['scene'],'native ISO reader failed')
                actual = d.read(allocated,size)
                assert actual == expected, (item['scene'],'native readback differs')
                results.append(dict(scene=item['scene'], size=size, allocation=allocated,
                                    native_reader_result=loaded,
                                    sha256=hashlib.sha256(actual).hexdigest(),
                                    iso_bytes_match=True))
                if extra_scenes:
                    (ROOT/f'work/build/campaign_{version}_{item["scene"]}_native.bin').write_bytes(actual)
                invoke(0xb8b60,[heap,allocated])
                allocated=None
                assert d.read(heap,0x10008)==replacement_baseline, 'Allocator state differs after freeing'
                print(item['scene'], size, 'native allocation and ISO read passed', flush=True)
        finally:
            if read_pending and d.is_stepping():
                invoke(0x227230, [base+0x31ac80])
            if allocated and d.is_stepping():
                invoke(0xb8b60,[heap,allocated])
            if original_freed and d.is_stepping():
                restored_pointer = invoke(0xb899c,[heap,original_size,0])
                assert restored_pointer==original_pointer
                d.write(restored_pointer,original_script)
                assert d.read(heap,0x10008)==heap_before
                assert d.read(original_pointer,original_size)==original_script
            if d.is_stepping():
                restore()
                d.call('cpu.breakpoint.remove',address=marker)
                d.call('cpu.resume')
        assert len(results)==len(selected)
    report = dict(version=version, module_base=base, controller=controller,
                  map_heap=heap, script_heap_capacity=capacity,
                  original_script_slot=original_slot, original_script_size=original_size,
                  original_scene=original_scene,
                  native_allocator_and_reader_verified=True, scenes=results,
                  allocator_restored=True, full_map_events_playtested=False,
                  method='Native game functions invoked at a renderer breakpoint in isolated PPSSPP')
    suffix = '_extra' if extra_scenes else ''
    (ROOT/f'work/output/campaign_{version}{suffix}_scene_loading.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':
    main(*sys.argv[1:])
