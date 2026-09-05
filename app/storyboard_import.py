from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .storage import PROJECT_ID_RE


WORLD_FIELDS = {
    "name", "era", "country", "city", "geography", "technology", "magic",
    "history", "factions", "rules", "conflict", "weather", "time", "visual", "materials",
}
ADAPTATION_KINDS = {"direct", "visualized", "agent_bridge"}
TEXT_KINDS = {"dialogue", "narration", "sfx"}
TEXT_POSITIONS = {"top-left", "top-right", "left", "right", "bottom"}
TEXT_STYLES = {"speech", "thought", "caption", "sfx"}
BUBBLE_SEMANTICS = {"dialogue", "thought", "narration", "shout", "sfx"}
LAYOUT_CONTAINER_TYPES = {
    "single_panel", "full_width", "split_row_2", "progression_row_3", "inset_panel", "cinematic_wide",
}
LAYOUT_BORDER_STYLES = {"none", "solid_black_2px", "solid_white_2px", "broken_panel"}
FORMATS = {"vertical_comic", "horizontal_storyboard", "square_social"}
ADAPTATION_MODES = {"faithful", "visual"}
CHARACTER_MODES = {"user", "agent"}
PROMPT_PROFILES = {"natural", "nai"}
PANEL_LAYOUT_COUNTS = {"single": 1, "split_vertical_2": 2, "split_horizontal_2": 2, "progression_3": 3, "main_with_inset": 2}
DYNAMIC_EXPRESSIONS = {"still", "action_peak", "speed_lines", "motion_blur", "follow_composition", "impact_composition"}
MAX_PANEL_BUDGET = 50
CJK_RE = re.compile(r"[\u3400-\u9fff]")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}必须是对象")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label}必须是数组")
    return value


def _text(value: Any, label: str, *, required: bool = False, maximum: int = 8000) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError(f"{label}必须是文本")
    result = value.strip()
    if required and not result:
        raise ValueError(f"{label}不能为空")
    if len(result) > maximum:
        raise ValueError(f"{label}不能超过 {maximum} 个字符")
    return result


def _client_id(value: Any, label: str) -> str:
    result = _text(value, label, required=True, maximum=80)
    if not PROJECT_ID_RE.fullmatch(result):
        raise ValueError(f"{label}无效")
    return result


def _nai_english(value: Any, label: str, *, required: bool = False, maximum: int = 8000) -> str:
    result = _text(value, label, required=required, maximum=maximum)
    if CJK_RE.search(result):
        raise ValueError(f"NAI 项目的生图字段必须使用英文：{label}")
    return result


def _layout_meta(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    layout = _object(value, label)
    container_type = layout.get("container_type", "single_panel")
    if container_type not in LAYOUT_CONTAINER_TYPES:
        raise ValueError(f"{label}.container_type 无效")
    row_index = layout.get("row_index", 1)
    slot_index = layout.get("slot_index", 1)
    gutter_bottom = layout.get("gutter_bottom", 0)
    for key, number, minimum, maximum in (
        ("row_index", row_index, 1, 100), ("slot_index", slot_index, 1, 3),
        ("gutter_bottom", gutter_bottom, 0, 4000),
    ):
        if not isinstance(number, int) or isinstance(number, bool) or not minimum <= number <= maximum:
            raise ValueError(f"{label}.{key} 必须是 {minimum} 到 {maximum} 的整数")
    border_style = layout.get("border_style", "none")
    if border_style not in LAYOUT_BORDER_STYLES:
        raise ValueError(f"{label}.border_style 无效")
    inset = layout.get("inset_config")
    if inset is not None:
        inset = _object(inset, f"{label}.inset_config")
        for key in ("x", "y", "width", "height"):
            number = inset.get(key)
            if not isinstance(number, (int, float)) or isinstance(number, bool) or not 0 <= number <= 1:
                raise ValueError(f"{label}.inset_config.{key} 必须是 0 到 1 的数字")
    return layout


def validate_manifest(manifest: dict[str, Any], *, append: bool = False) -> dict[str, Any]:
    data = deepcopy(_object(manifest, "manifest"))
    if data.get("schema_version") != 1:
        raise ValueError("仅支持 schema_version 1")
    if not append:
        project = _object(data.get("project"), "project")
        _text(project.get("name"), "项目名称", required=True, maximum=120)
        _text(project.get("description", ""), "项目说明", maximum=500)

    preferences = _object(data.get("preferences", {}), "preferences")
    prompt_profile = preferences.get("prompt_profile")
    if prompt_profile not in PROMPT_PROFILES:
        raise ValueError("preferences.prompt_profile 必须是 natural 或 nai")
    format_value = preferences.get("format", "vertical_comic")
    if format_value not in FORMATS:
        raise ValueError("无效的画面格式")
    panel_budget = preferences.get("panel_budget")
    if not isinstance(panel_budget, int) or isinstance(panel_budget, bool) or not 1 <= panel_budget <= MAX_PANEL_BUDGET:
        raise ValueError(f"panel_budget 必须是 1 到 {MAX_PANEL_BUDGET} 的整数")
    if preferences.get("adaptation_mode", "faithful") not in ADAPTATION_MODES:
        raise ValueError("无效的改编模式")
    if preferences.get("character_mode", "user") not in CHARACTER_MODES:
        raise ValueError("无效的角色完善模式")
    for key, maximum in (("style_pack_id", 80), ("style_prompt", 8000), ("style_negative_prompt", 4000), ("bubble_pack_id", 80)):
        _text(preferences.get(key, ""), f"preferences.{key}", maximum=maximum)
    style_analysis = preferences.get("style_analysis", {})
    if not isinstance(style_analysis, dict):
        raise ValueError("preferences.style_analysis 必须是对象")
    for key, value in style_analysis.items():
        _text(key, "画风分析字段", required=True, maximum=80)
        _text(value, f"画风分析 {key}", maximum=2000)
    if prompt_profile == "nai":
        _nai_english(preferences.get("style_prompt", ""), "preferences.style_prompt", required=True)
        _nai_english(preferences.get("style_negative_prompt", ""), "preferences.style_negative_prompt", maximum=4000)
        for key, value in style_analysis.items():
            _nai_english(value, f"preferences.style_analysis.{key}", maximum=2000)

    source_batch = _object(data.get("source_batch"), "source_batch")
    _client_id(source_batch.get("batch_id"), "批次 ID")
    selected_text = _text(source_batch.get("selected_text"), "选定原文", required=True, maximum=100000)
    start_quote = _text(source_batch.get("start_quote"), "起始原句", required=True, maximum=1000)
    end_quote = _text(source_batch.get("end_quote"), "结束原句", required=True, maximum=1000)
    if start_quote not in selected_text or end_quote not in selected_text:
        raise ValueError("起止原句必须来自选定原文")
    if source_batch.get("char_count") != len(selected_text):
        raise ValueError("char_count 与选定原文长度不一致")

    characters = _list(data.get("characters", []), "characters")
    character_ids: set[str] = set()
    for index, character in enumerate(characters):
        character = _object(character, f"characters[{index}]")
        client_id = _client_id(character.get("client_id"), "角色 client_id")
        if client_id in character_ids:
            raise ValueError("角色 client_id 重复")
        character_ids.add(client_id)
        _text(character.get("name"), "角色名称", required=True, maximum=120)
        if prompt_profile == "nai":
            for key in ("role", "faction", "personality", "appearance", "costume", "signature"):
                _nai_english(character.get(key, ""), f"characters[{index}].{key}", maximum=2000)
        for key in ("source_facts", "ai_supplements", "needs_user_input", "reference_requests"):
            values = _list(character.get(key, []), f"角色 {key}")
            for value in values:
                _text(value, f"角色 {key} 项", required=True, maximum=1000)

    existing_ids = set()
    for value in _list(data.get("existing_character_ids", []), "existing_character_ids"):
        existing_ids.add(_client_id(value, "已有角色 ID"))

    shots = _list(data.get("shots", []), "shots")
    if not shots:
        raise ValueError("至少需要一个镜头")
    if len(shots) != panel_budget:
        raise ValueError("镜头数量必须与 panel_budget 完全一致")
    shot_ids: set[str] = set()
    available_character_ids = character_ids | existing_ids
    for index, shot in enumerate(shots):
        shot = _object(shot, f"shots[{index}]")
        client_id = _client_id(shot.get("client_id"), "镜头 client_id")
        if client_id in shot_ids:
            raise ValueError("镜头 client_id 重复")
        shot_ids.add(client_id)
        _text(shot.get("title"), "镜头标题", required=True, maximum=120)
        _text(shot.get("description"), "镜头说明", required=True, maximum=1000)
        for character_id in _list(shot.get("characters", []), "镜头角色"):
            if _client_id(character_id, "镜头角色 ID") not in available_character_ids:
                raise ValueError(f"镜头引用了未声明角色：{character_id}")
        directions = _object(shot.get("character_directions", {}), "逐角色画面约束")
        for character_id, direction in directions.items():
            direction = _object(direction, f"角色 {character_id} 画面约束")
            for key in ("position", "action", "expression", "costume"):
                value = _text(direction.get(key, ""), f"角色 {character_id}.{key}", maximum=2000)
                if prompt_profile == "nai":
                    _nai_english(value, f"shots[{index}].character_directions.{character_id}.{key}", maximum=2000)
        visual = _object(shot.get("visual"), "镜头 visual")
        for key in ("prompt", "scene", "action", "expression", "lighting", "style"):
            value = _text(visual.get(key, ""), f"镜头 visual.{key}", maximum=8000)
            if prompt_profile == "nai":
                _nai_english(value, f"shots[{index}].visual.{key}", maximum=8000)
        dynamic_expression = visual.get("dynamic_expression", "still")
        if dynamic_expression not in DYNAMIC_EXPRESSIONS:
            raise ValueError(f"shots[{index}].visual.dynamic_expression 无效")
        panel_layout = visual.get("panel_layout", "single")
        if panel_layout not in PANEL_LAYOUT_COUNTS:
            raise ValueError(f"shots[{index}].visual.panel_layout 无效")
        panel_beats = _list(visual.get("panel_beats", []), f"shots[{index}].visual.panel_beats")
        if panel_beats and len(panel_beats) != PANEL_LAYOUT_COUNTS[panel_layout]:
            raise ValueError(f"shots[{index}].visual.panel_beats 数量与 panel_layout 不匹配")
        for beat_index, beat in enumerate(panel_beats):
            beat = _object(beat, f"shots[{index}].visual.panel_beats[{beat_index}]")
            value = _text(beat.get("visual"), "子格画面内容", required=True, maximum=2000)
            if prompt_profile == "nai":
                _nai_english(value, f"shots[{index}].visual.panel_beats[{beat_index}].visual", maximum=2000)
        if prompt_profile == "nai":
            _nai_english(
                visual.get("nai_positive_prompt"),
                f"shots[{index}].visual.nai_positive_prompt",
                required=True,
            )
            _nai_english(
                visual.get("nai_negative_prompt"),
                f"shots[{index}].visual.nai_negative_prompt",
                required=True,
                maximum=4000,
            )
        _layout_meta(shot.get("layout_meta"), f"shots[{index}].layout_meta")
        source = _object(shot.get("source"), "镜头来源")
        anchor = _text(source.get("anchor"), "原文锚点", required=True, maximum=500)
        if anchor not in selected_text:
            raise ValueError("镜头原文锚点必须逐字来自选定原文")
        if source.get("adaptation_kind") not in ADAPTATION_KINDS:
            raise ValueError("无效的 adaptation_kind")
        safe_areas = _list(shot.get("text_safe_areas", []), "文字安全区")
        if any(area not in TEXT_POSITIONS for area in safe_areas):
            raise ValueError("无效的文字安全区")
        for block in _list(shot.get("post_text", []), "后期文字"):
            block = _object(block, "后期文字项")
            if block.get("kind") not in TEXT_KINDS or block.get("position") not in TEXT_POSITIONS or block.get("style") not in TEXT_STYLES:
                raise ValueError("后期文字类型、位置或样式无效")
            _text(block.get("text"), "后期文字", required=True, maximum=200)
            semantic = block.get("bubble_semantic", "")
            if semantic and semantic not in BUBBLE_SEMANTICS:
                raise ValueError("无效的气泡语义类型")
            _text(block.get("bubble_asset_id", ""), "气泡样式 ID", maximum=80)
            if block.get("position") not in safe_areas:
                raise ValueError("后期文字位置必须包含在文字安全区中")

    _list(data.get("checklist", []), "checklist")
    if prompt_profile == "nai":
        for key, value in _object(data.get("world", {}), "world").items():
            if key in WORLD_FIELDS:
                _nai_english(value, f"world.{key}", maximum=4000)
    return data


def _next_id(preferred: str, used: set[str], prefix: str) -> str:
    if preferred not in used:
        used.add(preferred)
        return preferred
    numbers = [int(value[len(prefix):]) for value in used if value.startswith(prefix) and value[len(prefix):].isdigit()]
    candidate = f"{prefix}{max(numbers, default=0) + 1:03d}"
    while candidate in used:
        candidate = f"{prefix}{int(candidate[len(prefix):]) + 1:03d}"
    used.add(candidate)
    return candidate


def _character_record(source: dict[str, Any], final_id: str) -> dict[str, Any]:
    record = deepcopy(source)
    record.pop("client_id", None)
    record["id"] = final_id
    record["sourceFacts"] = record.pop("source_facts", [])
    record["aiSupplements"] = record.pop("ai_supplements", [])
    record["needsUserInput"] = record.pop("needs_user_input", [])
    record["referenceRequests"] = record.pop("reference_requests", [])
    return record


def _shot_record(source: dict[str, Any], final_id: str, character_map: dict[str, str], batch_id: str) -> dict[str, Any]:
    visual = deepcopy(source.get("visual") or {})
    character_ids = [character_map.get(value, value) for value in source.get("characters", [])]
    directions = {
        character_map.get(key, key): deepcopy(value)
        for key, value in (source.get("character_directions") or {}).items()
    }
    record = {key: deepcopy(value) for key, value in source.items() if key not in {"client_id", "characters", "character_directions", "visual", "source", "post_text", "text_safe_areas", "layout_meta"}}
    record.update({
        "id": final_id,
        "type": source.get("type", "Wide Shot"),
        "title": source.get("title", "新镜头"),
        "desc": source.get("description", ""),
        "status": "待制作",
        "source": {
            **deepcopy(source.get("source") or {}),
            "batchId": batch_id,
            "adaptationKind": (source.get("source") or {}).get("adaptation_kind", "direct"),
        },
        "postText": [
            {
                **deepcopy(block),
                "speakerId": character_map.get(block.get("speaker_id"), block.get("speaker_id", "")),
                "bubbleSemantic": block.get("bubble_semantic") or {
                    "speech": "dialogue", "thought": "thought", "caption": "narration", "sfx": "sfx"
                }.get(block.get("style"), "dialogue"),
                "bubbleAssetId": block.get("bubble_asset_id", ""),
            }
            for block in source.get("post_text", [])
        ],
        "textSafeAreas": deepcopy(source.get("text_safe_areas", [])),
        "warnings": deepcopy(source.get("warnings", [])),
        "layoutMeta": {
            **deepcopy(source.get("layout_meta") or {}),
            "containerType": (source.get("layout_meta") or {}).get("container_type", "single_panel"),
            "rowIndex": (source.get("layout_meta") or {}).get("row_index", 1),
            "slotIndex": (source.get("layout_meta") or {}).get("slot_index", 1),
            "gutterBottom": (source.get("layout_meta") or {}).get("gutter_bottom", 0),
            "borderStyle": (source.get("layout_meta") or {}).get("border_style", "none"),
            "insetConfig": deepcopy((source.get("layout_meta") or {}).get("inset_config")),
        },
        "content": {
            "shotId": final_id,
            "shotType": source.get("type", "Wide Shot"),
            "cameraAngle": visual.get("camera_angle", "Eye Level"),
            "dynamicExpression": visual.get("dynamic_expression", "still"),
            "panelLayout": visual.get("panel_layout", "single"),
            "panelBeats": deepcopy(visual.get("panel_beats") or [{"label": "第 1 格", "visual": ""}]),
            "aspectRatio": visual.get("aspect_ratio", "Auto"),
            "resolution": visual.get("resolution", "Auto"),
            "selectedCharacters": character_ids,
            "characterDirections": directions,
            "prompt": visual.get("prompt", ""),
            "scene": visual.get("scene", ""),
            "action": visual.get("action", ""),
            "expression": visual.get("expression", ""),
            "lighting": visual.get("lighting", ""),
            "style": visual.get("style", ""),
            "naiPositivePrompt": visual.get("nai_positive_prompt", ""),
            "naiNegativePrompt": visual.get("nai_negative_prompt", ""),
            "lastImage": "",
            "generationHistory": [],
        },
    })
    record["source"].pop("adaptation_kind", None)
    for block in record["postText"]:
        block.pop("speaker_id", None)
        block.pop("bubble_semantic", None)
        block.pop("bubble_asset_id", None)
    return record


def apply_manifest(base_state: dict[str, Any], manifest: dict[str, Any], *, append: bool) -> tuple[dict[str, Any], dict[str, str], dict[str, str], list[str]]:
    if append:
        incoming_profile = str(((manifest.get("preferences") or {}).get("prompt_profile") or "")).strip().lower()
        existing_profile = str(base_state.get("promptProfile") or "natural").strip().lower()
        if incoming_profile in PROMPT_PROFILES and incoming_profile != existing_profile:
            raise ValueError(f"项目提示词类型为 {existing_profile}，不能续接 {incoming_profile} 内容")
    data = validate_manifest(manifest, append=append)
    state = deepcopy(base_state) if append else {
        "activeView": "director", "shotId": "", "world": {}, "characters": [], "shots": [],
    }
    state.setdefault("world", {})
    state.setdefault("characters", [])
    state.setdefault("shots", [])
    state.setdefault("sourceBatches", [])
    state.setdefault("storyboardChecklist", [])
    preferences = deepcopy(data.get("preferences", {}))
    incoming_profile = preferences.get("prompt_profile", "natural")
    existing_profile = str(state.get("promptProfile") or "natural")
    if append and incoming_profile != existing_profile:
        raise ValueError(f"项目提示词类型为 {existing_profile}，不能续接 {incoming_profile} 内容")
    state["promptProfile"] = incoming_profile if not append else existing_profile
    state["storyboardPreferences"] = preferences

    warnings: list[str] = []
    imported_art_direction = {
        "stylePackId": preferences.get("style_pack_id", ""),
        "compiledPrompt": preferences.get("style_prompt", ""),
        "negativePrompt": preferences.get("style_negative_prompt", ""),
        "styleAnalysis": deepcopy(preferences.get("style_analysis", {})),
        "locked": True,
    }
    imported_lettering = {"bubblePackId": preferences.get("bubble_pack_id", "jp-clean-v1"), "locked": True}
    if append:
        incoming_style = imported_art_direction["stylePackId"]
        existing_style = (state.get("artDirection") or {}).get("stylePackId", "")
        if incoming_style and existing_style and incoming_style != existing_style:
            warnings.append("续写批次选择了不同画风，本次保留项目原画风")
        elif incoming_style and not existing_style:
            state["artDirection"] = imported_art_direction
        incoming_bubbles = imported_lettering["bubblePackId"]
        existing_bubbles = (state.get("lettering") or {}).get("bubblePackId", "")
        if incoming_bubbles and existing_bubbles and incoming_bubbles != existing_bubbles:
            warnings.append("续写批次选择了不同气泡包，本次保留项目原气泡包")
        elif incoming_bubbles and not existing_bubbles:
            state["lettering"] = imported_lettering
    else:
        state["artDirection"] = imported_art_direction
        state["lettering"] = imported_lettering
    if append:
        for key, value in (data.get("world") or {}).items():
            if key in WORLD_FIELDS and value and not state["world"].get(key):
                state["world"][key] = deepcopy(value)
            elif key in WORLD_FIELDS and value and state["world"].get(key) != value:
                warnings.append(f"世界观字段 {key} 已有内容，本次未覆盖")
    else:
        state["world"] = deepcopy(data.get("world") or {})

    existing_character_ids = {item.get("id") for item in state["characters"] if isinstance(item, dict) and item.get("id")}
    declared_existing = set(data.get("existing_character_ids", []))
    missing_existing = declared_existing - existing_character_ids
    if missing_existing:
        raise ValueError(f"续接引用了不存在的角色：{', '.join(sorted(missing_existing))}")
    character_map = {value: value for value in declared_existing}
    for character in data.get("characters", []):
        final_id = _next_id(character["client_id"], existing_character_ids, "CHR-")
        character_map[character["client_id"]] = final_id
        state["characters"].append(_character_record(character, final_id))

    used_shot_ids = {item.get("id") for item in state["shots"] if isinstance(item, dict) and item.get("id")}
    shot_map: dict[str, str] = {}
    batch_id = data["source_batch"]["batch_id"]
    for shot in data["shots"]:
        final_id = _next_id(shot["client_id"], used_shot_ids, "SHOT-")
        shot_map[shot["client_id"]] = final_id
        state["shots"].append(_shot_record(shot, final_id, character_map, batch_id))

    batch = deepcopy(data["source_batch"])
    batch["preferences"] = deepcopy(data.get("preferences", {}))
    state["sourceBatches"].append(batch)
    for item in data.get("checklist", []):
        mapped = deepcopy(item)
        owner = mapped.get("owner_client_id")
        mapped["ownerId"] = character_map.get(owner, shot_map.get(owner, owner))
        mapped.pop("owner_client_id", None)
        mapped["blocking"] = bool(mapped.get("blocking", False))
        state["storyboardChecklist"].append(mapped)
    if not state.get("shotId") and state["shots"]:
        state["shotId"] = state["shots"][0]["id"]
    return state, {key: value for key, value in character_map.items() if key not in declared_existing}, shot_map, warnings


def patch_shot(state: dict[str, Any], shot_id: str, patch: dict[str, Any], allow_generated: bool) -> dict[str, Any]:
    next_state = deepcopy(state)
    shot = next((item for item in next_state.get("shots", []) if item.get("id") == shot_id), None)
    if shot is None:
        raise KeyError(shot_id)
    history = ((shot.get("content") or {}).get("generationHistory") or [])
    if history and not allow_generated:
        raise PermissionError("该镜头已有生成记录；确认后才能修订")
    data = deepcopy(_object(patch, "patch"))
    if "description" in data:
        shot["desc"] = _text(data.pop("description"), "镜头说明", required=True, maximum=1000)
    for key in ("title", "type", "warnings"):
        if key in data:
            shot[key] = data.pop(key)
    visual = data.pop("visual", None)
    if visual is not None:
        content = shot.setdefault("content", {})
        visual_map = {"camera_angle": "cameraAngle", "dynamic_expression": "dynamicExpression", "panel_layout": "panelLayout", "panel_beats": "panelBeats", "aspect_ratio": "aspectRatio", "resolution": "resolution", "prompt": "prompt", "scene": "scene", "action": "action", "expression": "expression", "lighting": "lighting", "style": "style", "nai_positive_prompt": "naiPositivePrompt", "nai_negative_prompt": "naiNegativePrompt"}
        for key, value in _object(visual, "visual patch").items():
            if key in visual_map:
                content[visual_map[key]] = deepcopy(value)
            else:
                content[key] = deepcopy(value)
    if "layout_meta" in data:
        layout = _layout_meta(data.pop("layout_meta"), "layout_meta patch")
        shot["layoutMeta"] = {
            **deepcopy(layout),
            "containerType": layout.get("container_type", "single_panel"),
            "rowIndex": layout.get("row_index", 1),
            "slotIndex": layout.get("slot_index", 1),
            "gutterBottom": layout.get("gutter_bottom", 0),
            "borderStyle": layout.get("border_style", "none"),
            "insetConfig": deepcopy(layout.get("inset_config")),
        }
    if "source" in data:
        source = deepcopy(data.pop("source"))
        if "adaptation_kind" in source:
            source["adaptationKind"] = source.pop("adaptation_kind")
        shot["source"] = {**(shot.get("source") or {}), **source}
    if "post_text" in data:
        shot["postText"] = [
            {
                **deepcopy(item),
                "speakerId": item.get("speaker_id", ""),
                "bubbleSemantic": item.get("bubble_semantic") or {
                    "speech": "dialogue", "thought": "thought", "caption": "narration", "sfx": "sfx"
                }.get(item.get("style"), "dialogue"),
                "bubbleAssetId": item.get("bubble_asset_id", ""),
            }
            for item in data.pop("post_text")
        ]
        for item in shot["postText"]:
            item.pop("speaker_id", None)
            item.pop("bubble_semantic", None)
            item.pop("bubble_asset_id", None)
    if "text_safe_areas" in data:
        shot["textSafeAreas"] = deepcopy(data.pop("text_safe_areas"))
    for key, value in data.items():
        shot[key] = deepcopy(value)
    return next_state
