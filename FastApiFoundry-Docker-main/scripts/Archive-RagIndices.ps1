# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Архивация RAG индексов
# =============================================================================
# Описание:
#   Упаковка директории индекса в ZIP-архив в папку archive/rag_indices/.
#   Используется перед окончательным удалением старых индексов.
#
# File: scripts/Archive-RagIndices.ps1
# Project: Ai Assistant
# Version: 1.0.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

<#
.SYNOPSIS
    Архивирует указанный индекс RAG в ZIP файл.
.DESCRIPTION
    Создает сжатый архив содержимого папки индекса в директории archive/ проекта.
    Позволяет сохранить данные перед их автоматической очисткой.

.PARAMETER IndexPath
    Полный путь к папке индекса RAG.
.PARAMETER ArchiveDir
    Относительный путь к папке для хранения архивов.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$IndexPath,
    [string]$ArchiveDir = "archive\rag_indices"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FullArchiveDir = Join-Path $ProjectRoot $ArchiveDir

if (-not (Test-Path $FullArchiveDir)) {
    New-Item -ItemType Directory -Path $FullArchiveDir -Force | Out-Null
}

if (-not (Test-Path $IndexPath)) {
    Write-Warning "Путь к индексу не найден: $IndexPath"
    exit 1
}

$IndexName = Split-Path $IndexPath -Leaf
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ZipName = "$($IndexName)_$($Timestamp).zip"
$ZipPath = Join-Path $FullArchiveDir $ZipName

Write-Host "📦 Архивация индекса $IndexName в $ZipPath..." -ForegroundColor Cyan

try {
    Compress-Archive -Path "$IndexPath\*" -DestinationPath $ZipPath -Force
    Write-Host "✅ Архив создан успешно." -ForegroundColor Green
    exit 0
} catch {
    Write-Error "❌ Сбой при создании архива: $($_.Exception.Message)"
    exit 1
}