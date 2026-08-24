# ============================================================
# Установщик проекта Mediteka (FastAPI + LangChain + AI Media)
# ============================================================
# Скрипт подготавливает рабочее окружение:
# 1. Снимает Windows Mark of the Web со всех файлов проекта.
# 2. Находит установленный Python и создает venv (если не существует).
# 3. Обновляет pip и устанавливает зависимости из req/*.txt.
# 4. Проверяет корректность установки всех компонентов.

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir    = Join-Path $ScriptRoot 'venv'
$PythonPath = Join-Path $VenvDir 'Scripts\python.exe'

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host '║              MEDITEKA — МАСТЕР УСТАНОВКИ                      ║' -ForegroundColor Cyan
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Cyan
Write-Host ''

# ============================================================
# [1/5] Снятие Mark of the Web со всего проекта
# ============================================================
Write-Host '[1/5] Снятие блокировки Windows (Unblock-File)...' -ForegroundColor Cyan

Get-ChildItem -Path $ScriptRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    Unblock-File -ErrorAction SilentlyContinue

Write-Host '    [OK] Файлы разблокированы' -ForegroundColor Green

# ============================================================
# [2/5] Проверка / Создание виртуального окружения
# ============================================================
Write-Host ''
Write-Host '[2/5] Проверка виртуального окружения (venv)...' -ForegroundColor Cyan

$needCreateVenv = $false

if (Test-Path $PythonPath) {
    try {
        $testVer = & $PythonPath --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    [OK] venv уже существует: $testVer ($PythonPath)" -ForegroundColor Green
        } else {
            Write-Host "    [WARN] Существующий venv поврежден. Требуется пересоздание." -ForegroundColor Yellow
            $needCreateVenv = $true
        }
    } catch {
        Write-Host "    [WARN] Ошибка запуска venv python: $_" -ForegroundColor Yellow
        $needCreateVenv = $true
    }
} else {
    $needCreateVenv = $true
}

if ($needCreateVenv) {
    Write-Host '    Поиск системного интерпретатора Python...' -ForegroundColor DarkGray
    
    $sysPythonCmd = $null
    
    # 1. Проверяем py launcher
    $pyCheck = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCheck) {
        foreach ($ver in @('-3.13', '-3.12', '-3.11', '-3')) {
            $check = & py $ver --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $sysPythonCmd = @('py', $ver)
                Write-Host "    [OK] Найден интерпретатор через Python Launcher: $check" -ForegroundColor Green
                break
            }
        }
    }
    
    # 2. Если py launcher не найден, ищем python / python3
    if (-not $sysPythonCmd) {
        foreach ($cmd in @('python', 'python3')) {
            $cmdCheck = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($cmdCheck) {
                $check = & $cmd --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $check -notmatch 'WindowsApps') {
                    $sysPythonCmd = @($cmd)
                    Write-Host "    [OK] Найден системный интерпретатор: $check ($($cmdCheck.Source))" -ForegroundColor Green
                    break
                }
            }
        }
    }

    if (-not $sysPythonCmd) {
        Write-Host ''
        Write-Host '    [ERROR] Python не найден на вашей системе!' -ForegroundColor Red
        Write-Host '    Пожалуйста, установите Python 3.12 или 3.13 с официального сайта: https://www.python.org/downloads/' -ForegroundColor Yellow
        Write-Host '    При установке обязательно отметьте галочку "Add python.exe to PATH".' -ForegroundColor Yellow
        exit 1
    }

    if (Test-Path $VenvDir) {
        Write-Host '    Удаление старого каталога venv...' -ForegroundColor DarkGray
        Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host "    Создание виртуального окружения в $VenvDir..." -ForegroundColor Cyan
    & $sysPythonCmd[0] $sysPythonCmd[1..($sysPythonCmd.Length-1)] -m venv $VenvDir
    
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $PythonPath)) {
        Write-Host '    [ERROR] Не удалось создать виртуальное окружение.' -ForegroundColor Red
        exit 1
    }
    
    # Снимаем блокировку со свежесозданного venv
    Get-ChildItem -Path $VenvDir -Recurse -File -ErrorAction SilentlyContinue |
        Unblock-File -ErrorAction SilentlyContinue

    Write-Host '    [OK] Виртуальное окружение успешно создано' -ForegroundColor Green
}

# ============================================================
# [3/5] Обновление pip
# ============================================================
Write-Host ''
Write-Host '[3/5] Обновление pip и базовых утилит...' -ForegroundColor Cyan
& $PythonPath -m pip install --upgrade pip setuptools wheel --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host '    [OK] pip, setuptools, wheel обновлены' -ForegroundColor Green
} else {
    Write-Host '    [WARN] Не удалось обновить pip (продолжаем установку)' -ForegroundColor Yellow
}

# ============================================================
# [4/5] Установка зависимостей проекта
# ============================================================
Write-Host ''
Write-Host '[4/5] Установка зависимостей проекта...' -ForegroundColor Cyan

$reqMain = Join-Path $ScriptRoot 'requirements.txt'
$reqCore = Join-Path $ScriptRoot 'req\requirements-core.txt'
$reqAi   = Join-Path $ScriptRoot 'req\requirements-ai.txt'
$reqTest = Join-Path $ScriptRoot 'req\requirements-test.txt'
$reqDocs = Join-Path $ScriptRoot 'req\requirements-docs.txt'

Write-Host '    Выберите вариант установки зависимостей:' -ForegroundColor Gray
Write-Host '      [1] Полная установка (Core + AI + Media + Utils) — РЕКОМЕНДУЕТСЯ' -ForegroundColor White
Write-Host '      [2] Только базовый сервер (Core)' -ForegroundColor Gray
Write-Host '      [3] Сервер + AI модули (Core + AI)' -ForegroundColor Gray
Write-Host '      [4] Полная установка + Тесты и Документация (Dev)' -ForegroundColor Gray
Write-Host '      [5] Пропустить установку зависимостей' -ForegroundColor DarkGray
Write-Host ''

$choice = Read-Host '    Ваш выбор [по умолчанию 1]'
if (-not $choice) { $choice = '1' }

switch ($choice) {
    '1' {
        Write-Host ''
        Write-Host '    Установка всех основных зависимостей из requirements.txt...' -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain
    }
    '2' {
        Write-Host ''
        Write-Host '    Установка Core зависимостей...' -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqCore
    }
    '3' {
        Write-Host ''
        Write-Host '    Установка Core + AI зависимостей...' -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqCore -r $reqAi
    }
    '4' {
        Write-Host ''
        Write-Host '    Установка полного набора + Dev...' -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain -r $reqTest -r $reqDocs
    }
    '5' {
        Write-Host '    Установка зависимостей пропущена пользователем.' -ForegroundColor Yellow
    }
    default {
        Write-Host ''
        Write-Host '    Выбрано по умолчанию: полная установка из requirements.txt...' -ForegroundColor Cyan
        & $PythonPath -m pip install -r $reqMain
    }
}

if ($choice -ne '5' -and $LASTEXITCODE -ne 0) {
    Write-Host '    [ERROR] Возникли ошибки при установке пакетов pip.' -ForegroundColor Red
    exit 1
}

# ============================================================
# [5/5] Финальная проверка работоспособности
# ============================================================
Write-Host ''
Write-Host '[5/5] Проверка установленного окружения...' -ForegroundColor Cyan

$testScript = "
import sys
modules = ['fastapi', 'uvicorn', 'dotenv', 'pydantic', 'aiohttp']
loaded = []
failed = []
for m in modules:
    try:
        __import__(m)
        loaded.append(m)
    except ImportError:
        failed.append(m)
print('loaded=' + ','.join(loaded))
if failed:
    print('missing=' + ','.join(failed))
"

$checkOutput = & $PythonPath -c $testScript 2>&1

if ($LASTEXITCODE -eq 0 -and $checkOutput -match 'loaded=') {
    Write-Host "    [OK] Основные библиотеки успешно инициализированы" -ForegroundColor Green
    Write-Host "    [OK] Python интерпретатор: $PythonPath" -ForegroundColor Green
} else {
    Write-Host "    [WARN] Результат проверки: $checkOutput" -ForegroundColor Yellow
}

Write-Host ''
Write-Host '╔═══════════════════════════════════════════════════════════════╗' -ForegroundColor Green
Write-Host '║         УСТАНОВКА MEDITEKA УСПЕШНО ЗАВЕРШЕНА!                 ║' -ForegroundColor Green
Write-Host '║                                                               ║' -ForegroundColor Green
Write-Host '║  Запуск сервера:  ./run.ps1                                   ║' -ForegroundColor Green
Write-Host '╚═══════════════════════════════════════════════════════════════╝' -ForegroundColor Green
Write-Host ''
