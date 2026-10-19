"""Combine verified platform releases into one Retro Trans manifest."""
import argparse
import html
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main(version,retro_trans_root,artifact_tests=None):
    sys.path.insert(0,str(Path(retro_trans_root).resolve()))
    from retro_trans.release import validate_directory
    from retro_trans.catalog import validate_manifest
    from retro_trans.core import sha256_file
    sources=[ROOT/f'work/output/release-{p}-v{version}' for p in ('psp','ps2')]
    for path in sources:validate_directory(path)
    dest=ROOT/f'work/output/release-v{version}'
    assert not dest.exists(),'Preserve existing release packages'
    manifests=[json.loads((p/'BUILD-MANIFEST.json').read_text()) for p in sources]
    assert all(m['version']==version for m in manifests)
    assert manifests[0]['source_commit']==manifests[1]['source_commit']
    manifest=dict(manifests[0]);manifest['patches']=[]
    checks=[]
    dest.mkdir()
    for source,m in zip(sources,manifests):
        validation=json.loads((source/'VALIDATION.json').read_text())
        for row in m['patches']:
            item=dict(row,platform=m['platform'],game_name=m['game_name'])
            manifest['patches'].append(item)
            shutil.copyfile(source/row['patch'],dest/row['patch'])
            passed=next(p for p in validation['patches'] if p['patch']==row['patch'])
            assert passed['roundtrip_verified'] and passed['target_sha256']==row['target_sha256']
            checks.append(passed)
    validate_manifest(manifest)
    def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
    write(dest/'BUILD-MANIFEST.json',manifest)
    write(dest/'VALIDATION.json',dict(schema_version=1,manifest_sha256=sha256_file(dest/'BUILD-MANIFEST.json'),patches=checks))
    if artifact_tests:
        test_data=json.loads(Path(artifact_tests).read_text(encoding='utf8'))
        assert test_data['version']==version and test_data['all_artifact_checks_passed']
        assert test_data['campaign_proofreading_included']
        import title_footer
        for platform,prefix,manifest_data in zip(('PSP','PS2'),('SRWMX_EN_','SRWMX_PS2_EN_'),manifests):
            target=ROOT/f'work/output/{prefix}{version}.iso'
            assert sha256_file(target)==test_data['outputs'][platform]['sha256']==manifest_data['patches'][0]['target_sha256']
            assert title_footer.verify_iso(target,platform,version)==test_data['native_iso_footer_readback'][platform]
        write(dest/f'BUILD-TESTS-v{version}.json',test_data)
    else:
        legacy_runtime_tests(version,manifests,write,dest)
    notes=ROOT/f'docs/releases/v{version}.md'
    text=notes.read_text(encoding='utf8').split('\n### Exact images\n',1)[0]
    text+='\n### Exact images\n\n| Platform / image | Bytes | SHA-256 |\n|---|---:|---|\n'
    seen=set()
    for row in manifest['patches']:
        label=f"{row['platform']} {row['source_version']} source"
        for label,size,digest in [(label,row['source_bytes'],row['source_sha256']),
                                  (f"{row['platform']} v{version} output",row['target_bytes'],row['target_sha256'])]:
            if (label,digest) in seen:continue
            seen.add((label,digest));text+=f'| {label} | {size:,} | `{digest}` |\n'
    (dest/f'README-v{version}.txt').write_text(text,encoding='utf8')
    shutil.copyfile(ROOT/'docs/CHANGELOG.md',dest/f'CHANGELOG-v{version}.md')
    license_files=[ROOT/f'work/output/{prefix}{version}_FONT_LICENSE.txt' for prefix in ('SRWMX_EN_','SRWMX_PS2_EN_')]
    assert license_files[0].read_bytes()==license_files[1].read_bytes()
    shutil.copyfile(license_files[0],dest/'FONT-LICENSE.txt')
    if artifact_tests:
        for source,name in [('chapters01_end_proofread.html',f'PROOFREADING-v{version}.html'),
                            ('dialogue_review_2026_10_12.html',f'DIALOGUE-REVIEW-v{version}.html')]:
            # Historical review pages are optional presentation aids. Current
            # ISO/native evidence above is required even after cache cleanup.
            review_path=ROOT/'work/output'/source
            if not review_path.is_file():continue
            page=review_path.read_text(encoding='utf8')
            assert page.count('<main>')==1
            banner=(f'<p><strong>Included in release v{version} for PSP and PS2.</strong> '
                    'The source-review notes below describe the earlier proofreading step. '
                    'These corrections are now included in the rebuilt images; see the release '
                    'README and BUILD-TESTS file for current verification and pending gameplay checks.</p>')
            if source=='chapters01_end_proofread.html':
                layouts=json.loads((ROOT/'work/translation/en/ps2/script/reviewed_layout.en.json').read_text(encoding='utf8'))
                assert title_footer.version_key(layouts['version'])<=title_footer.version_key(version)
                banner+='<section><h2>PS2 wording adjustments</h2><p>These three source-checked lines use shorter wording to fit the native PS2 font and maximum editable nickname length.</p><table><thead><tr><th>Scene / slot</th><th>Before</th><th>PS2 release wording</th><th>Reason</th></tr></thead><tbody>'
                for row in layouts['rows']:
                    before=row['expected_english'].split('\u300c',1)[1].rstrip('\u300d')
                    after=row['english'].split('\u300c',1)[1].rstrip('\u300d')
                    banner+='<tr>'+''.join('<td>'+html.escape(str(value))+'</td>' for value in (f"{row['scene']}:{row['slot']}",before,after,row['reason']))+'</tr>'
                banner+='</tbody></table></section>'
            (dest/name).write_text(page.replace('<main>','<main>'+banner,1),encoding='utf8')
    # The catalog downloads only the canonical required files; the versioned
    # checksum file also covers every document and the canonical checksum list.
    canonical={'BUILD-MANIFEST.json','VALIDATION.json'}|{p['patch'] for p in manifest['patches']}
    (dest/'SHA256SUMS.txt').write_text(''.join(f'{sha256_file(dest/name)}  {name}\n' for name in sorted(canonical)),encoding='utf8')
    (dest/f'SHA256SUMS-v{version}.txt').write_text(''.join(f'{sha256_file(p)}  {p.name}\n' for p in sorted(dest.iterdir())),encoding='utf8')
    validate_directory(dest)
    print('Verified shared release:',dest,flush=True)


def legacy_runtime_tests(version,manifests,write,dest):
    """Preserve the stricter live-title evidence used by historical releases."""
    psp=json.loads((ROOT/f'work/output/psp_title_footer_{version}_runtime.json').read_text())
    ps2=json.loads((ROOT/f'work/output/ps2_font_{version}_runtime.json').read_text())
    title=json.loads((ROOT/f'work/output/ps2_title_footer_{version}_execution.json').read_text())
    footer_records=[json.loads((ROOT/f'work/output/{p}_title_footer_{version}_verification.json').read_text()) for p in ('psp','ps2')]
    assert psp['version']==ps2['version']==version
    assert footer_records[0]['output_sha256']==manifests[0]['patches'][0]['target_sha256']
    assert ps2['iso_sha256']==manifests[1]['patches'][0]['target_sha256']
    assert psp['full_native_title_texture_matches_candidate']
    assert ps2['immutable_segment_equal'] and all(h['equal'] for h in ps2['hook_checks'])
    assert ps2['fresh_boot'] and ps2['visual_validation'].startswith('passed:')
    assert (ROOT/ps2['title_screenshot']).is_file()
    assert title['passed']
    write(dest/f'BUILD-TESTS-v{version}.json',dict(version=version,
        native_iso_footer_readback={p:r['footer']['readback'] for p,r in zip(('PSP','PS2'),footer_records)},
        psp_title_fresh_boot=psp,ps2_title_fresh_boot={k:v for k,v in ps2.items() if k not in ('hook_checks','mutable_ranges')},
        ps2_native_title_execution=dict(passed=True,cases=len(title['cases']),native_width_executed=title['native_width_executed']),
        psp_name_caption_validation='Fresh-boot verified in 0.4.28; executable and save unchanged in 0.4.29',
        later_campaign_proofreading_included=False,physical_console_tested=False,complete_playthrough_tested=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('version');p.add_argument('--retro-trans-root',required=True)
    p.add_argument('--artifact-tests',type=Path,help='Verified current ISO/native execution evidence; live checks remain explicitly pending')
    args=p.parse_args();main(args.version,args.retro_trans_root,args.artifact_tests)
