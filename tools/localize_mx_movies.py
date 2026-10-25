"""Localize bounded movie captions while retaining native PES/audio packets."""
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/build/title_credits_0.4.47'
UI=ROOT/'work/ui/title_credits_0.4.47'
START=re.compile(b'\x00\x00(?:\x00)?\x01')


def ensure_movies():
    """Rebuild ignored movie outputs from the user's original discs if absent."""
    report=BASE/'movie_verification.json'
    if report.is_file():
        data=json.loads(report.read_text())
        if data.get('passed') and all(
            (BASE/(stem+('.pmf' if stem.startswith('PSP') else '.bin'))).is_file()
            and
            (BASE/(stem+'_english'+('.pmf' if stem.startswith('PSP') else '.bin'))).is_file()
            and hashlib.sha256((BASE/(stem+'_english'+('.pmf' if stem.startswith('PSP') else '.bin'))).read_bytes()).hexdigest()==row['output_sha256']
            for stem,row in data['movies'].items()):return data
    import pycdlib
    BASE.mkdir(parents=True,exist_ok=True)
    for platform,disc,path in [('PSP','Super Robot Taisen MX Portable (Japan).iso','/PSP_GAME/USRDIR/MOVIE.BIN'),
                               ('PS2','Super Robot Taisen MX (Japan).iso','/DATA/STRM.BIN;1')]:
        iso=pycdlib.PyCdlib();iso.open(str(ROOT/disc))
        with iso.open_file_from_iso(iso_path=path) as f:data=f.read()
        iso.close()
        if platform=='PSP':
            offsets=[m.start() for m in re.finditer(b'PSMF',data)]
            assert len(offsets)==33
            for n in (29,30,31):
                o=offsets[n];a,z=struct.unpack_from('>2I',data,o+8)
                (BASE/f'PSP_movie{n}.pmf').write_bytes(data[o:o+a+z])
        else:
            offsets=list(struct.unpack_from('<5I',data))+[len(data)]
            for n in (1,2,3):(BASE/f'PS2_movie{n}.bin').write_bytes(data[offsets[n]:offsets[n+1]])
    psp_production();psp_title();ps2_production();ps2_title()
    from verify_mx_movies import verify
    return verify()


def patch_archive(data,platform):
    ensure_movies();out=bytearray(data)
    entries=[(0x2c7d800,'PSP_movie29','.pmf'),(0x460d800,'PSP_movie31','.pmf')] if platform=='PSP' else [
        (0x931000,'PS2_movie1','.bin'),(0x6b55800,'PS2_movie2','.bin')]
    for offset,stem,suffix in entries:
        old=(BASE/(stem+suffix)).read_bytes();new=(BASE/(stem+'_english'+suffix)).read_bytes()
        assert len(old)==len(new) and data[offset:offset+len(old)] in (old,new)
        out[offset:offset+len(old)]=new
    return bytes(out)


def pes(data,start=0):
    """Map the elementary video plane without rewriting container or audio."""
    segments=[];video=bytearray();pos=start
    while pos<len(data)-6:
        a=data.find(b'\0\0\1',pos)
        if a<0:break
        code=data[a+3]
        if code==0xba:
            assert data[a+4]&0xc0==0x40
            pos=a+14+(data[a+13]&7);continue
        if code==0xb9:pos=a+4;continue
        assert code>=0xbb,(hex(a),hex(code))
        z=a+6+int.from_bytes(data[a+4:a+6],'big')
        assert z<=len(data)
        if code==0xe0:
            assert data[a+6]&0xc0==0x80
            s=a+9+data[a+8]
            segments.append((len(video),s,z));video+=data[s:z]
        pos=z
    return bytes(video),segments


def h264_units(data):
    starts=[m.start() for m in START.finditer(data) if data[m.end()]&31==9]
    assert starts and starts[0]==0
    return [(a,z) for a,z in zip(starts,starts[1:]+[len(data)])]


def mpeg2_units(data):
    pictures=[m.start() for m in re.finditer(b'\0\0\1\0',data)]
    starts=[];last=0
    for a in pictures:
        headers=[m.start()+last for m in re.finditer(b'\0\0\1[\xb3\xb8]',data[last:a])]
        starts.append(min(headers) if headers else a);last=a+4
    starts[0]=0
    return [(a,z) for a,z in zip(starts,starts[1:]+[len(data)])]


def picture_type(raw):
    a=raw.index(b'\0\0\1\0');return (raw[a+5]>>3)&7


def command(args):
    result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y']+list(map(str,args)),
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert result.returncode==0,result.stderr.decode(errors='replace')[-3000:]


def caption_filter(platform):
    # Text is composited onto the game's corresponding clean opening frames.
    size,ys=(15,[98,120,141]) if platform=='PSP' else (23,[165,199,232])
    alpha='if(lt(t,0.65),0,if(lt(t,0.85),(t-0.65)/0.2,if(lt(t,3.0),1,max(0,(4.5-t)/1.5))))'
    names=['PRODUCED BY','BANPRESOFT CO., LTD.','BANPRESTO CO., LTD.']
    filters=[]
    for n,(text,y) in enumerate(zip(names,ys)):
        filters.append(f"drawtext=fontfile=work/build/title_credits_0.4.47/credit.ttf:text='{text}':fontsize={size-3 if n==0 else size}:fontcolor=white:borderw=1:bordercolor=black:x=(w-tw)/2:y={y}:alpha='{alpha}'")
    return ','.join(filters)


def psp_production():
    import shutil
    from make_latin_font import FONT
    shutil.copyfile(FONT,BASE/'credit.ttf')
    container=(BASE/'PSP_movie29.pmf').read_bytes();video,segments=pes(container,2048)
    units=h264_units(video);first=2613;count=len(units)-first
    tail=BASE/'PSP_production_tail.h264'
    # Keep the readable production card at CRF 30. Constrain only the short
    # preceding moving shot and final near-black fade to their small packets.
    zones={n:43 for n in range(22,59)}
    zones.update({n:48 for n in range(145,count)});crf=30
    for attempt in range(8):
        params='aud=1:repeat-headers=1:keyint=59:min-keyint=59:scenecut=0:aq-mode=0:mbtree=0'
        if zones:params+=':zones='+'/'.join(f'{n},{n},q={q}' for n,q in sorted(zones.items()))
        command(['-i',BASE/'PSP_movie30.pmf','-vf',
            f'trim=start_frame={first-1}:end_frame={len(units)-1},setpts=PTS-STARTPTS,'+caption_filter('PSP'),
            '-fps_mode','passthrough','-an','-c:v','libx264','-profile:v','main','-level:v','2.1',
            '-qp',crf,'-preset','slow','-bf','0','-refs','1',
            '-x264-params',params,
            '-f','h264',tail])
        new=tail.read_bytes();blocks=[new[a:z] for a,z in h264_units(new)]
        result,over=replace_units(container,segments,video,units,first,blocks,'h264')
        print('PSP tail attempt',attempt,'frames',len(blocks),'over budget',over[:8],flush=True)
        if result is not None:
            (BASE/'PSP_movie29_english.pmf').write_bytes(result)
            info=dict(first_edited_frame=first,edited_frames=count,qp=crf,limited_frame_qp=zones,
                original_bytes=len(container),output_bytes=len(result),
                container_headers_timestamps_and_all_audio_unchanged=True,
                elementary_prefix_unchanged=True,per_frame_byte_budgets_preserved=True)
            (BASE/'PSP_production.json').write_text(json.dumps(info,indent=2)+'\n')
            return info
        for n,length,budget in over:
            for k in range(n,min(count,n+8)):
                zones[k]=min(51,zones.get(k,38)+3)
    raise AssertionError('Localized video cannot fit original frame budgets')


def replace_units(container,segments,original,units,first,new_units,kind,indices=None):
    indices=list(range(first,len(units))) if indices is None else indices
    assert len(indices)==len(new_units),(len(indices),len(new_units),len(units))
    out=bytearray(original);over=[]
    for index,(n,raw) in enumerate(zip(indices,new_units)):
        a,z=units[n];budget=z-a;remaining=budget-len(raw)
        if remaining<0:over.append((index,len(raw),budget));continue
        if kind=='h264':
            pad=b'\0\0\1\x0c'+b'\xff'*(remaining-5)+b'\x80' if remaining>=6 else bytes(remaining)
            out[a:z]=raw+pad
        else:
            assert picture_type(raw)==picture_type(original[a:z]),(n,picture_type(raw),picture_type(original[a:z]))
            # MPEG user data terminates at the next picture start code.
            pad=b'\0\0\1\xb2'+b'\xff'*(remaining-4) if remaining>=4 else bytes(remaining)
            out[a:z]=pad+raw
    if over:return None,over
    result=bytearray(container)
    for a,s,z in segments:result[s:z]=out[a:a+z-s]
    assert len(result)==len(container)
    # Every header, PES timestamp, private stream, audio and non-video byte
    # remains identical, as do all elementary bytes before the edited tail.
    mask=bytearray(result)
    for a,s,z in segments:mask[s:z]=container[s:z]
    assert mask==container and bytes(out[:units[first][0]])==original[:units[first][0]]
    return bytes(result),[]


def ps2_production():
    container=(BASE/'PS2_movie1.bin').read_bytes();video,segments=pes(container)
    units=mpeg2_units(video);first=2629
    # Retain two leading B pictures; the opening GOP's I picture is forward.
    indices=[first]+list(range(first+3,len(units)))
    target=BASE/'PS2_production_tail.m2v'
    command(['-i',BASE/'PS2_movie3.bin','-vf',
        f'trim=start_frame={first+2},setpts=PTS-STARTPTS,'+caption_filter('PS2'),
        '-fps_mode','passthrough','-an','-c:v','mpeg2video','-g','18','-bf','2',
        '-b_strategy','0','-sc_threshold','1000000000','-q:v','4',
        '-maxrate','9000000','-bufsize','1835008','-f','mpeg2video',target])
    new=target.read_bytes();blocks=[bytearray(new[a:z]) for a,z in mpeg2_units(new)]
    print('PS2 tail units',len(blocks),'expected',len(indices),flush=True)
    for n,raw in zip(indices,blocks):
        a,z=units[n];prior=video[a:z]
        # The two retained native leading B pictures use the original mixed
        # sequence flag. Progressive replacement pictures remain valid in it.
        for m in re.finditer(b'\0\0\1\xb5',raw):
            if raw[m.end()]>>4==1:raw[m.end()+1]&=~8
        assert picture_type(raw)==picture_type(prior),(n,picture_type(raw),picture_type(prior))
        p=raw.index(b'\0\0\1\0');q=prior.index(b'\0\0\1\0')
        raw[p+4]=prior[q+4];raw[p+5]=(raw[p+5]&0x3f)|(prior[q+5]&0xc0)
        g=raw.find(b'\0\0\1\xb8');h=prior.find(b'\0\0\1\xb8')
        assert (g>=0)==(h>=0),(n,g,h)
        if g>=0:raw[g+4:g+8]=prior[h+4:h+8]
    result,over=replace_units(container,segments,video,units,first,[bytes(b) for b in blocks],'mpeg2',indices)
    assert result is not None,over[:20]
    (BASE/'PS2_movie1_english.bin').write_bytes(result)
    info=dict(first_edited_coded_picture=first,edited_pictures=len(blocks),
              two_leading_b_pictures_preserved=True,picture_types_and_temporal_references_preserved=True,
              gop_timecodes_preserved=True,container_headers_timestamps_and_all_audio_unchanged=True,
              elementary_prefix_unchanged=True,per_picture_byte_budgets_preserved=True,
              original_bytes=len(container),output_bytes=len(result))
    (BASE/'PS2_production.json').write_text(json.dumps(info,indent=2)+'\n')
    return info


def ps2_title():
    source=BASE/'PS2_movie2.bin';out=BASE/'PS2_title_english.mpg'
    graph=('[0:v]setpts=PTS-STARTPTS[original];'
           '[1:v]format=rgba,fade=t=in:st=3.4:d=0.3:alpha=1[english];'
           '[original][english]overlay=shortest=1:enable=gte(t\\,3.4),'
           'fade=t=out:st=6.0:d=0.7:color=white[v]')
    command(['-i',source,'-loop','1','-framerate','30000/1001','-i',UI/'PS2_title_english.png',
        '-filter_complex',graph,'-map','[v]','-an','-fps_mode','passthrough',
        '-c:v','mpeg2video','-q:v','3','-g','18','-bf','2',
        '-maxrate','9000000','-bufsize','1835008','-muxpreload','0','-muxdelay','0',
        '-output_ts_offset','0.083522222','-avoid_negative_ts','disabled','-f','vob',out])
    container=source.read_bytes();video,segments=pes(container);units=mpeg2_units(video)
    first=94;indices=[first]+list(range(first+3,len(units)))
    tail=BASE/'PS2_title_tail.m2v'
    command(['-i',out,'-vf',f'trim=start_frame={first+2},setpts=PTS-STARTPTS',
        '-an','-fps_mode','passthrough','-c:v','mpeg2video','-q:v','8','-g','18','-bf','2',
        '-b_strategy','0','-sc_threshold','1000000000',
        '-maxrate','9000000','-bufsize','1835008','-f','mpeg2video',tail])
    new=tail.read_bytes();blocks=[bytearray(new[a:z]) for a,z in mpeg2_units(new)]
    assert len(blocks)==len(indices)
    for n,raw in zip(indices,blocks):
        a,z=units[n];prior=video[a:z]
        for m in re.finditer(b'\0\0\1\xb5',raw):
            if raw[m.end()]>>4==1:raw[m.end()+1]&=~8
        assert picture_type(raw)==picture_type(prior),(n,picture_type(raw),picture_type(prior))
        p=raw.index(b'\0\0\1\0');q=prior.index(b'\0\0\1\0')
        raw[p+4]=prior[q+4];raw[p+5]=(raw[p+5]&0x3f)|(prior[q+5]&0xc0)
        g=raw.find(b'\0\0\1\xb8');h=prior.find(b'\0\0\1\xb8')
        assert (g>=0)==(h>=0)
        if g>=0:raw[g+4:g+8]=prior[h+4:h+8]
    result,over=replace_units(container,segments,video,units,first,[bytes(b) for b in blocks],'mpeg2',indices)
    assert result is not None,over[:20]
    (BASE/'PS2_movie2_english.bin').write_bytes(result)
    info=dict(original_bytes=len(container),output_bytes=len(result),edited_pictures=len(blocks),
              first_edited_coded_picture=first,container_headers_timestamps_and_all_audio_unchanged=True,
              two_leading_b_pictures_preserved=True,picture_types_and_temporal_references_preserved=True,
              gop_timecodes_preserved=True,per_picture_byte_budgets_preserved=True,audio_streams=0,
              clean_source_frame='PS2_title_clean.png',logo='PS2_logo_english_master.png',
              native_opening_until_seconds=3.4,english_logo_fade_seconds=[3.4,3.7],
              final_white_transition_seconds=[6.0,6.7])
    (BASE/'PS2_title.json').write_text(json.dumps(info,indent=2)+'\n')
    return info


def psp_title():
    container=(BASE/'PSP_movie31.pmf').read_bytes();video,segments=pes(container,2048)
    units=h264_units(video);first=57;count=len(units)-first;target=BASE/'PSP_title_tail.h264'
    graph=('[0:v]setpts=PTS-STARTPTS[original];'
           '[1:v]format=rgba[english];'
           '[original][english]overlay=shortest=1:enable=gte(t\\,3.837166),'
           'fade=t=out:st=5.8:d=0.4:color=white,'
           f'trim=start_frame={first},setpts=PTS-STARTPTS[v]')
    zones={}
    for attempt in range(10):
        params='aud=1:repeat-headers=1:keyint=58:min-keyint=58:scenecut=0:aq-mode=0:mbtree=0'
        if zones:params+=':zones='+'/'.join(f'{n},{n},q={q}' for n,q in sorted(zones.items()))
        command(['-i',BASE/'PSP_movie31.pmf','-loop','1','-framerate','30000/1001',
            '-i',UI/'PSP_title_english.png','-filter_complex',graph,'-map','[v]',
            '-an','-fps_mode','passthrough','-c:v','libx264','-profile:v','main','-level:v','2.1',
            '-pix_fmt','yuv420p','-qp','30','-preset','slow','-bf','0','-refs','1','-x264-params',params,'-f','h264',target])
        new=target.read_bytes();blocks=[new[a:z] for a,z in h264_units(new)]
        result,over=replace_units(container,segments,video,units,first,blocks,'h264')
        print('PSP title attempt',attempt,'over budget',over[:8],flush=True)
        if result is not None:
            (BASE/'PSP_movie31_english.pmf').write_bytes(result)
            info=dict(original_bytes=len(container),output_bytes=len(result),
                first_edited_frame=first,edited_frames=count,qp=30,limited_frame_qp=zones,
                container_headers_timestamps_and_all_audio_unchanged=True,
                elementary_prefix_unchanged=True,per_frame_byte_budgets_preserved=True,
                native_opening_until_seconds=3.837166,english_logo_on_original_key_frame=115,
                final_white_transition_seconds=[5.8,6.2])
            (BASE/'PSP_title.json').write_text(json.dumps(info,indent=2)+'\n');return info
        for n,length,budget in over:
            for k in range(n,min(count,n+7)):zones[k]=min(51,zones.get(k,38)+3)
    raise AssertionError('Localized PSP title does not fit the native frame budgets')


def inspect():
    for p,name,skip in [('PSP','PSP_movie29.pmf',2048),('PS2','PS2_movie1.bin',0)]:
        data=(BASE/name).read_bytes();video,segs=pes(data,skip)
        (BASE/f'{p}_elementary.bin').write_bytes(video)
        units=h264_units(video) if p=='PSP' else mpeg2_units(video)
        print(p,len(video),'units',len(units),flush=True)
        if p=='PS2':
            print('tail coding types',''.join(str(picture_type(video[a:z])) for a,z in units[-170:]),flush=True)
            print('tail GOPs',[(n,z-a) for n,(a,z) in enumerate(units) if n>2550 and b'\0\0\1\xb8' in video[a:z]],flush=True)


if __name__=='__main__':inspect()
