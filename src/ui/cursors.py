from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QAbstractButton, QApplication, QComboBox, QWidget


class ClickableCursorFilter(QObject):
    """Keep clickable controls using the pointing-hand cursor."""

    CLICKABLE_TYPES = (QAbstractButton, QComboBox)

    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget):
            event_type = event.type()
            if event_type in (
                QEvent.Type.Polish,
                QEvent.Type.Show,
                QEvent.Type.EnabledChange,
                QEvent.Type.ChildAdded,
            ):
                self._apply(obj)
        return super().eventFilter(obj, event)

    def _apply(self, widget: QWidget):
        if isinstance(widget, self.CLICKABLE_TYPES):
            if widget.isEnabled():
                widget.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                widget.unsetCursor()

        for child in widget.findChildren(QWidget):
            if isinstance(child, self.CLICKABLE_TYPES):
                if child.isEnabled():
                    child.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    child.unsetCursor()


def install_clickable_cursor_filter(app: QApplication):
    cursor_filter = ClickableCursorFilter(app)
    app.installEventFilter(cursor_filter)
    app._clickable_cursor_filter = cursor_filter
