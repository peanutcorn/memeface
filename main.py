"""Memeface webcam detection and desktop overlay entry point."""
import os
import sys
import time
from pathlib import Path

for stream_name in ('stdout', 'stderr'):
    stream = getattr(sys, stream_name, None)
    if stream is not None:
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError, ValueError):
            pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from detector.camera import CameraThread
from detector.face_detector import FaceDetector
from detector.hand_detector import HandDetector
from detector.expression_classifier import ExpressionClassifier
from detector.gesture_classifier import classify_hand, classify_two_hand_gesture
from detector.task_runtime import prepare_frame
from detector.trigger_stabilizer import TriggerStabilizer
from mapper.meme_mapper import MemeMapper
from ui.overlay_window import OverlayWindow
from ui.settings_window import SettingsWindow
from ui.tray import TrayIcon
from ui.theme import apply_theme

ROOT = Path(__file__).resolve().parent
MEME_DIR = ROOT / 'meme'
# Bundled resources are read-only; frozen applications keep settings per user.
CONFIG_PATH = (Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Memeface' / 'config.json'
               if getattr(sys, 'frozen', False) else ROOT / 'config.json')
DEFAULT_PATH = MEME_DIR / 'default.png'
ERROR_PATHS = [MEME_DIR / 'error1.png', MEME_DIR / 'error2.png']


class AppController(QObject):
    trigger_changed = pyqtSignal(str, object)
    frame_processed = pyqtSignal()

    def __init__(self, mapper, parent=None):
        super().__init__(parent)
        self.mapper = mapper
        self.face_det = FaceDetector()
        self.hand_det = HandDetector()
        self.expr_clf = ExpressionClassifier()
        self.stabilizer = TriggerStabilizer(mapper.settings)
        self.paused = False

    def configure(self):
        self.stabilizer.configure(self.mapper.settings)
        current = self.stabilizer.current
        if not self.mapper.get_images(current):
            self.stabilizer.reset()
            current = 'neutral'
        path = self.mapper.get_image(current)
        self.trigger_changed.emit(current, str(path) if path else None)

    def set_paused(self, paused):
        self.paused = paused
        self.stabilizer.configure(self.mapper.settings)

    def on_frame(self, bgr_frame):
        try:
            if not self.paused:
                self._process_frame(bgr_frame)
        finally:
            self.frame_processed.emit()

    def _process_frame(self, bgr_frame):
        frame = prepare_frame(bgr_frame)
        hands = self.hand_det.process(frame)
        raw_gestures = [classify_hand(hand) for hand in hands]
        gesture = classify_two_hand_gesture(hands[0], hands[1], raw_gestures[:2]) if len(hands) >= 2 else None
        if gesture is None or not self.mapper.get_images(gesture):
            detected = [g for g in raw_gestures if g and self.mapper.get_images(g)]
            # MediaPipe may reorder hands: retain the active hand gesture when possible.
            current = self.stabilizer.current
            gesture = current if current in detected else next((g for g in detected if g), None)
        expression = None
        faces = self.face_det.process(frame)
        if faces:
            label, confidence = self.expr_clf.classify(faces[0])
            if confidence >= self.mapper.settings['confidence'] and label != 'neutral':
                expression = label
        combined = 'open_palm' in raw_gestures and expression == 'angry' and self.mapper.get_images('handup_fury')
        trigger = 'handup_fury' if combined else gesture or expression
        # An unmapped hand must not replace a useful face expression with the default image.
        if trigger and not self.mapper.get_images(trigger):
            trigger = expression if expression and self.mapper.get_images(expression) else None
        confirmed = self.stabilizer.update(trigger, time.monotonic() * 1000)
        if confirmed:
            path = self.mapper.get_image(confirmed)
            self.trigger_changed.emit(confirmed, str(path) if path else None)

    def close(self):
        self.face_det.close()
        self.hand_det.close()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    apply_theme(app)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName('Memeface')
    icon = QIcon(str(DEFAULT_PATH))
    app.setWindowIcon(icon)
    mapper = MemeMapper(MEME_DIR, CONFIG_PATH)
    controller = AppController(mapper)
    overlay = OverlayWindow(default_path=DEFAULT_PATH, error_paths=ERROR_PATHS)
    overlay.setWindowIcon(icon)
    settings = SettingsWindow(mapper)
    tray = TrayIcon(overlay, settings, app)
    controller.trigger_changed.connect(overlay.on_trigger)
    controller.trigger_changed.connect(settings.on_trigger)
    settings.settings_changed.connect(controller.configure)
    settings.pause_changed.connect(controller.set_paused)
    settings.overlay_requested.connect(overlay.toggle_visibility)
    overlay.settings_requested.connect(settings.show)
    controller.configure()
    camera = CameraThread(camera_index=0)
    camera.frame_ready.connect(controller.on_frame)
    controller.frame_processed.connect(camera.release_frame)
    camera.camera_error.connect(overlay.show_error)
    camera.camera_error.connect(settings.show_camera_error)
    camera.start()
    try:
        import keyboard
        # keyboard invokes callbacks on its own thread. Relay to Qt's GUI thread.
        keyboard.add_hotkey('ctrl+shift+m', settings.overlay_requested.emit)
    except Exception as exc:
        print(f'[Memeface] 단축키 등록 실패: {exc}')
    overlay.show()
    settings.show()

    def on_quit():
        camera.stop()
        controller.close()
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    app.aboutToQuit.connect(on_quit)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
