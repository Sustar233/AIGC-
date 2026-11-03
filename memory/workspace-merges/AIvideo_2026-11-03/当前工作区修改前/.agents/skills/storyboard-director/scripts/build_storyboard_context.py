#!/usr/bin/env python3
"""Print the minimum context needed for one storyboard batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CONTINUATION_KEYS = (
    "本集场次与地点",
    "场地固定结构",
    "出场人物与不可变外观",
    "当前人物性格与OOC摘要",
    "稳定声线",
    "惯用手、武器、能力源点",
    "关键道具及状态",
    "视觉参考与锚点",
    "已完成单元",
    "上一批末态",
)

NEW_EPISODE_KEYS = (
    "本集场次与地点",
    "场地固定结构",
    "出场人物与不可变外观",
    "当前人物性格与OOC摘要",
    "稳定声线",
    "人物关系与初始站位",
    "惯用手、武器、能力源点",
    "关键道具及状态",
    "视觉参考与锚点",
    "台词与 OS 边界",
    "多人/战斗/特效风险单元",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root; defaults to current directory")
    parser.add_argument("--episode", type=int, required=True)
    parser.add_argument("--script", help="Script path relative to project root")
    parser.add_argument("--start", type=int, help="First one-based script line")
    parser.add_argument("--end", type=int, help="Last one-based script line")
    parser.add_argument("--new-episode", action="store_true")
    parser.add_argument("--character", action="append", default=[], help="Current character name; repeat as needed")
    parser.add_argument("--scene", help="Current scene name")
    parser.add_argument("--prop", action="append", default=[], help="Current key prop name; repeat as needed")
    parser.add_argument("--output-mode", choices=("文字版", "带图版"), help="Storyboard output mode")
    return parser.parse_args()


def load_project(root: Path) -> dict:
    with (root / "project.json").open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def names_for(item: dict[str, Any]) -> list[str]:
    name = item.get("名称", item.get("name", ""))
    aliases = item.get("别名", item.get("aliases", []))
    if isinstance(aliases, str):
        aliases = [aliases]
    return [str(value).strip() for value in [name, *aliases] if str(value).strip()]


def find_named(items: list[dict[str, Any]], requested: str) -> dict[str, Any] | None:
    needle = requested.casefold().strip()
    for item in items:
        if any(name.casefold() == needle for name in names_for(item)):
            return item
    for item in items:
        if any(needle in name.casefold() or name.casefold() in needle for name in names_for(item)):
            return item
    return None


def compact(item: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: item[field] for field in fields if field in item and item[field] not in (None, "", [], {})}


def asset_summaries(root: Path, project: dict, characters: list[str], scene: str | None, props: list[str]) -> list[str]:
    database = root / project.get("paths", {}).get("database", "项目资料/database")
    output: list[str] = []

    if characters:
        character_data = load_json(database / "角色.json")
        character_items = character_data if isinstance(character_data, list) else []
        fields = (
            "名称", "别名", "身份", "性格与表演", "性格", "OOC限制", "外观锚点", "视觉锚点",
            "正式声线", "声线提示词", "能力与动作", "能力", "武器", "绑定道具", "状态变化",
        )
        for name in characters:
            item = find_named(character_items, name)
            if item:
                output.append(f"- 角色 {name}：{json.dumps(compact(item, fields), ensure_ascii=False)}")
            else:
                output.append(f"- 角色 {name}：未匹配；待确认或先运行 script-analyzer。")

    if scene:
        scene_data = load_json(database / "场景.json")
        scene_items = scene_data if isinstance(scene_data, list) else []
        fields = (
            "名称", "别名", "场景类型", "空间结构", "固定空间元素", "允许变化元素", "入口与动线",
            "关键标志物", "可交互物", "光源", "参考图",
        )
        item = find_named(scene_items, scene)
        if item:
            output.append(f"- 场景 {scene}：{json.dumps(compact(item, fields), ensure_ascii=False)}")
        else:
            output.append(f"- 场景 {scene}：未匹配；待确认是否为新增场景或已有场景子区域。")

    if props:
        prop_data = load_json(database / "道具与制度.json")
        if isinstance(prop_data, dict):
            prop_items = prop_data.get("关键道具", [])
        else:
            prop_items = prop_data if isinstance(prop_data, list) else []
        fields = (
            "名称", "别名", "类型", "视觉与动作", "核心轮廓", "关键结构", "关键颜色/材质",
            "状态", "参考图",
        )
        for name in props:
            item = find_named(prop_items, name)
            if item:
                output.append(f"- 关键道具 {name}：{json.dumps(compact(item, fields), ensure_ascii=False)}")
            else:
                output.append(f"- 关键道具 {name}：未匹配；待确认是否需要建立资产。")

    return output


def cache_items(cache_path: Path, keys: tuple[str, ...]) -> list[str]:
    if not cache_path.exists():
        return ["- 缓存：不存在；这是新集时应先建立缓存。"]

    selected: list[str] = []
    for raw_line in cache_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        for key in keys:
            if line.startswith(f"- {key}："):
                selected.append(line)
                break
    return selected


def script_excerpt(root: Path, script: str | None, start: int | None, end: int | None) -> list[str]:
    if not script:
        return []
    if start is None or end is None or start < 1 or end < start:
        raise SystemExit("--script requires valid --start and --end line numbers")

    script_path = root / script
    lines = script_path.read_text(encoding="utf-8-sig").splitlines()
    stop = min(end, len(lines))
    return [f"{number}: {lines[number - 1]}" for number in range(start, stop + 1)]


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    project = load_project(root)
    workflow = project.get("workflow", {}).get("storyboard_generation", {})
    output_mode = args.output_mode or workflow.get("default_output_mode", "文字版")
    keys = NEW_EPISODE_KEYS if args.new_episode else CONTINUATION_KEYS
    cache_path = root / "memory" / "storyboard-cache" / f"第{args.episode}集.md"

    print("# 分镜最小上下文")
    print(f"- 项目：{project.get('project_name', '待确认')}")
    print(f"- 默认模式：{workflow.get('default_detail', project.get('workflow', {}).get('default_storyboard_mode', '标准版'))}")
    print(f"- 输出模式：{output_mode}")
    print(f"- 画面风格：{project.get('default_visual_style', '')}")
    print("\n## 连续性缓存")
    for item in cache_items(cache_path, keys):
        print(item)

    summaries = asset_summaries(root, project, args.character, args.scene, args.prop)
    if summaries:
        print("\n## 当前资产摘要")
        for item in summaries:
            print(item)

    excerpt = script_excerpt(root, args.script, args.start, args.end)
    if excerpt:
        print("\n## 本次剧本行")
        for item in excerpt:
            print(item)


if __name__ == "__main__":
    main()
