#!/usr/bin/env python3
"""Validate mechanical requirements in a storyboard Markdown file."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


UNIT_RE = re.compile(r"(?m)^\[第\d+集-第\d+单元(?:·[^\] /]+)?\s*/[^\]]+\]\s*$")
REQUIRED_FIELDS = (
    "分镜类型：",
    "场景：",
    "时间：",
    "出场人物：",
    "时长：",
    "画面综述：",
    "其他要求：",
)


def split_units(text: str) -> list[tuple[str, str]]:
    matches = list(UNIT_RE.finditer(text))
    units: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        units.append((match.group(0), text[match.start() : end]))
    return units


def load_project_style(storyboard_path: Path) -> str:
    """Load the active visual style instead of assuming a fixed 3D template."""
    candidates = [Path.cwd() / "project.json"]
    candidates.extend(parent / "project.json" for parent in storyboard_path.resolve().parents)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        try:
            project = json.loads(resolved.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        style = str(project.get("default_visual_style", "")).strip()
        if style:
            return style
    return ""


def validate_unit(title: str, body: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in body:
            errors.append(f"{title} 缺少字段：{field}")

    if not re.search(r"(?m)^镜号\s*\d+", body):
        errors.append(f"{title} 没有镜号")

    duration = re.search(r"(?m)^时长：\s*(?:0\s*-\s*)?(\d+)\s*秒", body)
    if not duration:
        errors.append(f"{title} 无法识别单元时长")
    elif int(duration.group(1)) > 15:
        errors.append(f"{title} 单元时长超过 15 秒")

    estimated = re.search(r"(?m)^预计时长：\s*(\d+)(?:\s*[-~—–至]\s*(\d+))?\s*秒", body)
    if not estimated:
        warnings.append(f"{title} 缺少可演时长范围；旧分镜可忽略，新分镜应填写预计时长")
    else:
        lower = int(estimated.group(1))
        upper = int(estimated.group(2) or estimated.group(1))
        if lower > upper:
            errors.append(f"{title} 预计时长范围起止倒置")
        if upper > 15:
            errors.append(f"{title} 预计时长上限超过 15 秒")

    output_mode = re.search(r"(?m)^输出模式：\s*(\S+)", body)
    if not output_mode:
        warnings.append(f"{title} 缺少输出模式；旧分镜可忽略，新分镜应写文字版或带图版")
    elif output_mode.group(1) not in {"文字版", "带图版"}:
        errors.append(f"{title} 输出模式只能是文字版或带图版")
    elif output_mode.group(1) == "带图版" and not re.search(r"(?m)^预览图：\s*\S+", body):
        warnings.append(f"{title} 标记为带图版，但尚未记录预览图结果")

    estimate = re.search(r"镜头时长估算：([^\n]+)", body)
    if not estimate:
        errors.append(f"{title} 缺少镜头时长估算")
    else:
        spans = [
            (int(start), int(end))
            for start, end in re.findall(r"镜号\s*\d+\s+(\d+)\s*-\s*(\d+)\s*秒", estimate.group(1))
        ]
        if not spans:
            errors.append(f"{title} 无法解析镜头时间轴")
        else:
            if spans[0][0] != 0:
                errors.append(f"{title} 时间轴不是从 0 秒开始")
            for previous, current in zip(spans, spans[1:]):
                if previous[1] != current[0]:
                    errors.append(f"{title} 时间轴在 {previous[1]}-{current[0]} 秒之间不连续")
            if any(start >= end for start, end in spans):
                errors.append(f"{title} 存在起止时间倒置或零时长镜头")
            if spans[-1][1] > 15:
                errors.append(f"{title} 镜头时间轴超过 15 秒")

    shot_count = len(re.findall(r"(?m)^镜号\s*\d+", body))
    if shot_count > 7:
        warnings.append(f"{title} 包含 {shot_count} 个镜头，请确认没有因复杂度过高而拆得过碎")

    return errors, warnings


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：validate_storyboard.py <分镜脚本.md>")
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"错误：文件不存在：{path}")
        return 2

    text = path.read_text(encoding="utf-8-sig")
    units = split_units(text)
    errors: list[str] = []
    warnings: list[str] = []

    if not units:
        errors.append("没有找到形如 [第X集-第Y单元 / 演员名] 的单元标题")

    if "9:16" in text or "竖屏" in text:
        errors.append("发现竖屏或 9:16 表述，项目必须使用 16:9 横屏")

    if re.search(r"(?i)l-cut", text):
        errors.append("发现 L-cut 剪辑术语；请改为自然的画面与声音描述，避免模型误读")

    if re.search(r"\d+(?:\.\d+)?\s*字/秒", text):
        errors.append("发现字速数值；语速仅用于内部估时，不得写入视频生成提示")

    project_style = load_project_style(path)
    if project_style:
        style_count = text.count(project_style)
        if units and style_count < len(units):
            errors.append(f"项目画面风格出现 {style_count} 次，少于单元数 {len(units)}")
    else:
        warnings.append("project.json 未提供 default_visual_style，无法校验画面风格")

    if len(units) > 4:
        warnings.append("文件包含超过 4 个单元；若这是多批结果汇总可忽略，否则请拆批输出")

    for title, body in units:
        unit_errors, unit_warnings = validate_unit(title, body)
        errors.extend(unit_errors)
        warnings.extend(unit_warnings)

    for warning in warnings:
        print(f"警告：{warning}")
    for error in errors:
        print(f"错误：{error}")

    if errors:
        print(f"校验失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1

    print(f"校验通过：{len(units)} 个单元，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
