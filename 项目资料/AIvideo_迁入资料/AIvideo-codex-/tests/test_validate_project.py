from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_project import ValidationResult, validate_conflict_markers, validate_json_databases


class ProjectValidatorTests(unittest.TestCase):
    def test_conflict_markers_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "broken.md").write_text("<<<<<<< ours\ntext\n=======\nother\n>>>>>>> theirs\n", encoding="utf-8")
            result = ValidationResult()

            validate_conflict_markers(root, result)

            self.assertEqual(3, len(result.errors))

    def test_duplicate_database_names_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "剧本文件夹" / "database"
            database.mkdir(parents=True)
            (database / "角色.json").write_text(
                json.dumps([{"name": "角色甲"}, {"name": "角色甲"}], ensure_ascii=False),
                encoding="utf-8",
            )
            result = ValidationResult()

            validate_json_databases(root, result)

            self.assertEqual(1, len(result.errors))
            self.assertIn("重复 name", result.errors[0])


if __name__ == "__main__":
    unittest.main()
