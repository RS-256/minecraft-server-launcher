import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont
from core.lang import lang
from ui.theme import (
    STYLE_SCROLL_AREA_TRANSPARENT, STYLE_TRANSPARENT_BG,
    COLOR_TEXT_BRIGHT, COLOR_TEXT_MUTED, COLOR_ACCENT_HOVER
)


class ProfileIcon(QWidget):
    def __init__(self, brand: str, running: bool, parent=None):
        super().__init__(parent)
        self.brand = brand
        self.running = running
        self.setFixedSize(40, 40)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        brand_colors = {
            "vanilla":  QColor(106, 153,  85, 255),
            "fabric":   QColor( 63, 135, 189, 255),
            "neoforge": QColor(204, 119,  34, 255),
            "spigot":   QColor(230,  81,   0, 255),
            "paper":    QColor(244,  67,  54, 255),
        }
        bg = brand_colors.get(self.brand.lower(), QColor(90, 90, 90, 255))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(2, 2, 36, 36, 6, 6)

        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 220))
        p.drawText(2, 2, 36, 36, Qt.AlignmentFlag.AlignCenter, self.brand[0].upper())

        dot_color = QColor(76, 175, 80, 255) if self.running else QColor(80, 80, 80, 255)
        p.setPen(QColor(37, 37, 37, 255))
        p.setBrush(dot_color)
        p.drawEllipse(26, 26, 12, 12)


class ScrollingLabel(QWidget):
    """Scroll overflowing text at a constant speed on hover, then loop."""
    def __init__(self, text: str, style: str = "", label_height: int = 20, parent=None):
        super().__init__(parent)
        self._text = text
        self._scrolling = False

        # Scroll animation
        self._anim = QPropertyAnimation()
        self._anim.finished.connect(self._on_anim_finished)

        # Start delay timer
        self._start_timer = QTimer(self)
        self._start_timer.setSingleShot(True)
        self._start_timer.timeout.connect(self._start_scroll)

        # Pause after reaching the right edge
        self._pause_timer = QTimer(self)
        self._pause_timer.setSingleShot(True)
        self._pause_timer.timeout.connect(self._restart_scroll)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(STYLE_SCROLL_AREA_TRANSPARENT)
        self._scroll.setFrameShape(self._scroll.Shape.NoFrame)

        self._label = QLabel(text)
        self._label.setStyleSheet(style + " " + STYLE_TRANSPARENT_BG)
        self._label.setFixedHeight(label_height)
        self._label.adjustSize()
        self._scroll.setWidget(self._label)

        layout.addWidget(self._scroll)
        self.setMouseTracking(True)

    def _needs_scroll(self) -> bool:
        return self._label.sizeHint().width() > self._scroll.width()

    def enterEvent(self, event):
        if self._needs_scroll():
            self._start_timer.start(800)

    def leaveEvent(self, event):
        self._stop_all()

    def _stop_all(self):
        self._start_timer.stop()
        self._pause_timer.stop()
        if self._anim:
            self._anim.stop()
        self._scrolling = False
        self._scroll.horizontalScrollBar().setValue(0)

    def _start_scroll(self):
        if not self._needs_scroll():
            return
        self._scrolling = True
        self._do_scroll_forward()

    def _do_scroll_forward(self):
        bar = self._scroll.horizontalScrollBar()
        travel = self._label.sizeHint().width() - self._scroll.width()
        if travel <= 0:
            return

        # Constant speed: 30 px/s
        duration = int(travel / 30 * 1000)

        self._anim = QPropertyAnimation(bar, b"value")
        self._anim.setDuration(duration)
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._anim.setStartValue(0)
        self._anim.setEndValue(travel)
        self._anim.finished.connect(self._on_anim_finished)
        self._anim.start()

    def _on_anim_finished(self):
        if not self._scrolling:
            return
        # After reaching the right edge, wait 800 ms before resetting
        self._pause_timer.start(800)

    def _restart_scroll(self):
        if not self._scrolling:
            return
        self._scroll.horizontalScrollBar().setValue(0)
        # Wait briefly before scrolling again
        QTimer.singleShot(300, self._do_scroll_forward)


class ProfileListItem(QWidget):
    clicked = pyqtSignal(str)

    def __init__(
        self,
        profile: dict,
        running: bool = False,
        selected: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self._profile = profile
        self._running = running
        self._selected = selected
        self._hovered = False
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(64)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Icon
        brand = self._profile.get("brand", "vanilla")
        icon = ProfileIcon(brand, self._running)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Text area
        text_widget = QWidget()
        text_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        # Top row: scrollable profile name
        name_label = ScrollingLabel(
            self._profile.get("name", ""),
            f"font-size: 13px; font-weight: bold; color: {COLOR_TEXT_BRIGHT};"
        )
        name_label.setFixedHeight(20)
        text_layout.addWidget(name_label)

        # Bottom row: dir plus brand/version side by side
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        bottom_widget.setFixedHeight(16)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(6)

        server_dir = self._profile.get("server_dir", "")
        dir_text = os.path.basename(server_dir) if server_dir \
              else lang.get("ui.menu.profile.no_dir")
        dir_label = ScrollingLabel(
            f"{lang.get('ui.menu.profile.dir')} {dir_text}",
            f"font-size: 11px; color: {COLOR_TEXT_MUTED};",
            label_height=16
        )
        dir_label.setFixedHeight(16)

        brand_ver = f"{self._profile.get('brand', 'vanilla')} {self._profile.get('version', '')}"
        brand_label = QLabel(brand_ver)
        brand_label.setFixedHeight(16)
        brand_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_label.setStyleSheet(
            f"font-size: 11px; color: {COLOR_TEXT_MUTED}; {STYLE_TRANSPARENT_BG}"
        )
        brand_label.setWhiteSpace = None
        brand_label.setSizePolicy(
            brand_label.sizePolicy().horizontalPolicy(),
            brand_label.sizePolicy().verticalPolicy()
        )
        from PyQt6.QtWidgets import QSizePolicy
        brand_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        brand_label.adjustSize()

        bottom_layout.addWidget(dir_label, stretch=1)
        bottom_layout.addWidget(brand_label)
        text_layout.addWidget(bottom_widget)

        layout.addWidget(text_widget, stretch=1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._selected:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(31, 106, 165, 56))
            p.drawRoundedRect(self.rect().adjusted(4, 8, -4, -8), 6, 6)
            p.setBrush(QColor(31, 106, 165, 255))
            p.drawRoundedRect(3, 16, 2, self.height() - 32, 1, 1)
        if self._hovered:
            p.fillRect(self.rect(), QColor(255, 255, 255, 15))

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._profile.get("name", ""))


class AddProfileItem(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hovered = False
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        label = QLabel(lang.get("ui.menu.profile.add"))
        label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLOR_ACCENT_HOVER};
            background: transparent;
        """)
        layout.addWidget(label)
        layout.addStretch()

    def paintEvent(self, event):
        p = QPainter(self)
        if self._hovered:
            p.fillRect(self.rect(), QColor(255, 255, 255, 15))

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
