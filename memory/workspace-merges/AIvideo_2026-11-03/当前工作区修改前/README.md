# AIvideo 人设与分镜工作区

从根目录 `project.json` 开始。它决定当前项目、画风和资料路径；同一工作区保留的历史项目不自动参与当前制作。

## 常用入口

| 要做的事 | 入口 |
| --- | --- |
| 查看当前制作进度 | `project.json.paths.project_status`；未配置时看 `memory/aivideo-project-status.md` |
| 继续制作分镜 | `paths.storyboard_cache` 中对应集、章节的缓存，再读当前剧情行 |
| 查看当前剧本与数据库 | `paths.scripts`、`paths.database` |
| 查看最新人设与正式分镜 | `paths.character_prompts`、`paths.storyboards` |
| 查看项目专属分镜要求 | `paths.storyboard_rules`（如已配置） |
| 查看通用约束与技能路由 | `AGENTS.md` |

续写只读本次相关缓存和资料；开场、不同章节、补镜各自的状态不能互相覆盖。用户未指定新剧情时不自行推进。

## 检查项目

在项目根目录使用 PowerShell 7：

```powershell
pwsh -File scripts/validate_project.ps1 -RequireInitialized
```

检查当前配置指向的目录、六份数据库、项目名称、预览图归属、时长和批次上限、固定提示词结束句。尚未生成的人设文件和预览图不要求预先存在。没有确认画风时提示待确认，不替用户选择。

可在 PowerShell 中指定 `-ForbiddenTerms @('要排查的旧角色名')` 搜索当前项目的残留文字；备份、工具依赖和配置之外的历史目录不参与。该选项按字面匹配，历史资料说明中提到的旧名称也会命中，需人工判断。

## 新建独立项目

```powershell
pwsh -File scripts/init_project.ps1 -Destination '新项目目录' -ProjectName '项目名称' -VisualStyle '已确认的画风'
```

目标必须是空目录。初始化使用 `templates/project.json`、空数据库、通用记忆模板及工作技能，不复制当前剧本、角色、画风、专属分镜规则或产出。未提供画风时保留待确认状态。初始化后的资料导入与校准遵循 `AGENTS.md`。

当前制作配置保存在根目录，通用初始化配置保存在 `templates/project.json`。以后新增通用配置时同步维护模板，避免把单剧要求写进母版。

## 验证维护工具

```powershell
pwsh -File scripts/test_project_tools.ps1
```

测试会在临时目录建立独立样例，验证初始化隔离、非空目录保护、自定义数据库路径、损坏数据、预览图路径、空数组及历史目录排除；不写入当前剧本或分镜。
