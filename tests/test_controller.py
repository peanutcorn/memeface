import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
import main
from mapper.meme_mapper import MemeMapper

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.mapper = MemeMapper(ROOT / 'meme', Path(self.directory.name) / 'config.json')
        with patch.object(main, 'FaceDetector'), patch.object(main, 'HandDetector'), patch.object(main, 'ExpressionClassifier'):
            self.controller = main.AppController(self.mapper)
        self.controller.face_det.process.return_value = [[]]
        self.controller.expr_clf.classify.return_value = ('happy', .95)
        self.controller.hand_det.process.return_value = [{'landmarks': [], 'handedness': 'Left'}]
        self.events = []
        self.controller.trigger_changed.connect(lambda key, path: self.events.append((key, path)))

    def run_frames(self, gesture):
        with patch.object(main, 'prepare_frame'), patch.object(main, 'classify_hand', return_value=gesture):
            with patch.object(main.time, 'monotonic', return_value=0):
                self.controller.on_frame(None)
            with patch.object(main.time, 'monotonic', return_value=.65):
                self.controller.on_frame(None)

    def test_disabled_hand_does_not_mask_face(self):
        self.mapper.enabled = {'happy'}
        self.run_frames('thumbs_up')
        self.assertEqual(self.events[0][0], 'happy')

    def test_middle_finger_displays_fku_after_confirmation(self):
        self.run_frames('middle_finger')
        self.assertEqual(self.events[0][0], 'middle_finger')
        self.assertEqual(Path(self.events[0][1]).name, 'fku.png')

    def test_combo_can_be_enabled_without_its_components(self):
        self.mapper.enabled = {'handup_fury'}
        self.controller.expr_clf.classify.return_value = ('angry', .95)
        self.run_frames('open_palm')
        self.assertEqual(self.events[0][0], 'handup_fury')

    def test_pausing_preserves_output_and_releases_camera_frame(self):
        self.controller.set_paused(True)
        released = []
        self.controller.frame_processed.connect(lambda: released.append(True))
        self.controller.on_frame(None)
        self.controller.hand_det.process.assert_not_called()
        self.assertEqual(self.events, [])
        self.assertEqual(released, [True])

    def test_changing_current_mapping_updates_output(self):
        self.controller.stabilizer.current = 'happy'
        self.mapper.set_mapping('happy', ROOT / 'meme' / 'wow.png')
        self.controller.configure()
        self.assertEqual(Path(self.events[0][1]).name, 'wow.png')
