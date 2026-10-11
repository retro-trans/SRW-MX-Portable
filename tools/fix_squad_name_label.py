"""Shorten the rename-screen caption without changing the saved squad name."""
import argparse
import re

import fix_est_surname as common
import strip_jp
import textfit

VERSION, BASE = '0.4.28', '0.4.27'
OLD, NEW = 'Squad Name', 'Name'


def inputs():
    path = common.ROOT/'work/translation/en/ui/boot_ui.json'
    data = common.read(path)
    row = data['overrides']['28F910']
    assert row['en'] in (OLD, NEW)
    row.update(en=NEW, why='User-requested short rename-screen caption; avoids overlap with the editable squad name.')
    common.write(path, data)
    common.write(path.with_name(path.stem+'.en.json'), strip_jp.clean(data))
    common.write(common.ROOT/'work/translation/en/ui/squad_name_label_0.4.28.en.json',
                 dict(version=VERSION, base_version=BASE, before=OLD, after=NEW,
                      address='28F910', saved_name_unchanged=True,
                      reason='Shorten the caption to avoid overlap with Magnet X.'))


def setup_scan():
    pairs = [(textfit.encode(OLD), textfit.encode(NEW)),
             (OLD.encode('ascii'), NEW.encode('ascii'))]
    common.inherited.PATTERNS = [(re.compile(re.escape(old)), None) for old, new in pairs]
    def replace(data):
        count = 0
        for old, new in pairs:
            count += data.count(old)
            data = data.replace(old, new)
        return data, count
    common.inherited.replace_text = replace


def build(platform='PSP',version=VERSION,base=BASE):
    common.VERSION, common.BASE = version, base
    common.setup_scan = setup_scan
    common.build(platform, patch_key='squad_name_label', correction_label='caption',
                 proof_flag='no_old_squad_name_caption_in_game_files',
                 occurrence_field='caption_occurrences',
                 scope=f'Rename-screen caption Name and exact version footer over {platform} {base}; saved names unchanged; later story proofreading remains source-only')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', action='store_true')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--platform',choices=['PSP','PS2'],default='PSP')
    parser.add_argument('--version',default=VERSION)
    parser.add_argument('--base',default=BASE)
    args = parser.parse_args()
    if args.inputs: inputs()
    if args.build: build(args.platform,args.version,args.base)
