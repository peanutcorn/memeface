"""Shared MediaPipe Tasks frame preparation and model resource paths."""
from dataclasses import dataclass
from pathlib import Path
import time
import cv2
import mediapipe as mp

MODEL_DIR = Path(__file__).resolve().parents[1] / 'models'


@dataclass(frozen=True)
class DetectionFrame:
    image: mp.Image
    timestamp_ms: int

    @property
    def width(self):
        return self.image.width

    @property
    def height(self):
        return self.image.height


def prepare_frame(bgr_frame):
    """Convert each camera frame once for both face and hand inference."""
    rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
    return DetectionFrame(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                          int(time.monotonic() * 1000))


class VideoTaskDetector:
    def __init__(self, task):
        self.task = task
        self._last_timestamp = -1

    def frame(self, value):
        frame = value if isinstance(value, DetectionFrame) else prepare_frame(value)
        # Tasks require strictly increasing timestamps, even for frames in the same millisecond.
        self._last_timestamp = max(frame.timestamp_ms, self._last_timestamp + 1)
        return frame, self._last_timestamp

    def close(self):
        self.task.close()
