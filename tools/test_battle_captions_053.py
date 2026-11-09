"""AT Field caption against actual .52 resources and neighboring artwork."""
import unittest
from patch_at_field import ROOT,SPECS
from patch_battle_banners import patch,regions
from verify_text_build import read_iso

NEW='at_field_neutralized'


class Caption053Regression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data={}
        for p,prefix,asset in [('PSP','SRWMX_EN_','/PSP_GAME/USRDIR/STATIC2_ADD.BIN'),
                               ('PS2','SRWMX_PS2_EN_','/DATA/STATIC.BIN;1')]:
            cls.data[p]=read_iso(str(ROOT/f'work/output/{prefix}0.4.52.iso'),[asset])[asset]

    def test_only_new_caption_changes_and_twenty_earlier_captions_stay(self):
        for p,data in self.data.items():
            with self.subTest(platform=p):
                updated,report=patch(data,p,version='0.4.53')
                self.assertEqual([r['id'] for r in report['regions'] if not r['already_translated']],[NEW])
                self.assertEqual(sum(r['already_translated'] for r in report['regions']),20)
                self.assertEqual(updated,patch(data,p,region_ids=[NEW])[0])
                self.assertEqual(updated,patch(updated,p,version='0.4.53')[0])
                self.assertEqual(data,patch(data,p,region_ids=['sword_cut'])[0])

    def test_neighboring_cross_manager_outline_and_unit_labels_stay(self):
        for p,data in self.data.items():
            updated,_=patch(data,p,version='0.4.53')
            x,y,z,w=next(r['box'] for r in regions(p) if r['id']==NEW)
            width=SPECS[p]['size'][0];start=SPECS[p]['pixels']
            # The previous caption's black descenders extend onto y-1.
            # Also preserve the adjacent left/right labels and row below.
            for box in [(x,y-1,z,y),(x-8,y,x,w),(z,y,z+16,w),(x,w,z,w+24)]:
                with self.subTest(platform=p,box=box):
                    a,b,c,d=box
                    for yy in range(b,d):
                        lo=start+yy*width+a;hi=start+yy*width+c
                        self.assertEqual(data[lo:hi],updated[lo:hi])

    def test_full_label_fits_and_palette_stays(self):
        for p,data in self.data.items():
            _,report=patch(data,p,region_ids=[NEW])
            row=report['regions'][0]
            with self.subTest(platform=p):
                self.assertEqual(row['text'],'AT Field Neutralized')
                self.assertEqual(row['english'],row['text'])
                self.assertGreaterEqual(row['cap_height'],17)
                self.assertFalse(row['horizontal_rescaling'])
                self.assertTrue(report['palette_preserved'])
                self.assertTrue(report['all_other_pixels_and_bytes_preserved'])

    def test_rejects_unknown_source_artwork(self):
        for p,data in self.data.items():
            row=next(r for r in regions(p) if r['id']==NEW)
            bad=bytearray(data);x,y,_,_=row['box']
            bad[SPECS[p]['pixels']+y*SPECS[p]['size'][0]+x]^=1
            with self.subTest(platform=p),self.assertRaisesRegex(AssertionError,'Unknown caption artwork: '+NEW):
                patch(bad,p,region_ids=[NEW])


if __name__=='__main__':unittest.main()
