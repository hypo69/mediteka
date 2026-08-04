# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Автозапуск FastAPI Foundry при старте Windows
# =============================================================================
# Описание:
#   Запуск основного скрипта start.ps1 в фоновом режиме.
#   Перенаправление всего вывода в файлы логов.
#   Предназначен для использования в Планировщике задач Windows.
#
# Примеры:
#   # Прямой запуск:
#   .\autostart.ps1
#
#   # Регистрация в планировщике через инсталлер:
#   .\scripts\Install\Install-Autostart.ps1
#
# File: autostart.ps1
# Project: AI Assistant
# Version: 0.3.0
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# Licence: MIT
# =============================================================================

$ErrorActionPreference = 'Continue'
$Root = $PSScriptRoot

# Конфигурация путей
$LogDir  = Join-Path $Root 'logs'
$LogFile = Join-Path $LogDir 'autostart.log'

<#
.SYNOPSIS
    Логирование событий процесса автозапуска.

.PARAMETER Message
    Текст сообщения для записи.

.PARAMETER Level
    Уровень важности (INFO, WARNING, ERROR). По умолчанию 'INFO'.

.OUTPUTS
    Результат записывается в файл $LogFile.

.EXAMPLE
    Write-Log "Process started" "INFO"
#>
function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')

    # Проверка наличия директории логов
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }

    $Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $LogLine   = "$Timestamp | $($Level.PadRight(8)) | autostart | $Message"
    
    # Запись в файл с кодировкой UTF8
    Add-Content -Path $LogFile -Value $LogLine -Encoding UTF8
}

Write-Log "=== FastAPI Foundry autostart ==="
Write-Log "Root: $Root"
Write-Log "Log:  $LogFile"

# Проверка и установка PowerShell 7
$pwsh = 'C:\Program Files\PowerShell\7\pwsh.exe'
if (-not (Test-Path $pwsh)) {
    $msi = Join-Path $Root 'bin\PowerShell-7.4.6-win-x64.msi'
    if (Test-Path $msi) {
        Write-Log "Installation: PowerShell 7 from $msi"
        try {
            Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /quiet /norestart" -Wait -ErrorAction Stop
            Write-Log "Status: PowerShell 7 installed"
        } catch {
            Write-Log "Exception: Failed to install PowerShell 7: $_" 'ERROR'
        }
    } else {
        Write-Log "Warning: PowerShell 7 MSI not found: $msi" 'WARNING'
    }
} else {
    Write-Log "Status: PowerShell 7 already installed"
}

# Активация виртуального окружения
$ActivateScript = Join-Path $Root 'venv\Scripts\Activate.ps1'
if (Test-Path $ActivateScript) {
    try {
        . $ActivateScript
        Write-Log "Status: venv activated: $ActivateScript"
    } catch {
        Write-Log "Exception: Activation failed: $_" 'ERROR'
    }
} else {
    Write-Log "Warning: venv/Scripts/Activate.ps1 not found, skipping" 'WARNING'
}

# Проверка наличия основного скрипта
$StartScript = Join-Path $Root 'start.ps1'
if (-not (Test-Path $StartScript)) {
    Write-Log "Error: start.ps1 not found: $StartScript" 'ERROR'
    exit 1
}

Write-Log "Action: Launching start.ps1..."

# Подготовка временных файлов для захвата потоков
$StdoutFile = Join-Path $LogDir 'autostart_stdout.tmp'
$StderrFile = Join-Path $LogDir 'autostart_stderr.tmp'

try {
    # Запуск процесса с перенаправлением вывода
    $Proc = Start-Process -FilePath 'powershell.exe' `
        -ArgumentList @(
            '-NonInteractive', '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', $StartScript
        ) `
        -WorkingDirectory $Root `
        -RedirectStandardOutput "$StdoutFile" `
        -RedirectStandardError  "$StderrFile" `
        -NoNewWindow `
        -PassThru `
        -Wait

    # Чтение и фильтрация stdout
    if (Test-Path $StdoutFile) {
        try {
            Get-Content $StdoutFile -Encoding UTF8 | ForEach-Object {
                # Удаление ANSI escape-последовательностей
                $CleanText = $_ -replace '\x1b\[[0-9;]*m', ''
                if ($CleanText.Trim()) { Write-Log $CleanText }
            }
            Remove-Item $StdoutFile -Force
        } catch {
            Write-Log "Exception: STDOUT processing failed: $_" 'ERROR'
        }
    }

    # Чтение и фильтрация stderr
    if (Test-Path $StderrFile) {
        try {
            Get-Content $StderrFile -Encoding UTF8 | ForEach-Object {
                $CleanText = $_ -replace '\x1b\[[0-9;]*m', ''
                if ($CleanText.Trim()) { Write-Log $CleanText 'ERROR' }
            }
            Remove-Item $StderrFile -Force
        } catch {
            Write-Log "Exception: STDERR processing failed: $_" 'ERROR'
        }
    }

    # Анализ кода завершения
    $ExitCode = $Proc.ExitCode
    if ($ExitCode -eq 0) {
        Write-Log "start.ps1 completed successfully (exit 0)"
    } else {
        Write-Log "Error: start.ps1 completed with code $ExitCode" 'ERROR'
        exit $ExitCode
    }
} catch {
    Write-Log "Exception: Error launching start.ps1: $_" 'ERROR'
    exit 1
}
