import os
import sys
import json
import re


def get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def get_config_dir() -> str:
    path = os.path.join(get_base_dir(), "config")
    os.makedirs(path, exist_ok=True)
    return path


def get_profiles_config_dir() -> str:
    path = os.path.join(get_config_dir(), "profiles")
    os.makedirs(path, exist_ok=True)
    return path


def get_assets_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return get_base_dir()


def get_server_profiles_dir() -> str:
    """Directory that stores server files under profiles/."""
    path = os.path.join(get_base_dir(), "profiles")
    os.makedirs(path, exist_ok=True)
    return path


# Default settings

PROFILE_DEFAULTS = {
    "name": "",
    "server_dir": "",
    "exec_file": "start.bat",
    "custom_flags": False,
    "custom_bat": "",
    "custom_jar": False,
    "jar_path": "",
    "custom_java": False,
    "java_path": "",
    "brand": "vanilla",
    "version": "1.21.1",
    "loader_version": "",
    "ram_min_mb": 4096,
    "ram_max_mb": 8192,
    "nogui": True
}

_PROFILES_INDEX_PATH = os.path.join(get_config_dir(), "profiles.json")
_PROFILE_DEFAULT_PATH = os.path.join(get_config_dir(), "profile_default.json")

_PROFILES_INDEX_DEFAULTS = {
    "profiles": [],
    "last_used": None
}


# profile_default.json

def ensure_profile_default() -> None:
    """Create profile_default.json if it does not exist."""
    if not os.path.exists(_PROFILE_DEFAULT_PATH):
        _write_json(_PROFILE_DEFAULT_PATH, PROFILE_DEFAULTS)


# profiles.json index

def load_profiles_index() -> dict:
    if not os.path.exists(_PROFILES_INDEX_PATH):
        _write_json(_PROFILES_INDEX_PATH, _PROFILES_INDEX_DEFAULTS)
        return _PROFILES_INDEX_DEFAULTS.copy()
    return _read_json(_PROFILES_INDEX_PATH)


def save_profiles_index(index: dict) -> None:
    _write_json(_PROFILES_INDEX_PATH, index)


# Individual profiles

def load_profile(config_path: str) -> dict:
    """Load a profile and fill missing keys with default values."""
    abs_path = os.path.join(get_base_dir(), config_path)
    if not os.path.exists(abs_path):
        return PROFILE_DEFAULTS.copy()
    data = _read_json(abs_path)
    for key, value in PROFILE_DEFAULTS.items():
        if key not in data:
            data[key] = value
    return data


def save_profile(config_path: str, profile: dict) -> None:
    abs_path = os.path.join(get_base_dir(), config_path)
    _write_json(abs_path, profile)


def create_profile(name: str) -> str:
    """
    Create a new profile and return its config_path.
    Also append it to profiles.json.
    """
    safe_name = _to_safe_filename(name)
    config_path = f"config/profiles/{safe_name}.json"
    abs_path = os.path.join(get_base_dir(), config_path)

    profile = PROFILE_DEFAULTS.copy()
    profile["name"] = name
    _write_json(abs_path, profile)

    index = load_profiles_index()
    index["profiles"].append({
        "name": name,
        "config_path": config_path
    })
    if index["last_used"] is None:
        index["last_used"] = name
    save_profiles_index(index)

    return config_path


def delete_profile(name: str) -> None:
    """Remove a profile from the index and delete its JSON file."""
    index = load_profiles_index()
    entry = next((p for p in index["profiles"] if p["name"] == name), None)
    if entry is None:
        return
    abs_path = os.path.join(get_base_dir(), entry["config_path"])
    if os.path.exists(abs_path):
        os.remove(abs_path)
    index["profiles"] = [p for p in index["profiles"] if p["name"] != name]
    if index["last_used"] == name:
        index["last_used"] = index["profiles"][0]["name"] if index["profiles"] else None
    save_profiles_index(index)


def get_all_profiles() -> list[dict]:
    """Load and return all profiles."""
    index = load_profiles_index()
    result = []
    for entry in index["profiles"]:
        profile = load_profile(entry["config_path"])
        profile["_config_path"] = entry["config_path"]
        result.append(profile)
    return result


def get_last_used_profile() -> dict | None:
    """Return the most recently used profile."""
    index = load_profiles_index()
    last = index.get("last_used")
    if not last:
        return None
    entry = next((p for p in index["profiles"] if p["name"] == last), None)
    if not entry:
        return None
    return load_profile(entry["config_path"])


def set_last_used(name: str) -> None:
    index = load_profiles_index()
    index["last_used"] = name
    save_profiles_index(index)


# Utilities

def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _to_safe_filename(name: str) -> str:
    """Convert a profile name to a safe filename."""
    safe = re.sub(r'[\\/*?:"<>|]', "_", name)
    safe = safe.strip().replace(" ", "_").lower()
    return safe or "profile"

def rename_profile(old_name: str, new_name: str) -> bool:
    """Rename a profile and return True on success."""
    index = load_profiles_index()
    entry = next((p for p in index["profiles"] if p["name"] == old_name), None)
    if not entry:
        return False

    # Check for duplicate names
    if any(p["name"] == new_name for p in index["profiles"]):
        return False

    profile = load_profile(entry["config_path"])
    profile["name"] = new_name

    # Save with the new filename
    new_safe = _to_safe_filename(new_name)
    new_config_path = f"config/profiles/{new_safe}.json"
    new_abs = os.path.join(get_base_dir(), new_config_path)

    # Delete the old file and save to the new path
    old_abs = os.path.join(get_base_dir(), entry["config_path"])
    if os.path.exists(old_abs):
        os.remove(old_abs)

    save_profile(new_config_path, profile)

    # Update the index
    entry["name"]        = new_name
    entry["config_path"] = new_config_path

    if index.get("last_used") == old_name:
        index["last_used"] = new_name

    save_profiles_index(index)
    return True
