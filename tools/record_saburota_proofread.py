"""Apply the Chapter 17 screenshot follow-up to the source proofreading work."""
import copy
import hashlib
import shutil
from pathlib import Path
import campaign_status
import campaign_context_overrides
import textfit
import strip_jp
from proofread_chapters import ROOT, read, write
from record_campaign_context_review import fingerprint
from ps2_narration_port import native_width

OLD="Sometimes we get the cold shoulder where Commander Misumaru can't see it."
NEW="Sometimes we get a raw deal behind Commander Misumaru's back."
REASON=('Screenshot proofreading follow-up: cold or unfair treatment is broader than simply '
        'being ignored. The line describes mistreatment outside Commander Misumaru\'s oversight. '
        'Raw deal and behind his back preserve Saburota\'s casual tone without the literal, awkward location clause.')


def main():
    folder=ROOT/'work/translation/en/script'
    record=folder/'screenshot_proofread_followups.en.json'
    assert not record.exists(), 'Preserve the recorded proofreading baseline'
    path=folder/'stage17_campaign_full_merged.json';full=read(path)
    row=next(r for r in full['rows'] if r['id']==524)
    assert row['en']==OLD and row['speaker_en']=='Saburota' and row['uses']==['i03s3b:19']
    before=copy.deepcopy(row)
    override_path=folder/'campaign_context_overrides.json';overrides=read(override_path)
    assert not any(o['stage']==17 and o['full_id']==524 for o in overrides['overrides'])
    overrides['overrides'].append(dict(stage=17,full_id=524,expected_owner=copy.deepcopy(row['translation_owner']),
        expected_jp=row['jp'],expected_en=OLD,en=NEW,reason=REASON))
    new=campaign_context_overrides.apply_override(17,row,overrides['overrides'])
    row.update(new)
    # Rebuild this row independently from the unchanged contributor packet.
    original=next(r for r in read(folder/'stage17_campaign_all_source.json')['rows'] if r['id']==524)
    contributor=next(r for r in read(folder/'stage17_campaign_sol61medium_merged.json')['rows'] if r['id']==360)
    reconstructed=dict(original)
    reconstructed.update({k:contributor.get(k,[] if k=='uncertain' else '') for k in ['speaker_en','en','notes','uncertain']})
    reconstructed=campaign_context_overrides.apply_override(17,reconstructed,overrides['overrides'])
    assert all(row[k]==reconstructed[k] for k in ['jp','en','speaker_en','notes','uncertain','uses','translation_owner'])
    findings=campaign_status.check_full(full['rows']);assert not findings,findings
    _,lines,ok=textfit.fit_dialogue('Saburota',NEW);assert ok
    font=read(ROOT/'work/build/ps2/font_0.4.22/patch.json')
    widths=[native_width(l.replace('「','').replace('」','').replace('　',' '),font)+24*(l.count('「')+l.count('」')) for l in lines]
    assert max(widths)<=528,widths
    journal_path=ROOT/'work/output/campaign_context_reviews.json';journal=read(journal_path)
    review=copy.deepcopy(journal['stages']['17']);review['fingerprint']=fingerprint(full['rows'])
    review['note']+=' 2026-10-10: Applied Chapter 17 entry 524 screenshot proofreading correction; recorded in screenshot_proofread_followups.en.json and cumulative HTML. Source-only; no ISO rebuild.'
    full['context_review']=review;journal['stages']['17']=review
    full['context_review_pending']=False
    data=dict(date='2026-10-10',scope='Screenshot follow-ups to the completed campaign proofreading',
        status='Applied to current assembled sources and guarded context overrides',iso_rebuilt=False,
        edits=[dict(speaker='Saburota',kind=row['kind'],before=OLD,after=NEW,reason=REASON,
            appearances=[[17,524]],source_sha256=hashlib.sha256(row['jp'].encode('utf8')).hexdigest())],
        validation=dict(chapter=17,rows=len(full['rows']),problems=findings,guarded_reassembly_verified=True,
            fingerprint=review['fingerprint'],psp_widths=[textfit.px(l) for l in lines],ps2_widths=widths),
        unchanged_disc_builds=['0.4.21','0.4.22'])
    write(path,full);write(path.with_name(path.stem+'.en.json'),strip_jp.clean(full))
    write(override_path,overrides);write(override_path.with_name(override_path.stem+'.en.json'),strip_jp.clean(overrides))
    write(journal_path,journal);write(record,data)
    ui=ROOT/'work/ui/psp/proofread_followups';ui.mkdir(parents=True,exist_ok=True)
    screenshot=Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-e2d3ca49-5726-415b-ad4f-665522aa2248.png')
    shutil.copyfile(screenshot,ui/'chapter17_saburota_reported.png')
    print('Applied Chapter 17 entry 524; entire chapter passes checks; guarded reassembly and both font widths verified.')


if __name__=='__main__':main()
