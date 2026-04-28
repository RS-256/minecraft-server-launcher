import urllib.request
import urllib.error
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

VANILLA_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"


class ServerDownloader(QThread):
    """Thread that downloads server jars."""
    progress  = pyqtSignal(int, int)   # (downloaded_bytes, total_bytes)
    finished  = pyqtSignal(str)        # Saved file path.
    failed    = pyqtSignal(str)        # Error message.
    log       = pyqtSignal(str)        # Log message.

    def __init__(self, profile: dict, parent=None):
        super().__init__(parent)
        self._profile = profile

    def run(self):
        brand   = self._profile.get("brand", "vanilla")
        version = self._profile.get("version", "")
        loader  = self._profile.get("loader_version", "")
        dest    = self._profile.get("server_dir", "")

        if not dest:
            self.failed.emit("Server directory is not set.")
            return

        try:
            if brand == "vanilla":
                url, filename = self._get_vanilla_url(version)
            elif brand == "fabric":
                url, filename = self._get_fabric_url(version, loader)
            elif brand == "neoforge":
                url, filename = self._get_neoforge_url(version, loader)
            else:
                self.failed.emit(f"Download not supported for brand: {brand}")
                return

            save_path = self._profile.get("target_jar_path", "").strip()
            if not save_path:
                save_path = os.path.join(dest, filename)
            if not save_path.lower().endswith(".jar"):
                raise ValueError("Download target must be a .jar file.")
            os.makedirs(os.path.dirname(save_path) or dest, exist_ok=True)
            self.log.emit(f"[INFO] Downloading: {filename}")
            self.log.emit(f"[INFO] URL: {url}")
            self._download(url, save_path)
            self.finished.emit(save_path)

        except Exception as e:
            self.failed.emit(str(e))

    def _get_vanilla_url(self, version: str) -> tuple[str, str]:
        self.log.emit(f"[INFO] Fetching version manifest...")
        with urllib.request.urlopen(VANILLA_MANIFEST_URL, timeout=10) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))

        ver_entry = next(
            (v for v in manifest["versions"] if v["id"] == version), None
        )
        if not ver_entry:
            raise ValueError(f"Version {version} not found in manifest.")

        self.log.emit(f"[INFO] Fetching version metadata...")
        with urllib.request.urlopen(ver_entry["url"], timeout=10) as resp:
            ver_data = json.loads(resp.read().decode("utf-8"))

        server_info = ver_data.get("downloads", {}).get("server")
        if not server_info:
            raise ValueError(f"No server download available for {version}.")

        url = server_info["url"]
        filename = f"server-{version}-vanilla.jar"
        return url, filename

    def _get_fabric_url(self, mc_version: str, loader_version: str) -> tuple[str, str]:
        if not loader_version:
            raise ValueError("Fabric loader version is not set.")
        # URL format: /loader/<mc_version>/<loader_version>/<installer_version>/server/jar
        # Use installer_version=0 to request the latest installer
        url = (
            f"https://meta.fabricmc.net/v2/versions/loader/"
            f"{mc_version}/{loader_version}/0/server/jar"
        )
        self.log.emit(f"[INFO] Fabric URL: {url}")

        # Validate the URL before starting the download
        import urllib.request
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    raise ValueError(
                        f"Fabric server jar not available for "
                        f"MC {mc_version} + Loader {loader_version}"
                    )
        except Exception as e:
            raise ValueError(f"Fabric download check failed: {e}")

        filename = f"server-{mc_version}-fabric-{loader_version}.jar"
        return url, filename

    def _get_neoforge_url(self, mc_version: str, neoforge_version: str) -> tuple[str, str]:
        if not neoforge_version:
            raise ValueError("NeoForge version is not set.")
        url = (
            f"https://maven.neoforged.net/releases/net/neoforged/neoforge/"
            f"{neoforge_version}/neoforge-{neoforge_version}-installer.jar"
        )
        filename = f"server-{mc_version}-neoforge-{neoforge_version}-installer.jar"
        return url, filename

    def _download(self, url: str, save_path: str):
        with urllib.request.urlopen(url, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192

            with open(save_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    self.progress.emit(downloaded, total)

