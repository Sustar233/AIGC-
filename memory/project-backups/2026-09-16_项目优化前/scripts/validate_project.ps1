[CmdletBinding()]
param(
    [string]$Root = ".",
    [switch]$RequireInitialized,
    [string[]]$ForbiddenTerms = @()
)

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath($Root)
$errors = New-Object System.Collections.Generic.List[string]

$requiredFiles = @(
    "AGENTS.md",
    "project.json",
    "memory\MEMORY.md",
    "memory\project-rules.md",
    "memory\aivideo-project-status.md",
    "项目资料\database\角色.json",
    "项目资料\database\场景.json",
    "项目资料\database\生物与灵体.json",
    "项目资料\database\道具与制度.json",
    "项目资料\database\世界观.json",
    "项目资料\database\分集剧情.json",
    ".agents\skills\ai-short-drama-character\SKILL.md",
    ".agents\skills\storyboard-director\SKILL.md",
    ".agents\skills\seedance-combat-prompt\SKILL.md",
    ".agents\skills\script-analyzer\SKILL.md"
)

foreach ($relativePath in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $errors.Add("缺少必要文件：$relativePath")
    }
}

$jsonFiles = @(
    "project.json",
    "项目资料\database\角色.json",
    "项目资料\database\场景.json",
    "项目资料\database\生物与灵体.json",
    "项目资料\database\道具与制度.json",
    "项目资料\database\世界观.json",
    "项目资料\database\分集剧情.json"
)

foreach ($relativePath in $jsonFiles) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
        try {
            $null = Get-Content -Raw -Encoding UTF8 -LiteralPath $fullPath | ConvertFrom-Json
        } catch {
            $errors.Add("JSON 无效：$relativePath；$($_.Exception.Message)")
        }
    }
}

$configPath = Join-Path $projectRoot "project.json"
if (Test-Path -LiteralPath $configPath -PathType Leaf) {
    try {
        $config = Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath | ConvertFrom-Json
        if ($RequireInitialized -and -not $config.initialized) {
            $errors.Add("project.json 尚未标记为 initialized=true。")
        }
        if ($RequireInitialized -and [string]::IsNullOrWhiteSpace([string]$config.project_name)) {
            $errors.Add("project.json 缺少项目名称。")
        }
    } catch {
        # JSON 错误已在上一轮记录。
    }
}

$legacySynopsisPath = Join-Path $projectRoot "项目资料\database\剧情梗概.json"
if (Test-Path -LiteralPath $legacySynopsisPath -PathType Leaf) {
    $errors.Add("发现已废弃文件：项目资料\database\剧情梗概.json；请将项目级内容迁移到分集剧情.json 的项目总览后删除该文件。")
}

$worldPath = Join-Path $projectRoot "项目资料\database\世界观.json"
if (Test-Path -LiteralPath $worldPath -PathType Leaf) {
    try {
        $world = Get-Content -Raw -Encoding UTF8 -LiteralPath $worldPath | ConvertFrom-Json
        foreach ($field in @("时代与地域", "社会与技术边界", "能力体系", "统一视觉规则", "不可变规则")) {
            if (-not ($world.PSObject.Properties.Name -contains $field)) {
                $errors.Add("世界观.json 缺少字段：$field")
            }
        }
    } catch {
        # JSON 错误已在上一轮记录。
    }
}

$episodePath = Join-Path $projectRoot "项目资料\database\分集剧情.json"
if (Test-Path -LiteralPath $episodePath -PathType Leaf) {
    try {
        $episodes = Get-Content -Raw -Encoding UTF8 -LiteralPath $episodePath | ConvertFrom-Json
        foreach ($field in @("项目名称", "项目总览", "集数")) {
            if (-not ($episodes.PSObject.Properties.Name -contains $field)) {
                $errors.Add("分集剧情.json 缺少字段：$field")
            }
        }
        if ($episodes.PSObject.Properties.Name -contains "项目总览") {
            foreach ($field in @("一句话梗概", "主线目标", "主要矛盾", "阶段节点")) {
                if (-not ($episodes.项目总览.PSObject.Properties.Name -contains $field)) {
                    $errors.Add("分集剧情.json 的项目总览缺少字段：$field")
                }
            }
        }
    } catch {
        # JSON 错误已在上一轮记录。
    }
}

if ($ForbiddenTerms.Count -gt 0) {
    $textFiles = Get-ChildItem -Recurse -File -LiteralPath $projectRoot | Where-Object {
        $_.FullName -notmatch "\\.git(\\|$)" -and
        $_.Extension -in @(".md", ".json", ".txt", ".ps1", ".py", ".yaml", ".yml")
    }

    foreach ($term in $ForbiddenTerms) {
        if ([string]::IsNullOrWhiteSpace($term)) {
            continue
        }
        $matches = $textFiles | Select-String -SimpleMatch -Pattern $term
        foreach ($match in $matches) {
            $relative = $match.Path.Substring($projectRoot.Length).TrimStart('\', '/')
            $errors.Add("发现禁止残留词 '$term'：${relative}:$($match.LineNumber)")
        }
    }
}

if ($errors.Count -gt 0) {
    Write-Host "项目验证失败："
    $errors | ForEach-Object { Write-Host "- $_" }
    throw "项目验证失败，共发现 $($errors.Count) 个问题。"
}

Write-Host "项目验证通过：$projectRoot"
