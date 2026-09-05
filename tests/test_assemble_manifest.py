import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "anime-ai-art-director"
    / "scripts"
    / "assemble_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("assemble_manifest", SCRIPT_PATH)
assemble_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(assemble_module)


class AssembleManifestTests(unittest.TestCase):
    def write_json(self, root: Path, name: str, value) -> Path:
        path = root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_assembles_ordered_chunks_matching_budget(self):
        with tempfile.TemporaryDirectory(prefix="manifest-stage-") as directory:
            root = Path(directory)
            base = self.write_json(root, "base.json", {"preferences": {"panel_budget": 3}, "shots": []})
            first = self.write_json(root, "shots-001-002.json", [{"client_id": "SHOT-001"}, {"client_id": "SHOT-002"}])
            second = self.write_json(root, "shots-003-003.json", [{"client_id": "SHOT-003"}])

            manifest = assemble_module.assemble(base, [first, second])

            self.assertEqual(
                ["SHOT-001", "SHOT-002", "SHOT-003"],
                [shot["client_id"] for shot in manifest["shots"]],
            )

    def test_rejects_duplicate_ids_and_budget_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="manifest-stage-invalid-") as directory:
            root = Path(directory)
            base = self.write_json(root, "base.json", {"preferences": {"panel_budget": 2}})
            duplicate = self.write_json(
                root,
                "duplicate.json",
                [{"client_id": "SHOT-001"}, {"client_id": "SHOT-001"}],
            )
            with self.assertRaisesRegex(ValueError, "duplicate shot client_id"):
                assemble_module.assemble(base, [duplicate])

            one_shot = self.write_json(root, "one.json", [{"client_id": "SHOT-001"}])
            with self.assertRaisesRegex(ValueError, "does not match panel_budget"):
                assemble_module.assemble(base, [one_shot])


if __name__ == "__main__":
    unittest.main()
