from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt
from ui.theme import (
    MENU_WIDTH, STYLE_BUTTON_TRANSPARENT,
    STYLE_TAB_BUTTON_ACTIVE, STYLE_TAB_BUTTON_INACTIVE,
    STYLE_BUTTON, STYLE_RENAME_INPUT, STYLE_TRANSPARENT_BG,
    STYLE_SEPARATOR_BORDER, STYLE_PROFILE_HEADER,
    STYLE_STATUS_DOT_OFFLINE, STYLE_LABEL_PLACEHOLDER,
    style_status_dot
)
from ui.tabs.basic_tab import BasicTab
from ui.tabs.jvm_tab import JvmTab
from ui.settings_view import SettingsView
from core.lang import lang
from ui.views.add_profile_view import AddProfileView

from ui.overlays.delete_profile_overlay import DeleteProfileOverlay
from core.profile_manager import rename_profile
from ui.tabs.properties_tab import PropertiesTab


class _DeleteButton(QPushButton):
    """Delete button that turns red on hover."""
    def __init__(self, parent=None):
        super().__init__("", parent)  # This button is icon-only
        self._server_running = False
        self._hovered = False
        from PyQt6.QtWidgets import QSizePolicy
        sp = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(sp)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def resizeEvent(self, event):
        self.setFixedWidth(self.height())
        super().resizeEvent(event)

    def set_server_running(self, running: bool):
        self._server_running = running
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if self._server_running:
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QFont
        from PyQt6.QtCore import QRect
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        if self._server_running:
            # Disabled while the server is running.
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QColor(204, 204, 204, 55))
        elif self._hovered:
            # Red background and white text
            p.setBrush(QColor(229, 57, 53, 255))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, w, h, 4, 4)
            p.setPen(QColor(255, 255, 255, 255))
        else:
            # Transparent background and dim text
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QColor(204, 204, 204, 80))

        font = QFont()
        font.setPixelSize(max(10, int(h * 0.45)))
        font.setBold(True)
        p.setFont(font)
        text_rect = QRect(0, -int(h * 0.05), w, h)  # Shift 5% upward
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "×")


class _RenameLabel(QWidget):
    """Label that can be renamed by clicking."""
    def __init__(self, text: str, rename_callback=None, parent=None):
        super().__init__(parent)
        self._text = text
        self._rename_callback = rename_callback
        self._server_running = False
        self._editing = False
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label = QLabel(self._text)
        self._label.setStyleSheet(f"font-size: 12px; {STYLE_TRANSPARENT_BG}")
        self._label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._input = QLineEdit(self._text)
        self._input.setStyleSheet(STYLE_RENAME_INPUT)
        self._input.hide()
        self._input.editingFinished.connect(self._on_confirm)
        self._input.installEventFilter(self)

        layout.addWidget(self._label)
        layout.addWidget(self._input)

    def set_text(self, text: str):
        self._text = text
        self._label.setText(text)
        self._input.setText(text)

    def set_server_running(self, running: bool):
        self._server_running = running
        cursor = (
            Qt.CursorShape.ArrowCursor
            if running else
            Qt.CursorShape.PointingHandCursor
        )
        self._label.setCursor(cursor)
        self.setCursor(cursor)
        if running and self._editing:
            self._cancel_edit()

    def mousePressEvent(self, event):
        if self._server_running or self._editing:
            return
        self._start_edit()

    def _start_edit(self):
        self._editing = True
        self._label.hide()
        self._input.setText(self._text)
        self._input.show()
        self._input.selectAll()
        self._input.setFocus()

    def _cancel_edit(self):
        self._editing = False
        self._input.hide()
        self._label.show()

    def _on_confirm(self):
        new_name = self._input.text().strip()
        self._editing = False
        self._input.hide()
        self._label.show()
        if new_name and new_name != self._text:
            if self._rename_callback:
                self._rename_callback(new_name)
        
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self._input and event.type() == QEvent.Type.KeyPress:
            from PyQt6.QtCore import Qt as QtCore
            if event.key() == QtCore.Key.Key_Escape:
                self._cancel_edit()
                return True
        return super().eventFilter(obj, event)


class LeftPanel(QWidget):
    def __init__(self, parent=None, toggle_menu_callback=None, on_profile_created=None):
        super().__init__(parent)
        self._toggle_menu       = toggle_menu_callback
        self._on_profile_created = on_profile_created

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.main_view = self._build_main_view()
        self.stack.addWidget(self.main_view)

        self.settings_view = SettingsView(back_callback=self._show_main)
        self.stack.addWidget(self.settings_view)

        self.add_profile_view = AddProfileView(
            back_callback=self._show_main,
            confirm_callback=self._on_add_profile_confirm
        )
        self.stack.addWidget(self.add_profile_view)

        self.stack.setCurrentWidget(self.main_view)

    def _build_main_view(self) -> QWidget:
        view = QWidget()
        root = QVBoxLayout(view)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(6)

        btn_size = MENU_WIDTH // 3 - 8

        # Menu button on the left
        self.hamburger_btn = QPushButton("☰")
        self.hamburger_btn.setFixedSize(btn_size, btn_size)
        self.hamburger_btn.setStyleSheet(STYLE_BUTTON_TRANSPARENT)
        if self._toggle_menu:
            self.hamburger_btn.clicked.connect(self._toggle_menu)
        top_bar.addWidget(self.hamburger_btn)

        # Right side: two rows for profile info and tabs
        right_widget = QWidget()
        right_widget.setFixedHeight(btn_size)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)

        # Top row: profile indicator
        self._profile_widget = QWidget()
        self._profile_widget.setStyleSheet(STYLE_PROFILE_HEADER)
        profile_layout = QHBoxLayout(self._profile_widget)
        profile_layout.setContentsMargins(8, 0, 0, 0)
        profile_layout.setSpacing(4)

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(STYLE_STATUS_DOT_OFFLINE)

        self._profile_name_label = _RenameLabel(
            lang.get("ui.profile.untitled"),
            rename_callback=self._on_rename_profile
        )

        self._delete_btn = _DeleteButton()
        self._delete_btn.clicked.connect(self._on_delete_profile)

        profile_layout.addWidget(self._status_dot)
        profile_layout.addWidget(self._profile_name_label, stretch=1)
        profile_layout.addWidget(self._delete_btn)

        right_layout.addWidget(self._profile_widget, stretch=1)  # Top row

        # Widget that contains tab buttons for gray-out control
        self._tab_bar_widget = QWidget()
        tab_bar_layout = QHBoxLayout(self._tab_bar_widget)
        tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        tab_bar_layout.setSpacing(2)

        

        from PyQt6.QtWidgets import QSizePolicy
        labels  = [
            lang.get("ui.left.tab.basic"),
            lang.get("ui.left.tab.jvm"),
            lang.get("ui.left.tab.properties"),
            "---",
        ]
        indices = [0, 1, 2, None]
        self._tab_btns = []

        for label, idx in zip(labels, indices):
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            if idx is not None:
                btn.clicked.connect(lambda _, n=idx: self._switch_tab(n))
            else:
                btn.setEnabled(False)
            tab_bar_layout.addWidget(btn)
            self._tab_btns.append((btn, idx))

        right_layout.addWidget(self._tab_bar_widget, stretch=1)
        top_bar.addWidget(right_widget, stretch=1)
        root.addLayout(top_bar)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLE_SEPARATOR_BORDER)
        root.addWidget(line)

        # Content area for tabs or placeholder
        self._content_stack = QStackedWidget()

        # Tab content
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_stack = QStackedWidget()
        self.basic_tab = BasicTab()
        self.jvm_tab = JvmTab()
        self.properties_tab = PropertiesTab()
        self.tab_stack.addWidget(self.basic_tab)      # index 0
        self.tab_stack.addWidget(self.jvm_tab)         # index 1
        self.tab_stack.addWidget(self.properties_tab)  # index 2
        tab_layout.addWidget(self.tab_stack)
        self._content_stack.addWidget(tab_container)   # index 0: tabs

        

        # Placeholder shown when there is no profile
        placeholder = self._build_placeholder()
        self._content_stack.addWidget(placeholder)     # index 1: placeholder

        root.addWidget(self._content_stack, stretch=1)

        self._switch_tab(0)
        return view

    def _build_placeholder(self) -> QWidget:
        """Build the widget shown when no profile exists."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("📂")
        icon.setStyleSheet(f"font-size: 48px; {STYLE_TRANSPARENT_BG}")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(lang.get("ui.left.no_profile.message"))
        msg.setStyleSheet(STYLE_LABEL_PLACEHOLDER)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        add_btn = QPushButton(lang.get("ui.menu.profile.add"))
        add_btn.setStyleSheet(STYLE_BUTTON)
        add_btn.setFixedWidth(180)
        add_btn.clicked.connect(self._on_add_profile_from_placeholder)
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return widget

    def _on_add_profile_from_placeholder(self):
        self._notify_app("add_profile")
    
    def _switch_tab(self, index: int):
        self.tab_stack.setCurrentIndex(index)
        for btn, idx in self._tab_btns:
            if idx == index:
                btn.setStyleSheet(STYLE_TAB_BUTTON_ACTIVE)
            elif idx is not None:
                btn.setStyleSheet(STYLE_TAB_BUTTON_INACTIVE)

    def show_settings(self):
        self.stack.setCurrentWidget(self.settings_view)

    def _show_main(self):
        self.stack.setCurrentWidget(self.main_view)

    def apply_profile(self, profile: dict):
        name    = profile.get("name", "")
        running = profile.get("_running", False)

        if hasattr(self, "_profile_name_label"):
            self._profile_name_label.set_text(
                name if name else lang.get("ui.profile.untitled")
            )
        if hasattr(self, "_status_dot"):
            self._status_dot.setStyleSheet(style_status_dot(running))

        self.set_server_running(running)
        self.basic_tab.set_values(profile)
        self.jvm_tab.set_values(profile)
        self.properties_tab.set_values(profile)
        self._switch_tab(self.tab_stack.currentIndex())
    
    def show_add_profile(self):
        self.add_profile_view.reset()
        self.stack.setCurrentWidget(self.add_profile_view)

    def _on_add_profile_confirm(self, data: dict):
        """Delegate the action to AppWindow."""
        if self._on_profile_created:
            created = self._on_profile_created(data)
            if created is False:
                return
        self._show_main()
        self._switch_tab(0)

    def _on_delete_profile(self):
        """Handle delete button clicks."""
        name = self._current_profile_name()
        if not name:
            return
        self._show_delete_overlay(name)

    def _on_rename_profile(self, new_name: str):
        """Handle confirmed profile renames."""
        old_name = self._current_profile_name()
        if not old_name:
            return
        if rename_profile(old_name, new_name):
            self._profile_name_label.set_text(new_name)
            # Notify AppWindow
            self._notify_app("profile_renamed", old_name=old_name, new_name=new_name)

    def _current_profile_name(self) -> str:
        label = self._profile_name_label._text
        return label if label != lang.get("ui.profile.untitled") else ""

    def _show_delete_overlay(self, name: str):
        # Show the overlay above AppWindow's central widget
        central = self._get_central()
        if not central:
            return
        self._delete_overlay = DeleteProfileOverlay(
            central,
            profile_name=name,
            confirm_callback=lambda delete_dir: self._on_delete_confirmed(name, delete_dir),
            cancel_callback=self._close_delete_overlay
        )
        self._delete_overlay.setGeometry(central.rect())
        self._delete_overlay.show()
        self._delete_overlay.raise_()

    def _close_delete_overlay(self):
        if hasattr(self, "_delete_overlay") and self._delete_overlay:
            self._delete_overlay.hide()
            self._delete_overlay = None

    def _on_delete_confirmed(self, name: str, delete_dir: bool):
        self._close_delete_overlay()
        # Delegate to AppWindow
        self._notify_app("profile_deleted", name=name, delete_dir=delete_dir)

    def _get_central(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "centralWidget"):
                return parent.centralWidget()
            parent = parent.parent() if hasattr(parent, "parent") else None
        return None

    def _notify_app(self, event: str, **kwargs):
        parent = self.parent()
        while parent:
            if hasattr(parent, "on_left_panel_event"):
                parent.on_left_panel_event(event, **kwargs)
                return
            parent = parent.parent() if hasattr(parent, "parent") else None

    def set_server_running(self, running: bool):
        """Reflect server running state in the indicator."""
        if hasattr(self, "_delete_btn"):
            self._delete_btn.set_server_running(running)
        if hasattr(self, "_profile_name_label"):
            self._profile_name_label.set_server_running(running)
        
    def set_has_profile(self, has_profile: bool):
        """Switch the UI based on whether a profile exists."""
        if not hasattr(self, "_content_stack"):
            return

        if has_profile:
            self._content_stack.setCurrentIndex(0)  # Show tabs
            # Enable tab buttons
            for btn, idx in self._tab_btns:
                if idx is not None:
                    btn.setEnabled(True)
            self._switch_tab(self.tab_stack.currentIndex())
        else:
            self._profile_name_label.set_text(lang.get("ui.profile.untitled"))
            self._status_dot.setStyleSheet(STYLE_STATUS_DOT_OFFLINE)
            self.set_server_running(False)
            self._content_stack.setCurrentIndex(1)  # Show placeholder
            # Gray out tab buttons
            for btn, idx in self._tab_btns:
                btn.setEnabled(False)
                btn.setStyleSheet(STYLE_TAB_BUTTON_INACTIVE)
