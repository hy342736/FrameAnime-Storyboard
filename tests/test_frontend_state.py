import subprocess
import unittest
from pathlib import Path


class FrontendStateTests(unittest.TestCase):
    def test_multi_character_state_and_reference_mapping(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["node", str(root / "tests" / "frontend_state_test.js")],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("frontend multi-character state tests passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
