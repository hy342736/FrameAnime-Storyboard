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

    def test_automatic_selection_uses_specialized_bubbles(self):
        root = Path(__file__).resolve().parents[1] / "assets" / "bubble-packs"
        library = BubblePackLibrary(root)

        cases = [
            ({"bubbleSemantic": "shout", "text": "住手！", "position": "top-left"}, "d04"),
            ({"bubbleSemantic": "narration", "text": "三天后", "position": "top-left"}, "e05"),
            ({"bubbleSemantic": "dialogue", "text": "……", "position": "top-right"}, "g04"),
            ({"bubbleSemantic": "dialogue", "bubbleIntent": "robot", "text": "识别完成"}, "f06"),
        ]
        for block, expected in cases:
            with self.subTest(block=block):
                self.assertEqual(expected, library.resolve_asset_id("jp-clean-v1", block))

    def test_explicit_asset_wins_over_automatic_selection(self):
        root = Path(__file__).resolve().parents[1] / "assets" / "bubble-packs"
        library = BubblePackLibrary(root)
        block = {
            "bubbleSemantic": "shout",
            "bubbleIntent": "anger",
            "bubbleAssetId": "d05",
            "text": "住手！",
        }
        self.assertEqual("d05", library.resolve_asset_id("jp-clean-v1", block))


if __name__ == "__main__":
    unittest.main()
