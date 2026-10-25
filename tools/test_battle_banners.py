"""Regression checks for the adjacent EN boundary and historical caption sets."""
import copy
import json
import unittest
from unittest.mock import patch as mock_patch
import patch_battle_banners as banners
from patch_at_field import ROOT,SPECS
from verify_text_build import read_iso


class BannerRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms=json.loads(banners.TERMS.read_text(encoding='utf-8'))
        cls.data={}
        for platform,prefix,asset in [('PSP','SRWMX_EN_','/PSP_GAME/USRDIR/STATIC2_ADD.BIN'),
                                     ('PS2','SRWMX_PS2_EN_','/DATA/STATIC.BIN;1')]:
            cls.data[platform]=read_iso(str(ROOT/f'work/output/{prefix}0.4.35.iso'),[asset])[asset]

    def test_red_en_boundary_is_rejected(self):
        bad=copy.deepcopy(self.terms)
        next(r for r in bad['regions'] if r['id']=='god_shadow')['box'][2]=352
        for platform,data in self.data.items():
            with self.subTest(platform=platform),mock_patch.object(banners.json,'loads',return_value=bad):
                with self.assertRaisesRegex(AssertionError,'adjacent red'):
                    banners.patch(data,platform)

    def test_field_captions_preserve_neighboring_labels(self):
        neighbors={
            'PSP': [(192,280,352,304),(104,376,152,400)],
            'PS2': [(608,24,768,48),(520,120,568,144)]}
        for platform,data in self.data.items():
            with self.subTest(platform=platform):
                updated,_=banners.patch(data,platform,region_ids=['distortion_field','te_sphere'])
                spec=SPECS[platform];width=spec['size'][0]
                for x0,y0,x1,y1 in neighbors[platform]:
                    for y in range(y0,y1):
                        a=spec['pixels']+y*width+x0;z=a+x1-x0
                        self.assertEqual(data[a:z],updated[a:z])
                self.assertNotEqual(updated,data)
                self.assertEqual(banners.patch(updated,platform,region_ids=['distortion_field','te_sphere'])[0],updated)

    def test_historical_subset_does_not_add_later_caption(self):
        for platform,data in self.data.items():
            with self.subTest(platform=platform):
                self.assertEqual(banners.patch(data,platform,region_ids=['assist_attack','simultaneous_attack'])[0],data)
                translated,_=banners.patch(data,platform)
                self.assertNotEqual(translated,data)
                self.assertEqual(banners.patch(translated,platform)[0],translated)

    def test_unrecognized_caption_pixels_are_preserved_by_rejection(self):
        for platform,data in self.data.items():
            with self.subTest(platform=platform):
                altered=bytearray(data);spec=SPECS[platform]
                position=spec['pixels']+48*spec['size'][0]+240
                altered[position]^=1
                with self.assertRaisesRegex(AssertionError,'Unknown caption artwork: god_shadow'):
                    banners.patch(altered,platform)


if __name__=='__main__':unittest.main()
