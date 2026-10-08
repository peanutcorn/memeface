"""Current Gesture Recognizer model with landmarks for additional custom actions."""
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.components.processors import ClassifierOptions
from detector.task_runtime import MODEL_DIR, VideoTaskDetector

MODEL_GESTURES = {
    'Closed_Fist': 'fist', 'Open_Palm': 'open_palm', 'Pointing_Up': 'pointing',
    'Thumb_Down': 'thumbs_down', 'Thumb_Up': 'thumbs_up', 'Victory': 'peace',
}


class HandDetector(VideoTaskDetector):
    def __init__(self):
        options = vision.GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_DIR / 'gesture_recognizer.task')),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
            canned_gesture_classifier_options=ClassifierOptions(score_threshold=0.7),
        )
        super().__init__(vision.GestureRecognizer.create_from_options(options))

    def process(self, value):
        frame, timestamp = self.frame(value)
        result = self.task.recognize_for_video(frame.image, timestamp)
        hands = []
        for index, landmarks in enumerate(result.hand_landmarks):
            categories = result.gestures[index]
            category = categories[0] if categories else None
            hands.append({
                'landmarks': [(p.x * frame.width, p.y * frame.height, p.z) for p in landmarks],
                'handedness': result.handedness[index][0].category_name,
                'gesture': MODEL_GESTURES.get(category.category_name) if category else None,
            })
        return hands
