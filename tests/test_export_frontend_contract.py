from pathlib import Path
import unittest


class ExportFrontendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.html = (root / "web" / "index.html").read_text(encoding="utf-8")
        cls.js = (root / "web" / "app.js").read_text(encoding="utf-8")
        cls.css = (root / "web" / "styles.css").read_text(encoding="utf-8")

    def test_export_is_a_distinct_sidebar_module(self):
        self.assertIn('data-view="export"', self.html)
        self.assertIn("package-open", self.html)
        self.assertIn('data-active-view="export"', self.css)

    def test_all_delivery_formats_are_exposed(self):
        for export_format in ("png_bundle", "vertical_comic", "pdf", "video"):
            self.assertIn(f'value: "{export_format}"', self.js)

    def test_export_uses_user_selected_generated_shots_and_export_endpoint(self):
        self.assertIn("data-export-shot-id", self.js)
        self.assertIn("selectedExportShotIds", self.js)
        self.assertIn("shot_ids:", self.js)
        self.assertIn('/exports`', self.js)
        export_function = self.js.split("async function downloadProjectExport()", 1)[1].split("function updatePath", 1)[0]
        self.assertNotIn("/api/generate", export_function)


if __name__ == "__main__":
    unittest.main()
