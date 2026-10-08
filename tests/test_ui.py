import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from mapper.meme_mapper import MemeMapper
from mapper.presets import ACTION_LABELS
from ui.settings_window import SettingsWindow
from ui.overlay_window import OverlayWindow

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])


class UiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.mapper = MemeMapper(ROOT / 'meme', Path(self.directory.name) / 'config.json')

    def test_cards_and_selected_details_show_only_action_names(self):
        window = SettingsWindow(self.mapper)
        self.addCleanup(window.close)
        for index in range(window.library.count()):
            item = window.library.item(index)
            action = self.mapper.assigned_action(Path(item.data(Qt.UserRole)))
            self.assertEqual(item.text(), ACTION_LABELS.get(action, '미할당'))
        self.assertEqual(window.action_name.text(), '웃음')
        self.assertFalse(hasattr(window, 'filter'))

    def test_popup_excludes_all_assigned_actions_and_refreshes_after_release(self):
        window = SettingsWindow(self.mapper)
        self.addCleanup(window.close)
        self.assertEqual(window.assignment.currentData(), 'happy')
        for index in range(window.assignment.count()):
            if not window.assignment.view().isRowHidden(index):
                self.assertNotIn(window.assignment.itemData(index), self.mapper.mappings)
        window.assignment.setCurrentIndex(0)
        self.assertNotIn('happy', self.mapper.mappings)
        happy = window.assignment.findData('happy')
        self.assertGreaterEqual(happy, 0)
        self.assertFalse(window.assignment.view().isRowHidden(happy))
        self.assertEqual(window.notice.text(), '')

    def test_pause_and_live_status_do_not_include_removed_hints(self):
        window = SettingsWindow(self.mapper)
        self.addCleanup(window.close)
        window.pause.click()
        self.assertEqual(window.live.text(), '감지 일시정지')
        window.pause.click()
        self.assertEqual(window.live.text(), '감지 중')
        window.on_trigger('happy', str(ROOT / 'meme' / 'pepe_happy.png'))
        self.assertEqual(window.live.text(), '감지 중 · 웃음')

    def test_library_assignment_and_action_selection(self):
        window = SettingsWindow(self.mapper)
        self.addCleanup(window.close)
        window.show()
        APP.processEvents()
        for index in range(window.library.count()):
            item = window.library.item(index)
            if Path(item.data(Qt.UserRole)).name == 'pepe_happy.png':
                window.library.setCurrentItem(item)
                break
        # Already assigned actions cannot be selected for another image.
        self.assertEqual(window.assignment.findData('thumbs_up'), -1)
        window.assignment.setCurrentIndex(window.assignment.findData('heart'))
        self.assertEqual(self.mapper.get_image('heart').name, 'pepe_happy.png')
        self.assertNotIn('happy', self.mapper.mappings)
        window._checks['heart'].setChecked(False)
        self.assertIsNone(self.mapper.get_image('heart'))
        events = []
        window.overlay_requested.connect(lambda: events.append('toggle'))
        for button in window.findChildren(__import__('PyQt5.QtWidgets', fromlist=['QPushButton']).QPushButton):
            if button.text() == '오버레이 표시 / 숨기기':
                button.click()
        self.assertEqual(events, ['toggle'])
        window.pause.click()
        self.assertTrue(window.pause.isChecked())

    def test_overlay_preserves_aspect_and_resizes_webp(self):
        overlay = OverlayWindow(default_path=ROOT / 'meme' / 'default.png')
        self.addCleanup(overlay.close)
        overlay.show()
        overlay.resize(300, 150)
        overlay.on_trigger('happy', str(ROOT / 'meme' / 'pepe_happy.png'))
        APP.processEvents()
        pixmap = overlay.meme_label.pixmap()
        self.assertEqual((pixmap.width(), pixmap.height()), (150, 150))
        overlay.on_trigger('heart', str(ROOT / 'meme' / 'fk.webp'))
        overlay.resize(160, 240)
        APP.processEvents()
        self.assertLessEqual(overlay.meme_label.pixmap().width(), 160)
        self.assertLessEqual(overlay.meme_label.pixmap().height(), 240)

    def test_animated_webp_preserves_player_for_same_image(self):
        path = Path(self.directory.name) / 'animated.webp'
        Image.new('RGBA', (40, 20), 'red').save(path, save_all=True,
            append_images=[Image.new('RGBA', (40, 20), 'blue')], duration=[80, 120], loop=0)
        overlay = OverlayWindow()
        self.addCleanup(overlay.close)
        overlay.on_trigger('happy', str(path))
        self.assertIsNotNone(overlay._anim_webp)
        player = overlay._anim_webp
        overlay.on_trigger('happy', str(path))
        self.assertIs(overlay._anim_webp, player)
        self.assertEqual(player.durations, [80, 120])
