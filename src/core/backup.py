import os
import zipfile
from datetime import datetime


BACKUP_SCOPE_WORLD = "world"
BACKUP_SCOPE_WORLD_CONFIG = "world_config"
BACKUP_SCOPE_FULL = "full"


def create_backup(server_dir: str, scope: str = BACKUP_SCOPE_WORLD) -> str:
    """Create a zip backup and return the saved path."""
    if not server_dir or not os.path.isdir(server_dir):
        raise ValueError("Server directory is not set or does not exist.")

    backup_dir = os.path.join(server_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    valid_scopes = (BACKUP_SCOPE_WORLD, BACKUP_SCOPE_WORLD_CONFIG, BACKUP_SCOPE_FULL)
    scope = scope if scope in valid_scopes else BACKUP_SCOPE_WORLD

    if scope == BACKUP_SCOPE_WORLD:
        source = os.path.join(server_dir, "world")
        if not os.path.isdir(source):
            raise FileNotFoundError(f"World directory not found: {source}")
        backup_path = os.path.join(backup_dir, f"world-{timestamp}.zip")
        _zip_directory(source, backup_path, base_dir=server_dir)
    elif scope == BACKUP_SCOPE_WORLD_CONFIG:
        backup_path = os.path.join(backup_dir, f"world-config-{timestamp}.zip")
        sources = [
            os.path.join(server_dir, "world"),
            os.path.join(server_dir, "config"),
        ]
        existing_sources = [path for path in sources if os.path.exists(path)]
        if not existing_sources:
            raise FileNotFoundError("World and config directories were not found.")
        _zip_sources(existing_sources, backup_path, base_dir=server_dir)
    else:
        backup_path = os.path.join(backup_dir, f"server-{timestamp}.zip")
        _zip_directory(
            server_dir,
            backup_path,
            base_dir=server_dir,
            skip_dirs={os.path.abspath(backup_dir)}
        )

    return backup_path


def _zip_sources(sources: list[str], backup_path: str, base_dir: str) -> None:
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for source in sources:
            if os.path.isdir(source):
                _write_directory_to_zip(zf, source, base_dir)
            elif os.path.isfile(source):
                arcname = os.path.relpath(source, base_dir)
                zf.write(source, arcname)


def _zip_directory(
    source_dir: str,
    backup_path: str,
    base_dir: str,
    skip_dirs: set[str] | None = None
) -> None:
    skip_dirs = skip_dirs or set()
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        _write_directory_to_zip(zf, source_dir, base_dir, skip_dirs, backup_path)


def _write_directory_to_zip(
    zf: zipfile.ZipFile,
    source_dir: str,
    base_dir: str,
    skip_dirs: set[str] | None = None,
    backup_path: str = ""
) -> None:
    skip_dirs = skip_dirs or set()
    for root, dirs, files in os.walk(source_dir):
        abs_root = os.path.abspath(root)
        dirs[:] = [
            d for d in dirs
            if os.path.abspath(os.path.join(root, d)) not in skip_dirs
        ]
        if abs_root in skip_dirs:
            continue
        for filename in files:
            path = os.path.join(root, filename)
            if backup_path and os.path.abspath(path) == os.path.abspath(backup_path):
                continue
            arcname = os.path.relpath(path, base_dir)
            zf.write(path, arcname)
