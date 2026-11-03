#requires -Version 7.0
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$tempParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/')
$testRoot = Join-Path $tempParent ('aivideo-tools-test-' + [guid]::NewGuid().ToString('N'))
$fixture = Join-Path $testRoot 'project'
$passed = 0

function Expect-Failure([string]$Name, [scriptblock]$Action, [string]$Message) {
    $caught = $null
    try { & $Action } catch { $caught = $_ }
    if ($null -eq $caught -or $caught.Exception.Message -notmatch $Message) {
        throw "测试失败：$Name；未得到预期错误 $Message"
    }
    $script:passed++
    Write-Host "通过：$Name"
}
function Write-Config($Value) {
    $Value | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 (Join-Path $fixture 'project.json')
}
try {
    New-Item -ItemType Directory -Path $testRoot | Out-Null
    & (Join-Path $sourceRoot 'scripts/init_project.ps1') -Destination $fixture -ProjectName '隔离验证项目' -VisualStyle '二维线稿'
    $config = Get-Content -Raw -Encoding utf8 (Join-Path $fixture 'project.json') | ConvertFrom-Json
    if ($config.paths.database -ne '项目资料/database' -or $config.paths.storyboard_rules -or $config.workflow.storyboard_generation.performance_priority) {
        throw '初始化继承了当前项目专属路径或表演规则。'
    }
    if ($config.default_visual_style -ne '二维线稿' -or $config.workflow.visual_prompt_output.scene_style_suffix -ne '统一场景画风：二维线稿') {
        throw '初始化没有正确应用传入画风。'
    }
    $scriptFiles = @(Get-ChildItem -File -Recurse -LiteralPath (Join-Path $fixture $config.paths.scripts))
    $characters = Get-Content -Raw -Encoding utf8 (Join-Path $fixture '项目资料/database/角色.json') | ConvertFrom-Json -NoEnumerate
    if ($scriptFiles.Count -ne 0 -or $characters.Count -ne 0) { throw '新项目包含旧剧本或角色。' }
    $passed++
    Write-Host '通过：初始化隔离当前项目资料及专属配置'

    Expect-Failure '非空目录保护' { & (Join-Path $sourceRoot 'scripts/init_project.ps1') -Destination $fixture -ProjectName '不应覆盖' } '不是空目录'
    $after = Get-Content -Raw -Encoding utf8 (Join-Path $fixture 'project.json') | ConvertFrom-Json
    if ($after.project_name -ne '隔离验证项目') { throw '非空目录被意外改写。' }

    $other = Join-Path $fixture '当前资料'
    New-Item -ItemType Directory -Path $other | Out-Null
    Copy-Item -Recurse -LiteralPath (Join-Path $fixture '项目资料/database') -Destination $other
    $config.paths.database = '当前资料/database'
    Write-Config $config
    # 刻意损坏旧数据库，当前配置检查仍应通过。
    '{ broken' | Set-Content -Encoding utf8 (Join-Path $fixture '项目资料/database/角色.json')
    & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture -RequireInitialized
    $passed++
    Write-Host '通过：只检查当前配置的数据库（空数组合法）'

    $characterFile = Join-Path $other 'database/角色.json'
    '{ broken' | Set-Content -Encoding utf8 $characterFile
    Expect-Failure '发现当前数据库损坏' { & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture } '项目验证失败'
    '[]' | Set-Content -Encoding utf8 $characterFile
    Move-Item -LiteralPath $characterFile -Destination ($characterFile + '.saved')
    Expect-Failure '发现当前数据库缺失' { & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture } '项目验证失败'
    Move-Item -LiteralPath ($characterFile + '.saved') -Destination $characterFile

    $config.workflow.storyboard_generation.preview.output_path = '旧项目/previews'
    Write-Config $config
    Expect-Failure '发现预览图串入旧目录' { & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture } '项目验证失败'
    $config.workflow.storyboard_generation.preview.output_path = '项目资料/outputs/分镜/previews'
    $config.paths.database = '../越界/database'
    Write-Config $config
    Expect-Failure '拒绝越界资料路径' { & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture } '项目验证失败'
    $config.paths.database = '当前资料/database'
    Write-Config $config

    $episodeFile = Join-Path $other 'database/分集剧情.json'
    $episodes = Get-Content -Raw -Encoding utf8 $episodeFile | ConvertFrom-Json
    $episodes.项目名称 = '错误的旧项目'
    $episodes | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 $episodeFile
    Expect-Failure '发现数据库项目名称不一致' { & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture } '项目验证失败'
    $episodes.项目名称 = $config.project_name
    $episodes | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 $episodeFile

    $archive = Join-Path $fixture 'memory/project-backups'
    New-Item -ItemType Directory -Path $archive | Out-Null
    '仅用于隔离验证的残留标记' | Set-Content -Encoding utf8 (Join-Path $archive '历史.txt')
    & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture -ForbiddenTerms '仅用于隔离验证的残留标记'
    $passed++
    Write-Host '通过：残留词检查排除历史备份'
    '仅用于隔离验证的残留标记' | Set-Content -Encoding utf8 (Join-Path $fixture '项目资料/剧本/当前.txt')
    Expect-Failure '残留词检查覆盖当前剧本' { & (Join-Path $sourceRoot 'scripts/validate_project.ps1') -Root $fixture -ForbiddenTerms '仅用于隔离验证的残留标记' } '项目验证失败'

    & (Join-Path $sourceRoot 'scripts/init_project.ps1') -Destination (Join-Path $testRoot 'no-style') -ProjectName '待确认画风项目'
    $noStyle = Get-Content -Raw -Encoding utf8 (Join-Path $testRoot 'no-style/project.json') | ConvertFrom-Json
    if ($noStyle.default_visual_style -ne '' -or $noStyle.workflow.visual_prompt_output.scene_style_suffix -ne '') { throw '未提供画风时发生默认继承。' }
    $passed++
    Write-Host '通过：未指定画风保持待确认'
    Write-Host "全部 $passed 项集成检查通过。"
} finally {
    # 只清理本次创建、位于系统临时目录下的唯一测试目录。
    $resolvedTest = [IO.Path]::GetFullPath($testRoot)
    if ((Split-Path $resolvedTest -Parent) -ne $tempParent -or (Split-Path $resolvedTest -Leaf) -notmatch '^aivideo-tools-test-[0-9a-f]{32}$') {
        throw "测试目录不满足清理范围：$resolvedTest"
    }
    if (Test-Path -LiteralPath $resolvedTest) { Remove-Item -LiteralPath $resolvedTest -Recurse -Force }
}
