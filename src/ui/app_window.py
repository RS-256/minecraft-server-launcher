import os

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel
from ui.overlays.overlay_menu import OverlayMenu
from core.server_process import ServerProcess
from ui.theme import (
    STYLE_WINDOW, STYLE_LABEL, STYLE_INPUT, STYLE_BUTTON,
    STYLE_COMBO, STYLE_BOTTOM_BAR, MENU_WIDTH, FONT_SIZE_SMALL,
    COLOR_TEXT_MUTED
)
from core.lang import lang
from core.profile_manager import (
    get_all_profiles, get_last_used_profile,
    create_profile, set_last_used, load_profile
)

APP_VERSION = "0.1.0"


class BgDimOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 100))


class DimOverlay(QWidget):
    def __init__(self, parent, close_callback):
        super().__init__(parent)
        self._close_callback = close_callback
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 0))

    def mousePressEvent(self, event):
        self._close_callback()


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._menu_open      = False
        self._current_profile: dict | None = None
        self._server_process: ServerProcess | None = None
        self._setup_window()
        self._build()
        self._load_initial_profile()
        
    def _setup_window(self):
        self.setWindowTitle("MC Server Launcher")
        self.resize(1280, 720)
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(
            STYLE_WINDOW + STYLE_LABEL + STYLE_INPUT + STYLE_BUTTON + STYLE_COMBO
        )

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 5)
        content_layout.setSpacing(10)

        self.left_panel = LeftPanel(
            central,
            toggle_menu_callback=self._toggle_menu,
            on_profile_created=self._on_profile_created
        )
        self.right_panel = RightPanel(central)

        # Connect the log callback
        self.left_panel.basic_tab.set_log_callback(
            self.right_panel.log_display.append_log
        )

        # Connect start and stop callbacks
        self.left_panel.basic_tab.start_btn.clicked.connect(self._on_start_server)
        self.left_panel.basic_tab.stop_btn.clicked.connect(self._on_stop_server)

        # Connect the command send callback
        self.right_panel.set_send_command_callback(self._on_send_command)


        content_layout.addWidget(self.left_panel,  stretch=4)
        content_layout.addWidget(self.right_panel, stretch=6)

        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(28)
        bottom_bar.setStyleSheet(STYLE_BOTTOM_BAR)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 0, 12, 0)
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(
            f"font-size: {FONT_SIZE_SMALL}px; color: {COLOR_TEXT_MUTED};"
        )
        bottom_layout.addStretch()
        bottom_layout.addWidget(version_label)

        root.addWidget(content)
        root.addWidget(bottom_bar)

        self._bg_dim = BgDimOverlay(central)
        self._bg_dim.hide()

        self._dim = DimOverlay(central, close_callback=self._close_menu)
        self._dim.hide()

        self._overlay_menu = OverlayMenu(
            central,
            close_callback=self._close_menu,
            open_settings_callback=self._open_settings,
            select_profile_callback=self._on_select_profile,
            add_profile_callback=self._on_add_profile
        )

    def _load_initial_profile(self):
        profiles = get_all_profiles()
        if not profiles:
            self.left_panel.set_has_profile(False)
            return

        self.left_panel.set_has_profile(True)
        profile = get_last_used_profile()
        if not profile:
            profile = profiles[0]
            set_last_used(profile["name"])
        self._apply_profile(profile)

    def _apply_profile(self, profile: dict):
        """Apply a profile to the UI."""
        self._current_profile = profile
        self.left_panel.apply_profile(profile)

    def _on_select_profile(self, name: str):
        """Handle selecting a profile from the profile list."""
        profiles = get_all_profiles()
        profile = next((p for p in profiles if p["name"] == name), None)
        if profile:
            set_last_used(name)
            self._apply_profile(profile)

    def _on_add_profile(self):
        self._close_menu()
        self.left_panel.show_add_profile()

    def _toggle_menu(self):
        if self._menu_open:
            self._close_menu()
        else:
            self._open_menu()

    def _open_menu(self):
        self._menu_open = True
        central = self.centralWidget()
        h = central.height()
        w = central.width()

        self._bg_dim.setGeometry(0, 0, w, h)
        self._bg_dim.show()
        self._bg_dim.raise_()

        self._dim.setGeometry(MENU_WIDTH + 10, 0, w - MENU_WIDTH - 10, h)
        self._dim.show()
        self._dim.raise_()

        self._overlay_menu.slide_in(x=0, y=0, width=MENU_WIDTH, height=h)

    def _close_menu(self):
        if not self._menu_open:
            return
        self._menu_open = False
        self._bg_dim.hide()
        self._dim.hide()
        central = self.centralWidget()
        h = central.height()
        self._overlay_menu.slide_out(
            x=0, y=0, width=MENU_WIDTH, height=h, callback=lambda: None
        )

    def _open_settings(self):
        self.left_panel.show_settings()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_menu_open") or not self._menu_open:
            return
        central = self.centralWidget()
        h = central.height()
        w = central.width()
        self._bg_dim.setGeometry(0, 0, w, h)
        self._dim.setGeometry(MENU_WIDTH + 10, 0, w - MENU_WIDTH - 10, h)

    def _on_profile_created(self, data: dict):
        from core.profile_manager import load_profiles_index, load_profile, save_profile
        create_profile(data["name"])
        index = load_profiles_index()
        entry = next(
            (p for p in index["profiles"] if p["name"] == data["name"]), None
        )
        if entry:
            profile = load_profile(entry["config_path"])
            profile["brand"]          = data.get("brand", "vanilla")
            profile["version"]        = data.get("version", "")
            profile["loader_version"] = data.get("loader_version", "")
            profile["server_dir"]     = data.get("server_dir", "")
            profile["java_path"]      = data.get("java_path", "")
            save_profile(entry["config_path"], profile)

        self._overlay_menu.refresh()
        self.left_panel.set_has_profile(True)
        self._on_select_profile(data["name"])

    def _on_start_server(self):
        if self._server_process is not None:
            return
        if not self._current_profile:
            return


        self.right_panel.log_display.clear()
        profile = dict(self._current_profile)
        # Get server_dir from the Basic tab UI
        profile["server_dir"] = self.left_panel.basic_tab.dir_entry.text().strip()

        self._server_process = ServerProcess(profile)
        self._server_process.log_received.connect(
            self.right_panel.log_display.append_log
        )
        self._server_process.started_ok.connect(self._on_server_started)
        self._server_process.stopped.connect(self._on_server_stopped)
        self._server_process.failed.connect(self._on_server_failed)
        self._server_process.start()

        self.left_panel.basic_tab.start_btn.setEnabled(False)
        self.left_panel.basic_tab.stop_btn.setEnabled(True)
        self.left_panel.basic_tab.download_btn.setEnabled(False)

    def _on_stop_server(self):
        if self._server_process:
            self._server_process.stop()

    def _on_send_command(self, command: str):
        if self._server_process:
            self._server_process.send_command(command)

    def _on_server_started(self):
        self.right_panel.log_display.append_log("[INFO] Server started.")
        if self._current_profile:
            self._current_profile["_running"] = True
            self.left_panel.apply_profile(self._current_profile)
        self.left_panel.set_server_running(True)

    def _on_server_stopped(self, exit_code: int):
        self.right_panel.log_display.append_log(
            f"[INFO] Server stopped. (exit code: {exit_code})"
        )
        self._server_process = None
        self.left_panel.basic_tab.start_btn.setEnabled(
            self.left_panel.basic_tab.eula_checkbox.isChecked()
        )
        self.left_panel.basic_tab.stop_btn.setEnabled(False)
        self.left_panel.basic_tab.download_btn.setEnabled(True)
        if self._current_profile:
            self._current_profile["_running"] = False
            self.left_panel.apply_profile(self._current_profile)
        self.left_panel.set_server_running(False)

    def _on_server_failed(self, error: str):
        self.right_panel.log_display.append_log(f"[ERROR] {error}")
        self._server_process = None
        self.left_panel.basic_tab.start_btn.setEnabled(True)
        self.left_panel.basic_tab.stop_btn.setEnabled(False)
        self.left_panel.basic_tab.download_btn.setEnabled(True)

    def on_left_panel_event(self, event: str, **kwargs):
        if event == "profile_deleted":
            self._handle_profile_deleted(
                kwargs["name"], kwargs["delete_dir"]
            )
        elif event == "profile_renamed":
            self._handle_profile_renamed(
                kwargs["old_name"], kwargs["new_name"]
            )
        elif event == "add_profile":
            self._on_add_profile()

    def _handle_profile_deleted(self, name: str, delete_dir: bool):
        import shutil
        from core.profile_manager import delete_profile, get_all_profiles

        if delete_dir:
            profiles = get_all_profiles()
            profile  = next((p for p in profiles if p["name"] == name), None)
            if profile:
                server_dir = profile.get("server_dir", "")
                if server_dir and os.path.isdir(server_dir):
                    try:
                        shutil.rmtree(server_dir)
                        self.right_panel.log_display.append_log(
                            f"[INFO] Deleted directory: {server_dir}"
                        )
                    except Exception as e:
                        self.right_panel.log_display.append_log(
                            f"[ERROR] Failed to delete directory: {e}"
                        )

        delete_profile(name)
        self._overlay_menu.refresh()

        remaining = get_all_profiles()
        if remaining:
            self.left_panel.set_has_profile(True)
            self._on_select_profile(remaining[0]["name"])
        else:
            self.left_panel.set_has_profile(False)
            self._current_profile = None

    def _handle_profile_renamed(self, old_name: str, new_name: str):
        self._overlay_menu.refresh()
        if self._current_profile and self._current_profile.get("name") == old_name:
            self._current_profile["name"] = new_name
