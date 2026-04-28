from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QGraphicsBlurEffect
from ui.theme import (
    STYLE_BUTTON, STYLE_BUTTON_TRANSPARENT, STYLE_DIALOG_CARD,
    STYLE_SEPARATOR_BORDER, STYLE_LABEL_SECONDARY_SMALL,
    COLOR_TEXT_PRIMARY, COLOR_WARNING, FONT_SIZE_LARGE
)
from core.lang import lang


class PortConflictOverlay(QWidget):
    """Overlay that warns about a server-port conflict before starting."""

    def __init__(
        self,
        parent,
        blur_target,
        port: int,
        conflicting_profiles: list[str],
        confirm_callback,
        cancel_callback
    ):
        super().__init__(parent)
        self._blur_target = blur_target
        self._blur_effect = None
        self._port = port
        self._conflicting_profiles = conflicting_profiles
        self._confirm_callback = confirm_callback
        self._cancel_callback = cancel_callback
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._apply_blur()
        self._build()

    def close_overlay(self):
        self._clear_blur()
        self.hide()
        self.deleteLater()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 150))

    def _apply_blur(self):
        if self._blur_target is None:
            return
        self._blur_effect = QGraphicsBlurEffect(self._blur_target)
        self._blur_effect.setBlurRadius(10)
        self._blur_target.setGraphicsEffect(self._blur_effect)

    def _clear_blur(self):
        if self._blur_target is not None:
            self._blur_target.setGraphicsEffect(None)
        self._blur_effect = None

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setFixedWidth(420)
        card.setStyleSheet(STYLE_DIALOG_CARD)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        title = QLabel(lang.get("ui.start.port_conflict.title"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold;"
            f"color: {COLOR_WARNING};"
        )
        card_layout.addWidget(title)

        conflicts = ", ".join(self._conflicting_profiles)
        desc = QLabel(
            lang.get("ui.start.port_conflict.desc").format(self._port, conflicts)
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        card_layout.addWidget(desc)

        hint = QLabel(lang.get("ui.start.port_conflict.hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(STYLE_LABEL_SECONDARY_SMALL)
        card_layout.addWidget(hint)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(STYLE_SEPARATOR_BORDER)
        card_layout.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton(lang.get("ui.dialog.cancel"))
        cancel_btn.setStyleSheet(STYLE_BUTTON_TRANSPARENT)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)

        start_btn = QPushButton(lang.get("ui.start.port_conflict.start_anyway"))
        start_btn.setStyleSheet(STYLE_BUTTON)
        start_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(start_btn)

        card_layout.addLayout(btn_row)
        outer.addWidget(card)

    def _on_cancel(self):
        self._cancel_callback()

    def _on_confirm(self):
        self._confirm_callback()
