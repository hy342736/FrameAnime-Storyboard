#!/usr/bin/env python3
"""Validate storyboard manifests and call FrameAnimeDesk's local import API."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


FORMATS = {"vertical_comic", "horizontal_storyboard", "square_social"}
PROMPT_PROFILES = {"natural", "nai"}
ADAPTATION_MODES = {"faithful", "visual"}
CHARACTER_MODES = {"user", "agent"}
SHOT_TYPES = {
    "Extreme Close Up",
    "Close Up",
    "Medium Shot",
    "Full Shot",
    "Wide Shot",
    "Extreme Wide Shot",
}
CAMERA_ANGLES = {"Eye Level", "Low Angle", "High Angle", "POV", "Over Shoulder"}
TEXT_KINDS = {"dialogue", "narration", "sfx"}
TEXT_POSITIONS = {"top-left", "top-right", "left", "right", "bottom"}
TEXT_STYLES = {"speech", "thought", "caption", "sfx"}
BUBBLE_SEMANTICS = {"dialogue", "thought", "narration", "shout", "sfx"}
OWNER_TYPES = {"character", "world", "shot"}
LAYOUT_CONTAINER_TYPES = {"single_panel", "full_width", "split_row_2", "progression_row_3", "inset_panel", "cinematic_wide"}
LAYOUT_BORDER_STYLES = {"none", "solid_black_2px", "solid_white_2px", "broken_panel"}
PANEL_LAYOUT_COUNTS = {"single": 1, "split_vertical_2": 2, "split_horizontal_2": 2, "progression_3": 3, "main_with_inset": 2}
DYNAMIC_EXPRESSIONS = {"still", "action_peak", "speed_lines", "motion_blur", "follow_composition", "impact_composition"}
APP_NAME = "FrameAnimeDesk"
MIN_APP_VERSION = (0, 3, 0)
IMPORT_PROTOCOL_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1
PORT_RANGE = range(8000, 8040)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
MULTI_PANEL_MARKERS = (
    "comic strip",
    "webtoon strip",
    "filmstrip layout",
    "manga page layout",
    "grid layout contact sheet",
)
WORLD_FIELDS = {
    "name", "era", "country", "city", "geography", "technology", "magic",
    "history", "factions", "rules", "conflict", "weather", "time", "visual", "materials",
}


class ClientError(RuntimeError):
    pass


def runtime_file_path() -> Path:
    override = os.environ.get("FRAME_ANIME_DESK_HOME", "").strip()
    if override:
        return Path(override).expanduser() / "runtime.json"
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data) / APP_NAME / "runtime.json"
    return Path.home() / "AppData" / "Local" / APP_NAME / "runtime.json"


def parse_version(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def compatibility_errors(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, dict):
        return ["capabilities response is not an object"]
    errors = []
    if capabilities.get("app_name") != APP_NAME:
        errors.append(f"app_name must be {APP_NAME}")
    if capabilities.get("runtime_mode") != "desktop":
        errors.append("the installed desktop runtime is required")
    version = parse_version(capabilities.get("app_version"))
    if version is None:
        errors.append("app_version must use MAJOR.MINOR.PATCH")
    elif version < MIN_APP_VERSION:
        errors.append("FrameAnimeDesk 0.3.0 or newer is required")
    if capabilities.get("storyboard_import") is not True:
        errors.append("storyboard_import is unavailable")
    if capabilities.get("storyboard_import_protocol_version") != IMPORT_PROTOCOL_VERSION:
        errors.append(f"storyboard import protocol {IMPORT_PROTOCOL_VERSION} is required")
    if MANIFEST_SCHEMA_VERSION not in capabilities.get("schema_versions", []):
        errors.append(f"storyboard schema {MANIFEST_SCHEMA_VERSION} is unavailable")
    if capabilities.get("project_revision") is not True:
        errors.append("project revision protection is unavailable")
    if capabilities.get("deep_link") is not True:
        errors.append("project deep links are unavailable")
    if capabilities.get("style_packs") is not True:
        errors.append("project style packs are unavailable")
    if capabilities.get("custom_style_packs") is not True:
        errors.append("custom style packs are unavailable")
    if capabilities.get("bubble_packs") is not True:
        errors.append("bubble packs are unavailable")
    return errors


def load_json(path: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ClientError(f"Cannot read JSON file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ClientError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ClientError("The JSON root must be an object")
    return value


def require_text(value: Any, path: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")
        return ""
    return value.strip()


def reject_cjk(value: Any, path: str, errors: list[str], *, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        errors.append(f"{path} must be a string")
        return ""
    result = value.strip()
    if required and not result:
        errors.append(f"{path} must be a non-empty string")
    if CJK_RE.search(result):
        errors.append(f"{path} must use English for an NAI project")
    return result


def validate_manifest(manifest: dict[str, Any], *, require_project: bool | None = None) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    project = manifest.get("project")
    if require_project is True and not isinstance(project, dict):
        errors.append("project must be an object for create")
    if require_project is False and project is not None:
        errors.append("project must be omitted for append")
    if isinstance(project, dict):
        require_text(project.get("name"), "project.name", errors)

    preferences = manifest.get("preferences")
    if not isinstance(preferences, dict):
        errors.append("preferences must be an object")
        preferences = {}
    if preferences.get("format") not in FORMATS:
        errors.append(f"preferences.format must be one of {sorted(FORMATS)}")
    budget = preferences.get("panel_budget")
    if not isinstance(budget, int) or isinstance(budget, bool) or not 1 <= budget <= 50:
        errors.append("preferences.panel_budget must be an integer from 1 to 50")
    if preferences.get("adaptation_mode") not in ADAPTATION_MODES:
        errors.append(f"preferences.adaptation_mode must be one of {sorted(ADAPTATION_MODES)}")
    if preferences.get("character_mode") not in CHARACTER_MODES:
        errors.append(f"preferences.character_mode must be one of {sorted(CHARACTER_MODES)}")
    prompt_profile = preferences.get("prompt_profile")
    if prompt_profile not in PROMPT_PROFILES:
        errors.append(f"preferences.prompt_profile must be one of {sorted(PROMPT_PROFILES)}")
    require_text(preferences.get("style_mode"), "preferences.style_mode", errors)
    style_pack_id = preferences.get("style_pack_id", "")
    if require_project is True:
        require_text(style_pack_id, "preferences.style_pack_id", errors)
    elif style_pack_id and not isinstance(style_pack_id, str):
        errors.append("preferences.style_pack_id must be a string")
    for field in ("style_prompt", "style_negative_prompt", "bubble_pack_id"):
        value = preferences.get(field, "")
        if value and not isinstance(value, str):
            errors.append(f"preferences.{field} must be a string")
    if require_project is True:
        require_text(preferences.get("style_prompt"), "preferences.style_prompt", errors)
        require_text(preferences.get("bubble_pack_id"), "preferences.bubble_pack_id", errors)
    style_analysis = preferences.get("style_analysis", {})
    if not isinstance(style_analysis, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in style_analysis.items()):
        errors.append("preferences.style_analysis must be an object of strings")
    if prompt_profile == "nai":
        reject_cjk(preferences.get("style_prompt"), "preferences.style_prompt", errors, required=True)
        reject_cjk(preferences.get("style_negative_prompt", ""), "preferences.style_negative_prompt", errors)
        if isinstance(style_analysis, dict):
            for key, value in style_analysis.items():
                reject_cjk(value, f"preferences.style_analysis.{key}", errors)

        world = manifest.get("world", {})
        if isinstance(world, dict):
            for key, value in world.items():
                if key in WORLD_FIELDS:
                    reject_cjk(value, f"world.{key}", errors)

    source = manifest.get("source_batch")
    if not isinstance(source, dict):
        errors.append("source_batch must be an object")
        source = {}
    selected_text = require_text(source.get("selected_text"), "source_batch.selected_text", errors)
    start_quote = require_text(source.get("start_quote"), "source_batch.start_quote", errors)
    end_quote = require_text(source.get("end_quote"), "source_batch.end_quote", errors)
    if selected_text and start_quote and start_quote not in selected_text:
        errors.append("source_batch.start_quote must occur in selected_text")
    if selected_text and end_quote and end_quote not in selected_text:
        errors.append("source_batch.end_quote must occur in selected_text")
    char_count = source.get("char_count")
    if not isinstance(char_count, int) or isinstance(char_count, bool) or char_count != len(selected_text):
        errors.append("source_batch.char_count must equal len(selected_text)")

    existing_character_ids = manifest.get("existing_character_ids", [])
    if not isinstance(existing_character_ids, list) or not all(
        isinstance(item, str) and item.strip() for item in existing_character_ids
    ):
        errors.append("existing_character_ids must be an array of non-empty strings")
        existing_character_ids = []
    if require_project is True and existing_character_ids:
        errors.append("existing_character_ids must be empty for create")

    characters = manifest.get("characters")
    if not isinstance(characters, list):
        errors.append("characters must be an array")
        characters = []
    character_ids: set[str] = set(existing_character_ids)
    for index, character in enumerate(characters):
        path = f"characters[{index}]"
        if not isinstance(character, dict):
            errors.append(f"{path} must be an object")
            continue
        client_id = require_text(character.get("client_id"), f"{path}.client_id", errors)
        require_text(character.get("name"), f"{path}.name", errors)
        if client_id in character_ids:
            errors.append(f"duplicate character client_id: {client_id}")
        character_ids.add(client_id)
        for field in ("source_facts", "ai_supplements", "needs_user_input", "reference_requests"):
            if not isinstance(character.get(field, []), list):
                errors.append(f"{path}.{field} must be an array")
        if prompt_profile == "nai":
            for field in ("role", "faction", "personality", "appearance", "costume", "signature"):
                reject_cjk(character.get(field, ""), f"{path}.{field}", errors)

    shots = manifest.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array")
        shots = []
    if isinstance(budget, int) and len(shots) != budget:
        errors.append("shot count must equal preferences.panel_budget")
    if len(shots) > 50:
        errors.append("a single manifest cannot contain more than 50 shots")

    shot_ids: set[str] = set()
    for index, shot in enumerate(shots):
        path = f"shots[{index}]"
        if not isinstance(shot, dict):
            errors.append(f"{path} must be an object")
            continue
        shot_id = require_text(shot.get("client_id"), f"{path}.client_id", errors)
        if shot_id in shot_ids:
            errors.append(f"duplicate shot client_id: {shot_id}")
        shot_ids.add(shot_id)
        if shot.get("type") not in SHOT_TYPES:
            errors.append(f"{path}.type must be a supported FrameAnimeDesk shot type")
        require_text(shot.get("title"), f"{path}.title", errors)
        require_text(shot.get("description"), f"{path}.description", errors)

        selected = shot.get("characters", [])
        if not isinstance(selected, list):
            errors.append(f"{path}.characters must be an array")
            selected = []
        unknown = [item for item in selected if item not in character_ids]
        if unknown:
            errors.append(f"{path}.characters references unknown manifest IDs: {unknown}")

        visual = shot.get("visual")
        if not isinstance(visual, dict):
            errors.append(f"{path}.visual must be an object")
        else:
            for field in ("prompt", "scene", "action", "expression", "lighting", "style"):
                require_text(visual.get(field), f"{path}.visual.{field}", errors)
            camera_angle = visual.get("camera_angle", "Eye Level")
            if camera_angle not in CAMERA_ANGLES:
                errors.append(f"{path}.visual.camera_angle is invalid")
            dynamic_expression = visual.get("dynamic_expression", "still")
            if dynamic_expression not in DYNAMIC_EXPRESSIONS:
                errors.append(f"{path}.visual.dynamic_expression is invalid")
            visual_aspect_ratio = str(visual.get("aspect_ratio") or "Auto").strip()
            panel_layout = visual.get("panel_layout", "single")
            if panel_layout not in PANEL_LAYOUT_COUNTS:
                errors.append(f"{path}.visual.panel_layout is invalid")
                expected_panel_count = 1
            else:
                expected_panel_count = PANEL_LAYOUT_COUNTS[panel_layout]
            panel_beats = visual.get("panel_beats", [])
            if not isinstance(panel_beats, list):
                errors.append(f"{path}.visual.panel_beats must be an array")
                panel_beats = []
            if panel_beats and len(panel_beats) != expected_panel_count:
                errors.append(f"{path}.visual.panel_beats count must match panel_layout")
            for beat_index, beat in enumerate(panel_beats):
                if not isinstance(beat, dict):
                    errors.append(f"{path}.visual.panel_beats[{beat_index}] must be an object")
                    continue
                require_text(beat.get("visual"), f"{path}.visual.panel_beats[{beat_index}].visual", errors)
            if prompt_profile == "nai":
                for field in ("prompt", "scene", "action", "expression", "lighting", "style"):
                    reject_cjk(visual.get(field, ""), f"{path}.visual.{field}", errors)
                reject_cjk(visual.get("nai_positive_prompt"), f"{path}.visual.nai_positive_prompt", errors, required=True)
                reject_cjk(visual.get("nai_negative_prompt"), f"{path}.visual.nai_negative_prompt", errors, required=True)
                for beat_index, beat in enumerate(panel_beats):
                    if isinstance(beat, dict):
                        reject_cjk(beat.get("visual", ""), f"{path}.visual.panel_beats[{beat_index}].visual", errors)

            final_prompt = str(
                visual.get("nai_positive_prompt") if prompt_profile == "nai" else visual.get("prompt")
                or ""
            )
            lower_prompt = final_prompt.lower()
            if any(marker in lower_prompt for marker in MULTI_PANEL_MARKERS):
                count_match = re.search(r"\b([2-9])-panel\b", final_prompt, re.IGNORECASE)
                if not count_match:
                    errors.append(
                        f"{path}.visual final multi-panel prompt must state the exact panel count"
                    )
                else:
                    prompt_panel_count = int(count_match.group(1))
                    missing_positions = [
                        number
                        for number in range(1, prompt_panel_count + 1)
                        if not re.search(
                            rf"\bPanel\s+{number}\s*\([^)]+\)", final_prompt, re.IGNORECASE
                        )
                    ]
                    if missing_positions:
                        errors.append(
                            f"{path}.visual final multi-panel prompt must give every panel "
                            "an explicit numbered position"
                        )
                if CJK_RE.search(final_prompt):
                    errors.append(f"{path}.visual final multi-panel prompt must be entirely English")
                if "featuring the same character across all panels:" not in lower_prompt:
                    errors.append(
                        f"{path}.visual final multi-panel prompt must include the shared "
                        "character appearance anchor"
                    )
                if not all(
                    phrase in lower_prompt
                    for phrase in ("clean panels", "no text", "no gibberish speech bubbles")
                ):
                    errors.append(
                        f"{path}.visual final multi-panel prompt must include clean panels, "
                        "no text, and no gibberish speech bubbles"
                    )
                if not re.search(
                    r"\b(clean (?:white )?(?:gutters|borders)|thin borders|borders between panels)\b",
                    lower_prompt,
                ):
                    errors.append(
                        f"{path}.visual final multi-panel prompt must control gutters or borders"
                    )
                ratio_match = re.search(
                    r"--ar\s+(\d+)\s*:\s*(\d+)\s*[.]?\s*$",
                    final_prompt,
                    re.IGNORECASE,
                )
                if not ratio_match:
                    errors.append(
                        f"{path}.visual final multi-panel prompt must end with an aspect-ratio parameter"
                    )
                else:
                    prompt_ratio = f"{int(ratio_match.group(1))}:{int(ratio_match.group(2))}"
                    if visual_aspect_ratio == "Auto":
                        errors.append(
                            f"{path}.visual.aspect_ratio must be explicit for a multi-panel prompt"
                        )
                    elif prompt_ratio != visual_aspect_ratio:
                        errors.append(
                            f"{path}.visual final multi-panel ratio {prompt_ratio} must match "
                            f"visual.aspect_ratio {visual_aspect_ratio}"
                        )

        directions = shot.get("character_directions", {})
        if prompt_profile == "nai" and isinstance(directions, dict):
            for character_id, direction in directions.items():
                if isinstance(direction, dict):
                    for field in ("position", "action", "expression", "costume"):
                        reject_cjk(direction.get(field, ""), f"{path}.character_directions.{character_id}.{field}", errors)

        shot_source = shot.get("source")
        if not isinstance(shot_source, dict):
            errors.append(f"{path}.source must be an object")
        else:
            anchor = require_text(shot_source.get("anchor"), f"{path}.source.anchor", errors)
            if selected_text and anchor and anchor not in selected_text:
                errors.append(f"{path}.source.anchor must be an exact substring of selected_text")
        if shot_source.get("adaptation_kind") not in {"direct", "visualized", "agent_bridge"}:
                errors.append(f"{path}.source.adaptation_kind is invalid")

        layout = shot.get("layout_meta")
        if layout is not None:
            if not isinstance(layout, dict):
                errors.append(f"{path}.layout_meta must be an object")
            else:
                container_type = layout.get("container_type", "single_panel")
                if container_type not in LAYOUT_CONTAINER_TYPES:
                    errors.append(f"{path}.layout_meta.container_type is invalid")
                border_style = layout.get("border_style", "none")
                if border_style not in LAYOUT_BORDER_STYLES:
                    errors.append(f"{path}.layout_meta.border_style is invalid")
                for field in ("row_index", "slot_index"):
                    value = layout.get(field, 1)
                    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                        errors.append(f"{path}.layout_meta.{field} must be a positive integer")
                gutter = layout.get("gutter_bottom", 0)
                if isinstance(gutter, bool) or not isinstance(gutter, int) or not 0 <= gutter <= 2000:
                    errors.append(f"{path}.layout_meta.gutter_bottom must be an integer from 0 to 2000")
                inset = layout.get("inset_config")
                if inset is not None:
                    if not isinstance(inset, dict):
                        errors.append(f"{path}.layout_meta.inset_config must be an object or null")
                    else:
                        for field in ("x", "y", "width", "height"):
                            value = inset.get(field)
                            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
                                errors.append(f"{path}.layout_meta.inset_config.{field} must be a number from 0 to 1")

        post_text = shot.get("post_text", [])
        if not isinstance(post_text, list):
            errors.append(f"{path}.post_text must be an array")
            post_text = []
        ordinary_count = 0
        sfx_count = 0
        for text_index, block in enumerate(post_text):
            block_path = f"{path}.post_text[{text_index}]"
            if not isinstance(block, dict):
                errors.append(f"{block_path} must be an object")
                continue
            kind = block.get("kind")
            if kind not in TEXT_KINDS:
                errors.append(f"{block_path}.kind is invalid")
            elif kind == "sfx":
                sfx_count += 1
            else:
                ordinary_count += 1
            require_text(block.get("text"), f"{block_path}.text", errors)
            if block.get("position") not in TEXT_POSITIONS:
                errors.append(f"{block_path}.position is invalid")
            if block.get("style") not in TEXT_STYLES:
                errors.append(f"{block_path}.style is invalid")
            bubble_semantic = block.get("bubble_semantic", "")
            if bubble_semantic and bubble_semantic not in BUBBLE_SEMANTICS:
                errors.append(f"{block_path}.bubble_semantic is invalid")
            bubble_asset_id = block.get("bubble_asset_id", "")
            if bubble_asset_id and not isinstance(bubble_asset_id, str):
                errors.append(f"{block_path}.bubble_asset_id must be a string")
        if ordinary_count > 2:
            errors.append(f"{path} has more than two dialogue/narration blocks")
        if sfx_count > 1:
            errors.append(f"{path} has more than one sound-effect block")

    if preferences.get("format") == "vertical_comic" and len(shots) >= 8:
        valid_shots = [shot for shot in shots if isinstance(shot, dict)]
        visuals = [
            shot.get("visual") if isinstance(shot.get("visual"), dict) else {}
            for shot in valid_shots
        ]
        required_dynamic = (len(valid_shots) + 1) // 2
        dynamic_count = sum(
            visual.get("dynamic_expression", "still") != "still" for visual in visuals
        )
        if dynamic_count < required_dynamic:
            errors.append(
                "vertical comic batches of 8+ shots require at least 50% non-still "
                f"dynamic expressions ({dynamic_count}/{len(valid_shots)} supplied)"
            )

        camera_angles = [visual.get("camera_angle", "Eye Level") for visual in visuals]
        if len(set(camera_angles)) < 2:
            errors.append("vertical comic batches of 8+ shots require at least two camera angles")
        run_length = 1
        for previous, current in zip(camera_angles, camera_angles[1:]):
            run_length = run_length + 1 if current == previous else 1
            if run_length > 4:
                errors.append("the same camera angle cannot be used for more than four consecutive shots")
                break

    checklist = manifest.get("checklist", [])
    if not isinstance(checklist, list):
        errors.append("checklist must be an array")
    return errors


class ApiClient:
    def __init__(self, base_url: str, api_key: str, timeout: float) -> None:
        parsed = urllib.parse.urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ClientError("base URL must be an absolute HTTP(S) URL")
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ClientError("FrameAnimeDesk URL must use the local loopback interface")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        data = None
        headers = self._headers()
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        return self.request_bytes(method, path, data=data, headers=headers)

    def request_bytes(
        self,
        method: str,
        path: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        request_headers = self._headers()
        request_headers.update(headers or {})
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=request_headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                if not raw:
                    return {}
                try:
                    return json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ClientError("FrameAnimeDesk returned a non-JSON response") from exc
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw).get("detail", raw)
            except json.JSONDecodeError:
                detail = raw
            raise ClientError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ClientError(f"Cannot reach FrameAnimeDesk at {self.base_url}: {exc.reason}") from exc

    def preflight(self) -> dict[str, Any]:
        health = self.request("GET", "/health")
        if not isinstance(health, dict) or health.get("status") != "ok":
            raise ClientError(f"Unexpected health response from {self.base_url}")
        capabilities = self.request("GET", "/api/import/storyboard/capabilities")
        errors = compatibility_errors(capabilities)
        if errors:
            raise ClientError(
                f"Incompatible FrameAnimeDesk at {self.base_url}:\n- " + "\n- ".join(errors)
            )
        return capabilities


def read_runtime_descriptor() -> tuple[dict[str, Any] | None, str]:
    path = runtime_file_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except OSError as exc:
        return None, f"unreadable: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(value, dict):
        return None, "invalid: root must be an object"
    return value, "present"


def inspect_candidate(base_url: str, api_key: str, timeout: float, source: str) -> dict[str, Any]:
    result: dict[str, Any] = {"base_url": base_url, "source": source, "compatible": False}
    try:
        client = ApiClient(base_url, api_key, min(timeout, 1.0))
        health = client.request("GET", "/health")
        result["health"] = health
        if not isinstance(health, dict) or health.get("status") != "ok":
            result["errors"] = ["unexpected health response"]
            return result
        capabilities = client.request("GET", "/api/import/storyboard/capabilities")
        result["capabilities"] = capabilities
        errors = compatibility_errors(capabilities)
        result["errors"] = errors
        result["compatible"] = not errors
    except ClientError as exc:
        result["errors"] = [str(exc)]
    return result


def connection_report(explicit_url: str | None, api_key: str, timeout: float) -> dict[str, Any]:
    descriptor, runtime_status = read_runtime_descriptor()
    runtime_path = runtime_file_path()
    env_url = os.environ.get("FRAME_ANIME_DESK_URL", "").strip()
    preferred_url = explicit_url or env_url
    preferred_source = "--base-url" if explicit_url else "FRAME_ANIME_DESK_URL"
    if not preferred_url and descriptor:
        candidate = descriptor.get("base_url")
        if isinstance(candidate, str) and candidate.strip():
            preferred_url = candidate.strip()
            preferred_source = "runtime.json"

    inspected: list[dict[str, Any]] = []
    if preferred_url:
        inspected.append(inspect_candidate(preferred_url, api_key, timeout, preferred_source))
        if inspected[0]["compatible"]:
            return {
                "selected": inspected[0],
                "candidates": inspected,
                "runtime_file": str(runtime_path),
                "runtime_status": runtime_status,
                "runtime_descriptor": descriptor,
            }
        if explicit_url or env_url:
            return {
                "selected": None,
                "candidates": inspected,
                "runtime_file": str(runtime_path),
                "runtime_status": runtime_status,
                "runtime_descriptor": descriptor,
            }

    scanned_urls = [f"http://127.0.0.1:{port}" for port in PORT_RANGE]
    already = {item["base_url"] for item in inspected}
    scanned_urls = [url for url in scanned_urls if url not in already]
    with ThreadPoolExecutor(max_workers=10) as executor:
        scanned = list(executor.map(lambda url: inspect_candidate(url, api_key, timeout, "port scan"), scanned_urls))
    inspected.extend(item for item in scanned if item.get("health") is not None)
    compatible = [item for item in inspected if item["compatible"]]
    selected = compatible[0] if len(compatible) == 1 else None
    return {
        "selected": selected,
        "candidates": inspected,
        "runtime_file": str(runtime_path),
        "runtime_status": runtime_status,
        "runtime_descriptor": descriptor,
    }


def resolve_client(args: argparse.Namespace) -> tuple[ApiClient, dict[str, Any]]:
    report = connection_report(args.base_url, args.api_key, args.timeout)
    selected = report["selected"]
    compatible = [item for item in report["candidates"] if item["compatible"]]
    if selected is None:
        if len(compatible) > 1:
            urls = ", ".join(item["base_url"] for item in compatible)
            raise ClientError(
                f"Multiple compatible FrameAnimeDesk instances were found ({urls}). "
                "Use --base-url to select one."
            )
        details = []
        for item in report["candidates"]:
            details.extend(item.get("errors", []))
        suffix = f" Last check: {details[0]}" if details else ""
        raise ClientError(f"No compatible FrameAnimeDesk desktop instance was found.{suffix}")
    client = ApiClient(selected["base_url"], args.api_key, args.timeout)
    return client, report


def encode_multipart_files(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----FrameAnimeDesk{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for file_field, file_path in files:
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode(),
                f"Content-Type: {mime_type}\r\n\r\n".encode(),
                file_path.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def encode_multipart(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    return encode_multipart_files(fields, [(file_field, file_path)])


def validate_remote_resources(client: ApiClient, manifest: dict[str, Any]) -> None:
    preferences = manifest.get("preferences") or {}
    style_pack_id = preferences.get("style_pack_id", "")
    if style_pack_id:
        styles = client.request("GET", "/api/style-packs")
        if not isinstance(styles, list):
            raise ClientError("FrameAnimeDesk returned an invalid style-pack list")
        style_ids = {item.get("id") for item in styles if isinstance(item, dict)}
        if style_pack_id not in style_ids:
            raise ClientError(f"Selected style pack is unavailable: {style_pack_id}")
    bubble_pack_id = preferences.get("bubble_pack_id", "")
    if bubble_pack_id:
        bubbles = client.request("GET", "/api/bubble-packs")
        if not isinstance(bubbles, list):
            raise ClientError("FrameAnimeDesk returned an invalid bubble-pack list")
        bubble_ids = {item.get("id") for item in bubbles if isinstance(item, dict)}
        if bubble_pack_id not in bubble_ids:
            raise ClientError(f"Selected bubble pack is unavailable: {bubble_pack_id}")


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def add_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base-url",
        default=None,
    )
    parser.add_argument("--api-key", default=os.environ.get("FRAME_ANIME_DESK_API_KEY", ""))
    parser.add_argument("--timeout", type=float, default=15.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_connection_args(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Check the local FrameAnimeDesk service")
    subparsers.add_parser("capabilities", help="Read storyboard import capabilities")
    subparsers.add_parser("discover", help="Find the active FrameAnimeDesk desktop instance")
    subparsers.add_parser("doctor", help="Diagnose desktop discovery and import compatibility")
    subparsers.add_parser("projects", help="List projects")
    subparsers.add_parser("style-packs", help="List currently available project style packs")
    subparsers.add_parser("bubble-packs", help="List currently available post-production bubble packs")

    project = subparsers.add_parser("project", help="Read one project and its revision")
    project.add_argument("project_id")

    validate = subparsers.add_parser("validate", help="Validate a storyboard manifest without mutation")
    validate.add_argument("manifest")
    validate.add_argument("--mode", choices=("create", "append"))

    create = subparsers.add_parser("create", help="Atomically create a storyboard project")
    create.add_argument("manifest")

    append = subparsers.add_parser("append", help="Atomically append a storyboard batch")
    append.add_argument("project_id")
    append.add_argument("manifest")
    append.add_argument("--expected-revision", type=int, required=True)

    revise = subparsers.add_parser("revise", help="Apply a targeted shot revision")
    revise.add_argument("project_id")
    revise.add_argument("shot_id")
    revise.add_argument("patch")
    revise.add_argument("--expected-revision", type=int, required=True)
    revise.add_argument("--allow-generated-shot-change", action="store_true")

    upload = subparsers.add_parser("upload-reference", help="Upload an explicitly authorized image")
    upload.add_argument("project_id")
    upload.add_argument("owner_type", choices=sorted(OWNER_TYPES))
    upload.add_argument("owner_id")
    upload.add_argument("file")
    upload.add_argument("--reference-type", default="other")
    upload.add_argument("--note", default="")
    upload.add_argument("--primary", action="store_true")

    custom_style = subparsers.add_parser("create-style", help="Create a custom style pack from confirmed local images and analysis")
    custom_style.add_argument("profile", help="JSON file containing display_name, description, style_analysis, compiled_prompt, and negative_prompt")
    custom_style.add_argument("primary", help="Required primary style reference")
    custom_style.add_argument("--auxiliary", action="append", default=[], help="Optional auxiliary style reference; repeat up to three times")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            manifest = load_json(args.manifest)
            mode = None if args.mode is None else args.mode == "create"
            errors = validate_manifest(manifest, require_project=mode)
            if errors:
                print_json({"valid": False, "errors": errors})
                return 1
            print_json({"valid": True, "shot_count": len(manifest["shots"])})
            return 0

        report = connection_report(args.base_url, args.api_key, args.timeout)
        if args.command in {"discover", "doctor"}:
            print_json(report)
            return 0 if report["selected"] is not None else 2

        client, _ = resolve_client(args)
        if args.command == "health":
            result = client.request("GET", "/health")
        elif args.command == "capabilities":
            result = client.request("GET", "/api/import/storyboard/capabilities")
        elif args.command == "projects":
            result = client.request("GET", "/api/projects")
        elif args.command == "style-packs":
            result = client.request("GET", "/api/style-packs")
        elif args.command == "bubble-packs":
            result = client.request("GET", "/api/bubble-packs")
        elif args.command == "project":
            project_id = urllib.parse.quote(args.project_id, safe="")
            result = client.request("GET", f"/api/projects/{project_id}")
        elif args.command == "create":
            client.preflight()
            manifest = load_json(args.manifest)
            errors = validate_manifest(manifest, require_project=True)
            if errors:
                raise ClientError("Manifest validation failed:\n- " + "\n- ".join(errors))
            validate_remote_resources(client, manifest)
            result = client.request("POST", "/api/import/storyboard/projects", manifest)
        elif args.command == "append":
            client.preflight()
            manifest = load_json(args.manifest)
            errors = validate_manifest(manifest, require_project=False)
            if errors:
                raise ClientError("Manifest validation failed:\n- " + "\n- ".join(errors))
            validate_remote_resources(client, manifest)
            project_id = urllib.parse.quote(args.project_id, safe="")
            result = client.request(
                "POST",
                f"/api/import/storyboard/projects/{project_id}/append",
                {"expected_revision": args.expected_revision, "manifest": manifest},
            )
        elif args.command == "revise":
            client.preflight()
            patch = load_json(args.patch)
            project_id = urllib.parse.quote(args.project_id, safe="")
            shot_id = urllib.parse.quote(args.shot_id, safe="")
            result = client.request(
                "PATCH",
                f"/api/import/storyboard/projects/{project_id}/shots/{shot_id}",
                {
                    "expected_revision": args.expected_revision,
                    "allow_generated_shot_change": args.allow_generated_shot_change,
                    "patch": patch,
                },
            )
        elif args.command == "upload-reference":
            client.preflight()
            file_path = Path(args.file)
            if not file_path.is_file():
                raise ClientError(f"Reference file does not exist: {file_path}")
            fields = {
                "owner_type": args.owner_type,
                "owner_id": args.owner_id,
                "reference_type": args.reference_type,
                "note": args.note,
                "is_primary": "true" if args.primary else "false",
            }
            body, content_type = encode_multipart(fields, "file", file_path)
            project_id = urllib.parse.quote(args.project_id, safe="")
            result = client.request_bytes(
                "POST",
                f"/api/projects/{project_id}/references",
                data=body,
                headers={"Content-Type": content_type},
            )
        elif args.command == "create-style":
            client.preflight()
            profile = load_json(args.profile)
            primary = Path(args.primary)
            auxiliary = [Path(value) for value in args.auxiliary]
            if not primary.is_file():
                raise ClientError(f"Primary style reference does not exist: {primary}")
            if len(auxiliary) > 3:
                raise ClientError("A custom style accepts at most three auxiliary references")
            if any(not path.is_file() for path in auxiliary):
                raise ClientError("One or more auxiliary style references do not exist")
            display_name = require_text(profile.get("display_name"), "display_name", [])
            compiled_prompt = require_text(profile.get("compiled_prompt"), "compiled_prompt", [])
            analysis = profile.get("style_analysis")
            if not display_name or not compiled_prompt or not isinstance(analysis, dict):
                raise ClientError("Style profile requires display_name, compiled_prompt, and style_analysis")
            fields = {
                "display_name": display_name,
                "description": str(profile.get("description", "")),
                "style_analysis": json.dumps(analysis, ensure_ascii=False),
                "compiled_prompt": compiled_prompt,
                "negative_prompt": str(profile.get("negative_prompt", "")),
            }
            body, content_type = encode_multipart_files(fields, [("primary", primary), *(("auxiliary", path) for path in auxiliary)])
            result = client.request_bytes("POST", "/api/style-packs/custom", data=body, headers={"Content-Type": content_type})
        else:
            raise ClientError(f"Unsupported command: {args.command}")
        print_json(result)
        return 0
    except ClientError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
