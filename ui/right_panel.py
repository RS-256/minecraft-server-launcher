from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QLineEdit, QFrame, QLabel, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont
from ui.theme import (
    STYLE_LOG_TAB_ACTIVE, STYLE_LOG_TAB_INACTIVE,
    STYLE_ICON_BUTTON, STYLE_COMMAND_INPUT, STYLE_LOGBOX,
    STYLE_BUTTON_DARK, STYLE_COMMAND_FRAME, STYLE_SEPARATOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_DANGER_BRIGHT,
    COLOR_WARNING
)
from core.lang import lang


class LogDisplay(QTextEdit):
    """透かしロゴ付きログ表示エリア"""
    def __init__(self, watermark_text: str = "MC Server Launcher", parent=None):
        super().__init__(parent)
        self._watermark = watermark_text
        self.setReadOnly(True)
        self.setStyleSheet(STYLE_LOGBOX)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 18))
        p.drawText(
            self.viewport().rect(),
            Qt.AlignmentFlag.AlignCenter,
            self._watermark
        )

    def append_log(self, line: str):
        """ログ行を色分けして追加する"""
        line_lower = line.lower()
        if any(k in line_lower for k in ["error", "exception", "fatal", "severe"]):
            color = COLOR_DANGER_BRIGHT
        elif any(k in line_lower for k in ["warn", "warning"]):
            color = COLOR_WARNING
        elif any(k in line_lower for k in ["info"]):
            color = COLOR_TEXT_PRIMARY
        else:
            color = COLOR_TEXT_SECONDARY

        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.append(f'<span style="color:{color}; font-family:monospace;">{escaped}</span>')


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 10, 10)
        layout.setSpacing(0)

        # ヘッダー
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(0)

        self.tab_log_btn   = QPushButton(lang.get("ui.right.tab.log"))
        self.tab_crash_btn = QPushButton(lang.get("ui.right.tab.crash"))
        self.tab_log_btn.clicked.connect(lambda: self._switch_tab(0))
        self.tab_crash_btn.clicked.connect(lambda: self._switch_tab(1))

        header.addWidget(self.tab_log_btn)
        header.addWidget(self.tab_crash_btn)
        header.addStretch()

        upload_btn = QPushButton("☁")
        upload_btn.setToolTip(lang.get("ui.right.upload"))
        upload_btn.setStyleSheet(STYLE_ICON_BUTTON)
        upload_btn.setFixedSize(32, 32)
        header.addWidget(upload_btn)
        layout.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLE_SEPARATOR_BORDER + " margin-bottom: 4px;")
        layout.addWidget(line)

        # ログ表示
        self.log_stack = QStackedWidget()

        self.log_display = LogDisplay(lang.get("ui.right.watermark"))
        self.crash_display = QTextEdit()
        self.crash_display.setReadOnly(True)
        self.crash_display.setStyleSheet(STYLE_LOGBOX)
        self.crash_display.setPlaceholderText("No crash report found.")

        self.log_stack.addWidget(self.log_display)
        self.log_stack.addWidget(self.crash_display)
        layout.addWidget(self.log_stack, stretch=1)

        # コマンド入力
        cmd_frame = QFrame()
        cmd_frame.setStyleSheet(STYLE_COMMAND_FRAME)
        cmd_layout = QHBoxLayout(cmd_frame)
        cmd_layout.setContentsMargins(0, 6, 0, 0)
        cmd_layout.setSpacing(6)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText(lang.get("ui.right.cmd.placeholder"))
        self.cmd_input.setStyleSheet(STYLE_COMMAND_INPUT)
        self.cmd_input.returnPressed.connect(self._on_send)

        send_btn = QPushButton(lang.get("ui.right.cmd.send"))
        send_btn.setFixedWidth(60)
        send_btn.setStyleSheet(STYLE_BUTTON_DARK)
        send_btn.clicked.connect(self._on_send)

        cmd_layout.addWidget(self.cmd_input, stretch=1)
        cmd_layout.addWidget(send_btn)
        layout.addWidget(cmd_frame)

        self._switch_tab(0)
        self._send_command_callback = None

    def set_send_command_callback(self, callback):
        self._send_command_callback = callback

    def _on_send(self):
        text = self.cmd_input.text().strip()
        if not text:
            return
        if self._send_command_callback:
            self._send_command_callback(text)
        self.log_display.append_log(f"> {text}")
        self.cmd_input.clear()

    def _switch_tab(self, index: int):
        self.log_stack.setCurrentIndex(index)
        self.tab_log_btn.setStyleSheet(
            STYLE_LOG_TAB_ACTIVE if index == 0 else STYLE_LOG_TAB_INACTIVE
        )
        self.tab_crash_btn.setStyleSheet(
            STYLE_LOG_TAB_ACTIVE if index == 1 else STYLE_LOG_TAB_INACTIVE
        )
