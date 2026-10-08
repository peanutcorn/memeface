"""Current Face Landmarker model: landmarks and 52 facial blendshape coefficients."""
from mediapipe.tasks.python import BaseOptions, vision
from detector.task_runtime import MODEL_DIR, VideoTaskDetector


class FaceDetector(VideoTaskDetector):
    def __init__(self):
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_DIR / 'face_landmarker.task')),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            output_face_blendshapes=True,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        super().__init__(vision.FaceLandmarker.create_from_options(options))

    def process(self, value):
        frame, timestamp = self.frame(value)
        result = self.task.detect_for_video(frame.image, timestamp)
        faces = []
        for landmarks, blendshapes in zip(result.face_landmarks, result.face_blendshapes):
            faces.append({
                'landmarks': [(p.x * frame.width, p.y * frame.height, p.z) for p in landmarks],
                'blendshapes': {category.category_name: category.score for category in blendshapes},
            })
        return faces
