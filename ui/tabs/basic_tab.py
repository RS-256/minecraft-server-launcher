import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QCheckBox, QFrame, QFileDialog,
    QMessageBox, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt
from ui.theme import (
    STYLE_BUTTON, STYLE_BUTTON_SUCCESS, STYLE_BUTTON_DANGER,
    STYLE_INPUT, STYLE_CHECKBOX, STYLE_COMBO,
    STYLE_INPUT_DISABLED, STYLE_SCROLL_AREA_THIN,
    STYLE_TRANSPARENT_BG, STYLE_BOTTOM_ACTION_BAR,
    STYLE_SEPARATOR, STYLE_LABEL_SECONDARY_SMALL,
    STYLE_LABEL_DISABLED_SMALL, STYLE_LABEL_PRIMARY_SMALL,
    STYLE_CHECKBOX_DISABLED_TEXT
)
from ui.widgets.collapsible_section import CollapsibleSection
from core.lang import lang
from core.profile_manager import get_server_profiles_dir
from core.downloader import ServerDownloader
from core.instance import save_profile_field, check_eula
from core.version_fetcher import (
    VanillaVersionFetcher, FabricVersionFetcher,
    FabricLoaderFetcher, NeoForgeVersionFetcher
)

BRANDS = ["vanilla", "fabric", "neoforge", "spigot", "paper"]
FILTER_CATEGORIES = ["release", "snapshot", "beta", "alpha"]

# ブランドごとの有効フィルター
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
        self._build()

    def set_log_callback(self, callback):
        self._log_callback = callback

    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)

    def _build(self):
        # 外枠レイアウト（スクロール＋固定ボタンの2段構成）
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── スクロールエリア ───────────────────────────
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

        # ── サーバーディレクトリ ───────────────────────
        dir_label = QLabel(lang.get("ui.left.server_directory"))
        dir_label.setToolTip(lang.get("ui.left.server_directory.tooltip"))
        layout.addWidget(dir_label)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(6)
        self.dir_entry = QLineEdit()
        self.dir_entry.setPlaceholderText(lang.get("ui.left.server_directory"))
        self.dir_entry.editingFinished.connect(self._on_dir_changed)
        browse_btn = QPushButton(lang.get("ui.left.browse"))
        browse_btn.setFixedWidth(70)
        browse_btn.setStyleSheet(STYLE_BUTTON)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_entry)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # ── ブランド（左） + MCバージョン（右）────────
        # 左端を揃えるためにQGridLayoutを使う
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 3)

        grid.addWidget(QLabel(lang.get("ui.basic.brand")), 0, 0)
        grid.addWidget(QLabel(lang.get("ui.basic.version")), 0, 1)

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
        grid.addWidget(self.version_combo, 1, 1)

        # ── Loaderバージョン（右列のみ） ───────────────
        self._loader_ver_label = QLabel(lang.get("ui.basic.loader_version"))
        grid.addWidget(self._loader_ver_label, 2, 1)

        self.loader_combo = QComboBox()
        self.loader_combo.setStyleSheet(STYLE_COMBO)
        self.loader_combo.setEnabled(False)
        self.loader_combo.currentTextChanged.connect(self._on_loader_changed)
        grid.addWidget(self.loader_combo, 3, 1)

        layout.addLayout(grid)

        layout.addWidget(self._make_separator())

        # ── EULA ──────────────────────────────────────
        eula_row = QHBoxLayout()
        self.eula_checkbox = QCheckBox(lang.get("ui.basic.eula"))
        self.eula_checkbox.setToolTip(lang.get("ui.basic.eula.tooltip"))
        self.eula_checkbox.setStyleSheet(STYLE_CHECKBOX)
        self.eula_checkbox.toggled.connect(self._on_eula_toggled)
        eula_row.addWidget(self.eula_checkbox)
        eula_row.addStretch()
        layout.addLayout(eula_row)

        # ── 詳細設定（折りたたみ） ─────────────────────
        self._advanced = CollapsibleSection(
            lang.get("ui.add_profile.advanced"),
            expanded=False
        )

        # バージョンフィルター
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

        # Javaパス
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
        java_browse_btn.setFixedWidth(70)
        java_browse_btn.setStyleSheet(STYLE_BUTTON)
        java_browse_btn.clicked.connect(self._browse_java)
        self._java_browse_btn = java_browse_btn
        self._java_browse_btn.setEnabled(False)
        java_row.addWidget(self.java_entry)
        java_row.addWidget(self._java_browse_btn)
        custom_java_col.addLayout(java_row)
        self._advanced.add_widget(custom_java_widget)

        # カスタムjar
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
        self.jar_browse_btn.setFixedWidth(70)
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

        # ── 固定ボタンエリア（スクロール外） ──────────
        btn_area = QWidget()
        btn_area.setStyleSheet(STYLE_BOTTOM_ACTION_BAR)
        btn_layout = QVBoxLayout(btn_area)
        btn_layout.setContentsMargins(12, 8, 12, 0)
        btn_layout.setSpacing(6)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL +
            "border: none;"
        )
        btn_layout.addWidget(self.progress_label)

        btn_row = QHBoxLayout()
        self.download_btn = QPushButton(lang.get("ui.basic.download"))
        self.download_btn.setStyleSheet(STYLE_BUTTON)
        self.download_btn.clicked.connect(self._on_download)

        self.start_btn = QPushButton(lang.get("ui.left.start"))
        self.start_btn.setStyleSheet(STYLE_BUTTON_SUCCESS)
        self.start_btn.setEnabled(False)

        self.stop_btn = QPushButton(lang.get("ui.left.stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(STYLE_BUTTON_DANGER)

        btn_row.addWidget(self.download_btn)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_layout.addLayout(btn_row)

        outer.addWidget(btn_area)

    # ── ユーティリティ ─────────────────────────────────

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

    # ── フェッチ ───────────────────────────────────────

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

    # ── コールバック ───────────────────────────────────

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
        self._save_field(server_dir=path)
        self._check_eula_file(path)

    def _on_eula_toggled(self, checked: bool):
        self._refresh_start_btn()
        if not checked:
            return
        server_dir = self.dir_entry.text().strip()
        if not server_dir:
            self._log("[WARN] Server directory is not set.")
            return
        self._write_eula(server_dir)

    def _check_eula_file(self, server_dir: str):
        agreed = check_eula(server_dir)
        self.eula_checkbox.blockSignals(True)
        self.eula_checkbox.setChecked(agreed)
        self.eula_checkbox.blockSignals(False)
        self._refresh_start_btn()

    def _write_eula(self, server_dir: str):
        eula_path = os.path.join(server_dir, "eula.txt")
        try:
            with open(eula_path, "w", encoding="utf-8") as f:
                f.write("# Minecraft EULA\n")
                f.write(f"# {lang.get('ui.basic.eula.url')}\n")
                f.write("eula=true\n")
            self._log(f"[INFO] EULA accepted: {eula_path}")
        except Exception as e:
            self._log(f"[ERROR] Failed to write eula.txt: {e}")

    def _save_field(self, **kwargs):
        name = self._current_profile.get("name", "")
        if not name:
            return
        self._current_profile.update(kwargs)
        save_profile_field(name, **kwargs)

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
            self._save_field(server_dir=path)
            self._check_eula_file(path)
            if self.eula_checkbox.isChecked():
                self._write_eula(path)

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
                reply = QMessageBox.question(
                    self, lang.get("ui.basic.download"),
                    lang.get("ui.basic.download.already_exists"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

        profile = dict(self._current_profile)
        profile["server_dir"]     = server_dir
        profile["brand"]          = brand
        profile["version"]        = version
        profile["loader_version"] = loader

        self.download_btn.setEnabled(False)
        self.progress_label.setText(
            lang.get("ui.basic.download.progress").format(0)
        )

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
            self.progress_label.setText(
                lang.get("ui.basic.download.progress").format(pct)
            )

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

        # どちらかにチェックが入っていればAdvanced Settingsを開く
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
            "custom_jar":     self.custom_jar_checkbox.isChecked(),
            "jar_path":       self.jar_entry.text().strip(),
            "custom_java":    self.custom_java_checkbox.isChecked(),
            "java_path":      self.java_entry.text().strip(),
        }
    
    def _notify_jvm_tab(self):
        """JVMタブにプロファイル変更を通知する"""
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
