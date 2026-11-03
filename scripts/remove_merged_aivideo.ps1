#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$expectedSource = 'C:\Users\浮白文化\Documents\ChatGPT\AIvideo'
$sourceRoot = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $expectedSource).Path).TrimEnd('\')
if ($sourceRoot -cne $expectedSource) { throw '旧工作区解析路径不符，停止删除。' }
if ($sourceRoot -eq $workspaceRoot -or $workspaceRoot.StartsWith($sourceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw '不能删除当前工作区或其父目录。' }
$auditRoot = Join-Path $workspaceRoot 'memory\workspace-merges\AIvideo_2026-11-03'
$manifestPath = Join-Path $auditRoot '迁移清单.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (!$manifest.backup_verified -or $manifest.source_root -cne $expectedSource) { throw '备份校验状态或源路径不符。' }
$backupPath = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $manifest.backup))
if (!$backupPath.StartsWith($auditRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw '备份不在预期目录。' }
if ((Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash -ine $manifest.backup_sha256) { throw '完整备份校验失败。' }
$allItems = @(Get-ChildItem -LiteralPath $sourceRoot -Force -Recurse)
if (@($allItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -gt 0) { throw '源目录含链接，停止删除。' }
$files = @($allItems | Where-Object { !$_.PSIsContainer })
$verifiedEmptyRemainder = $manifest.source_contents_deleted -eq $true -and $files.Count -eq 0 -and $allItems.Count -eq 0
if ($files.Count -ne $manifest.source_files -and !$verifiedEmptyRemainder) { throw '源文件数量发生变化。' }
foreach ($row in $manifest.files) {
    $sourceFile = [IO.Path]::GetFullPath((Join-Path $sourceRoot $row.source))
    if (!$sourceFile.StartsWith($sourceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw '源文件超出授权目录。' }
    if (!$verifiedEmptyRemainder -and (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash -ine $row.sha256) { throw "源文件发生变化：$($row.source)" }
    if ($null -ne $row.destination) {
        $destinationFile = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $row.destination))
        $importRoot = Join-Path $workspaceRoot '项目资料\AIvideo_迁入资料'
        if (!$destinationFile.StartsWith($importRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw '目标文件不在迁入目录。' }
        if ((Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash -ine $row.sha256) { throw "迁入副本校验失败：$($row.destination)" }
    }
}
Write-Host "已核对 $($files.Count) 个源文件、迁入副本及完整备份，删除指定旧目录：$sourceRoot"
Remove-Item -LiteralPath $sourceRoot -Recurse -Force -ErrorAction Stop
if (Test-Path -LiteralPath $sourceRoot) { throw '旧目录仍存在。' }
$manifest.source_deleted = $true
$manifest | Add-Member -NotePropertyName deletion_verified -NotePropertyValue $true -Force
$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Host '旧工作区目录已删除；当前工作区和完整恢复备份均保留。'
