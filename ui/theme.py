from pathlib import Path

# ---------------------------------------------------

# 背景色
COLOR_BG_PRIMARY        = "rgb(30, 30, 30)"
COLOR_BG_SECONDARY      = "rgb(37, 37, 37)"
COLOR_BG_TERTIARY       = "rgb(43, 43, 43)"
COLOR_BG_DEEP           = "rgb(26, 26, 26)"

# アクセント
COLOR_ACCENT            = "rgb(31, 106, 165)"
COLOR_ACCENT_HOVER      = "rgb(40, 120, 184)"

# テキスト
COLOR_TEXT_PRIMARY      = "rgb(204, 204, 204)"
COLOR_TEXT_BRIGHT       = "rgb(220, 220, 220)"
COLOR_TEXT_SECONDARY    = "rgb(170, 170, 170)"
COLOR_TEXT_MUTED        = "rgb(102, 102, 102)"
COLOR_TEXT_DIM          = "rgb(90, 90, 90)"
COLOR_TEXT_DISABLED     = "rgb(136, 136, 136)"

# ボーダー
COLOR_BORDER            = "rgb(58, 58, 58)"
COLOR_BORDER_STRONG     = "rgb(51, 51, 51)"

# 状態色
COLOR_SUCCESS           = "rgb(46, 125, 50)"
COLOR_SUCCESS_HOVER     = "rgb(56, 142, 60)"
COLOR_DANGER            = "rgb(198, 40, 40)"
COLOR_DANGER_HOVER      = "rgb(211, 47, 47)"
COLOR_DANGER_BRIGHT     = "rgb(239, 83, 80)"
COLOR_DANGER_STRONG     = "rgb(216, 0, 0)"
COLOR_WARNING           = "rgb(255, 183, 77)"
COLOR_DISABLED          = "rgb(68, 68, 68)"

# トグルスイッチ
COLOR_TOGGLE_ON_BG      = "rgba(76, 175, 80, 255)"
COLOR_TOGGLE_OFF_BG     = "rgba(80, 80, 80, 255)"
COLOR_TOGGLE_HANDLE     = "rgba(255, 255, 255, 255)"

# オーバーレイ
COLOR_OVERLAY_BG        = "rgba(0, 0, 0, 100)"    # 半透明グレー
COLOR_OVERLAY_MENU_BG   = "rgb(37, 37, 37)"        # メニュー背景（不透明）

# サイズ
FONT_SIZE_DEFAULT       = 13
FONT_SIZE_SMALL         = 11
FONT_SIZE_LARGE         = 16
FONT_SIZE_DEFAULT_PT    = 10
RADIUS_DEFAULT          = 6
MENU_WIDTH              = 220

ASSETS_DIR              = Path(__file__).resolve().parent.parent / "assets"
ICON_CHECK              = (ASSETS_DIR / "icons" / "check_white.svg").as_posix()

# ---------------------------------------------------

STYLE_WINDOW = f"""
    QMainWindow {{ background-color: {COLOR_BG_PRIMARY}; }}
    QWidget {{ color: {COLOR_TEXT_PRIMARY}; }}
"""

STYLE_LABEL = f"""
    QLabel {{
        font-size: {FONT_SIZE_DEFAULT}px;
        color: {COLOR_TEXT_PRIMARY};
    }}
"""

STYLE_INPUT = f"""
    QLineEdit {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
"""

STYLE_INPUT_DISABLED = f"""
    QLineEdit {{
        background-color: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_DIM};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
"""

STYLE_INPUT_ERROR = f"""
    QLineEdit {{ border: 1px solid {COLOR_DANGER}; }}
"""

STYLE_BUTTON = f"""
    QPushButton {{
        background-color: {COLOR_ACCENT};
        color: white;
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
    QPushButton:disabled {{
        background-color: {COLOR_DISABLED};
        color: {COLOR_TEXT_DISABLED};
    }}
"""

STYLE_BUTTON_TRANSPARENT = f"""
    QPushButton {{
        background: transparent;
        color: {COLOR_TEXT_PRIMARY};
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_BG_SECONDARY}; }}
"""

STYLE_BUTTON_SUCCESS = f"""
    QPushButton {{
        background-color: {COLOR_SUCCESS};
        color: white;
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_SUCCESS_HOVER}; }}
    QPushButton:disabled {{
        background-color: {COLOR_DISABLED};
        color: {COLOR_TEXT_DISABLED};
    }}
"""

STYLE_BUTTON_DANGER = f"""
    QPushButton {{
        background-color: {COLOR_DANGER};
        color: white;
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_DANGER_HOVER}; }}
    QPushButton:disabled {{
        background-color: {COLOR_DISABLED};
        color: {COLOR_TEXT_DISABLED};
    }}
"""

STYLE_BUTTON_DARK = f"""
    QPushButton {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px;
        font-size: 12px;
    }}
    QPushButton:hover {{ background-color: rgb(74, 74, 74); }}
"""

STYLE_BUTTON_DANGER_CONFIRM = f"""
    QPushButton {{
        background-color: {COLOR_DANGER_STRONG};
        color: white;
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_DANGER_HOVER}; }}
"""

STYLE_BUTTON_DANGER_CONFIRM_DISABLED = f"""
    QPushButton {{
        background-color: {COLOR_DISABLED};
        color: rgb(120, 120, 120);
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
"""


def style_delete_confirm_button(enabled: bool) -> str:
    return STYLE_BUTTON_DANGER_CONFIRM if enabled else STYLE_BUTTON_DANGER_CONFIRM_DISABLED

STYLE_COMBO = f"""
    QComboBox {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px;
        font-size: {FONT_SIZE_DEFAULT_PT}pt;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        outline: none;
        font-size: {FONT_SIZE_DEFAULT_PT}pt;
        selection-background-color: {COLOR_ACCENT};
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 24px;
        padding: 4px 8px;
    }}
"""

STYLE_LOGBOX = f"""
    QTextEdit {{
        background-color: {COLOR_BG_DEEP};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_DEFAULT}px;
        font-family: monospace;
        font-size: 12px;
    }}
"""

STYLE_TEXT_EDIT_ACTIVE = f"""
    QTextEdit {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_ACCENT};
        border-radius: {RADIUS_DEFAULT}px;
        font-family: monospace;
        font-size: 12px;
        padding: 4px;
    }}
"""

STYLE_TEXT_EDIT_INACTIVE = f"""
    QTextEdit {{
        background-color: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_SECONDARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        font-family: monospace;
        font-size: 12px;
        padding: 4px;
    }}
"""

STYLE_RAW_EDITOR = f"""
    QTextEdit {{
        background-color: {COLOR_BG_DEEP};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        font-family: monospace;
        font-size: 12px;
        padding: 6px;
    }}
"""

STYLE_BOTTOM_BAR = f"""
    QFrame {{
        background-color: {COLOR_BG_DEEP};
        border-top: 1px solid {COLOR_BORDER_STRONG};
    }}
"""

STYLE_BOTTOM_ACTION_BAR = f"""
    border-top: 1px solid {COLOR_BORDER};
    background-color: {COLOR_BG_PRIMARY};
"""

STYLE_OVERLAY_MENU = f"""
    QPushButton {{
        background: transparent;
        color: {COLOR_TEXT_PRIMARY};
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_BG_SECONDARY}; }}
    QLabel {{ color: {COLOR_TEXT_SECONDARY}; }}
"""

# タブ
COLOR_TAB_ACTIVE        = "rgb(31, 106, 165)"
COLOR_TAB_INACTIVE      = "rgb(43, 43, 43)"
COLOR_TAB_HOVER         = "rgb(55, 55, 55)"

# ステータスインジケーター
COLOR_STATUS_ONLINE     = "rgba(76, 175, 80, 255)"
COLOR_STATUS_OFFLINE    = "rgb(120, 120, 120)"

# カード・セクション
COLOR_CARD_BG           = "rgb(37, 37, 37)"
COLOR_CARD_BORDER       = "rgb(55, 55, 55)"

STYLE_TAB_BUTTON_ACTIVE = f"""
    QPushButton {{
        background-color: {COLOR_TAB_ACTIVE};
        color: white;
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
"""

STYLE_TAB_BUTTON_INACTIVE = f"""
    QPushButton {{
        background-color: {COLOR_TAB_INACTIVE};
        color: {COLOR_TEXT_SECONDARY};
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px 16px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ background-color: {COLOR_TAB_HOVER}; }}
"""

STYLE_CARD = f"""
    QFrame {{
        background-color: {COLOR_CARD_BG};
        border: 1px solid {COLOR_CARD_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
    }}
"""

STYLE_TOGGLE_ON = f"""
    QPushButton {{
        background-color: {COLOR_STATUS_ONLINE};
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 11px;
        padding: 2px 10px;
    }}
"""

STYLE_TOGGLE_OFF = f"""
    QPushButton {{
        background-color: {COLOR_DISABLED};
        color: {COLOR_TEXT_SECONDARY};
        border: none;
        border-radius: 10px;
        font-size: 11px;
        padding: 2px 10px;
    }}
"""

STYLE_CHECKBOX = f"""
    QCheckBox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_DEFAULT}px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLOR_BORDER};
        border-radius: 3px;
        background-color: {COLOR_BG_TERTIARY};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_ACCENT};
        border-color: {COLOR_ACCENT};
        image: url("{ICON_CHECK}");
    }}
"""

STYLE_CHECKBOX_DANGER = f"""
    QCheckBox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_DEFAULT}px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLOR_DANGER};
        border-radius: 3px;
        background-color: {COLOR_BG_TERTIARY};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_DANGER};
        border-color: {COLOR_DANGER};
        image: url("{ICON_CHECK}");
    }}
    QCheckBox::indicator:hover {{
        border-color: {COLOR_DANGER_HOVER};
    }}
"""

STYLE_CHECKBOX_DISABLED_TEXT = f"""
    QCheckBox {{ color: {COLOR_TEXT_DIM}; }}
"""

STYLE_RANGE_SLIDER_LABEL = f"""
    QLabel {{
        color: {COLOR_TEXT_SECONDARY};
        font-size: {FONT_SIZE_SMALL}px;
    }}
"""

STYLE_COMMAND_INPUT = f"""
    QLineEdit {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 6px 10px;
        font-size: {FONT_SIZE_DEFAULT}px;
        font-family: monospace;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLOR_ACCENT};
    }}
"""

STYLE_LOG_TAB_ACTIVE = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLOR_TEXT_PRIMARY};
        border: none;
        border-bottom: 2px solid {COLOR_ACCENT};
        border-radius: 0px;
        padding: 4px 12px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
"""

STYLE_LOG_TAB_INACTIVE = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLOR_TEXT_MUTED};
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0px;
        padding: 4px 12px;
        font-size: {FONT_SIZE_DEFAULT}px;
    }}
    QPushButton:hover {{ color: {COLOR_TEXT_PRIMARY}; }}
"""

STYLE_ICON_BUTTON = f"""
    QPushButton {{
        background: transparent;
        color: {COLOR_TEXT_SECONDARY};
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 4px;
        font-size: 16px;
    }}
    QPushButton:hover {{ color: {COLOR_TEXT_PRIMARY}; background-color: {COLOR_BG_TERTIARY}; }}
"""

STYLE_COMMAND_FRAME = f"""
    QFrame {{
        border-top: 1px solid {COLOR_BORDER};
        padding-top: 6px;
    }}
"""

STYLE_COLLAPSIBLE_HEADER = f"""
    QPushButton {{
        background: transparent;
        color: {COLOR_TEXT_SECONDARY};
        border: none;
        border-top: 1px solid {COLOR_BORDER};
        padding: 8px 4px;
        font-size: {FONT_SIZE_DEFAULT}px;
        text-align: left;
    }}
    QPushButton:hover {{
        color: {COLOR_TEXT_BRIGHT};
    }}
"""

STYLE_SCROLL_AREA_THIN = """
    QScrollArea { border: none; background: transparent; }
    QScrollBar:vertical {
        background: rgba(255, 255, 255, 18);
        width: 8px;
        border-radius: 4px;
        margin: 2px 0px 2px 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 110);
        border-radius: 4px;
        min-height: 28px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(255, 255, 255, 155);
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical { background: transparent; }
"""

STYLE_SCROLL_AREA_TRANSPARENT = """
    QScrollArea { border: none; background: transparent; }
"""

STYLE_TRANSPARENT_BG = "background: transparent;"

STYLE_PROFILE_HEADER = f"""
    QWidget {{
        background-color: {COLOR_BG_TERTIARY};
        border-radius: {RADIUS_DEFAULT}px;
    }}
"""

STYLE_SEPARATOR = "color: rgba(255, 255, 255, 30);"
STYLE_SEPARATOR_SUBTLE = "color: rgba(255, 255, 255, 20);"
STYLE_SEPARATOR_FAINT = "color: rgba(255, 255, 255, 15);"
STYLE_SEPARATOR_BORDER = f"color: {COLOR_BORDER};"

STYLE_DIALOG_CARD = f"""
    QWidget {{
        background-color: {COLOR_BG_SECONDARY};
        border-radius: {RADIUS_DEFAULT}px;
    }}
"""

STYLE_RENAME_INPUT = f"""
    QLineEdit {{
        background-color: rgb(55, 55, 55);
        color: {COLOR_TEXT_BRIGHT};
        border: 1px solid {COLOR_ACCENT};
        border-radius: 4px;
        padding: 2px 4px;
        font-size: 12px;
    }}
"""

STYLE_LABEL_SECONDARY_SMALL = f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;"
STYLE_LABEL_DISABLED_SMALL = f"color: {COLOR_TEXT_DIM}; font-size: {FONT_SIZE_SMALL}px;"
STYLE_LABEL_PRIMARY_SMALL = f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_SMALL}px;"
STYLE_LABEL_MUTED_SMALL = f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_SMALL}px;"
STYLE_LABEL_DANGER_SMALL = f"color: {COLOR_DANGER}; font-size: {FONT_SIZE_SMALL}px;"
STYLE_LABEL_BAT_PREVIEW = "color: rgba(204, 204, 204, 120); font-size: 11px;"
STYLE_LABEL_PLACEHOLDER = f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SIZE_DEFAULT}px; background: transparent;"
STYLE_STATUS_DOT_OFFLINE = f"color: {COLOR_TOGGLE_OFF_BG}; font-size: 10px; background: transparent;"


def style_status_dot(running: bool) -> str:
    color = COLOR_STATUS_ONLINE if running else COLOR_TOGGLE_OFF_BG
    return f"color: {color}; font-size: 10px; background: transparent;"
