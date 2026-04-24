import sys
from PyQt6.QtWidgets import QApplication
from core.config_manager import load_config
from core.profile_manager import ensure_profile_default, get_profiles_config_dir
from core.lang import lang
from ui.app_window import AppWindow


def main():
    # 必要なディレクトリ・ファイルを初期化
    get_profiles_config_dir()
    ensure_profile_default()

    config = load_config()
    lang.load(config["language"])

    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()