# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Восстановление RAG индекса
# =============================================================================
# Описание:
#   Распаковка ранее архивированного ZIP-индекса обратно в рабочую директорию
#   ~/.ai-assist/rag/.
#
# File: scripts/Restore-RagIndex.ps1
# Project: Ai Assistant
# Version: 1.0.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

<#
.SYNOPSIS
    Восстанавливает RAG индекс из архива.
.DESCRIPTION
    Берет ZIP файл из папки архивов и распаковывает его содержимое 
    в директорию ~/.aiassistant/rag/ под указанным или оригинальным именем.

.PARAMETER ZipPath
    Полный путь к ZIP архиву индекса.
.PARAMETER ProfileName
    Имя профиля, под которым нужно восстановить индекс. 
    Если не указано, берется имя из названия файла архива.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ZipPath,
    [string]$ProfileName
)

$RagDir = [System.IO.Path]::Combine($env:USERPROFILE, ".aiassistant", "rag")

if (-not (Test-Path $ZipPath)) {
    Write-Error "❌ Файл архива не найден: $ZipPath"
    exit 1
}

# Если имя профиля не указано, пытаемся извлечь его из имени файла (до первой метки времени)
if (-not $ProfileName) {
    $FileName = [System.IO.Path]::GetFileNameWithoutExtension($ZipPath)
    $ProfileName = $FileName.Split('_')[0]
}

$TargetDir = Join-Path $RagDir $ProfileName

if (Test-Path $TargetDir) {
    Write-Warning "⚠️ Директория профиля '$ProfileName' уже существует."
    $Confirm = Read-Host "Перезаписать существующий индекс? [y/N]"
    if ($Confirm -ne 'y') {
        Write-Host "⏭️ Восстановление отменено." -ForegroundColor Yellow
        exit 0
    }
    Remove-Item $TargetDir -Recurse -Force
}

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

Write-Host "📦 Восстановление индекса '$ProfileName' в $TargetDir..." -ForegroundColor Cyan

try {
    Expand-Archive -Path $ZipPath -DestinationPath $TargetDir -Force
    Write-Host "✅ Индекс успешно восстановлен." -ForegroundColor Green
} catch {
    Write-Error "❌ Ошибка при восстановлении: $($_.Exception.Message)"
    exit 1
}