# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Завершение установки
# =============================================================================
# Описание:
#   Финальные шаги установки: загрузка моделей по умолчанию, создание ярлыков,
#   проведение аудита безопасности зависимостей и вывод инструкций по запуску.
#
# File: scripts/Install/Step-Finalize.ps1
# Project: Наш интеллектуальный помощник
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$InstallLogFile
)

$firstInstallMarker = Join-Path $Root 'venv\.first_install_done'
if (-not (Test-Path $firstInstallMarker)) {
    $answer = Read-Host "`nDownload default models? (y/N)"
    if ($answer -eq 'y' -or $answer -eq 'Y') {
        & (Get-InstallScriptPath 'Install-Models.ps1')
    }
    '' | Out-File $firstInstallMarker -Encoding UTF8
}

Write-Host "`nCreating shortcuts..." -ForegroundColor Yellow
$makeIco = Get-InstallScriptPath 'Make-Ico.ps1'
if (Test-Path $makeIco) {
    try { & $makeIco -ProjectRoot $Root } catch { Write-Host "  icon.ico warning: $_" -ForegroundColor Yellow }
}

Write-Host "`nSecurity audit..." -ForegroundColor Cyan
if (Test-Path $Python) {
    try {
        & $Python -m pip install pip-audit --quiet
        & $Python -m pip_audit
        if ($LASTEXITCODE -eq 0) {
            Write-Host '  No known vulnerabilities detected.' -ForegroundColor Green
        } else {
            Write-Host '  Potential vulnerabilities detected. Run Invoke-Qa.ps1 for details.' -ForegroundColor Yellow
        }
    } catch {
        Write-Host '  Security audit failed or was skipped.' -ForegroundColor Gray
    }
}

Write-Host "`n$('=' * 50)" -ForegroundColor Green
Write-Host 'Installation complete!' -ForegroundColor Green

$appPort = 9696
$docsPort = 9697
try {
    $cfg = Get-Content (Join-Path $Root 'config.json') -Raw | ConvertFrom-Json
    if ($cfg.fastapi_server.port) { $appPort = [int]$cfg.fastapi_server.port }
    if ($cfg.docs_server.port) { $docsPort = [int]$cfg.docs_server.port }
} catch { }

Write-Host ''
Write-Host "  Web UI:    http://localhost:$appPort" -ForegroundColor Green
Write-Host "  Docs:      http://localhost:$docsPort" -ForegroundColor Green
Write-Host "  Swagger:   http://localhost:$appPort/docs" -ForegroundColor Green
Write-Host "  Install log: $InstallLogFile" -ForegroundColor Green
Write-Host ''
Write-Host '  Start: powershell -ExecutionPolicy Bypass -File .\start.ps1' -ForegroundColor Cyan
Write-InstallLog '=== FastAPI Foundry install.ps1 completed ==='
