import os
from core.properties_schema import KNOWN_PROPERTIES, PRIORITY_KEYS


def read_properties(path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not os.path.exists(path):
        return result
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
    return result


def write_properties(path: str, props: dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Minecraft server properties\n")
        for key, value in props.items():
            f.write(f"{key}={value}\n")


def read_raw(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def write_raw(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def get_property_meta(key: str) -> dict:
    return KNOWN_PROPERTIES.get(key, {"type": "str", "default": ""})