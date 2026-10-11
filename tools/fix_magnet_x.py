"""Set the eight-character native squad default to the requested Magnet X."""
import argparse
import json
import re
from pathlib import Path

import fix_est_surname as common
import strip_jp
import textfit

ROOT=Path(__file__).resolve().parents[1]
VERSION,BASE='0.4.25','0.4.24'
OLD,NEW='Magnate Ten','Magnet X'


def inputs():
    path=ROOT/'work/translation/en/ui/boot_ui.json';data=common.read(path)
    assert data['defaults']['マグネイト・テン']==OLD
    data['defaults']['マグネイト・テン']=NEW
    data['uncertain']=[n for n in data.get('uncertain',[]) if 'Magnate Ten' not in n]
    common.write(path,data);common.write(path.with_name(path.stem+'.en.json'),strip_jp.clean(data))
    path=ROOT/'work/glossary/decisions.json';d=common.read(path)
    d['names']['マグネイト・テン']=NEW
    d['squad_name_default']=dict(date='2026-10-11',en=NEW,previous=OLD,
        reason='Explicit user request: Magnet X is the default squad name. Eight characters including the space fit the native name limit.',
        dialogue_policy='Keep #部隊名 substitution so user-selected names appear naturally in dialogue.',existing_saves='Preserve saved names; Reset selects the new default.')
    common.write(path,d)
    assert len(NEW)==8 and len(textfit.encode(NEW))==16
    common.write(ROOT/'work/translation/en/ui/magnet_x_0.4.25.en.json',dict(version=VERSION,base_version=BASE,
        date='2026-10-11',default=NEW,previous_default=OLD,characters=8,
        saved_names_preserved=True,ruri_dialogue_uses_saved_squad_name=True,
        psp_save_import_report='work/output/magnet_x_save_import.json'))
    print('Native PSP/PS2 default input now Magnet X; dynamic dialogue and saved names preserved.',flush=True)


def setup_scan():
    common.inherited.PATTERNS=[(re.compile(re.escape(textfit.encode(OLD))),None),
                              (re.compile(re.escape(OLD.encode('ascii'))),None)]
    def replace(data):
        count=0
        for old,new in [(textfit.encode(OLD),textfit.encode(NEW)),(OLD.encode('ascii'),NEW.encode('ascii'))]:
            found=data.count(old);data=data.replace(old,new);count+=found
        return data,count
    common.inherited.replace_text=replace


def build(platform):
    common.VERSION,common.BASE=VERSION,BASE
    common.setup_scan=setup_scan
    common.build(platform,patch_key='magnet_x',correction_label='default-name',
        proof_flag='no_old_default_name_in_game_files',occurrence_field='default_name_occurrences',
        scope='Default squad name Magnet X and exact version footer over 0.4.24; later source proofreading still awaits full story rebuild')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',action='store_true');p.add_argument('--build',choices=['PSP','PS2'])
    args=p.parse_args()
    if args.inputs:inputs()
    if args.build:build(args.build)
