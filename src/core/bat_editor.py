import os
import re


def read_bat(bat_path: str) -> str:
    if not os.path.exists(bat_path):
        return ""
    with open(bat_path, encoding="utf-8", errors="replace") as f:
        return f.read()


def write_bat(bat_path: str, content: str) -> None:
    os.makedirs(os.path.dirname(bat_path), exist_ok=True)
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_bat(bat_path: str, java: str, ram_min_mb: int, ram_max_mb: int,
                 jar_name: str, nogui: bool) -> str:
    """Generate and write a bat file from profile settings, then return it."""
    # Quote the Java path when it contains spaces
    java_str = f'"{java}"' if " " in java else java
    # Quote the jar path when it contains spaces
    jar_str  = f'"{jar_name}"' if " " in jar_name else jar_name
    nogui_str = " nogui" if nogui else ""

    content = (
        f"@echo off\n"
        f"{java_str} -Xms{ram_min_mb}M -Xmx{ram_max_mb}M"
        f" -jar {jar_str}{nogui_str}\n"
    )
    if bat_path:
        write_bat(bat_path, content)
    return content
