"""Regression checks for Tasks adapters and facial-action classification."""
import unittest
from dataclasses import replace
from types import SimpleNamespace as Result
from unittest.mock import MagicMock, patch
import numpy as np
from detector.task_runtime import prepare_frame, VideoTaskDetector
from detector.face_detector import FaceDetector
from detector.hand_detector import HandDetector
from detector.expression_classifier import ExpressionClassifier
from detector.gesture_classifier import classify_hand, classify_gesture


def middle_finger_landmarks():
    landmarks = [(0, 100, 0)] * 21
    landmarks[2], landmarks[3], landmarks[4] = (-30, 85, 0), (-20, 78, 0), (-15, 80, 0)
    for mcp, x in [(5, -20), (9, 0), (13, 20), (17, 35)]:
        landmarks[mcp] = (x, 55, 0)
        landmarks[mcp + 1] = (x, 35, 0)
        landmarks[mcp + 2] = (x, 60, 0)
        landmarks[mcp + 3] = (x, 75, 0)
    landmarks[12] = (0, 0, 0)
    return landmarks


class DetectionTests(unittest.TestCase):
    def test_middle_finger_recognizes_both_hands_and_rotated_poses(self):
        landmarks = middle_finger_landmarks()
        for points in [landmarks, [(-y, x, z) for x, y, z in landmarks],
                       [(-x, -y, z) for x, y, z in landmarks]]:
            for side in ['Left', 'Right']:
                self.assertEqual(classify_gesture(points, side), 'middle_finger')
        self.assertEqual(classify_hand({'landmarks': landmarks, 'handedness': 'Left',
                                       'gesture': 'fist'}), 'middle_finger')

    def test_middle_finger_rejects_folded_middle_and_multiple_extended_fingers(self):
        landmarks = middle_finger_landmarks()
        landmarks[12] = (0, 75, 0)
        self.assertNotEqual(classify_gesture(landmarks, 'Left'), 'middle_finger')
        landmarks = middle_finger_landmarks()
        landmarks[8] = (-20, 0, 0)
        self.assertNotEqual(classify_gesture(landmarks, 'Left'), 'middle_finger')

    def expression(self, **shapes):
        return ExpressionClassifier.classify({'blendshapes': shapes})

    def test_smile_uses_both_sides(self):
        self.assertEqual(self.expression(mouthSmileLeft=.9, mouthSmileRight=.9), ('happy', .9))

    def test_normal_blink_is_not_wink(self):
        self.assertEqual(self.expression(eyeBlinkLeft=.9, eyeBlinkRight=.9)[0], 'neutral')
        self.assertEqual(self.expression(eyeBlinkLeft=.9, eyeBlinkRight=.1)[0], 'wink')

    def test_open_mouth_alone_does_not_trigger_surprise(self):
        self.assertEqual(self.expression(jawOpen=.9)[0], 'neutral')
        self.assertEqual(self.expression(jawOpen=.9, eyeWideLeft=.9, eyeWideRight=.9)[0], 'surprised')

    def test_frown_requires_supporting_facial_movement(self):
        self.assertEqual(self.expression(mouthFrownLeft=.9, mouthFrownRight=.9)[0], 'neutral')
        self.assertEqual(self.expression(mouthFrownLeft=.9, mouthFrownRight=.9, browInnerUp=.8)[0], 'sad')
        self.assertEqual(self.expression(browDownLeft=.9, browDownRight=.9, mouthPressLeft=.8, mouthPressRight=.8)[0], 'angry')

    def test_preparation_converts_bgr_once(self):
        frame = prepare_frame(np.array([[[10, 20, 30]]], dtype=np.uint8))
        self.assertEqual(frame.image.numpy_view().tolist(), [[[30, 20, 10]]])

    def test_face_adapter_preserves_blendshapes_and_strict_timestamps(self):
        task = MagicMock()
        task.detect_for_video.return_value = Result(
            face_landmarks=[[Result(x=.5, y=.25, z=.1)]],
            face_blendshapes=[[Result(category_name='mouthSmileLeft', score=.9)]])
        detector = FaceDetector.__new__(FaceDetector)
        VideoTaskDetector.__init__(detector, task)
        frame = replace(prepare_frame(np.zeros((80, 100, 3), dtype=np.uint8)), timestamp_ms=100)
        result = detector.process(frame)
        detector.process(frame)
        self.assertEqual(result[0]['landmarks'], [(50, 20, .1)])
        self.assertEqual(result[0]['blendshapes'], {'mouthSmileLeft': .9})
        self.assertEqual([call.args[1] for call in task.detect_for_video.call_args_list], [100, 101])

    def test_hand_adapter_converts_model_category_to_action(self):
        task = MagicMock()
        task.recognize_for_video.return_value = Result(
            hand_landmarks=[[Result(x=.5, y=.25, z=.1)]],
            handedness=[[Result(category_name='Left')]],
            gestures=[[Result(category_name='Thumb_Up')]])
        detector = HandDetector.__new__(HandDetector)
        VideoTaskDetector.__init__(detector, task)
        result = detector.process(np.zeros((80, 100, 3), dtype=np.uint8))
        self.assertEqual(result[0]['gesture'], 'thumbs_up')
        self.assertEqual(result[0]['handedness'], 'Left')

    def test_model_pose_and_custom_pose_priority(self):
        hand = {'landmarks': [], 'handedness': 'Left', 'gesture': 'thumbs_up'}
        with patch('detector.gesture_classifier.classify_gesture', return_value='fist'):
            self.assertEqual(classify_hand(hand), 'thumbs_up')
        with patch('detector.gesture_classifier.classify_gesture', return_value='oneshot'):
            self.assertEqual(classify_hand(hand), 'oneshot')
