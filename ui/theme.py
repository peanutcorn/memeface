"""Shared white, red and orange desktop theme."""
from PyQt5.QtGui import QColor, QPalette

LIGHT_THEME = '''
QWidget { background: #ffffff; color: #302624; font-family: "Malgun Gothic"; font-size: 13px; }
QWidget#memefaceOverlay, QLabel { background: transparent; }
QLabel#muted { color: #766763; }
QLabel#title { color: #c52d2d; font-size: 26px; font-weight: bold; }
QLabel#groupHeading { color: #b84c16; font-size: 16px; padding-top: 14px; font-weight: bold; }
QFrame#panel { background: #fff8f3; border: 1px solid #efdbd0; border-radius: 12px; }
QPushButton { background: #ffffff; border: 1px solid #e5c9bd; border-radius: 7px; padding: 9px 14px; }
QPushButton:hover { background: #fff0e5; border-color: #e47a3b; }
QPushButton:pressed { background: #ffe2cc; }
QPushButton:focus { border-color: #d83b32; }
QPushButton#primary { background: #d83b32; color: #ffffff; border: 1px solid #d83b32; font-weight: bold; }
QPushButton#primary:hover { background: #bc2d27; border-color: #bc2d27; }
QPushButton#primary:pressed { background: #a12521; }
QPushButton:checked { background: #fff0df; color: #a34413; border-color: #e47a3b; }
QPushButton:disabled { color: #a59a95; background: #f7f4f2; border-color: #e8e0dc; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #dfcfc8; border-radius: 7px; padding: 8px; selection-background-color: #d83b32; selection-color: #ffffff; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #e47a3b; }
QComboBox QAbstractItemView { background: #ffffff; color: #302624; border: 1px solid #e5c9bd; selection-background-color: #fff0e5; selection-color: #a82c26; }
QTabWidget::pane { border: none; }
QTabBar::tab { padding: 12px 20px; color: #766763; border-bottom: 2px solid transparent; }
QTabBar::tab:hover { color: #b84c16; background: #fff8f3; }
QTabBar::tab:selected { color: #c52d2d; border-bottom: 2px solid #d83b32; }
QListWidget { background: #ffffff; border: none; outline: none; }
QListWidget::item { background: #fffaf6; border: 1px solid #efdbd0; border-radius: 10px; margin: 5px; padding: 9px; }
QListWidget::item:hover { background: #fff0e5; border-color: #eaa275; }
QListWidget::item:selected { background: #fff0e9; color: #a82c26; border: 1px solid #d83b32; }
QScrollArea { border: none; }
QCheckBox { spacing: 10px; padding: 6px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QScrollBar:vertical { background: #faf5f1; width: 10px; }
QScrollBar::handle:vertical { background: #e7a17b; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #df7a41; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QMenu { background: #ffffff; color: #302624; border: 1px solid #efdbd0; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 4px; }
QMenu::item:selected { background: #fff0e5; color: #a82c26; }
QMenu::separator { height: 1px; background: #efdbd0; margin: 4px 8px; }
QToolTip { background: #fff8f3; color: #302624; border: 1px solid #e5c9bd; padding: 5px; }
'''


def apply_theme(app):
    app.setStyle('Fusion')
    palette = QPalette()
    for role, color in (
        (QPalette.Window, '#ffffff'), (QPalette.Base, '#ffffff'),
        (QPalette.AlternateBase, '#fff8f3'), (QPalette.Button, '#ffffff'),
        (QPalette.WindowText, '#302624'), (QPalette.Text, '#302624'),
        (QPalette.ButtonText, '#302624'), (QPalette.Highlight, '#d83b32'),
        (QPalette.HighlightedText, '#ffffff'), (QPalette.PlaceholderText, '#766763'),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(LIGHT_THEME)
