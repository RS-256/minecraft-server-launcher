import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox,
    QTextEdit, QLineEdit, QFrame,
)
from PyQt6.QtCore import Qt
from ui.theme import (
    STYLE_BUTTON, STYLE_CHECKBOX, STYLE_TEXT_EDIT_ACTIVE,
    STYLE_TEXT_EDIT_INACTIVE, STYLE_SEPARATOR,
    STYLE_LABEL_DISABLED_SMALL, STYLE_LABEL_PRIMARY_SMALL,
    STYLE_LABEL_BAT_PREVIEW
)
from ui.widgets.toggle_switch import ToggleSwitch
from ui.widgets.range_slider import RangeSlider
from core.lang import lang
from core.bat_editor import generate_bat, read_bat, write_bat
from core.instance import save_profile_field


class JvmTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_profile: dict = {}
        self._updating = False
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 実行ファイル名
        file_label = QLabel(lang.get("ui.left.file_name"))
        file_label.setToolTip(lang.get("ui.left.file_name.tooltip"))
        layout.addWidget(file_label)
        self.file_entry = QLineEdit()
        self.file_entry.setPlaceholderText("start.bat")
        self.file_entry.editingFinished.connect(self._on_exec_file_changed)
        layout.addWidget(self.file_entry)

        layout.addWidget(self._make_separator())

        # RAMスライダー
        ram_label = QLabel(lang.get("ui.jvm.ram"))
        ram_label.setToolTip(lang.get("ui.jvm.ram.tooltip"))
        layout.addWidget(ram_label)
        self.ram_slider = RangeSlider()
        self.ram_slider.mouseReleaseEvent = self._on_slider_released
        layout.addWidget(self.ram_slider)

        # nogui トグル
        nogui_row = QHBoxLayout()
        self.nogui_label = QLabel(lang.get("ui.jvm.nogui"))
        self.nogui_label.setToolTip(lang.get("ui.jvm.nogui.tooltip"))
        self.nogui_toggle = ToggleSwitch()
        self.nogui_toggle.setChecked(True)
        self.nogui_toggle.toggled.connect(self._on_nogui_changed)
        nogui_row.addWidget(self.nogui_label, stretch=1)
        nogui_row.addWidget(self.nogui_toggle)
        layout.addLayout(nogui_row)

        layout.addWidget(self._make_separator())

        # カスタムJVMフラグ
        custom_row = QHBoxLayout()
        self.custom_checkbox = QCheckBox(lang.get("ui.jvm.custom_flag"))
        self.custom_checkbox.setToolTip(lang.get("ui.jvm.custom_flag.tooltip"))
        self.custom_checkbox.setStyleSheet(STYLE_CHECKBOX)
        self.custom_checkbox.toggled.connect(self._on_custom_flags_toggled)
        custom_row.addWidget(self.custom_checkbox)
        custom_row.addStretch()
        layout.addLayout(custom_row)

        self.bat_label = QLabel(lang.get("ui.jvm.bat_preview"))
        self.bat_label.setStyleSheet(STYLE_LABEL_BAT_PREVIEW)
        layout.addWidget(self.bat_label)

        self.bat_editor = QTextEdit()
        self.bat_editor.setReadOnly(True)
        self.bat_editor.setFixedHeight(100)
        self._refresh_bat_style(editable=False)
        self.bat_editor.textChanged.connect(self._on_bat_text_changed)
        layout.addWidget(self.bat_editor)

        # 初期化ボタン
        reset_row = QHBoxLayout()
        reset_row.addStretch()
        self.reset_btn = QPushButton(lang.get("ui.jvm.reset"))
        self.reset_btn.setFixedWidth(130)
        self.reset_btn.setStyleSheet(STYLE_BUTTON)
        self.reset_btn.clicked.connect(self._on_reset)
        reset_row.addWidget(self.reset_btn)
        layout.addLayout(reset_row)

        layout.addStretch()

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLE_SEPARATOR)
        return line

    def _refresh_bat_style(self, editable: bool):
        if editable:
            self.bat_editor.setStyleSheet(STYLE_TEXT_EDIT_ACTIVE)
        else:
            self.bat_editor.setStyleSheet(STYLE_TEXT_EDIT_INACTIVE)

    # ── ヘルパー ───────────────────────────────────────

    def _get_bat_path(self) -> str:
        server_dir = self._current_profile.get("server_dir", "")
        exec_file  = self.file_entry.text().strip() or "start.bat"
        if not server_dir:
            return ""
        return os.path.join(server_dir, exec_file)

    def _get_java(self) -> str:
        if self._current_profile.get("custom_java", False):
            return self._current_profile.get("java_path", "").strip() or "java"
        return "java"

    def _get_jar(self) -> str:
        """
        使用するjarのパスまたは名前を返す。
        custom_jar=True → jar_pathのフルパス
        custom_jar=False → server_dir内のjarを検索
        """
        if self._current_profile.get("custom_jar", False):
            return self._current_profile.get("jar_path", "")

        # server_dir内のjarを検索
        server_dir = self._current_profile.get("server_dir", "")
        if server_dir and os.path.isdir(server_dir):
            for f in os.listdir(server_dir):
                if f.endswith(".jar"):
                    return f  # ファイル名のみ返す（cwdがserver_dirになるため）
        return "server.jar"

    # ── UI→JSON→bat の更新 ────────────────────────────

    def _sync(self):
        """
        UIの現在値をJSONに保存してbatを再生成する。
        これが唯一の更新経路。
        """
        if self._updating:
            return

        ram_min = self.ram_slider.low
        ram_max = self.ram_slider.high
        nogui   = self.nogui_toggle.isChecked()

        # JSONに保存
        self._save_field(
            ram_min_mb=ram_min,
            ram_max_mb=ram_max,
            nogui=nogui,
        )

        # batを再生成してプレビューを更新
        bat_path = self._get_bat_path()
        java     = self._get_java()
        jar      = self._get_jar()

        content = generate_bat(
            bat_path=bat_path,
            java=java,
            ram_min_mb=ram_min,
            ram_max_mb=ram_max,
            jar_name=jar,
            nogui=nogui
        )

        self._updating = True
        self.bat_editor.setPlainText(content)
        self._updating = False

    # ── UIイベント ─────────────────────────────────────

    def _on_slider_released(self, event):
        RangeSlider.mouseReleaseEvent(self.ram_slider, event)
        self._sync()

    def _on_nogui_changed(self, _):
        self._sync()

    def _on_exec_file_changed(self):
        exec_file = self.file_entry.text().strip() or "start.bat"
        self._save_field(exec_file=exec_file)
        self._sync()

    def _on_custom_flags_toggled(self, checked: bool):
        self._save_field(custom_flags=checked)
        self._refresh_custom_mode()
        if not checked:
            self._sync()

    def _on_bat_text_changed(self):
        """カスタムモード時のみ保存"""
        if self._updating:
            return
        if self.custom_checkbox.isChecked():
            content = self.bat_editor.toPlainText()
            self._save_field(custom_bat=content)
            # カスタムモードはbatに直接書き込む
            bat_path = self._get_bat_path()
            if bat_path:
                write_bat(bat_path, content)

    def _on_reset(self):
        self._updating = True
        self.ram_slider.low  = 4096
        self.ram_slider.high = 8192
        self.ram_slider.update()
        self.nogui_toggle.blockSignals(True)
        self.nogui_toggle.setChecked(True)
        self.nogui_toggle.blockSignals(False)
        self.custom_checkbox.setChecked(False)
        self._updating = False
        self._sync()

    def _refresh_custom_mode(self):
        enabled = not self.custom_checkbox.isChecked()
        self.ram_slider.setEnabled(enabled)
        self.nogui_toggle.setEnabled(enabled)
        self.nogui_label.setStyleSheet(
            STYLE_LABEL_DISABLED_SMALL if not enabled
            else STYLE_LABEL_PRIMARY_SMALL
        )
        self.bat_editor.setReadOnly(enabled)
        self._refresh_bat_style(editable=not enabled)

        if not enabled:
            custom_bat = self._current_profile.get("custom_bat", "")
            if custom_bat:
                self._updating = True
                self.bat_editor.setPlainText(custom_bat)
                self._updating = False

    # ── 外部通知 ───────────────────────────────────────

    def notify_profile_changed(self):
        """BasicTabから設定変更（jar/java等）を通知される"""
        self._sync()

    # ── プロファイル保存 ───────────────────────────────

    def _save_field(self, **kwargs):
        name = self._current_profile.get("name", "")
        if not name:
            return
        self._current_profile.update(kwargs)
        save_profile_field(name, **kwargs)

    # ── 公開メソッド ───────────────────────────────────

    def set_values(self, profile: dict):
        """プロファイルを読み込んでUIとbatを更新する"""
        self._current_profile = profile
        self._updating = True

        exec_file    = profile.get("exec_file", "start.bat") or "start.bat"
        ram_min      = profile.get("ram_min_mb", 4096)
        ram_max      = profile.get("ram_max_mb", 8192)
        nogui        = profile.get("nogui", True)
        custom_flags = profile.get("custom_flags", False)

        self.file_entry.setText(exec_file)

        self.ram_slider.low  = max(self.ram_slider.min_val, ram_min)
        self.ram_slider.high = min(self.ram_slider.max_val, ram_max)
        self.ram_slider.update()

        self.nogui_toggle.blockSignals(True)
        self.nogui_toggle.setChecked(nogui)
        self.nogui_toggle.blockSignals(False)

        self.custom_checkbox.blockSignals(True)
        self.custom_checkbox.setChecked(custom_flags)
        self.custom_checkbox.blockSignals(False)

        self._updating = False

        self._refresh_custom_mode()

        if custom_flags:
            custom_bat = profile.get("custom_bat", "")
            if custom_bat:
                self._updating = True
                self.bat_editor.setPlainText(custom_bat)
                self._updating = False
        else:
            # JSONの値からbatを再生成してプレビューに表示
            self._sync()

    def get_values(self) -> dict:
        return {
            "exec_file":    self.file_entry.text().strip() or "start.bat",
            "custom_flags": self.custom_checkbox.isChecked(),
            "custom_bat":   self.bat_editor.toPlainText(),
            "ram_min_mb":   self.ram_slider.low,
            "ram_max_mb":   self.ram_slider.high,
            "nogui":        self.nogui_toggle.isChecked(),
        }
