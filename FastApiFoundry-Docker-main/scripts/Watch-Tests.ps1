# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Test Watcher — запуск тестов при изменении кода
# =============================================================================
# Description:
#   Следит за изменениями в src/ и tests/.
#   При изменении файла *.py автоматически запускает связанные тесты.
#   Результат выводится в консоль с цветовой индикацией.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1 -Path src/api/endpoints
#   powershell -ExecutionPolicy Bypass -File .\scripts\watch_tests.ps1 -All
#
# File: scripts/watch_tests.ps1
# Project: AI Assistant
# Version: 0.7.1
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# Licence: MIT
# =============================================================================

param (
    [string]$WatchPath = 'src',
    [switch]$All,
    [int]$DebounceMs = 1500
)

$ErrorActionPreference = 'Continue'
$Root = $PSScriptRoot | Split-Path -Parent
$Python = "$Root\venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host '❌ venv not found. Run install.ps1 first.' -ForegroundColor Red
    exit 1
}

function Get-RelatedTestFile {
    <#
    .SYNOPSIS
        Find test file corresponding to a changed source file.
    .PARAMETER ChangedFile
        Absolute path to the changed .py file.
    .OUTPUTS
        string — Relative path to test file, or 'tests/' if not found.
    #>
    param ([string]$ChangedFile)

    $rel = [System.IO.Path]::GetRelativePath($Root, $ChangedFile)
    # src/api/endpoints/chat_endpoints.py -> tests/unit/test_chat_endpoints.py
    $name = [System.IO.Path]::GetFileNameWithoutExtension($ChangedFile)
    $candidates = @(
        "tests\unit\test_$name.py",
        "tests\integration\test_$name.py",
        "tests\agents\test_$name.py"
    )
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $Root $c)) {
            return $c
        }
    }
    return 'tests\'
}

function Invoke-Tests {
    <#
    .SYNOPSIS
        Run pytest for a given path and print colored result.
    .PARAMETER TestPath
        Relative path to test file or directory.
    .PARAMETER ChangedFile
        Source file that triggered the run (for display).
    #>
    param ([string]$TestPath, [string]$ChangedFile)

    $display = [System.IO.Path]::GetRelativePath($Root, $ChangedFile)
    Write-Host "`n$('─' * 60)" -ForegroundColor DarkGray
    Write-Host "📝 Changed : $display" -ForegroundColor Cyan
    Write-Host "🧪 Running : $TestPath" -ForegroundColor Cyan
    Write-Host "$('─' * 60)" -ForegroundColor DarkGray

    $result = & $Python -m pytest $TestPath -v --tb=short --no-header 2>&1
    $exit = $LASTEXITCODE

    $result | ForEach-Object {
        if ($_ -match 'PASSED') {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -match 'FAILED|ERROR') {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -match 'WARNING') {
            Write-Host $_ -ForegroundColor Yellow
        } else {
            Write-Host $_
        }
    }

    if ($exit -eq 0) {
        Write-Host "`n✅ All tests passed" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Tests failed (exit $exit)" -ForegroundColor Red
    }
}

# --- main ---

$watchDir = Join-Path $Root $WatchPath
Write-Host '👁️  Test Watcher started' -ForegroundColor Cyan
Write-Host "   Watching : $watchDir" -ForegroundColor Gray
Write-Host "   Debounce : ${DebounceMs}ms" -ForegroundColor Gray
Write-Host '   Press Ctrl+C to stop' -ForegroundColor Gray
Write-Host ''

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $watchDir
$watcher.Filter = '*.py'
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$lastFile = ''
$lastTime = [datetime]::MinValue

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $now = [datetime]::Now

    # Debounce: ignore rapid successive events on the same file
    if ($path -eq $script:lastFile -and ($now - $script:lastTime).TotalMilliseconds -lt $DebounceMs) {
        return
    }
    $script:lastFile = $path
    $script:lastTime = $now

    if ($All) {
        Invoke-Tests -TestPath 'tests\' -ChangedFile $path
    } else {
        $testPath = Get-RelatedTestFile -ChangedFile $path
        Invoke-Tests -TestPath $testPath -ChangedFile $path
    }
}

Register-ObjectEvent $watcher Changed -Action $action | Out-Null
Register-ObjectEvent $watcher Created -Action $action | Out-Null

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host '👋 Watcher stopped' -ForegroundColor Gray
}
