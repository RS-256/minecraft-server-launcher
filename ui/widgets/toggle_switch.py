from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    QRectF, pyqtProperty
)
from PyQt6.QtGui import QPainter, QColor


class ToggleSwitch(QCheckBox):
    """
    左右スライド式トグルスイッチ。
    OFF: rgba(80, 80, 80, 255)
    ON:  rgba(31, 106, 165, 255)  ← アクセントカラーに統一
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._handle_pos = 0.0
        self.setFixedSize(52, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"handle_pos")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.stateChanged.connect(self._on_state_changed)

    @pyqtProperty(float)
    def handle_pos(self) -> float:
        return self._handle_pos

    @handle_pos.setter
    def handle_pos(self, value: float):
        self._handle_pos = value
        self.update()

    def _on_state_changed(self, state: int):
        self._anim.stop()
        self._anim.setStartValue(self._handle_pos)
        self._anim.setEndValue(1.0 if self.isChecked() else 0.0)
        self._anim.start()

    def mousePressEvent(self, event):
        """クリック領域全体でトグル発生"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        r = h / 2

        if self.isEnabled():
            off_bg = QColor(80, 80, 80, 255)
            on_bg  = QColor(31, 106, 165, 255)  # アクセントカラー
        else:
            off_bg = QColor(55, 55, 55, 255)
            on_bg  = QColor(25, 70, 110, 255)

        t = self._handle_pos
        bg = QColor(
            int(off_bg.red()   + (on_bg.red()   - off_bg.red())   * t),
            int(off_bg.green() + (on_bg.green() - off_bg.green()) * t),
            int(off_bg.blue()  + (on_bg.blue()  - off_bg.blue())  * t),
            255
        )

        # トラック
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # ハンドル
        padding  = 3
        handle_r = r - padding
        travel   = w - h
        x = padding + travel * self._handle_pos
        y = padding

        handle_color = QColor(255, 255, 255, 255) if self.isEnabled() \
                  else QColor(160, 160, 160, 255)
        p.setBrush(handle_color)
        p.drawEllipse(QRectF(x, y, handle_r * 2, handle_r * 2))

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(52, 26)