from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any


APP_DATA_DIRECTORY = "FrameAnimeDesk"
APP_NAME = "FrameAnimeDesk"
APP_VERSION = "0.3.0"
STORYBOARD_IMPORT_PROTOCOL_VERSION = 1
STORYBOARD_SCHEMA_VERSIONS = [1]
RUNTIME_FILE_NAME = "runtime.json"


def is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_path(*parts: str) -> Path:
    """Return a bundled asset path in an exe and a repo path in source mode."""

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return bundle_root.joinpath(*parts)


def packaged_data_root() -> Path:
    override = os.getenv("FRAME_ANIME_DESK_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data) / APP_DATA_DIRECTORY
    return Path.home() / "AppData" / "Local" / APP_DATA_DIRECTORY


def runtime_file_path() -> Path:
    return packaged_data_root() / RUNTIME_FILE_NAME


def write_runtime_descriptor(port: int, *, pid: int | None = None) -> dict[str, Any]:
    """Publish the active desktop endpoint without exposing it beyond loopback."""

    process_id = os.getpid() if pid is None else pid
    descriptor = {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "runtime_mode": "desktop",
        "pid": process_id,
        "port": port,
        "base_url": f"http://127.0.0.1:{port}",
        "storyboard_import_protocol_version": STORYBOARD_IMPORT_PROTOCOL_VERSION,
        "storyboard_schema_versions": list(STORYBOARD_SCHEMA_VERSIONS),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    target = runtime_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{process_id}.tmp")
    temporary.write_text(json.dumps(descriptor, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return descriptor


def remove_runtime_descriptor(*, pid: int | None = None) -> bool:
    """Remove only the descriptor owned by this process."""

    process_id = os.getpid() if pid is None else pid
    target = runtime_file_path()
    try:
        descriptor = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if descriptor.get("pid") != process_id:
        return False
    try:
        target.unlink()
    except FileNotFoundError:
        return False
    return True


def configure_packaged_environment() -> Path | None:
    """Point mutable files outside PyInstaller's temporary extraction folder."""

    if not is_packaged():
        return None

    root = packaged_data_root().resolve()
    defaults = {
        "DATA_DIR": root / "data",
        "BROWSER_PROFILE_DIR": root / "browser-profile",
        "IMAGE_DIR": root / "generated",
        "REFERENCE_DIR": root / "references",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, str(value))

    bundled_browsers = resource_path("ms-playwright")
    if bundled_browsers.is_dir():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(bundled_browsers))
    root.mkdir(parents=True, exist_ok=True)
    return root
