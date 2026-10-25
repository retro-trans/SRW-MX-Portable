"""Validate localized native movie packets, timestamps, decoding and previews."""
import hashlib
import json
import subprocess
from localize_mx_movies import BASE,UI,pes,h264_units,mpeg2_units


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
        '-show_entries','stream=codec_name,profile,width,height,r_frame_rate,nb_read_frames,start_pts,duration_ts',
        '-of','json',str(path)]))['streams']


def verify():
    result={}
    for platform,stem,first in [('PSP','PSP_movie29',2613),('PSP','PSP_movie31',57),
                               ('PS2','PS2_movie1',2629),('PS2','PS2_movie2',94)]:
        suffix='.pmf' if platform=='PSP' else '.bin'
        old=BASE/(stem+suffix);new=BASE/(stem+'_english'+suffix)
        a,b=probe(old),probe(new)
        assert len(a)==len(b)==1
        for key in ['codec_name','profile','width','height','r_frame_rate','nb_read_frames','start_pts','duration_ts']:
            assert a[0][key]==b[0][key],(new,key,a,b)
        original=old.read_bytes();localized=new.read_bytes();assert len(original)==len(localized)
        ov,segs=pes(original,2048 if platform=='PSP' else 0)
        nv,nsegs=pes(localized,2048 if platform=='PSP' else 0);assert segs==nsegs
        mask=bytearray(localized)
        for offset,start,end in segs:mask[start:end]=original[start:end]
        assert mask==original,'Non-video bytes changed'
        units=h264_units(ov) if platform=='PSP' else mpeg2_units(ov)
        assert ov[:units[first][0]]==nv[:units[first][0]]
        # The original PSP has one duplicated DTS. Normalize only this decode
        # test's discarded output timestamps; the actual packets stay native.
        check=subprocess.run(['ffmpeg','-v','error','-i',str(new),'-vf','setpts=N*1001/(30000*TB)',
            '-fps_mode','passthrough','-f','null','-'],capture_output=True)
        assert check.returncode==0 and not check.stderr,(new,check.stderr.decode(errors='replace')[:2000])
        at='5' if stem.endswith(('31','movie2')) else '89.5'
        preview=UI/(stem+'_english.png')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(new),'-ss',at,'-frames:v','1',str(preview)],check=True)
        result[stem]=dict(original_stream=a,localized_stream=b,full_decode_passed=True,
            all_non_video_bytes_headers_timestamps_and_audio_preserved=True,
            elementary_prefix_preserved=True,original_bytes=len(original),
            output_sha256=hashlib.sha256(localized).hexdigest(),preview=preview.name)
        print('Native movie verified:',stem,flush=True)
    report=dict(passed=True,movies=result,emulator_and_hardware_playback='pending')
    (BASE/'movie_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':verify()
