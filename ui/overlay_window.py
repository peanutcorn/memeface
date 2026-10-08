"""Transparent, movable and resizable OBS overlay with native image proportions."""
from pathlib import Path
from io import BytesIO
from PIL import Image
from PyQt5.QtCore import Qt, QSize, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QMovie, QImageReader, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QSizePolicy, QMenu
from ui.images import load_pixmap


class AnimatedWebpLabel:
    def __init__(self, label, path):
        self.label = label
        self.frames = []
        self.durations = []
        self.index = 0
        self.timer = QTimer(label)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._next)
        with Image.open(path) as source:
            for index in range(source.n_frames):
                source.seek(index)
                frame = source.convert('RGBA')
                pm = QPixmap()
                buffer = BytesIO()
                frame.save(buffer, format='PNG')
                pm.loadFromData(buffer.getvalue())
                self.frames.append(pm)
                self.durations.append(max(20, int(source.info.get('duration', 100))))
        self._render()
        self.timer.start(self.durations[0])

    def _render(self):
        self.label.setPixmap(self.frames[self.index].scaled(
            self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _next(self):
        self.index = (self.index + 1) % len(self.frames)
        self._render()
        self.timer.start(self.durations[self.index])

    def stop(self):
        self.timer.stop()
        self.timer.deleteLater()


class OverlayWindow(QWidget):
    settings_requested = pyqtSignal()
    MIN_SIZE = 80
    RESIZE_ZONE = 20

    def __init__(self, default_path=None, error_paths=None, parent=None):
        super().__init__(parent)
        self.setObjectName('memefaceOverlay')
        self._default_path = Path(default_path) if default_path else None
        self._error_paths = [Path(p) for p in (error_paths or [])]
        self._current_path = None
        self._cached_pm = QPixmap()
        self._current_movie = None
        self._anim_webp = None
        self._drag_pos = None
        self._resize_origin = None
        self._resize_start = QSize()
        self._movie_size = QSize()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowTitle('Memeface Overlay')
        self.setMinimumSize(self.MIN_SIZE, self.MIN_SIZE)
        self.resize(400, 400)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - 440, screen.bottom() - 460)
        self.setMouseTracking(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.meme_label = QLabel(self)
        self.meme_label.setAlignment(Qt.AlignCenter)
        self.meme_label.setStyleSheet('background: transparent;')
        self.meme_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.meme_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        layout.addWidget(self.meme_label)
        self.show_default()

    def on_trigger(self, trigger, image_path):
        path = image_path if image_path and Path(image_path).is_file() else self._default_path
        if path:
            self._display(str(path))

    def show_default(self):
        if self._default_path and self._default_path.is_file():
            self._display(str(self._default_path))

    def show_error(self, message=''):
        if message:
            print(f'[Overlay] {message}')
        valid = [path for path in self._error_paths if path.is_file()]
        if valid:
            self._display(str(valid[0]))

    def _display(self, path):
        # Repeated state/config updates do not restart animations or flash the window.
        if path == self._current_path:
            return
        pixmap = load_pixmap(path)
        if pixmap.isNull():
            return
        self._stop_current()
        self._current_path = path
        self._cached_pm = pixmap
        suffix = Path(path).suffix.lower()
        if suffix == '.gif':
            self._current_movie = QMovie(path, parent=self)
            self._movie_size = QImageReader(path).size()
            self.meme_label.setMovie(self._current_movie)
            self._render()
            self._current_movie.start()
        elif suffix == '.webp':
            try:
                with Image.open(path) as source:
                    animated = getattr(source, 'is_animated', False)
                if animated:
                    self._anim_webp = AnimatedWebpLabel(self.meme_label, path)
                else:
                    self._render()
            except (OSError, ValueError):
                self._render()
        else:
            self._render()

    def _render(self):
        if self._current_movie:
            size = self._movie_size.scaled(self.size(), Qt.KeepAspectRatio)
            self._current_movie.setScaledSize(size)
        elif self._anim_webp:
            self._anim_webp._render()
        elif not self._cached_pm.isNull():
            self.meme_label.setPixmap(self._cached_pm.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _stop_current(self):
        if self._current_movie:
            self._current_movie.stop()
            self._current_movie.deleteLater()
            self._current_movie = None
        if self._anim_webp:
            self._anim_webp.stop()
            self._anim_webp = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_path:
            self._render()

    def _in_resize_zone(self, position):
        return position.x() >= self.width() - self.RESIZE_ZONE and position.y() >= self.height() - self.RESIZE_ZONE

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._in_resize_zone(event.pos()):
                self._resize_origin = event.globalPos()
                self._resize_start = self.size()
            else:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if self._resize_origin is not None:
                delta = event.globalPos() - self._resize_origin
                self.resize(max(self.MIN_SIZE, self._resize_start.width() + delta.x()),
                            max(self.MIN_SIZE, self._resize_start.height() + delta.y()))
            elif self._drag_pos is not None:
                self.move(event.globalPos() - self._drag_pos)
        else:
            self.setCursor(Qt.SizeFDiagCursor if self._in_resize_zone(event.pos()) else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_origin = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction('컨트롤룸 열기', self.settings_requested.emit)
        menu.addAction('크기 초기화', lambda: self.resize(400, 400))
        menu.addAction('오버레이 숨기기', self.hide)
        menu.exec_(event.globalPos())

    def closeEvent(self, event):
        self._stop_current()
        super().closeEvent(event)

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())
