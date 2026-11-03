import json
import tempfile
import unittest
from pathlib import Path

from parse_episode import parse_pipe_rows, process_report


SAMPLE_REPORT = """
## 1. 分集剧情摘要
{"ep": 2, "剧情": "测试剧情", "主题": "测试", "角色": ["角色甲"], "凶兽": [], "场景": ["测试场景"]}

## 2. 现有角色本集表现
角色甲：完成一次关键选择

## 3. 新登场角色
角色乙 | 女 | 银色短发 | 调查员 | 冷静 | 短杖 | 首次登场 | 无

## 4. 新登场场景
测试场景 | 双层大厅 | 夜晚 | 冷色顶光 | 中央控制台

## 5. 新登场凶兽
无

## 6. 新道具/制度
记录仪 | 道具 | 记录影像 | 角色乙 | 第2集

## 7. 剧情梗概更新
角色甲在测试场景完成关键选择。

## 8. 人设提示词（中文）
### 角色：角色乙
纯白背景，3D动漫角色设定图。
"""


class ParseEpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name) / "project"
        database = self.project / "database"
        database.mkdir(parents=True)
        (database / "分集剧情.json").write_text(
            json.dumps({"标题": "测试", "说明": "", "集数": []}, ensure_ascii=False), encoding="utf-8"
        )
        (database / "角色.json").write_text(
            json.dumps([{"name": "角色甲", "性别": "男", "首次出现": "第1集"}], ensure_ascii=False),
            encoding="utf-8",
        )
        (database / "场景.json").write_text("[]", encoding="utf-8")
        (database / "外星凶兽.json").write_text("[]", encoding="utf-8")
        (database / "关键道具与制度.json").write_text("{}", encoding="utf-8")
        (database / "剧情梗概.json").write_text('{"关键剧情节点": []}', encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_json(self, name):
        return json.loads((self.project / "database" / name).read_text(encoding="utf-8"))

    def test_updates_are_idempotent(self):
        process_report(SAMPLE_REPORT, self.project, create_backups=False)
        process_report(SAMPLE_REPORT, self.project, create_backups=False)

        episodes = self.read_json("分集剧情.json")["集数"]
        characters = self.read_json("角色.json")
        scenes = self.read_json("场景.json")
        props = self.read_json("关键道具与制度.json")
        outline = self.read_json("剧情梗概.json")["关键剧情节点"]

        self.assertEqual([item["ep"] for item in episodes], [2])
        self.assertEqual(sum(item["name"] == "角色乙" for item in characters), 1)
        self.assertEqual(next(item for item in characters if item["name"] == "角色甲")["第二集表现"], "完成一次关键选择")
        self.assertEqual(sum(item["name"] == "测试场景" for item in scenes), 1)
        self.assertIn("记录仪", props)
        self.assertEqual(outline, ["角色甲在测试场景完成关键选择。"])
        self.assertIn("纯白背景", (self.project / "人设提示词.md").read_text(encoding="utf-8"))

    def test_dry_run_does_not_write(self):
        _, changed = process_report(SAMPLE_REPORT, self.project, dry_run=True)
        self.assertTrue(changed)
        self.assertEqual(self.read_json("分集剧情.json")["集数"], [])
        self.assertFalse((self.project / "人设提示词.md").exists())

    def test_dry_run_does_not_create_project_directory(self):
        missing_project = Path(self.temp_dir.name) / "missing-project"
        report = '## 1. 分集剧情摘要\n{"ep": 1, "剧情": "测试"}'

        _, changed = process_report(report, missing_project, dry_run=True)

        self.assertTrue(changed)
        self.assertFalse(missing_project.exists())

    def test_pipe_table_headers_are_ignored(self):
        rows = parse_pipe_rows("角色名 | 性别 | 外貌\n角色乙 | 女 | 银色短发")
        self.assertEqual([["角色乙", "女", "银色短发"]], rows)


if __name__ == "__main__":
    unittest.main()
