"""Record the reviewed screenshot corrections in reusable translation inputs."""
import json
from pathlib import Path
import fix_psp_0413 as fix
from record_campaign_context_review import fingerprint
from strip_jp import clean

ROOT = Path(__file__).resolve().parents[1]
NOTE = 'PSP 0.4.13: defeat means Zeorymer is lost; corrected the imperative in s0150:207 and s0430:207.'


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf8')


def main():
    folder = ROOT/'work/translation/en/script'
    updated = []
    reviews_path = ROOT/'work/output/campaign_context_reviews.json'
    reviews = json.loads(reviews_path.read_text(encoding='utf8'))
    for name in ('stage07_campaign_full_merged', 'stage21_campaign_full_merged',
                 'stage07_campaign_sol61medium_merged'):
        path = folder/(name+'.json')
        data = json.loads(path.read_text(encoding='utf8'))
        affected = [r for r in data['rows'] if r['en']==fix.OLD_OBJECTIVE]
        if not affected:
            assert any(r['en']==fix.NEW_OBJECTIVE for r in data['rows']), name
            continue
        for row in affected:
            assert set(row['uses']) <= {'s0150:207','s0430:207'}
            row['en'] = fix.NEW_OBJECTIVE
        if 'context_review' in data:
            data['context_review']['fingerprint'] = fingerprint(data['rows'])
            data['context_review']['note'] = data['context_review'].get('note','')+' '+NOTE
        write(path,data)
        write(folder/(name+'.en.json'),clean(data))
        if name.endswith('_full_merged'):
            stage=str(int(name[5:7]))
            reviews['stages'][stage]['fingerprint']=fingerprint(data['rows'])
            reviews['stages'][stage]['note']=reviews['stages'][stage].get('note','')+' '+NOTE
        updated.append(name)
    write(reviews_path,reviews)
    path=ROOT/'work/translation/en/ui/all_chapter_cards.json'
    data=json.loads(path.read_text(encoding='utf8'))
    for row in data['cards']:
        if row['en']=='do justice to':
            row['needs_translation']=True
            row['layout_note']='PSP 0.4.13: redraw native mixed-size English artwork with uniform centered lettering.'
    write(path,data)
    print('Updated inputs:',updated)


if __name__=='__main__':main()
