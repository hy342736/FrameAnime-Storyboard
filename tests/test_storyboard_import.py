import asyncio
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import httpx

import app.main as main
from app.config import Settings
from app.main import app
from app.storage import WorkspaceStorage


def make_storage(root: Path) -> WorkspaceStorage:
    settings = Settings(
        data_dir=root / "data",
        mirror_url="",
        mirror_chat_url="",
        headless=True,
        browser_profile_dir=root / "profile",
        image_dir=root / "generated",
        reference_dir=root / "references",
        generation_timeout_seconds=60,
        local_api_key="",
    )
    settings.image_dir.mkdir(parents=True)
    settings.reference_dir.mkdir(parents=True)
    return WorkspaceStorage(settings)


def batch(batch_id: str, text: str) -> dict:
    return {
        "batch_id": batch_id,
        "source_title": "测试短篇",
        "source_file": "story.txt",
        "selected_text": text,
        "start_quote": text.split("。", 1)[0] + "。",
        "end_quote": text.rsplit("。", 2)[-2] + "。",
        "char_count": len(text),
    }


def shot(client_id: str, anchor: str, character_id: str) -> dict:
    return {
        "client_id": client_id,
        "type": "Medium Shot",
        "title": "递出信封",
        "description": "莉亚将信封递到寒色面前。",
        "characters": [character_id],
        "character_directions": {
            character_id: {"position": "画面左侧", "action": "递出信封", "expression": "迟疑"}
        },
        "visual": {
            "mode": "Storyboard Mode",
            "camera_angle": "Eye Level",
            "camera_move": "Static",
            "aspect_ratio": "3:4",
            "resolution": "Auto",
            "prompt": "角色左侧，右上保留干净对白区，不绘制文字",
            "scene": "旧站台 / 深夜 / 小雨",
            "action": "递出信封",
            "expression": "克制的迟疑",
            "lighting": "冷蓝月光与暖黄站灯",
            "style": "清晰彩色动画插画",
        },
        "source": {"anchor": anchor, "adaptation_kind": "direct"},
        "post_text": [
            {"kind": "dialogue", "text": "这封信给你。", "speaker_id": character_id, "position": "top-right", "style": "speech"}
        ],
        "text_safe_areas": ["top-right"],
        "layout_meta": {
            "container_type": "split_row_2",
            "row_index": 1,
            "slot_index": 1,
            "gutter_bottom": 80,
            "border_style": "solid_black_2px",
            "inset_config": None,
        },
        "warnings": [],
    }


def new_manifest() -> dict:
    text = "莉亚在雨夜站台等候。列车灯掠过时，她将信封递到寒色面前。"
    return {
        "schema_version": 1,
        "project": {"name": "雨夜来信", "description": "短篇分镜测试"},
        "preferences": {
            "prompt_profile": "natural",
            "format": "vertical_comic",
            "panel_budget": 1,
            "adaptation_mode": "faithful",
            "character_mode": "user",
            "style_mode": "color_anime",
            "style_pack_id": "modern-seinen-v1",
            "style_prompt": "清晰彩色动画插画",
            "style_negative_prompt": "可读文字，水印",
            "style_analysis": {"linework": "清晰线稿"},
            "bubble_pack_id": "jp-clean-v1",
        },
        "source_batch": batch("BATCH-001", text),
        "world": {"name": "雾港", "era": "近未来", "visual": "冷蓝雨夜与暖黄灯光"},
        "characters": [
            {
                "client_id": "CHR-001",
                "name": "莉亚",
                "role": "守望者",
                "faction": "",
                "personality": "沉静",
                "appearance": "",
                "costume": "",
                "signature": "",
                "source_facts": ["在雨夜站台等候"],
                "ai_supplements": [],
                "needs_user_input": ["补充外貌与服装"],
                "reference_requests": ["上传正面角色设定图"],
            }
        ],
        "shots": [shot("SHOT-001", "列车灯掠过时，她将信封递到寒色面前。", "CHR-001")],
        "checklist": [
            {"kind": "character_reference", "owner_client_id": "CHR-001", "message": "上传正面角色设定图", "blocking": False}
        ],
    }


def manifest_with_panel_count(count: int) -> dict:
    manifest = new_manifest()
    template = manifest["shots"][0]
    manifest["preferences"]["panel_budget"] = count
    manifest["shots"] = []
    for index in range(count):
        item = deepcopy(template)
        item["client_id"] = f"SHOT-{index + 1:03d}"
        item["layout_meta"]["row_index"] = index + 1
        manifest["shots"].append(item)
    return manifest


def append_manifest() -> dict:
    text = "寒色没有接信。他抬头看向远处熄灭的灯塔。"
    return {
        "schema_version": 1,
        "preferences": {
            "prompt_profile": "natural", "format": "vertical_comic", "panel_budget": 1, "adaptation_mode": "faithful", "character_mode": "user"
        },
        "source_batch": batch("BATCH-002", text),
        "existing_character_ids": ["CHR-001"],
        "characters": [],
        "shots": [shot("SHOT-001", "他抬头看向远处熄灭的灯塔。", "CHR-001")],
        "checklist": [],
    }


class StoryboardImportTests(unittest.TestCase):
    def request(self, storage: WorkspaceStorage, method: str, path: str, json=None):
        async def send():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8001") as client:
                return await client.request(method, path, json=json)

        with patch("app.main.storage", storage):
            return asyncio.run(send())

    def test_capabilities_and_create_persist_storyboard_contract(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-create-") as directory:
            storage = make_storage(Path(directory))
            with patch("app.main.settings", storage.settings):
                capabilities = self.request(storage, "GET", "/api/import/storyboard/capabilities")
            self.assertEqual(200, capabilities.status_code)
            self.assertEqual(
                {
                    "app_name": "FrameAnimeDesk",
                    "app_version": "0.3.0",
                    "runtime_mode": "development",
                    "storyboard_import": True,
                    "storyboard_import_protocol_version": 1,
                    "storyboard_import_max_shots": 50,
                    "schema_versions": [1],
                    "project_revision": True,
                    "deep_link": True,
                    "style_packs": True,
                    "custom_style_packs": True,
                    "bubble_packs": True,
                    "exports": ["png_bundle", "vertical_comic", "pdf", "video"],
                    "generation": {
                        "mode": "mirror",
                        "channel": "镜像站浏览器",
                        "model": "",
                        "protocol": "browser",
                        "prompt_profile": "unknown",
                        "configured_prompt_profile": "unknown",
                        "supports_reference_images": True,
                    },
                },
                capabilities.json(),
            )

            response = self.request(storage, "POST", "/api/import/storyboard/projects", new_manifest())
            self.assertEqual(201, response.status_code, response.text)
            result = response.json()
            self.assertEqual(1, result["revision"])
            self.assertEqual({"CHR-001": "CHR-001"}, result["created_character_ids"])
            self.assertEqual({"SHOT-001": "SHOT-001"}, result["created_shot_ids"])
            self.assertEqual(f"http://127.0.0.1:8001/?project_id={result['project_id']}", result["open_url"])

            project = storage.get_project(result["project_id"])
            state = project["state"]
            self.assertEqual("BATCH-001", state["sourceBatches"][0]["batch_id"])
            self.assertEqual("natural", state["promptProfile"])
            self.assertEqual("direct", state["shots"][0]["source"]["adaptationKind"])
            self.assertEqual("列车灯掠过时，她将信封递到寒色面前。", state["shots"][0]["source"]["anchor"])
            self.assertEqual("这封信给你。", state["shots"][0]["postText"][0]["text"])
            self.assertEqual("dialogue", state["shots"][0]["postText"][0]["bubbleSemantic"])
            self.assertEqual(["top-right"], state["shots"][0]["textSafeAreas"])
            self.assertEqual("split_row_2", state["shots"][0]["layoutMeta"]["containerType"])
            self.assertEqual(80, state["shots"][0]["layoutMeta"]["gutterBottom"])
            self.assertEqual("solid_black_2px", state["shots"][0]["layoutMeta"]["borderStyle"])
            self.assertEqual("modern-seinen-v1", state["artDirection"]["stylePackId"])
            self.assertEqual("清晰彩色动画插画", state["artDirection"]["compiledPrompt"])
            self.assertEqual("jp-clean-v1", state["lettering"]["bubblePackId"])
            self.assertFalse(state["storyboardChecklist"][0]["blocking"])
            self.assertEqual([], state["shots"][0]["content"]["generationHistory"])

    def test_nai_manifest_persists_english_prompt_contract(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-nai-create-") as directory:
            storage = make_storage(Path(directory))
            manifest = new_manifest()
            manifest["preferences"].update({
                "prompt_profile": "nai",
                "style_prompt": "clean lineart, cel shading, muted colors",
                "style_negative_prompt": "photorealistic, 3d, text, watermark",
                "style_analysis": {"linework": "clean lineart", "coloring": "two-level cel shading"},
            })
            manifest["world"] = {
                "name": "Mist Harbor",
                "era": "near future",
                "visual": "cool rainy night, warm station lights",
            }
            character = manifest["characters"][0]
            character.update({
                "role": "lighthouse keeper",
                "personality": "quiet, persistent",
                "appearance": "adult woman, long silver hair, gray-blue eyes",
                "costume": "dark navy coat, black ankle boots",
                "signature": "star-shaped earring",
            })
            shot_data = manifest["shots"][0]
            shot_data["character_directions"]["CHR-001"] = {
                "position": "frame left, facing right",
                "action": "offers a sealed envelope",
                "expression": "restrained hesitation",
            }
            shot_data["visual"].update({
                "prompt": "reserve a clean speech area in the upper right",
                "scene": "old railway platform, rainy night",
                "action": "offering a sealed envelope",
                "expression": "restrained hesitation",
                "lighting": "cool moonlight, warm station lamp",
                "style": "clean color anime illustration",
                "nai_positive_prompt": "1girl, adult woman, long silver hair, gray-blue eyes, dark navy coat, old railway platform, rainy night, medium shot",
                "nai_negative_prompt": "bad anatomy, bad hands, extra fingers, text, watermark",
            })

            response = self.request(storage, "POST", "/api/import/storyboard/projects", manifest)

            self.assertEqual(201, response.status_code, response.text)
            state = storage.get_project(response.json()["project_id"])["state"]
            self.assertEqual("nai", state["promptProfile"])
            self.assertIn("long silver hair", state["shots"][0]["content"]["naiPositivePrompt"])
            self.assertIn("bad anatomy", state["shots"][0]["content"]["naiNegativePrompt"])

    def test_nai_manifest_rejects_chinese_generation_fields(self):
        manifest = new_manifest()
        manifest["preferences"]["prompt_profile"] = "nai"
        manifest["preferences"]["style_prompt"] = "清晰动画线稿"
        manifest["shots"][0]["visual"]["nai_positive_prompt"] = "1girl, 银白长发"
        manifest["shots"][0]["visual"]["nai_negative_prompt"] = "text, watermark"

        with self.assertRaisesRegex(ValueError, "NAI 项目的生图字段必须使用英文"):
            main.validate_manifest(manifest)

    def test_layout_metadata_rejects_invalid_values(self):
        manifest = new_manifest()
        manifest["shots"][0]["layout_meta"]["container_type"] = "freeform_grid"
        manifest["shots"][0]["layout_meta"]["inset_config"] = {"x": 1.2, "y": 0, "width": 1, "height": 1}
        with self.assertRaisesRegex(ValueError, "container_type 无效"):
            main.validate_manifest(manifest)

        manifest = new_manifest()
        manifest["shots"][0]["layout_meta"]["inset_config"] = {"x": 1.2, "y": 0, "width": 1, "height": 1}
        with self.assertRaisesRegex(ValueError, "inset_config.x 必须是 0 到 1 的数字"):
            main.validate_manifest(manifest)

    def test_legacy_shot_without_layout_metadata_defaults_to_single_panel(self):
        manifest = new_manifest()
        manifest["shots"][0].pop("layout_meta")
        state, _, _, _ = main.apply_manifest({}, manifest, append=False)
        layout = state["shots"][0]["layoutMeta"]
        self.assertEqual("single_panel", layout["containerType"])
        self.assertEqual(1, layout["rowIndex"])
        self.assertEqual(0, layout["gutterBottom"])

    def test_append_rejects_prompt_profile_change(self):
        state, _, _, _ = main.apply_manifest({}, new_manifest(), append=False)
        continuation = append_manifest()
        continuation["preferences"]["prompt_profile"] = "nai"

        with self.assertRaisesRegex(ValueError, "项目提示词类型"):
            main.apply_manifest(state, continuation, append=True)

    def test_capabilities_expose_resolved_nai_generation_profile(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-capabilities-nai-") as directory:
            storage = make_storage(Path(directory))
            changes = {
                "generation_mode": "api",
                "image_api_name": "Anime API",
                "image_api_protocol": "images",
                "image_api_model": "nai-diffusion-5-curated",
                "image_api_prompt_profile": "auto",
            }
            originals = {key: getattr(main.settings, key) for key in changes}
            try:
                for key, value in changes.items():
                    setattr(main.settings, key, value)
                capabilities = self.request(storage, "GET", "/api/import/storyboard/capabilities")
            finally:
                for key, value in originals.items():
                    setattr(main.settings, key, value)

            self.assertEqual(200, capabilities.status_code)
            self.assertEqual(
                {
                    "mode": "api",
                    "channel": "Anime API",
                    "model": "nai-diffusion-5-curated",
                    "protocol": "images",
                    "prompt_profile": "nai",
                    "configured_prompt_profile": "auto",
                    "supports_reference_images": False,
                },
                capabilities.json()["generation"],
            )
    def test_panel_budget_accepts_fifty_and_rejects_invalid_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-budget-") as directory:
            storage = make_storage(Path(directory))
            manifest = new_manifest()
            accepted = self.request(storage, "POST", "/api/import/storyboard/projects", manifest)
            self.assertEqual(201, accepted.status_code, accepted.text)

            maximum = manifest_with_panel_count(50)
            accepted_maximum = self.request(storage, "POST", "/api/import/storyboard/projects", maximum)
            self.assertEqual(201, accepted_maximum.status_code, accepted_maximum.text)
            self.assertEqual(50, len(accepted_maximum.json()["created_shot_ids"]))

            over_limit = new_manifest()
            over_limit["preferences"]["panel_budget"] = 51
            rejected_limit = self.request(storage, "POST", "/api/import/storyboard/projects", over_limit)
            self.assertEqual(400, rejected_limit.status_code, rejected_limit.text)
            self.assertIn("1 到 50", rejected_limit.text)

            missing = new_manifest()
            missing["preferences"].pop("panel_budget")
            rejected_missing = self.request(storage, "POST", "/api/import/storyboard/projects", missing)
            self.assertEqual(400, rejected_missing.status_code, rejected_missing.text)
            self.assertIn("panel_budget", rejected_missing.text)

            mismatch = new_manifest()
            mismatch["preferences"]["panel_budget"] = 2
            rejected = self.request(storage, "POST", "/api/import/storyboard/projects", mismatch)
            self.assertEqual(400, rejected.status_code, rejected.text)
            self.assertIn("完全一致", rejected.text)

    def test_stale_append_is_409_and_workspace_is_byte_identical(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-conflict-") as directory:
            storage = make_storage(Path(directory))
            created = self.request(storage, "POST", "/api/import/storyboard/projects", new_manifest()).json()
            project_id = created["project_id"]
            state_with_history = deepcopy(storage.get_project(project_id)["state"])
            state_with_history["shots"][0]["content"]["generationHistory"] = [{"id": "existing-generation"}]
            state_with_history["future_import_field"] = {"preserve": True}
            storage.update_project(project_id, state=state_with_history)
            storage.add_reference(
                project_id=project_id,
                owner_type="character",
                owner_id="CHR-001",
                file_name="identity.png",
                mime_type="image/png",
                content=b"identity",
                reference_type="character_design",
            )
            before = storage.workspace_file.read_bytes()

            response = self.request(
                storage,
                "POST",
                f"/api/import/storyboard/projects/{project_id}/append",
                {"expected_revision": created["revision"], "manifest": append_manifest()},
            )
            self.assertEqual(409, response.status_code, response.text)
            self.assertEqual(before, storage.workspace_file.read_bytes())
            state = storage.get_project(project_id)["state"]
            self.assertEqual(1, len(state["shots"]))
            self.assertEqual(1, len(state["characters"]))
            self.assertEqual([{"id": "existing-generation"}], state["shots"][0]["content"]["generationHistory"])
            self.assertEqual({"preserve": True}, state["future_import_field"])
            self.assertEqual("雾港", state["world"]["name"])
            self.assertEqual(1, len(storage.list_references(project_id)))

    def test_append_assigns_collision_free_ids_without_overwriting(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-append-") as directory:
            storage = make_storage(Path(directory))
            created = self.request(storage, "POST", "/api/import/storyboard/projects", new_manifest()).json()
            response = self.request(
                storage,
                "POST",
                f"/api/import/storyboard/projects/{created['project_id']}/append",
                {"expected_revision": 1, "manifest": append_manifest()},
            )
            self.assertEqual(200, response.status_code, response.text)
            result = response.json()
            self.assertEqual(2, result["revision"])
            self.assertEqual({"SHOT-001": "SHOT-002"}, result["created_shot_ids"])
            state = storage.get_project(created["project_id"])["state"]
            self.assertEqual(["SHOT-001", "SHOT-002"], [item["id"] for item in state["shots"]])
            self.assertEqual(["BATCH-001", "BATCH-002"], [item["batch_id"] for item in state["sourceBatches"]])

    def test_stale_regular_editor_save_cannot_overwrite_appended_state(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-editor-conflict-") as directory:
            storage = make_storage(Path(directory))
            created = self.request(storage, "POST", "/api/import/storyboard/projects", new_manifest()).json()
            project_id = created["project_id"]
            appended = self.request(
                storage,
                "POST",
                f"/api/import/storyboard/projects/{project_id}/append",
                {"expected_revision": 1, "manifest": append_manifest()},
            )
            self.assertEqual(200, appended.status_code, appended.text)
            before = storage.workspace_file.read_bytes()

            stale_state = deepcopy(storage.get_project(project_id)["state"])
            stale_state["shots"] = stale_state["shots"][:1]
            response = self.request(
                storage,
                "PATCH",
                f"/api/projects/{project_id}",
                {"expected_revision": 1, "state": stale_state},
            )
            self.assertEqual(409, response.status_code, response.text)
            self.assertEqual(before, storage.workspace_file.read_bytes())
            self.assertEqual(2, len(storage.get_project(project_id)["state"]["shots"]))

    def test_generated_shot_revision_requires_override_and_preserves_history(self):
        with tempfile.TemporaryDirectory(prefix="storyboard-revision-") as directory:
            storage = make_storage(Path(directory))
            created = self.request(storage, "POST", "/api/import/storyboard/projects", new_manifest()).json()
            project_id = created["project_id"]
            project = storage.get_project(project_id)
            state = deepcopy(project["state"])
            history = [{"id": "generation-1", "url": "/generated/original.png"}]
            state["shots"][0]["content"]["generationHistory"] = deepcopy(history)
            project = storage.update_project(project_id, state=state)

            rejected = self.request(
                storage,
                "PATCH",
                f"/api/import/storyboard/projects/{project_id}/shots/SHOT-001",
                {"expected_revision": project["revision"], "patch": {"description": "调整后的镜头"}},
            )
            self.assertEqual(409, rejected.status_code, rejected.text)
            self.assertEqual(history, storage.get_project(project_id)["state"]["shots"][0]["content"]["generationHistory"])

            accepted = self.request(
                storage,
                "PATCH",
                f"/api/import/storyboard/projects/{project_id}/shots/SHOT-001",
                {
                    "expected_revision": project["revision"],
                    "allow_generated_shot_change": True,
                    "patch": {"description": "调整后的镜头", "visual": {"camera_angle": "Low Angle"}},
                },
            )
            self.assertEqual(200, accepted.status_code, accepted.text)
            revised = storage.get_project(project_id)["state"]["shots"][0]
            self.assertEqual("调整后的镜头", revised["desc"])
            self.assertEqual("Low Angle", revised["content"]["cameraAngle"])
            self.assertEqual(history, revised["content"]["generationHistory"])


if __name__ == "__main__":
    unittest.main()
