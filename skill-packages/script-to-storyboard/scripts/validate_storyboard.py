#!/usr/bin/env python3
"""Validate the mechanical structure of a Chinese AI-video storyboard."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


UNIT_START_RE = re.compile(r"(?m)^画面比例：")
TITLE_RE = re.compile(
    r"(?m)^##\s*(?:\[第\d+集-第\d+单元(?:·[^\]]+)?\]|第\d+集-第\d+单元(?:·[^\n]+)?)\s*$"
)
SHOT_RE = re.compile(r"(?m)^###\s*镜号\s*(\d+)\s*$")
REQUIRED_FIELDS = (
    "画面比例：",
    "画面风格：",
    "目标模型：",
    "单元名称：",
    "分镜模式：",
    "分镜类型：",
    "场景：",
    "时间：",
    "出场人物：",
    "时长：",
    "画面综述：",
    "其他要求：",
)
SHOT_FIELDS = ("镜头语言：", "画面描述：", "台词：", "音效：")
FORBIDDEN_PLACEHOLDERS = ("同上", "承接上一单元", "承接上集", "豁免标注")
DASH = r"[-—–]"


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def normalize_ratio(value: str) -> str | None:
    match = re.search(r"(\d+)\s*:\s*(\d+)", value)
    return f"{match.group(1)}:{match.group(2)}" if match else None


def split_units(text: str) -> list[str]:
    starts = [match.start() for match in UNIT_START_RE.finditer(text)]
    return [
        text[start : starts[index + 1] if index + 1 < len(starts) else len(text)]
        for index, start in enumerate(starts)
    ]


def display_title(unit: str, index: int) -> str:
    match = TITLE_RE.search(unit)
    return match.group(0).lstrip("# ") if match else f"第 {index} 个单元"


def validate_shots(unit: str, title: str, report: Report) -> list[int]:
    matches = list(SHOT_RE.finditer(unit))
    if not matches:
        report.error(f"{title}：没有找到形如“### 镜号 1”的镜号")
        return []

    numbers = [int(match.group(1)) for match in matches]
    if numbers != list(range(1, len(numbers) + 1)):
        report.error(f"{title}：镜号必须从 1 开始连续编号，当前为 {numbers}")

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(unit)
        body = unit[match.end() : end]
        for required in SHOT_FIELDS:
            if required not in body:
                report.error(f"{title} 镜号 {numbers[index]}：缺少字段“{required}”")
    return numbers


def parse_duration(unit: str, title: str, report: Report) -> int | None:
    match = re.search(r"(?m)^时长：\s*(\d+)\s*秒\s*$", unit)
    if not match:
        report.error(f"{title}：时长必须填写为实际整数秒，例如“时长：12秒”")
        return None
    duration = int(match.group(1))
    if not 1 <= duration <= 15:
        report.error(f"{title}：单元时长为 {duration} 秒，必须在 1—15 秒之间")
    return duration


def validate_timeline(
    unit: str,
    title: str,
    shot_numbers: list[int],
    duration: int | None,
    report: Report,
) -> None:
    line = re.search(r"(?m)^-\s*镜头时长估算：([^\n]+)$", unit)
    if not line:
        report.error(f"{title}：其他要求第一项缺少“镜头时长估算”")
        return

    spans = [
        (int(number), int(start), int(end))
        for number, start, end in re.findall(
            rf"镜号\s*(\d+)\s+(\d+)\s*{DASH}\s*(\d+)\s*秒", line.group(1)
        )
    ]
    if not spans:
        report.error(f"{title}：无法解析镜头时间轴")
        return

    timeline_numbers = [number for number, _, _ in spans]
    if shot_numbers and timeline_numbers != shot_numbers:
        report.error(
            f"{title}：时间轴镜号 {timeline_numbers} 与正文镜号 {shot_numbers} 不一致"
        )
    if spans[0][1] != 0:
        report.error(f"{title}：时间轴必须从 0 秒开始")

    for number, start, end in spans:
        if start >= end:
            report.error(f"{title} 镜号 {number}：时间段 {start}-{end} 秒不是正时长")
    for previous, current in zip(spans, spans[1:]):
        if previous[2] != current[1]:
            report.error(
                f"{title}：时间轴在 {previous[2]} 秒与 {current[1]} 秒之间不连续"
            )
    if duration is not None and spans[-1][2] != duration:
        report.error(
            f"{title}：时间轴结束于 {spans[-1][2]} 秒，与单元时长 {duration} 秒不一致"
        )
    if spans[-1][2] > 15:
        report.error(f"{title}：镜头时间轴超过 15 秒")


def validate_unit(
    unit: str,
    index: int,
    expected_ratio: str | None,
    report: Report,
) -> str | None:
    title = display_title(unit, index)
    title_matches = TITLE_RE.findall(unit)
    if len(title_matches) != 1:
        report.error(f"{title}：每个比例块必须且只能包含一个规范单元标题")

    for required in REQUIRED_FIELDS:
        if required not in unit:
            report.error(f"{title}：缺少字段“{required}”")

    for placeholder in FORBIDDEN_PLACEHOLDERS:
        if placeholder in unit:
            report.error(f"{title}：发现禁用代称“{placeholder}”")

    ratio_line = re.search(r"(?m)^画面比例：\s*(.+)$", unit)
    ratio = normalize_ratio(ratio_line.group(1)) if ratio_line else None
    if ratio is None:
        report.error(f"{title}：画面比例中缺少形如 16:9 的数值")
    elif expected_ratio and ratio != expected_ratio:
        report.error(f"{title}：画面比例为 {ratio}，要求为 {expected_ratio}")

    duration = parse_duration(unit, title, report)
    shot_numbers = validate_shots(unit, title, report)
    validate_timeline(unit, title, shot_numbers, duration, report)
    return ratio


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("storyboard", type=Path, help="UTF-8 Markdown 分镜文件")
    parser.add_argument("--ratio", help="要求的画面比例，例如 16:9 或 9:16")
    parser.add_argument("--max-units", type=int, default=4, help="单批最大单元数，默认 4")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = Report()

    if not args.storyboard.is_file():
        print(f"错误：文件不存在：{args.storyboard}")
        return 2
    if args.max_units < 1:
        print("错误：--max-units 必须为正整数")
        return 2

    expected_ratio = normalize_ratio(args.ratio) if args.ratio else None
    if args.ratio and expected_ratio is None:
        print("错误：--ratio 必须包含形如 16:9 的数值")
        return 2

    text = args.storyboard.read_text(encoding="utf-8-sig")
    units = split_units(text)
    titles = TITLE_RE.findall(text)

    if not units:
        report.error("没有找到以“画面比例：”开头的分镜单元")
    if len(titles) != len(units):
        report.error(
            f"找到 {len(titles)} 个单元标题，但只有 {len(units)} 个“画面比例”块"
        )
    if len(units) > args.max_units:
        report.error(f"单批包含 {len(units)} 个单元，超过上限 {args.max_units}")

    ratios = [
        ratio
        for index, unit in enumerate(units, start=1)
        if (ratio := validate_unit(unit, index, expected_ratio, report)) is not None
    ]
    if len(set(ratios)) > 1:
        report.error(f"同一批次混用了多个画面比例：{sorted(set(ratios))}")

    for warning in report.warnings:
        print(f"警告：{warning}")
    for error in report.errors:
        print(f"错误：{error}")

    if report.errors:
        print(f"校验失败：{len(report.errors)} 个错误，{len(report.warnings)} 个警告")
        return 1
    print(f"校验通过：{len(units)} 个单元，画面比例 {ratios[0] if ratios else '未识别'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
