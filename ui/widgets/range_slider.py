import psutil
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


def get_max_ram_mb() -> int:
    """マシンの合計RAMをMB単位で512MB刻みに切り捨てて返す"""
    total = psutil.virtual_memory().total
    total_mb = total // (1024 * 1024)
    return (total_mb // 512) * 512


class RangeSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_val   = 512
        self.max_val   = get_max_ram_mb() / 2 + self.min_val
        self.step      = 512
        self.low       = 2048
        self.high      = 4096
        self._enabled  = True
        self._dragging = None
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setEnabled(self, enabled: bool):
        self._enabled = enabled
        self.update()

    def _val_to_x(self, val: int) -> int:
        w = self.width() - 40
        steps_total = (self.max_val - self.min_val) // self.step
        steps_val   = (val - self.min_val) // self.step
        return int(20 + steps_val / steps_total * w)

    def _x_to_val(self, x: float) -> int:
        w = self.width() - 40
        steps_total = (self.max_val - self.min_val) // self.step
        steps = round((x - 20) / w * steps_total)
        steps = max(0, min(steps_total, steps))
        return self.min_val + steps * self.step

    def _fmt(self, mb: int) -> str:
        if mb >= 1024 and mb % 1024 == 0:
            return f"{mb // 1024}GB"
        return f"{mb}MB"

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = self.height() // 2 + 8

        if self._enabled:
            track_color  = QColor(68,  68,  68,  255)
            accent_color = QColor(31,  106, 165, 255)
            handle_color = QColor(255, 255, 255, 255)
            text_color   = QColor(170, 170, 170, 255)
        else:
            track_color  = QColor(55,  55,  55,  255)
            accent_color = QColor(55,  55,  55,  255)
            handle_color = QColor(100, 100, 100, 255)
            text_color   = QColor(90,  90,  90,  255)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(20, y - 3, self.width() - 40, 6, 3, 3)

        x_low  = self._val_to_x(self.low)
        x_high = self._val_to_x(self.high)

        if x_low == x_high:
            p.setBrush(QBrush(accent_color))
            p.drawEllipse(QPoint(x_low, y), 4, 4)
        else:
            p.setBrush(QBrush(accent_color))
            p.drawRoundedRect(x_low, y - 3, x_high - x_low, 6, 3, 3)

        for x in [x_low, x_high]:
            p.setBrush(QBrush(handle_color))
            p.setPen(QPen(accent_color, 2))
            p.drawEllipse(QPoint(x, y), 9, 9)

        p.setPen(QPen(text_color))
        if self.low == self.high:
            p.drawText(x_low - 20, y - 18, self._fmt(self.low))
        else:
            p.drawText(x_low  - 20, y - 18, self._fmt(self.low))
            p.drawText(x_high - 20, y - 18, self._fmt(self.high))

    def mousePressEvent(self, event):
        if not self._enabled:
            return
        x = event.position().x()
        x_low  = self._val_to_x(self.low)
        x_high = self._val_to_x(self.high)
        if abs(x - x_high) <= abs(x - x_low):
            self._dragging = "high"
        else:
            self._dragging = "low"

    def mouseMoveEvent(self, event):
        if not self._enabled or not self._dragging:
            return
        val = self._x_to_val(event.position().x())
        if self._dragging == "low":
            self.low = max(self.min_val, min(val, self.high))
        else:
            self.high = min(self.max_val, max(val, self.low))
        self.update()

    def mouseReleaseEvent(self, event):
        self._dragging = None