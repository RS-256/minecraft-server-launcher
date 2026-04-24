import urllib.request
import json
import re
from PyQt6.QtCore import QThread, pyqtSignal


VANILLA_MANIFEST_URL  = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
FABRIC_GAME_URL       = "https://meta.fabricmc.net/v2/versions/game"
FABRIC_LOADER_URL     = "https://meta.fabricmc.net/v2/versions/loader/{mc_version}"
NEOFORGE_VERSIONS_URL = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"

VERSION_TYPE_MAP = {
    "release":  "release",
    "snapshot": "snapshot",
    "old_beta": "beta",
    "old_alpha": "alpha",
}


class VanillaVersionFetcher(QThread):
    finished = pyqtSignal(list)
    failed   = pyqtSignal(str)

    def run(self):
        try:
            with urllib.request.urlopen(VANILLA_MANIFEST_URL, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            versions = []
            for v in data.get("versions", []):
                category = VERSION_TYPE_MAP.get(v.get("type", ""), None)
                if category is None:
                    continue
                versions.append({
                    "id":           v["id"],
                    "type":         category,
                    "release_time": v.get("releaseTime", ""),
                })

            versions.sort(key=lambda x: x["release_time"], reverse=True)
            self.finished.emit(versions)

        except Exception as e:
            self.failed.emit(str(e))


class FabricVersionFetcher(QThread):
    finished = pyqtSignal(list)
    failed   = pyqtSignal(str)

    def run(self):
        try:
            with urllib.request.urlopen(FABRIC_GAME_URL, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            versions = []
            for v in data:
                category = "release" if v.get("stable", False) else "snapshot"
                versions.append({
                    "id":           v["version"],
                    "type":         category,
                    "release_time": "",
                })

            self.finished.emit(versions)

        except Exception as e:
            self.failed.emit(str(e))


class FabricLoaderFetcher(QThread):
    """特定MCバージョン向けのFabric Loaderバージョン一覧を取得する"""
    finished = pyqtSignal(list)   # [{"id": "0.16.5", "stable": True}, ...]
    failed   = pyqtSignal(str)

    def __init__(self, mc_version: str, parent=None):
        super().__init__(parent)
        self._mc_version = mc_version

    def run(self):
        try:
            url = FABRIC_LOADER_URL.format(mc_version=self._mc_version)
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            versions = []
            for entry in data:
                loader = entry.get("loader", {})
                versions.append({
                    "id":     loader.get("version", ""),
                    "stable": loader.get("stable", False),
                })

            self.finished.emit(versions)

        except Exception as e:
            self.failed.emit(str(e))


class NeoForgeVersionFetcher(QThread):
    finished = pyqtSignal(dict)
    failed   = pyqtSignal(str)

    def run(self):
        try:
            with urllib.request.urlopen(NEOFORGE_VERSIONS_URL, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            raw_versions = data.get("versions", [])
            mc_map: dict[str, list] = {}

            for raw in raw_versions:
                mc_ver, mc_type = self._extract_mc_info(raw)
                if not mc_ver:
                    continue

                # NeoForge自身のカテゴリ
                if "+snapshot" in raw:
                    nf_category = "snapshot"
                elif "alpha" in raw.split("+")[0]:
                    nf_category = "alpha"
                elif "beta" in raw.split("+")[0]:
                    nf_category = "beta"
                else:
                    nf_category = "release"

                if mc_ver not in mc_map:
                    mc_map[mc_ver] = []
                mc_map[mc_ver].append({
                    "id":      raw,
                    "type":    nf_category,
                    "mc_type": mc_type,  # MCバージョン自体のタイプ
                })

            for mc_ver in mc_map:
                mc_map[mc_ver].reverse()

            reversed_map = dict(reversed(list(mc_map.items())))
            self.finished.emit(reversed_map)

        except Exception as e:
            self.failed.emit(str(e))

    def _extract_mc_info(self, neoforge_ver: str) -> tuple[str, str]:
        """
        NeoForgeバージョン文字列からMCバージョンとMCのタイプを返す。
        戻り値: (mc_version, mc_type)
        mc_type: "release" | "snapshot"

        例:
          "21.1.226"                        → ("1.21.1", "release")
          "26.1.0.0-alpha.1+snapshot-1"     → ("26.1 snapshot-1", "snapshot")
          "26.1.0.1-beta"                   → ("26.1.0", "release")
          "26.1.2.7-beta"                   → ("26.1.2", "release")
        """
        mc_type = "release"

        # +snapshot-X を含む場合はMC側がsnapshot
        if "+snapshot" in neoforge_ver:
            snapshot_part = neoforge_ver.split("+snapshot")[1]  # "-1" など
            clean = neoforge_ver.split("+")[0]  # "26.1.0.0-alpha.1"
            clean = re.split(r"-", clean)[0]    # "26.1.0.0"
            parts = clean.split(".")
            if len(parts) >= 2:
                mc_ver = f"{parts[0]}.{parts[1]} snapshot{snapshot_part}"
            else:
                mc_ver = clean
            mc_type = "snapshot"
            return mc_ver, mc_type

        # 通常処理
        clean = re.split(r"[-+]", neoforge_ver)[0]
        parts = clean.split(".")
        if len(parts) < 2:
            return "", "release"

        try:
            major_int = int(parts[0])
        except ValueError:
            return "", "release"

        if major_int >= 26 and len(parts) >= 4:
            mc_ver = f"{parts[0]}.{parts[1]}.{parts[2]}"
        elif major_int >= 26 and len(parts) == 3:
            mc_ver = f"{parts[0]}.{parts[1]}.{parts[2]}"
        else:
            minor = parts[1]
            mc_ver = f"1.{major_int}" if minor == "0" else f"1.{major_int}.{minor}"

        return mc_ver, mc_type