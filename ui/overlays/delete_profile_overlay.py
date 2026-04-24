from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox,
    QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from ui.theme import (
    STYLE_BUTTON_TRANSPARENT,
    STYLE_INPUT, STYLE_CHECKBOX_DANGER,
    STYLE_DIALOG_CARD, style_delete_confirm_button,
    STYLE_SEPARATOR_BORDER, STYLE_LABEL_SECONDARY_SMALL,
    COLOR_TEXT_PRIMARY, COLOR_DANGER_BRIGHT,
    FONT_SIZE_LARGE
)
from core.lang import lang


class DeleteProfileOverlay(QWidget):
    """Overlay that confirms profile deletion."""

    def __init__(self, parent, profile_name: str,
                 confirm_callback, cancel_callback):
        super().__init__(parent)
        self._profile_name    = profile_name
        self._confirm_callback = confirm_callback
        self._cancel_callback  = cancel_callback
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._build()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 160))

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Dialog card
        card = QWidget()
        card.setFixedWidth(360)
        card.setStyleSheet(STYLE_DIALOG_CARD)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # Title
        title = QLabel(lang.get("ui.delete_profile.title"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold;"
            f"color: {COLOR_DANGER_BRIGHT};"
        )
        card_layout.addWidget(title)

        # Description
        desc = QLabel(
            lang.get("ui.delete_profile.desc").format(self._profile_name)
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        card_layout.addWidget(desc)

        # Red checkbox for deleting the directory
        self.delete_dir_checkbox = QCheckBox(lang.get("ui.delete_profile.delete_dir"))
        self.delete_dir_checkbox.setChecked(False)
        self.delete_dir_checkbox.setStyleSheet(STYLE_CHECKBOX_DANGER)
        card_layout.addWidget(self.delete_dir_checkbox)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(STYLE_SEPARATOR_BORDER)
        card_layout.addWidget(sep)

        # Profile name input
        confirm_label = QLabel(
            lang.get("ui.delete_profile.type_name").format(self._profile_name)
        )
        confirm_label.setWordWrap(True)
        confirm_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL
        )
        card_layout.addWidget(confirm_label)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(STYLE_INPUT)
        self.name_input.setPlaceholderText(self._profile_name)
        self.name_input.textChanged.connect(self._on_text_changed)
        card_layout.addWidget(self.name_input)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton(lang.get("ui.dialog.cancel"))
        cancel_btn.setStyleSheet(STYLE_BUTTON_TRANSPARENT)
        cancel_btn.clicked.connect(self._cancel_callback)
        btn_row.addWidget(cancel_btn)

        self.delete_btn = QPushButton(lang.get("ui.delete_profile.delete"))
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(self._delete_btn_style(enabled=False))
        self.delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self.delete_btn)

        card_layout.addLayout(btn_row)
        outer.addWidget(card)

    def _delete_btn_style(self, enabled: bool) -> str:
        return style_delete_confirm_button(enabled)

    def _on_text_changed(self, text: str):
        match = text == self._profile_name
        self.delete_btn.setEnabled(match)
        self.delete_btn.setStyleSheet(self._delete_btn_style(enabled=match))

    def _on_delete(self):
        delete_dir = self.delete_dir_checkbox.isChecked()
        self._confirm_callback(delete_dir)
