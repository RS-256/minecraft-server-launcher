import sys
from PyQt6.QtWidgets import QApplication
from core.config_manager import load_config
from core.profile_manager import ensure_profile_default, get_profiles_config_dir
from core.lang import lang
from ui.app_window import AppWindow
from ui.cursors import install_clickable_cursor_filter


def main():
    # Initialize required directories and files
    get_profiles_config_dir()
    ensure_profile_default()

    config = load_config()
    lang.load(config["language"])

    app = QApplication(sys.argv)
    install_clickable_cursor_filter(app)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
