"""New battle captions against the actual latest local PSP/PS2 resources."""
import json
import unittest
from unittest.mock import patch as mock_patch
import patch_battle_banners as banners
from patch_at_field import ROOT,SPECS
from verify_text_build import read_iso

NEW={'nattoru_bullet','ship_support_attack','field_pierced','god_hand_final'}


class Caption052Regression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data={}
        for p,prefix,version,asset in [('PSP','SRWMX_EN_','0.4.51','/PSP_GAME/USRDIR/STATIC2_ADD.BIN'),
                                     ('PS2','SRWMX_PS2_EN_','0.4.50','/DATA/STATIC.BIN;1')]:
            cls.data[p]=read_iso(str(ROOT/f'work/output/{prefix}{version}.iso'),[asset])[asset]

    def test_preserves_all_sixteen_earlier_captions(self):
        for p,data in self.data.items():
            with self.subTest(platform=p):
                updated,report=banners.patch(data,p,version='0.4.52')
                self.assertEqual({r['id'] for r in report['regions'] if not r['already_translated']},NEW)
                self.assertEqual(sum(r['already_translated'] for r in report['regions']),16)
                self.assertEqual(updated,banners.patch(data,p,region_ids=NEW)[0])
                self.assertEqual(updated,banners.patch(updated,p,version='0.4.52')[0])
                self.assertTrue(report['palette_preserved'])
                self.assertTrue(report['all_other_pixels_and_bytes_preserved'])

    def test_repeated_reports_are_already_translated(self):
        for p,data in self.data.items():
            with self.subTest(platform=p):
                updated,report=banners.patch(data,p,region_ids=['cannot_attack','open_get'])
                self.assertEqual(updated,data)
                self.assertTrue(all(r['already_translated'] for r in report['regions']))

    def test_preserves_beam_coat_combination_and_adjacent_status(self):
        for p,data in self.data.items():
            updated,_=banners.patch(data,p,version='0.4.52')
            boxes=[(240,168,332,192),(124,208,224,232)]
            boxes+=([(0,256,8,280),(192,256,352,280),(472,256,488,280)] if p=='PSP'
                    else [(416,0,424,24),(608,0,768,24),(888,0,904,24)])
            width=SPECS[p]['size'][0];start=SPECS[p]['pixels']
            for box in boxes:
                with self.subTest(platform=p,box=box):
                    x,y,z,w=box
                    for line in range(y,w):
                        a=start+line*width+x;b=start+line*width+z
                        self.assertEqual(data[a:b],updated[a:b])

    def test_rejects_unknown_source_artwork(self):
        for p,data in self.data.items():
            for row in banners.regions(p):
                if row['id'] not in NEW:continue
                with self.subTest(platform=p,caption=row['id']):
                    bad=bytearray(data);x,y,_,_=row['box']
                    bad[SPECS[p]['pixels']+y*SPECS[p]['size'][0]+x]^=1
                    with self.assertRaisesRegex(AssertionError,'Unknown caption artwork: '+row['id']):
                        banners.patch(bad,p,region_ids=[row['id']])

    def test_rejects_beam_coat_in_nattoru_crop(self):
        terms=json.loads(banners.TERMS.read_text(encoding='utf8'))
        next(r for r in terms['regions'] if r['id']=='nattoru_bullet')['box'][0]=320
        for p,data in self.data.items():
            with self.subTest(platform=p),mock_patch.object(banners.json,'loads',return_value=terms):
                with self.assertRaisesRegex(AssertionError,'adjacent Beam Coat'):
                    banners.patch(data,p,region_ids=['nattoru_bullet'])

    def test_full_words_fit_without_horizontal_rescaling(self):
        for p,data in self.data.items():
            _,report=banners.patch(data,p,region_ids=NEW)
            for row in report['regions']:
                with self.subTest(platform=p,caption=row['id']):
                    self.assertEqual(row['english'],row['text'])
                    self.assertGreaterEqual(row['cap_height'],15)
                    self.assertFalse(row['horizontal_rescaling'])
                    x,y,z,w=row['box'];a,b,c,d=row['ink_bounds']
                    self.assertTrue(x<a<c<z and y<b<d<w)


if __name__=='__main__':unittest.main()
