import unittest
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app import main
from app.api_image_client import ApiGenerationResult
from app.browser_session import GenerationResult
from app.config import Settings
from app.storage import WorkspaceStorage


class AgentMultiPanelPromptTests(unittest.TestCase):
    prompt = (
        "A cinematic 3-panel horizontal filmstrip layout, side by side with thin borders, "
        "featuring the same character across all panels: a young woman with silver hair, "
        "blue coat, star earring. Panel 1 (left): she raises a lantern. "
        "Panel 2 (center): she passes an envelope. Panel 3 (right): she turns away. "
        "Clean 2D anime line art, clean panels, no text, no gibberish speech bubbles, "
        "no logo, no watermark, --ar 16:9"
    )

    def test_accepts_complete_agent_prompt_with_matching_ratio(self):
        self.assertTrue(main.is_agent_multi_panel_prompt(self.prompt))
        main.validate_agent_multi_panel_prompt(self.prompt, "16:9")

    def test_rejects_auto_or_mismatched_canvas_ratio(self):
        for ratio in ("Auto", "3:4"):
            with self.subTest(ratio=ratio), self.assertRaises(HTTPException) as captured:
                main.validate_agent_multi_panel_prompt(self.prompt, ratio)
            self.assertEqual(400, captured.exception.status_code)
            self.assertIn("比例", captured.exception.detail)

    def test_rejects_non_english_or_missing_position(self):
        invalid = self.prompt.replace("Panel 2 (center):", "Panel 2:").replace("she turns away", "她转身离开")
        with self.assertRaises(HTTPException) as captured:
            main.validate_agent_multi_panel_prompt(invalid, "16:9")
        self.assertIn("Panel 2", captured.exception.detail)
        self.assertIn("英文", captured.exception.detail)


class CharacterReferenceStorage:
    def __init__(self, complete_second_character=False):
        self.complete_second_character = complete_second_character

    def get_reference(self, reference_id):
        if reference_id == "ref-char-1":
            return {
                "id": reference_id,
                "project_id": "project-test",
                "owner_type": "character",
                "owner_id": "CHR-001",
                "enabled": True,
            }
        return None

    def reference_file(self, _reference_id):
        return Path(__file__)

    def get_conversation_binding(self, _project_id):
        return None

    def set_conversation_binding(self, project_id, *, url, title=""):
        return {"project_id": project_id, "url": url, "title": title}

    def get_project(self, project_id):
        if project_id != "project-test":
            return None
        return {
            "id": project_id,
            "state": {
                "characters": [
                    {
                        "id": "CHR-001",
                        "name": "角色一",
                        "appearance": "短黑发，窄脸，成年男性，中等身形",
                        "costume": "深灰夹克与黑色长裤",
                        "signature": "银色旧手表",
                    },
                    {
                        "id": "CHR-002",
                        "name": "角色二",
                        "appearance": "棕色长发，圆脸，成年女性，纤细身形"
                        if self.complete_second_character
                        else "原文未提供稳定外貌特征，待用户补充。",
                        "costume": "米白风衣与深蓝围巾" if self.complete_second_character else "",
                        "signature": "旧皮革文件袋" if self.complete_second_character else "",
                    },
                ]
            },
        }


class GenerationContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_mirror_generation_auto_binds_and_reuses_project_conversation(self):
        class BindingMirrorSession:
            def __init__(self, output):
                self.output = output
                self.conversation_urls = []

            async def generate(self, prompt, project_id, reference_paths, require_all_references, conversation_url=""):
                self.conversation_urls.append(conversation_url)
                return GenerationResult(
                    self.output,
                    conversation_url=conversation_url or "https://example.test/c/project-conversation",
                )

        with tempfile.TemporaryDirectory(prefix="anime-desk-conversation-route-") as directory:
            root = Path(directory)
            settings = Settings(
                data_dir=root / "data",
                mirror_url="https://example.test",
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
            storage = WorkspaceStorage(settings)
            project = storage.create_project("绑定测试")
            output = settings.image_dir / project["id"] / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"\x89PNG\r\n\x1a\nresult")
            fake_session = BindingMirrorSession(output)
            originals = (main.settings.generation_mode, main.settings.image_dir, main.storage, main.session)
            main.settings.generation_mode = "mirror"
            main.settings.image_dir = settings.image_dir
            main.storage = storage
            main.session = fake_session
            try:
                request = main.GenerateRequest(prompt="draw", project_id=project["id"])
                first = await main.generate(request)
                second = await main.generate(request)
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.storage, main.session = originals

            self.assertEqual(["", "https://example.test/c/project-conversation"], fake_session.conversation_urls)
            self.assertEqual("bound", first["conversation_status"])
            self.assertEqual("https://example.test/c/project-conversation", second["conversation_url"])
            self.assertEqual(
                "https://example.test/c/project-conversation",
                storage.get_conversation_binding(project["id"])["url"],
            )

    async def test_failed_first_generation_still_binds_the_created_conversation(self):
        class FailingNewConversationSession:
            async def generate(self, prompt, project_id, reference_paths, require_all_references, conversation_url=""):
                self.conversation_url = conversation_url
                error = RuntimeError("provider failed after prompt submission")
                error.conversation_url = "https://example.test/c/failed-generation-chat"
                raise error

        with tempfile.TemporaryDirectory(prefix="anime-desk-failed-conversation-bind-") as directory:
            root = Path(directory)
            settings = Settings(
                data_dir=root / "data",
                mirror_url="https://example.test",
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
            storage = WorkspaceStorage(settings)
            project = storage.create_project("失败后绑定测试")
            fake_session = FailingNewConversationSession()
            originals = (main.settings.generation_mode, main.settings.image_dir, main.storage, main.session)
            main.settings.generation_mode = "mirror"
            main.settings.image_dir = settings.image_dir
            main.storage = storage
            main.session = fake_session
            try:
                with self.assertRaises(HTTPException) as captured:
                    await main.generate(main.GenerateRequest(prompt="draw", project_id=project["id"]))
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.storage, main.session = originals

            self.assertEqual(502, captured.exception.status_code)
            self.assertEqual("", fake_session.conversation_url)
            self.assertEqual(
                "https://example.test/c/failed-generation-chat",
                storage.get_conversation_binding(project["id"])["url"],
            )

    async def test_response_reports_the_channel_that_actually_executed(self):
        class EmptyStorage:
            def get_reference(self, _reference_id):
                return None

            def get_project(self, _project_id):
                return None

        class SwitchingMirrorSession:
            async def generate(self, *args, **kwargs):
                main.settings.generation_mode = "api"
                return ApiGenerationResult(output)

        class FailingApiClient:
            async def generate(self, *args, **kwargs):
                raise AssertionError("API client must not run for a mirror request")

        with tempfile.TemporaryDirectory(prefix="anime-desk-mirror-route-") as directory:
            root = Path(directory)
            output = root / "project-test" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"\x89PNG\r\n\x1a\nresult")
            originals = (main.settings.generation_mode, main.settings.image_dir, main.storage, main.session, main.api_image_client)
            main.settings.generation_mode = "mirror"
            main.settings.image_dir = root
            main.storage = EmptyStorage()
            main.session = SwitchingMirrorSession()
            main.api_image_client = FailingApiClient()
            try:
                result = await main.generate(main.GenerateRequest(prompt="draw", project_id="project-test"))
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.storage, main.session, main.api_image_client = originals

            self.assertEqual("mirror", result["generation_mode"])
            self.assertEqual("镜像站浏览器", result["generation_channel"])
            self.assertEqual("", result["generation_model"])

    async def test_multi_character_generation_requires_dna_when_reference_is_missing(self):
        originals = (main.settings.generation_mode, main.storage)
        main.settings.generation_mode = "mirror"
        main.storage = CharacterReferenceStorage()
        request = main.GenerateRequest(
            prompt="two characters",
            project_id="project-test",
            shot_id="SHOT-001",
            reference_ids=["ref-char-1"],
            selected_character_ids=["CHR-001", "CHR-002"],
        )
        try:
            with self.assertRaises(HTTPException) as captured:
                await main.generate(request)
        finally:
            main.settings.generation_mode, main.storage = originals

        self.assertEqual(400, captured.exception.status_code)
        self.assertIn("CHR-002", captured.exception.detail)
        self.assertIn("补全", captured.exception.detail)

    async def test_multi_character_generation_allows_complete_text_dna_without_references(self):
        class FakeMirrorSession:
            def __init__(self, output):
                self.output = output
                self.call = None

            async def generate(self, prompt, project_id, reference_paths, require_all_references, conversation_url=""):
                self.call = {
                    "prompt": prompt,
                    "project_id": project_id,
                    "reference_paths": reference_paths,
                    "require_all_references": require_all_references,
                    "conversation_url": conversation_url,
                }
                return ApiGenerationResult(self.output)

        with tempfile.TemporaryDirectory(prefix="anime-desk-text-dna-") as directory:
            root = Path(directory)
            output = root / "project-test" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"\x89PNG\r\n\x1a\nresult")
            fake_session = FakeMirrorSession(output)
            originals = (main.settings.generation_mode, main.settings.image_dir, main.storage, main.session)
            main.settings.generation_mode = "mirror"
            main.settings.image_dir = root
            main.storage = CharacterReferenceStorage(complete_second_character=True)
            main.session = fake_session
            try:
                result = await main.generate(
                    main.GenerateRequest(
                        prompt="two text-defined characters",
                        project_id="project-test",
                        shot_id="SHOT-001",
                        selected_character_ids=["CHR-001", "CHR-002"],
                    )
                )
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.storage, main.session = originals

            self.assertEqual([], fake_session.call["reference_paths"])
            self.assertFalse(fake_session.call["require_all_references"])
            self.assertIn("CHR-001、CHR-002", result["reference_warning"])
            self.assertIn("一致性可能较弱", result["reference_warning"])

    async def test_api_mode_routes_generation_without_using_browser_session(self):
        class EmptyStorage:
            def get_reference(self, _reference_id):
                return None

            def get_project(self, _project_id):
                return None

        class FakeApiClient:
            def __init__(self, output):
                self.output = output
                self.call = None

            def resolved_prompt_profile(self):
                return "natural"

            async def generate(
                self,
                prompt,
                project_id,
                reference_paths,
                aspect_ratio,
                resolution,
                style_prompt="",
                style_negative_prompt="",
            ):
                main.settings.generation_mode = "mirror"
                self.call = {
                    "prompt": prompt,
                    "project_id": project_id,
                    "reference_paths": reference_paths,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "style_prompt": style_prompt,
                    "style_negative_prompt": style_negative_prompt,
                }
                return ApiGenerationResult(self.output)

        class FailingBrowserSession:
            async def generate(self, *args, **kwargs):
                raise AssertionError("browser session must not be used in API mode")

        with tempfile.TemporaryDirectory(prefix="anime-desk-api-route-") as directory:
            root = Path(directory)
            output = root / "project-test" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"\x89PNG\r\n\x1a\nresult")
            fake_client = FakeApiClient(output)
            originals = (main.settings.generation_mode, main.settings.image_dir, main.settings.image_api_name, main.settings.image_api_model, main.storage, main.session, main.api_image_client)
            main.settings.generation_mode = "api"
            main.settings.image_dir = root
            main.settings.image_api_name = "Test API Node"
            main.settings.image_api_model = "test-image-model"
            main.storage = EmptyStorage()
            main.session = FailingBrowserSession()
            main.api_image_client = fake_client
            try:
                result = await main.generate(
                    main.GenerateRequest(
                        prompt="draw",
                        project_id="project-test",
                        aspect_ratio="16:9",
                        resolution="2K",
                    )
                )
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.settings.image_api_name, main.settings.image_api_model, main.storage, main.session, main.api_image_client = originals

            self.assertEqual("api", result["generation_mode"])
            self.assertEqual("Test API Node", result["generation_channel"])
            self.assertEqual("test-image-model", result["generation_model"])
            self.assertEqual("16:9", fake_client.call["aspect_ratio"])
            self.assertEqual("2K", fake_client.call["resolution"])
            self.assertEqual("/images/project-test/generated/result.png", result["url"])

    async def test_api_mode_rejects_project_and_model_prompt_profile_mismatch(self):
        class NaiProjectStorage:
            def get_project(self, _project_id):
                return {"id": "project-test", "state": {"promptProfile": "nai", "artDirection": {"locked": False}}}

            def get_reference(self, _reference_id):
                return None

        class NaturalApiClient:
            def resolved_prompt_profile(self):
                return "natural"

            async def generate(self, *args, **kwargs):
                raise AssertionError("mismatched project must not reach the provider")

        originals = (main.settings.generation_mode, main.storage, main.api_image_client)
        main.settings.generation_mode = "api"
        main.storage = NaiProjectStorage()
        main.api_image_client = NaturalApiClient()
        try:
            with self.assertRaises(main.HTTPException) as caught:
                await main.generate(main.GenerateRequest(prompt="1girl", project_id="project-test"))
        finally:
            main.settings.generation_mode, main.storage, main.api_image_client = originals

        self.assertEqual(400, caught.exception.status_code)
        self.assertIn("NAI 项目", caught.exception.detail)


if __name__ == "__main__":
    unittest.main()
