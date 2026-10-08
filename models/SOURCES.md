# 감지 모델 기록

확인·다운로드 날짜: 2026-10-08 (Asia/Seoul). 공식 PyPI 최신 MediaPipe 1.1.0의 Windows AMD64 패키지에서 실행을 검증했습니다.

- [공식 MediaPipe 패키지](https://pypi.org/project/mediapipe/1.1.0/)
- [Face Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/index)
- [Gesture Recognizer](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer)

두 모델은 공식 문서가 제공하는 Latest 모델 번들입니다. Latest 주소의 내용은 바뀔 수 있으므로 아래 SHA-256으로 이 프로젝트에 포함된 파일을 식별합니다. 새 모델이 실제 웹캠에서 더 정확한지는 별도 측정이 필요합니다.

| 파일 | 다운로드 | SHA-256 |
|---|---|---|
| face_landmarker.task | [Google 원본](https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task) | `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff` |
| gesture_recognizer.task | [Google 원본](https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task) | `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482` |

공식 공개 검사 이미지 portrait.jpg와 thumb_up.jpg에서 얼굴 1개와 엄지 위 행동 1개를 확인했습니다. 모델 구성·결과 변환·표정 규칙은 tests/test_detection.py에서도 검사합니다.
