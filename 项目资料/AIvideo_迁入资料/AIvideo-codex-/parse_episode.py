#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse a structured episode report and update one project's data safely."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


SECTION_PATTERN = re.compile(r"(?m)^##\s*(\d+)\.\s*([^\r\n]*)\s*$")
EMPTY_VALUES = {"", "无", "无。", "不需要", "不需要。", "none", "n/a"}


class ParseError(RuntimeError):
    """Raised when the report or project database is structurally invalid."""


def split_sections(text: str) -> dict[int, str]:
    matches = list(SECTION_PATTERN.finditer(text))
    sections: dict[int, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        content = re.sub(r"^={8,}\s*", "", content).strip()
        sections[int(match.group(1))] = content
    return sections


def extract_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ParseError("第1节未找到有效的 JSON 对象")


def is_empty_section(text: str) -> bool:
    normalized = text.strip().strip("` ").lower()
    return normalized in EMPTY_VALUES


def parse_pipe_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    header_names = {"name", "名称", "角色名", "场景名", "凶兽名", "生物名", "条目名"}
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("|")
        if not line or line.startswith(("```", "#", "格式", "---")) or "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if (
            parts
            and parts[0].lower() not in header_names
            and not all(set(part) <= {"-", ":", " "} for part in parts)
        ):
            rows.append(parts)
    return rows


def parse_colon_rows(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-* ")
        if not line or line.startswith(("```", "#", "格式")):
            continue
        parts = re.split(r"[：:]", line, maxsplit=1)
        if len(parts) == 2 and all(parts):
            rows[parts[0].strip()] = parts[1].strip()
    return rows


def chinese_number(value: int) -> str:
    digits = "零一二三四五六七八九"
    if value < 10:
        return digits[value]
    if value < 20:
        return "十" + (digits[value % 10] if value % 10 else "")
    if value < 100:
        return digits[value // 10] + "十" + (digits[value % 10] if value % 10 else "")
    return str(value)


def episode_field(episode: int, suffix: str = "表现") -> str:
    return f"第{chinese_number(episode)}集{suffix}"


def find_asset_file(database_dir: Path) -> Path:
    candidates = (
        "外星凶兽.json",
        "生物.json",
        "怪物.json",
        "生物与怪物.json",
        "creatures.json",
        "assets.json",
    )
    for name in candidates:
        path = database_dir / name
        if path.exists():
            return path
    return database_dir / "生物.json"


@dataclass
class ProjectWriter:
    project_dir: Path
    dry_run: bool = False
    create_backups: bool = True
    staged_json: dict[Path, Any] = field(default_factory=dict)
    staged_text: dict[Path, str] = field(default_factory=dict)

    @property
    def database_dir(self) -> Path:
        return self.project_dir / "database"

    def load_json(self, path: Path, default: Any | None = None) -> Any:
        if path in self.staged_json:
            return self.staged_json[path]
        if not path.exists():
            if default is None:
                raise ParseError(f"缺少数据库文件：{path}")
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParseError(f"无法读取 JSON：{path}：{exc}") from exc

    def stage_json(self, path: Path, data: Any) -> None:
        json.dumps(data, ensure_ascii=False)
        self.staged_json[path] = data

    def stage_text(self, path: Path, text: str) -> None:
        self.staged_text[path] = text.rstrip() + "\n"

    def _backup_root(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return self.project_dir / ".backups" / "parse_episode" / stamp

    def _atomic_write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temp_path = Path(handle.name)
        try:
            with handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    def commit(self) -> list[Path]:
        serialized: dict[Path, str] = {
            path: json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            for path, data in self.staged_json.items()
        }
        serialized.update(self.staged_text)

        changed = [
            path
            for path, text in serialized.items()
            if not path.exists() or path.read_text(encoding="utf-8-sig") != text
        ]
        if self.dry_run or not changed:
            return changed

        backup_root = self._backup_root()
        if self.create_backups:
            for path in changed:
                if path.exists():
                    relative = path.relative_to(self.project_dir)
                    backup_path = backup_root / relative
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, backup_path)

        for path in changed:
            self._atomic_write(path, serialized[path])
        return changed


def require_list(value: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ParseError(f"数据库根结构必须是数组：{path}")
    return value


def process_report(
    text: str,
    project_dir: Path,
    *,
    dry_run: bool = False,
    create_backups: bool = True,
) -> tuple[list[str], list[Path]]:
    sections = split_sections(text)
    if not sections:
        raise ParseError("输入中没有找到形如“## 1. 标题”的章节")
    if 1 not in sections:
        raise ParseError("输入缺少第1节分集剧情摘要")

    writer = ProjectWriter(project_dir.resolve(), dry_run, create_backups)
    report: list[str] = []

    episode_data = extract_json_object(sections[1])
    if "ep" not in episode_data:
        raise ParseError("第1节 JSON 缺少 ep 字段")
    try:
        episode = int(episode_data["ep"])
    except (TypeError, ValueError) as exc:
        raise ParseError("ep 必须是整数") from exc
    if episode < 1:
        raise ParseError("ep 必须大于或等于 1")

    episodes_path = writer.database_dir / "分集剧情.json"
    episodes_root = writer.load_json(episodes_path, {"标题": project_dir.name, "说明": "分集剧情", "集数": []})
    if not isinstance(episodes_root, dict) or not isinstance(episodes_root.get("集数"), list):
        raise ParseError(f"分集剧情数据库结构无效：{episodes_path}")
    episodes = episodes_root["集数"]
    existing = next((item for item in episodes if int(item.get("ep", -1)) == episode), None)
    if existing is None:
        episodes.append(episode_data)
        report.append(f"分集剧情：新增第{episode}集")
    else:
        existing.clear()
        existing.update(episode_data)
        report.append(f"分集剧情：更新第{episode}集")
    episodes.sort(key=lambda item: int(item.get("ep", 0)))
    writer.stage_json(episodes_path, episodes_root)

    characters_path = writer.database_dir / "角色.json"
    if 2 in sections and not is_empty_section(sections[2]):
        characters = require_list(writer.load_json(characters_path), characters_path)
        updates = parse_colon_rows(sections[2])
        updated_names: list[str] = []
        for character in characters:
            name = character.get("name")
            if name in updates:
                character[episode_field(episode)] = updates[name]
                updated_names.append(name)
        unknown = sorted(set(updates) - set(updated_names))
        if unknown:
            report.append("角色更新未匹配：" + "、".join(unknown))
        if updated_names:
            writer.stage_json(characters_path, characters)
            report.append("角色更新：" + "、".join(updated_names))

    if 3 in sections and not is_empty_section(sections[3]):
        characters = require_list(writer.load_json(characters_path, []), characters_path)
        known = {item.get("name") for item in characters}
        added: list[str] = []
        for parts in parse_pipe_rows(sections[3]):
            name = parts[0]
            if not name or name in known:
                continue
            values = parts + [""] * (8 - len(parts))
            characters.append(
                {
                    "name": name,
                    "性别": values[1],
                    "外貌": values[2],
                    "身份": values[3],
                    "性格": values[4],
                    "武器/能力": values[5],
                    episode_field(episode): values[6],
                    "首次出现": f"第{episode}集",
                    "备注": values[7],
                }
            )
            known.add(name)
            added.append(name)
        if added:
            writer.stage_json(characters_path, characters)
            report.append("新增角色：" + "、".join(added))

    scenes_path = writer.database_dir / "场景.json"
    if 4 in sections and not is_empty_section(sections[4]):
        scenes = require_list(writer.load_json(scenes_path, []), scenes_path)
        known = {item.get("name") for item in scenes}
        added: list[str] = []
        for parts in parse_pipe_rows(sections[4]):
            name = parts[0]
            if not name or name in known:
                continue
            values = parts + [""] * (5 - len(parts))
            scenes.append(
                {
                    "name": name,
                    "描述": values[1],
                    "时间": values[2],
                    "光影": values[3],
                    "关键道具": values[4],
                    "首次出现": f"第{episode}集",
                }
            )
            known.add(name)
            added.append(name)
        if added:
            writer.stage_json(scenes_path, scenes)
            report.append("新增场景：" + "、".join(added))

    if 5 in sections and not is_empty_section(sections[5]):
        assets_path = find_asset_file(writer.database_dir)
        assets = require_list(writer.load_json(assets_path, []), assets_path)
        known = {item.get("name") for item in assets}
        added: list[str] = []
        for parts in parse_pipe_rows(sections[5]):
            name = parts[0]
            if not name or name in known:
                continue
            values = parts + [""] * (4 - len(parts))
            assets.append(
                {
                    "name": name,
                    "描述": values[1],
                    "特性": values[2],
                    episode_field(episode): values[3],
                    "首次出现": f"第{episode}集",
                }
            )
            known.add(name)
            added.append(name)
        if added:
            writer.stage_json(assets_path, assets)
            report.append("新增生物/灵体：" + "、".join(added))

    props_path = writer.database_dir / "关键道具与制度.json"
    if 6 in sections and not is_empty_section(sections[6]):
        props = writer.load_json(props_path, {})
        if not isinstance(props, dict):
            raise ParseError(f"道具数据库根结构必须是对象：{props_path}")
        added: list[str] = []
        for parts in parse_pipe_rows(sections[6]):
            name = parts[0]
            if not name or name in props:
                continue
            values = parts + [""] * (5 - len(parts))
            entry = {"类型": values[1], "描述": values[2], "首次出现": values[4] or f"第{episode}集"}
            if values[3]:
                entry["持有者"] = values[3]
            props[name] = entry
            added.append(name)
        if added:
            writer.stage_json(props_path, props)
            report.append("新增道具/制度：" + "、".join(added))

    outline_path = writer.database_dir / "剧情梗概.json"
    if 7 in sections and not is_empty_section(sections[7]):
        outline = writer.load_json(outline_path, {"关键剧情节点": []})
        if not isinstance(outline, dict) or not isinstance(outline.get("关键剧情节点"), list):
            raise ParseError(f"剧情梗概数据库结构无效：{outline_path}")
        node = sections[7].strip()
        if node not in outline["关键剧情节点"]:
            outline["关键剧情节点"].append(node)
            writer.stage_json(outline_path, outline)
            report.append("剧情梗概：追加关键节点")

    if 8 in sections and not is_empty_section(sections[8]):
        prompt_path = writer.project_dir / "人设提示词.md"
        writer.stage_text(
            prompt_path,
            f"# 人设提示词 - 第{episode}集\n\n"
            "> 此文件只保留最新一批已确认提示词。\n\n"
            + sections[8],
        )
        report.append("人设提示词：更新最新版本")

    if 9 in sections and not is_empty_section(sections[9]):
        script_path = writer.project_dir / f"{episode}集剧本.txt"
        writer.stage_text(script_path, sections[9])
        report.append(f"剧本文件：更新 {script_path.name}")

    changed = writer.commit()
    return report, changed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("剧本文件夹"), help="当前项目目录")
    parser.add_argument("--input", type=Path, help="结构化报告文件；省略时从 stdin 读取")
    parser.add_argument("--dry-run", action="store_true", help="完成解析和校验，但不写入文件")
    parser.add_argument("--no-backup", action="store_true", help="写入前不创建本地备份")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = args.input.read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
        report, changed = process_report(
            text,
            args.project_dir,
            dry_run=args.dry_run,
            create_backups=not args.no_backup,
        )
    except (OSError, ParseError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    mode = "检查" if args.dry_run else "更新"
    print(f"=== {mode}结果 ===")
    for item in report:
        print(f"[OK] {item}")
    if changed:
        print("受影响文件：")
        for path in changed:
            print(f"- {path}")
    else:
        print("没有文件变化。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
