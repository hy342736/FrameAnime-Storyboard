import os
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import ast

from app import runtime


class DesktopRuntimeTests(unittest.TestCase):
    def test_desktop_window_starts_maximized(self):
        launcher = Path(__file__).resolve().parents[1] / "desktop_launcher.py"
        tree = ast.parse(launcher.read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_window"
        ]
        self.assertEqual(1, len(calls))
        keywords = {item.arg: item.value for item in calls[0].keywords if item.arg}
        self.assertIsInstance(keywords.get("maximized"), ast.Constant)
        self.assertTrue(keywords["maximized"].value)

    def test_source_mode_does_not_override_environment(self):
        with patch.object(runtime, "is_packaged", return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                self.assertIsNone(runtime.configure_packaged_environment())
                self.assertNotIn("DATA_DIR", os.environ)

    def test_packaged_mode_uses_local_app_data(self):
        with tempfile.TemporaryDirectory(prefix="frame-desktop-") as directory:
            with patch.object(runtime, "is_packaged", return_value=True):
                with patch.object(runtime, "resource_path", return_value=Path(directory) / "missing-browsers"):
                    with patch.dict(os.environ, {"LOCALAPPDATA": directory}, clear=True):
                        root = runtime.configure_packaged_environment()
                        expected = Path(directory) / "FrameAnimeDesk"
                        self.assertEqual(expected.resolve(), root)
                        self.assertEqual(str(expected.resolve() / "data"), os.environ["DATA_DIR"])
                        self.assertEqual(str(expected.resolve() / "generated"), os.environ["IMAGE_DIR"])
                        self.assertTrue(expected.is_dir())

    def test_explicit_home_takes_priority(self):
        with tempfile.TemporaryDirectory(prefix="frame-custom-home-") as directory:
            with patch.object(runtime, "is_packaged", return_value=True):
                with patch.object(runtime, "resource_path", return_value=Path(directory) / "missing-browsers"):
                    with patch.dict(os.environ, {"FRAME_ANIME_DESK_HOME": directory}, clear=True):
                        root = runtime.configure_packaged_environment()
                        self.assertEqual(Path(directory).resolve(), root)

    def test_runtime_descriptor_is_atomic_and_removed_by_owner(self):
        with tempfile.TemporaryDirectory(prefix="frame-runtime-") as directory:
            with patch.dict(os.environ, {"FRAME_ANIME_DESK_HOME": directory}, clear=True):
                descriptor = runtime.write_runtime_descriptor(8017, pid=4321)
                target = Path(directory) / "runtime.json"
                self.assertEqual(descriptor, json.loads(target.read_text(encoding="utf-8")))
                self.assertEqual("http://127.0.0.1:8017", descriptor["base_url"])
                self.assertEqual(runtime.APP_VERSION, descriptor["app_version"])
                self.assertFalse(list(Path(directory).glob("*.tmp")))
                self.assertTrue(runtime.remove_runtime_descriptor(pid=4321))
                self.assertFalse(target.exists())

    def test_runtime_descriptor_is_not_removed_by_another_process(self):
        with tempfile.TemporaryDirectory(prefix="frame-runtime-owner-") as directory:
            with patch.dict(os.environ, {"FRAME_ANIME_DESK_HOME": directory}, clear=True):
                runtime.write_runtime_descriptor(8021, pid=100)
                self.assertFalse(runtime.remove_runtime_descriptor(pid=200))
                self.assertTrue((Path(directory) / "runtime.json").exists())


if __name__ == "__main__":
    unittest.main()
