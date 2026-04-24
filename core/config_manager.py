import json
import os
from core.profile_manager import get_config_dir

_DEFAULTS = {
    "language": "en_us"
}


def _get_path() -> str:
    return os.path.join(get_config_dir(), "app.json")


def load_config() -> dict:
    path = _get_path()
    if not os.path.exists(path):
        save_config(_DEFAULTS)
        return _DEFAULTS.copy()
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    updated = False
    for key, value in _DEFAULTS.items():
        if key not in config:
            config[key] = value
            updated = True
    if updated:
        save_config(config)
    return config


def save_config(config: dict) -> None:
    path = _get_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)