"""Create local PS2 v0.4.44 with aligned map-menu values; no release."""
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path
import pycdlib
import title_footer
from fix_ps2_turn_funds import patch,BIAS
from verify_ps2_turn_funds import verify
from build_ps2_dialogue import directory_position
from build_ps2_font import digest_file,files,patch_udf
from port_ps2_translations import sha

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.4.44'
SOURCE=ROOT/'work/output/SRWMX_PS2_EN_0.4.43.iso'
TARGET=ROOT/f'work/output/SRWMX_PS2_EN_{VERSION}.iso'
BASE=ROOT/f'work/build/ps2/font_{VERSION}'


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def save(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


class MetadataWrites:
    """Collect small UDF writes so the full disc transform can be hashed once."""
    def __init__(self):self.at=0;self.writes=[]
    def seek(self,at):self.at=at
    def write(self,raw):
        self.writes.append((self.at,bytes(raw)));self.at+=len(raw);return len(raw)


def build(version=VERSION,source_version='0.4.43',kind='turn_funds',patcher=patch,verifier=verify):
    assert kind in ('turn_funds','stage30_transition','objective_footer')
    VERSION=version
    SOURCE=ROOT/f'work/output/SRWMX_PS2_EN_{source_version}.iso'
    TARGET=ROOT/f'work/output/SRWMX_PS2_EN_{VERSION}.iso'
    BASE=ROOT/f'work/build/ps2/font_{VERSION}'
    assert not TARGET.exists() and not BASE.exists(),'Preserve existing builds'
    previous=read(ROOT/f'work/output/ps2_font_{source_version}_verification.json')
    stat=SOURCE.stat();assert stat.st_size==previous['bytes']
    iso=pycdlib.PyCdlib();iso.open(str(SOURCE));path='/SLPS_253.45;1'
    with iso.open_file_from_iso(iso_path=path) as stream:old=stream.read()
    meta=copy.deepcopy(previous['font']);assert sha(old)==meta['target_sha256']
    title_footer.verify_iso(SOURCE,'PS2',source_version)
    elf,meta,info=patcher(old,meta)
    elf,footer=title_footer.patch(elf,'PS2',VERSION);meta['target_sha256']=sha(elf)
    spans=[(int(h['va'],16)-BIAS,int(h['va'],16)-BIAS+len(bytes.fromhex(h['new']))) for h in info['hooks']]
    spans += [(164,172),(0x100180-BIAS,0x100184-BIAS),(0x100188-BIAS,0x10018c-BIAS)]
    spans += [tuple(s) for s in footer['byte_ranges']]
    mask=bytearray(elf[:len(old)])
    for a,z in spans:mask[a:z]=old[a:z]
    assert mask==old,'Unrelated executable changes'
    print('Executing native '+kind+' checks',flush=True)
    native=verifier(old,elf,meta)
    BASE.mkdir(parents=True);(BASE/'SLPS_253.45').write_bytes(elf)
    save(BASE/'patch.json',meta);save(BASE/(kind+'.json'),info);save(BASE/('native_'+kind+'.json'),native)
    from verify_ps2_title_footer import main as verify_title
    verify_title(VERSION)
    start=stat.st_size//2048;last=start+(len(elf)+2047)//2048;total=last+1
    assert total*2048<=4700372992
    collector=MetadataWrites();position=directory_position(iso,SOURCE,path)
    collector.seek(position+2);collector.write(struct.pack('<I',start)+struct.pack('>I',start))
    collector.seek(position+10);collector.write(struct.pack('<I',len(elf))+struct.pack('>I',len(elf)))
    with SOURCE.open('rb') as stream:
        n=16
        while True:
            stream.seek(n*2048);head=stream.read(7);assert head[1:6]==b'CD001'
            if head[0]==255:break
            if head[0] in (1,2):
                collector.seek(n*2048+80);collector.write(struct.pack('<I',total)+struct.pack('>I',total))
            n+=1
    patch_udf(iso,collector,start,len(elf),last)
    edits=sorted(collector.writes)
    assert all(a+len(raw)<=b for (a,raw),(b,_) in zip(edits,edits[1:]))
    # No existing resource bytes may be touched, including the prior executable.
    for p in files(iso):
        r=iso.get_record(iso_path=p);a=r.extent_location()*2048;z=a+r.data_length
        assert all(at+len(raw)<=a or at>=z for at,raw in edits),p
    source_hash=hashlib.sha256();expected_hash=hashlib.sha256();at=0
    print('Copying baseline, checking its complete hash and applying registered metadata',flush=True)
    with SOURCE.open('rb') as src,TARGET.open('xb') as dst:
        while raw:=src.read(8*1024*1024):
            source_hash.update(raw);out=bytearray(raw)
            for a,data in edits:
                left,right=max(at,a),min(at+len(raw),a+len(data))
                if left<right:out[left-at:right-at]=data[left-a:right-a]
            dst.write(out);expected_hash.update(out);at+=len(raw)
        assert source_hash.hexdigest()==previous['target_sha256'],'Unsupported baseline ISO'
        tail=bytearray(elf+bytes(-len(elf)%2048)+bytes(2048))
        for a,data in edits:
            if a>=at:tail[a-at:a-at+len(data)]=data
        dst.write(tail);expected_hash.update(tail)
    assert TARGET.stat().st_size==total*2048
    print('Verifying complete output image and ISO9660/UDF executable readback',flush=True)
    actual_hash=digest_file(TARGET);assert actual_hash==expected_hash.hexdigest()
    checked=pycdlib.PyCdlib();checked.open(str(TARGET));records=[]
    for row in previous['files']:
        p=row['path'];a,b=iso.get_record(iso_path=p),checked.get_record(iso_path=p)
        if p==path:assert b.extent_location()==start and b.data_length==len(elf)
        else:assert b.extent_location()==a.extent_location() and b.data_length==a.data_length
        records.append(dict(row,changed=p==path,bytes=b.data_length,target_sector=b.extent_location(),
            target_sha256=sha(elf) if p==path else row['target_sha256']))
    assert len(records)==37 and any(a.extent_location()==last for a in checked.udf_anchors)
    for key in ('iso_path','udf_path'):
        with checked.open_file_from_iso(**{key:path if key=='iso_path' else '/SLPS_253.45'}) as stream:
            actual=stream.read();assert actual==elf
    assert verifier(old,actual,meta)==native
    checked.close();iso.close()
    assert (SOURCE.stat().st_size,SOURCE.stat().st_mtime_ns)==(stat.st_size,stat.st_mtime_ns)
    footer['readback']=title_footer.verify_iso(TARGET,'PS2',VERSION)
    result=dict(version=VERSION,platform='PS2',base_version=source_version,output=TARGET.relative_to(ROOT).as_posix(),
        bytes=TARGET.stat().st_size,source_sha256=source_hash.hexdigest(),output_sha256=actual_hash,
        native_execution=native,footer=footer,files=records,
        complete_source_and_output_hash_verified=True,unrelated_disc_bytes_preserved=True,
        all_other_36_resources_and_locations_preserved=True,iso9660_and_udf_readback=True,
        source_unchanged=True,pcsx2_visual_validation='pending',local_build_only=True,github_release=False)
    result['transition' if kind=='stage30_transition' else 'alignment']=info
    save(ROOT/f'work/output/ps2_{kind}_{VERSION}_verification.json',result)
    save(ROOT/f'work/translation/en/ps2/{kind}_{VERSION}.en.json',result)
    save(ROOT/f'work/output/ps2_title_footer_{VERSION}_verification.json',dict(version=VERSION,footer=footer))
    aggregate=copy.deepcopy(previous)
    aggregate.update(version=VERSION,output=result['output'],bytes=result['bytes'],target_sha256=actual_hash,
        source_build_version=source_version,source_build_sha256=result['source_sha256'],font=meta,files=records,
        title_footer=footer,
        current_correction_report=f'work/output/ps2_{kind}_{VERSION}_verification.json',
        pcsx2_fresh_boot_verified=False,github_release=False)
    aggregate['turn_funds_alignment' if kind=='turn_funds' else kind+'_fix']=info
    aggregate[kind+'_execution']=native
    save(ROOT/f'work/output/ps2_font_{VERSION}_verification.json',aggregate)
    shutil.copyfile(ROOT/'incoming/fonts/FONT_LICENSE.txt',TARGET.with_name(TARGET.stem+'_FONT_LICENSE.txt'))
    print('Verified local PS2',VERSION,actual_hash,flush=True)


if __name__=='__main__':build()
