# Memeface

웹캠의 표정과 손동작에 맞춰 밈 이미지를 표시하는 Windows 투명 오버레이 앱입니다.

## 실행

Python 3.10 이상과 웹캠이 필요합니다.

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe main.py
```

## 사용법

- 이미지를 선택해 미할당 행동을 연결하고 **사용할 행동**에서 감지 항목을 선택합니다.
- **반응 설정**에서 행동 확인 시간과 이미지 유지 시간을 조절합니다.
- 변경 후 **설정 저장**을 누르면 다음 실행에도 유지됩니다.
- 오버레이를 드래그해 이동하고 우하단을 드래그해 크기를 조절합니다.
- `Ctrl+Shift+M`: 오버레이 표시/숨기기. 트레이 더블 클릭: 컨트롤룸 열기.

OBS에서는 **창 캡처 → Memeface Overlay → Windows 그래픽 캡처**를 선택하세요.

## 개발

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
venv\Scripts\python.exe build.py --package
```

빌드 결과는 `dist/Memeface/Memeface.exe`입니다. 설정은 개발 실행 시 `config.json`, 배포 앱에서는 `%LOCALAPPDATA%\Memeface\config.json`에 저장됩니다.

MediaPipe Tasks로 얼굴과 손을 감지합니다. [모델 출처](models/SOURCES.md)
