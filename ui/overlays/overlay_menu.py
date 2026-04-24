from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, Qt
from PyQt6.QtGui import QPainter, QColor
from ui.theme import (
    MENU_WIDTH, COLOR_OVERLAY_MENU_BG,
    STYLE_OVERLAY_MENU, STYLE_BUTTON_TRANSPARENT,
    STYLE_SCROLL_AREA_THIN, STYLE_TRANSPARENT_BG,
    STYLE_SEPARATOR_FAINT, STYLE_LABEL_MUTED_SMALL
)
from ui.widgets.profile_list_item import ProfileListItem, AddProfileItem
from core.lang import lang
from core.profile_manager import get_all_profiles


class OverlayMenu(QWidget):
    def __init__(self, parent, close_callback, open_settings_callback,
                 select_profile_callback, add_profile_callback):
        super().__init__(parent)
        self._close_callback          = close_callback
        self._open_settings_callback  = open_settings_callback
        self._select_profile_callback = select_profile_callback
        self._add_profile_callback    = add_profile_callback
        self._anim = None
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._build()
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(COLOR_OVERLAY_MENU_BG))

    def _build(self):
        self.setStyleSheet(STYLE_OVERLAY_MENU)

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # Top bar
        top_widget = QWidget()
        top_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(8, 10, 8, 10)
        top_layout.setSpacing(0)

        btn_size = MENU_WIDTH // 3 - 8

        def make_btn(label, callback=None):
            btn = QPushButton(label)
            btn.setFixedSize(btn_size, btn_size)
            btn.setStyleSheet(STYLE_BUTTON_TRANSPARENT)
            if callback:
                btn.clicked.connect(callback)
            return btn

        top_layout.addStretch()
        top_layout.addWidget(make_btn("☰", self._close_callback))
        top_layout.addStretch()
        top_layout.addWidget(make_btn("●"))
        top_layout.addStretch()
        top_layout.addWidget(make_btn("⚙️", self._on_settings))
        top_layout.addStretch()
        self._root_layout.addWidget(top_widget)
        self._root_layout.addWidget(self._make_separator())

        # Profile label
        profiles_label = QLabel(lang.get("ui.menu.profiles"))
        profiles_label.setStyleSheet(
            STYLE_LABEL_MUTED_SMALL + " padding: 8px 12px 4px 12px; background: transparent;"
        )
        self._root_layout.addWidget(profiles_label)

        # Scroll area for the list body
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(STYLE_SCROLL_AREA_THIN)
        self._root_layout.addWidget(self._scroll, stretch=1)
        self._refresh_list()

    def _refresh_list(self):
        """Rebuild the profile list."""
        list_widget = QWidget()
        list_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        profiles = get_all_profiles()
        for profile in profiles:
            list_layout.addWidget(self._make_separator())
            item = ProfileListItem(
                profile=profile,
                running=profile.get("_running", False)
            )
            item.clicked.connect(self._on_profile_clicked)
            list_layout.addWidget(item)

        list_layout.addWidget(self._make_separator())

        add_item = AddProfileItem()
        add_item.clicked.connect(self._on_add_profile)
        list_layout.addWidget(add_item)

        list_layout.addWidget(self._make_separator())
        list_layout.addStretch()

        self._scroll.setWidget(list_widget)

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLE_SEPARATOR_FAINT)
        line.setFixedHeight(1)
        return line

    def _on_profile_clicked(self, name: str):
        self._select_profile_callback(name)
        self._close_callback()

    def _on_add_profile(self):
        self._add_profile_callback()

    def _on_settings(self):
        self._close_callback()
        self._open_settings_callback()

    def refresh(self):
        """Refresh the list from outside this widget."""
        self._refresh_list()

    def slide_in(self, x: int, y: int, width: int, height: int):
        self.setGeometry(QRect(-width, y, width, height))
        self.show()
        self.raise_()
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(QRect(-width, y, width, height))
        anim.setEndValue(QRect(x, y, width, height))
        self._anim = anim
        anim.start()

    def slide_out(self, x: int, y: int, width: int, height: int, callback):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.setStartValue(QRect(x, y, width, height))
        anim.setEndValue(QRect(-width, y, width, height))
        anim.finished.connect(lambda: (self.hide(), callback()))
        self._anim = anim
        anim.start()
