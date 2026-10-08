"""Character presets, image/action assignments and calm detection controls."""
from pathlib import Path
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTabWidget, QComboBox, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView, QCheckBox, QScrollArea, QFormLayout,
    QSpinBox, QDoubleSpinBox, QFileDialog, QInputDialog, QMessageBox,
)
from mapper.presets import ACTIONS, ACTION_LABELS
from ui.images import load_pixmap
from ui.theme import LIGHT_THEME




def label(text, muted=False):
    widget = QLabel(text)
    widget.setWordWrap(True)
    if muted:
        widget.setObjectName('muted')
    return widget


class SettingsWindow(QWidget):
    settings_changed = pyqtSignal()
    pause_changed = pyqtSignal(bool)
    overlay_requested = pyqtSignal()

    def __init__(self, mapper, parent=None):
        super().__init__(parent)
        self.mapper = mapper
        self.selected_path = None
        self._checks = {}
        self._controls = {}
        self.setWindowTitle('Memeface · 컨트롤룸')
        self.resize(1060, 800)
        self.setMinimumSize(860, 650)
        self.setStyleSheet(LIGHT_THEME)
        self._setup_ui()
        self._refresh_presets()
        self.refresh()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)
        header = QHBoxLayout()
        title = label('Memeface')
        title.setObjectName('title')
        header.addWidget(title)
        header.addStretch()
        self.pause = QPushButton('감지 일시정지')
        self.pause.setCheckable(True)
        self.pause.toggled.connect(self._pause)
        header.addWidget(self.pause)
        toggle = QPushButton('오버레이 표시 / 숨기기')
        toggle.clicked.connect(self.overlay_requested.emit)
        header.addWidget(toggle)
        root.addLayout(header)
        self.live = label('카메라 연결 중', True)
        root.addWidget(self.live)
        preset_bar = QHBoxLayout()
        preset_bar.addWidget(label('객체 프리셋'))
        self.presets = QComboBox()
        self.presets.setMinimumWidth(190)
        preset_bar.addWidget(self.presets)
        apply = QPushButton('적용')
        apply.clicked.connect(self._apply_preset)
        preset_bar.addWidget(apply)
        custom = QPushButton('현재 구성을 프리셋으로 저장')
        custom.clicked.connect(self._save_preset)
        preset_bar.addWidget(custom)
        preset_bar.addStretch()
        root.addLayout(preset_bar)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._library_tab(), '이미지 · 행동 할당')
        self.tabs.addTab(self._actions_tab(), '사용할 행동')
        self.tabs.addTab(self._behavior_tab(), '반응 설정')
        root.addWidget(self.tabs, 1)
        footer = QHBoxLayout()
        self.notice = label('', True)
        footer.addWidget(self.notice, 1)
        save = QPushButton('설정 저장')
        save.setObjectName('primary')
        save.clicked.connect(self._save)
        footer.addWidget(save)
        root.addLayout(footer)

    def _library_tab(self):
        page = QWidget()
        body = QHBoxLayout(page)
        body.setContentsMargins(0, 16, 0, 0)
        left = QVBoxLayout()
        tools = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('이미지 또는 행동 검색')
        self.search.textChanged.connect(self._filter)
        tools.addWidget(self.search)
        add = QPushButton('+ 이미지 추가')
        add.clicked.connect(self._import)
        tools.addWidget(add)
        left.addLayout(tools)
        self.library = QListWidget()
        self.library.setViewMode(QListWidget.IconMode)
        self.library.setResizeMode(QListWidget.Adjust)
        self.library.setMovement(QListWidget.Static)
        self.library.setIconSize(QSize(100, 100))
        self.library.setGridSize(QSize(164, 160))
        self.library.setWordWrap(True)
        self.library.setSelectionMode(QAbstractItemView.SingleSelection)
        self.library.currentItemChanged.connect(self._select)
        left.addWidget(self.library, 1)
        body.addLayout(left, 1)
        panel = QFrame()
        panel.setObjectName('panel')
        panel.setFixedWidth(270)
        side = QVBoxLayout(panel)
        side.setContentsMargins(18, 18, 18, 18)
        side.addWidget(label('선택한 이미지'))
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(232, 210)
        side.addWidget(self.preview)
        self.action_name = label('이미지를 선택하세요', True)
        side.addWidget(self.action_name)
        side.addSpacing(16)
        side.addWidget(label('이 이미지의 행동'))
        self.assignment = QComboBox()
        self.assignment.currentIndexChanged.connect(self._assign)
        side.addWidget(self.assignment)
        side.addWidget(label('미할당 행동만 선택할 수 있습니다.', True))
        side.addStretch()
        side.addWidget(label('Ctrl + Shift + M  ·  오버레이 토글\n오버레이 드래그  ·  위치 이동\n우하단 드래그  ·  크기 조절', True))
        body.addWidget(panel)
        return page

    def _actions_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(label('감지에 사용할 행동만 선택하세요. 이미지가 없는 행동은 감지에 반영되지 않습니다.', True))
        buttons = QHBoxLayout()
        for text, enabled in [('이미지가 있는 행동 모두 선택', True), ('모두 해제', False)]:
            button = QPushButton(text)
            button.clicked.connect(lambda _, value=enabled: self._select_actions(value))
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        rows = QVBoxLayout(container)
        previous_group = None
        for key, text, group in ACTIONS:
            if group != previous_group:
                heading = label(group)
                heading.setObjectName('groupHeading')
                rows.addWidget(heading)
                previous_group = group
            check = QCheckBox(text)
            check.toggled.connect(lambda value, action=key: self._enable(action, value))
            rows.addWidget(check)
            self._checks[key] = check
        rows.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        return page

    def _behavior_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(label('작은 움직임은 넘기고, 의도한 행동에만 반응하도록 조절하세요.', True))
        form = QFormLayout()
        form.setVerticalSpacing(18)
        for key, text, low, high in [
            ('confirm_ms', '행동 확인 시간', 150, 2000),
            ('hold_ms', '이미지 최소 유지 시간', 500, 6000),
            ('neutral_ms', '대기로 돌아가기 전 대기 시간', 500, 8000),
        ]:
            control = QSpinBox()
            control.setRange(low, high)
            control.setSingleStep(50)
            control.setSuffix(' ms')
            control.setValue(int(self.mapper.settings[key]))
            control.valueChanged.connect(self._change_behavior)
            self._controls[key] = control
            form.addRow(text, control)
        confidence = QDoubleSpinBox()
        confidence.setRange(0.5, 0.95)
        confidence.setSingleStep(0.01)
        confidence.setValue(self.mapper.settings['confidence'])
        confidence.valueChanged.connect(self._change_behavior)
        self._controls['confidence'] = confidence
        form.addRow('표정 최소 강도', confidence)
        layout.addLayout(form)
        layout.addWidget(label('확인 시간을 늘리면 순간적인 오인식을 줄입니다. 최소 유지 시간을 늘리면 이미지 전환이 덜 잦아집니다. 대기 시간이 지나도 새 행동을 확인한 뒤 전환합니다.', True))
        layout.addStretch()
        return page

    def refresh(self):
        selected = self.selected_path
        self.library.blockSignals(True)
        self.library.clear()
        for path in self.mapper.available_images():
            action = self.mapper.assigned_action(path)
            title = ACTION_LABELS.get(action, '미할당')
            pixmap = load_pixmap(path, 100)
            icon = QIcon(pixmap)
            icon.addPixmap(pixmap, QIcon.Selected, QIcon.Off)
            icon.addPixmap(pixmap, QIcon.Selected, QIcon.On)
            item = QListWidgetItem(icon, title)
            item.setSizeHint(QSize(148, 150))
            item.setData(Qt.UserRole, str(path))
            item.setToolTip(f'{path.name}\n행동: {title}')
            item.setTextAlignment(Qt.AlignCenter)
            self.library.addItem(item)
            if path == selected:
                self.library.setCurrentItem(item)
        if self.library.currentItem() is None and self.library.count():
            self.library.setCurrentRow(0)
        self.library.blockSignals(False)
        for action, check in self._checks.items():
            check.blockSignals(True)
            check.setChecked(action in self.mapper.enabled)
            assigned = action in self.mapper.mappings
            check.setText(ACTION_LABELS[action] if assigned else f'{ACTION_LABELS[action]} · 미할당')
            check.blockSignals(False)
        self._filter()
        self._select(self.library.currentItem())

    def _filter(self, *_):
        query = self.search.text().casefold()
        for index in range(self.library.count()):
            item = self.library.item(index)
            path = Path(item.data(Qt.UserRole))
            visible = query in f'{item.text()} {path.name}'.casefold()
            item.setHidden(not visible)

    def _select(self, item, *_):
        self.selected_path = Path(item.data(Qt.UserRole)) if item else None
        self.assignment.blockSignals(True)
        self.assignment.setEnabled(item is not None)
        self.preview.setPixmap(load_pixmap(self.selected_path, 210))
        action = self.mapper.assigned_action(self.selected_path) if item else None
        self.action_name.setText(ACTION_LABELS.get(action, '미할당') if item else '이미지를 선택하세요')
        self.assignment.clear()
        self.assignment.addItem('할당하지 않음', None)
        if action:
            self.assignment.addItem(ACTION_LABELS[action], action)
            # Show the current assignment in the field, but offer only unused actions in the popup.
        for key, text, group in ACTIONS:
            if key not in self.mapper.mappings:
                self.assignment.addItem(f'{group} · {text}', key)
        for index in range(self.assignment.count()):
            self.assignment.view().setRowHidden(index, bool(action) and index == 1)
        self.assignment.setCurrentIndex(max(0, self.assignment.findData(action)))
        self.assignment.blockSignals(False)

    def _assign(self, *_):
        if self.selected_path:
            self.mapper.assign_image(self.selected_path, self.assignment.currentData())
            self.settings_changed.emit()
            self.refresh()
            self.notice.clear()

    def _enable(self, action, enabled):
        self.mapper.set_enabled(action, enabled)
        self.settings_changed.emit()

    def _select_actions(self, enabled):
        self.mapper.enabled = set(self.mapper.mappings) if enabled else set()
        self.mapper.preset_name = '사용자 설정'
        self.refresh()
        self.settings_changed.emit()

    def _change_behavior(self, *_):
        self.mapper.update_settings({key: widget.value() for key, widget in self._controls.items()})
        self.settings_changed.emit()

    def _refresh_presets(self):
        self.presets.clear()
        self.presets.addItems(self.mapper.preset_names())
        index = self.presets.findText(self.mapper.preset_name)
        if index >= 0:
            self.presets.setCurrentIndex(index)

    def _apply_preset(self):
        self.mapper.apply_preset(self.presets.currentText())
        self.refresh()
        self.settings_changed.emit()
        self.notice.setText(f'{self.mapper.preset_name} 적용 · 사용할 행동 탭에서 행동을 고를 수 있습니다.')

    def _save_preset(self):
        name, ok = QInputDialog.getText(self, '객체 프리셋 저장', '프리셋 이름')
        if ok:
            try:
                self.mapper.save_preset(name)
                self.mapper.save_config()
                self._refresh_presets()
                self.notice.setText(f'{name.strip()} 프리셋을 저장했습니다.')
            except (ValueError, OSError) as exc:
                QMessageBox.warning(self, '저장 실패', str(exc))

    def _import(self):
        paths, _ = QFileDialog.getOpenFileNames(self, '이미지 추가', '', '이미지 (*.png *.jpg *.jpeg *.gif *.webp)')
        for path in paths:
            try:
                self.mapper.import_image(path)
            except ValueError as exc:
                QMessageBox.warning(self, '추가 실패', str(exc))
        self.refresh()

    def _save(self):
        try:
            self.mapper.save_config()
            self.notice.setText('설정을 저장했습니다.')
        except OSError as exc:
            QMessageBox.warning(self, '저장 실패', str(exc))

    def _pause(self, paused):
        self.pause.setText('감지 다시 시작' if paused else '감지 일시정지')
        self.pause_changed.emit(paused)
        self.live.setText('감지 일시정지' if paused else '감지 중')

    def on_trigger(self, trigger, path):
        self.live.setText(f'감지 중 · {ACTION_LABELS.get(trigger, trigger)}')

    def show_camera_error(self, message):
        self.live.setText(f'카메라 연결 확인 · {message}')

    def show(self):
        super().show()
        self.raise_()
        self.activateWindow()
