"""Shorten the two CWndStatus reward labels within their existing slots."""
import struct

from insert_text import encode
from patch_at_field import sha
from verify_text_build import read_iso

ASSETS = {'PSP': '/PSP_GAME/SYSDIR/BOOT.BIN', 'PS2': '/SLPS_253.45;1'}
PSP_EBOOT = '/PSP_GAME/SYSDIR/EBOOT.BIN'
LABELS = [('Funds Gained', 'Funds'), ('PP Gained', 'PP')]
# Native CWndStatus label rows and their position-independent text descriptors.
TABLES = {
    'PSP': [(0x295178, 0x2951DC, 12, 54), (0x295184, 0x2951F8, 143, 54)],
    'PS2': [(0x49A2F4, 0x49A35C, 302, 362), (0x49A300, 0x49A378, 464, 362)],
}


def patch(data, platform, preview=None):
    phoff = struct.unpack_from('<I', data, 28)[0]
    entry_size, count = struct.unpack_from('<2H', data, 42)
    segments = [struct.unpack_from('<8I', data, phoff + index * entry_size)
                for index in range(count)]

    def file_offset(address, size):
        [offset] = [offset + address - va for kind, offset, va, _, filesz, *_ in segments
                    if kind == 1 and va <= address and address + size <= va + filesz]
        return offset

    updated = bytearray(data)
    ranges, regions = [], []
    for (old_label, new_label), (row, descriptor, x, y) in zip(LABELS, TABLES[platform]):
        address, label_x, label_y = struct.unpack_from('<3I', data, file_offset(row, 12))
        assert (label_x, label_y) == (x, y), 'Unexpected reward label position'
        assert struct.unpack_from('<I', data, file_offset(descriptor, 4))[0] == address
        old = encode(old_label)
        new = encode(new_label).ljust(len(old), b'\0')
        offset = file_offset(address, len(old))
        end = offset + len(old)
        before = data[offset:end]
        assert before in (old, new), 'Unexpected status reward label: ' + old_label
        updated[offset:end] = new
        ranges.append([offset, end])
        regions.append(dict(english=new_label, old_label=old_label, x=x, y=y,
                            offset=hex(offset), already_translated=before == new))

    return bytes(updated), dict(platform=platform, regions=regions, byte_ranges=ranges,
                                source_resource_sha256=sha(data), target_resource_sha256=sha(updated))


def verify_iso(path, platform):
    asset = ASSETS[platform]
    paths = [asset, PSP_EBOOT] if platform == 'PSP' else [asset]
    files = read_iso(str(path), paths)
    if platform == 'PSP':
        assert files[PSP_EBOOT] == files[asset]
    expected, report = patch(files[asset], platform)
    assert expected == files[asset] and all(row['already_translated'] for row in report['regions'])
    return report
