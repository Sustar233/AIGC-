#!/usr/bin/env python3
"""Validate mechanical requirements in a storyboard Markdown file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FIXED_STYLE = (
    "3D写实动漫风格，电影级三维动画质感，次世代CG渲染，高精角色模型，"
    "富有层次感的体积光影，电影级景深虚化，无明显2D勾线，虚幻引擎5渲染风格"
)
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


def validate_unit(title: str, body: str) -> list[str]:
    errors: list[str] = []

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

    return errors


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

    style_count = text.count(FIXED_STYLE)
    if units and style_count < len(units):
        errors.append(f"固定画面风格出现 {style_count} 次，少于单元数 {len(units)}")

    if len(units) > 4:
        warnings.append("文件包含超过 4 个单元；若这是多批结果汇总可忽略，否则请拆批输出")

    for title, body in units:
        errors.extend(validate_unit(title, body))

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
