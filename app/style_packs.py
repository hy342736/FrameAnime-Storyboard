from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
from typing import Any
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from .storage import safe_child


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
STYLE_ANALYSIS_FIELDS = (
    "linework",
    "character_rendering",
    "coloring",
    "background",
    "palette_lighting",
    "composition",
    "exclusions",
)
CUSTOM_ID_RE = re.compile(r"^custom-[a-f0-9]{12}$")


class StylePackError(ValueError):
    pass


class StylePackLibrary:
    def __init__(self, builtin_root: Path, custom_root: Path | None = None) -> None:
        self.builtin_root = builtin_root.resolve()
        self.custom_root = custom_root.resolve() if custom_root else None

    def list_packs(self, *, include_disabled: bool = False) -> list[dict[str, Any]]:
        packs = [*self._list_builtin(), *self._list_custom()]
        seen_ids: set[str] = set()
        for pack in packs:
            if pack["id"] in seen_ids:
                raise StylePackError(f"画风 ID 重复：{pack['id']}")
            seen_ids.add(pack["id"])
        return [pack for pack in packs if include_disabled or pack["enabled"]]

    def get_pack(self, pack_id: str, *, include_disabled: bool = False) -> dict[str, Any] | None:
        return next(
            (pack for pack in self.list_packs(include_disabled=include_disabled) if pack["id"] == pack_id),
            None,
        )

    def asset_path(self, pack_id: str, role: str) -> Path:
        pack = self.get_pack(pack_id, include_disabled=True)
        if pack is None:
            raise StylePackError("画风包不存在")
        reference = self._reference_for_role(pack, role)
        return safe_child(self._root_for_pack(pack), pack["slug"], reference["file"])

    def enabled_reference_paths(self, pack_id: str) -> list[Path]:
        pack = self.get_pack(pack_id)
        if pack is None:
            raise StylePackError("画风包不存在或未启用")
        order = pack["generation"]["reference_order"]
        resolved_roles = ["overall_style" if role == "primary" else role for role in order]
        return [self.asset_path(pack_id, role) for role in resolved_roles if self._reference_for_role(pack, role)["enabled"]]

    def create_custom_pack(
        self,
        *,
        display_name: str,
        description: str,
        style_analysis: dict[str, Any],
        compiled_prompt: str,
        negative_prompt: str,
        primary: tuple[str, bytes],
        auxiliary: list[tuple[str, bytes]] | None,
    ) -> dict[str, Any]:
        if self.custom_root is None:
            raise StylePackError("未配置自定义画风目录")
        name = self._required_text(display_name, "画风名称", 80)
        prompt = self._required_text(compiled_prompt, "画风提示词", 8000)
        negative = self._text(negative_prompt, "排除提示词", 4000)
        analysis = self._validate_analysis(style_analysis)
        if auxiliary is not None and len(auxiliary) > 3:
            raise StylePackError("辅助参考图最多 3 张")

        pack_id = f"custom-{uuid4().hex[:12]}"
        target = safe_child(self.custom_root, pack_id)
        temporary = safe_child(self.custom_root, f".{pack_id}.tmp")
        self.custom_root.mkdir(parents=True, exist_ok=True)
        temporary.mkdir(parents=True, exist_ok=False)
        try:
            primary_manifest = self._write_uploaded_image(temporary, "primary", primary, "主参考图")
            primary_manifest.update({"label": "主参考图", "role": "overall_style", "required": True, "enabled": True})
            auxiliary_manifest = []
            for index, upload in enumerate(auxiliary, start=1):
                reference = self._write_uploaded_image(temporary, f"auxiliary-{index}", upload, f"辅助参考图 {index}")
                reference.update({
                    "label": f"辅助参考图 {index}",
                    "role": f"auxiliary_{index}",
                    "enabled": True,
                })
                auxiliary_manifest.append(reference)
            manifest = self._custom_manifest(
                pack_id=pack_id,
                display_name=name,
                description=self._text(description, "画风说明", 500),
                style_analysis=analysis,
                compiled_prompt=prompt,
                negative_prompt=negative,
                primary=primary_manifest,
                auxiliary=auxiliary_manifest,
            )
            (temporary / "配置.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(target)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return self.get_pack(pack_id, include_disabled=True) or manifest

    def update_custom_pack(self, pack_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        pack, directory = self._custom_pack_and_directory(pack_id)
        if "display_name" in changes:
            pack["display_name"] = self._required_text(changes["display_name"], "画风名称", 80)
        if "description" in changes:
            pack["description"] = self._text(changes["description"], "画风说明", 500)
        if "style_analysis" in changes:
            pack["style_analysis"] = self._validate_analysis(changes["style_analysis"])
        if "compiled_prompt" in changes:
            pack["compiled_prompt"] = self._required_text(changes["compiled_prompt"], "画风提示词", 8000)
        if "negative_prompt" in changes:
            pack["negative_prompt"] = self._text(changes["negative_prompt"], "排除提示词", 4000)
        self._write_manifest_atomic(directory, pack)
        return self.get_pack(pack_id, include_disabled=True) or pack

    def replace_custom_assets(
        self,
        pack_id: str,
        *,
        primary: tuple[str, bytes] | None,
        auxiliary: list[tuple[str, bytes]],
    ) -> dict[str, Any]:
        pack, directory = self._custom_pack_and_directory(pack_id)
        if len(auxiliary) > 3:
            raise StylePackError("辅助参考图最多 3 张")
        staged = safe_child(directory, ".assets.tmp")
        staged.mkdir(parents=True, exist_ok=False)
        try:
            current_primary = pack["references"]["primary"]
            primary_manifest = (
                self._write_uploaded_image(staged, "primary", primary, "主参考图")
                if primary is not None
                else {"file": current_primary["file"]}
            )
            primary_manifest.update({"label": "主参考图", "role": "overall_style", "required": True, "enabled": True})
            auxiliary_manifest = deepcopy(pack["references"]["auxiliary"])
            if auxiliary is not None:
                auxiliary_manifest = []
                for index, upload in enumerate(auxiliary, start=1):
                    reference = self._write_uploaded_image(staged, f"auxiliary-{index}", upload, f"辅助参考图 {index}")
                    reference.update({"label": f"辅助参考图 {index}", "role": f"auxiliary_{index}", "enabled": True})
                    auxiliary_manifest.append(reference)

            new_files = []
            if primary is not None:
                new_files.append(primary_manifest["file"])
            if auxiliary is not None:
                new_files.extend(item["file"] for item in auxiliary_manifest)
            for file_name in new_files:
                (staged / file_name).replace(directory / file_name)
            keep = {primary_manifest["file"], *(item["file"] for item in auxiliary_manifest)}
            for path in directory.iterdir():
                if path.is_file() and path.name != "配置.json" and path.name not in keep:
                    path.unlink()
            pack["references"] = {"primary": primary_manifest, "auxiliary": auxiliary_manifest}
            pack["generation"]["reference_order"] = ["primary", *(item["role"] for item in auxiliary_manifest)]
            self._write_manifest_atomic(directory, pack)
        finally:
            shutil.rmtree(staged, ignore_errors=True)
        return self.get_pack(pack_id, include_disabled=True) or pack

    def delete_custom_pack(self, pack_id: str) -> None:
        _, directory = self._custom_pack_and_directory(pack_id)
        shutil.rmtree(directory)

    @staticmethod
    def compile_project_prompt(pack: dict[str, Any], art_direction: dict[str, Any] | None) -> tuple[str, str]:
        direction = art_direction if isinstance(art_direction, dict) else {}
        prompt = str(direction.get("compiledPrompt") or pack.get("compiled_prompt") or "").strip()
        negative = str(direction.get("negativePrompt") or pack.get("negative_prompt") or "").strip()
        return prompt, negative

    def _list_builtin(self) -> list[dict[str, Any]]:
        catalog = self._read_json(self.builtin_root / "配置.json", "画风目录索引")
        if catalog.get("schema_version") != 1 or not isinstance(catalog.get("packs"), list):
            raise StylePackError("画风目录索引格式无效")
        packs: list[dict[str, Any]] = []
        for entry in catalog["packs"]:
            if not isinstance(entry, dict):
                raise StylePackError("画风目录项必须是对象")
            directory = self._clean_segment(entry.get("directory"), "画风目录")
            manifest_name = self._clean_segment(entry.get("manifest", "配置.json"), "画风配置文件")
            pack = self._load_manifest(safe_child(self.builtin_root, directory, manifest_name), directory, "builtin")
            if entry.get("id") != pack["id"] or bool(entry.get("enabled")) != pack["enabled"]:
                raise StylePackError(f"画风目录与配置不一致：{pack['id']}")
            packs.append(pack)
        return packs

    def _list_custom(self) -> list[dict[str, Any]]:
        if self.custom_root is None or not self.custom_root.is_dir():
            return []
        packs = []
        for directory in sorted(path for path in self.custom_root.iterdir() if path.is_dir() and not path.name.startswith(".")):
            packs.append(self._load_manifest(directory / "配置.json", directory.name, "custom"))
        return packs

    def _load_manifest(self, path: Path, directory: str, source: str) -> dict[str, Any]:
        pack = self._read_json(path, f"画风配置 {directory}")
        if pack.get("schema_version") != 1:
            raise StylePackError(f"画风配置版本无效：{directory}")
        required_text = ("id", "slug", "display_name", "description", "compiled_prompt", "negative_prompt")
        for field in required_text:
            if not isinstance(pack.get(field), str):
                raise StylePackError(f"画风配置字段无效：{directory}.{field}")
        if pack["slug"] != directory:
            raise StylePackError(f"画风 slug 与目录不一致：{pack['id']}")
        if source == "custom" and not CUSTOM_ID_RE.fullmatch(pack["id"]):
            raise StylePackError(f"自定义画风 ID 无效：{pack['id']}")
        pack["enabled"] = bool(pack.get("enabled"))
        if pack["enabled"] and pack.get("status") != "ready":
            raise StylePackError(f"启用的画风必须处于 ready 状态：{pack['id']}")
        if pack["enabled"] and not pack["compiled_prompt"].strip():
            raise StylePackError(f"启用的画风缺少合成提示词：{pack['id']}")

        analysis = pack.get("style_analysis")
        if not isinstance(analysis, dict) or any(not isinstance(analysis.get(field), str) for field in STYLE_ANALYSIS_FIELDS):
            raise StylePackError(f"画风分析不完整：{pack['id']}")
        references = pack.get("references")
        if not isinstance(references, dict) or not isinstance(references.get("primary"), dict):
            raise StylePackError(f"画风主参考图配置无效：{pack['id']}")
        auxiliary = references.get("auxiliary")
        if not isinstance(auxiliary, list) or len(auxiliary) > 3:
            raise StylePackError(f"画风辅助参考图必须为 0 到 3 张：{pack['id']}")
        all_references = [references["primary"], *auxiliary]
        roles: set[str] = set()
        for reference in all_references:
            if not isinstance(reference, dict):
                raise StylePackError(f"画风参考图配置无效：{pack['id']}")
            role = str(reference.get("role", ""))
            if not role or role in roles:
                raise StylePackError(f"画风参考图角色重复：{pack['id']}.{role}")
            roles.add(role)
            file_name = self._clean_segment(reference.get("file"), "画风参考图")
            image_path = safe_child(path.parent, file_name)
            if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES or not image_path.is_file():
                raise StylePackError(f"画风参考图不存在或格式不支持：{image_path.name}")
            reference["enabled"] = bool(reference.get("enabled", True))
        if references["primary"].get("role") != "overall_style" or not references["primary"].get("required"):
            raise StylePackError(f"画风必须声明必填主参考图：{pack['id']}")

        generation = pack.get("generation")
        if not isinstance(generation, dict) or not isinstance(generation.get("reference_order"), list):
            raise StylePackError(f"画风生成配置无效：{pack['id']}")
        configured_roles = ["overall_style" if role == "primary" else str(role) for role in generation["reference_order"]]
        if set(configured_roles) != roles or len(configured_roles) != len(roles):
            raise StylePackError(f"画风参考图发送顺序无效：{pack['id']}")
        if int(generation.get("max_auxiliary", 3)) != 3:
            raise StylePackError(f"画风辅助参考图上限必须为 3：{pack['id']}")
        pack["source"] = source
        pack["editable"] = source == "custom"
        return deepcopy(pack)

    def _custom_pack_and_directory(self, pack_id: str) -> tuple[dict[str, Any], Path]:
        pack = self.get_pack(pack_id, include_disabled=True)
        if pack is None:
            raise StylePackError("画风包不存在")
        if pack.get("source") != "custom" or self.custom_root is None:
            raise StylePackError("内置画风不能修改或删除")
        return pack, safe_child(self.custom_root, pack["slug"])

    @staticmethod
    def _custom_manifest(
        *, pack_id: str, display_name: str, description: str, style_analysis: dict[str, str],
        compiled_prompt: str, negative_prompt: str, primary: dict[str, Any], auxiliary: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "schema_version": 1, "id": pack_id, "slug": pack_id, "display_name": display_name,
            "version": 1, "status": "ready", "enabled": True,
            "description": description or "用户创建的项目画风。", "recommended_for": [],
            "references": {"primary": primary, "auxiliary": auxiliary},
            "style_analysis": style_analysis, "compiled_prompt": compiled_prompt,
            "negative_prompt": negative_prompt,
            "generation": {
                "reference_strength_default": "standard", "require_primary": True, "max_auxiliary": 3,
                "include_all_enabled_references": True,
                "reference_order": ["primary", *(item["role"] for item in auxiliary)],
            },
            "asset_provenance": {"source_type": "user_uploaded", "usage_scope": "local_user_data"},
        }

    @staticmethod
    def _write_uploaded_image(directory: Path, stem: str, upload: tuple[str, bytes], label: str) -> dict[str, str]:
        original_name, data = upload
        suffix = Path(original_name or "").suffix.lower()
        if suffix not in SUPPORTED_IMAGE_SUFFIXES:
            raise StylePackError(f"{label}格式不支持，请使用 PNG、JPG、JPEG 或 WebP")
        if not data or len(data) > 20 * 1024 * 1024:
            raise StylePackError(f"{label}必须大于 0 且不超过 20 MB")
        file_name = f"{stem}{suffix}"
        path = directory / file_name
        path.write_bytes(data)
        try:
            with Image.open(path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            path.unlink(missing_ok=True)
            raise StylePackError(f"{label}不是有效图片") from exc
        return {"file": file_name}

    @staticmethod
    def _write_manifest_atomic(directory: Path, manifest: dict[str, Any]) -> None:
        clean = deepcopy(manifest)
        clean.pop("source", None)
        clean.pop("editable", None)
        temporary = directory / "配置.tmp"
        temporary.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(directory / "配置.json")

    def _root_for_pack(self, pack: dict[str, Any]) -> Path:
        if pack.get("source") == "custom":
            if self.custom_root is None:
                raise StylePackError("未配置自定义画风目录")
            return self.custom_root
        return self.builtin_root

    @staticmethod
    def _validate_analysis(value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            raise StylePackError("画风分析必须是对象")
        return {field: StylePackLibrary._text(value.get(field, ""), f"画风分析 {field}", 2000) for field in STYLE_ANALYSIS_FIELDS}

    @staticmethod
    def _required_text(value: Any, label: str, maximum: int) -> str:
        result = StylePackLibrary._text(value, label, maximum)
        if not result:
            raise StylePackError(f"{label}不能为空")
        return result

    @staticmethod
    def _text(value: Any, label: str, maximum: int) -> str:
        if not isinstance(value, str):
            raise StylePackError(f"{label}必须是文本")
        result = value.strip()
        if len(result) > maximum:
            raise StylePackError(f"{label}不能超过 {maximum} 个字符")
        return result

    @staticmethod
    def _read_json(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise StylePackError(f"{label}不存在") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise StylePackError(f"{label}无法读取") from exc
        if not isinstance(value, dict):
            raise StylePackError(f"{label}必须是对象")
        return value

    @staticmethod
    def _clean_segment(value: Any, label: str) -> str:
        if not isinstance(value, str) or not value or Path(value).name != value or value in {".", ".."}:
            raise StylePackError(f"{label}无效")
        return value

    @staticmethod
    def _reference_for_role(pack: dict[str, Any], role: str) -> dict[str, Any]:
        references = [pack["references"]["primary"], *pack["references"]["auxiliary"]]
        reference = next((item for item in references if item["role"] == role), None)
        if reference is None:
            raise StylePackError(f"画风包没有 {role} 参考图")
        return reference
