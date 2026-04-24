import os
from core.profile_manager import (
    load_profiles_index, load_profile, save_profile
)


def save_profile_field(profile_name: str, **kwargs) -> None:
    index = load_profiles_index()
    entry = next(
        (p for p in index["profiles"] if p["name"] == profile_name), None
    )
    if not entry:
        return
    profile = load_profile(entry["config_path"])
    for key, value in kwargs.items():
        profile[key] = value
    save_profile(entry["config_path"], profile)


def check_eula(server_dir: str) -> bool:
    """eula.txtが存在してeula=trueが含まれているか確認する"""
    if not server_dir:
        return False
    eula_path = os.path.join(server_dir, "eula.txt")
    if not os.path.exists(eula_path):
        return False
    with open(eula_path, encoding="utf-8", errors="replace") as f:
        return "eula=true" in f.read()