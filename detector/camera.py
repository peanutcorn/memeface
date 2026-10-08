"""
camera.py — 웹캠 캡처 QThread
프레임을 30fps로 읽어 frame_ready 시그널로 방출합니다.

변경 이력
---------
- camera_error 시그널 추가:
    · cap.isOpened() 실패 시 즉시 방출
    · 연속 30프레임(~1 초) read 실패 시 방출
"""
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal


class CameraThread(QThread):
    frame_ready  = pyqtSignal(np.ndarray)   # BGR numpy array
    camera_error = pyqtSignal(str)           # 오류 메시지

    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._running = False
        self._frame_pending = False

    def run(self):
        self._running = True
        self._frame_pending = False
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS,          30)

        if not cap.isOpened():
            self.camera_error.emit(f'카메라 {self.camera_index}번을 열 수 없습니다.')
            cap.release()
            self._running = False
            return

        fail_count = 0
        while self._running:
            ret, frame = cap.read()
            if ret:
                fail_count = 0
                frame = cv2.flip(frame, 1)   # 좌우 반전 (거울 모드)
                if not self._frame_pending:
                    self._frame_pending = True
                    self.frame_ready.emit(frame)
            else:
                fail_count += 1
                if fail_count >= 30:          # ~1 초 연속 실패 → 오류
                    self.camera_error.emit(
                        f'카메라 {self.camera_index}번 연결이 끊어졌습니다.'
                    )
                    break
                self.msleep(33)

        cap.release()
        self._running = False

    def release_frame(self):
        """Allow a fresh frame after the GUI has processed the previous one."""
        self._frame_pending = False

    def stop(self):
        self._running = False
        self.wait()
