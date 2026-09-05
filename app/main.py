from contextlib import asynccontextmanager
import json
import mimetypes
from pathlib import Path
import re
from typing import Any

from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .api_image_client import ApiImageClient
from .bubble_packs import BubblePackError, BubblePackLibrary
from .browser_session import BrowserSession
from .config import Settings, load_settings
from .exporter import ExportError, ExportOptions, export_project
from .runtime import (
    APP_NAME,
    APP_VERSION,
    STORYBOARD_IMPORT_PROTOCOL_VERSION,
    STORYBOARD_SCHEMA_VERSIONS,
    is_packaged,
    resource_path,
)
from .storage import RevisionConflictError, WorkspaceStorage, safe_child
from .storyboard_import import MAX_PANEL_BUDGET, apply_manifest, patch_shot, validate_manifest
from .style_packs import StylePackError, StylePackLibrary


settings: Settings = load_settings()
session = BrowserSession(settings)
api_image_client = ApiImageClient(settings)
storage = WorkspaceStorage(settings)
style_library = StylePackLibrary(resource_path("assets", "style-packs"), settings.data_dir / "style-packs")
bubble_library = BubblePackLibrary(resource_path("assets", "bubble-packs"))

MAX_PROJECT_REFERENCES = 6
MAX_STYLE_REFERENCES = 4
MAX_GENERATION_REFERENCES = MAX_PROJECT_REFERENCES + MAX_STYLE_REFERENCES
MULTI_PANEL_PROMPT_MARKERS = (
    "comic strip",
    "webtoon strip",
    "filmstrip layout",
    "manga page layout",
    "grid layout contact sheet",
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await session.stop()


app = FastAPI(title="Personal Mirror Image Service", lifespan=lifespan)


@app.middleware("http")
async def prevent_stale_frontend(request: Request, call_next):
    """Keep local HTML and frontend assets from reviving an older workbench UI."""

    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".css", ".js", ".html")):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    negative_prompt: str = Field(default="", max_length=4000)
    project_id: str = Field(default="project-default", min_length=1, max_length=80)
    shot_id: str = Field(default="", max_length=80)
    reference_ids: list[str] = Field(default_factory=list, max_length=MAX_PROJECT_REFERENCES)
    selected_character_ids: list[str] = Field(default_factory=list, max_length=6)
    aspect_ratio: str = Field(default="Auto", max_length=16)
    resolution: str = Field(default="Auto", max_length=16)
    style_pack_override: str = Field(default="", max_length=160)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    state: dict[str, Any] = Field(default_factory=dict)


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    state: dict[str, Any] | None = None
    expected_revision: int | None = Field(default=None, ge=1)


class StoryboardAppendRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    manifest: dict[str, Any]


class StoryboardShotRevisionRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    allow_generated_shot_change: bool = False
    patch: dict[str, Any]


class ReferencePatch(BaseModel):
    reference_type: str | None = None
    note: str | None = Field(default=None, max_length=500)
    sort_order: int | None = Field(default=None, ge=0, le=9999)
    enabled: bool | None = None
    is_primary: bool | None = None


class SettingsPatch(BaseModel):
    mirror_url: str | None = None
    mirror_chat_url: str | None = None
    image_dir: str | None = None
    reference_dir: str | None = None
    headless: bool | None = None
    generation_timeout_seconds: float | None = Field(default=None, ge=10, le=3600)
    generation_mode: str | None = None
    image_api_name: str | None = Field(default=None, max_length=120)
    image_api_base_url: str | None = Field(default=None, max_length=500)
    image_api_protocol: str | None = None
    image_api_model: str | None = Field(default=None, max_length=160)
    image_api_prompt_profile: str | None = None
    image_api_key: str | None = Field(default=None, max_length=1000)
    clear_image_api_key: bool | None = None
    image_api_timeout_seconds: float | None = Field(default=None, ge=10, le=3600)


class CustomStylePatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    style_analysis: dict[str, Any] | None = None
    compiled_prompt: str | None = Field(default=None, min_length=1, max_length=8000)
    negative_prompt: str | None = Field(default=None, max_length=4000)


class ProjectExportRequest(BaseModel):
    format: str
    include_lettering: bool = True
    width: int = Field(default=1080, ge=640, le=2160)
    gap: int = Field(default=24, ge=0, le=160)
    frame_duration_seconds: float = Field(default=3.0, ge=1, le=10)
    shot_ids: list[str] = Field(default_factory=list, max_length=500)


def model_values(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def style_pack_with_urls(pack: dict[str, Any]) -> dict[str, Any]:
    result = dict(pack)
    references = dict(pack["references"])
    primary = dict(references["primary"])
    primary["url"] = f"/api/style-packs/{pack['id']}/assets/{primary['role']}"
    auxiliary = []
    for reference in references["auxiliary"]:
        item = dict(reference)
        item["url"] = f"/api/style-packs/{pack['id']}/assets/{item['role']}"
        auxiliary.append(item)
    result["references"] = {"primary": primary, "auxiliary": auxiliary}
    return result


def bubble_pack_with_urls(pack: dict[str, Any]) -> dict[str, Any]:
    result = dict(pack)
    result["assets"] = [
        {**asset, "url": f"/api/bubble-packs/{pack['id']}/assets/{asset['id']}"}
        for asset in pack["assets"]
    ]
    return result


def project_art_direction(project: dict[str, Any] | None) -> dict[str, Any]:
    if not project:
        return {}
    value = (project.get("state") or {}).get("artDirection")
    return value if isinstance(value, dict) else {}


def project_prompt_profile(project: dict[str, Any] | None) -> str:
    value = str(((project or {}).get("state") or {}).get("promptProfile") or "natural").strip().lower()
    return value if value in {"natural", "nai"} else "natural"


def compose_style_prompt(prompt: str, style_prompt: str, negative_prompt: str) -> str:
    sections = [prompt.strip()]
    if style_prompt:
        sections.append(f"[PROJECT ART DIRECTION]\n{style_prompt}")
    if negative_prompt:
        sections.append(f"[EXCLUDE FROM IMAGE]\n{negative_prompt}")
    return "\n\n".join(section for section in sections if section)


def is_agent_multi_panel_prompt(prompt: str) -> bool:
    lower_prompt = prompt.lower()
    return any(marker in lower_prompt for marker in MULTI_PANEL_PROMPT_MARKERS)


def validate_agent_multi_panel_prompt(prompt: str, aspect_ratio: str) -> None:
    if not is_agent_multi_panel_prompt(prompt):
        return

    errors: list[str] = []
    count_match = re.search(r"\b([2-9])-panel\b", prompt, re.IGNORECASE)
    if count_match is None:
        errors.append("必须声明准确的 N-panel 格数")
    else:
        panel_count = int(count_match.group(1))
        missing = [
            str(number)
            for number in range(1, panel_count + 1)
            if re.search(rf"\bPanel\s+{number}\s*\([^)]+\)", prompt, re.IGNORECASE) is None
        ]
        if missing:
            errors.append(f"缺少带空间方位的 Panel {', '.join(missing)}")

    lower_prompt = prompt.lower()
    if CJK_RE.search(prompt):
        errors.append("整段多格提示词必须使用英文")
    if "featuring the same character across all panels:" not in lower_prompt:
        errors.append("缺少统一角色外观锚点")
    if not all(
        phrase in lower_prompt
        for phrase in ("clean panels", "no text", "no gibberish speech bubbles")
    ):
        errors.append("缺少 clean panels、no text 或 no gibberish speech bubbles")
    if not re.search(
        r"\b(clean (?:white )?(?:gutters|borders)|thin borders|borders between panels)\b",
        lower_prompt,
    ):
        errors.append("缺少明确的分隔线或留白控制")

    ratio_match = re.search(r"--ar\s+(\d+)\s*:\s*(\d+)\s*[.]?\s*$", prompt, re.IGNORECASE)
    if ratio_match is None:
        errors.append("画幅比例参数必须位于提示词最后")
    else:
        prompt_ratio = f"{int(ratio_match.group(1))}:{int(ratio_match.group(2))}"
        if aspect_ratio == "Auto":
            errors.append("导演台画面比例不能为 Auto")
        elif prompt_ratio != aspect_ratio:
            errors.append(f"末尾比例 {prompt_ratio} 与导演台选择 {aspect_ratio} 不一致")

    if errors:
        raise HTTPException(status_code=400, detail="多格漫画提示词不符合 Agent 合同：" + "；".join(errors))


def resolve_style_contract(project: dict[str, Any] | None, style_override: str) -> tuple[str, str, str, list[Path]]:
    art_direction = project_art_direction(project)
    override = style_override.strip()
    if override == "none":
        style_pack_id = ""
    elif override:
        style_pack_id = override
    else:
        style_pack_id = str(art_direction.get("stylePackId") or "").strip() if art_direction.get("locked", True) is not False else ""
    if not style_pack_id:
        return "", "", "", []
    pack = style_library.get_pack(style_pack_id)
    if pack is None:
        raise StylePackError("项目选择的画风包不存在或未启用")
    overrides = art_direction if style_pack_id == str(art_direction.get("stylePackId") or "") else {}
    style_prompt, style_negative_prompt = style_library.compile_project_prompt(pack, overrides)
    return style_pack_id, style_prompt, style_negative_prompt, style_library.enabled_reference_paths(style_pack_id)


def validate_import_resources(manifest: dict[str, Any]) -> None:
    preferences = manifest.get("preferences") or {}
    style_pack_id = str(preferences.get("style_pack_id") or "").strip()
    if style_pack_id and style_library.get_pack(style_pack_id) is None:
        raise ValueError(f"画风包不存在或未启用：{style_pack_id}")
    bubble_pack_id = str(preferences.get("bubble_pack_id") or "").strip()
    if bubble_pack_id and bubble_library.get_pack(bubble_pack_id) is None:
        raise ValueError(f"气泡包不存在或未启用：{bubble_pack_id}")


def check_api_key(value: str | None) -> None:
    if settings.local_api_key and value != settings.local_api_key:
        raise HTTPException(status_code=401, detail="invalid API key")


def has_complete_character_visual_dna(character: dict[str, Any]) -> bool:
    incomplete_markers = ("原文未提供", "待用户", "待补充", "未设定", "暂无")

    def usable(value: Any) -> bool:
        text = str(value or "").strip()
        return bool(text) and not any(marker in text for marker in incomplete_markers)

    return usable(character.get("appearance")) and usable(character.get("costume"))


def characters_missing_visual_dna(project_id: str, character_ids: list[str]) -> list[str]:
    project = storage.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    characters = {
        str(character.get("id", "")): character
        for character in (project.get("state") or {}).get("characters", [])
        if isinstance(character, dict)
    }
    return [
        character_id
        for character_id in character_ids
        if character_id not in characters or not has_complete_character_visual_dna(characters[character_id])
    ]


def storyboard_response(
    project: dict[str, Any],
    request: Request,
    character_ids: dict[str, str],
    shot_ids: dict[str, str],
    warnings: list[str],
) -> dict[str, Any]:
    base_url = str(request.base_url).rstrip("/")
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "revision": project["revision"],
        "created_character_ids": character_ids,
        "created_shot_ids": shot_ids,
        "shot_count": len((project.get("state") or {}).get("shots", [])),
        "warnings": warnings,
        "open_url": f"{base_url}/?project_id={project['id']}",
    }


def project_conversation_title(project: dict[str, Any]) -> str:
    short_id = project["id"].removeprefix("project-")[-6:]
    return f"{project['name']} · FRAME-{short_id}"


def conversation_payload(project_id: str, *, status: str | None = None) -> dict[str, Any]:
    binding = storage.get_conversation_binding(project_id)
    if binding:
        return {"status": "bound", **binding}
    return {"status": status or "unbound", "project_id": project_id, "url": "", "title": ""}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/skill")
async def skill_profile() -> dict[str, object]:
    return {
        "name": "Anime AI Art Director",
        "version": "personal-workbench",
        "modules": [
            "Character DNA",
            "Character Bible",
            "World Bible",
            "Storyboard",
            "Layout",
            "Key Animation",
            "Continuity Check",
        ],
        "negative_prompt": [
            "bad anatomy",
            "bad hands",
            "extra fingers",
            "wrong face",
            "wrong hairstyle",
            "different character",
            "low quality",
            "blurry",
            "bad composition",
            "incorrect perspective",
        ],
    }


@app.get("/api/import/storyboard/capabilities")
async def storyboard_capabilities(x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    check_api_key(x_api_key)
    if settings.generation_mode == "api":
        resolved_profile = api_image_client.resolved_prompt_profile()
        generation = {
            "mode": "api",
            "channel": settings.image_api_name,
            "model": settings.image_api_model,
            "protocol": settings.image_api_protocol,
            "prompt_profile": resolved_profile,
            "configured_prompt_profile": settings.image_api_prompt_profile,
            "supports_reference_images": settings.image_api_protocol == "responses",
        }
    else:
        generation = {
            "mode": "mirror",
            "channel": "镜像站浏览器",
            "model": "",
            "protocol": "browser",
            "prompt_profile": "unknown",
            "configured_prompt_profile": "unknown",
            "supports_reference_images": True,
        }
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "runtime_mode": "desktop" if is_packaged() else "development",
        "storyboard_import": True,
        "storyboard_import_protocol_version": STORYBOARD_IMPORT_PROTOCOL_VERSION,
        "storyboard_import_max_shots": MAX_PANEL_BUDGET,
        "schema_versions": list(STORYBOARD_SCHEMA_VERSIONS),
        "project_revision": True,
        "deep_link": True,
        "style_packs": True,
        "custom_style_packs": True,
        "bubble_packs": True,
        "exports": ["png_bundle", "vertical_comic", "pdf", "video"],
        "generation": generation,
    }


@app.get("/api/style-packs")
async def style_packs(
    include_disabled: bool = Query(default=False),
    x_api_key: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    check_api_key(x_api_key)
    try:
        return [
            style_pack_with_urls(pack)
            for pack in style_library.list_packs(include_disabled=include_disabled)
        ]
    except StylePackError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/style-packs/{pack_id}")
async def style_pack(pack_id: str, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        pack = style_library.get_pack(pack_id, include_disabled=True)
    except StylePackError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if pack is None:
        raise HTTPException(status_code=404, detail="画风包不存在")
    return style_pack_with_urls(pack)


@app.get("/api/style-packs/{pack_id}/assets/{role}")
async def style_pack_asset(pack_id: str, role: str, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    try:
        path = style_library.asset_path(pack_id, role)
    except StylePackError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=3600"})


@app.post("/api/style-packs/custom", status_code=201)
async def create_custom_style_pack(
    display_name: str = Form(...),
    description: str = Form(default=""),
    style_analysis: str = Form(default="{}"),
    compiled_prompt: str = Form(...),
    negative_prompt: str = Form(default=""),
    primary: UploadFile = File(...),
    auxiliary: list[UploadFile] = File(default=[]),
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        analysis = json.loads(style_analysis)
        if not isinstance(analysis, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="画风分析必须是 JSON 对象") from exc
    try:
        pack = style_library.create_custom_pack(
            display_name=display_name,
            description=description,
            style_analysis=analysis,
            compiled_prompt=compiled_prompt,
            negative_prompt=negative_prompt,
            primary=(primary.filename or "primary", await primary.read()),
            auxiliary=[(upload.filename or "auxiliary", await upload.read()) for upload in auxiliary],
        )
        return style_pack_with_urls(pack)
    except StylePackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/style-packs/{pack_id}/custom")
async def update_custom_style_pack(
    pack_id: str,
    body: CustomStylePatch,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        return style_pack_with_urls(style_library.update_custom_pack(pack_id, model_values(body)))
    except StylePackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/style-packs/{pack_id}/custom/assets")
async def replace_custom_style_assets(
    pack_id: str,
    primary: UploadFile | None = File(default=None),
    auxiliary: list[UploadFile] = File(default=[]),
    replace_auxiliary: bool = Form(default=False),
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        pack = style_library.replace_custom_assets(
            pack_id,
            primary=(primary.filename or "primary", await primary.read()) if primary else None,
            auxiliary=[(upload.filename or "auxiliary", await upload.read()) for upload in auxiliary] if replace_auxiliary else None,
        )
        return style_pack_with_urls(pack)
    except StylePackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/style-packs/{pack_id}/custom", status_code=204)
async def delete_custom_style_pack(pack_id: str, x_api_key: str | None = Header(default=None)) -> None:
    check_api_key(x_api_key)
    try:
        style_library.delete_custom_pack(pack_id)
    except StylePackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/bubble-packs")
async def bubble_packs(x_api_key: str | None = Header(default=None)) -> list[dict[str, Any]]:
    check_api_key(x_api_key)
    try:
        return [bubble_pack_with_urls(pack) for pack in bubble_library.list_packs()]
    except BubblePackError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/bubble-packs/{pack_id}/assets/{asset_id}")
async def bubble_pack_asset(pack_id: str, asset_id: str, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    try:
        path = bubble_library.asset_path(pack_id, asset_id)
    except BubblePackError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


@app.post("/api/import/storyboard/projects", status_code=201)
async def import_storyboard_project(
    manifest: dict[str, Any],
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        validated = validate_manifest(manifest)
        validate_import_resources(validated)
        state, character_ids, shot_ids, warnings = apply_manifest({}, validated, append=False)
        project_spec = validated["project"]
        created = storage.create_project(
            project_spec["name"],
            project_spec.get("description", ""),
            state,
        )
        return storyboard_response(created, request, character_ids, shot_ids, warnings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/import/storyboard/projects/{project_id}/append")
async def append_storyboard_project(
    project_id: str,
    body: StoryboardAppendRequest,
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    character_ids: dict[str, str] = {}
    shot_ids: dict[str, str] = {}
    warnings: list[str] = []

    def append_state(current: dict[str, Any]) -> dict[str, Any]:
        nonlocal character_ids, shot_ids, warnings
        validated = validate_manifest(body.manifest, append=True)
        validate_import_resources(validated)
        next_state, character_ids, shot_ids, warnings = apply_manifest(current, validated, append=True)
        return next_state

    try:
        updated = storage.update_project_state_if_revision(project_id, body.expected_revision, append_state)
        return storyboard_response(updated, request, character_ids, shot_ids, warnings)
    except RevisionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "expected_revision": exc.expected, "current_revision": exc.actual},
        ) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目或角色不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/import/storyboard/projects/{project_id}/shots/{shot_id}")
async def revise_storyboard_shot(
    project_id: str,
    shot_id: str,
    body: StoryboardShotRevisionRequest,
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)

    def revise_state(current: dict[str, Any]) -> dict[str, Any]:
        return patch_shot(current, shot_id, body.patch, body.allow_generated_shot_change)

    try:
        updated = storage.update_project_state_if_revision(project_id, body.expected_revision, revise_state)
        return storyboard_response(updated, request, {}, {}, [])
    except RevisionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "expected_revision": exc.expected, "current_revision": exc.actual},
        ) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目或镜头不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/projects")
async def projects(x_api_key: str | None = Header(default=None)) -> list[dict[str, Any]]:
    check_api_key(x_api_key)
    return storage.list_projects()


@app.post("/api/projects", status_code=201)
async def create_project(
    request: ProjectCreate,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        return storage.create_project(request.name, request.description, request.state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/projects/{project_id}")
async def project(project_id: str, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    check_api_key(x_api_key)
    result = storage.get_project(project_id, include_state=True)
    if result is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return result


@app.get("/api/projects/{project_id}/conversation")
async def project_conversation(
    project_id: str,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    if storage.get_project(project_id, include_state=False) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return conversation_payload(project_id)


@app.post("/api/projects/{project_id}/conversation/bind-current")
async def bind_current_project_conversation(
    project_id: str,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    project = storage.get_project(project_id, include_state=False)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        url = await session.current_conversation_url()
        storage.set_conversation_binding(project_id, url=url, title=project_conversation_title(project))
        return conversation_payload(project_id)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/conversation/new")
async def new_project_conversation(
    project_id: str,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    if storage.get_project(project_id, include_state=False) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        await session.start_new_conversation()
        storage.delete_conversation_binding(project_id)
        return conversation_payload(project_id, status="pending")
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/conversation/open")
async def open_project_conversation(
    project_id: str,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    if storage.get_project(project_id, include_state=False) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    binding = storage.get_conversation_binding(project_id)
    if binding is None:
        raise HTTPException(status_code=409, detail="当前项目尚未绑定镜像站对话")
    try:
        await session.open_conversation(binding["url"])
        return conversation_payload(project_id)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete("/api/projects/{project_id}/conversation")
async def unbind_project_conversation(
    project_id: str,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        storage.delete_conversation_binding(project_id)
        return conversation_payload(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc


@app.patch("/api/projects/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectPatch,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        updated = storage.update_project(project_id, **model_values(request))
        binding = storage.get_conversation_binding(project_id)
        if request.name is not None and binding:
            storage.set_conversation_binding(
                project_id,
                url=binding["url"],
                title=project_conversation_title(updated),
            )
        return updated
    except RevisionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "expected_revision": exc.expected, "current_revision": exc.actual},
        ) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/projects/{project_id}", status_code=204)
async def delete_project(project_id: str, x_api_key: str | None = Header(default=None)) -> None:
    check_api_key(x_api_key)
    try:
        storage.delete_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/exports")
async def create_project_export(
    project_id: str,
    request: ProjectExportRequest,
    x_api_key: str | None = Header(default=None),
):
    check_api_key(x_api_key)
    project = storage.get_project(project_id, include_state=True)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    def resolve_lettering_asset(reference_id: str) -> Path | None:
        reference = storage.get_reference(reference_id)
        if (
            reference is None
            or reference.get("project_id") != project_id
            or reference.get("owner_type") != "lettering"
        ):
            return None
        return storage.reference_file(reference_id)

    try:
        artifact = export_project(
            project,
            settings.image_dir,
            bubble_library,
            ExportOptions(
                **{
                    **model_values(request),
                    "shot_ids": tuple(request.shot_ids),
                }
            ),
            resolve_lettering_asset,
        )
    except (ExportError, BubblePackError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FileResponse(
        artifact.path,
        media_type=artifact.media_type,
        filename=artifact.filename,
        headers={"Cache-Control": "no-store"},
    )


def reference_with_url(reference: dict[str, Any]) -> dict[str, Any]:
    result = dict(reference)
    result["url"] = f"/api/references/{reference['id']}/file"
    return result


def uploaded_mime_type(file: UploadFile) -> str:
    declared = (file.content_type or "").lower()
    if declared.startswith("image/"):
        return declared
    guessed = mimetypes.guess_type(file.filename or "")[0]
    return guessed or "image/png"


@app.get("/api/projects/{project_id}/references")
async def references(
    project_id: str,
    owner_type: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    x_api_key: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    check_api_key(x_api_key)
    if storage.get_project(project_id, include_state=False) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        return [
            reference_with_url(reference)
            for reference in storage.list_references(project_id, owner_type, owner_id)
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/references", status_code=201)
async def upload_reference(
    project_id: str,
    file: UploadFile = File(...),
    owner_type: str = Form("shot"),
    owner_id: str = Form("shot-default"),
    reference_type: str = Form("other"),
    note: str = Form(""),
    enabled: bool = Form(True),
    sort_order: int | None = Form(None),
    is_primary: bool = Form(False),
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="参考图不能超过 20 MB")
    try:
        result = storage.add_reference(
            project_id=project_id,
            owner_type=owner_type,
            owner_id=owner_id,
            file_name=file.filename or "reference.png",
            mime_type=uploaded_mime_type(file),
            content=content,
            reference_type=reference_type,
            note=note,
            enabled=enabled,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        return reference_with_url(result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="项目不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/references/{reference_id}")
async def update_reference(
    reference_id: str,
    request: ReferencePatch,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    try:
        return reference_with_url(storage.update_reference(reference_id, **model_values(request)))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="参考图不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/references/{reference_id}/replace")
async def replace_reference(
    reference_id: str,
    file: UploadFile = File(...),
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="参考图不能超过 20 MB")
    try:
        result = storage.replace_reference_file(
            reference_id,
            file_name=file.filename or "reference.png",
            mime_type=uploaded_mime_type(file),
            content=content,
        )
        return reference_with_url(result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="参考图不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/references/{reference_id}", status_code=204)
async def delete_reference(reference_id: str, x_api_key: str | None = Header(default=None)) -> None:
    check_api_key(x_api_key)
    try:
        storage.delete_reference(reference_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="参考图不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/references/{reference_id}/file")
async def reference_file(reference_id: str, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    reference = storage.get_reference(reference_id)
    path = storage.reference_file(reference_id)
    if reference is None or path is None:
        raise HTTPException(status_code=404, detail="参考图不存在")
    return FileResponse(path, media_type=reference.get("mime_type", "image/png"))


@app.get("/api/settings")
async def get_settings(x_api_key: str | None = Header(default=None)) -> dict[str, object]:
    check_api_key(x_api_key)
    return settings.public()


@app.patch("/api/settings")
async def patch_settings(
    request: SettingsPatch,
    x_api_key: str | None = Header(default=None),
) -> dict[str, object]:
    check_api_key(x_api_key)
    values = model_values(request)
    if "mirror_url" in values and values["mirror_url"] and not str(values["mirror_url"]).startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="镜像站网址必须以 http:// 或 https:// 开头")
    if "mirror_chat_url" in values and values["mirror_chat_url"] and not str(values["mirror_chat_url"]).startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="聊天页面网址必须以 http:// 或 https:// 开头")
    if "image_api_base_url" in values and values["image_api_base_url"] and not str(values["image_api_base_url"]).startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="API 地址必须以 http:// 或 https:// 开头")
    try:
        settings.update(values)
    except (TypeError, ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return settings.public()


@app.post("/api/settings/test-connection")
async def test_connection(x_api_key: str | None = Header(default=None)) -> dict[str, str]:
    check_api_key(x_api_key)
    try:
        url = await session.test_connection()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"无法连接镜像站：{exc}") from exc
    return {"url": url, "message": "镜像站连接成功"}


@app.post("/api/settings/test-image-api")
async def test_image_api(x_api_key: str | None = Header(default=None)) -> dict[str, str]:
    check_api_key(x_api_key)
    try:
        message = await api_image_client.test_connection()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"无法连接生图 API：{exc}") from exc
    return {"message": message}


@app.post("/api/settings/validate-directories")
async def validate_directories(x_api_key: str | None = Header(default=None)) -> dict[str, object]:
    check_api_key(x_api_key)
    return settings.directory_status()


@app.post("/api/session/login")
async def login(x_api_key: str | None = Header(default=None)) -> dict[str, str]:
    check_api_key(x_api_key)
    try:
        url = await session.open_for_login()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"浏览器会话不可用：{exc}") from exc
    return {"message": "浏览器已打开，请手动完成登录", "url": url}


@app.get("/api/session/status")
async def session_status(x_api_key: str | None = Header(default=None)) -> dict[str, object]:
    check_api_key(x_api_key)
    return session.status()


@app.post("/api/generate/preview")
async def preview_generation(
    request: GenerateRequest,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    project = storage.get_project(request.project_id)
    prompt_profile = project_prompt_profile(project)
    validate_agent_multi_panel_prompt(request.prompt, request.aspect_ratio)
    agent_multi_panel = is_agent_multi_panel_prompt(request.prompt)
    try:
        style_pack_id, style_prompt, style_negative_prompt, style_paths = resolve_style_contract(
            project, request.style_pack_override
        )
    except StylePackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if settings.generation_mode == "api":
        configured_profile = api_image_client.resolved_prompt_profile()
        if configured_profile != prompt_profile:
            raise HTTPException(status_code=400, detail="当前 API 提示词格式与项目不匹配")
        if prompt_profile == "nai":
            positive, embedded_negative = api_image_client._compile_nai_prompt(request.prompt, "", "")
            negative = api_image_client._flatten_nai_tags([embedded_negative, request.negative_prompt])
        elif agent_multi_panel:
            positive, negative = request.prompt.strip(), ""
        else:
            positive, negative = api_image_client.compile_prompt(request.prompt, style_prompt, style_negative_prompt)
        size = (
            api_image_client._nai_pixel_size(request.aspect_ratio, request.resolution)
            if prompt_profile == "nai"
            else api_image_client._pixel_size(request.aspect_ratio, request.resolution)
        )
    else:
        positive = request.prompt.strip() if agent_multi_panel else compose_style_prompt(request.prompt, style_prompt, style_negative_prompt)
        negative = ""
        size = api_image_client._pixel_size(request.aspect_ratio, request.resolution)
    return {
        "positive_prompt": positive,
        "negative_prompt": negative,
        "size": size or "由通道自动决定",
        "aspect_ratio": request.aspect_ratio,
        "style_pack_id": style_pack_id,
        "style_reference_count": len(style_paths),
        "project_reference_count": len(request.reference_ids),
        "prompt_profile": prompt_profile,
    }


@app.post("/api/generate")
async def generate(
    request: GenerateRequest,
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    check_api_key(x_api_key)
    generation_mode = settings.generation_mode
    generation_channel = settings.image_api_name if generation_mode == "api" else "镜像站浏览器"
    generation_model = settings.image_api_model if generation_mode == "api" else ""
    image_dir = settings.image_dir
    project = storage.get_project(request.project_id)
    prompt_profile = project_prompt_profile(project)
    validate_agent_multi_panel_prompt(request.prompt, request.aspect_ratio)
    agent_multi_panel = is_agent_multi_panel_prompt(request.prompt)
    if generation_mode == "api":
        configured_profile = api_image_client.resolved_prompt_profile()
        if configured_profile != prompt_profile:
            project_label = "NAI 项目" if prompt_profile == "nai" else "GPT 自然语言项目"
            model_label = "NAI 标签" if configured_profile == "nai" else "GPT 自然语言"
            raise HTTPException(
                status_code=400,
                detail=f"当前是{project_label}，但 API 模型被识别为{model_label}。请在设置中选择匹配的模型和提示词格式。",
            )
    conversation_binding = (
        storage.get_conversation_binding(request.project_id)
        if generation_mode == "mirror" and project is not None
        else None
    )
    try:
        style_pack_id, style_prompt, style_negative_prompt, style_reference_paths = resolve_style_contract(
            project, request.style_pack_override
        )
    except StylePackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    effective_prompt = request.prompt.strip() if agent_multi_panel else compose_style_prompt(request.prompt, style_prompt, style_negative_prompt)

    project_reference_paths: list[Path] = []
    referenced_character_ids: set[str] = set()
    for reference_id in request.reference_ids[:MAX_PROJECT_REFERENCES]:
        reference = storage.get_reference(reference_id)
        if reference is None or reference.get("project_id") != request.project_id:
            raise HTTPException(status_code=400, detail="参考图不属于当前项目")
        if reference.get("owner_type") == "lettering":
            continue
        if not reference.get("enabled", True):
            continue
        if reference.get("owner_type") == "character":
            referenced_character_ids.add(str(reference.get("owner_id", "")))
        path = storage.reference_file(reference_id)
        if path is not None:
            project_reference_paths.append(path)
    reference_paths = [*style_reference_paths, *project_reference_paths]
    nai_references_omitted = generation_mode == "api" and prompt_profile == "nai" and bool(reference_paths)
    if generation_mode == "api" and prompt_profile == "nai":
        reference_paths = []
    if len(reference_paths) > MAX_GENERATION_REFERENCES:
        raise HTTPException(
            status_code=400,
            detail=f"本次参考图超过 {MAX_GENERATION_REFERENCES} 张，请减少镜头、角色或场景参考图",
        )
    selected_character_ids = list(dict.fromkeys(request.selected_character_ids))
    text_only_character_ids: list[str] = []
    if generation_mode == "mirror" and len(selected_character_ids) > 1:
        missing = [character_id for character_id in selected_character_ids if character_id not in referenced_character_ids]
        if missing:
            incomplete = characters_missing_visual_dna(request.project_id, missing)
            if incomplete:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "多角色无参考图试生成前，请先补全以下角色的外貌锁定与固定服装："
                        f"{', '.join(incomplete)}。也可以为每名角色上传并启用参考图。"
                    ),
                )
            text_only_character_ids = missing
    try:
        if generation_mode == "api":
            api_arguments = {
                "project_id": request.project_id,
                "reference_paths": reference_paths,
                "aspect_ratio": request.aspect_ratio,
                "resolution": request.resolution,
                "style_prompt": "" if agent_multi_panel else style_prompt,
                "style_negative_prompt": "" if agent_multi_panel else style_negative_prompt,
            }
            if prompt_profile == "nai":
                api_arguments["negative_prompt"] = request.negative_prompt
            output = await api_image_client.generate(request.prompt, **api_arguments)
        else:
            output = await session.generate(
                effective_prompt,
                project_id=request.project_id,
                reference_paths=reference_paths,
                require_all_references=bool(style_reference_paths) or (len(selected_character_ids) > 1 and bool(reference_paths)),
                conversation_url=conversation_binding["url"] if conversation_binding else "",
            )
    except Exception as exc:
        failed_conversation_url = str(getattr(exc, "conversation_url", "") or "").strip()
        if (
            generation_mode == "mirror"
            and failed_conversation_url
            and project is not None
            and conversation_binding is None
        ):
            try:
                storage.set_conversation_binding(
                    request.project_id,
                    url=failed_conversation_url,
                    title=project_conversation_title(project),
                )
            except (KeyError, ValueError):
                pass
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    relative_output = output.path.relative_to(image_dir).as_posix()
    text_dna_warning = ""
    if text_only_character_ids:
        text_dna_warning = (
            f"角色 {'、'.join(text_only_character_ids)} 未使用参考图，已按文字视觉设定生成；"
            "跨镜头的脸部、发型和服装一致性可能较弱"
        )
    reference_warning = "；".join(
        warning for warning in (
            output.reference_warning,
            "NAI 标签项目默认使用纯文本请求，本次未上传画风、角色或场景参考图" if nai_references_omitted else "",
            text_dna_warning,
        ) if warning
    )
    conversation_url = ""
    conversation_status = "not_applicable" if generation_mode == "api" else "unbound"
    generation_warning = output.generation_warning
    if generation_mode == "mirror":
        captured_url = getattr(output, "conversation_url", "")
        if captured_url and project is not None:
            conversation_binding = storage.set_conversation_binding(
                request.project_id,
                url=captured_url,
                title=project_conversation_title(project),
            )
        if conversation_binding:
            conversation_url = conversation_binding["url"]
            conversation_status = "bound"
        elif captured_url:
            conversation_url = captured_url
            conversation_status = "bound"
        else:
            missing_binding_warning = "图片已生成，但未识别到对话网址；可在导演台绑定当前对话"
            generation_warning = "；".join(
                warning for warning in (generation_warning, missing_binding_warning) if warning
            )
    return {
        "prompt": effective_prompt,
        "filename": output.path.name,
        "project_id": request.project_id,
        "shot_id": request.shot_id,
        "url": f"/images/{relative_output}",
        "references_requested": str(output.references_requested),
        "references_attached": str(output.references_attached),
        "style_pack_id": style_pack_id,
        "style_references_requested": len(style_reference_paths),
        "reference_warning": reference_warning,
        "generation_warning": generation_warning,
        "requested_size": getattr(output, "requested_size", ""),
        "actual_size": getattr(output, "actual_size", ""),
        "generation_mode": generation_mode,
        "generation_channel": generation_channel,
        "generation_model": generation_model,
        "prompt_profile": getattr(output, "prompt_profile", "natural"),
        "conversation_status": conversation_status,
        "conversation_url": conversation_url,
    }


@app.get("/images/{image_path:path}")
async def image(image_path: str):
    try:
        requested = safe_child(settings.image_dir, *Path(image_path).parts)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="image not found") from exc
    if not requested.is_file():
        raise HTTPException(status_code=404, detail="image not found")
    media_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
    return FileResponse(requested, media_type=media_type)


app.mount("/", StaticFiles(directory=resource_path("web"), html=True), name="web")
