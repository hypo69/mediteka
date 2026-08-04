# scripts/clear-reports.ps1
# -*- coding: utf-8 -*-

# =============================================================================
# Название процесса: Очистка артефактов тестирования
# =============================================================================
# Описание:
#   Удаление всех файлов и подпапок из директории tests/reports.
#   Подготовка окружения перед запуском нового цикла QA.
#
# File: scripts/clear-reports.ps1
# Project: Ai Assistant
# Author: Gemini Code Assist
# Copyright: © 2026 Ai Assistant
# =============================================================================

# Определение путей относительно расположения скрипта
$script:RootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$script:ReportsPath = Join-Path $script:RootPath "..\tests\reports"

Write-Host "--- Запуск процесса очистки отчетов ---" -ForegroundColor Cyan

# Проверка существования целевой директории
if (Test-Path $script:ReportsPath) {
    try {
        # Рекурсивное удаление содержимого без удаления самой корневой папки reports
        Get-ChildItem -Path $script:ReportsPath | Remove-Item -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Очистка директории $script:ReportsPath завершена успешно." -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Ошибка при очистке: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ℹ️ Директория отчетов не найдена, создание новой структуры..." -ForegroundColor Yellow
    New-Item -Path $script:ReportsPath -ItemType Directory -Force | Out-Null
}

Write-Host "--- Окружение готово к тестированию ---" -ForegroundColor Cyan