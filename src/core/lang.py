import json
import os
from core.profile_manager import get_assets_dir


class LangManager:
    def __init__(self):
        self._strings: dict = {}
        self._current: str = "en_us"

    def load(self, lang_code: str) -> None:
        path = os.path.join(get_assets_dir(), "assets", "lang", f"{lang_code}.json")
        if not os.path.exists(path):
            print(f"[Lang] {lang_code}.json not found, falling back to en_us")
            lang_code = "en_us"
            path = os.path.join(get_assets_dir(), "assets", "lang", "en_us.json")
        with open(path, encoding="utf-8") as f:
            self._strings = json.load(f)
        self._current = lang_code

    def get(self, key: str) -> str:
        return self._strings.get(key, key)

    @property
    def current(self) -> str:
        return self._current


lang = LangManager()