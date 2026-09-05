from pathlib import Path
import unittest

from app.bubble_packs import BubblePackLibrary


class BubblePackTests(unittest.TestCase):
    def test_jp_clean_pack_maps_all_supported_semantics_to_existing_pngs(self):
        root = Path(__file__).resolve().parents[1] / "assets" / "bubble-packs"
        library = BubblePackLibrary(root)
        packs = library.list_packs()
        self.assertEqual(["jp-clean-v1"], [pack["id"] for pack in packs])
        pack = packs[0]
        self.assertEqual({"dialogue", "thought", "narration", "shout", "sfx"}, set(pack["semantic_defaults"]))
        for asset_id in pack["semantic_defaults"].values():
            path = library.asset_path(pack["id"], asset_id)
            self.assertTrue(path.is_file())
            self.assertEqual(".png", path.suffix.lower())


if __name__ == "__main__":
    unittest.main()
