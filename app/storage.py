"""Small JSON-backed storage layer for the personal workbench.

The application is intentionally local and single-user, so a database would add
more operational weight than value here. This module still keeps all path
handling and persistence in one place so project isolation is explicit.
"""

from __future__ import annotations

import json
import re
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from .config import Settings


PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
OWNER_TYPES = {"character", "world", "shot", "lettering"}
REFERENCE_TYPES = {
    "character_design",
    "hair_costume_palette",
    "expression",
    "pose",
    "character_version",
    "world_impression",
    "architecture",
    "landscape",
    "interior",
    "map_landmark",
    "palette_material",
    "era_atmosphere",
    "faction",
    "character_position",
    "draft_revision",
    "action_pose",
    "background_color",
    "composition",
    "other",
}


class RevisionConflictError(RuntimeError):
    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(f"项目版本冲突：期望 {expected}，当前 {actual}")
        self.expected = expected
        self.actual = actual


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_id(value: str, label: str = "id") -> str:
    if not isinstance(value, str) or not PROJECT_ID_RE.fullmatch(value):
        raise ValueError(f"无效的{label}")
    return value


def safe_child(root: Path, *parts: str) -> Path:
    """Resolve a path and ensure it stays under root."""

    root = root.expanduser().resolve()
    target = root.joinpath(*parts).resolve()
    if target != root and root not in target.parents:
        raise ValueError("路径超出允许目录")
    return target


class WorkspaceStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.RLock()
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_file = self.settings.data_dir / "workspace.json"
        self._workspace = self._read_workspace()

    def _read_workspace(self) -> dict[str, Any]:
        if not self.workspace_file.is_file():
            return {"projects": {}, "references": {}, "conversation_bindings": {}}
        try:
            data = json.loads(self.workspace_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"projects": {}, "references": {}, "conversation_bindings": {}}
        if not isinstance(data, dict):
            return {"projects": {}, "references": {}, "conversation_bindings": {}}
        projects = data.get("projects")
        references = data.get("references")
        conversation_bindings = data.get("conversation_bindings")
        return {
            "projects": projects if isinstance(projects, dict) else {},
            "references": references if isinstance(references, dict) else {},
            "conversation_bindings": conversation_bindings if isinstance(conversation_bindings, dict) else {},
        }

    def _write_workspace(self) -> None:
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.workspace_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._workspace, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.workspace_file)

    @staticmethod
    def _project_public(project: dict[str, Any], include_state: bool = False) -> dict[str, Any]:
        result = {
            "id": project["id"],
            "name": project.get("name", "未命名项目"),
            "description": project.get("description", ""),
            "created_at": project.get("created_at", ""),
            "updated_at": project.get("updated_at", ""),
            "revision": max(1, int(project.get("revision", 1))),
        }
        if include_state:
            result["state"] = project.get("state") or {}
        return result

    def list_projects(self) -> list[dict[str, Any]]:
        with self._lock:
            projects = list(self._workspace["projects"].values())
            projects.sort(key=lambda item: item.get("created_at", ""))
            return [self._project_public(project) for project in projects]

    def get_project(self, project_id: str, include_state: bool = True) -> dict[str, Any] | None:
        validate_id(project_id, "项目 ID")
        with self._lock:
            project = self._workspace["projects"].get(project_id)
            return self._project_public(project, include_state) if project else None

    def create_project(
        self,
        name: str,
        description: str = "",
        state: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        clean_name = name.strip()
        if not clean_name or len(clean_name) > 120:
            raise ValueError("项目名称不能为空且不能超过 120 个字符")
        with self._lock:
            project_id = validate_id(project_id, "项目 ID") if project_id else f"project-{uuid4().hex[:12]}"
            if project_id in self._workspace["projects"]:
                raise ValueError("项目 ID 已存在")
            now = utc_now()
            project = {
                "id": project_id,
                "name": clean_name,
                "description": description.strip()[:500],
                "created_at": now,
                "updated_at": now,
                "revision": 1,
                "state": state if isinstance(state, dict) else {},
            }
            self._workspace["projects"][project_id] = project
            self._write_workspace()
            return self._project_public(project, include_state=True)

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        state: dict[str, Any] | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        validate_id(project_id, "项目 ID")
        with self._lock:
            project = self._workspace["projects"].get(project_id)
            if project is None:
                raise KeyError(project_id)
            actual_revision = max(1, int(project.get("revision", 1)))
            if expected_revision is not None and expected_revision != actual_revision:
                raise RevisionConflictError(expected_revision, actual_revision)
            if name is not None:
                clean_name = name.strip()
                if not clean_name or len(clean_name) > 120:
                    raise ValueError("项目名称不能为空且不能超过 120 个字符")
                project["name"] = clean_name
            if description is not None:
                project["description"] = description.strip()[:500]
            if state is not None:
                project["state"] = state
            project["updated_at"] = utc_now()
            project["revision"] = actual_revision + 1
            self._write_workspace()
            return self._project_public(project, include_state=True)

    def update_project_state_if_revision(
        self,
        project_id: str,
        expected_revision: int,
        updater,
    ) -> dict[str, Any]:
        """Apply one state transformation and one disk replace under the project lock."""

        validate_id(project_id, "项目 ID")
        with self._lock:
            project = self._workspace["projects"].get(project_id)
            if project is None:
                raise KeyError(project_id)
            actual_revision = max(1, int(project.get("revision", 1)))
            if expected_revision != actual_revision:
                raise RevisionConflictError(expected_revision, actual_revision)
            next_state = updater(deepcopy(project.get("state") or {}))
            if not isinstance(next_state, dict):
                raise ValueError("项目状态必须是对象")
            project["state"] = next_state
            project["revision"] = actual_revision + 1
            project["updated_at"] = utc_now()
            self._write_workspace()
            return self._project_public(project, include_state=True)

    def delete_project(self, project_id: str) -> None:
        validate_id(project_id, "项目 ID")
        with self._lock:
            if project_id not in self._workspace["projects"]:
                raise KeyError(project_id)
            reference_ids = [
                ref_id
                for ref_id, reference in self._workspace["references"].items()
                if reference.get("project_id") == project_id
            ]
            for reference_id in reference_ids:
                reference = self._workspace["references"].pop(reference_id)
                self._remove_reference_file(reference)
            self._workspace["conversation_bindings"].pop(project_id, None)
            self._workspace["projects"].pop(project_id)
            self._write_workspace()

    @staticmethod
    def conversation_binding_public(binding: dict[str, Any]) -> dict[str, Any]:
        return {
            "project_id": binding["project_id"],
            "url": binding["url"],
            "title": binding.get("title", ""),
            "created_at": binding.get("created_at", ""),
            "updated_at": binding.get("updated_at", ""),
        }

    def get_conversation_binding(self, project_id: str) -> dict[str, Any] | None:
        validate_id(project_id, "项目 ID")
        with self._lock:
            binding = self._workspace["conversation_bindings"].get(project_id)
            return self.conversation_binding_public(binding) if binding else None

    def set_conversation_binding(self, project_id: str, *, url: str, title: str = "") -> dict[str, Any]:
        validate_id(project_id, "项目 ID")
        parsed = urlsplit(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("镜像站对话网址无效")
        with self._lock:
            if project_id not in self._workspace["projects"]:
                raise KeyError(project_id)
            existing = self._workspace["conversation_bindings"].get(project_id)
            now = utc_now()
            binding = {
                "project_id": project_id,
                "url": url.strip(),
                "title": title.strip()[:160],
                "created_at": existing.get("created_at", now) if existing else now,
                "updated_at": now,
            }
            self._workspace["conversation_bindings"][project_id] = binding
            self._write_workspace()
            return self.conversation_binding_public(binding)

    def delete_conversation_binding(self, project_id: str) -> None:
        validate_id(project_id, "项目 ID")
        with self._lock:
            if project_id not in self._workspace["projects"]:
                raise KeyError(project_id)
            self._workspace["conversation_bindings"].pop(project_id, None)
            self._write_workspace()

    def _project_reference_root(self, project_id: str, owner_type: str, owner_id: str) -> Path:
        validate_id(project_id, "项目 ID")
        if owner_type not in OWNER_TYPES:
            raise ValueError("无效的参考图归属类型")
        validate_id(owner_id, "归属对象 ID")
        return safe_child(self.settings.reference_dir, project_id, owner_type, owner_id)

    def _remove_reference_file(self, reference: dict[str, Any]) -> None:
        file_path = Path(reference.get("file_path", ""))
        if file_path.is_file():
            file_path.unlink()

    @staticmethod
    def reference_public(reference: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": reference["id"],
            "project_id": reference["project_id"],
            "owner_type": reference["owner_type"],
            "owner_id": reference["owner_id"],
            "file_name": reference.get("file_name", "参考图"),
            "reference_type": reference.get("reference_type", "other"),
            "note": reference.get("note", ""),
            "sort_order": reference.get("sort_order", 0),
            "enabled": bool(reference.get("enabled", True)),
            "is_primary": bool(reference.get("is_primary", False)),
            "created_at": reference.get("created_at", ""),
            "mime_type": reference.get("mime_type", "image/png"),
        }

    def list_references(
        self,
        project_id: str,
        owner_type: str | None = None,
        owner_id: str | None = None,
    ) -> list[dict[str, Any]]:
        validate_id(project_id, "项目 ID")
        with self._lock:
            references = [
                reference
                for reference in self._workspace["references"].values()
                if reference.get("project_id") == project_id
                and (owner_type is None or reference.get("owner_type") == owner_type)
                and (owner_id is None or reference.get("owner_id") == owner_id)
            ]
            references.sort(key=lambda item: (item.get("sort_order", 0), item.get("created_at", "")))
            return [self.reference_public(reference) for reference in references]

    def get_reference(self, reference_id: str) -> dict[str, Any] | None:
        validate_id(reference_id, "参考图 ID")
        with self._lock:
            return self._workspace["references"].get(reference_id)

    def reference_file(self, reference_id: str) -> Path | None:
        reference = self.get_reference(reference_id)
        if reference is None:
            return None
        file_path = Path(reference.get("file_path", ""))
        return file_path if file_path.is_file() else None

    def add_reference(
        self,
        *,
        project_id: str,
        owner_type: str,
        owner_id: str,
        file_name: str,
        mime_type: str,
        content: bytes,
        reference_type: str = "other",
        note: str = "",
        enabled: bool = True,
        sort_order: int | None = None,
        is_primary: bool = False,
    ) -> dict[str, Any]:
        if not self.get_project(project_id, include_state=False):
            raise KeyError(project_id)
        if not content:
            raise ValueError("参考图文件为空")
        if not mime_type.startswith("image/"):
            raise ValueError("只支持图片参考图")
        if reference_type not in REFERENCE_TYPES:
            raise ValueError("无效的参考图类型")
        root = self._project_reference_root(project_id, owner_type, owner_id)
        suffix = Path(file_name).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
            suffix = ".png"
        reference_id = f"ref-{uuid4().hex[:16]}"
        target = safe_child(root, f"{reference_id}{suffix}")
        with self._lock:
            root.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            if sort_order is None:
                project_refs = [
                    item for item in self._workspace["references"].values()
                    if item.get("project_id") == project_id
                    and item.get("owner_type") == owner_type
                    and item.get("owner_id") == owner_id
                ]
                sort_order = len(project_refs)
                is_primary = not project_refs
            if is_primary:
                for existing in self._workspace["references"].values():
                    if (
                        existing.get("project_id") == project_id
                        and existing.get("owner_type") == owner_type
                        and existing.get("owner_id") == owner_id
                    ):
                        existing["is_primary"] = False
            reference = {
                "id": reference_id,
                "project_id": project_id,
                "owner_type": owner_type,
                "owner_id": owner_id,
                "file_name": Path(file_name).name[:180] or f"{reference_id}{suffix}",
                "file_path": str(target),
                "mime_type": mime_type,
                "reference_type": reference_type,
                "note": note.strip()[:500],
                "sort_order": max(0, int(sort_order)),
                "enabled": bool(enabled),
                "is_primary": bool(is_primary),
                "created_at": utc_now(),
            }
            self._workspace["references"][reference_id] = reference
            self._touch_project(project_id)
            self._write_workspace()
            return self.reference_public(reference)

    def update_reference(
        self,
        reference_id: str,
        *,
        reference_type: str | None = None,
        note: str | None = None,
        sort_order: int | None = None,
        enabled: bool | None = None,
        is_primary: bool | None = None,
    ) -> dict[str, Any]:
        validate_id(reference_id, "参考图 ID")
        with self._lock:
            reference = self._workspace["references"].get(reference_id)
            if reference is None:
                raise KeyError(reference_id)
            if reference_type is not None:
                if reference_type not in REFERENCE_TYPES:
                    raise ValueError("无效的参考图类型")
                reference["reference_type"] = reference_type
            if note is not None:
                reference["note"] = note.strip()[:500]
            if sort_order is not None:
                reference["sort_order"] = max(0, int(sort_order))
            if enabled is not None:
                reference["enabled"] = bool(enabled)
            if is_primary is not None:
                if is_primary:
                    for existing in self._workspace["references"].values():
                        if (
                            existing.get("project_id") == reference["project_id"]
                            and existing.get("owner_type") == reference["owner_type"]
                            and existing.get("owner_id") == reference["owner_id"]
                        ):
                            existing["is_primary"] = False
                reference["is_primary"] = bool(is_primary)
            self._touch_project(reference["project_id"])
            self._write_workspace()
            return self.reference_public(reference)

    def delete_reference(self, reference_id: str) -> None:
        validate_id(reference_id, "参考图 ID")
        with self._lock:
            reference = self._workspace["references"].pop(reference_id, None)
            if reference is None:
                raise KeyError(reference_id)
            self._remove_reference_file(reference)
            self._touch_project(reference["project_id"])
            self._write_workspace()

    def replace_reference_file(
        self,
        reference_id: str,
        *,
        file_name: str,
        mime_type: str,
        content: bytes,
    ) -> dict[str, Any]:
        if not mime_type.startswith("image/"):
            raise ValueError("只支持图片参考图")
        if not content:
            raise ValueError("参考图文件为空")
        with self._lock:
            reference = self._workspace["references"].get(reference_id)
            if reference is None:
                raise KeyError(reference_id)
            old_path = Path(reference.get("file_path", ""))
            suffix = Path(file_name).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
                suffix = old_path.suffix or ".png"
            target = safe_child(old_path.parent, f"{reference_id}{suffix}")
            target.write_bytes(content)
            if old_path != target and old_path.is_file():
                old_path.unlink()
            reference["file_name"] = Path(file_name).name[:180] or reference["file_name"]
            reference["file_path"] = str(target)
            reference["mime_type"] = mime_type
            self._touch_project(reference["project_id"])
            self._write_workspace()
            return self.reference_public(reference)

    def _touch_project(self, project_id: str) -> None:
        project = self._workspace["projects"].get(project_id)
        if project:
            project["updated_at"] = utc_now()
            project["revision"] = max(1, int(project.get("revision", 1))) + 1
