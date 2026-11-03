# AIvideo 工作区记忆索引

本文件只保存跨项目通用约定。题材设定、角色、服装、平台参数和制作进度必须放在各自的项目目录中，不能作为其他项目的默认值。

## 通用约定

- 人设任务使用 `ai-short-drama-character`，并先读取当前项目资料。
- 日常分镜使用 `storyboard-director`；连续战斗单元再调用 `seedance-combat-prompt`。
- 新剧本导入或资料缺失时，使用 `script-analyzer` 做最小必要提取。
- 分镜缓存按 `memory/storyboard-cache/<project-id>/` 隔离。
- 项目规则和状态按 `memory/projects/<project-id>/` 隔离。
- 发现会改变剧情逻辑、角色身份或关键连续性的严重问题时，先暂停并向用户确认。
- 用户要求简要解析时，只做剧情归纳和必要问题提示，不自动扩展视觉资产或正式分镜。

## 当前项目

- 《鹿城》（2D 搞笑动画）：[`../鹿城/项目资料归纳.md`](../鹿城/项目资料归纳.md)。用户于 2026-10-09 指定本次接管聊天后续负责该项目；不改变其他聊天的项目归属。
- 《鹿城》规则与状态：[`projects/lucheng/project-rules.md`](projects/lucheng/project-rules.md)、[`projects/lucheng/status.md`](projects/lucheng/status.md)。
- 《琥珀之城》：[`projects/amber-city/project-rules.md`](projects/amber-city/project-rules.md)
- 《琥珀之城》状态：[`projects/amber-city/status.md`](projects/amber-city/status.md)
- 《琥珀之城》分镜缓存：[`storyboard-cache/amber-city/`](storyboard-cache/amber-city/)
