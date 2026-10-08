"""Shared static image loading, including WebP on Qt installations without plugins."""
import io
from pathlib import Path
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap


def load_pixmap(path, size=None):
    if not path or not Path(path).is_file():
        return QPixmap()
    pm = QPixmap(str(path))
    if pm.isNull():
        try:
            with Image.open(path) as source:
                buffer = io.BytesIO()
                source.convert('RGBA').save(buffer, format='PNG')
                pm.loadFromData(buffer.getvalue())
        except (OSError, ValueError):
            return QPixmap()
    if size:
        pm = pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pm
