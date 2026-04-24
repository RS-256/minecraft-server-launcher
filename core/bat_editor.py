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
    """プロファイルの設定からbatを生成して書き込む。生成内容を返す。"""
    # javaパスにスペースが含まれる場合は引用符で囲む
    java_str = f'"{java}"' if " " in java else java
    # jarパスにスペースが含まれる場合は引用符で囲む
    jar_str  = f'"{jar_name}"' if " " in jar_name else jar_name
    nogui_str = " nogui" if nogui else ""

    content = (
        f"@echo off\n"
        f"{java_str} -Xms{ram_min_mb}M -Xmx{ram_max_mb}M"
        f" -jar {jar_str}{nogui_str}\n"
        f"pause\n"
    )
    if bat_path:
        write_bat(bat_path, content)
    return content