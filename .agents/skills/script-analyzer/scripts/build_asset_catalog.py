#!/usr/bin/env python3
"""Print a lightweight asset catalog without exposing full project databases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


NAME_KEYS = ("名称", "name", "Name")
ID_KEYS = ("id", "ID", "编号")
ALIAS_KEYS = ("别名", "aliases", "alias", "Aliases", "Alias")
REFERENCE_KEYS = ("参考图", "参考图片", "人设图", "场景图", "reference", "references")
STATUS_KEYS = ("状态", "人设图状态", "场景图状态", "资产状态")
SCENE_ANCHORS = (
    "食堂", "后厨", "教室", "走廊", "校门", "操场", "宿舍", "办公室", "大厅", "客厅", "卧室",
    "街道", "庭院", "广场", "车站", "商店", "仓库", "森林", "山洞", "屋顶", "地下室",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root; defaults to current directory")
    parser.add_argument(
        "--type",
        choices=("all", "character", "scene", "prop"),
        default="all",
        help="Asset type to inspect",
    )
    parser.add_argument("--query", help="Optional name or alias to match")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def first_value(item: dict[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return default


def to_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def has_reference(item: dict[str, Any]) -> bool:
    return any(to_strings(item.get(key)) for key in REFERENCE_KEYS)


def load_assets(database: Path, asset_type: str) -> list[dict[str, Any]]:
    if asset_type == "character":
        data = load_json(database / "角色.json")
        return data if isinstance(data, list) else []
    if asset_type == "scene":
        data = load_json(database / "场景.json")
        return data if isinstance(data, list) else []

    data = load_json(database / "道具与制度.json")
    if isinstance(data, dict):
        props = data.get("关键道具", [])
        return props if isinstance(props, list) else []
    return data if isinstance(data, list) else []


def match_kind(asset_type: str, query: str | None, name: str, aliases: list[str]) -> str | None:
    if not query:
        return "CATALOG"

    needle = query.casefold().strip()
    if name.casefold() == needle:
        return "EXACT_NAME"
    if any(alias.casefold() == needle for alias in aliases):
        return "EXACT_ALIAS"

    candidates = [name, *aliases]
    if any(needle in candidate.casefold() or candidate.casefold() in needle for candidate in candidates):
        return "POSSIBLE_SUBAREA" if asset_type == "scene" else "POSSIBLE_MATCH"
    if asset_type == "scene" and any(anchor in query and any(anchor in candidate for candidate in candidates) for anchor in SCENE_ANCHORS):
        return "POSSIBLE_SUBAREA"
    return None


def reference_stems(root: Path) -> list[str]:
    reference_root = root / "项目资料" / "参考图"
    if not reference_root.is_dir():
        return []
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    return [path.stem.casefold() for path in reference_root.rglob("*") if path.is_file() and path.suffix.casefold() in extensions]


def summarize(asset_type: str, item: dict[str, Any], match: str, filenames: list[str]) -> dict[str, Any]:
    name = str(first_value(item, NAME_KEYS, "")).strip()
    aliases = to_strings(first_value(item, ALIAS_KEYS, []))
    status = str(first_value(item, STATUS_KEYS, "已有条目")).strip() or "已有条目"
    ignored = set(NAME_KEYS + ID_KEYS + ALIAS_KEYS + REFERENCE_KEYS + STATUS_KEYS)
    has_details = any(value not in (None, "", [], {}) for key, value in item.items() if key not in ignored)
    return {
        "asset_type": {"character": "角色", "scene": "场景", "prop": "关键道具"}[asset_type],
        "id": first_value(item, ID_KEYS, ""),
        "name": name,
        "aliases": aliases,
        "has_reference": has_reference(item) or any(
            candidate.casefold() in stem for candidate in [name, *aliases] if candidate for stem in filenames
        ),
        "has_details": has_details,
        "status": status,
        "match": match,
    }


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    project = load_json(root / "project.json")
    database = root / project.get("paths", {}).get("database", "项目资料/database")
    requested = ("character", "scene", "prop") if args.type == "all" else (args.type,)
    filenames = reference_stems(root)

    results: list[dict[str, Any]] = []
    for asset_type in requested:
        for item in load_assets(database, asset_type):
            if not isinstance(item, dict):
                continue
            name = str(first_value(item, NAME_KEYS, "")).strip()
            if not name:
                continue
            aliases = to_strings(first_value(item, ALIAS_KEYS, []))
            match = match_kind(asset_type, args.query, name, aliases)
            if match:
                results.append(summarize(asset_type, item, match, filenames))

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
