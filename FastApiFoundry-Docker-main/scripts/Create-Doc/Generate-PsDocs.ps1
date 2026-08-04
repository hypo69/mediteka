# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Generate PowerShell Docs
# =============================================================================
# Description:
#   Generates Markdown documentation from PowerShell comment-based help
#   for ALL .ps1 files in the project (root, scripts/, scripts/Install/, mcp/,
#   check_engine/, src/, tests/, microsoft_sandbox_operations/).
#   Excludes archived files (~), venv/ and site/.
#   Used by GitHub Actions deploy-docs.yml workflow and locally.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Create-Doc\Generate-PsDocs.ps1
#
# File: Generate-PsDocs.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Scan all project directories, not only mcp/src/servers and scripts/
#   - Group index page by directory
#   - Exclude ~, venv/, site/ from scan
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ErrorActionPreference = 'Stop'

$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUT_DIR = Join-Path $PROJECT_ROOT "docs/ru/dev/powershell"
New-Item -ItemType Directory -Force -Path $OUT_DIR | Out-Null

$SKIP_FILE_NAMES = @(
    "test_debug.ps1",
    "test_debug2.ps1",
    "test_debug3.ps1",
    "test_process.ps1"
)

# Файл для фрагмента навигации
$NAV_FRAGMENT = Join-Path $OUT_DIR "nav_fragment.yml"

function Get-RelativeNavPath {
    <#
    .SYNOPSIS
        Возвращает путь к файлу относительно папки docs/ru для использования в nav.
    #>
    param([string]$FullPath)
    $docsRuPath = (Join-Path $PROJECT_ROOT "docs/ru/").Replace("\", "/")
    return $FullPath.Replace("\", "/").Replace($docsRuPath, "")
}

function Get-Synopsis {
    <#
    .SYNOPSIS
        Extracts .SYNOPSIS or file header Process Name from PS1 content.
    .DESCRIPTION
        Args:
            $Content (string) — raw file content.
            $Fallback (string) — value to return if nothing found.

        Returns:
            string — synopsis text.
    .EXAMPLE
        Get-Synopsis -Content $raw -Fallback "MyScript"
    #>
    param([string]$Content, [string]$Fallback)

    # file header "Process Name:"
    if ($Content -match 'Process Name:\s*(.+)') { return $Matches[1].Trim() }
    # comment-based help .SYNOPSIS
    if ($Content -match '\.SYNOPSIS\s*\r?\n\s*(.+)') { return $Matches[1].Trim() }
    return $Fallback
}

function Get-Description {
    <#
    .SYNOPSIS
        Extracts .DESCRIPTION block or header Description section from PS1 content.
    .DESCRIPTION
        Args:
            $Content (string) — raw file content.

        Returns:
            string — description text, empty string if not found.
    .EXAMPLE
        Get-Description -Content $raw
    #>
    param([string]$Content)

    # file header multi-line description block
    if ($Content -match '#\s*Description:\s*\r?\n((?:#[^\r\n]*\r?\n)+)') {
        return ($Matches[1] -split '\r?\n' |
            ForEach-Object { $_ -replace '^\s*#\s*', '' } |
            Where-Object { $_ -ne '' }) -join "`n"
    }
    if ($Content -match '\.DESCRIPTION\s*\r?\n([\s\S]+?)(?=\r?\n\.[A-Z]|\r?\n#>)') { return $Matches[1].Trim() }
    return ''
}

function Get-Examples {
    <#
    .SYNOPSIS
        Extracts .EXAMPLE blocks or header Examples section from PS1 content.
    .DESCRIPTION
        Args:
            $Content (string) — raw file content.

        Returns:
            string — examples text, empty string if not found.
    .EXAMPLE
        Get-Examples -Content $raw
    #>
    param([string]$Content)

    if ($Content -match '#\s*Examples?:\s*\r?\n((?:#[^\r\n]*\r?\n)+)') {
        return ($Matches[1] -split '\r?\n' |
            ForEach-Object { $_ -replace '^\s*#\s*', '' } |
            Where-Object { $_ -ne '' }) -join "`n"
    }
    if ($Content -match '\.EXAMPLE\s*\r?\n([\s\S]+?)(?=\r?\n\.[A-Z]|\r?\n#>)') { return $Matches[1].Trim() }
    return ''
}

# --- collect files ---

$rootFiles = Get-ChildItem -Path $PROJECT_ROOT -Filter "*.ps1" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch '~' -and $SKIP_FILE_NAMES -notcontains $_.Name }

$subDirs = @("scripts", "mcp", "install", "check_engine", "src", "tests", "microsoft_sandbox_operations")
$subDirPaths = $subDirs | ForEach-Object { Join-Path $PROJECT_ROOT $_ } | Where-Object { Test-Path $_ }
$subFiles = Get-ChildItem -Path $subDirPaths -Filter "*.ps1" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\~' -and
                   $_.FullName -notmatch '\\venv\\' -and
                   $_.FullName -notmatch '\\site\\' -and
                   $SKIP_FILE_NAMES -notcontains $_.Name }

$allFiles = @($rootFiles) + @($subFiles)

# --- generate per-file pages ---

$projectRoot = $PROJECT_ROOT

foreach ($file in $allFiles) {
    try {
        $name    = $file.BaseName
        $content = Get-Content $file.FullName -Raw -Encoding UTF8

        $synopsis    = Get-Synopsis    -Content $content -Fallback $name
        $description = Get-Description -Content $content
        $examples    = Get-Examples    -Content $content

        $relPath = $file.FullName.Replace($projectRoot + "\", "").Replace("\", "/")

        $md  = "# $name`n`n> $synopsis`n"
        if ($description) { $md += "`n## Description`n`n$description`n" }
        if ($examples)    { $md += "`n## Examples`n`n``````powershell`n$examples`n```````n" }
        $md += "`n## Source`n`n``$relPath```n"

        $outFileName = "$name.md"
        $outFile = Join-Path $OUT_DIR $outFileName

        Get-ChildItem -Path $OUT_DIR -Filter $outFileName -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -cne $outFileName } |
            Remove-Item -Force

        $md | Set-Content -Path $outFile -Encoding UTF8
    } catch {
        Write-Warning "Failed to process $($file.Name): $_"
    }
}

# --- generate grouped index ---

$groups = $allFiles | Group-Object {
    $rel = $_.FullName.Replace($projectRoot + "\", "")
    $parts = $rel -split '\\'
    if ($parts.Count -eq 1) { "(root)" } else { $parts[0] }
} | Sort-Object Name

$index = "# PowerShell Scripts`n`nAll PowerShell scripts in the AI Assistant project.`n"
$navYaml = "  # Auto-generated navigation fragment`n"

foreach ($group in $groups) {
    $groupTitle = if ($group.Name -eq "(root)") { "Root" } else { $group.Name }
    $index += "`n## $groupTitle`n`n"
    $navYaml += "  - ${groupTitle}:`n"
    
    foreach ($file in ($group.Group | Sort-Object BaseName)) {
        $index += "- [$($file.BaseName)]($($file.BaseName).md)`n"
        $navYaml += "      - $($file.BaseName): dev/powershell/$($file.BaseName).md`n"
    }
}

$index | Set-Content -Path "$OUT_DIR/index.md" -Encoding UTF8
$navYaml | Set-Content -Path $NAV_FRAGMENT -Encoding UTF8

Write-Host "Done: $OUT_DIR ($($allFiles.Count) files)" -ForegroundColor Green
Write-Host "Nav fragment: $NAV_FRAGMENT" -ForegroundColor Cyan
