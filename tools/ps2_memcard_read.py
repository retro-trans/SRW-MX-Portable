"""Read-only extraction of a selected save directory from a PS2 card image.

Directory/superblock/FAT format reference: public-domain ps2dev/mymc by Ross Ridge.
This module never opens a memory card for writing; output files must be new.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


class Card:
    def __init__(self, data):
        self.data = data
        sb = struct.unpack_from('<28s12sHHHHLLLLLL8x128s128sbbxx', data)
        if sb[0] != b'Sony PS2 Memory Card Format ':
            raise ValueError('Not a PS2 memory card')
        self.page_size, self.pages_per_cluster = sb[2:4]
        self.clusters, self.alloc_start, self.alloc_end, self.root = sb[6:10]
        self.indirect = struct.unpack('<32I', sb[12])
        pages = self.clusters * self.pages_per_cluster
        if len(data) == pages * self.page_size:
            self.raw_page_size = self.page_size
        elif len(data) == pages * (self.page_size + self.page_size // 32):
            self.raw_page_size = self.page_size + self.page_size // 32
        else:
            raise ValueError('Unexpected card length')
        self.cluster_size = self.page_size * self.pages_per_cluster
        self.entries_per_cluster = self.cluster_size // 4

    def cluster(self, number):
        if not 0 <= number < self.clusters:
            raise ValueError('Cluster outside card')
        first = number * self.pages_per_cluster
        return b''.join(self.data[(first+i)*self.raw_page_size:
                                  (first+i)*self.raw_page_size+self.page_size]
                        for i in range(self.pages_per_cluster))

    def fat(self, number):
        if not 0 <= number < self.alloc_end:
            raise ValueError('Invalid allocation index')
        epc = self.entries_per_cluster
        fat_number, within = divmod(number, epc)
        indirect_number, indirect_within = divmod(fat_number, epc)
        ind = self.cluster(self.indirect[indirect_number])
        fat_cluster = struct.unpack_from('<I', ind, indirect_within*4)[0]
        return struct.unpack_from('<I', self.cluster(fat_cluster), within*4)[0]

    def chain(self, first):
        seen = set()
        current = first
        while current != 0xFFFFFFFF:
            if current in seen:
                raise ValueError('Cyclic allocation chain')
            seen.add(current)
            yield self.cluster(self.alloc_start + current)
            nxt = self.fat(current)
            if not nxt & 0x80000000:
                raise ValueError('Unallocated cluster in file chain')
            current = nxt if nxt == 0xFFFFFFFF else nxt & 0x7FFFFFFF

    def contents(self, first, length):
        result = b''.join(self.chain(first))
        if len(result) < length:
            raise ValueError('File chain shorter than declared size')
        return result[:length]

    def directory(self, first, count=None):
        data = b''.join(self.chain(first))
        if count is None:
            count = struct.unpack_from('<I', data, 4)[0]
        if count*512 > len(data):
            raise ValueError('Directory shorter than declared entry count')
        out = []
        for off in range(0, count*512, 512):
            mode, _, length, created, cluster, parent, modified, attr, name = struct.unpack_from(
                '<HHL8sLL8sL28x448s', data, off)
            name = name.split(b'\0',1)[0].decode('ascii')
            if mode & 0x8000:
                out.append(dict(name=name, mode=mode, length=length, cluster=cluster,
                                created=list(struct.unpack('<xBBBBBH', created)),
                                modified=list(struct.unpack('<xBBBBBH', modified))))
        return out


def extract(card_path, prefix, outdir):
    original = Path(card_path)
    data = original.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    card = Card(data)
    root = card.directory(card.root)
    selected = [e for e in root if e['name'].startswith(prefix) and e['mode'] & 0x20]
    if not selected:
        raise ValueError('Selected save not found')
    output = Path(outdir)
    output.mkdir(parents=True, exist_ok=False)
    files = []
    for directory in selected:
        target = output / directory['name']
        target.mkdir()
        for e in card.directory(directory['cluster'], directory['length']):
            if e['name'] in ('.','..'):
                continue
            if '/' in e['name'] or '\\' in e['name'] or not e['mode'] & 0x10:
                raise ValueError('Unexpected save entry')
            content = card.contents(e['cluster'], e['length'])
            (target / e['name']).write_bytes(content)
            files.append(dict(directory=directory['name'], **e,
                              sha256=hashlib.sha256(content).hexdigest(),
                              head_hex=content[:64].hex()))
    if hashlib.sha256(original.read_bytes()).hexdigest() != digest:
        raise ValueError('Source card changed during extraction; retry with a stable card')
    report = dict(source=str(original.resolve()), source_bytes=len(data), source_sha256=digest,
                  original_unchanged=True, ecc_checked=False, files=files)
    (output/'extraction.json').write_text(json.dumps(report,indent=2), encoding='utf8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('card')
    parser.add_argument('prefix')
    parser.add_argument('outdir')
    args = parser.parse_args()
    print(json.dumps(extract(args.card,args.prefix,args.outdir),indent=2))
