# -*- coding: utf-8 -*-
# =============================================================================
# Название: Скрипт сборки релиза (Build-Release)
# =============================================================================
# Описание:
#   1. Запускает полную проверку QA (Run-Qa.ps1).
#   2. Очищает временные файлы и артефакты.
#   3. Создает ZIP-архив проекта для распространения.
# =============================================================================
#
# <#
# .SYNOPSIS
#     Собирает релизную версию проекта, включая QA-проверки, очистку и упаковку в ZIP-архив.
# .DESCRIPTION
#     Этот скрипт автоматизирует процесс подготовки релиза:
#     1. Вызывает `Run-Qa.ps1` для выполнения всех проверок качества (линтер, типы, тесты, безопасность).
#        Если QA-проверки не пройдены, сборка прерывается.
#     2. Создает временную директорию для стейджинга, куда копирует все необходимые файлы проекта,
#        исключая временные файлы, логи, виртуальные окружения и другие артефакты разработки.
#        Использует `robocopy` для эффективного зеркалирования.
#     3. Упаковывает содержимое стейджинг-директории в ZIP-архив. Имя архива включает текущую версию проекта,
#        которая считывается из файла `VERSION`.
#     4. Удаляет временные файлы и директории после завершения сборки.
# .EXAMPLE
#     .\Build-Release.ps1
#     Запускает процесс сборки релиза.
# .OUTPUTS
#     Выводит сообщения о ходе выполнения, статусе QA-проверок, очистке и создании архива.
#     В случае успеха создает ZIP-архив в директории `release/`.
# .NOTES
#     Требует наличия `Run-Qa.ps1` в той же директории.
#     Для корректной работы `robocopy` должен быть доступен в системе.
# =============================================================================

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 0. Проверка обязательных файлов
Write-Host "🔍 Проверка обязательных файлов..." -ForegroundColor Cyan
$RequiredFiles = @('VERSION', 'LICENSE', 'README.md', 'config.json.example', '.env.example')
$MissingFiles = @()

foreach ($file in $RequiredFiles) {
    $filePath = Join-Path $ProjectRoot $file
    if (-not (Test-Path $filePath)) {
        $MissingFiles += $file
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "❌ Ошибка: В корне проекта отсутствуют обязательные файлы:" -ForegroundColor Red
    foreach ($f in $MissingFiles) { Write-Host "  - $f" -ForegroundColor Red }
    exit 1
}

$Version = Get-Content (Join-Path $ProjectRoot 'VERSION') -Raw
$Version = $Version.Trim()

Write-Host "🏗️  Начало сборки релиза версии $Version" -ForegroundColor Cyan

# 1. Запуск QA
Write-Host "`n[1/3] Запуск контроля качества (QA)..." -ForegroundColor Yellow
$QaScript = Join-Path $PSScriptRoot 'Invoke-Qa.ps1'
if (Test-Path $QaScript) {
    & $QaScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Сборка прервана: Тесты или проверки безопасности не пройдены." -ForegroundColor Red
        exit 1
    }
}

# 2. Подготовка директории сборки
Write-Host "`n[2/3] Очистка и подготовка артефактов..." -ForegroundColor Yellow

# Удаление архивных файлов (~) в исходном коде перед копированием
$CleanerScript = Join-Path $PSScriptRoot 'Clear-ArchivedFiles.ps1'
if (Test-Path $CleanerScript) {
    & $CleanerScript -Force
}

$ReleaseDir = Join-Path $ProjectRoot "release"
$StagingDir = Join-Path $ReleaseDir "temp_staging"

if (Test-Path $StagingDir) { Remove-Item $StagingDir -Recurse -Force }
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

# Список исключений для Robocopy
$ExcludeDirs = @(
    'venv', '.git', 'logs', '__pycache__', 'release', '.pytest_cache', '.mypy_cache', 
    'site', 'archive', 'rag_index', '.gemini', '.claude', 'tests/reports', '.vs', '.vscode', '.idea'
)
$ExcludeFiles = @('.env', '*.pyc', '*.tmp', 'autostart_stdout.tmp', 'autostart_stderr.tmp', '.gitignore', '.secrets.baseline', 'MODE', '*.log')

robocopy $ProjectRoot $StagingDir /MIR /XD $ExcludeDirs /XF $ExcludeFiles /R:1 /W:1 /NFL /NDL /NJH /NJS

# 3. Создание архива
Write-Host "`n[3/3] Упаковка в ZIP..." -ForegroundColor Yellow
$ZipName = "ai_assistant_$($Version).zip"
$ZipPath = Join-Path $ReleaseDir $ZipName

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }

Compress-Archive -Path "$StagingDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

# Финализация
Remove-Item $StagingDir -Recurse -Force
Write-Host "`n✅ Сборка успешно завершена!" -ForegroundColor Green
Write-Host "📦 Архив: $ZipPath" -ForegroundColor Cyan