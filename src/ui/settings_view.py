from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import Qt
from ui.theme import (
    STYLE_BUTTON, STYLE_COMBO, COLOR_TEXT_MUTED,
    FONT_SIZE_LARGE, FONT_SIZE_SMALL
)
from core.lang import lang
from core.config_manager import load_config, save_config

LANGUAGES = {
    "en_us": "English",
    "ja_jp": "日本語",
}


class SettingsView(QWidget):
    def __init__(self, parent=None, back_callback=None):
        super().__init__(parent)
        self._back_callback = back_callback
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        back_btn = QPushButton(lang.get("ui.settings.back"))
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(STYLE_BUTTON)
        back_btn.clicked.connect(self._on_back)
        layout.addWidget(back_btn)

        title = QLabel(lang.get("ui.settings.title"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold;"
        )
        layout.addWidget(title)

        layout.addWidget(QLabel(lang.get("ui.settings.language")))

        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet(STYLE_COMBO)
        config = load_config()
        for i, (code, display) in enumerate(LANGUAGES.items()):
            self.lang_combo.addItem(display, code)
            if code == config.get("language", "en_us"):
                self.lang_combo.setCurrentIndex(i)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        layout.addWidget(self.lang_combo)

        self.restart_label = QLabel("")
        self.restart_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(self.restart_label)

        layout.addStretch()

    def _on_lang_changed(self):
        code = self.lang_combo.currentData()
        config = load_config()
        config["language"] = code
        save_config(config)
        self.restart_label.setText(lang.get("ui.settings.restart_required"))

    def _on_back(self):
        if self._back_callback:
            self._back_callback()