# scripts/Invoke-Qa.ps1
# -*- coding: utf-8 -*-

# =============================================================================
# Название процесса: Запуск полного цикла QA (Linting, Types, Tests, Coverage)
# =============================================================================
# Описание:
#   Автоматизирует запуск статического анализа (ruff, mypy) и тестов (pytest)
#   с генерацией отчета о покрытии кода в формате HTML.
#
# File: scripts/Invoke-Qa.ps1
# Version: 1.6.0
# Project: Ai Assistant
# Author: Gemini Code Assist
# Copyright: © 2026 Ai Assistant
# =============================================================================

<#
.SYNOPSIS
    Запускает полный цикл контроля качества (QA) для проекта Ai Assistant.
.DESCRIPTION
    Этот скрипт выполняет следующие шаги:
    1. Активирует виртуальное окружение Python.
    2. Запускает линтер Ruff для проверки стиля кода.
    3. Запускает статический анализатор Mypy для проверки типов.
    4. Проверяет наличие обновлений для установленных пакетов (pip list --outdated).
    5. Проводит аудит безопасности пакетов (pip-audit).
    6. Ищет секреты и ключи в коде (detect-secrets).
    4. Запускает Pytest для выполнения всех тестов.
    5. Генерирует отчет о покрытии кода в формате HTML.
    6. Открывает сгенерированный HTML отчет в браузере.
.EXAMPLE
    .\Invoke-Qa.ps1
    Запускает полный цикл QA.
.EXAMPLE
    .\Invoke-Qa.ps1 -SkipCoverageReport
    Запускает QA, но не открывает отчет о покрытии.
.PARAMETER SkipCoverageReport
    Если указан, HTML отчет о покрытии не будет открыт автоматически.
#>
[CmdletBinding()]
param(
    [switch]$SkipCoverageReport
)

$script:RootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$script:VenvPath = Join-Path $script:RootPath "..\venv"
$script:SourcePath = Join-Path $script:RootPath "..\src"
$script:CoverageReportDir = Join-Path $script:RootPath "..\tests\reports\coverage"
$script:AuditJsonPath = Join-Path $script:RootPath "..\tests\reports\audit.json"
$script:SecretsPath = Join-Path $script:RootPath "..\tests\reports\secrets.json"
$script:PdfReportPath = Join-Path $script:RootPath "..\tests\reports\qa_management_report.pdf"
$script:CoverageReportPath = Join-Path $script:CoverageReportDir "index.html"

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = 'INFO',
        [string]$Color = 'White'
    )
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $Color
}

function Check-OutdatedDependencies {
    <#
    .SYNOPSIS
        Проверяет наличие новых версий установленных пакетов.
    #>
    Write-Log "Проверка обновлений пакетов (pip list --outdated)..." -Color Cyan
    $outdated = & python -m pip list --outdated --format=columns
    
    if ($outdated.Count -gt 2) {
        Write-Log "Найдены обновления для следующих пакетов:" -Level WARNING -Color Yellow
        $outdated | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkYellow }
        Write-Log "Рекомендуется обновить зависимости: pip install --upgrade <package>" -Color Gray
    } else {
        Write-Log "Все пакеты актуальны." -Color Green
    }
    return $outdated
}

function Check-Vulnerabilities {
    <#
    .SYNOPSIS
        Проверяет установленные пакеты на наличие известных уязвимостей через pip-audit.
    #>
    Write-Log "Проверка безопасности пакетов (pip-audit)..." -Color Cyan
    
    # Проверка наличия pip-audit в окружении
    & python -m pip_audit --version > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "pip-audit не установлен. Пропуск аудита безопасности." -Level WARNING -Color Yellow
        return
    }

    # Запуск аудита с генерацией JSON отчета и выводом в консоль
    & python -m pip_audit --desc on --format columns --output $script:AuditJsonPath --force
    $auditResult = $LASTEXITCODE
    
    # Также дублируем вывод в консоль для наглядности (без сохранения в файл)
    & python -m pip_audit --desc on --format columns
    
    if ($auditResult -eq 0) {
        Write-Log "Уязвимостей в пакетах не обнаружено." -Color Green
    } else {
        Write-Log "ОБНАРУЖЕНЫ УЯЗВИМОСТИ! Рекомендуется обновить проблемные пакеты." -Level ERROR -Color Red
        # В режиме CI не завершаем скрипт, чтобы GitHub Action мог создать Issue и продолжить другие проверки.
    }
    return $auditResult
}

function Load-EnvFile {
    param(
        [string]$EnvPath = (Join-Path $script:RootPath "..\.env")
    )

    if (-not (Test-Path $EnvPath)) {
        Write-Log "Файл .env не найден по пути: $EnvPath. Пропуск загрузки переменных окружения." -Level WARNING -Color Yellow
        return
    }

    Write-Log "Загрузка переменных окружения из $EnvPath..." -Color Cyan
    $envContent = Get-Content $EnvPath -Raw -Encoding UTF8

    $lines = $envContent -split "`n"
    $loadedCount = 0

    foreach ($line in $lines) {
        $line = $line.Trim()
        if ([string]::IsNullOrEmpty($line) -or $line.StartsWith('#')) {
            continue # Пропускаем пустые строки и комментарии
        }

        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            $key = $matches[1]
            $value = $matches[2]

            # Удаляем кавычки, если они есть
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            } elseif ($value.StartsWith("'") -and $value.EndsWith("'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }

            # Устанавливаем переменную окружения
            [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
            $loadedCount++

            # Маскируем чувствительные данные для лога
            $displayValue = $value
            if ($key -match 'PASSWORD|SECRET|KEY|TOKEN|PAT') {
                $displayValue = "***"
            }
            Write-Log "  ✓ $key = $displayValue" -Color Gray
        }
    }
    Write-Log "Загружено переменных окружения: $loadedCount" -Color Green
}

function Send-TelegramAlert {
    param([string]$Message)
    
    $envFile = Join-Path $script:RootPath "..\.env"
    if (-not (Test-Path $envFile)) { return }
    
    # Получение настроек из окружения или .env
    $token = [System.Environment]::GetEnvironmentVariable('TELEGRAM_BOT_TOKEN')
    $chatId = [System.Environment]::GetEnvironmentVariable('TELEGRAM_CHAT_ID')
    
    if (-not $token -or -not $chatId) {
        $content = Get-Content $envFile -Raw
        if ($content -match '(?m)^TELEGRAM_BOT_TOKEN=(.+)$') { $token = $matches[1].Trim() }
        if ($content -match '(?m)^TELEGRAM_CHAT_ID=(.+)$') { $chatId = $matches[1].Trim() }
    }
    
    if ($token -and $chatId -and $token -notmatch "your_bot_token_here" -and $chatId -notmatch "your_chat_id_here") {
        $url = "https://api.telegram.org/bot$token/sendMessage"
        $body = @{ chat_id = $chatId; text = $Message } | ConvertTo-Json
        try {
            Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5 | Out-Null
        } catch {
            Write-Log "Failed to send Telegram alert: $($_.Exception.Message)" -Level WARNING -Color Yellow
        }
    }
}

function Check-Secrets {
    <#
    .SYNOPSIS
        Поиск жестко закодированных секретов (API ключи, пароли) в исходном коде.
    #>
    Write-Log "Поиск секретов в коде (detect-secrets)..." -Color Cyan
    
    # Сканирование директории src
    & detect-secrets scan $script:SourcePath --output-hook "detect_secrets.plugins.common.filters.opt_out" > $script:SecretsPath
    
    if (-not (Test-Path $script:SecretsPath)) { return 0 }
    
    $secretsJson = Get-Content $script:SecretsPath | ConvertFrom-Json
    $secretsFound = $secretsJson.results.PSObject.Properties.Count
    
    if ($secretsFound -eq 0) {
        Write-Log "Секретов в коде не обнаружено." -Color Green
        return 0
    } else {
        Write-Log "⚠️ ВНИМАНИЕ: Найдено $secretsFound потенциальных секретов! Проверьте $script:SecretsPath" -Level ERROR -Color Red
        
        return $secretsFound
    }
}

function Verify-Dependencies {
    <#
    .SYNOPSIS
        Проверяет наличие установленных пакетов из requirements-qa.txt.
        В интерактивном режиме предлагает автоматическую установку.
    #>
    # Проверка на окружение CI (GitHub Actions), где ввод невозможен
    $isCI = [Environment]::GetEnvironmentVariable("CI") -eq "true"

    $reqFile = Join-Path $script:RootPath "..\requirements-qa.txt"
    if (-not (Test-Path $reqFile)) {
        Write-Log "Файл $reqFile не найден. Пропуск проверки зависимостей." -Level WARNING -Color Yellow
        return
    }

    Write-Log "Проверка установленных QA зависимостей..." -Color Cyan
    
    # Обоснование использования python для проверки:
    # Гарантирует, что пакеты видны именно в текущем виртуальном окружении.
    $verifyCmd = "python -c ""import pkg_resources; reqs = open('$($reqFile.Replace('\','/'))').readlines(); pkg_resources.require(reqs)"""
    
    Invoke-Expression $verifyCmd
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Критические QA зависимости отсутствуют." -Level WARNING -Color Yellow
        
        if ($isCI) {
            Write-Log "Режим CI: Автоматическая установка зависимостей..." -Color Cyan
            & python -m pip install -r $reqFile
        } else {
        $choice = Read-Host "Установить недостающие пакеты из $reqFile сейчас? (y/N)"
        if ($choice -eq 'y' -or $choice -eq 'Y') {
            Write-Log "Запуск установки зависимостей..." -Color Cyan
            & python -m pip install -r $reqFile
            if ($LASTEXITCODE -ne 0) {
                Write-Log "Ошибка при установке зависимостей." -Level ERROR -Color Red
                exit 1
            }
            Write-Log "Зависимости успешно установлены." -Color Green
        } else {
            Write-Log "QA цикл прерван. Выполните вручную: pip install -r requirements-qa.txt" -Level ERROR -Color Red
            exit 1
        }
        }
    }
    Write-Log "Все QA зависимости установлены." -Color Green
}

function Activate-Venv {
    Write-Log "Активация виртуального окружения..." -Color Cyan
    if (Test-Path (Join-Path $script:VenvPath "Scripts\Activate.ps1")) {
        . (Join-Path $script:VenvPath "Scripts\Activate.ps1")
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Ошибка активации виртуального окружения." -Level ERROR -Color Red
            exit 1
        }
        Write-Log "Виртуальное окружение активировано." -Color Green
    } else {
        Write-Log "Виртуальное окружение не найдено по пути: $script:VenvPath. Убедитесь, что оно создано." -Level ERROR -Color Red
        exit 1
    }
    
    Verify-Dependencies
}

function Run-Command {
    param(
        [string]$Command,
        [string]$Description,
        [string]$SuccessMessage,
        [string]$ErrorMessage
    )
    Write-Log "Запуск: $Description" -Color Cyan
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Log $ErrorMessage -Level ERROR -Color Red
        exit 1
    }
    Write-Log $SuccessMessage -Color Green
}

# --- Main Script Logic ---
try {
    Write-Log "Начало полного цикла QA для Ai Assistant..." -Color Yellow

    # Очистка предыдущих отчетов
    Write-Log "Подготовка: Очистка старых отчетов..." -Color Cyan
    & powershell -ExecutionPolicy Bypass -File (Join-Path $script:RootPath "clear-reports.ps1")

    # Создание директории для отчетов, если она отсутствует
    if (!(Test-Path $script:CoverageReportDir)) {
        New-Item -Path $script:CoverageReportDir -ItemType Directory -Force | Out-Null
    }

    # Установка хуков перед запуском QA-цикла
    $SetupHooksScript = Join-Path $script:RootPath "Setup-GitHooks.ps1"
    if (Test-Path $SetupHooksScript) {
        & powershell -ExecutionPolicy Bypass -File $SetupHooksScript
    }

    Activate-Venv

    # Загрузка переменных окружения из .env
    Load-EnvFile
    
    # Новый шаг: Проверка актуальности пакетов
    Check-OutdatedDependencies

    # Новый шаг: Проверка безопасности
    $vulnerabilityStatus = Check-Vulnerabilities
    $securityStatus = if ($vulnerabilityStatus -eq 0) { "SECURE" } else { "VULNERABILITIES FOUND" }

    # Новый шаг: Поиск секретов
    $secretsStatusVal = Check-Secrets
    $secretsStatusStr = if ($secretsStatusVal -eq 0) { "CLEAN" } else { "SECRETS DETECTED" }

    Run-Command "ruff check $script:SourcePath" "Ruff (линтер)" "Ruff завершен успешно." "Ruff обнаружил ошибки."
    Run-Command "mypy $script:SourcePath" "Mypy (проверка типов)" "Mypy завершен успешно." "Mypy обнаружил ошибки типов."
    
    # Запуск Pester тестов для PowerShell скриптов
    $PesterTestsPath = Join-Path $script:RootPath "..\tests"
    Run-Command "Invoke-Pester -Path $PesterTestsPath -Output Detailed" "Pester (PowerShell тесты)" "Pester тесты пройдены." "Pester тесты обнаружили ошибки."

    $script:JUnitReport = Join-Path $script:RootPath "..\tests\reports\junit.xml"
    Run-Command "pytest --cov=$script:SourcePath --cov-report=html:$script:CoverageReportDir --junitxml=$script:JUnitReport" "Pytest (тесты и покрытие)" "Все тесты пройдены успешно, отчет о покрытии сгенерирован." "Тесты завершились с ошибками."

    # Генерация PDF отчета
    Write-Log "Генерация PDF отчета для руководства..." -Color Cyan
    $GeneratePdfCmd = "python -c ""import sys; from fpdf import FPDF; pdf=FPDF(); pdf.add_page(); pdf.set_font('Arial', 'B', 16); pdf.cell(40, 10, 'Ai Assistant QA Management Report'); pdf.ln(20); pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 10, 'General Status: PASSED\nSecurity Audit: $($securityStatus)\nSecrets Scan: $($secretsStatusStr)\nStatic Analysis: Ruff + Mypy\nTest Suite: Pytest + JUnit\nReports: HTML Coverage + Security Logs'); pdf.output('$($script:PdfReportPath.Replace('\','\\'))')"""
    
    try {
        Invoke-Expression $GeneratePdfCmd
        Write-Log "PDF отчет создан: $script:PdfReportPath" -Color Green
    } catch {
        Write-Log "Не удалось создать PDF отчет. Убедитесь, что библиотека fpdf2 установлена (pip install fpdf2)." -Level WARNING -Color Yellow
    }

    # --- Интеграционные тесты API ---
    Write-Host "`n"
    Write-Log "Запуск интеграционных тестов API (REST Endpoints)..." -Color Yellow
    $env:API_KEY = [System.Environment]::GetEnvironmentVariable('API_KEY')
    $ApiTestScript = Join-Path $script:RootPath "..\tests\Test-ApiEndpoints.ps1"
    if (Test-Path $ApiTestScript) {
        & powershell -ExecutionPolicy Bypass -File $ApiTestScript
    } else {
        Write-Log "Скрипт $ApiTestScript не найден. Пропуск." -Level WARNING -Color Yellow
    }

    # --- Нагрузочное тестирование и визуализация ---
    Write-Log "Переход к блоку нагрузочного тестирования..." -Color Yellow
    
    $LoadTestScript = Join-Path $script:RootPath "..\tests\run-load-tests.ps1"
    if (Test-Path $LoadTestScript) {
        Write-Log "Проверка доступности сервера (порт 9696)..." -Color Cyan
        try {
            $tcp = [System.Net.Sockets.TcpClient]::new()
            $tcp.Connect('127.0.0.1', 9696)
            $tcp.Close()
            & powershell -ExecutionPolicy Bypass -File $LoadTestScript
        } catch {
            Write-Log "Сервер на порту 9696 не отвечает. Нагрузочные тесты пропущены." -Level WARNING -Color Yellow
        }
    }

    $VizScript = Join-Path $script:RootPath "..\tests\visualize_performance.py"
    if (Test-Path $VizScript) {
        Run-Command "python $VizScript" "Визуализация производительности" "Графики производительности успешно сгенерированы." "Ошибка при генерации графиков."
    }

    if (-not $SkipCoverageReport) {
        if (Test-Path $script:CoverageReportPath) {
            Write-Log "Открытие HTML отчета о покрытии: $script:CoverageReportPath" -Color Green
            Start-Process $script:CoverageReportPath
        } else {
            Write-Log "HTML отчет о покрытии не найден по пути: $script:CoverageReportPath" -Level WARNING -Color Yellow
        }
    }
    Write-Log "Полный цикл QA завершен успешно!" -Color Green
} catch {
    Write-Log "Критическая ошибка в скрипте QA: $($_.Exception.Message)" -Level ERROR -Color Red
    exit 1
}
