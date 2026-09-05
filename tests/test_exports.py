from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
import zipfile

from PIL import Image, ImageChops, ImageDraw

from app.bubble_packs import BubblePackLibrary
from app.exporter import ExportError, ExportOptions, compose_panel, export_project, fit_text, resolve_generated_image


class ProjectExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.image_root = Path(self.temp.name)
        generated = self.image_root / "project-export" / "generated"
        generated.mkdir(parents=True)
        Image.new("RGB", (320, 180), "#d94f4f").save(generated / "first.png")
        Image.new("RGB", (180, 320), "#3e8f70").save(generated / "second.png")
        self.project = {
            "id": "project-export",
            "name": "雨夜测试",
            "revision": 7,
            "state": {
                "lettering": {"bubblePackId": "jp-clean-v1"},
                "shots": [
                    {
                        "id": "SHOT-001",
                        "title": "红色开场",
                        "content": {"lastImage": "/images/project-export/generated/first.png"},
                        "postText": [],
                    },
                    {
                        "id": "SHOT-002",
                        "title": "绿色收束",
                        "content": {"lastImage": "/images/project-export/generated/second.png"},
                        "postText": [],
                    },
                ],
            },
        }
        root = Path(__file__).resolve().parents[1] / "assets" / "bubble-packs"
        self.bubbles = BubblePackLibrary(root)

    def tearDown(self):
        self.temp.cleanup()

    def test_png_bundle_preserves_order_and_manifest(self):
        artifact = export_project(self.project, self.image_root, self.bubbles, ExportOptions("png_bundle"))
        self.assertEqual("application/zip", artifact.media_type)
        with zipfile.ZipFile(artifact.path) as archive:
            names = archive.namelist()
            self.assertTrue(names[0].startswith("001_SHOT-001"), names)
            self.assertTrue(names[1].startswith("002_SHOT-002"), names)
            manifest = json.loads(archive.read("manifest.json"))
        self.assertEqual(2, manifest["shot_count"])
        self.assertEqual(names[:2], manifest["files"])

    def test_vertical_comic_normalizes_width_and_keeps_order(self):
        artifact = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", width=640, gap=20),
        )
        with Image.open(artifact.path) as image:
            self.assertEqual((640, 1518), image.size)
            self.assertGreater(image.getpixel((20, 20))[0], image.getpixel((20, 20))[1])
            self.assertGreater(image.getpixel((20, 1490))[1], image.getpixel((20, 1490))[0])

    def test_vertical_comic_honors_row_slots_border_and_gutter(self):
        self.project["state"]["shots"][0]["layoutMeta"] = {
            "rowIndex": 1, "slotIndex": 1, "borderStyle": "solid_black_2px", "gutterBottom": 40,
        }
        self.project["state"]["shots"][1]["layoutMeta"] = {
            "rowIndex": 1, "slotIndex": 2, "borderStyle": "solid_white_2px", "gutterBottom": 40,
        }
        artifact = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", width=640, gap=20),
        )
        with Image.open(artifact.path) as image:
            self.assertEqual(640, image.width)
            self.assertLess(image.height, 700)
            self.assertEqual((0, 0, 0), image.getpixel((0, 0)))
            self.assertEqual((255, 255, 255), image.getpixel((639, 0)))
            self.assertEqual((255, 255, 255), image.getpixel((320, image.height - 1)))

    def test_pdf_has_one_page_per_shot(self):
        artifact = export_project(self.project, self.image_root, self.bubbles, ExportOptions("pdf"))
        payload = artifact.path.read_bytes()
        self.assertTrue(payload.startswith(b"%PDF"))
        self.assertEqual(2, len(re.findall(rb"/Type\s*/Page(?!s)", payload)))

    def test_video_is_mp4_and_does_not_mutate_project(self):
        before = deepcopy(self.project)
        artifact = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("video", width=640, frame_duration_seconds=1),
        )
        payload = artifact.path.read_bytes()
        self.assertIn(b"ftyp", payload[:64])
        self.assertGreater(len(payload), 1000)
        self.assertEqual(before, self.project)

    def test_missing_images_report_every_affected_shot(self):
        self.project["state"]["shots"][0]["content"]["lastImage"] = ""
        self.project["state"]["shots"][1]["content"]["lastImage"] = "/images/project-export/generated/missing.png"
        with self.assertRaisesRegex(ExportError, "SHOT-001, SHOT-002"):
            export_project(self.project, self.image_root, self.bubbles, ExportOptions("pdf"))

    def test_selected_shots_export_in_project_order_and_ignore_unselected_missing_images(self):
        self.project["state"]["shots"].append({
            "id": "SHOT-003",
            "title": "尚未生成",
            "content": {"lastImage": ""},
            "postText": [],
        })
        artifact = export_project(
            self.project,
            self.image_root,
            self.bubbles,
            ExportOptions("png_bundle", shot_ids=("SHOT-002", "SHOT-001")),
        )
        with zipfile.ZipFile(artifact.path) as archive:
            names = archive.namelist()
            manifest = json.loads(archive.read("manifest.json"))
        self.assertTrue(names[0].startswith("001_SHOT-001"), names)
        self.assertTrue(names[1].startswith("002_SHOT-002"), names)
        self.assertEqual(2, manifest["shot_count"])

    def test_unknown_selected_shot_is_rejected(self):
        with self.assertRaisesRegex(ExportError, "不存在"):
            export_project(
                self.project,
                self.image_root,
                self.bubbles,
                ExportOptions("pdf", shot_ids=("SHOT-404",)),
            )

    def test_external_and_traversal_image_urls_are_rejected(self):
        for value in (
            "https://example.com/image.png",
            "/images/../workspace.json",
            "/api/references/ref/file",
        ):
            with self.subTest(value=value), self.assertRaises(ExportError):
                resolve_generated_image(self.image_root, value, "project-export")

    def test_another_projects_generated_image_is_rejected(self):
        with self.assertRaises(ExportError):
            resolve_generated_image(
                self.image_root,
                "/images/project-other/generated/image.png",
                "project-export",
            )

    def test_lettering_changes_panel_pixels(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "dialogue",
            "text": "快走！",
            "position": "top-right",
            "bubbleSemantic": "dialogue",
            "bubbleAssetId": "speech-right",
        }]
        plain = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=False, width=640),
        )
        plain_bytes = plain.path.read_bytes()
        lettered = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=True, width=640),
        )
        self.assertNotEqual(plain_bytes, lettered.path.read_bytes())

    def test_project_custom_bubble_is_used_by_export(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "dialogue",
            "text": "好",
            "position": "top-left",
            "bubbleSemantic": "dialogue",
            "bubbleReferenceId": "ref-custom-bubble",
        }]
        custom_bubble = self.image_root / "custom-bubble.png"
        bubble = Image.new("RGBA", (240, 160), (255, 255, 255, 0))
        ImageDraw.Draw(bubble).ellipse((4, 4, 235, 155), fill="white", outline="black", width=5)
        bubble.save(custom_bubble)
        bubble.close()

        plain = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=False, width=640),
        )
        plain_bytes = plain.path.read_bytes()
        lettered = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=True, width=640),
            lambda reference_id: custom_bubble if reference_id == "ref-custom-bubble" else None,
        )
        self.assertNotEqual(plain_bytes, lettered.path.read_bytes())

    def test_text_element_exports_without_bubble_asset(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "elementType": "text",
            "kind": "narration",
            "text": "这是直接绘制的文字",
            "position": "top-left",
            "bubbleSemantic": "narration",
            "bubbleAssetId": "",
            "bubbleReferenceId": "",
            "layout": {"x": 0.08, "y": 0.08, "width": 0.42, "fontScale": 1.0, "rotation": 12},
        }]
        plain = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=False, width=640),
        )
        plain_bytes = plain.path.read_bytes()
        lettered = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=True, width=640),
        )
        self.assertNotEqual(plain_bytes, lettered.path.read_bytes())

    def test_missing_project_custom_bubble_is_rejected(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "dialogue",
            "text": "缺失素材",
            "bubbleReferenceId": "ref-missing",
        }]
        with self.assertRaisesRegex(ExportError, "自定义气泡不存在"):
            export_project(
                self.project, self.image_root, self.bubbles,
                ExportOptions("png_bundle", include_lettering=True),
            )

    def test_hidden_lettering_does_not_change_panel_pixels(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "dialogue",
            "text": "这句暂时不显示",
            "position": "top-right",
            "bubbleSemantic": "dialogue",
            "hidden": True,
        }]
        plain = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=False, width=640),
        )
        plain_bytes = plain.path.read_bytes()
        lettered = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("vertical_comic", include_lettering=True, width=640),
        )
        self.assertEqual(plain_bytes, lettered.path.read_bytes())

    def test_custom_lettering_layout_controls_export_position_and_width(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "dialogue",
            "text": "快走！",
            "position": "bottom",
            "bubbleSemantic": "dialogue",
            "bubbleAssetId": "speech-right",
            "layout": {"x": 0.05, "y": 0.58, "width": 0.20, "flip": False},
        }]
        artifact = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("png_bundle", include_lettering=True),
        )
        with zipfile.ZipFile(artifact.path) as archive:
            panel_name = next(name for name in archive.namelist() if name.endswith(".png"))
            with archive.open(panel_name) as payload, Image.open(payload) as rendered:
                rendered = rendered.convert("RGB")
        source = Image.new("RGB", rendered.size, "#d94f4f")
        changed = ImageChops.difference(source, rendered).getbbox()
        self.assertIsNotNone(changed)
        self.assertLessEqual(changed[0], 18)
        self.assertGreaterEqual(changed[1], 95)
        self.assertLessEqual(changed[2] - changed[0], 72)

    def test_custom_lettering_font_scale_is_accepted_and_changes_rendering(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        block = {
            "kind": "dialogue",
            "text": "字号测试文字",
            "position": "top-right",
            "bubbleSemantic": "dialogue",
            "bubbleAssetId": "speech-right",
            "layout": {"x": 0.60, "y": 0.05, "width": 0.30, "flip": False, "fontScale": 0.6},
        }
        self.project["state"]["shots"][0]["postText"] = [block]
        small_font, _ = fit_text("字号测试文字", 324, 300, font_scale=0.6)
        block["layout"]["fontScale"] = 1.4
        large_font, _ = fit_text("字号测试文字", 324, 300, font_scale=1.4)
        self.assertGreater(large_font.size, small_font.size)

    def test_custom_lettering_rotation_is_rendered(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        block = {
            "kind": "dialogue", "text": "X", "position": "top-right",
            "bubbleSemantic": "dialogue", "bubbleAssetId": "speech-right",
            "layout": {"x": 0.10, "y": 0.10, "width": 0.30, "rotation": 0},
        }
        self.project["state"]["shots"][0]["postText"] = [block]
        source = self.image_root / "project-export" / "generated" / "first.png"
        normal = compose_panel(source, self.project["state"]["shots"][0], self.project, self.bubbles, True)
        block["layout"]["rotation"] = 24
        rotated = compose_panel(source, self.project["state"]["shots"][0], self.project, self.bubbles, True)
        try:
            self.assertIsNotNone(ImageChops.difference(normal.convert("RGB"), rotated.convert("RGB")).getbbox())
        finally:
            normal.close()
            rotated.close()

    def test_thought_bubble_adds_a_readable_light_backing(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "thought",
            "text": "不能再等了。",
            "position": "top-left",
            "bubbleSemantic": "thought",
            "bubbleAssetId": "thought",
            "layout": {"x": 0.05, "y": 0.05, "width": 0.24, "flip": False},
        }]
        artifact = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("png_bundle", include_lettering=True),
        )
        with zipfile.ZipFile(artifact.path) as archive:
            panel_name = next(name for name in archive.namelist() if name.endswith(".png"))
            with archive.open(panel_name) as payload, Image.open(payload) as rendered:
                rendered = rendered.convert("RGB")
        crop = rendered.crop((15, 8, 105, 150))
        pixels = crop.load()
        light_pixels = sum(
            1 for y in range(crop.height) for x in range(crop.width)
            if all(channel > 225 for channel in pixels[x, y])
        )
        self.assertGreater(light_pixels, 800)

    def test_thought_semantic_does_not_add_ellipse_behind_dialogue_asset(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        block = {
            "kind": "thought",
            "text": "不能再等了。",
            "position": "bottom",
            "bubbleSemantic": "dialogue",
            "bubbleAssetId": "cheerful",
            "layout": {"x": 0.35, "y": 0.55, "width": 0.24, "flip": False},
        }
        self.project["state"]["shots"][0]["postText"] = [block]
        dialogue = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("png_bundle", include_lettering=True),
        ).path.read_bytes()

        block["bubbleSemantic"] = "thought"
        thought = export_project(
            self.project, self.image_root, self.bubbles,
            ExportOptions("png_bundle", include_lettering=True),
        ).path.read_bytes()

        with zipfile.ZipFile(BytesIO(dialogue)) as dialogue_zip, zipfile.ZipFile(BytesIO(thought)) as thought_zip:
            dialogue_png = dialogue_zip.read(next(name for name in dialogue_zip.namelist() if name.endswith(".png")))
            thought_png = thought_zip.read(next(name for name in thought_zip.namelist() if name.endswith(".png")))
        self.assertEqual(dialogue_png, thought_png)

    def test_overlong_lettering_fails_instead_of_clipping(self):
        self.project["state"]["shots"] = [self.project["state"]["shots"][0]]
        self.project["state"]["shots"][0]["postText"] = [{
            "kind": "dialogue",
            "text": "这是一段不应该被静默裁切的超长对白" * 20,
            "position": "top-right",
            "bubbleSemantic": "dialogue",
        }]
        with self.assertRaisesRegex(ExportError, "文字过长"):
            export_project(self.project, self.image_root, self.bubbles, ExportOptions("png_bundle"))


if __name__ == "__main__":
    unittest.main()
