# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Настройка окружения Python
# =============================================================================
# Описание:
#   Поиск интерпретатора Python 3.11+, создание виртуального окружения (venv),
#   обновление pip и установка основных и опциональных зависимостей проекта.
#
# File: scripts/Install/Step-PythonEnvironment.ps1
# Project: Наш интеллектуальный помощник
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$true)][string]$Root,
    [switch]$Force,
    [switch]$SkipRag # Добавление параметра для пропуска установки RAG-зависимостей
)

Write-Host 'FastAPI Foundry - Installation' -ForegroundColor Green
Write-Host ('=' * 50)

Write-Host "`nChecking Python..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @('python', 'python3', 'python311')) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match 'Python 3\.(1[1-9]|[2-9]\d)') {
            $pythonCmd = $cmd
            Write-Host "  Found: $ver ($cmd)" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $pythonCmd) {
    $localZip = Join-Path $Root 'bin\Python-3.11.9.zip'
    if (Test-Path $localZip) {
        Write-Host "  Local archive found: $localZip" -ForegroundColor Cyan
        $answer = Read-Host '  Install Python from local archive? (y/N)'
        if ($answer -ne 'y' -and $answer -ne 'Y') { exit 1 }

        $localPythonDir = Join-Path $Root 'bin\Python-3.11.9'
        if (-not (Test-Path $localPythonDir)) {
            Expand-Archive -Path $localZip -DestinationPath $localPythonDir
        }
        $pythonCmd = Get-ChildItem -Path $localPythonDir -Filter 'python.exe' -Recurse |
                     Select-Object -First 1 -ExpandProperty FullName
        if (-not $pythonCmd) {
            Write-Host '  python.exe not found in archive' -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host '  Python 3.11+ not found. Download: https://www.python.org/downloads/' -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nVirtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $Root 'venv'

if ((Test-Path $venvPath) -and $Force) {
    Stop-VenvProcesses -VenvPath $venvPath
    try {
        Remove-Item $venvPath -Recurse -Force
        Write-Host '  Old venv removed' -ForegroundColor Gray
    } catch {
        Write-Host "  Could not remove venv: $_" -ForegroundColor Red
        Write-Host '  Close all terminals/apps using the venv and retry.' -ForegroundColor Cyan
        exit 1
    }
} elseif (Test-Path $venvPath) {
    Write-Host '  venv already exists.' -ForegroundColor Yellow
    $answer = Read-Host '  Recreate? (y/N)'
    if ($answer -eq 'y' -or $answer -eq 'Y') {
        Stop-VenvProcesses -VenvPath $venvPath
        try {
            Remove-Item $venvPath -Recurse -Force
            Write-Host '  venv removed' -ForegroundColor Gray
        } catch {
            Write-Host "  Could not remove venv: $_" -ForegroundColor Red
            Write-Host '  Close all terminals/apps using the venv and retry.' -ForegroundColor Cyan
            exit 1
        }
    }
}

if (-not (Test-Path $venvPath)) {
    & $pythonCmd -m venv $venvPath
    Write-Host "  venv created: $venvPath" -ForegroundColor Green
}

$python = Join-Path $venvPath 'Scripts\python.exe'

Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip | Out-Null
Write-Host '  pip upgraded' -ForegroundColor Green

Write-Host "`nInstalling requirements.txt..." -ForegroundColor Yellow
& $python -m pip install -r (Join-Path $Root 'requirements.txt')
Write-Host '  Core dependencies installed' -ForegroundColor Green

Write-Host "`nOptional dependency sets:" -ForegroundColor Yellow
$optionalReqs = @(
    @{ File = 'requirements-qa.txt';     Label = 'QA / testing tools (pytest, ruff, mypy, httpx, coverage)' },
    @{ File = 'requirements-google.txt'; Label = 'Google Workspace integration (GoogleAgent)'               },
    @{ File = 'docs/requirements.txt';   Label = 'MkDocs plugins (documentation build only)'                },
    @{ File = 'mcp/requirements.txt';    Label = 'Python MCP server dependencies'                           }
)

foreach ($req in $optionalReqs) {
    $reqPath = Join-Path $Root $req.File
    if (-not (Test-Path $reqPath)) {
        Write-Host "  [$($req.File)] not found - skipping" -ForegroundColor Gray
        continue
    }
    $answer = Read-Host "  Install $($req.Label)?`n  ($($req.File)) (y/N)"
    if ($answer -eq 'y' -or $answer -eq 'Y') {
        Write-Host "  Installing $($req.File)..." -ForegroundColor Cyan
        try {
            & $python -m pip install -r $reqPath
            Write-Host "  $($req.File) installed" -ForegroundColor Green
        } catch {
            Write-Host "  Error installing $($req.File): $_" -ForegroundColor Yellow
            Write-Host "  Retry manually: pip install -r $($req.File)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  Skipped $($req.File)" -ForegroundColor Gray
    }
}

# Блок установки RAG-зависимостей
if (-not $SkipRag) {
    Write-Host "`n📦 Проверка RAG-зависимостей (torch, sentence-transformers, faiss)..." -ForegroundColor Cyan
    
    # Вызов python-скрипта, который теперь сам читает требования из requirements.txt
    & $python (Join-Path $Root 'scripts\Install\install_rag_deps.py')
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Установка некоторых RAG-компонентов завершилась с ошибкой. Функции RAG могут быть недоступны."
    }
} else {
    Write-Host "⏭️ Пропуск RAG-зависимостей по запросу." -ForegroundColor Gray
}
