# 项目记忆索引

先读取根目录 [project.json](../project.json)，以其中的项目名称、初始化状态、画风和路径为准。

- [项目规则入口](project-rules.md)：规则来源及最小读取范围。
- [项目状态入口](aivideo-project-status.md)：按配置定位当前制作进度。
- [AIvideo合并资料入口](../项目资料/AIvideo_迁入资料/合并入口.md)：迁入分镜、预览、素材、成片与工具；指定历史片段时按需读取。
- 分镜续写：读取配置 `paths.storyboard_cache` 内对应集/章节的缓存与上一批末态。

只加载当前任务所需资料。`project-backups/`、`storyboard-backups/`、`skill-backups/` 和配置路径之外的旧项目文件属于历史资料，默认不读取。
