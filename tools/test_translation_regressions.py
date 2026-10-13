"""Regression checks for accidentally erasing translated battle/source rows."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import battle_quotes
import strip_jp


class TranslationLossTests(unittest.TestCase):
    def test_build_rejects_missing_battle_english_before_parsing_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'unique.json').write_text(json.dumps({'q00000': {'raw':'source'}}), encoding='utf8')
            (root/'batch_00.en.json').write_text(json.dumps({'rows':[{'id':'q00000'}]}), encoding='utf8')
            with patch.object(battle_quotes, 'SRC', str(root)), patch.object(battle_quotes, 'OUT', str(root)):
                with self.assertRaisesRegex(ValueError, '1 missing English rows'):
                    battle_quotes.build_subfile(b'', b'')

    def test_guard_rejects_whitespace_english(self):
        with self.assertRaises(ValueError):
            battle_quotes.require_complete_translations({'q00000':{}}, {'q00000':'   '})

    def test_guard_accepts_complete_translations(self):
        value = {'q00000':'Hit!'}
        self.assertEqual(battle_quotes.require_complete_translations({'q00000':{}}, value), value)

    def test_export_does_not_truncate_previous_translation(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'work/translation/en/script'; folder.mkdir(parents=True)
            source, destination = folder/'chapter.json', folder/'chapter.en.json'
            source.write_text(json.dumps({'rows':[{'id':'line1','jp':'source text'}]}), encoding='utf8')
            before = json.dumps({'rows':[{'id':'line1','en':'Existing translation.'}]}).encode('utf8')
            destination.write_bytes(before)
            with self.assertRaisesRegex(ValueError, 'Refusing to erase 1 English rows'):
                strip_jp.main(directory)
            self.assertEqual(destination.read_bytes(), before)

    def test_export_rejects_removed_translated_id(self):
        with self.assertRaises(ValueError):
            strip_jp.reject_translation_loss({'rows':[{'id':'line1','en':'Existing'}]}, {'rows':[]}, 'fixture')

    def test_export_accepts_intentional_english_revision(self):
        strip_jp.reject_translation_loss({'rows':[{'id':'line1','en':'Before'}]},
                                        {'rows':[{'id':'line1','en':'After'}]}, 'fixture')


class NativeFooterAssemblerTests(unittest.TestCase):
    def test_ps2_footer_is_stable_after_psp_artwork_render(self):
        import ps2_title_footer
        import title_footer
        before = ps2_title_footer.block(0x7d9580, '0.4.33')[0]
        spec = title_footer.SPECS['PSP']
        width, height = spec['size']
        fixture = bytes(spec['offset'] + 1024 + width*height)
        title_footer.render(fixture, 'PSP', '0.4.33')
        after = ps2_title_footer.block(0x7d9580, '0.4.33')[0]
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
