# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Запуск Desktop UI
# =============================================================================
# Описание:
#   Запуск Desktop-клиента на базе pywebview.
#   Проверка зависимостей и активация виртуального окружения из корня.
#
# Примеры:
#   powershell -ExecutionPolicy Bypass -File .\gui\Start-User.ps1
#
# File: Start-User.ps1
# Project: Ai Assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
# Поиск Python в родительской директории проекта
$PYTHON = Resolve-Path (Join-Path $Root '..\venv\Scripts\python.exe') -ErrorAction SilentlyContinue

if (-not (Test-Path $PYTHON)) {
    Write-Host "❌ Виртуальное окружение не найдено по пути: $(Join-Path $Root '..\venv')" -ForegroundColor Red
    Write-Host "Запустите install.ps1 из корня проекта." -ForegroundColor Yellow
    Pause
    exit 1
}

Write-Host "📦 Проверка зависимостей (pywebview)..." -ForegroundColor Cyan
& $PYTHON -m pip install pywebview --quiet 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при установке/проверке pywebview." -ForegroundColor Red
    Pause
    exit 1
}

Write-Host "🚀 Запуск интерфейса..." -ForegroundColor Green

# Установка рабочей директории в gui для корректности путей
Set-Location $Root

& $PYTHON app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Приложение закрылось с кодом ошибки $LASTEXITCODE" -ForegroundColor Red
    Pause
}