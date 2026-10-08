"""
tray.py — 시스템 트레이 아이콘

변경 이력
---------
- _make_icon(): assets/icon.png 대신 meme/default.png 우선 사용
"""
from pathlib import Path

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QColor


def _make_icon() -> QIcon:
    """아이콘 우선순위:
      1. meme/default.png  (사용자 지정 기본 이미지)
      2. assets/icon.png   (커스텀 트레이 아이콘)
      3. 단색 32×32 폴백
    """
    root = Path(__file__).parent.parent

    for candidate in (
        root / 'meme'   / 'default.png',
        root / 'assets' / 'icon.png',
    ):
        if candidate.exists():
            return QIcon(str(candidate))

    # 폴백: 단색 픽스맵
    pm = QPixmap(32, 32)
    pm.fill(QColor('#d83b32'))
    return QIcon(pm)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, overlay, settings_win, parent=None):
        super().__init__(_make_icon(), parent)
        self.overlay      = overlay
        self.settings_win = settings_win
        self._build_menu()
        self.activated.connect(self._on_activated)
        self.setToolTip('Memeface')
        self.show()

    def _build_menu(self):
        menu = QMenu()

        toggle_act = QAction('오버레이 표시/숨기기', self)
        toggle_act.triggered.connect(self.overlay.toggle_visibility)
        menu.addAction(toggle_act)

        settings_act = QAction('컨트롤룸 열기', self)
        settings_act.triggered.connect(self.settings_win.show)
        menu.addAction(settings_act)

        menu.addSeparator()

        quit_act = QAction('종료', self)
        quit_act.triggered.connect(QApplication.quit)
        menu.addAction(quit_act)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.settings_win.show()
