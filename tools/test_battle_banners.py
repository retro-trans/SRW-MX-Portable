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
        cls.public_data={}
        cls.support_data={}
        cls.double_data={}
        for platform,prefix,asset in [('PSP','SRWMX_EN_','/PSP_GAME/USRDIR/STATIC2_ADD.BIN'),
                                     ('PS2','SRWMX_PS2_EN_','/DATA/STATIC.BIN;1')]:
            cls.data[platform]=read_iso(str(ROOT/f'work/output/{prefix}0.4.35.iso'),[asset])[asset]
            cls.public_data[platform]=read_iso(str(ROOT/f'work/output/{prefix}0.4.47.iso'),[asset])[asset]
            cls.support_data[platform]=read_iso(str(ROOT/f'work/output/{prefix}0.4.48.iso'),[asset])[asset]
            cls.double_data[platform]=read_iso(str(ROOT/f'work/output/{prefix}0.4.49.iso'),[asset])[asset]

    def test_support_captions_preserve_public_translations_and_adjacent_artwork(self):
        support_ids={'support_attack','support_defend'}
        for platform,data in self.public_data.items():
            with self.subTest(platform=platform):
                updated,report=banners.patch(data,platform,region_ids=support_ids)
                changed={r['id'] for r in report['regions'] if not r['already_translated']}
                self.assertEqual(changed,support_ids)
                self.assertEqual(banners.patch(updated,platform,region_ids=support_ids)[0],updated)
                spec=SPECS[platform];width=spec['size'][0]
                # Assist Attack / Defend share Support Attack's row; Critical
                # shares Support Defend's row. Include both opposite edges.
                for x0,y0,x1,y1 in [(0,152,84,176),(168,152,240,176),
                                      (240,120,336,144),(420,120,440,144),
                                      (84,151,168,152),(84,176,168,177),
                                      (336,119,420,120),(336,144,420,145)]:
                    for y in range(y0,y1):
                        a=spec['pixels']+y*width+x0;z=a+x1-x0
                        self.assertEqual(data[a:z],updated[a:z])

    def test_double_attack_preserves_support_captions_and_red_neighbor(self):
        for platform,data in self.support_data.items():
            with self.subTest(platform=platform):
                updated,report=banners.patch(data,platform,region_ids=['double_attack'])
                self.assertEqual({r['id'] for r in report['regions'] if not r['already_translated']},
                                 {'double_attack'})
                self.assertEqual(banners.patch(data,platform,region_ids=['double_attack'])[0],updated)
                self.assertEqual(banners.patch(updated,platform,region_ids=['double_attack'])[0],updated)
                row=next(r for r in report['regions'] if r['id']=='double_attack')
                self.assertEqual(row['cap_height'],18)
                self.assertFalse(row['horizontal_rescaling'])
                spec=SPECS[platform];width=spec['size'][0]
                for x0,y0,x1,y1 in [(120,232,240,256),(0,231,120,232)]:
                    for y in range(y0,y1):
                        a=spec['pixels']+y*width+x0;z=a+x1-x0
                        self.assertEqual(data[a:z],updated[a:z])

    def test_six_reported_captions_preserve_all_earlier_artwork(self):
        new_ids={'open_get','cannot_attack','sword_cut','harmonic_field','after_image','barrier'}
        for platform,data in self.double_data.items():
            with self.subTest(platform=platform):
                updated,report=banners.patch(data,platform,region_ids=new_ids)
                self.assertEqual({r['id'] for r in report['regions'] if not r['already_translated']},new_ids)
                self.assertEqual(banners.patch(data,platform,region_ids=new_ids)[0],updated)
                self.assertEqual(banners.patch(updated,platform,region_ids=new_ids)[0],updated)
                self.assertTrue(report['palette_preserved'])
                self.assertTrue(report['all_other_pixels_and_bytes_preserved'])
                for row in report['regions']:
                    self.assertFalse(row['horizontal_rescaling'])
                    x,y,z,w=row['box'];a,b,c,d=row['ink_bounds']
                    self.assertTrue(x<a<c<z and y<b<d<w)

    def test_six_reported_captions_reject_unknown_source_pixels(self):
        new_ids={'open_get','cannot_attack','sword_cut','harmonic_field','after_image','barrier'}
        for platform,data in self.double_data.items():
            for row in banners.regions(platform):
                if row['id'] not in new_ids:continue
                with self.subTest(platform=platform,caption=row['id']):
                    altered=bytearray(data);spec=SPECS[platform]
                    x,y,_,_=row['box']
                    altered[spec['pixels']+y*spec['size'][0]+x]^=1
                    with self.assertRaisesRegex(AssertionError,'Unknown caption artwork: '+row['id']):
                        banners.patch(altered,platform,region_ids=[row['id']])

    def test_cannot_attack_preserves_red_warning_color(self):
        from patch_at_field import palette
        for platform,data in self.double_data.items():
            with self.subTest(platform=platform):
                updated,report=banners.patch(data,platform,region_ids=['cannot_attack'])
                pal=palette(updated,platform);spec=SPECS[platform];width=spec['size'][0]
                x,y,z,w=report['regions'][0]['box']
                colors=[pal[v] for j in range(y,w) for v in updated[spec['pixels']+j*width+x:spec['pixels']+j*width+z]]
                self.assertTrue(any(c[0]>2*max(c[1],c[2]) for c in colors))
                self.assertFalse(any(c[2]>2*max(c[0],c[1]) for c in colors))

    def test_warning_and_barrier_bounds_do_not_cut_source_letters(self):
        from patch_battle_hud import picture
        for platform,data in self.double_data.items():
            original=picture(data,platform)
            for row in banners.regions(platform):
                if row['id'] not in ('cannot_attack','barrier'):continue
                with self.subTest(platform=platform,caption=row['id']):
                    x,y,z,w=row['box']
                    # These slots end in transparent padding or a neighboring
                    # black outline, never in the colored body of a source
                    # letter. A too-short crop leaves Japanese strokes behind.
                    edge=original.crop((z-1,y,z,w))
                    self.assertFalse(any(c[3]>0 and max(c[:3])>64 for c in edge.getdata()))

    def test_unknown_double_attack_artwork_is_rejected(self):
        for platform,data in self.support_data.items():
            with self.subTest(platform=platform):
                altered=bytearray(data);spec=SPECS[platform]
                altered[spec['pixels']+232*spec['size'][0]]^=1
                with self.assertRaisesRegex(AssertionError,'Unknown caption artwork: double_attack'):
                    banners.patch(altered,platform)

    def test_unknown_support_artwork_is_rejected(self):
        for platform,data in self.public_data.items():
            for row in banners.regions(platform):
                if row['id'] not in ('support_attack','support_defend'):continue
                with self.subTest(platform=platform,caption=row['id']):
                    altered=bytearray(data);spec=SPECS[platform]
                    x,y,_,_=row['box']
                    altered[spec['pixels']+y*spec['size'][0]+x]^=1
                    with self.assertRaisesRegex(AssertionError,'Unknown caption artwork: '+row['id']):
                        banners.patch(altered,platform)

    def test_red_en_boundary_is_rejected(self):
        for caption,right in [('god_shadow',352),('double_attack',128)]:
            bad=copy.deepcopy(self.terms)
            next(r for r in bad['regions'] if r['id']==caption)['box'][2]=right
            for platform,data in self.data.items():
                with self.subTest(platform=platform,caption=caption),mock_patch.object(banners.json,'loads',return_value=bad):
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
