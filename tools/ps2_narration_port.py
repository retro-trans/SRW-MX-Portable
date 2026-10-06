"""Fit reviewed PSP narration to the original PS2 timed record sequences."""
import struct
import insert_text as it
from port_ps2_translations import ROOT,read_json,sha
from ps2_translation_native import extend

BLANK=0x4c3448
END=0x4c3450
TABLES={'opening':(0x3a93b8,0x3a9664),'ending':(0x3a9b00,0x3a9e18)}

def patch(original,data,metadata):
    source=read_json(ROOT/'work/translation/en/ui/boot_text.json')['narration']
    report={}
    for name,(first,after) in TABLES.items():
        records=[struct.unpack_from('<iII',original,o) for o in range(first,after,12)]
        assert records[0]==(207,7,BLANK) and records[-1][2]==END
        assert all(r[1]==7 for r in records)
        end=len(records)-1
        last_text=max(i for i,r in enumerate(records[:-1]) if r[2]!=BLANK)
        paragraphs=list(source[name])
        # PS2 follows the common ending with the player-named protagonists.
        if name=='ending':paragraphs.append('And then, #男愛称 and #女愛称...')
        lines=[it.wrap(it.clean(p),416) for p in paragraphs]
        target=last_text+1
        spare=target-sum(map(len,lines));gaps=len(lines)-1
        assert spare>=gaps,(name,target,sum(map(len,lines)))
        per,lead=divmod(spare,gaps)
        sequence=[BLANK]*lead;ptrs=[]
        for k,para in enumerate(lines):
            if k:sequence.extend([BLANK]*per)
            for line in para:
                data,ptr=extend(data,metadata,it.encode(line),alignment=4)
                sequence.append(ptr);ptrs.append(dict(pointer=hex(ptr),english=line))
        assert len(sequence)==target
        sequence.extend([BLANK]*(end-len(sequence)))
        for i,ptr in enumerate(sequence):struct.pack_into('<I',data,first+12*i+8,ptr)
        for i,r in enumerate(records):assert struct.unpack_from('<iI',data,first+12*i)==r[:2]
        assert struct.unpack_from('<I',data,first+end*12+8)[0]==END
        report[name]=dict(translated_lines=len(ptrs),timing_and_end_record_preserved=True,lines=ptrs)
    metadata['target_sha256']=sha(data)
    return bytes(data),report

def terrain(data):
    import insert_tiles
    saved=insert_tiles.MPTI
    try:
        insert_tiles.MPTI=0x6109800
        result=insert_tiles.patch(data)
    finally:insert_tiles.MPTI=saved
    assert len(result)==len(data)
    count=struct.unpack_from('<I',data,0x6109804)[0]
    for i in range(count):
        p=0x6109808+i*52
        assert result[p+32:p+52]==data[p+32:p+52]
    assert data[:0x6109800]==result[:0x6109800]
    assert data[0x6109808+52*count:]==result[0x6109808+52*count:]
    return result,dict(terrain_records=count,numeric_tile_properties_unchanged=True)
