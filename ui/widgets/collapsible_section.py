from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame
)
from ui.theme import STYLE_COLLAPSIBLE_HEADER, STYLE_TRANSPARENT_BG


class CollapsibleSection(QWidget):
    """折りたたみ可能なセクション"""
    def __init__(self, title: str, parent=None, expanded: bool = False):
        super().__init__(parent)
        self._expanded = expanded
        self._build(title)

    def _build(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダーボタン
        self._header = QPushButton()
        self._header.setStyleSheet(STYLE_COLLAPSIBLE_HEADER)
        self._update_header(title)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # コンテンツエリア
        self._content = QWidget()
        self._content.setStyleSheet(STYLE_TRANSPARENT_BG)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 4, 8, 8)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content)

        self._content.setVisible(self._expanded)

    def _update_header(self, title: str):
        arrow = "▼" if self._expanded else "▶"
        self._header.setText(f"  {arrow}  {title}")

    def _toggle(self):
        self._expanded = not self._expanded
        title = self._header.text().split("  ", 2)[-1]
        self._update_header(title)
        self._content.setVisible(self._expanded)

    def add_widget(self, widget: QWidget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)
    
    def set_expanded(self, expanded: bool):
        """外部から展開状態を設定する"""
        if self._expanded == expanded:
            return
        self._expanded = expanded
        title = self._header.text().split("  ", 2)[-1]
        self._update_header(title)
        self._content.setVisible(self._expanded)
