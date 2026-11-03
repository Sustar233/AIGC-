#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Root = ".",
    [switch]$RequireInitialized,
    [string[]]$ForbiddenTerms = @()
)

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
$rootPrefix = $projectRoot + [System.IO.Path]::DirectorySeparatorChar
$errors = New-Object System.Collections.Generic.List[string]
$notices = New-Object System.Collections.Generic.List[string]

function Resolve-ProjectPath([object]$Value, [string]$Label) {
    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)) {
        $errors.Add("缺少有效路径：$Label")
        return $null
    }
    if ([System.IO.Path]::IsPathRooted($Value)) {
        $errors.Add("路径必须相对项目根目录：$Label")
        return $null
    }
    try { $full = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Value)) }
    catch { $errors.Add("路径无效：$Label"); return $null }
    if (-not $full.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        $errors.Add("路径超出项目范围或指向根目录：$Label")
        return $null
    }
    return $full
}

function Read-ProjectJson([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $errors.Add("缺少必要文件：$Path")
        return $null
    }
    try {
        $value = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json -NoEnumerate
        if ($null -eq $value) { throw 'JSON 内容为空或为 null' }
        return ,$value
    } catch {
        $errors.Add("JSON 无效：$Path；$($_.Exception.Message)")
        return $null
    }
}

$requiredFiles = @(
    "AGENTS.md", "memory/MEMORY.md", "memory/project-rules.md",
    "memory/aivideo-project-status.md", "templates/project.json",
    ".agents/skills/ai-short-drama-character/SKILL.md",
    ".agents/skills/storyboard-director/SKILL.md",
    ".agents/skills/seedance-combat-prompt/SKILL.md",
    ".agents/skills/script-analyzer/SKILL.md"
)
foreach ($relative in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $relative) -PathType Leaf)) {
        $errors.Add("缺少必要文件：$relative")
    }
}

$config = Read-ProjectJson (Join-Path $projectRoot "project.json")
$resolved = @{}
$db = @{}
if ($null -ne $config) {
    if ($config.initialized -isnot [bool]) { $errors.Add("initialized 必须是布尔值。") }
    if ($RequireInitialized -and $config.initialized -ne $true) {
        $errors.Add("project.json 尚未标记为 initialized=true。")
    }
    if ($config.initialized -eq $true -and [string]::IsNullOrWhiteSpace([string]$config.project_name)) {
        $errors.Add("已初始化项目缺少项目名称。")
    }
    foreach ($key in @('scripts', 'database', 'storyboards', 'storyboard_cache', 'style_references', 'character_prompts')) {
        $resolved[$key] = Resolve-ProjectPath $config.paths.$key "paths.$key"
    }
    foreach ($key in @('scripts', 'database', 'storyboards', 'storyboard_cache', 'style_references')) {
        if ($resolved[$key] -and -not (Test-Path -LiteralPath $resolved[$key] -PathType Container)) {
            $errors.Add("配置目录不存在：paths.$key = $($config.paths.$key)")
        }
    }
    if ($resolved['character_prompts']) {
        $parent = Split-Path $resolved['character_prompts'] -Parent
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
            $errors.Add("人设输出目录不存在：$parent")
        }
    }
    foreach ($key in @('storyboard_rules', 'project_status')) {
        if ($config.paths.PSObject.Properties.Name -contains $key) {
            $resolved[$key] = Resolve-ProjectPath $config.paths.$key "paths.$key"
            if ($resolved[$key] -and -not (Test-Path -LiteralPath $resolved[$key] -PathType Leaf)) {
                $errors.Add("配置文件不存在：paths.$key = $($config.paths.$key)")
            }
        }
    }
    $preview = Resolve-ProjectPath $config.workflow.storyboard_generation.preview.output_path 'workflow.storyboard_generation.preview.output_path'
    if ($preview -and $resolved['storyboards']) {
        $storyboardPrefix = $resolved['storyboards'].TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        if (-not $preview.StartsWith($storyboardPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            $errors.Add("预览图路径必须位于当前配置的分镜目录内。")
        }
    }
    $seconds = $config.workflow.storyboard_generation.max_unit_seconds
    if ($seconds -isnot [ValueType] -or $seconds -is [bool] -or $seconds -le 0 -or $seconds -gt 15) {
        $errors.Add("每单元时长上限必须大于0且不超过15秒。")
    }
    $batch = $config.workflow.max_storyboard_units_per_batch
    if ($batch -isnot [ValueType] -or $batch -is [bool] -or $batch -lt 1 -or $batch -gt 4 -or [math]::Floor($batch) -ne $batch) {
        $errors.Add("每批单元上限必须是1到4的整数。")
    }
    if ($config.workflow.visual_prompt_output.required_suffix -cne '生成4次，每次返回不同图片。') {
        $errors.Add("视觉提示词结束句与工作区固定要求不一致。")
    }
    if ([string]::IsNullOrWhiteSpace([string]$config.default_visual_style)) {
        $notices.Add("默认画风尚未确认；进入视觉制作前需确认。")
    } elseif ([string]::IsNullOrWhiteSpace([string]$config.workflow.visual_prompt_output.scene_style_suffix)) {
        $errors.Add("已配置画风，但缺少固定场景画风后缀。")
    }
    if ($resolved['database']) {
        foreach ($name in @('角色', '场景', '生物与灵体', '道具与制度', '世界观', '分集剧情')) {
            $db[$name] = Read-ProjectJson (Join-Path $resolved['database'] "$name.json")
        }
        if (Test-Path -LiteralPath (Join-Path $resolved['database'] '剧情梗概.json')) {
            $errors.Add("当前数据库包含废弃文件剧情梗概.json；请核对后迁移至分集剧情.json。")
        }
    }
    if ($null -ne $db['世界观']) {
        foreach ($field in @('时代与地域', '社会与技术边界', '能力体系', '统一视觉规则', '不可变规则')) {
            if ($db['世界观'].PSObject.Properties.Name -notcontains $field) {
                $errors.Add("世界观.json 缺少字段：$field")
            }
        }
    }
    if ($null -ne $db['分集剧情']) {
        $episodes = $db['分集剧情']
        foreach ($field in @('项目名称', '项目总览', '集数')) {
            if ($episodes.PSObject.Properties.Name -notcontains $field) {
                $errors.Add("分集剧情.json 缺少字段：$field")
            }
        }
        foreach ($field in @('一句话梗概', '主线目标', '主要矛盾', '阶段节点')) {
            if ($episodes.项目总览.PSObject.Properties.Name -notcontains $field) {
                $errors.Add("分集剧情.json 的项目总览缺少字段：$field")
            }
        }
        if ($episodes.项目名称 -cne $config.project_name) {
            $errors.Add("分集剧情.json 的项目名称与 project.json 不一致。")
        }
    }
}

# 只搜索当前制作范围；遍历时即跳过备份、工具环境与媒体帧，不先扫描全仓库。
function Get-ScopedTextFiles([string]$Path) {
    $item = Get-Item -LiteralPath $Path
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { return }
    if (-not $item.PSIsContainer) {
        if ($item.Extension -in @('.md', '.json', '.txt', '.ps1', '.py', '.yaml', '.yml')) { $item.FullName }
        return
    }
    foreach ($child in Get-ChildItem -LiteralPath $Path -Force) {
        if ($child.Name -in @('.git', '.venv', 'venv', 'node_modules', '__pycache__', 'project-backups', 'storyboard-backups', 'skill-backups', 'frames', '视频帧', '核验帧')) { continue }
        Get-ScopedTextFiles $child.FullName
    }
}
if ($ForbiddenTerms.Count -gt 0 -and $null -ne $config) {
    $scope = @((Join-Path $projectRoot 'project.json'), (Join-Path $projectRoot 'memory/MEMORY.md'), (Join-Path $projectRoot 'memory/project-rules.md'), (Join-Path $projectRoot 'memory/aivideo-project-status.md'))
    $scope += @($resolved.Values | Where-Object { $_ })
    $textFiles = @($scope | Where-Object { Test-Path -LiteralPath $_ } | ForEach-Object { Get-ScopedTextFiles $_ } | Sort-Object -Unique)
    foreach ($term in $ForbiddenTerms) {
        if ([string]::IsNullOrWhiteSpace($term)) { continue }
        foreach ($path in $textFiles) {
            foreach ($match in Select-String -LiteralPath $path -SimpleMatch -Pattern $term) {
                $relative = $path.Substring($rootPrefix.Length)
                $errors.Add("发现禁止残留词 '$term'：${relative}:$($match.LineNumber)")
            }
        }
    }
}

$notices | ForEach-Object { Write-Warning $_ }
if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Host "- $_" }
    throw "项目验证失败，共发现 $($errors.Count) 个问题。"
}
Write-Host "项目验证通过（当前配置范围）：$projectRoot"
