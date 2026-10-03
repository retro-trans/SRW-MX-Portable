"""Prepare the remaining story campaign without changing completed translations."""
import argparse,contextlib,hashlib,io,json,re
from pathlib import Path
import export_rows,play_order
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/translation/en/script'
MANIFEST=ROOT/'work/output/stages31_end_sol_medium_manifest.json'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=1),encoding='utf8')
def plan():
    blocks=export_rows.blocks(str(ROOT/'work/build/iso/MAP_ADD.BIN'));speakers=export_rows.speakers()
    supplement=read(ROOT/'work/glossary/campaign_terms.json')
    for r in supplement['characters']:
        for key in ('jp_short','jp_full'):
            if r.get(key):speakers.setdefault(r[key],r['en_short'])
    for r in supplement['speaker_aliases']:speakers.setdefault(r['jp'],r['en'])
    seeds=[OUT/('stage%02d_campaign_full_merged.json'%n) for n in range(1,31)]
    seeds.insert(0,OUT/'prologue_merged.json')
    owners={}
    for path in seeds:
        for r in read(path)['rows']:
            assert r['en'].strip()
            owners.setdefault(r['jp'],dict(source=path.relative_to(ROOT).as_posix(),id=r['id']))
    stages=[]
    for line in (ROOT/'docs/stage_map.md').read_text(encoding='utf8').splitlines():
        cells=[x.strip() for x in line.split('|')[1:-1]]
        if len(cells)!=7:continue
        if cells[0].isdigit() and 31<=int(cells[0])<=54:n=int(cells[0])
        elif cells[0]=='FINAL':n=55
        elif cells[0]=='SECRET':continue
        else:continue
        scenes=[re.search(r'`([^`]+)`',c).group(1) for c in cells[4:] if '`' in c]
        route=dict(route=cells[1],title=cells[3],scenes=scenes,map_scene=re.search(r'`([^`]+)`',cells[5]).group(1))
        if not stages or stages[-1]['stage']!=n:stages.append(dict(stage=n,label='FINAL' if n==55 else str(n),routes=[]))
        stages[-1]['routes'].append(route)
    stages += [dict(stage=56,label='SECRET',routes=[dict(route='-',title='What Gnaws at the Heart',scenes=['i057b','s0570','i057a'],map_scene='s0570')]),dict(stage=57,label='UNUSED',routes=[dict(route='-',title='Unused scenes',scenes=['i063b','i076b','s0760','i076a'],map_scene='s0760')]),dict(stage=58,label='SAVE MESSAGES',routes=[dict(route='-',title='Closing/save messages',scenes=['end_mes'],map_scene=None)])]
    packets=[]
    for stage in stages:
        rows=[];seen={};scenes=[s for r in stage['routes'] for s in r['scenes']]
        for scene in scenes:
            for index,jp in enumerate(blocks[scene]):
                classified=export_rows.classify(jp)
                if not classified:continue
                if re.match(r'^[０-９]+、',jp):classified=dict(kind='plain',speaker_jp='',body_jp=jp)
                if jp in seen:seen[jp]['uses'].append('%s:%s'%(scene,index));continue
                r=dict(id=len(rows),jp=jp,uses=['%s:%s'%(scene,index)],**classified)
                r.update(speaker_en=speakers.get(r['speaker_jp']) if r['speaker_jp'] else '',en='')
                seen[jp]=r;rows.append(r)
        base='stage%02d_campaign'%stage['stage'];fresh=[]
        for r in rows:
            if r['jp'] not in owners:
                new=dict(r,id=len(fresh));fresh.append(new)
                owners[r['jp']]=dict(source='work/translation/en/script/'+base+'.json',id=new['id'])
            r['translation_owner']=owners[r['jp']]
        count=max(6,(len(fresh)+79)//80) if fresh else 0
        stage.update(base=base,rows=len(fresh),all_rows=len(rows),reused_rows=len(rows)-len(fresh),packets=count,missing_speakers=sorted({r['speaker_jp'] for r in fresh if r['speaker_jp'] and not r['speaker_en']}),_source=dict(scenes=scenes,routes=stage['routes'],rows=fresh),_all_source=dict(scenes=scenes,routes=stage['routes'],rows=rows))
        for i in range(count):
            small=len(fresh)<=400;start=i*len(fresh)//6 if small else i*80;stop=(i+1)*len(fresh)//6 if small else min((i+1)*80,len(fresh))
            packets.append(dict(stage=stage['stage'],slice=i,worker=i%6+1,start=start,stop=stop,status='pending',source='work/translation/en/script/'+base+'.json',output='work/translation/en/script/'+base+'_sol61medium_slice_'+str(i)+'.json'))
    return stages,packets,seeds

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    stages,packets,seeds=plan()
    print(json.dumps([dict(stage=s['stage'],label=s['label'],rows=s['rows'],all_rows=s['all_rows'],packets=s['packets'],missing_speakers=s['missing_speakers']) for s in stages],ensure_ascii=False))
    print('%s fresh rows, %s packets'%(sum(s['rows'] for s in stages),len(packets)))
    if not a.write:return
    targets=[OUT/(s['base']+suffix) for s in stages for suffix in ('.json','_all_source.json')]+[MANIFEST,OUT/'BASE_RULES_remaining.md',OUT/'TRANSLATOR_BRIEF_remaining.md']
    assert not any(p.exists() for p in targets),'Refusing overwrite'
    snapshots={}
    for name,source in [('BASE_RULES_remaining.md',ROOT/'BASE_RULES.md'),('TRANSLATOR_BRIEF_remaining.md',OUT/'TRANSLATOR_BRIEF.md')]:
        (OUT/name).write_bytes(source.read_bytes());snapshots[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    for s in stages:
        source=OUT/(s['base']+'.json');write(source,s.pop('_source'));allpath=OUT/(s['base']+'_all_source.json');write(allpath,s.pop('_all_source'));s['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();orders=[]
        for route in s['routes']:
            if not route['map_scene']:continue
            op=OUT/(s['base']+'_'+route['map_scene']+'_order.json')
            with contextlib.redirect_stdout(io.StringIO()):play_order.main(str(ROOT/'work/build/iso/MAP_ADD.BIN'),route['map_scene'],str(allpath),str(op))
            orders.append(op.relative_to(ROOT).as_posix())
        s['order_files']=orders
    write(MANIFEST,dict(model='gpt-6.1-sol',effort='medium',workers_per_stage=6,packet_size=80,snapshots=snapshots,seed_sources=[p.relative_to(ROOT).as_posix() for p in seeds],stages=stages,packets=packets,release_authorized=False))
    print('Wrote remaining campaign queue and source/context snapshots.')
if __name__=='__main__':main()
