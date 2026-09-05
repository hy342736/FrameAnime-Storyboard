import json
from pathlib import Path
import unittest


STYLE_PACK_ROOT = Path(__file__).resolve().parents[1] / "assets" / "style-packs"
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
REFERENCE_ROLES = {"linework", "lighting", "background"}


class StylePackConfigTests(unittest.TestCase):
    def test_catalog_and_manifests_are_consistent(self):
        catalog = json.loads((STYLE_PACK_ROOT / "配置.json").read_text(encoding="utf-8"))
        self.assertEqual(1, catalog["schema_version"])

        seen_ids = set()
        for entry in catalog["packs"]:
            manifest_path = STYLE_PACK_ROOT / entry["directory"] / entry["manifest"]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertNotIn(manifest["id"], seen_ids)
            seen_ids.add(manifest["id"])
            self.assertEqual(entry["id"], manifest["id"])
            self.assertEqual(entry["enabled"], manifest["enabled"])
            self.assertEqual(entry["directory"], manifest["slug"])

            primary = manifest["references"]["primary"]
            self.assertTrue(primary["required"])
            self.assertEqual("overall_style", primary["role"])
            self._assert_image_exists(manifest_path.parent, primary["file"])

            auxiliary = manifest["references"]["auxiliary"]
            self.assertLessEqual(len(auxiliary), manifest["generation"]["max_auxiliary"])
            self.assertEqual(
                REFERENCE_ROLES,
                {reference["role"] for reference in auxiliary},
            )
            for reference in auxiliary:
                self._assert_image_exists(manifest_path.parent, reference["file"])

            if manifest["enabled"]:
                self.assertEqual("ready", manifest["status"])
                self.assertTrue(primary["enabled"])
                self.assertTrue(all(reference["enabled"] for reference in auxiliary))
                self.assertTrue(manifest["compiled_prompt"].strip())
                self.assertTrue(manifest["negative_prompt"].strip())

    def _assert_image_exists(self, directory: Path, file_name: str):
        image_path = directory / file_name
        self.assertIn(image_path.suffix.lower(), SUPPORTED_IMAGE_SUFFIXES)
        self.assertTrue(image_path.is_file(), image_path)


if __name__ == "__main__":
    unittest.main()
