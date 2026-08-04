# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Очистка архивных файлов (~)
# =============================================================================
# Описание:
#   Рекурсивный поиск и удаление временных/архивных файлов, созданных при
#   переносе документации или рефакторинге (файлы с суффиксом ~).
#
# File: scripts/Clear-ArchivedFiles.ps1
# Project: Ai Assistant
# Version: 1.3.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

<#
.SYNOPSIS
    Удаляет все файлы с суффиксом ~ во всем проекте.
.DESCRIPTION
    Скрипт сканирует корневую директорию проекта и все вложенные папки,
    находит файлы, чьи имена заканчиваются на тильду (~), и принудительно удаляет их.
    Используется для очистки репозитория от "мусора" после массовых перемещений файлов.
    
.PARAMETER Force
    Принудительное удаление без подтверждения.
.PARAMETER WhatIf
    Показать список файлов, которые были бы удалены, не производя фактических действий.
#>

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$WhatIf
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Ротация лога перед началом работы (интеграция)
$RotatorScript = Join-Path $PSScriptRoot "Rotate-CleanupLog.ps1"
if (Test-Path $RotatorScript) {
    & $RotatorScript
}

$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "cleanup.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-LogEntry {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Timestamp] $Message" | Add-Content -Path $LogFile -Encoding UTF8
}

Write-Host "🔍 Запуск очистки архивных файлов в $ProjectRoot..." -ForegroundColor Cyan
if (-not $WhatIf) { Write-LogEntry "--- Запуск очистки ---" }

$files = Get-ChildItem -Path $ProjectRoot -Filter "*~" -Recurse -File -ErrorAction SilentlyContinue

if ($null -eq $files -or $files.Count -eq 0) {
    Write-Host "✅ Архивных файлов не обнаружено." -ForegroundColor Green
    if (-not $WhatIf) { Write-LogEntry "Архивных файлов не обнаружено." }
    exit 0
}

Write-Host "Найдено файлов: $($files.Count)" -ForegroundColor Yellow
$FilesDeleted = 0
foreach ($file in $files) {
    if ($WhatIf) {
        Write-Host "  [WHATIF] Будет удален: $($file.FullName)" -ForegroundColor Gray
    } else {
        Remove-Item $file.FullName -Force
        Write-Host "  🗑️ Удален: $($file.FullName)" -ForegroundColor Yellow
        Write-LogEntry "Удален файл: $($file.FullName)"
        $FilesDeleted++
    }
}

Write-Host "`n📁 Поиск и очистка пустых папок..." -ForegroundColor Cyan
# Сортируем папки по глубине (длине пути), чтобы удалять вложенные первыми
$dirs = Get-ChildItem -Path $ProjectRoot -Recurse -Directory | Sort-Object { $_.FullName.Length } -Descending

$DirsDeleted = 0
foreach ($dir in $dirs) {
    # Проверяем, пуста ли папка (включая скрытые элементы)
    if (-not (Get-ChildItem -Path $dir.FullName -Force | Select-Object -First 1)) {
        if ($WhatIf) {
            Write-Host "  [WHATIF] Будет удалена пустая папка: $($dir.FullName)" -ForegroundColor Gray
        } else {
            Remove-Item $dir.FullName -Force
            Write-Host "  🗑️ Удалена пустая папка: $($dir.FullName)" -ForegroundColor Yellow
            Write-LogEntry "Удалена пустая папка: $($dir.FullName)"
            $DirsDeleted++
        }
    }
}

# Отправка уведомления в Telegram (при наличии настроек в окружении)
if (-not $WhatIf -and $env:TELEGRAM_ADMIN_TOKEN -and $env:TELEGRAM_ADMIN_IDS) {
    $Message = "🧹 *AI Assistant Cleanup Report*`n" +
               "📄 Files deleted: $FilesDeleted`n" +
               "📁 Folders removed: $DirsDeleted`n" +
               "🕒 Timestamp: $(Get-Date -Format 'HH:mm:ss')"
    
    foreach ($ChatId in ($env:TELEGRAM_ADMIN_IDS -split ',')) {
        try {
            $Uri = "https://api.telegram.org/bot$($env:TELEGRAM_ADMIN_TOKEN)/sendMessage"
            $Body = @{ chat_id = $ChatId.Trim(); text = $Message; parse_mode = "Markdown" }
            Invoke-RestMethod -Uri $Uri -Method Post -Body $Body | Out-Null
        } catch { }
    }
}

Write-Host "`n✨ Очистка завершена!" -ForegroundColor Green
exit 0