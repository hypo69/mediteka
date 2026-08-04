# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Создание ярлыков на рабочем столе
# =============================================================================
# Description:
#   Создаёт два ярлыка Windows на рабочем столе для запуска AI Assistant:
#     1. "AI Assistant"          — консольное окно через start.ps1
#     2. "AI Assistant (Silent)" — скрытое окно через autostart.ps1
#   Источник иконки: assets\icons\icon128.png (конвертируется автоматически).
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Shortcuts.ps1
#
# File: scripts\Install\Install-Shortcuts.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Обновлён заголовок и проект
#   - Комментарии переведены на русский
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# License: MIT
# =============================================================================

param (
    [switch]$Silent
)

$ErrorActionPreference = 'Stop'

# --- paths ---

# Project root is two levels above scripts\Install.
$PROJECT_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$DESKTOP_PATH = [Environment]::GetFolderPath('Desktop')
$ICON_PATH    = Join-Path $PROJECT_ROOT 'icon.ico'
$MAKE_ICO     = Join-Path $PROJECT_ROOT 'scripts\Install\Make-Ico.ps1'
$START_PS1    = Join-Path $PROJECT_ROOT 'start.ps1'
$AUTOSTART_PS1 = Join-Path $PROJECT_ROOT 'autostart.ps1'

# --- functions ---

function Ensure-Icon {
    <#
    .SYNOPSIS
        Создаёт icon.ico из PNG-файлов assets\icons\, если файл ещё не существует.
    .DESCRIPTION
        Returns:
            void
    .EXAMPLE
        Ensure-Icon
        # icon.ico создан в корне проекта
    #>
    if (Test-Path $ICON_PATH) {
        Write-Host "  ✅ icon.ico found: $ICON_PATH"
        return
    }

    if (-not (Test-Path $MAKE_ICO)) {
        Write-Host '  ⚠️  make-ico.ps1 not found — shortcuts will use default PowerShell icon' -ForegroundColor Yellow
        return
    }

    Write-Host '  🔧 Building icon.ico from assets\icons\...'
    & powershell.exe -ExecutionPolicy Bypass -File $MAKE_ICO -ProjectRoot $PROJECT_ROOT
    if (Test-Path $ICON_PATH) {
        Write-Host "  ✅ icon.ico created: $ICON_PATH"
    } else {
        Write-Host '  ⚠️  icon.ico was not created — shortcuts will use default icon' -ForegroundColor Yellow
    }
}

function New-AppShortcut {
    <#
    .SYNOPSIS
        Создаёт .lnk-ярлык на рабочем столе.
    .DESCRIPTION
        Args:
            $Name (string) — имя ярлыка без .lnk.
            $Arguments (string) — аргументы для powershell.exe.
            $WindowStyle (int) — 1 = обычное, 7 = скрытое.
            $Description (string) — подсказка при наведении.

        Returns:
            void
    .EXAMPLE
        New-AppShortcut -Name 'AI Assistant' -Arguments "-ExecutionPolicy Bypass -File start.ps1" -WindowStyle 1 -Description 'AI Assistant'
        # Ярлык AI Assistant.lnk создан на рабочем столе
    #>
    param (
        [string]$Name,
        [string]$Arguments,
        [int]$WindowStyle,
        [string]$Description
    )

    $lnkPath  = Join-Path $DESKTOP_PATH "$Name.lnk"
    $wsh      = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($lnkPath)

    $shortcut.TargetPath       = 'powershell.exe'
    $shortcut.Arguments        = $Arguments
    $shortcut.WorkingDirectory = $PROJECT_ROOT
    $shortcut.WindowStyle      = $WindowStyle
    $shortcut.Description      = $Description

    if (Test-Path $ICON_PATH) {
        $shortcut.IconLocation = $ICON_PATH
    }

    $shortcut.Save()
    Write-Host "  ✅ $lnkPath" -ForegroundColor Gray
}

# --- main ---

Write-Host '🖼️  Preparing icon...'
Ensure-Icon

Write-Host '🔗 Creating desktop shortcuts...'

New-AppShortcut `
    -Name        'AI Assistant' `
    -Arguments   "-ExecutionPolicy Bypass -File `"$START_PS1`"" `
    -WindowStyle 1 `
    -Description 'FastAPI Foundry — AI Assistant (console mode)'

New-AppShortcut `
    -Name        'AI Assistant (Silent)' `
    -Arguments   "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$AUTOSTART_PS1`"" `
    -WindowStyle 7 `
    -Description 'FastAPI Foundry — AI Assistant (silent mode)'

# Docs shortcut: opens browser directly on the docs port (no server start needed)
$DOCS_PORT = 9697
try {
    $cfg = Get-Content (Join-Path $PROJECT_ROOT 'config.json') -Raw | ConvertFrom-Json
    if ($cfg.docs_server.port) { $DOCS_PORT = [int]$cfg.docs_server.port }
} catch { }

$docsLnk  = Join-Path $DESKTOP_PATH 'AI Assistant Docs.lnk'
$wsh      = New-Object -ComObject WScript.Shell
$docsShortcut = $wsh.CreateShortcut($docsLnk)
$docsShortcut.TargetPath       = "http://localhost:$DOCS_PORT"
$docsShortcut.Description      = "FastAPI Foundry — Documentation (http://localhost:$DOCS_PORT)"
if (Test-Path $ICON_PATH) { $docsShortcut.IconLocation = $ICON_PATH }
$docsShortcut.Save()
Write-Host "  ✅ $docsLnk" -ForegroundColor Gray

Write-Host '✅ Done.' -ForegroundColor Green
