#!/usr/bin/env python3
"""Validate AIvideo skills, project databases, memory layout, and Python sources."""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yaml", ".yml"}
SKIP_DIRS = {".git", ".backups", ".venv", "__pycache__", "node_modules"}
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REFERENCE_RE = re.compile(r"references/[A-Za-z0-9_./-]+\.md")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"AGENTS.md", ".gitignore"}:
            yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def validate_conflict_markers(root: Path, result: ValidationResult) -> None:
    for path in iter_text_files(root):
        try:
            lines = read_text(path).splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("<<<<<<< ") or stripped == "=======" or stripped.startswith(">>>>>>> "):
                result.error(f"{relative(path, root)}:{number}: 存在未解决的 Git 冲突标记")


def parse_frontmatter(path: Path, root: Path, result: ValidationResult) -> dict[str, str] | None:
    lines = read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        result.error(f"{relative(path, root)}: SKILL.md 缺少开头 YAML frontmatter")
        return None

    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        result.error(f"{relative(path, root)}: SKILL.md frontmatter 未闭合")
        return None

    values: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            result.error(f"{relative(path, root)}:{number}: frontmatter 字段格式无效")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in values:
            result.error(f"{relative(path, root)}:{number}: frontmatter 字段 `{key}` 重复")
        values[key] = value.strip()

    allowed = {"name", "description"}
    unknown = sorted(set(values) - allowed)
    missing = sorted(allowed - set(values))
    if unknown:
        result.error(f"{relative(path, root)}: frontmatter 含不支持字段：{', '.join(unknown)}")
    if missing:
        result.error(f"{relative(path, root)}: frontmatter 缺少字段：{', '.join(missing)}")
    return values


def validate_skills(root: Path, result: ValidationResult) -> None:
    skills_root = root / ".agents" / "skills"
    if not skills_root.exists():
        result.error(".agents/skills: 技能目录不存在")
        return

    for path in sorted(skills_root.glob("*/SKILL.md")):
        values = parse_frontmatter(path, root, result)
        text = read_text(path)
        line_count = len(text.splitlines())
        if line_count > 500:
            result.error(f"{relative(path, root)}: 共 {line_count} 行，超过 500 行维护上限")
        elif line_count > 400:
            result.warning(f"{relative(path, root)}: 共 {line_count} 行，建议继续拆分 references")

        if values:
            name = values.get("name", "")
            if not SKILL_NAME_RE.fullmatch(name):
                result.error(f"{relative(path, root)}: skill name `{name}` 不是小写连字符格式")
            if name != path.parent.name:
                result.error(
                    f"{relative(path, root)}: skill name `{name}` 与目录 `{path.parent.name}` 不一致"
                )
            if not values.get("description"):
                result.error(f"{relative(path, root)}: description 不能为空")

        for reference in sorted(set(REFERENCE_RE.findall(text))):
            target = path.parent / Path(reference)
            if not target.is_file():
                result.error(f"{relative(path, root)}: 引用文件不存在：{reference}")


def find_duplicate_names(node: Any, location: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, list):
        names = [item.get("name") for item in node if isinstance(item, dict) and item.get("name")]
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        for name in sorted(duplicates):
            yield location, name
        for index, item in enumerate(node):
            yield from find_duplicate_names(item, f"{location}[{index}]")
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from find_duplicate_names(value, f"{location}.{key}")


def validate_episode_list(path: Path, data: Any, root: Path, result: ValidationResult) -> None:
    if path.name != "分集剧情.json":
        return
    episodes = data.get("集数") if isinstance(data, dict) else None
    if not isinstance(episodes, list):
        result.error(f"{relative(path, root)}: 缺少数组字段 `集数`")
        return

    numbers = [item.get("ep") for item in episodes if isinstance(item, dict)]
    if len(numbers) != len(episodes) or any(not isinstance(number, int) for number in numbers):
        result.error(f"{relative(path, root)}: 每条分集记录必须包含整数 `ep`")
        return

    duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
    if duplicates:
        result.error(f"{relative(path, root)}: 重复集数：{duplicates}")
    if numbers:
        expected = set(range(1, max(numbers) + 1))
        missing = sorted(expected - set(numbers))
        if missing:
            result.error(f"{relative(path, root)}: 缺少集数：{missing}")
        if numbers != sorted(numbers):
            result.error(f"{relative(path, root)}: 分集记录未按 `ep` 升序排列")


def validate_json_databases(root: Path, result: ValidationResult) -> None:
    database_root = root / "剧本文件夹" / "database"
    if not database_root.exists():
        result.warning("剧本文件夹/database: 当前工作区没有默认项目数据库")
        return

    for path in sorted(database_root.glob("*.json")):
        try:
            data = json.loads(read_text(path))
        except (OSError, json.JSONDecodeError) as exc:
            result.error(f"{relative(path, root)}: JSON 无法解析：{exc}")
            continue
        for location, name in find_duplicate_names(data):
            result.error(f"{relative(path, root)}:{location}: 重复 name：{name}")
        validate_episode_list(path, data, root, result)


def validate_memory_layout(root: Path, result: ValidationResult) -> None:
    cache_root = root / "memory" / "storyboard-cache"
    if not cache_root.exists():
        return
    for path in cache_root.glob("*.md"):
        result.error(f"{relative(path, root)}: 分镜缓存必须放入 `<project-id>/` 子目录")
    for path in cache_root.glob("*/*.md"):
        text = read_text(path)
        if "项目标识" not in text:
            result.error(f"{relative(path, root)}: 缓存缺少 `项目标识`")


def validate_python_sources(root: Path, result: ValidationResult) -> None:
    for path in [root / "parse_episode.py", root / "scripts" / "validate_project.py"]:
        if not path.exists():
            result.error(f"{relative(path, root)}: Python 源文件不存在")
            continue
        try:
            ast.parse(read_text(path), filename=str(path))
        except SyntaxError as exc:
            result.error(f"{relative(path, root)}:{exc.lineno}: Python 语法错误：{exc.msg}")


def validate(root: Path = ROOT) -> ValidationResult:
    result = ValidationResult()
    validate_conflict_markers(root, result)
    validate_skills(root, result)
    validate_json_databases(root, result)
    validate_memory_layout(root, result)
    validate_python_sources(root, result)
    return result


def main() -> int:
    result = validate(ROOT)
    for message in result.errors:
        print(f"ERROR: {message}")
    for message in result.warnings:
        print(f"WARN: {message}")
    print(f"Validation complete: {len(result.errors)} error(s), {len(result.warnings)} warning(s).")
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
