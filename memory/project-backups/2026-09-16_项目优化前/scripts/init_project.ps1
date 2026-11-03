[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ProjectName,

    [string]$ProjectType = "AI叙事视频",
    [string]$VisualStyle = ""
)

$ErrorActionPreference = "Stop"

$sourceRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$targetRoot = [System.IO.Path]::GetFullPath($Destination)

if ([string]::IsNullOrWhiteSpace($ProjectName)) {
    throw "ProjectName 不能为空。"
}

if ($targetRoot.TrimEnd('\', '/') -eq $sourceRoot.TrimEnd('\', '/')) {
    throw "目标目录不能是母版目录本身。"
}

if (Test-Path -LiteralPath $targetRoot) {
    $existing = @(Get-ChildItem -Force -LiteralPath $targetRoot)
    if ($existing.Count -gt 0) {
        throw "目标目录不是空目录，初始化已停止：$targetRoot"
    }
} else {
    New-Item -ItemType Directory -Path $targetRoot | Out-Null
}

$copyItems = @(".agents", "templates", "scripts")
foreach ($item in $copyItems) {
    $source = Join-Path $sourceRoot $item
    if (Test-Path -LiteralPath $source) {
        Copy-Item -Recurse -LiteralPath $source -Destination $targetRoot
    }
}

Copy-Item -LiteralPath (Join-Path $sourceRoot "AGENTS.md") -Destination $targetRoot
Copy-Item -LiteralPath (Join-Path $sourceRoot ".gitignore") -Destination $targetRoot
Copy-Item -LiteralPath (Join-Path $sourceRoot "project.json") -Destination $targetRoot

$projectData = Join-Path $targetRoot "项目资料"
$database = Join-Path $projectData "database"
$scriptFolder = Join-Path $projectData "剧本"
$characterOutput = Join-Path $projectData "outputs\人设"
$storyboardOutput = Join-Path $projectData "outputs\分镜"
$memory = Join-Path $targetRoot "memory"
$cache = Join-Path $memory "storyboard-cache"

@($database, $scriptFolder, $characterOutput, $storyboardOutput, $memory, $cache) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

Get-ChildItem -File -LiteralPath (Join-Path $sourceRoot "templates\database") | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $database
}

Get-ChildItem -File -LiteralPath (Join-Path $sourceRoot "templates\memory") | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $memory
}

$configPath = Join-Path $targetRoot "project.json"
$config = Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath | ConvertFrom-Json
$config.project_name = $ProjectName
$config.project_type = $ProjectType
$config.default_visual_style = $VisualStyle
$config.initialized = $true
$config | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -LiteralPath $configPath

$episodeIndexPath = Join-Path $database "分集剧情.json"
$episodeIndex = Get-Content -Raw -Encoding UTF8 -LiteralPath $episodeIndexPath | ConvertFrom-Json
$episodeIndex.项目名称 = $ProjectName
$episodeIndex | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -LiteralPath $episodeIndexPath

$statusPath = Join-Path $memory "aivideo-project-status.md"
$status = Get-Content -Raw -Encoding UTF8 -LiteralPath $statusPath
$status = $status -replace "状态：已创建，等待导入资料", "状态：已初始化，等待导入资料"
$status += "`n- 项目名称：$ProjectName`n"
Set-Content -Encoding UTF8 -LiteralPath $statusPath -Value $status

& (Join-Path $targetRoot "scripts\validate_project.ps1") -Root $targetRoot -RequireInitialized

Write-Host "项目初始化完成：$targetRoot"
