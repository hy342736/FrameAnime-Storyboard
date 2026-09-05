from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .storage import safe_child


class BubblePackError(ValueError):
    pass


class BubblePackLibrary:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def list_packs(self) -> list[dict[str, Any]]:
        catalog = self._read_json(self.root / "配置.json", "气泡目录索引")
        if catalog.get("schema_version") != 1 or not isinstance(catalog.get("packs"), list):
            raise BubblePackError("气泡目录索引格式无效")
        result = []
        seen = set()
        for entry in catalog["packs"]:
            if not isinstance(entry, dict):
                raise BubblePackError("气泡目录项必须是对象")
            directory = self._segment(entry.get("directory"), "气泡目录")
            manifest = self._read_json(safe_child(self.root, directory, entry.get("manifest", "配置.json")), f"气泡配置 {directory}")
            self._validate_manifest(manifest, directory)
            if manifest["id"] in seen:
                raise BubblePackError(f"气泡包 ID 重复：{manifest['id']}")
            seen.add(manifest["id"])
            if entry.get("id") != manifest["id"] or bool(entry.get("enabled")) != bool(manifest.get("enabled")):
                raise BubblePackError(f"气泡目录与配置不一致：{manifest['id']}")
            if manifest["enabled"]:
                result.append(deepcopy(manifest))
        return result

    def get_pack(self, pack_id: str) -> dict[str, Any] | None:
        return next((pack for pack in self.list_packs() if pack["id"] == pack_id), None)

    def asset_path(self, pack_id: str, asset_id: str) -> Path:
        pack = self.get_pack(pack_id)
        if pack is None:
            raise BubblePackError("气泡包不存在或未启用")
        asset = next((item for item in pack["assets"] if item["id"] == asset_id), None)
        if asset is None:
            raise BubblePackError("气泡样式不存在")
        return safe_child(self.root, pack["slug"], asset["file"])

    def _validate_manifest(self, manifest: dict[str, Any], directory: str) -> None:
        if manifest.get("schema_version") != 1 or manifest.get("slug") != directory:
            raise BubblePackError(f"气泡配置格式无效：{directory}")
        if not all(isinstance(manifest.get(key), str) and manifest[key] for key in ("id", "display_name", "description")):
            raise BubblePackError(f"气泡配置文字字段无效：{directory}")
        assets = manifest.get("assets")
        defaults = manifest.get("semantic_defaults")
        if not isinstance(assets, list) or not assets or not isinstance(defaults, dict):
            raise BubblePackError(f"气泡资源配置无效：{directory}")
        ids = set()
        for asset in assets:
            if not isinstance(asset, dict) or not all(isinstance(asset.get(key), str) and asset[key] for key in ("id", "label", "semantic_type", "file")):
                raise BubblePackError(f"气泡资源字段无效：{directory}")
            if asset["id"] in ids:
                raise BubblePackError(f"气泡资源 ID 重复：{asset['id']}")
            ids.add(asset["id"])
            image = safe_child(self.root, directory, self._segment(asset["file"], "气泡图片"))
            if image.suffix.lower() != ".png" or not image.is_file():
                raise BubblePackError(f"气泡图片不存在：{asset['file']}")
        if any(value not in ids for value in defaults.values()):
            raise BubblePackError(f"气泡默认映射无效：{directory}")

    @staticmethod
    def _read_json(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BubblePackError(f"{label}无法读取") from exc
        if not isinstance(value, dict):
            raise BubblePackError(f"{label}必须是对象")
        return value

    @staticmethod
    def _segment(value: Any, label: str) -> str:
        if not isinstance(value, str) or not value or Path(value).name != value or value in {".", ".."}:
            raise BubblePackError(f"{label}无效")
        return value
