import os
import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal


def _find_jar(profile: dict) -> str | None:
    """
    起動するjarファイルのパスを返す。
    custom_jar=Trueなら jar_path を直接使用。
    そうでなければ server_dir 内をブランドのパターンで検索。
    """
    if profile.get("custom_jar", False):
        jar = profile.get("jar_path", "")
        return jar if jar and os.path.exists(jar) else None

    server_dir = profile.get("server_dir", "")
    if not server_dir or not os.path.isdir(server_dir):
        return None

    brand   = profile.get("brand", "vanilla")
    version = profile.get("version", "")
    loader  = profile.get("loader_version", "")

    # ブランドごとの優先パターン
    patterns = _jar_patterns(brand, version, loader)

    # パターン順に検索
    for pattern in patterns:
        path = os.path.join(server_dir, pattern)
        if os.path.exists(path):
            return path

    # パターンに一致しなければ .jar を全探索して最初のものを返す
    for f in os.listdir(server_dir):
        if f.endswith(".jar"):
            return os.path.join(server_dir, f)

    return None


def _jar_patterns(brand: str, version: str, loader: str) -> list[str]:
    if brand == "vanilla":
        return [
            f"server-{version}-vanilla.jar",
            f"minecraft_server.{version}.jar",
            "server.jar",
        ]
    elif brand == "fabric":
        return [
            f"server-{version}-fabric-{loader}.jar",
            f"fabric-server-mc.{version}-loader.{loader}.jar",
            "fabric-server-launch.jar",
            "server.jar",
        ]
    elif brand == "neoforge":
        return [
            f"server-{version}-neoforge-{loader}-installer.jar",
            f"neoforge-{loader}-installer.jar",
            "server.jar",
        ]
    elif brand in ("spigot", "paper"):
        return [
            f"server-{version}-{brand}.jar",
            f"{brand}-{version}.jar",
            f"{brand}.jar",
            "server.jar",
        ]
    return ["server.jar"]


def _find_java(profile: dict) -> str:
    """
    使用するjavaコマンドを返す。
    1. profile の java_path
    2. フォールバック: "java"
    """
    java_path = profile.get("java_path", "").strip()
    if java_path and os.path.exists(java_path):
        return "\"" + java_path + "\""
    return "java"


def _build_command(profile: dict, jar_path: str) -> list[str]:
    java = _find_java(profile)

    if profile.get("custom_flags", False):
        custom_bat = profile.get("custom_bat", "").strip()
        if custom_bat:
            return custom_bat.split()
        return [java, "-jar", jar_path]

    # custom_jarが指定されている場合はそちらを使う
    if profile.get("custom_jar", False):
        custom_jar_path = profile.get("jar_path", "").strip()
        if custom_jar_path and os.path.exists(custom_jar_path):
            jar_path = custom_jar_path

    ram_min = profile.get("ram_min_mb", 4096)
    ram_max = profile.get("ram_max_mb", 8192)
    nogui   = profile.get("nogui", True)

    cmd = [
        java,
        f"-Xms{ram_min}M",
        f"-Xmx{ram_max}M",
        "-jar", jar_path,
    ]
    if nogui:
        cmd.append("nogui")

    return cmd


class ServerProcess(QThread):
    """サーバープロセスを管理するスレッド"""
    log_received = pyqtSignal(str)   # ログ行を emit
    started_ok   = pyqtSignal()      # 起動成功
    stopped      = pyqtSignal(int)   # 停止（終了コード）
    failed       = pyqtSignal(str)   # 起動失敗

    def __init__(self, profile: dict, parent=None):
        super().__init__(parent)
        self._profile = profile
        self._process: subprocess.Popen | None = None

#    def run(self):
#        jar_path = _find_jar(self._profile)
#        if not jar_path:
#            self.failed.emit("Server jar not found.")
#            return
#
#        server_dir = self._profile.get("server_dir", "")
#        cmd = _build_command(self._profile, jar_path)
#
#        self.log_received.emit(f"[INFO] Starting server...")
#        self.log_received.emit(f"[INFO] Command: {' '.join(cmd)}")
#        self.log_received.emit(f"[INFO] Working directory: {server_dir}")
#
#        try:
#            self._process = subprocess.Popen(
#                cmd,
#                cwd=server_dir,
#                stdout=subprocess.PIPE,
#                stderr=subprocess.STDOUT,
#                stdin=subprocess.PIPE,
#                text=True,
#                encoding="utf-8",
#                errors="replace",
#                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
#            )
#        except Exception as e:
#            self.failed.emit(str(e))
#            return
#
#        self.started_ok.emit()
#
#        # ログをリアルタイムで読む
#        for line in self._process.stdout:
#            self.log_received.emit(line.rstrip())
#
#        exit_code = self._process.wait()
#        self.stopped.emit(exit_code)

    def send_command(self, command: str):
        """サーバーにコマンドを送信する"""
        if self._process and self._process.stdin:
            try:
                self._process.stdin.write(command + "\n")
                self._process.stdin.flush()
            except Exception:
                pass

    def stop(self):
        """サーバーを停止する（stopコマンドを送信）"""
        self.send_command("stop")

    def kill(self):
        """強制終了"""
        if self._process:
            self._process.kill()
    
    def run(self):
        server_dir = self._profile.get("server_dir", "").strip()
        if not server_dir or not os.path.isdir(server_dir):
            self.failed.emit("Server directory is not set or does not exist.")
            return

        exec_file = self._profile.get("exec_file", "").strip() or "start.bat"
        exec_path = os.path.join(server_dir, exec_file)

        if self._profile.get("custom_flags", False):
            custom_bat = self._profile.get("custom_bat", "").strip()
            if not custom_bat:
                self.failed.emit("Custom flags enabled but no command set.")
                return
            cmd = custom_bat.split()

        elif os.path.exists(exec_path):
            if exec_file.endswith(".bat"):
                cmd = ["cmd.exe", "/c", exec_path]
            elif exec_file.endswith(".sh"):
                cmd = ["bash", exec_path]
            else:
                cmd = [exec_path]

        else:
            # exec_fileが存在しない → jarから起動コマンドを生成
            jar_path = _find_jar(self._profile)
            if not jar_path:
                self.failed.emit(
                    f"No exec file or jar found in: {server_dir}"
                )
                return

            cmd = _build_command(self._profile, jar_path)

            # start.batを自動生成
            if exec_file.endswith(".bat"):
                self._generate_bat(exec_path, cmd)
                self.log_received.emit(f"[INFO] Generated: {exec_path}")

        self.log_received.emit(f"[INFO] Command: {' '.join(cmd)}")
        self.log_received.emit(f"[INFO] Working directory: {server_dir}")

        

        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
        except Exception as e:
            self.failed.emit(str(e))
            return

        self.started_ok.emit()

        for line in self._process.stdout:
            self.log_received.emit(line.rstrip())

        exit_code = self._process.wait()
        self.stopped.emit(exit_code)

    def _generate_bat(self, bat_path: str, cmd: list[str]):
        """start.batを自動生成する"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write(" ".join(cmd) + "\n")
            f.write("pause\n")