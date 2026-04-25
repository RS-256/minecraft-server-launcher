from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QScrollArea,
    QFileDialog
)
from PyQt6.QtCore import Qt
from ui.theme import (
    STYLE_BUTTON, STYLE_BUTTON_TRANSPARENT,
    STYLE_INPUT, STYLE_COMBO, STYLE_CHECKBOX,
    STYLE_INPUT_ERROR,
    STYLE_SCROLL_AREA_THIN, STYLE_TRANSPARENT_BG,
    STYLE_LABEL_SECONDARY_SMALL, STYLE_LABEL_DISABLED_SMALL,
    STYLE_LABEL_PRIMARY_SMALL, STYLE_LABEL_DANGER_SMALL,
    STYLE_CHECKBOX_DISABLED_TEXT, FONT_SIZE_LARGE
)
from ui.widgets.collapsible_section import CollapsibleSection
from core.lang import lang
from core.version_fetcher import (
    VanillaVersionFetcher, FabricVersionFetcher,
    FabricLoaderFetcher, NeoForgeVersionFetcher
)
from core.profile_manager import get_server_profiles_dir

BRANDS = ["vanilla", "fabric", "neoforge", "spigot", "paper"]
FILTER_CATEGORIES = ["release", "snapshot", "beta", "alpha"]


class AddProfileView(QWidget):
    def __init__(self, parent=None, back_callback=None, confirm_callback=None):
        super().__init__(parent)
        self._back_callback    = back_callback
        self._confirm_callback = confirm_callback
        self._all_versions     = []
        self._neoforge_map: dict[str, list] = {}
        self._fetcher          = None
        self._loader_fetcher   = None
        self._active_threads: list = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(STYLE_SCROLL_AREA_THIN)

        inner = QWidget()
        inner.setStyleSheet(STYLE_TRANSPARENT_BG)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Back button
        back_btn = QPushButton(lang.get("ui.settings.back"))
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(STYLE_BUTTON_TRANSPARENT)
        back_btn.clicked.connect(self._on_back)
        layout.addWidget(back_btn)

        # Title
        title = QLabel(lang.get("ui.dialog.new_profile.title"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold;"
        )
        layout.addWidget(title)

        # Profile name
        layout.addWidget(QLabel(lang.get("ui.dialog.new_profile.name")))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(STYLE_INPUT)
        self.name_input.setPlaceholderText(
            lang.get("ui.dialog.new_profile.name.placeholder")
        )
        layout.addWidget(self.name_input)

        # Directory picker
        layout.addWidget(QLabel(lang.get("ui.add_profile.directory")))
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setStyleSheet(STYLE_INPUT)
        self.dir_input.setPlaceholderText(lang.get("ui.add_profile.directory"))
        browse_btn = QPushButton(lang.get("ui.left.browse"))
        browse_btn.setFixedWidth(70)
        browse_btn.setStyleSheet(STYLE_BUTTON)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # Brand and Minecraft version side by side
        brand_ver_row = QHBoxLayout()
        brand_ver_row.setSpacing(8)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(4)
        brand_col.addWidget(QLabel(lang.get("ui.dialog.new_profile.brand")))
        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(STYLE_COMBO)
        for b in BRANDS:
            self.brand_combo.addItem(b)
        self.brand_combo.currentTextChanged.connect(self._on_brand_changed)
        brand_col.addWidget(self.brand_combo)
        brand_ver_row.addLayout(brand_col, stretch=2)

        ver_col = QVBoxLayout()
        ver_col.setSpacing(4)
        ver_col.addWidget(QLabel(lang.get("ui.add_profile.version")))
        self.version_combo = QComboBox()
        self.version_combo.setStyleSheet(STYLE_COMBO)
        self.version_combo.addItem(lang.get("ui.add_profile.version.loading"))
        self.version_combo.setEnabled(False)
        self.version_combo.currentTextChanged.connect(self._on_mc_version_changed)
        ver_col.addWidget(self.version_combo)
        brand_ver_row.addLayout(ver_col, stretch=3)

        layout.addLayout(brand_ver_row)

        # Loader version, placed below the Minecraft version
        loader_row = QHBoxLayout()
        loader_row.setSpacing(8)
        loader_row.addStretch(2)  # Space matching the brand column width

        loader_col = QVBoxLayout()
        loader_col.setSpacing(4)
        self._loader_label = QLabel(lang.get("ui.add_profile.loader_version"))
        loader_col.addWidget(self._loader_label)
        self.loader_combo = QComboBox()
        self.loader_combo.setStyleSheet(STYLE_COMBO)
        self.loader_combo.setEnabled(False)
        loader_col.addWidget(self.loader_combo)
        loader_row.addLayout(loader_col, stretch=3)
        layout.addLayout(loader_row)

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
        java_label = QLabel(lang.get("ui.add_profile.java_path"))
        java_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL
        )
        java_label.setToolTip(lang.get("ui.add_profile.java_path.tooltip"))
        self._advanced.add_widget(java_label)

        java_widget = QWidget()
        java_widget.setStyleSheet(STYLE_TRANSPARENT_BG)
        java_row = QHBoxLayout(java_widget)
        java_row.setContentsMargins(0, 0, 0, 0)
        self.java_input = QLineEdit()
        self.java_input.setStyleSheet(STYLE_INPUT)
        self.java_input.setPlaceholderText(
            lang.get("ui.add_profile.java_path.placeholder")
        )
        java_browse_btn = QPushButton(lang.get("ui.left.browse"))
        java_browse_btn.setFixedWidth(70)
        java_browse_btn.setStyleSheet(STYLE_BUTTON)
        java_browse_btn.clicked.connect(self._browse_java)
        java_row.addWidget(self.java_input)
        java_row.addWidget(java_browse_btn)
        self._advanced.add_widget(java_widget)

        layout.addWidget(self._advanced)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            STYLE_LABEL_DANGER_SMALL
        )
        layout.addWidget(self.error_label)

        layout.addStretch()

        # Create button
        self.confirm_btn = QPushButton(lang.get("ui.add_profile.confirm"))
        self.confirm_btn.setStyleSheet(STYLE_BUTTON)
        self.confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(self.confirm_btn)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def reset(self):
        self.name_input.clear()
        self.dir_input.clear()
        self.java_input.clear()
        self.brand_combo.setCurrentIndex(0)
        self.error_label.setText("")
        self.name_input.setStyleSheet(STYLE_INPUT)
        for cat, cb in self._filter_checks.items():
            cb.setChecked(cat == "release")
        self._start_fetch()

    def _start_fetch(self):
        self.version_combo.clear()
        self.version_combo.addItem(lang.get("ui.add_profile.version.loading"))
        self.version_combo.setEnabled(False)
        self._reset_loader_combo()
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

        # Remove completed threads from the list
        fetcher.finished.connect(lambda _=None: self._remove_thread(fetcher))
        fetcher.failed.connect(lambda _=None: self._remove_thread(fetcher))

        self._fetcher = fetcher
        self._active_threads.append(fetcher)
        fetcher.start()

    def _reset_loader_combo(self):
        """Reset the loader combo box."""
        self.loader_combo.clear()
        self.loader_combo.setEnabled(False)

    def _on_brand_changed(self, brand: str):
        is_vanilla = brand == "vanilla"
        self._loader_label.setStyleSheet(
            STYLE_LABEL_DISABLED_SMALL if is_vanilla
            else STYLE_LABEL_PRIMARY_SMALL
        )

        # Define available filter categories by brand
        available = {
            "vanilla":  {"release", "snapshot", "beta", "alpha"},
            "fabric":   {"release", "snapshot"},
            "neoforge": {"release", "snapshot"},
            "spigot":   {"release"},
            "paper":    {"release"},
        }.get(brand, {"release"})

        for cat, cb in self._filter_checks.items():
            cb.setEnabled(cat in available)
            cb.setStyleSheet(
                STYLE_CHECKBOX if cat in available
                else STYLE_CHECKBOX + STYLE_CHECKBOX_DISABLED_TEXT
            )
            # Uncheck unavailable categories
            if cat not in available:
                cb.setChecked(False)
            # Keep release enabled by default
            elif cat == "release":
                cb.setChecked(True)

        self._start_fetch()

    def _on_fetch_finished(self, versions: list):
        """Handle completed Vanilla/Fabric Minecraft version fetches."""
        self._all_versions = versions
        self._refresh_version_combo()

    def _on_neoforge_fetch_finished(self, mc_map: dict):
        self._neoforge_map = mc_map

        # Determine each Minecraft version type from the first build's mc_type
        self._all_versions = []
        for mc_ver, builds in mc_map.items():
            mc_type = builds[0].get("mc_type", "release") if builds else "release"
            self._all_versions.append({
                "id":           mc_ver,
                "type":         mc_type,
                "release_time": "",
            })

        self._refresh_version_combo()

    def _on_fetch_failed(self, error: str):
        self.version_combo.clear()
        self.version_combo.addItem(lang.get("ui.add_profile.version.failed"))
        self.version_combo.setEnabled(False)
        self.error_label.setText(
            f"{lang.get('ui.add_profile.version.failed')}: {error}"
        )

    def _refresh_version_combo(self):
        """Refresh the Minecraft version dropdown based on filters."""
        brand = self.brand_combo.currentText()
        enabled_types = {
            cat for cat, cb in self._filter_checks.items() if cb.isChecked()
        }

        if brand == "neoforge":
            # NeoForge supports only release and beta here
            filtered = [
                v for v in self._all_versions
                if v["type"] in enabled_types
            ]
        else:
            filtered = [
                v for v in self._all_versions
                if v["type"] in enabled_types
            ]

        current = self.version_combo.currentText()
        self.version_combo.blockSignals(True)
        self.version_combo.clear()

        if not filtered:
            self.version_combo.addItem("---")
            self.version_combo.setEnabled(False)
            self.version_combo.blockSignals(False)
            return

        for v in filtered:
            self.version_combo.addItem(v["id"])

        idx = self.version_combo.findText(current)
        self.version_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.version_combo.setEnabled(True)
        self.version_combo.blockSignals(False)

        # Fetch loaders for the selected Minecraft version
        self._on_mc_version_changed(self.version_combo.currentText())

    def _on_mc_version_changed(self, mc_version: str):
        """Refresh loader versions when a Minecraft version is selected."""
        brand = self.brand_combo.currentText()
        self._reset_loader_combo()

        if not mc_version or mc_version in (
            lang.get("ui.add_profile.version.loading"),
            lang.get("ui.add_profile.version.failed"),
            "---"
        ):
            return

        if brand == "vanilla":
            # Vanilla does not need a loader
            self.loader_combo.addItem(lang.get("ui.add_profile.loader_version.na"))
            self.loader_combo.setEnabled(False)

        elif brand == "fabric":
            self.loader_combo.addItem(lang.get("ui.add_profile.version.loading"))
            loader_fetcher = FabricLoaderFetcher(mc_version)
            loader_fetcher.finished.connect(self._on_loader_fetch_finished)
            loader_fetcher.failed.connect(self._on_loader_fetch_failed)
            loader_fetcher.finished.connect(lambda _=None: self._remove_thread(loader_fetcher))
            loader_fetcher.failed.connect(lambda _=None: self._remove_thread(loader_fetcher))
            self._loader_fetcher = loader_fetcher
            self._active_threads.append(loader_fetcher)
            loader_fetcher.start()

        elif brand == "neoforge":
            # Read NeoForge builds from the local map
            builds = self._neoforge_map.get(mc_version, [])
            if builds:
                for b in builds:
                    self.loader_combo.addItem(b["id"])
                self.loader_combo.setEnabled(True)
            else:
                self.loader_combo.addItem("---")
                self.loader_combo.setEnabled(False)

        else:
            # Treat Spigot and Paper like Vanilla for now
            self.loader_combo.addItem(lang.get("ui.add_profile.loader_version.na"))
            self.loader_combo.setEnabled(False)

    def _on_loader_fetch_finished(self, loaders: list):
        self.loader_combo.clear()
        if not loaders:
            self.loader_combo.addItem("---")
            self.loader_combo.setEnabled(False)
            return
        for loader in loaders:
            self.loader_combo.addItem(loader["id"])
        self.loader_combo.setEnabled(True)

    def _on_loader_fetch_failed(self, error: str):
        self.loader_combo.clear()
        self.loader_combo.addItem(lang.get("ui.add_profile.version.failed"))
        self.loader_combo.setEnabled(False)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(
            self,
            lang.get("ui.browse.title"),
            get_server_profiles_dir()
        )
        if path:
            self.dir_input.setText(path)

    def _browse_java(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            lang.get("ui.add_profile.java_path"),
            "",
            "Java Executable (java.exe);;All Files (*)"
        )
        if path:
            self.java_input.setText(path)

    def _on_back(self):
        if self._back_callback:
            self._back_callback()

    def _on_confirm(self):
        name = self.name_input.text().strip()
        if not name:
            self.error_label.setText(
                lang.get("ui.dialog.new_profile.error.empty_name")
            )
            self.name_input.setStyleSheet(
                STYLE_INPUT + STYLE_INPUT_ERROR
            )
            return

        version = self.version_combo.currentText()
        if not version or version in (
            lang.get("ui.add_profile.version.loading"),
            lang.get("ui.add_profile.version.failed"),
            "---"
        ):
            self.error_label.setText(lang.get("ui.add_profile.version.failed"))
            return

        loader = self.loader_combo.currentText()

        if self._confirm_callback:
            self._confirm_callback({
                "name":           name,
                "brand":          self.brand_combo.currentText(),
                "version":        version,
                "loader_version": loader,
                "server_dir":     self.dir_input.text().strip(),
                "java_path":      self.java_input.text().strip(),
            })

    def _remove_thread(self, thread):
        """Remove a completed thread from the list."""
        if thread in self._active_threads:
            self._active_threads.remove(thread)
