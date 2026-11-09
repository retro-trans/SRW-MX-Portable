"""Structural and width checks on actual .54 source resources."""
import unittest
import re
from name_consistency_055 import *


class NameConsistency055(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data={}
        for p,prefix in [('PSP','SRWMX_EN_'),('PS2','SRWMX_PS2_EN_')]:
            cls.data[p]=read_iso(str(ROOT/f'work/output/{prefix}0.4.54.iso'),ASSETS[p])

    def test_all_nine_names_fit_and_keep_numbered_variants(self):
        for p,data in self.data.items():
            with self.subTest(platform=p):
                result,report=patch(data[ASSETS[p][0]],p)
                self.assertEqual(len(report['regions']),9)
                for row in report['regions']:
                    self.assertLessEqual(line_width(row['text'],p),160 if p=='PSP' else 240)
                    self.assertEqual(re.findall(r'\(\d\)',row['text']),re.findall(r'\(\d\)',ROWS[int(row['id'][5:])][0]))
                self.assertEqual(patch(result,p)[0],result)
                self.assertTrue(report['native_name_pointers_preserved'])

    def test_thirteen_speaker_corrections_preserve_all_203_command_streams(self):
        for p,data in self.data.items():
            _,elf,maps=ASSETS[p];base,rel=script_layout(data[elf],p)
            result,report=patch_story(data[maps],data[elf],p)
            self.assertEqual(len(report['changed_strings']),13)
            self.assertEqual({r['block'] for r in report['changed_strings']},{65,188})
            changed={(r['block'],r['slot']) for r in report['changed_strings']}
            for i,(a,b) in enumerate(zip(rel,rel[1:])):
                before_cmd,before=play_order.load(data[maps][base+a*2048:base+b*2048],0)
                after_cmd,after=play_order.load(result[base+a*2048:base+b*2048],0)
                self.assertEqual(before_cmd,after_cmd)
                self.assertEqual(len(before),len(after))
                for slot,(x,y) in enumerate(zip(before,after)):
                    if (i,slot) not in changed:self.assertEqual(x,y)
                    else:
                        expected=decode_english(x).replace('Galfa','Gulfer')
                        self.assertEqual(' '.join(expected.replace('@',' ').split()),
                                         ' '.join(decode_english(y).replace('@',' ').split()))
            self.assertEqual(patch_story(result,data[elf],p)[0],result)

    def test_reflow_stays_inside_native_dialogue_limits(self):
        for p,data in self.data.items():
            _,elf,maps=ASSETS[p];_,report=patch_story(data[maps],data[elf],p)
            self.assertGreater(sum(r['reflowed'] for r in report['changed_strings']),0)
            self.assertTrue(all(len(r['line_widths'])<=3 and max(r['line_widths'])<=(352 if p=='PSP' else 528)
                                for r in report['changed_strings']))

    def test_unknown_name_artifacts_are_rejected(self):
        for p,data in self.data.items():
            raw=data[ASSETS[p][0]];_,report=patch(raw,p)
            corrupt=bytearray(raw);corrupt[int(report['regions'][0]['offset'],16)]^=1
            with self.assertRaisesRegex(AssertionError,'Unknown Mazinger name'):patch(corrupt,p)


if __name__=='__main__':unittest.main()
