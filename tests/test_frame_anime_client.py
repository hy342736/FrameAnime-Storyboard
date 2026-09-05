import importlib.util
import os
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


CLIENT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "anime-ai-art-director"
    / "scripts"
    / "frame_anime_client.py"
)
SPEC = importlib.util.spec_from_file_location("frame_anime_client", CLIENT_PATH)
client_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(client_module)


def candidate(url: str, *, compatible: bool, source: str = "test") -> dict:
    return {
        "base_url": url,
        "source": source,
        "compatible": compatible,
        "health": {"status": "ok"},
        "errors": [] if compatible else ["incompatible"],
    }


def one_panel_manifest() -> dict:
    return {
        "schema_version": 1,
        "project": {"name": "单格测试"},
        "preferences": {
            "prompt_profile": "natural",
            "format": "vertical_comic",
            "panel_budget": 1,
            "adaptation_mode": "faithful",
            "character_mode": "user",
            "style_mode": "color_anime",
            "style_pack_id": "modern-seinen-v1",
            "style_prompt": "清晰动画线稿",
            "style_negative_prompt": "文字，水印",
            "style_analysis": {},
            "bubble_pack_id": "jp-clean-v1",
        },
        "source_batch": {
            "batch_id": "BATCH-001",
            "selected_text": "A",
            "start_quote": "A",
            "end_quote": "A",
            "char_count": 1,
        },
        "existing_character_ids": [],
        "characters": [],
        "shots": [
            {
                "client_id": "SHOT-001",
                "type": "Wide Shot",
                "title": "单格",
                "description": "单个视觉节拍",
                "characters": [],
                "visual": {
                    "prompt": "安静街道",
                    "scene": "街道",
                    "action": "雨停",
                    "expression": "平静",
                    "lighting": "傍晚天光",
                    "style": "彩色动画",
                },
                "source": {"anchor": "A", "adaptation_kind": "direct"},
                "post_text": [],
            }
        ],
        "checklist": [],
    }


def expand_manifest(manifest: dict, count: int) -> dict:
    template = manifest["shots"][0]
    manifest["preferences"]["panel_budget"] = count
    manifest["shots"] = []
    for index in range(count):
        item = deepcopy(template)
        item["client_id"] = f"SHOT-{index + 1:03d}"
        item["visual"]["camera_angle"] = "Eye Level"
        item["visual"]["dynamic_expression"] = "still"
        item["visual"]["panel_layout"] = "single"
        item["visual"]["panel_beats"] = [{"label": "Panel 1", "visual": "quiet street"}]
        manifest["shots"].append(item)
    return manifest


def make_multi_panel(shot: dict) -> None:
    shot["visual"].update(
        {
            "aspect_ratio": "3:4",
            "prompt": (
                "A 2-panel split comic strip, top-and-bottom split composition, "
                "featuring the same character across all panels: black hair, blue dress. "
                "Panel 1 (top): she notices the letter. Panel 2 (bottom): her hand reaches "
                "toward it. Clean 2D anime line art, clean panels, clean gutters, no text, "
                "no gibberish speech bubbles, no logo, no watermark, vertical comic "
                "composition, --ar 3:4"
            ),
        }
    )


class FrameAnimeClientDiscoveryTests(unittest.TestCase):
    def test_manifest_accepts_fifty_panels_and_requires_exact_budget(self):
        manifest = one_panel_manifest()
        self.assertEqual([], client_module.validate_manifest(manifest, require_project=True))

        manifest["preferences"]["panel_budget"] = 2
        errors = client_module.validate_manifest(manifest, require_project=True)
        self.assertIn("shot count must equal preferences.panel_budget", errors)

        manifest = one_panel_manifest()
        expand_manifest(manifest, 50)
        angles = ("Eye Level", "Low Angle", "High Angle", "POV", "Over Shoulder")
        for index, shot in enumerate(manifest["shots"]):
            shot["visual"]["camera_angle"] = angles[index % len(angles)]
            if index % 2 == 0:
                shot["visual"]["dynamic_expression"] = "action_peak"
            if index % 5 == 0:
                make_multi_panel(shot)
        self.assertEqual([], client_module.validate_manifest(manifest, require_project=True))

        manifest["preferences"]["panel_budget"] = 51
        errors = client_module.validate_manifest(manifest, require_project=True)
        self.assertIn("preferences.panel_budget must be an integer from 1 to 50", errors)

    def test_vertical_comic_enforces_storyboard_language_quota(self):
        manifest = expand_manifest(one_panel_manifest(), 20)
        for shot in manifest["shots"][:7]:
            shot["visual"]["dynamic_expression"] = "action_peak"

        errors = client_module.validate_manifest(manifest, require_project=True)

        self.assertTrue(any("at least 50% non-still" in error for error in errors))
        self.assertTrue(any("at least two camera angles" in error for error in errors))
        self.assertTrue(any("more than four consecutive shots" in error for error in errors))

        angles = ("Eye Level", "Low Angle", "High Angle", "POV", "Over Shoulder")
        for index, shot in enumerate(manifest["shots"]):
            shot["visual"]["camera_angle"] = angles[index % len(angles)]
            shot["visual"]["dynamic_expression"] = "action_peak" if index % 2 == 0 else "still"
        for index in (1, 6, 11, 16):
            make_multi_panel(manifest["shots"][index])

        self.assertEqual([], client_module.validate_manifest(manifest, require_project=True))

    def test_multi_panel_metadata_requires_a_complete_spatial_prompt(self):
        manifest = expand_manifest(one_panel_manifest(), 8)
        angles = ("Eye Level", "Low Angle")
        for index, shot in enumerate(manifest["shots"]):
            shot["visual"]["camera_angle"] = angles[index % len(angles)]
            shot["visual"]["dynamic_expression"] = "action_peak" if index % 2 == 0 else "still"
        for index in (0, 4):
            make_multi_panel(manifest["shots"][index])
        manifest["shots"][0]["visual"]["prompt"] = (
            "Dynamic manga page layout, asymmetrical diagonal panels, one dominant "
            "splash panel with inset reaction panels."
        )

        errors = client_module.validate_manifest(manifest, require_project=True)

        self.assertTrue(any("exact panel count" in error for error in errors))

        make_multi_panel(manifest["shots"][0])
        manifest["shots"][0]["visual"]["aspect_ratio"] = "16:9"
        errors = client_module.validate_manifest(manifest, require_project=True)
        self.assertTrue(any("must match visual.aspect_ratio 16:9" in error for error in errors))

        manifest = one_panel_manifest()
        manifest["preferences"].pop("panel_budget")
        errors = client_module.validate_manifest(manifest, require_project=True)
        self.assertIn("preferences.panel_budget must be an integer from 1 to 50", errors)

    def test_nai_manifest_requires_english_generation_fields_and_final_prompts(self):
        manifest = one_panel_manifest()
        manifest["preferences"].update(
            {
                "prompt_profile": "nai",
                "style_prompt": "clean lineart, cel shading",
                "style_negative_prompt": "text, watermark",
            }
        )
        manifest["shots"][0]["visual"] = {
            "prompt": "quiet street after rain",
            "scene": "residential street, evening",
            "action": "rain has stopped",
            "expression": "calm atmosphere",
            "lighting": "soft twilight",
            "style": "clean lineart, flat color",
            "nai_positive_prompt": "empty residential street, wet pavement, evening, clean lineart, cel shading",
            "nai_negative_prompt": "people, text, watermark",
        }
        self.assertEqual([], client_module.validate_manifest(manifest, require_project=True))

        manifest["shots"][0]["visual"]["scene"] = "安静街道"
        errors = client_module.validate_manifest(manifest, require_project=True)
        self.assertIn("shots[0].visual.scene must use English for an NAI project", errors)

    def test_runtime_descriptor_is_preferred_without_port_input(self):
        with tempfile.TemporaryDirectory(prefix="frame-client-runtime-") as directory:
            runtime_path = Path(directory) / "runtime.json"
            runtime_path.write_text(
                '{"base_url":"http://127.0.0.1:8027","pid":123}', encoding="utf-8"
            )
            with patch.dict(os.environ, {"FRAME_ANIME_DESK_HOME": directory}, clear=True):
                with patch.object(
                    client_module,
                    "inspect_candidate",
                    return_value=candidate("http://127.0.0.1:8027", compatible=True),
                ) as inspect:
                    report = client_module.connection_report(None, "", 1)
            self.assertEqual("http://127.0.0.1:8027", report["selected"]["base_url"])
            inspect.assert_called_once_with("http://127.0.0.1:8027", "", 1, "runtime.json")

    def test_stale_runtime_falls_back_to_port_scan(self):
        def inspect(url, _api_key, _timeout, source):
            return candidate(url, compatible=url.endswith(":8019"), source=source)

        with tempfile.TemporaryDirectory(prefix="frame-client-stale-") as directory:
            (Path(directory) / "runtime.json").write_text(
                '{"base_url":"http://127.0.0.1:8028","pid":999}', encoding="utf-8"
            )
            with patch.dict(os.environ, {"FRAME_ANIME_DESK_HOME": directory}, clear=True):
                with patch.object(client_module, "inspect_candidate", side_effect=inspect):
                    report = client_module.connection_report(None, "", 1)
        self.assertEqual("http://127.0.0.1:8019", report["selected"]["base_url"])

    def test_explicit_incompatible_url_does_not_silently_scan(self):
        with patch.object(
            client_module,
            "inspect_candidate",
            return_value=candidate("http://127.0.0.1:8123", compatible=False),
        ) as inspect:
            report = client_module.connection_report("http://127.0.0.1:8123", "", 1)
        self.assertIsNone(report["selected"])
        inspect.assert_called_once()

    def test_multiple_scanned_instances_require_explicit_selection(self):
        report = {
            "selected": None,
            "candidates": [
                candidate("http://127.0.0.1:8000", compatible=True),
                candidate("http://127.0.0.1:8001", compatible=True),
            ],
        }
        args = type("Args", (), {"base_url": None, "api_key": "", "timeout": 1})()
        with patch.object(client_module, "connection_report", return_value=report):
            with self.assertRaisesRegex(client_module.ClientError, "Multiple compatible"):
                client_module.resolve_client(args)

    def test_capability_identity_and_protocol_are_required(self):
        errors = client_module.compatibility_errors(
            {
                "app_name": "AnotherApp",
                "app_version": "0.3.0",
                "runtime_mode": "development",
                "storyboard_import": True,
                "storyboard_import_protocol_version": 2,
                "schema_versions": [1],
                "project_revision": True,
                "deep_link": True,
            }
        )
        self.assertTrue(any("app_name" in error for error in errors))
        self.assertTrue(any("desktop runtime" in error for error in errors))
        self.assertTrue(any("protocol" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
