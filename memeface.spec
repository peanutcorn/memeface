# -*- mode: python ; coding: utf-8 -*-
"""Package the Tasks C runtime, pinned model bundles and desktop UI."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

ROOT = Path(SPECPATH)
datas = collect_data_files('mediapipe', include_py_files=False)
datas += [(str(ROOT / 'meme'), 'meme'), (str(ROOT / 'models'), 'models')]
hiddenimports = [
    'cv2', 'numpy', 'keyboard', 'PIL.Image',
    'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'mediapipe.tasks.python.vision.face_landmarker',
    'mediapipe.tasks.python.vision.gesture_recognizer',
    'mediapipe.tasks.python.core.mediapipe_c_bindings',
]
a = Analysis(
    [str(ROOT / 'main.py')], pathex=[str(ROOT)],
    binaries=collect_dynamic_libs('mediapipe'), datas=datas,
    hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'tensorflow', 'jax', 'jaxlib',
              'onnxruntime', 'pandas', 'tkinter', 'PyQt6', 'PySide2', 'PySide6',
              'IPython', 'jupyter', 'notebook', 'sphinx'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='Memeface',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    icon=str(ROOT / 'build_icon.ico') if (ROOT / 'build_icon.ico').exists() else None,
    version=str(ROOT / 'version_info.txt') if (ROOT / 'version_info.txt').exists() else None,
    uac_admin=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Memeface')
