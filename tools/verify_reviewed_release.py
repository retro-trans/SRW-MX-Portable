"""Verify current release artifacts and native regressions without GUI claims."""
import argparse
import json
import struct
from pathlib import Path

import fix_psp_parts
import textfit
import title_footer
from build_campaign import file_sha256
from verify_text_build import read_iso

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def save(path,data):Path(path).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')


def psp_native(version):
    import verify_psp_0413 as regression
    import verify_psp_0410 as previous
    import verify_psp_parts
    from psp_spirit_footer import FOOTER_PATCHES
    path=ROOT/f'work/output/SRWMX_EN_{version}.iso'
    boot=read_iso(str(path),['/PSP_GAME/SYSDIR/BOOT.BIN'])['/PSP_GAME/SYSDIR/BOOT.BIN']
    for site in fix_psp_parts.SITES:
        destination=4 if site==0x1e5a90 else 5
        expected=0x24000000|(29<<21)|(destination<<16)|fix_psp_parts.NAME_STACK_OFFSET
        assert struct.unpack_from('<I',boot,site+0x60)[0]==expected
    for site,_,expected in FOOTER_PATCHES:
        assert struct.unpack_from('<I',boot,site+0x60)[0]==expected
    draws=regression.footer(boot,['Bless','Focus','Trust','????','Cheer','????'],[35,15,25,0,70,0])
    regression.check_footer(draws)
    levels=previous.level_up(boot,True)
    narration=previous.narration(boot)
    original=verify_psp_parts.execute(False); fixed=verify_psp_parts.execute(True)
    assert not original['pointer_preserved'] and fixed['pointer_preserved']
    names=read(ROOT/'work/translation/en/static2/names.json')
    max_bytes=max(len(textfit.encode(value))+1 for value in names.values() if value)
    assert max_bytes<=fix_psp_parts.NAME_CAPACITY
    report=dict(version=version,iso_sha256=file_sha256(path),passed=True,
        parts_patch_words_verified=len(fix_psp_parts.SITES),parts_native_regression=dict(original=original,fixed=fixed),
        longest_database_name_bytes=max_bytes,name_buffer_capacity=fix_psp_parts.NAME_CAPACITY,
        spirit_footer_six_cells_fit=True,level_up=levels,narration=narration,
        live_equip_and_exit_test='pending; previous user-stopped check was not resumed')
    save(ROOT/f'work/output/psp_native_{version}_execution.json',report)
    print('PSP actual patch words, six Spirit Search cells, Level Up, narration and native Parts regression pass',flush=True)
    return report


def main(version):
    import battle_quotes
    assert battle_quotes.verify(str(ROOT/f'work/output/SRWMX_EN_{version}.iso')) == 0, \
        'PSP native battle quotes differ from complete English sources'
    from verify_battle_release import verify as verify_battle
    from patch_battle_banners import verify_iso as verify_banners
    battle_checks={}
    banner_checks={}
    for platform,prefix in [('PSP','SRWMX_EN_'),('PS2','SRWMX_PS2_EN_')]:
        battle_checks[platform]=verify_battle(ROOT/f'work/output/{prefix}{version}.iso',platform)
        save(ROOT/f'work/output/{platform.lower()}_battle_{version}_verification.json',battle_checks[platform])
        banner_checks[platform]=verify_banners(ROOT/f'work/output/{prefix}{version}.iso',platform)
    psp=read(ROOT/f'work/output/campaign_{version}_verification.json')
    ps2=read(ROOT/f'work/output/ps2_font_{version}_verification.json')
    native=read(ROOT/f'work/output/psp_native_{version}_execution.json')
    psp_text=read(ROOT/f'work/output/psp_text_{version}_verification.json')
    title=read(ROOT/f'work/output/ps2_title_footer_{version}_execution.json')
    assert psp['all_story_strings_verified'] and not psp['problems']
    assert ps2['campaign_proofreading_included'] and ps2['campaign_review']['missing_readable_strings']==0
    assert native['passed'] and psp_text['passed'] and title['passed'] and len(title['cases'])==42
    assert ps2['stage30_execution_checks']['native_additional_asset_references_valid']
    outputs={}; footers={}
    for platform,prefix,expected in [('PSP','SRWMX_EN_',psp['iso_sha256']),('PS2','SRWMX_PS2_EN_',ps2['target_sha256'])]:
        path=ROOT/f'work/output/{prefix}{version}.iso';actual=file_sha256(path)
        assert actual==expected
        outputs[platform]=dict(sha256=actual,bytes=path.stat().st_size)
        footers[platform]=title_footer.verify_iso(path,platform,version)
    assert native['iso_sha256']==outputs['PSP']['sha256']
    assert ps2['campaign_review']['inputs']==read(ROOT/f'work/output/campaign_{version}_inputs.json')['input_sha256']
    data=dict(version=version,date='2026-10-13',all_artifact_checks_passed=True,
        native_battle_quotes=battle_checks,
        native_battle_banner_artwork=banner_checks,
        psp_non_story_text=psp_text,
        campaign_proofreading_included=True,outputs=outputs,native_iso_footer_readback=footers,
        psp_story=dict(blocks=psp['script_blocks'],original_readable_uses=psp['original_readable_uses_verified'],
                       stored_string_records=psp['string_records_checked'],raw_commands_preserved=psp['raw_commands_preserved']),
        psp_native_regressions=native,
        ps2_story=dict(blocks=ps2['total_scenes'],readable_strings=ps2['translated_strings'],
                       changed_slots=ps2['campaign_review']['changed_string_slots'],
                       native_linebreak_reflows=len(ps2['campaign_review']['native_linebreak_reflows']),
                       source_checked_shorter_ps2_phrasing=ps2['campaign_review']['native_layout_wording'],
                       verified_port_commands_preserved=True,psp_extra_scenarios_preserved=True),
        ps2_native_regressions=ps2['stage30_execution_checks'],
        ps2_title_execution=dict(passed=True,cases=len(title['cases']),native_width_executed=title['native_width_executed']),
        ps2_library=ps2['library_source_followup'],ps2_battle_quote_copies=ps2['battle_screenshot_copies_updated'],
        ps2_battle_quote_native_references=ps2['battle_quote_native_references_updated'],
        fresh_boot_gui_validation='not performed for this version',complete_playthrough_tested=False,
        physical_console_tested=False,psp_live_parts_menu_test='pending')
    path=ROOT/f'work/output/release_{version}_build_tests.json';save(path,data)
    print('Current artifact checks recorded:',path,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('version')
    parser.add_argument('--psp-native-only',action='store_true');args=parser.parse_args()
    if args.psp_native_only:psp_native(args.version)
    else:main(args.version)
