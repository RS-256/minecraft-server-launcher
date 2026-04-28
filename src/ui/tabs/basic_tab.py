import os
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QCheckBox, QFrame, QFileDialog,
    QComboBox, QScrollArea, QToolButton, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from ui.theme import (
    STYLE_BUTTON, STYLE_BUTTON_SUCCESS, STYLE_BUTTON_DANGER,
    STYLE_INPUT, STYLE_CHECKBOX, STYLE_COMBO,
    STYLE_INPUT_DISABLED, STYLE_SCROLL_AREA_THIN,
    STYLE_TRANSPARENT_BG, STYLE_BOTTOM_ACTION_BAR,
    STYLE_SEPARATOR, STYLE_LABEL_SECONDARY_SMALL,
    STYLE_LABEL_DISABLED_SMALL, STYLE_LABEL_PRIMARY_SMALL,
    STYLE_CHECKBOX_DISABLED_TEXT, BROWSE_BUTTON_WIDTH,
    COLOR_BG_TERTIARY, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_DISABLED, COLOR_TEXT_DISABLED, COLOR_ACCENT,
    ICON_CHEVRON_DOWN
)
from ui.widgets.collapsible_section import CollapsibleSection
from ui.overlays.download_confirm_overlay import DownloadConfirmOverlay
from core.lang import lang
from core.profile_manager import get_server_profiles_dir
from core.backup import (
    BACKUP_SCOPE_FULL, BACKUP_SCOPE_WORLD, BACKUP_SCOPE_WORLD_CONFIG
)
from core.backup import create_backup
from core.downloader import ServerDownloader
from core.instance import save_profile_field, check_eula
from core.version_fetcher import (
    VanillaVersionFetcher, FabricVersionFetcher,
    FabricLoaderFetcher, NeoForgeVersionFetcher
)

BRANDS = ["vanilla", "fabric", "neoforge", "spigot", "paper"]
FILTER_CATEGORIES = ["release", "snapshot", "beta", "alpha"]
ACTION_BUTTON_HEIGHT = 36

STYLE_BACKUP_MENU_BUTTON = f"""
    QToolButton {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 6px;
        font-size: 12px;
    }}
    QToolButton:hover {{ background-color: rgb(74, 74, 74); }}
    QToolButton:disabled {{
        background-color: {COLOR_DISABLED};
        color: {COLOR_TEXT_DISABLED};
    }}
    QToolButton::menu-button {{
        border-left: 1px solid {COLOR_BORDER};
        width: 24px;
    }}
    QToolButton::menu-arrow {{
        image: url("{ICON_CHEVRON_DOWN}");
        width: 10px;
        height: 10px;
    }}
    QMenu {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
    }}
    QMenu::item {{
        padding: 6px 22px 6px 10px;
    }}
    QMenu::item:selected {{
        background-color: {COLOR_ACCENT};
        color: white;
    }}
"""

# Available filters by brand
BRAND_FILTERS = {
    "vanilla":  {"release", "snapshot", "beta", "alpha"},
    "fabric":   {"release", "snapshot"},
    "neoforge": {"release", "snapshot", "beta", "alpha"},
    "spigot":   {"release"},
    "paper":    {"release"},
}


class BasicTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_profile: dict = {}
        self._downloader = None
        self._log_callback = None
        self._all_versions: list = []
        self._neoforge_map: dict = {}
        self._fetcher = None
        self._loader_fetcher = None
        self._active_threads: list = []
        self._download_overlay = None
        self._last_progress_log_time = 0.0
        self._last_progress_logged_pct = -1
        self._build()

    def set_log_callback(self, callback):
        self._log_callback = callback

    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    def _build(self):
        # Outer layout with scroll area and fixed buttons
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(STYLE_SCROLL_AREA_THIN)

        inner = QWidget()
        inner.setStyleSheet(STYLE_TRANSPARENT_BG)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Server directory
        dir_label = QLabel(lang.get("ui.left.server_directory"))
        dir_label.setToolTip(lang.get("ui.left.server_directory.tooltip"))
        layout.addWidget(dir_label)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(6)
        self.dir_entry = QLineEdit()
        self.dir_entry.setPlaceholderText(lang.get("ui.left.server_directory"))
        self.dir_entry.editingFinished.connect(self._on_dir_changed)
        browse_btn = QPushButton(lang.get("ui.left.browse"))
        browse_btn.setFixedWidth(BROWSE_BUTTON_WIDTH)
        browse_btn.setStyleSheet(STYLE_BUTTON)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_entry)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # Brand on the left and Minecraft version on the right
        # Use QGridLayout to align the left edges
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 3)

        grid.addWidget(QLabel(lang.get("ui.basic.brand")), 0, 0)

        version_label_row = QWidget()
        version_label_row.setStyleSheet(STYLE_TRANSPARENT_BG)
        version_label_layout = QHBoxLayout(version_label_row)
        version_label_layout.setContentsMargins(0, 0, 0, 0)
        version_label_layout.setSpacing(6)
        version_label_layout.addWidget(QLabel(lang.get("ui.basic.version")))

        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.progress_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL +
            "border: none;"
        )
        version_label_layout.addWidget(self.progress_label, stretch=1)
        grid.addWidget(version_label_row, 0, 1)

        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(STYLE_COMBO)
        for b in BRANDS:
            self.brand_combo.addItem(b)
        self.brand_combo.currentTextChanged.connect(self._on_brand_changed)
        grid.addWidget(self.brand_combo, 1, 0)

        self.version_combo = QComboBox()
        self.version_combo.setStyleSheet(STYLE_COMBO)
        self.version_combo.setEnabled(False)
        self.version_combo.currentTextChanged.connect(self._on_mc_version_changed)

        version_row_widget = QWidget()
        version_row_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        version_row = QHBoxLayout(version_row_widget)
        version_row.setContentsMargins(0, 0, 0, 0)
        version_row.setSpacing(6)
        version_row.addWidget(self.version_combo)

        self.download_btn = QPushButton("📥")
        self.download_btn.setStyleSheet(
            STYLE_BUTTON +
            """
            QPushButton {
                padding: 0px;
                font-size: 16px;
            }
            """
        )
        self.download_btn.setFixedSize(34, 34)
        self.download_btn.setToolTip(lang.get("ui.basic.download"))
        self.download_btn.clicked.connect(self._on_download)
        version_row.addWidget(self.download_btn)

        grid.addWidget(version_row_widget, 1, 1)

        # Loader version in the right column only
        self._loader_ver_label = QLabel(lang.get("ui.basic.loader_version"))
        grid.addWidget(self._loader_ver_label, 2, 1)

        self.loader_combo = QComboBox()
        self.loader_combo.setStyleSheet(STYLE_COMBO)
        self.loader_combo.setEnabled(False)
        self.loader_combo.currentTextChanged.connect(self._on_loader_changed)
        grid.addWidget(self.loader_combo, 3, 1)

        layout.addLayout(grid)

        layout.addWidget(self._make_separator())

        # EULA
        eula_row = QHBoxLayout()
        self.eula_checkbox = QCheckBox(lang.get("ui.basic.eula"))
        self.eula_checkbox.setToolTip(lang.get("ui.basic.eula.tooltip"))
        self.eula_checkbox.setStyleSheet(STYLE_CHECKBOX)
        self.eula_checkbox.toggled.connect(self._on_eula_toggled)
        eula_row.addWidget(self.eula_checkbox)
        eula_row.addStretch()
        layout.addLayout(eula_row)

        # Collapsible advanced settings
        self._advanced = CollapsibleSection(
            lang.get("ui.add_profile.advanced"),
            expanded=False
        )

        # Version filter
        filter_label = QLabel(lang.get("ui.add_profile.version.filter.label"))
        filter_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL
        )
        self._advanced.add_widget(filter_label)

        filter_widget = QWidget()
        filter_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(12)
        self._filter_checks: dict[str, QCheckBox] = {}
        for cat in FILTER_CATEGORIES:
            cb = QCheckBox(lang.get(f"ui.add_profile.version.filter.{cat}"))
            cb.setStyleSheet(STYLE_CHECKBOX)
            cb.setChecked(cat == "release")
            cb.stateChanged.connect(self._refresh_version_combo)
            self._filter_checks[cat] = cb
            filter_layout.addWidget(cb)
        filter_layout.addStretch()
        self._advanced.add_widget(filter_widget)

        # Java path
        custom_java_row = QHBoxLayout()
        self.custom_java_checkbox = QCheckBox(lang.get("ui.basic.custom_java"))
        self.custom_java_checkbox.setToolTip(lang.get("ui.basic.custom_java.tooltip"))
        self.custom_java_checkbox.setStyleSheet(STYLE_CHECKBOX)
        self.custom_java_checkbox.toggled.connect(self._on_custom_java_toggled)
        custom_java_row.addWidget(self.custom_java_checkbox)
        custom_java_row.addStretch()

        custom_java_widget = QWidget()
        custom_java_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        custom_java_col = QVBoxLayout(custom_java_widget)
        custom_java_col.setContentsMargins(0, 0, 0, 0)
        custom_java_col.setSpacing(4)
        custom_java_col.addLayout(custom_java_row)

        self.java_path_label = QLabel(lang.get("ui.add_profile.java_path"))
        self.java_path_label.setStyleSheet(
            STYLE_LABEL_DISABLED_SMALL
        )
        self.java_path_label.setToolTip(lang.get("ui.add_profile.java_path.tooltip"))
        custom_java_col.addWidget(self.java_path_label)

        java_row = QHBoxLayout()
        java_row.setSpacing(6)
        self.java_entry = QLineEdit()
        self.java_entry.setStyleSheet(self._jar_style(enabled=False))
        self.java_entry.setPlaceholderText(
            lang.get("ui.add_profile.java_path.placeholder")
        )
        self.java_entry.setEnabled(False)
        self.java_entry.editingFinished.connect(self._on_java_path_changed)
        java_browse_btn = QPushButton(lang.get("ui.left.browse"))
        java_browse_btn.setFixedWidth(BROWSE_BUTTON_WIDTH)
        java_browse_btn.setStyleSheet(STYLE_BUTTON)
        java_browse_btn.clicked.connect(self._browse_java)
        self._java_browse_btn = java_browse_btn
        self._java_browse_btn.setEnabled(False)
        java_row.addWidget(self.java_entry)
        java_row.addWidget(self._java_browse_btn)
        custom_java_col.addLayout(java_row)
        self._advanced.add_widget(custom_java_widget)

        # Custom jar
        custom_jar_widget = QWidget()
        custom_jar_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        custom_jar_col = QVBoxLayout(custom_jar_widget)
        custom_jar_col.setContentsMargins(0, 4, 0, 0)
        custom_jar_col.setSpacing(6)

        cj_row = QHBoxLayout()
        self.custom_jar_checkbox = QCheckBox(lang.get("ui.basic.custom_jar"))
        self.custom_jar_checkbox.setToolTip(lang.get("ui.basic.custom_jar.tooltip"))
        self.custom_jar_checkbox.setStyleSheet(STYLE_CHECKBOX)
        self.custom_jar_checkbox.toggled.connect(self._on_custom_jar_toggled)
        cj_row.addWidget(self.custom_jar_checkbox)
        cj_row.addStretch()
        custom_jar_col.addLayout(cj_row)

        self.jar_path_label = QLabel(lang.get("ui.basic.jar_path"))
        self.jar_path_label.setStyleSheet(
            STYLE_LABEL_DISABLED_SMALL
        )
        custom_jar_col.addWidget(self.jar_path_label)

        jar_file_row = QHBoxLayout()
        jar_file_row.setSpacing(6)
        self.jar_entry = QLineEdit()
        self.jar_entry.setPlaceholderText(lang.get("ui.basic.jar_path.placeholder"))
        self.jar_entry.setEnabled(False)
        self.jar_entry.setStyleSheet(self._jar_style(enabled=False))
        self.jar_entry.editingFinished.connect(self._on_jar_path_changed)
        self.jar_browse_btn = QPushButton(lang.get("ui.jvm.jar_path.browse"))
        self.jar_browse_btn.setFixedWidth(BROWSE_BUTTON_WIDTH)
        self.jar_browse_btn.setStyleSheet(STYLE_BUTTON)
        self.jar_browse_btn.setEnabled(False)
        self.jar_browse_btn.clicked.connect(self._browse_jar)
        jar_file_row.addWidget(self.jar_entry)
        jar_file_row.addWidget(self.jar_browse_btn)
        custom_jar_col.addLayout(jar_file_row)
        self._advanced.add_widget(custom_jar_widget)

        layout.addWidget(self._advanced)
        layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll, stretch=1)

        # Fixed button area outside the scroll area
        btn_area = QWidget()
        btn_area.setStyleSheet(STYLE_BOTTOM_ACTION_BAR)
        btn_layout = QVBoxLayout(btn_area)
        btn_layout.setContentsMargins(12, 8, 12, 0)
        btn_layout.setSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.backup_btn = QToolButton()
        self.backup_btn.setText(lang.get("ui.basic.backup"))
        self.backup_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.backup_btn.setStyleSheet(STYLE_BACKUP_MENU_BUTTON)
        self.backup_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.backup_btn.setFixedHeight(ACTION_BUTTON_HEIGHT)
        self.backup_btn.clicked.connect(
            lambda: self._run_backup(BACKUP_SCOPE_WORLD)
        )
        self._backup_menu = QMenu(self.backup_btn)
        self._backup_menu.setStyleSheet(STYLE_BACKUP_MENU_BUTTON)
        self._add_backup_action(
            lang.get("ui.basic.backup.scope.world"),
            BACKUP_SCOPE_WORLD
        )
        self._add_backup_action(
            lang.get("ui.basic.backup.scope.world_config"),
            BACKUP_SCOPE_WORLD_CONFIG
        )
        self._add_backup_action(
            lang.get("ui.basic.backup.scope.full"),
            BACKUP_SCOPE_FULL
        )
        self.backup_btn.setMenu(self._backup_menu)

        self.start_btn = QPushButton(lang.get("ui.left.start"))
        self.start_btn.setStyleSheet(STYLE_BUTTON_SUCCESS)
        self.start_btn.setEnabled(False)
        self.start_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.start_btn.setFixedHeight(ACTION_BUTTON_HEIGHT)

        self.stop_btn = QPushButton(lang.get("ui.left.stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(STYLE_BUTTON_DANGER)
        self.stop_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.stop_btn.setFixedHeight(ACTION_BUTTON_HEIGHT)

        btn_row.addWidget(self.backup_btn, stretch=1)
        btn_row.addWidget(self.start_btn, stretch=1)
        btn_row.addWidget(self.stop_btn, stretch=1)
        btn_layout.addLayout(btn_row)

        outer.addWidget(btn_area)

    # Utilities

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLE_SEPARATOR)
        return line

    def _jar_style(self, enabled: bool) -> str:
        if enabled:
            return STYLE_INPUT
        return STYLE_INPUT_DISABLED

    def _refresh_start_btn(self):
        eula_ok = self.eula_checkbox.isChecked()
        self.start_btn.setEnabled(eula_ok)
        self.start_btn.setToolTip(
            "" if eula_ok else lang.get("ui.basic.eula.tooltip")
        )

    def _refresh_loader_visibility(self):
        brand = self.brand_combo.currentText()
        needs_loader = brand not in ("vanilla", "spigot", "paper")
        visible = brand != "vanilla"
        self._loader_ver_label.setVisible(visible)
        self.loader_combo.setVisible(visible)
        self.loader_combo.setEnabled(needs_loader)
        self._loader_ver_label.setStyleSheet(
            STYLE_LABEL_PRIMARY_SMALL if needs_loader
            else STYLE_LABEL_DISABLED_SMALL
        )

    def _refresh_jar_ui(self, enabled: bool):
        self.jar_entry.setEnabled(enabled)
        self.jar_browse_btn.setEnabled(enabled)
        self.jar_entry.setStyleSheet(self._jar_style(enabled=enabled))
        self.jar_path_label.setStyleSheet(
            STYLE_LABEL_PRIMARY_SMALL
            if enabled else
            STYLE_LABEL_DISABLED_SMALL
        )

    # Fetching

    def _start_fetch(self):
        self.version_combo.clear()
        self.version_combo.addItem(lang.get("ui.add_profile.version.loading"))
        self.version_combo.setEnabled(False)
        self.loader_combo.clear()
        self.loader_combo.setEnabled(False)
        self._all_versions = []
        self._neoforge_map = {}

        brand = self.brand_combo.currentText()
        if brand == "fabric":
            fetcher = FabricVersionFetcher()
            fetcher.finished.connect(self._on_fetch_finished)
            fetcher.failed.connect(self._on_fetch_failed)
        elif brand == "neoforge":
            fetcher = NeoForgeVersionFetcher()
            fetcher.finished.connect(self._on_neoforge_fetch_finished)
            fetcher.failed.connect(self._on_fetch_failed)
        else:
            fetcher = VanillaVersionFetcher()
            fetcher.finished.connect(self._on_fetch_finished)
            fetcher.failed.connect(self._on_fetch_failed)

        fetcher.finished.connect(lambda _=None: self._remove_thread(fetcher))
        fetcher.failed.connect(lambda _=None: self._remove_thread(fetcher))
        self._fetcher = fetcher
        self._active_threads.append(fetcher)
        fetcher.start()

    def _remove_thread(self, thread):
        if thread in self._active_threads:
            self._active_threads.remove(thread)

    def _on_fetch_finished(self, versions: list):
        self._all_versions = versions
        self._refresh_version_combo()

    def _on_neoforge_fetch_finished(self, mc_map: dict):
        self._neoforge_map = mc_map
        self._all_versions = [
            {"id": mc, "type": "release", "release_time": ""}
            for mc in mc_map.keys()
        ]
        self._refresh_version_combo()

    def _on_fetch_failed(self, error: str):
        self.version_combo.clear()
        self.version_combo.addItem(lang.get("ui.add_profile.version.failed"))
        self.version_combo.setEnabled(False)

    def _refresh_version_combo(self):
        enabled_types = {
            cat for cat, cb in self._filter_checks.items() if cb.isChecked()
        }
        filtered = [v for v in self._all_versions if v["type"] in enabled_types]
        current = self._current_profile.get("version", "")

        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for v in filtered:
            self.version_combo.addItem(v["id"])
        idx = self.version_combo.findText(current)
        self.version_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.version_combo.setEnabled(bool(filtered))
        self.version_combo.blockSignals(False)

        self._on_mc_version_changed(self.version_combo.currentText())

    def _on_mc_version_changed(self, mc_version: str):
        if not mc_version or mc_version in (
            lang.get("ui.add_profile.version.loading"),
            lang.get("ui.add_profile.version.failed"),
        ):
            return
        self._save_field(version=mc_version)
        brand = self.brand_combo.currentText()
        self.loader_combo.clear()
        self.loader_combo.setEnabled(False)

        if brand == "fabric":
            self.loader_combo.addItem(lang.get("ui.add_profile.version.loading"))
            loader_fetcher = FabricLoaderFetcher(mc_version)
            loader_fetcher.finished.connect(self._on_loader_fetch_finished)
            loader_fetcher.failed.connect(lambda e: self.loader_combo.clear())
            loader_fetcher.finished.connect(
                lambda _=None: self._remove_thread(loader_fetcher)
            )
            self._loader_fetcher = loader_fetcher
            self._active_threads.append(loader_fetcher)
            loader_fetcher.start()
        elif brand == "neoforge":
            builds = self._neoforge_map.get(mc_version, [])
            for b in builds:
                self.loader_combo.addItem(b["id"])
            if builds:
                self.loader_combo.setEnabled(True)
                saved = self._current_profile.get("loader_version", "")
                idx = self.loader_combo.findText(saved)
                if idx >= 0:
                    self.loader_combo.setCurrentIndex(idx)
        else:
            self.loader_combo.addItem(lang.get("ui.basic.loader_version.na"))

    def _on_loader_fetch_finished(self, loaders: list):
        self.loader_combo.clear()
        for l in loaders:
            self.loader_combo.addItem(l["id"])
        if loaders:
            self.loader_combo.setEnabled(True)
            saved = self._current_profile.get("loader_version", "")
            idx = self.loader_combo.findText(saved)
            if idx >= 0:
                self.loader_combo.setCurrentIndex(idx)

    # Callbacks

    def _on_brand_changed(self, brand: str):
        self._refresh_loader_visibility()
        self._save_field(brand=brand)
        available = BRAND_FILTERS.get(brand, {"release"})
        for cat, cb in self._filter_checks.items():
            cb.setEnabled(cat in available)
            cb.setStyleSheet(
                STYLE_CHECKBOX if cat in available
                else STYLE_CHECKBOX + STYLE_CHECKBOX_DISABLED_TEXT
            )
            if cat not in available:
                cb.setChecked(False)
            elif cat == "release":
                cb.setChecked(True)
        self._start_fetch()

    def _on_loader_changed(self, loader: str):
        if loader and loader != lang.get("ui.add_profile.version.loading"):
            self._save_field(loader_version=loader)

    def _on_dir_changed(self):
        path = self.dir_entry.text().strip()
        self._save_field(server_dir=path, eula_agreed=False)
        self._check_eula_file(path)
        self._refresh_backup_btn()

    def _on_eula_toggled(self, checked: bool):
        self._refresh_start_btn()
        if not checked:
            self._save_field(eula_agreed=False)
            return
        server_dir = self.dir_entry.text().strip()
        if not server_dir:
            self._log("[WARN] Server directory is not set.")
            self.eula_checkbox.blockSignals(True)
            self.eula_checkbox.setChecked(False)
            self.eula_checkbox.blockSignals(False)
            self._refresh_start_btn()
            return
        if self._write_eula(server_dir):
            self._save_field(eula_agreed=True)
        else:
            self.eula_checkbox.blockSignals(True)
            self.eula_checkbox.setChecked(False)
            self.eula_checkbox.blockSignals(False)
            self._refresh_start_btn()

    def _check_eula_file(self, server_dir: str):
        agreed = self._current_profile.get("eula_agreed", False) and check_eula(server_dir)
        self.eula_checkbox.blockSignals(True)
        self.eula_checkbox.setChecked(agreed)
        self.eula_checkbox.blockSignals(False)
        self._refresh_start_btn()

    def _write_eula(self, server_dir: str) -> bool:
        eula_path = os.path.join(server_dir, "eula.txt")
        try:
            with open(eula_path, "w", encoding="utf-8") as f:
                f.write("# Minecraft EULA\n")
                f.write(f"# {lang.get('ui.basic.eula.url')}\n")
                f.write("eula=true\n")
            self._log(f"[INFO] EULA accepted: {eula_path}")
            return True
        except Exception as e:
            self._log(f"[ERROR] Failed to write eula.txt: {e}")
            return False

    def _save_field(self, **kwargs):
        name = self._current_profile.get("name", "")
        if not name:
            return
        self._current_profile.update(kwargs)
        save_profile_field(name, **kwargs)

    def _refresh_backup_btn(self):
        server_dir = self.dir_entry.text().strip()
        self.backup_btn.setEnabled(bool(server_dir and os.path.isdir(server_dir)))

    def _add_backup_action(self, label: str, scope: str):
        action = QAction(label, self._backup_menu)
        action.triggered.connect(lambda _, s=scope: self._run_backup(s))
        self._backup_menu.addAction(action)

    def _run_backup(self, scope: str):
        server_dir = self.dir_entry.text().strip()
        self._save_field(backup_scope=scope)
        try:
            path = create_backup(server_dir, scope)
        except Exception as e:
            self._log(f"[ERROR] {lang.get('ui.basic.backup.failed').format(e)}")
            return
        self._log(f"[INFO] {lang.get('ui.basic.backup.complete')}: {path}")

    def _on_custom_jar_toggled(self, checked: bool):
        self._refresh_jar_ui(checked)
        self._save_field(custom_jar=checked)

    def _on_jar_path_changed(self):
        path = self.jar_entry.text().strip()
        self._save_field(jar_path=path)
        self._notify_jvm_tab()

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, lang.get("ui.browse.title"), get_server_profiles_dir()
        )
        if path:
            self.dir_entry.setText(path)
            self._save_field(server_dir=path, eula_agreed=False)
            self._check_eula_file(path)
            self._refresh_backup_btn()

    def _browse_java(self):
        path, _ = QFileDialog.getOpenFileName(
            self, lang.get("ui.add_profile.java_path"), "",
            "Java Executable (java.exe);;All Files (*)"
        )
        if path:
            self.java_entry.setText(path)
            self._save_field(java_path=path)
            self._notify_jvm_tab()

    def _browse_jar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, lang.get("ui.basic.jar_path"), "",
            "Jar Files (*.jar);;All Files (*)"
        )
        if path:
            self.jar_entry.setText(path)
            self._save_field(jar_path=path)
            self._notify_jvm_tab()

    def _on_download(self):
        server_dir = self.dir_entry.text().strip()
        if not server_dir:
            self._log(f"[ERROR] {lang.get('ui.basic.download.no_dir')}")
            return

        brand   = self.brand_combo.currentText()
        version = self.version_combo.currentText()
        loader  = self.loader_combo.currentText()

        expected = self._expected_jar_name(brand, version, loader)
        if expected:
            jar_path = os.path.join(server_dir, expected)
            if os.path.exists(jar_path):
                self._show_download_overwrite_overlay(expected)
                return

        self._start_download(server_dir, brand, version, loader)

    def _show_download_overwrite_overlay(self, jar_name: str):
        if self._download_overlay:
            return

        window = self.window()
        central = window.centralWidget() if window else None
        parent = window if window else self

        self._download_overlay = DownloadConfirmOverlay(
            parent,
            central,
            jar_name,
            confirm_callback=self._on_download_overwrite_confirmed,
            cancel_callback=self._close_download_overlay
        )
        if central:
            top_left = central.mapTo(parent, central.rect().topLeft())
            self._download_overlay.setGeometry(
                top_left.x(), top_left.y(), central.width(), central.height()
            )
        else:
            self._download_overlay.setGeometry(parent.rect())
        self._download_overlay.show()
        self._download_overlay.raise_()

    def _close_download_overlay(self):
        if self._download_overlay:
            self._download_overlay.close_overlay()
            self._download_overlay = None

    def _on_download_overwrite_confirmed(self):
        self._close_download_overlay()
        server_dir = self.dir_entry.text().strip()
        brand = self.brand_combo.currentText()
        version = self.version_combo.currentText()
        loader = self.loader_combo.currentText()
        self._start_download(server_dir, brand, version, loader)

    def _start_download(self, server_dir: str, brand: str, version: str, loader: str):
        profile = dict(self._current_profile)
        profile["server_dir"]     = server_dir
        profile["brand"]          = brand
        profile["version"]        = version
        profile["loader_version"] = loader

        self.download_btn.setEnabled(False)
        self._last_progress_log_time = 0.0
        self._last_progress_logged_pct = -1
        self._set_download_progress(0, force_log=True)

        self._downloader = ServerDownloader(profile)
        self._downloader.progress.connect(self._on_progress)
        self._downloader.finished.connect(self._on_download_finished)
        self._downloader.failed.connect(self._on_download_failed)
        self._downloader.log.connect(self._log)
        self._downloader.start()

    def _expected_jar_name(self, brand: str, version: str, loader: str) -> str:
        if brand == "vanilla":
            return f"server-{version}-vanilla.jar"
        elif brand == "fabric":
            return f"server-{version}-fabric-{loader}.jar"
        elif brand == "neoforge":
            return f"server-{version}-neoforge-{loader}-installer.jar"
        return ""

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int(downloaded / total * 100)
            self._set_download_progress(pct)

    def _set_download_progress(self, pct: int, force_log: bool = False):
        msg = lang.get("ui.basic.download.progress").format(pct)
        self.progress_label.setText(msg)

        now = time.monotonic()
        should_log = (
            force_log or
            pct >= 100 or
            (
                pct != self._last_progress_logged_pct and
                now - self._last_progress_log_time >= 1.0
            )
        )
        if should_log:
            self._log(f"[INFO] {msg}")
            self._last_progress_log_time = now
            self._last_progress_logged_pct = pct

    def _on_download_finished(self, path: str):
        self.download_btn.setEnabled(True)
        self.progress_label.setText(lang.get("ui.basic.download.complete"))
        self._log(f"[INFO] {lang.get('ui.basic.download.complete')}: {path}")

    def _on_download_failed(self, error: str):
        self.download_btn.setEnabled(True)
        msg = lang.get("ui.basic.download.failed").format(error)
        self.progress_label.setText(msg)
        self._log(f"[ERROR] {msg}")

    def set_values(self, profile: dict):
        self._current_profile = profile
        self.dir_entry.setText(profile.get("server_dir", ""))
        self._refresh_backup_btn()

        brand = profile.get("brand", "vanilla")
        self.brand_combo.blockSignals(True)
        idx = self.brand_combo.findText(brand)
        self.brand_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.brand_combo.blockSignals(False)
        self._refresh_loader_visibility()

        for cat, cb in self._filter_checks.items():
            cb.blockSignals(True)
            cb.setChecked(cat == "release")
            cb.blockSignals(False)

        self._start_fetch()

        # custom java
        custom_java = profile.get("custom_java", False)
        self.custom_java_checkbox.blockSignals(True)
        self.custom_java_checkbox.setChecked(custom_java)
        self.custom_java_checkbox.blockSignals(False)
        self.java_entry.setText(profile.get("java_path", ""))
        self.java_entry.setEnabled(custom_java)
        self._java_browse_btn.setEnabled(custom_java)
        self.java_entry.setStyleSheet(self._jar_style(enabled=custom_java))
        self.java_path_label.setStyleSheet(
            STYLE_LABEL_PRIMARY_SMALL
            if custom_java else
            STYLE_LABEL_DISABLED_SMALL
        )

        # custom jar
        custom_jar = profile.get("custom_jar", False)
        self.custom_jar_checkbox.blockSignals(True)
        self.custom_jar_checkbox.setChecked(custom_jar)
        self.custom_jar_checkbox.blockSignals(False)
        self.jar_entry.setText(profile.get("jar_path", ""))
        self._refresh_jar_ui(custom_jar)

        # Open advanced settings when either option is enabled
        if custom_java or custom_jar:
            self._advanced.set_expanded(True)
        else:
            self._advanced.set_expanded(False)

        self._check_eula_file(profile.get("server_dir", ""))

    def get_values(self) -> dict:
        return {
            "server_dir":     self.dir_entry.text().strip(),
            "brand":          self.brand_combo.currentText(),
            "version":        self.version_combo.currentText(),
            "loader_version": self.loader_combo.currentText(),
            "eula_agreed":    self.eula_checkbox.isChecked(),
            "custom_jar":     self.custom_jar_checkbox.isChecked(),
            "jar_path":       self.jar_entry.text().strip(),
            "custom_java":    self.custom_java_checkbox.isChecked(),
            "java_path":      self.java_entry.text().strip(),
            "backup_scope":   self._current_profile.get("backup_scope", BACKUP_SCOPE_WORLD),
        }
    
    def _notify_jvm_tab(self):
        """Notify the JVM tab that profile settings changed."""
        parent = self.parent()
        while parent:
            if hasattr(parent, "jvm_tab"):
                parent.jvm_tab.notify_profile_changed()
                return
            parent = parent.parent() if hasattr(parent, "parent") else None
    
    def _on_java_path_changed(self):
        path = self.java_entry.text().strip()
        self._save_field(java_path=path)
        self._notify_jvm_tab()
    
    def _on_custom_java_toggled(self, checked: bool):
        self.java_entry.setEnabled(checked)
        self._java_browse_btn.setEnabled(checked)
        self.java_entry.setStyleSheet(self._jar_style(enabled=checked))
        self.java_path_label.setStyleSheet(
            STYLE_LABEL_PRIMARY_SMALL
            if checked else
            STYLE_LABEL_DISABLED_SMALL
        )
        if not checked:
            self.java_entry.clear()
            self._save_field(custom_java=False, java_path="")
        else:
            self._save_field(custom_java=True)
        self._notify_jvm_tab()
