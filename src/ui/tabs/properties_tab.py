import os
from html import escape
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QComboBox, QFrame, QTextEdit, QStackedWidget,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from ui.theme import (
    STYLE_BUTTON, STYLE_CHECKBOX, STYLE_COMBO,
    STYLE_INPUT, FONT_SIZE_DEFAULT,
    STYLE_SCROLL_AREA_THIN, STYLE_TRANSPARENT_BG,
    STYLE_RAW_EDITOR, STYLE_BOTTOM_ACTION_BAR,
    STYLE_SEPARATOR_SUBTLE, STYLE_LABEL_SECONDARY_SMALL,
    STYLE_LABEL_PLACEHOLDER, COLOR_TEXT_PRIMARY
)
from ui.widgets.toggle_switch import ToggleSwitch
from core.lang import lang
from core.properties_parser import (
    read_properties, write_properties,
    read_raw, write_raw,
    get_property_meta, PRIORITY_KEYS
)


PROPERTY_LABEL_WIDTH = 180
PROPERTY_VALUE_MIN_WIDTH = 160
PROPERTY_VALUE_MAX_WIDTH = 240
PROPERTY_SCROLL_RIGHT_PADDING = 18
PROPERTY_HIGHLIGHT_STYLE = "background-color: #dfff3f; color: #111111;"


class _NoWheelComboBox(QComboBox):
    """Combo box that ignores mouse-wheel changes while closed."""

    def wheelEvent(self, event):
        if self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()


class _PropRow(QWidget):
    """Row widget for one property."""
    def __init__(self, key: str, value: str, parent=None):
        super().__init__(parent)
        self._key  = key
        self._meta = get_property_meta(key)
        self._key_label: QLabel | None = None
        self._build(value)

    def _build(self, value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # Key label
        key_label = QLabel(self._key)
        key_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL
        )
        key_label.setFixedWidth(PROPERTY_LABEL_WIDTH)
        key_label.setToolTip(self._key)
        key_label.setTextFormat(Qt.TextFormat.RichText)
        self._key_label = key_label
        layout.addWidget(key_label)

        # Value widget
        self._widget = self._make_widget(value)
        self._apply_value_widget_layout(self._widget)
        layout.addStretch(1)
        layout.addWidget(self._widget, 0, Qt.AlignmentFlag.AlignRight)

    def _apply_value_widget_layout(self, widget: QWidget):
        if isinstance(widget, (QLineEdit, QComboBox)):
            widget.setMinimumWidth(PROPERTY_VALUE_MIN_WIDTH)
            widget.setMaximumWidth(PROPERTY_VALUE_MAX_WIDTH)
            widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )

    def _make_widget(self, value: str) -> QWidget:
        t = self._meta["type"]

        if t == "bool":
            toggle = ToggleSwitch()
            toggle.setChecked(value.lower() == "true")
            return toggle

        elif t == "combo":
            combo = _NoWheelComboBox()
            combo.setStyleSheet(STYLE_COMBO)
            for c in self._meta.get("choices", []):
                combo.addItem(c)
            idx = combo.findText(value)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            return combo

        elif t == "int":
            entry = QLineEdit(value)
            entry.setStyleSheet(STYLE_INPUT)
            mn = self._meta.get("min", 0)
            mx = self._meta.get("max", 99999999)
            entry.setValidator(QIntValidator(mn, mx))
            entry.setPlaceholderText(str(self._meta.get("default", "")))
            return entry

        else:  # str + unknown
            entry = QLineEdit(value)
            entry.setStyleSheet(STYLE_INPUT)
            entry.setPlaceholderText(str(self._meta.get("default", "")))
            return entry

    def set_search_query(self, query: str):
        if self._key_label is None:
            return

        if not query:
            self._key_label.setText(escape(self._key))
            return

        key_lower = self._key.lower()
        query_lower = query.lower()
        query_len = len(query)
        parts = []
        pos = 0

        while True:
            idx = key_lower.find(query_lower, pos)
            if idx < 0:
                parts.append(escape(self._key[pos:]))
                break

            parts.append(escape(self._key[pos:idx]))
            matched = escape(self._key[idx:idx + query_len])
            parts.append(
                f'<span style="{PROPERTY_HIGHLIGHT_STYLE}">{matched}</span>'
            )
            pos = idx + query_len

        self._key_label.setText("".join(parts))

    def get_value(self) -> str:
        """Return the current value as a string."""
        t = self._meta["type"]
        if t == "bool":
            return "true" if self._widget.isChecked() else "false"
        elif t == "combo":
            return self._widget.currentText()
        else:
            return self._widget.text().strip()


class PropertiesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_profile: dict = {}
        self._prop_rows: dict[str, _PropRow] = {}
        self._custom_mode = False
        self._search_text = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main stack: no file, normal mode, or custom mode
        self._main_stack = QStackedWidget()

        # index 0: no-file placeholder
        placeholder = self._build_placeholder()
        self._main_stack.addWidget(placeholder)

        # index 1: normal mode
        self._normal_widget = self._build_normal()
        self._main_stack.addWidget(self._normal_widget)

        # index 2: custom mode
        self._custom_widget = self._build_custom()
        self._main_stack.addWidget(self._custom_widget)

        layout.addWidget(self._main_stack, stretch=1)

        # Fixed bottom bar
        self._bottom_bar = self._build_bottom_bar()
        layout.addWidget(self._bottom_bar)

        self._main_stack.setCurrentIndex(0)
        self._bottom_bar.hide()

    def _build_placeholder(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("📄")
        icon.setStyleSheet(f"font-size: 48px; {STYLE_TRANSPARENT_BG}")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(lang.get("ui.properties.no_file.message"))
        msg.setStyleSheet(STYLE_LABEL_PLACEHOLDER)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)
        return w

    def _build_normal(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        search_row = QWidget()
        search_layout = QHBoxLayout(search_row)
        search_layout.setContentsMargins(12, 12, 12, 6)
        search_layout.setSpacing(0)

        self._search_entry = QLineEdit()
        self._search_entry.setStyleSheet(STYLE_INPUT)
        self._search_entry.setPlaceholderText(
            lang.get("ui.properties.search.placeholder")
        )
        self._search_entry.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_entry)
        layout.addWidget(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(STYLE_SCROLL_AREA_THIN)

        self._scroll_inner = QWidget()
        self._scroll_inner.setStyleSheet(STYLE_TRANSPARENT_BG)
        self._inner_layout = QVBoxLayout(self._scroll_inner)
        self._inner_layout.setContentsMargins(
            12, 12, PROPERTY_SCROLL_RIGHT_PADDING, 12
        )
        self._inner_layout.setSpacing(4)
        self._inner_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._scroll_inner)
        layout.addWidget(scroll)
        return w

    def _build_custom(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 0)
        layout.setSpacing(0)

        self._raw_editor = QTextEdit()
        self._raw_editor.setStyleSheet(STYLE_RAW_EDITOR)
        layout.addWidget(self._raw_editor)
        return w

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(STYLE_BOTTOM_ACTION_BAR)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(8)

        # Custom mode checkbox
        self._custom_checkbox = QCheckBox(lang.get("ui.properties.custom_mode"))
        self._custom_checkbox.setToolTip(lang.get("ui.properties.custom_mode.tooltip"))
        self._custom_checkbox.setStyleSheet(STYLE_CHECKBOX)
        self._custom_checkbox.toggled.connect(self._on_custom_toggled)
        layout.addWidget(self._custom_checkbox)

        layout.addStretch()

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            STYLE_LABEL_SECONDARY_SMALL +
            "border: none;"
        )
        layout.addWidget(self._status_label)

        # Reload button
        reload_btn = QPushButton(lang.get("ui.properties.reload"))
        reload_btn.setStyleSheet(STYLE_BUTTON)
        reload_btn.setFixedWidth(90)
        reload_btn.clicked.connect(self._on_reload)
        layout.addWidget(reload_btn)

        # Save button
        save_btn = QPushButton(lang.get("ui.properties.save"))
        save_btn.setStyleSheet(STYLE_BUTTON)
        save_btn.setFixedWidth(70)
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        return bar

    # Property row construction

    def _build_prop_rows(self, props: dict[str, str]):
        """Build UI rows from loaded properties."""
        # Clear existing widgets
        while self._inner_layout.count():
            item = self._inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._prop_rows.clear()

        # Priority properties section
        priority_shown = []
        for key in PRIORITY_KEYS:
            if key in props:
                priority_shown.append(key)

        if priority_shown:
            self._add_section_label(lang.get("ui.properties.section.priority"))
            for key in priority_shown:
                row = _PropRow(key, props[key])
                row.set_search_query(self._search_text)
                self._prop_rows[key] = row
                self._inner_layout.addWidget(row)
            self._inner_layout.addWidget(self._make_separator())

        # Other properties section
        other_keys = [k for k in props if k not in PRIORITY_KEYS]
        if other_keys:
            self._add_section_label(lang.get("ui.properties.section.other"))
            for key in sorted(other_keys):
                row = _PropRow(key, props[key])
                row.set_search_query(self._search_text)
                self._prop_rows[key] = row
                self._inner_layout.addWidget(row)

        self._inner_layout.addStretch()

    def _add_section_label(self, text: str):
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: {FONT_SIZE_DEFAULT}px;
            font-weight: bold;
            padding: 8px 0 4px 0;
            background: transparent;
        """)
        self._inner_layout.addWidget(label)

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(STYLE_SEPARATOR_SUBTLE)
        return line

    # Events

    def _on_custom_toggled(self, checked: bool):
        self._custom_mode = checked
        if checked:
            # Reflect current normal-mode values into raw text
            raw = self._collect_as_raw()
            self._raw_editor.setPlainText(raw)
            self._main_stack.setCurrentIndex(2)
        else:
            self._main_stack.setCurrentIndex(1)

    def _on_reload(self):
        self.load_properties(self._current_profile)

    def _on_search_changed(self, text: str):
        self._search_text = text.strip()
        for row in self._prop_rows.values():
            row.set_search_query(self._search_text)

    def _on_save(self):
        path = self._get_properties_path()
        if not path:
            return
        try:
            if self._custom_mode:
                write_raw(path, self._raw_editor.toPlainText())
            else:
                props = self._collect_props()
                write_properties(path, props)
            self._status_label.setText(lang.get("ui.properties.saved"))
        except Exception as e:
            self._status_label.setText(
                lang.get("ui.properties.save_failed").format(e)
            )

    # Helpers

    def _get_properties_path(self) -> str:
        server_dir = self._current_profile.get("server_dir", "")
        if not server_dir:
            return ""
        return os.path.join(server_dir, "server.properties")

    def _collect_props(self) -> dict[str, str]:
        """Collect all properties from the UI and return them as a dict."""
        return {key: row.get_value() for key, row in self._prop_rows.items()}

    def _collect_as_raw(self) -> str:
        """Collect values from the UI and convert them to raw text."""
        props = self._collect_props()
        lines = ["# Minecraft server properties"]
        for k, v in props.items():
            lines.append(f"{k}={v}")
        return "\n".join(lines) + "\n"

    # Public methods

    def load_properties(self, profile: dict):
        self._current_profile = profile
        path = self._get_properties_path()

        if not path or not os.path.exists(path):
            self._main_stack.setCurrentIndex(0)  # No file
            self._bottom_bar.hide()
            return

        self._bottom_bar.show()
        props = read_properties(path)

        if self._custom_mode:
            self._raw_editor.setPlainText(read_raw(path))
            self._main_stack.setCurrentIndex(2)
        else:
            self._build_prop_rows(props)
            self._main_stack.setCurrentIndex(1)

        self._status_label.setText("")

    def set_values(self, profile: dict):
        self._current_profile = profile
        self.load_properties(profile)
