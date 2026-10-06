"""Port native PS2 STAGE records and summaries with original route IDs intact."""
import json
import struct
from port_ps2_translations import ROOT,read_json,sha
import insert_text as it


def build(original):
    source=read_json(ROOT/'work/source/ps2/scenario_inventory.json')
    psp=read_json(ROOT/'work/source/text_inventory/static2_scenario.json')
    tr=read_json(ROOT/'work/translation/en/static2/scenario.json')
    data=bytearray(original);edits=[]
    def put(offset,size,en,kind,jp):
        encoded=it.encode(it.clean(en));assert len(encoded)<=size,(kind,en,size)
        data[offset:offset+size]=encoded+bytes(size-len(encoded))
        edits.append(dict(kind=kind,offset=offset,field_bytes=size,source_sha256=sha(jp.encode('cp932')),english=en))
    assert len(source['chapters'])==14 and len(source['summaries'])==66
    # Chapter records are 88 bytes: 56 name bytes, then count + seven IDs.
    # A 64-byte write corrupts the stage count and first location ID.
    for i,row in enumerate(source['chapters']):put(row['off'],56,tr['chapters'][str(i)],'chapter',row['text'])
    for row in source['locations']:
        # Main location fields are 64 bytes, terrain labels 12 bytes.
        size=64 if (row['off']-0x670)%136==4 else 12
        put(row['off'],size,tr['locations'][row['text']],'location',row['text'])
    for row in source['stage_titles']:
        en=tr['stage_titles'].get(row['text'],{}).get('en')
        if en is None:
            assert row['text']=='冥王、暁に出撃す';en='Hades Sorties at Dawn'
        put(row['off'],56,en,'scenario_title',row['text'])
    summary={r['text']:tr['summaries'][str(r['idx'])] for r in psp['summaries']}
    base=struct.unpack_from('<I',original,16)[0];n=struct.unpack_from('<I',original,base)[0]
    assert n==66
    head=4+4*n;blob=bytearray();ptrs=[]
    for row in source['summaries']:
        en=summary.get(row['text'])
        if en is None:
            assert row['idx']==34
            en='Having lost most of its Hakke robots, Tekkoryu makes its final move. Who will become the ruler of the underworld: Masato Akitsu or Empress Yuratei...?'
        lines=it.wrap(it.clean(en),448);assert len(lines)<=4,(row['idx'],len(lines))
        ptrs.append(head+len(blob));blob+=it.encode('＠'.join(lines))
        edits.append(dict(kind='summary',index=row['idx'],source_sha256=sha(row['text'].encode('cp932')),english=en))
    data=data[:base]+struct.pack('<I',n)+struct.pack('<%dI'%n,*ptrs)+blob
    # Only named string fields and the final summary subfile may differ.
    mask=bytearray(len(original))
    for row in edits:
        if 'offset' in row:mask[row['offset']:row['offset']+row['field_bytes']]=bytes([1])*row['field_bytes']
    assert all(mask[i] or original[i]==data[i] for i in range(base))
    for chapter in range(14):
        start=0x1a0+chapter*88+56
        assert data[start:start+32]==original[start:start+32],('chapter progression',chapter)
    report=dict(chapters=14,scenario_records=66,scenario_title_fields=132,summaries=66,
                numeric_route_records_unchanged=True,source_sha256=sha(original),target_sha256=sha(data),
                original_bytes=len(original),english_bytes=len(data),texts=edits)
    return bytes(data),report


if __name__=='__main__':
    data,report=build((ROOT/'work/source/ps2/STAGE.BIN').read_bytes())
    (ROOT/'work/build/ps2/campaign/STAGE.BIN').write_bytes(data)
    (ROOT/'work/translation/en/ps2/scenario_port.en.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='texts'},indent=2))
