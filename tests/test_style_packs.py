import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from fastapi import HTTPException
import httpx

from app import main
from app.browser_session import GenerationResult
from app.style_packs import STYLE_ANALYSIS_FIELDS, StylePackError, StylePackLibrary


BUILTIN_ROOT = Path(__file__).resolve().parents[1] / "assets" / "style-packs"


def image_bytes(format_name: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (16, 16), "#4f8f9d").save(output, format=format_name)
    return output.getvalue()


def analysis() -> dict[str, str]:
    return {field: f"test {field}" for field in STYLE_ANALYSIS_FIELDS}


class StylePackLibraryTests(unittest.TestCase):
    def test_lists_enabled_builtin_packs_in_catalog_order(self):
        packs = StylePackLibrary(BUILTIN_ROOT).list_packs()
        self.assertEqual(
            ["modern-seinen-v1", "webtoon-vibrant-v1", "commercial-anime-v1", "ink-v1"],
            [pack["id"] for pack in packs],
        )
        self.assertTrue(all(pack["source"] == "builtin" and not pack["editable"] for pack in packs))
        self.assertTrue(all(len(StylePackLibrary(BUILTIN_ROOT).enabled_reference_paths(pack["id"])) == 4 for pack in packs))

    def test_custom_pack_create_update_replace_and_delete(self):
        with tempfile.TemporaryDirectory(prefix="frame-style-custom-") as directory:
            library = StylePackLibrary(BUILTIN_ROOT, Path(directory))
            created = library.create_custom_pack(
                display_name="我的线稿",
                description="测试画风",
                style_analysis=analysis(),
                compiled_prompt="clean line art",
                negative_prompt="photo",
                primary=("primary.webp", image_bytes("WEBP")),
                auxiliary=[("light.jpg", image_bytes("JPEG"))],
            )
            self.assertEqual("custom", created["source"])
            self.assertTrue(created["editable"])
            self.assertEqual(2, len(library.enabled_reference_paths(created["id"])))

            updated = library.update_custom_pack(created["id"], {"display_name": "修改后的画风", "compiled_prompt": "edited"})
            self.assertEqual("修改后的画风", updated["display_name"])
            self.assertEqual("edited", updated["compiled_prompt"])

            replaced = library.replace_custom_assets(
                created["id"],
                primary=None,
                auxiliary=[("one.png", image_bytes()), ("two.png", image_bytes())],
            )
            self.assertEqual(3, len(library.enabled_reference_paths(created["id"])))
            self.assertEqual(["primary", "auxiliary_1", "auxiliary_2"], replaced["generation"]["reference_order"])

            library.delete_custom_pack(created["id"])
            self.assertIsNone(library.get_pack(created["id"], include_disabled=True))

    def test_custom_pack_rejects_more_than_three_auxiliary_images(self):
        with tempfile.TemporaryDirectory(prefix="frame-style-limit-") as directory:
            library = StylePackLibrary(BUILTIN_ROOT, Path(directory))
            with self.assertRaisesRegex(StylePackError, "最多 3 张"):
                library.create_custom_pack(
                    display_name="超限",
                    description="",
                    style_analysis=analysis(),
                    compiled_prompt="style",
                    negative_prompt="",
                    primary=("primary.png", image_bytes()),
                    auxiliary=[(f"{index}.png", image_bytes()) for index in range(4)],
                )

    def test_builtin_pack_cannot_be_deleted(self):
        with tempfile.TemporaryDirectory(prefix="frame-style-protect-") as directory:
            library = StylePackLibrary(BUILTIN_ROOT, Path(directory))
            with self.assertRaisesRegex(StylePackError, "内置画风"):
                library.delete_custom_pack("modern-seinen-v1")


class StyleGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generation_prepends_style_references_and_compiles_project_override(self):
        class ProjectStorage:
            def get_project(self, project_id):
                return {
                    "id": project_id,
                    "name": "Style test",
                    "state": {
                        "artDirection": {
                            "stylePackId": "modern-seinen-v1",
                            "compiledPrompt": "user edited style",
                            "negativePrompt": "user exclusions",
                        }
                    },
                }

            def get_reference(self, reference_id):
                return {"id": reference_id, "project_id": "project-style", "owner_type": "world", "owner_id": "world", "enabled": True}

            def reference_file(self, _reference_id):
                return Path(__file__)

            def get_conversation_binding(self, _project_id):
                return None

            def set_conversation_binding(self, project_id, *, url, title=""):
                return {"project_id": project_id, "url": url, "title": title}

        class Session:
            def __init__(self, output):
                self.output = output
                self.call = None

            async def generate(self, prompt, project_id, reference_paths, require_all_references, conversation_url=""):
                self.call = {"prompt": prompt, "paths": reference_paths, "require_all": require_all_references}
                return GenerationResult(self.output, references_requested=len(reference_paths), references_attached=len(reference_paths))

        with tempfile.TemporaryDirectory(prefix="frame-style-generation-") as directory:
            output = Path(directory) / "project-style" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(image_bytes())
            fake_session = Session(output)
            originals = (main.settings.generation_mode, main.settings.image_dir, main.storage, main.session)
            main.settings.generation_mode = "mirror"
            main.settings.image_dir = Path(directory)
            main.storage = ProjectStorage()
            main.session = fake_session
            try:
                result = await main.generate(main.GenerateRequest(prompt="draw scene", project_id="project-style", reference_ids=["world-ref"]))
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.storage, main.session = originals

        expected_style_paths = main.style_library.enabled_reference_paths("modern-seinen-v1")
        self.assertEqual(expected_style_paths, fake_session.call["paths"][:4])
        self.assertEqual(Path(__file__), fake_session.call["paths"][4])
        self.assertTrue(fake_session.call["require_all"])
        self.assertIn("[PROJECT ART DIRECTION]\nuser edited style", fake_session.call["prompt"])
        self.assertIn("[EXCLUDE FROM IMAGE]\nuser exclusions", fake_session.call["prompt"])
        self.assertEqual(4, result["style_references_requested"])

    async def test_generation_rejects_missing_project_style_pack(self):
        class MissingStyleStorage:
            def get_project(self, project_id):
                return {"id": project_id, "state": {"artDirection": {"stylePackId": "missing-style"}}}

            def get_conversation_binding(self, _project_id):
                return None

        originals = (main.settings.generation_mode, main.storage)
        main.settings.generation_mode = "mirror"
        main.storage = MissingStyleStorage()
        try:
            with self.assertRaises(HTTPException) as captured:
                await main.generate(main.GenerateRequest(prompt="draw", project_id="project-missing"))
        finally:
            main.settings.generation_mode, main.storage = originals
        self.assertEqual(400, captured.exception.status_code)
        self.assertIn("不存在", captured.exception.detail)

    async def test_shot_can_disable_project_style(self):
        captured = await self._generate_with_style_override("none")
        self.assertEqual([], captured["paths"])
        self.assertNotIn("PROJECT ART DIRECTION", captured["prompt"])

    async def test_shot_can_use_an_alternate_style_pack(self):
        captured = await self._generate_with_style_override("webtoon-vibrant-v1")
        expected = main.style_library.enabled_reference_paths("webtoon-vibrant-v1")
        self.assertEqual(expected, captured["paths"])
        self.assertNotIn("user edited project style", captured["prompt"])
        self.assertIn("PROJECT ART DIRECTION", captured["prompt"])

    async def test_shot_inherits_edited_project_style_by_default(self):
        captured = await self._generate_with_style_override("")
        expected = main.style_library.enabled_reference_paths("modern-seinen-v1")
        self.assertEqual(expected, captured["paths"])
        self.assertIn("user edited project style", captured["prompt"])

    async def test_agent_multi_panel_prompt_remains_the_exact_final_prompt(self):
        prompt = (
            "A 2-panel split comic strip, side-by-side split composition, clean white "
            "borders between panels, featuring the same character across all panels: "
            "a young woman with silver hair, blue coat, star earring. Panel 1 (left): "
            "she raises a lantern. Panel 2 (right): she passes an envelope. Clean 2D "
            "anime line art, clean panels, no text, no gibberish speech bubbles, no logo, "
            "no watermark, --ar 16:9"
        )
        captured = await self._generate_with_style_override("", prompt=prompt, aspect_ratio="16:9")
        self.assertEqual(prompt, captured["prompt"])
        self.assertNotIn("PROJECT ART DIRECTION", captured["prompt"])
        self.assertEqual(main.style_library.enabled_reference_paths("modern-seinen-v1"), captured["paths"])

    async def _generate_with_style_override(self, override, *, prompt="draw", aspect_ratio="Auto"):
        class Storage:
            def get_project(self, project_id):
                return {
                    "id": project_id,
                    "name": "Style override test",
                    "state": {
                        "artDirection": {
                            "stylePackId": "modern-seinen-v1",
                            "compiledPrompt": "user edited project style",
                            "negativePrompt": "user edited exclusions",
                        }
                    },
                }

            def get_conversation_binding(self, _project_id):
                return None

            def set_conversation_binding(self, project_id, *, url, title=""):
                return {"project_id": project_id, "url": url, "title": title}

        class Session:
            def __init__(self, output):
                self.output = output
                self.call = None

            async def generate(self, prompt, project_id, reference_paths, require_all_references, conversation_url=""):
                self.call = {"prompt": prompt, "paths": reference_paths}
                return GenerationResult(
                    self.output,
                    references_requested=len(reference_paths),
                    references_attached=len(reference_paths),
                    conversation_url="https://example.test/c/style-test",
                )

        with tempfile.TemporaryDirectory(prefix="frame-shot-style-") as directory:
            output = Path(directory) / "project-style" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(image_bytes())
            fake_session = Session(output)
            originals = (main.settings.generation_mode, main.settings.image_dir, main.storage, main.session)
            main.settings.generation_mode = "mirror"
            main.settings.image_dir = Path(directory)
            main.storage = Storage()
            main.session = fake_session
            try:
                await main.generate(
                    main.GenerateRequest(
                        prompt=prompt,
                        project_id="project-style",
                        style_pack_override=override,
                        aspect_ratio=aspect_ratio,
                    )
                )
            finally:
                main.settings.generation_mode, main.settings.image_dir, main.storage, main.session = originals
        return fake_session.call


class StylePackApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_asset_and_custom_create_routes(self):
        with tempfile.TemporaryDirectory(prefix="frame-style-api-") as directory:
            library = StylePackLibrary(BUILTIN_ROOT, Path(directory))
            transport = httpx.ASGITransport(app=main.app)
            with patch("app.main.style_library", library):
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    listed = await client.get("/api/style-packs")
                    self.assertEqual(200, listed.status_code, listed.text)
                    self.assertEqual(4, len(listed.json()))
                    asset = await client.get("/api/style-packs/modern-seinen-v1/assets/overall_style")
                    self.assertEqual(200, asset.status_code, asset.text)
                    self.assertTrue(asset.headers["content-type"].startswith("image/"))

                    created = await client.post(
                        "/api/style-packs/custom",
                        data={
                            "display_name": "API 自定义",
                            "description": "",
                            "style_analysis": __import__("json").dumps(analysis()),
                            "compiled_prompt": "api style",
                            "negative_prompt": "photo",
                        },
                        files={"primary": ("primary.png", image_bytes(), "image/png")},
                    )
                    self.assertEqual(201, created.status_code, created.text)
                    self.assertEqual("custom", created.json()["source"])
                    self.assertEqual(5, len((await client.get("/api/style-packs")).json()))


if __name__ == "__main__":
    unittest.main()
