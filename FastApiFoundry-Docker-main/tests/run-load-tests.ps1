# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Запуск нагрузочных тестов (Locust Headless)
# =============================================================================
# Описание:
#   Автоматизирует запуск Locust в фоновом режиме без GUI.
#   Сохраняет статистику производительности в CSV файлы.
#
# File: tests/run-load-tests.ps1
# Project: Ai Assistant
# Author: Gemini Code Assist
# =============================================================================

$LocustFile = Join-Path $PSScriptRoot "integration\locustfile.py"
$ReportDir = Join-Path $PSScriptRoot "reports\load"
$CsvPrefix = Join-Path $ReportDir "locust_results"

if (!(Test-Path $ReportDir)) {
    New-Item -Path $ReportDir -ItemType Directory -Force | Out-Null
}

Write-Host "🚀 Запуск нагрузочного теста (Locust Headless)..." -ForegroundColor Cyan
Write-Host "📍 Файл: $LocustFile" -ForegroundColor Gray
Write-Host "📊 Отчеты: $ReportDir" -ForegroundColor Gray

# Параметры нагрузки
$Users = 50
$SpawnRate = 10
$RunTime = "2m" # Время выполнения: 2 минуты

# Команда запуска Locust в headless режиме
$Command = "locust -f `"$LocustFile`" --headless -u $Users -r $SpawnRate --run-time $RunTime --host http://localhost:9696 --csv `"$CsvPrefix`""

Write-Host "Выполнение: $Command" -ForegroundColor DarkGray
Invoke-Expression $Command

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Нагрузочный тест завершен. Результаты сохранены в $ReportDir" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка при выполнении нагрузочного теста." -ForegroundColor Red
}