import os

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel
from ui.overlays.overlay_menu import OverlayMenu
from core.bat_editor import generate_bat
from core.downloader import ServerDownloader
from core.server_process import ServerProcess, _find_jar
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
        self._server_processes: dict[str, ServerProcess] = {}
        self._startup_downloaders: dict[str, ServerDownloader] = {}
        self._pending_start_profiles: dict[str, dict] = {}
        self._syncing_profile = False
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
        self.left_panel.basic_tab.eula_checkbox.toggled.connect(
            lambda _: self._sync_action_buttons()
        )
        self.left_panel.basic_tab.dir_entry.editingFinished.connect(
            self._sync_action_buttons
        )

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
        name = profile.get("name", "")
        profile["_running"] = self._is_profile_running(name)
        self._current_profile = profile
        self._syncing_profile = True
        try:
            self.left_panel.apply_profile(profile)
        finally:
            self._syncing_profile = False
        if hasattr(self, "_overlay_menu"):
            self._overlay_menu.set_current_profile_name(profile.get("name", ""))
            self._overlay_menu.set_profile_running(
                name,
                profile.get("_running", False)
            )
        self._sync_action_buttons()

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
        if self._current_profile:
            self._overlay_menu.set_current_profile_name(
                self._current_profile.get("name", "")
            )
            self._overlay_menu.set_profile_running(
                self._current_profile.get("name", ""),
                self._is_profile_running(self._current_profile.get("name", ""))
            )

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
        try:
            create_profile(data["name"])
        except ValueError as e:
            self.right_panel.log_display.append_log(f"[ERROR] {e}")
            return False

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
        return True

    def _on_start_server(self):
        if not self._current_profile:
            return

        name = self._current_profile.get("name", "")
        if self._is_profile_running(name) or self._is_profile_downloading(name):
            self._sync_action_buttons()
            return

        self.right_panel.log_display.clear()
        profile = dict(self._current_profile)
        # Get server_dir from the Basic tab UI
        profile["server_dir"] = self.left_panel.basic_tab.dir_entry.text().strip()
        profile.update(self.left_panel.basic_tab.get_values())
        profile.update(self.left_panel.jvm_tab.get_values())

        if not self._ensure_startup_files(profile):
            return

        self._start_server_process(profile)

    def _ensure_startup_files(self, profile: dict) -> bool:
        name = profile.get("name", "")
        server_dir = profile.get("server_dir", "").strip()
        if not server_dir:
            self.right_panel.log_display.append_log("[ERROR] Server directory is not set.")
            return False
        try:
            os.makedirs(server_dir, exist_ok=True)
        except Exception as e:
            self.right_panel.log_display.append_log(
                f"[ERROR] Failed to create server directory: {e}"
            )
            return False

        if profile.get("custom_jar", False) and not profile.get("jar_path", "").strip():
            self.right_panel.log_display.append_log(
                "[ERROR] Custom jar is enabled but jar path is not set."
            )
            return False

        target_jar = self._missing_jar_download_target(profile)
        if not target_jar:
            return True

        profile["target_jar_path"] = target_jar
        self._pending_start_profiles[name] = profile
        self.right_panel.log_display.append_log(
            f"[INFO] Required jar not found. Downloading before start: {target_jar}"
        )
        self._start_startup_download(profile)
        return False

    def _missing_jar_download_target(self, profile: dict) -> str:
        server_dir = profile.get("server_dir", "").strip()
        if profile.get("custom_jar", False):
            jar_path = profile.get("jar_path", "").strip()
            if not os.path.isabs(jar_path):
                jar_path = os.path.join(server_dir, jar_path)
            profile["jar_path"] = jar_path
            return "" if os.path.exists(jar_path) else jar_path

        if _find_jar(profile):
            return ""

        expected = self.left_panel.basic_tab._expected_jar_name(
            profile.get("brand", "vanilla"),
            profile.get("version", ""),
            profile.get("loader_version", "")
        )
        if not expected:
            return ""
        return os.path.join(server_dir, expected)

    def _start_startup_download(self, profile: dict):
        name = profile.get("name", "")
        self._sync_action_buttons()
        self.left_panel.basic_tab.progress_label.setText(
            lang.get("ui.basic.download.progress").format(0)
        )

        downloader = ServerDownloader(profile)
        downloader.progress.connect(
            lambda downloaded, total, n=name:
                self._on_startup_download_progress(n, downloaded, total)
        )
        downloader.finished.connect(
            lambda path, n=name: self._on_startup_download_finished(n, path)
        )
        downloader.failed.connect(
            lambda error, n=name: self._on_startup_download_failed(n, error)
        )
        downloader.log.connect(self.right_panel.log_display.append_log)
        self._startup_downloaders[name] = downloader
        self._sync_action_buttons()
        downloader.start()

    def _on_startup_download_progress(self, name: str, downloaded: int, total: int):
        if total <= 0:
            return
        if not self._is_current_profile(name):
            return
        pct = int(downloaded / total * 100)
        self.left_panel.basic_tab.progress_label.setText(
            lang.get("ui.basic.download.progress").format(pct)
        )

    def _on_startup_download_finished(self, name: str, path: str):
        self.right_panel.log_display.append_log(
            f"[INFO] {name}: {lang.get('ui.basic.download.complete')}: {path}"
        )
        if self._is_current_profile(name):
            self.left_panel.basic_tab.progress_label.setText(
                lang.get("ui.basic.download.complete")
            )
        profile = self._pending_start_profiles.pop(name, None)
        self._startup_downloaders.pop(name, None)
        self._sync_action_buttons()
        if profile:
            self._sync_generated_bat(profile)
            self._start_server_process(profile)

    def _on_startup_download_failed(self, name: str, error: str):
        self.right_panel.log_display.append_log(
            f"[ERROR] {name}: {lang.get('ui.basic.download.failed').format(error)}"
        )
        self._startup_downloaders.pop(name, None)
        self._pending_start_profiles.pop(name, None)
        self._sync_action_buttons()

    def _start_server_process(self, profile: dict):
        name = profile.get("name", "")
        if not name or self._is_profile_running(name):
            self._sync_action_buttons()
            return
        self._sync_generated_bat(profile)

        process = ServerProcess(profile)
        process.log_received.connect(
            self.right_panel.log_display.append_log
        )
        process.started_ok.connect(
            lambda n=name: self._on_server_started(n)
        )
        process.stopped.connect(
            lambda exit_code, n=name: self._on_server_stopped(n, exit_code)
        )
        process.failed.connect(
            lambda error, n=name: self._on_server_failed(n, error)
        )
        self._server_processes[name] = process
        process.start()

        self._sync_action_buttons()

    def _on_stop_server(self):
        name = self._current_profile.get("name", "") if self._current_profile else ""
        process = self._server_processes.get(name)
        if process:
            self.left_panel.basic_tab.stop_btn.setEnabled(False)
            process.stop()

    def _on_send_command(self, command: str):
        name = self._current_profile.get("name", "") if self._current_profile else ""
        process = self._server_processes.get(name)
        if process:
            process.send_command(command)

    def _on_server_started(self, name: str):
        self.right_panel.log_display.append_log(f"[INFO] {name}: Server started.")
        self._set_profile_running(name, True)

    def _on_server_stopped(self, name: str, exit_code: int):
        self.right_panel.log_display.append_log(
            f"[INFO] {name}: Server stopped. (exit code: {exit_code})"
        )
        self._server_processes.pop(name, None)
        self._set_profile_running(name, False)

    def _on_server_failed(self, name: str, error: str):
        self.right_panel.log_display.append_log(f"[ERROR] {name}: {error}")
        self._server_processes.pop(name, None)
        self._set_profile_running(name, False)

    def _is_current_profile(self, name: str) -> bool:
        return bool(
            self._current_profile and
            self._current_profile.get("name", "") == name
        )

    def _is_profile_running(self, name: str) -> bool:
        return bool(name and name in self._server_processes)

    def _is_profile_downloading(self, name: str) -> bool:
        return bool(name and name in self._startup_downloaders)

    def _set_profile_running(self, name: str, running: bool):
        self._overlay_menu.set_profile_running(name, running)
        if self._is_current_profile(name):
            if self._current_profile:
                self._current_profile["_running"] = running
            self.left_panel.set_server_running(running)
            self._sync_action_buttons()

    def _sync_action_buttons(self):
        if not self._current_profile or self._syncing_profile:
            return

        name = self._current_profile.get("name", "")
        running = self._is_profile_running(name)
        downloading = self._is_profile_downloading(name)
        eula_ok = self.left_panel.basic_tab.eula_checkbox.isChecked()

        self.left_panel.basic_tab.start_btn.setEnabled(
            eula_ok and not running and not downloading
        )
        self.left_panel.basic_tab.stop_btn.setEnabled(running)
        self.left_panel.basic_tab.download_btn.setEnabled(
            not running and not downloading
        )

        if self._current_profile:
            self._current_profile["_running"] = running
            self._overlay_menu.set_profile_running(
                name,
                running
            )
        self.left_panel.set_server_running(running)

    def _sync_generated_bat(self, profile: dict):
        if profile.get("custom_flags", False):
            return

        server_dir = profile.get("server_dir", "").strip()
        exec_file = profile.get("exec_file", "").strip() or "start.bat"
        if not server_dir or not exec_file.endswith(".bat"):
            return

        jar_path = profile.get("target_jar_path", "").strip() or _find_jar(profile)
        if not jar_path:
            return

        jar_name = jar_path
        try:
            if os.path.dirname(os.path.abspath(jar_path)) == os.path.abspath(server_dir):
                jar_name = os.path.basename(jar_path)
        except Exception:
            pass

        java = "java"
        if profile.get("custom_java", False):
            java = profile.get("java_path", "").strip() or "java"

        generate_bat(
            bat_path=os.path.join(server_dir, exec_file),
            java=java,
            ram_min_mb=profile.get("ram_min_mb", 4096),
            ram_max_mb=profile.get("ram_max_mb", 8192),
            jar_name=jar_name,
            nogui=profile.get("nogui", True)
        )

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
            self._overlay_menu.set_current_profile_name("")

    def _handle_profile_renamed(self, old_name: str, new_name: str):
        if old_name in self._server_processes:
            self._server_processes[new_name] = self._server_processes.pop(old_name)
        if old_name in self._startup_downloaders:
            self._startup_downloaders[new_name] = self._startup_downloaders.pop(old_name)
        if old_name in self._pending_start_profiles:
            self._pending_start_profiles[new_name] = self._pending_start_profiles.pop(old_name)
            self._pending_start_profiles[new_name]["name"] = new_name
        if self._current_profile and self._current_profile.get("name") == old_name:
            self._current_profile["name"] = new_name
            self._overlay_menu.set_current_profile_name(new_name)
            self._sync_action_buttons()
        self._overlay_menu.refresh()
