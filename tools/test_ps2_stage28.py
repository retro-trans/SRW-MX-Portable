"""Reject unsafe chapter-port inputs and preserve English through native wrapping."""
import struct
import unittest

import build_patch
import play_order
import ps2_stage28 as port


class Stage28Regression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = port.sources()[2]
        cls.font = port.read(port.ROOT / 'work/build/ps2/font_0.4.36/patch.json')
        cls.mapping = build_patch.load_translations([str(port.ROOT /
            'work/translation/en/script/stage28_campaign_full_merged.json')])

    def test_missing_translation_cannot_fall_back_to_japanese(self):
        mapping = dict(self.mapping['i055a'])
        texts = play_order.load(self.blocks['i055a'], 0)[1]
        del mapping[next(t for t in texts if t in mapping)]
        with self.assertRaises(AssertionError):
            port.rebuild(self.blocks['i055a'], mapping, self.font)

    def test_psp_only_opcode_cannot_enter_ps2_unadapted(self):
        raw = bytearray(self.blocks['i055a'])
        struct.pack_into('<I', raw, 32, 179)
        with self.assertRaisesRegex(AssertionError, 'PSP-only opcode'):
            port.rebuild(raw, self.mapping['i055a'], self.font)

    def test_native_reflow_preserves_approved_second_line(self):
        text = "Enough talk. Die... and take Masaki's blood with you...!"
        target = port.textfit.fit_dialogue('Ritsu', text)[0]
        self.assertGreater(max(port.native_width(line, self.font) for line in target.split('@')), 528)
        result = port.fit(target, self.font)
        self.assertLessEqual(max(port.native_width(line, self.font) for line in result.split('@')), 528)
        self.assertEqual(' '.join(result.replace('@', ' ').split()),
                         ' '.join(target.replace('@', ' ').split()))
        self.assertLessEqual(len(result.split('@')), 3)


if __name__ == '__main__':
    unittest.main()
