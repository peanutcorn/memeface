import json
import tempfile
import unittest
from pathlib import Path
from mapper.meme_mapper import MemeMapper

ROOT = Path(__file__).resolve().parents[1]


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = Path(self.directory.name) / 'config.json'
        self.mapper = MemeMapper(ROOT / 'meme', self.config)

    def test_repeated_action_has_one_fixed_image(self):
        paths = {self.mapper.get_image('happy') for _ in range(100)}
        self.assertEqual(paths, {ROOT / 'meme' / 'pepe_happy.png'})

    def test_one_image_can_only_have_one_action(self):
        path = self.mapper.get_image('happy')
        self.mapper.assign_image(path, 'peace')
        self.assertNotIn('happy', self.mapper.mappings)
        self.assertEqual(self.mapper.assigned_action(path), 'peace')
        self.assertEqual(self.mapper.get_image('peace'), path)
        self.assertIsNone(self.mapper.assigned_action(ROOT / 'meme' / 'double_piece.png'))

    def test_disabled_action_has_no_output(self):
        self.mapper.set_enabled('happy', False)
        self.assertIsNone(self.mapper.get_image('happy'))
        self.assertIn('happy', self.mapper.mappings)

    def test_unassignment_is_persisted(self):
        path = self.mapper.get_image('happy')
        self.mapper.assign_image(path, None)
        self.mapper.save_config()
        restored = MemeMapper(ROOT / 'meme', self.config)
        self.assertNotIn('happy', restored.mappings)

    def test_custom_preset_restores_mapping_and_enabled_actions(self):
        path = ROOT / 'meme' / 'wow.png'
        self.mapper.assign_image(path, 'happy')
        self.mapper.enabled = {'happy', 'peace'}
        self.mapper.save_preset('테스트 객체')
        self.mapper.save_config()
        restored = MemeMapper(ROOT / 'meme', self.config)
        restored.apply_preset('기본')
        restored.apply_preset('테스트 객체')
        self.assertEqual(restored.enabled, {'happy', 'peace'})
        self.assertEqual(restored.get_image('happy'), path)

    def test_face_preset_ignores_hands(self):
        self.mapper.enabled = {'happy', 'sad', 'angry', 'surprised', 'wink', 'neutral'}
        self.mapper.save_preset('표정 테스트')
        self.mapper.apply_preset('기본')
        self.mapper.apply_preset('표정 테스트')
        self.assertIsNone(self.mapper.get_image('thumbs_up'))
        self.assertIsNotNone(self.mapper.get_image('happy'))

    def test_default_is_the_only_initial_preset_and_maps_middle_finger(self):
        self.assertEqual(self.mapper.preset_names(), ['기본'])
        self.assertEqual(self.mapper.preset_name, '기본')
        self.assertEqual(self.mapper.get_image('middle_finger'), ROOT / 'meme' / 'fku.png')

    def test_all_presets_have_unique_images(self):
        for name in self.mapper.preset_names():
            self.mapper.apply_preset(name)
            paths = [p for images in self.mapper.mappings.values() for p in images]
            self.assertEqual(len(paths), len(set(paths)), name)

    def test_reserved_files_are_rejected(self):
        with self.assertRaises(ValueError):
            self.mapper.set_mapping('happy', ROOT / 'meme' / 'default.png')

    def test_imported_image_survives_save_and_reload(self):
        self.mapper.import_image(ROOT / 'meme' / 'wow.png')
        self.mapper.save_config()
        restored = MemeMapper(ROOT / 'meme', self.config)
        self.assertIn(ROOT / 'meme' / 'wow.png', restored.imported_images)

    def test_internal_paths_are_relative(self):
        config = ROOT / 'meme' / 'unused-config.json'
        self.mapper.config_path = config
        value = self.mapper._mapping_config()['happy']
        self.assertEqual(value, 'meme/pepe_happy.png')

    def test_bundle_image_path_resolves_independent_of_config_location(self):
        self.assertEqual(self.mapper._resolve('meme/pepe_happy.png'), ROOT / 'meme' / 'pepe_happy.png')

    def test_legacy_config_ignores_reserved_mapping(self):
        self.config.write_text(json.dumps({'version': 1, 'mappings': {
            'neutral': str(ROOT / 'meme' / 'default.png'),
            'happy': str(ROOT / 'meme' / 'smile.png')}}), encoding='utf-8')
        restored = MemeMapper(ROOT / 'meme', self.config)
        self.assertEqual(restored.get_image('happy'), ROOT / 'meme' / 'smile.png')
        self.assertNotEqual(restored.get_image('neutral'), ROOT / 'meme' / 'default.png')
