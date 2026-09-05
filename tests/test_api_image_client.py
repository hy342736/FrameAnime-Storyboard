import asyncio
import base64
import json
from io import BytesIO
import tempfile
import unittest
from pathlib import Path

import httpx
from PIL import Image

from app.api_image_client import ApiImageClient
from app.config import Settings


PNG_BYTES = b"\x89PNG\r\n\x1a\napi-original-image"
WEBP_BYTES = b"RIFF\x10\x00\x00\x00WEBPapi-original-image"


def make_settings(root: Path, protocol: str = "images") -> Settings:
    settings = Settings(
        data_dir=root / "data",
        mirror_url="https://mirror.test",
        mirror_chat_url="",
        headless=True,
        browser_profile_dir=root / "profile",
        image_dir=root / "generated",
        reference_dir=root / "references",
        generation_timeout_seconds=60,
        local_api_key="",
        generation_mode="api",
        image_api_name="Test Node",
        image_api_base_url="https://api.example.test/v1",
        image_api_protocol=protocol,
        image_api_model="gpt-image-test",
        image_api_key="secret-key",
        image_api_timeout_seconds=60,
    )
    settings.image_dir.mkdir(parents=True)
    settings.reference_dir.mkdir(parents=True)
    return settings


class ApiImageClientTests(unittest.TestCase):
    def test_natural_prompt_makes_reference_less_2d_style_binding_and_high_priority(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-gpt-style-contract-") as directory:
            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "gpt-image-2"
            client = ApiImageClient(settings)

            positive, negative = client.compile_prompt(
                "[Camera] Medium Shot\n一对夫妻站在现代日本住宅玄关",
                style_prompt="现代青年日漫，清晰二维线稿，干净平涂，两级赛璐璐阴影",
                style_negative_prompt="照片感，真人脸，照片化厚涂，油画笔触，3D渲染",
            )

            self.assertEqual("", negative)
            self.assertLess(positive.index("[RENDERING MEDIUM - HIGHEST PRIORITY]"), positive.index("[SHOT CONTENT]"))
            self.assertIn("必须是完成度高的纯二维日漫插画", positive)
            self.assertIn("自然仅指人体比例、透视和环境逻辑可信", positive)
            self.assertNotIn("写实", positive)
            self.assertIn("不得使用照片化真人面孔", positive)
            self.assertIn("不得使用连续柔和明暗塑造脸部体积", positive)

    def test_auto_gpt_profile_preserves_structured_natural_language_prompt(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-gpt-prompt-") as directory:
            captured = {}

            def handler(request: httpx.Request) -> httpx.Response:
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]},
                )

            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "gpt-image-2-1k"
            client = ApiImageClient(settings, httpx.MockTransport(handler))
            result = asyncio.run(
                client.generate(
                    "[Camera] Wide Shot\nA quiet Japanese street at night",
                    "project-test",
                    style_prompt="commercial anime illustration",
                    style_negative_prompt="text, watermark",
                )
            )

            payload = captured["payload"]
            self.assertIn("[Camera] Wide Shot", payload["prompt"])
            self.assertIn("[RENDERING MEDIUM - HIGHEST PRIORITY]", payload["prompt"])
            self.assertIn("[STRICT EXCLUSIONS]", payload["prompt"])
            self.assertNotIn("negative_prompt", payload)
            self.assertEqual("natural", result.prompt_profile)

    def test_auto_nai_profile_removes_control_headers_and_separates_negative_prompt(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-nai-prompt-") as directory:
            captured = {}

            def handler(request: httpx.Request) -> httpx.Response:
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]},
                )

            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "nai-diffusion-4-5-full"
            client = ApiImageClient(settings, httpx.MockTransport(handler))
            result = asyncio.run(
                client.generate(
                    "[Character 1: CHR-001 / 町野一男]\n"
                    "Appearance lock: short black hair, gray temples\n"
                    "[Camera] Close Up, Over-the-Shoulder, Static\n"
                    "[Negative Prompt] text, logo, watermark",
                    "project-test",
                    aspect_ratio="3:4",
                    resolution="Auto",
                    style_prompt="clean anime lineart, cel shading",
                    style_negative_prompt="photorealistic, 3d",
                )
            )

            payload = captured["payload"]
            self.assertNotIn("PROJECT ART DIRECTION", payload["prompt"])
            self.assertNotIn("[Character", payload["prompt"])
            self.assertNotIn("[Camera]", payload["prompt"])
            self.assertNotIn("logo", payload["prompt"])
            self.assertIn("short black hair", payload["prompt"])
            self.assertIn("logo", payload["negative_prompt"])
            self.assertNotIn("clean anime lineart", payload["prompt"])
            self.assertNotIn("photorealistic", payload["negative_prompt"])
            self.assertEqual("768x1024", payload["size"])
            self.assertEqual("nai", result.prompt_profile)

    def test_nai_generation_sends_only_final_positive_and_negative_prompts(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-nai-shot-prompt-") as directory:
            captured = {}

            def handler(request: httpx.Request) -> httpx.Response:
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]},
                )

            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "nai-diffusion-5-curated"
            client = ApiImageClient(settings, httpx.MockTransport(handler))
            asyncio.run(
                client.generate(
                    "1girl, adult woman, short black hair, modern Japanese home",
                    "project-test",
                    negative_prompt="duplicate person, merged bodies",
                    style_prompt="world history, faction rules, clean lineart, cel shading",
                    style_negative_prompt="project-wide exclusions, photorealistic, 3d",
                )
            )

            payload = captured["payload"]
            self.assertNotRegex(payload["prompt"], r"[\u3400-\u9fff]")
            self.assertEqual(
                "1girl, adult woman, short black hair, modern Japanese home",
                payload["prompt"],
            )
            self.assertEqual("duplicate person, merged bodies", payload["negative_prompt"])
            self.assertNotIn("world history", payload["prompt"])
            self.assertNotIn("clean lineart", payload["prompt"])
            self.assertNotIn("project-wide exclusions", payload["negative_prompt"])
            self.assertEqual(
                {"model", "prompt", "negative_prompt", "n", "size"},
                set(payload),
            )

    def test_nai_profile_orders_storyboard_tags_and_keeps_character_count(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-nai-order-") as directory:
            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "nai-diffusion-5-curated"
            client = ApiImageClient(settings)

            positive, negative = client.compile_prompt(
            "(masterpiece), best quality, high quality anime illustration\n"
            "[Characters in Frame] 2; CHR-001=Alice, CHR-002=Bob\n"
            "[Character 1: CHR-001 / Alice]\n"
            "Appearance lock: turquoise twin tails, green eyes\n"
            "Position and orientation: frame left, facing right\n"
            "Individual action: holding transparent umbrella\n"
            "Expression and eye line: surprised, looking at Bob\n"
            "[Character 2: CHR-002 / Bob]\n"
            "Appearance lock: short black hair\n"
            "Position and orientation: frame right, facing left\n"
            "Individual action: holding letter\n"
            "Interaction and shared event: facing each other\n"
            "Scene / time: rainy street, night\n"
            "[Camera] Medium Shot, Eye Level, Static\n"
            "Lighting: blue ambient light, warm shop light\n"
            "Style: clean lineart, cel shading\n"
            "[Negative Prompt] text, watermark",
            style_prompt="anime screencap",
            style_negative_prompt="photorealistic, 3d",
        )

            self.assertLess(positive.index("masterpiece"), positive.index("2people"))
            self.assertLess(positive.index("2people"), positive.index("turquoise twin tails"))
            self.assertLess(positive.index("facing each other"), positive.index("medium shot"))
            self.assertLess(positive.index("medium shot"), positive.index("rainy street"))
            self.assertLess(positive.index("rainy street"), positive.index("blue ambient light"))
            self.assertIn("Alice: frame left and facing right", positive)
            self.assertIn("Bob: frame right and facing left", positive)
            self.assertIn("text", negative)
            self.assertIn("photorealistic", negative)
            self.assertNotIn("[Camera]", positive)
            self.assertNotIn("Static", positive)

    def test_explicit_natural_profile_does_not_convert_nai_named_model(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-natural-profile-") as directory:
            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "nai-diffusion-5-curated"
            settings.image_api_prompt_profile = "natural"
            client = ApiImageClient(settings)

            positive, negative = client.compile_prompt(
                "[Camera] Medium Shot\n请生成雨夜双人场景",
                style_prompt="清晰二维动画",
                style_negative_prompt="文字，水印",
            )

            self.assertIn("[Camera] Medium Shot", positive)
            self.assertIn("[RENDERING MEDIUM - HIGHEST PRIORITY]", positive)
            self.assertIn("[STRICT EXCLUSIONS]", positive)
            self.assertEqual("", negative)

    def test_auto_profile_recognizes_display_style_nai_model_name(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-nai-name-") as directory:
            settings = make_settings(Path(directory), "images")
            settings.image_api_model = "NAI Diffusion V5 Full"

            self.assertEqual("nai", ApiImageClient(settings).resolved_prompt_profile())

    def test_images_protocol_omits_reference_images_and_reports_warning(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-images-reference-") as directory:
            root = Path(directory)
            reference = root / "reference.png"
            reference.write_bytes(PNG_BYTES)
            settings = make_settings(root, "images")
            captured = {}

            def handler(request: httpx.Request) -> httpx.Response:
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]},
                )

            client = ApiImageClient(settings, httpx.MockTransport(handler))
            result = asyncio.run(client.generate("draw with style wording", "project-test", [reference]))

            self.assertEqual("draw with style wording", captured["payload"]["prompt"])
            self.assertNotIn("input_image", json.dumps(captured["payload"]))
            self.assertEqual(1, result.references_requested)
            self.assertEqual(0, result.references_attached)
            self.assertIn("未发送 1 张", result.reference_warning)

    def test_full_endpoint_url_is_normalized_to_api_root(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-api-url-") as directory:
            settings = make_settings(Path(directory), "images")
            settings.image_api_base_url = "https://api.example.test/v1/images/generations"
            client = ApiImageClient(settings)

            self.assertEqual("https://api.example.test/v1/images/generations", client._endpoint("images/generations"))
            self.assertEqual("https://api.example.test/v1/models", client._endpoint("models"))

    def test_connection_accepts_reachable_provider_without_models_endpoint(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-api-probe-") as directory:
            def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual("/v1/models", request.url.path)
                return httpx.Response(404, json={"detail": "not found"})

            settings = make_settings(Path(directory), "responses")
            settings.image_api_base_url = "https://api.example.test/v1/responses"
            client = ApiImageClient(settings, httpx.MockTransport(handler))

            message = asyncio.run(client.test_connection())
            self.assertIn("地址可达", message)
            self.assertIn("首次生成", message)

    def test_images_protocol_sends_size_and_saves_original_base64(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-images-api-") as directory:
            captured = {}

            def handler(request: httpx.Request) -> httpx.Response:
                captured["path"] = request.url.path
                captured["authorization"] = request.headers.get("authorization")
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii")}]},
                )

            settings = make_settings(Path(directory), "images")
            client = ApiImageClient(settings, httpx.MockTransport(handler))
            result = asyncio.run(client.generate("draw", "project-test", aspect_ratio="16:9", resolution="2K"))

            self.assertEqual("/v1/images/generations", captured["path"])
            self.assertEqual("Bearer secret-key", captured["authorization"])
            self.assertEqual("gpt-image-test", captured["payload"]["model"])
            self.assertEqual("2048x1152", captured["payload"]["size"])
            self.assertEqual(PNG_BYTES, result.path.read_bytes())
            self.assertEqual(".png", result.path.suffix)

    def test_auto_resolution_still_sends_selected_non_square_ratio(self):
        self.assertEqual("768x1024", ApiImageClient._pixel_size("3:4", "Auto"))
        self.assertEqual("1024x576", ApiImageClient._pixel_size("16:9", "Auto"))

    def test_returned_ratio_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-ratio-warning-") as directory:
            captured = {}
            image_payload = BytesIO()
            Image.new("RGB", (64, 64), "white").save(image_payload, "PNG")
            square_png = image_payload.getvalue()

            def handler(request: httpx.Request) -> httpx.Response:
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"data": [{"b64_json": base64.b64encode(square_png).decode("ascii")}]},
                )

            settings = make_settings(Path(directory), "images")
            result = asyncio.run(
                ApiImageClient(settings, httpx.MockTransport(handler)).generate(
                    "draw", "project-test", aspect_ratio="3:4", resolution="Auto"
                )
            )

            self.assertEqual("768x1024", captured["payload"]["size"])
            self.assertEqual("768x1024", result.requested_size)
            self.assertEqual("64x64", result.actual_size)
            self.assertIn("比例不符", result.generation_warning)

    def test_responses_protocol_attaches_reference_and_saves_result(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-responses-api-") as directory:
            root = Path(directory)
            reference = root / "reference.png"
            reference.write_bytes(PNG_BYTES)
            captured = {}

            def handler(request: httpx.Request) -> httpx.Response:
                captured["path"] = request.url.path
                captured["payload"] = json.loads(request.content)
                return httpx.Response(
                    200,
                    json={"output": [{"type": "image_generation_call", "result": base64.b64encode(WEBP_BYTES).decode("ascii")}]},
                )

            settings = make_settings(root, "responses")
            client = ApiImageClient(settings, httpx.MockTransport(handler))
            result = asyncio.run(client.generate("edit", "project-test", [reference]))

            self.assertEqual("/v1/responses", captured["path"])
            content = captured["payload"]["input"][0]["content"]
            self.assertEqual("input_text", content[0]["type"])
            self.assertEqual("input_image", content[1]["type"])
            self.assertTrue(content[1]["image_url"].startswith("data:image/png;base64,"))
            self.assertEqual(1, result.references_attached)
            self.assertEqual(WEBP_BYTES, result.path.read_bytes())
            self.assertEqual(".webp", result.path.suffix)

    def test_remote_image_download_does_not_forward_api_key(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-api-download-") as directory:
            requests = []

            def handler(request: httpx.Request) -> httpx.Response:
                requests.append((str(request.url), request.headers.get("authorization")))
                if request.url.path.endswith("/images/generations"):
                    return httpx.Response(200, json={"data": [{"url": "https://cdn.example.test/original.png"}]})
                return httpx.Response(200, content=PNG_BYTES, headers={"content-type": "image/png"})

            settings = make_settings(Path(directory), "images")
            client = ApiImageClient(settings, httpx.MockTransport(handler))
            result = asyncio.run(client.generate("draw", "project-test"))

            self.assertEqual("Bearer secret-key", requests[0][1])
            self.assertIsNone(requests[1][1])
            self.assertEqual(PNG_BYTES, result.path.read_bytes())

    def test_api_key_is_persisted_but_never_returned_publicly(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-api-key-") as directory:
            settings = make_settings(Path(directory))
            settings.update({"image_api_key": "new-secret"})

            public = settings.public()
            stored = json.loads(settings.persistent_file.read_text(encoding="utf-8"))
            self.assertNotIn("image_api_key", public)
            self.assertNotIn("new-secret", json.dumps(public))
            self.assertTrue(public["has_image_api_key"])
            self.assertEqual("new-secret", stored["image_api_key"])


if __name__ == "__main__":
    unittest.main()
