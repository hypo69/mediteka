# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Автоматическое исправление уязвимостей
# =============================================================================
# Описание:
#   Использует pip-audit для автоматического обновления уязвимых пакетов.
#   Пытается исправить зависимости только там, где это не вызывает конфликтов.
#
# Использование:
#   .\scripts\Fix-Vulnerabilities.ps1
# =============================================================================

$ErrorActionPreference = 'Stop'
$Root = Resolve-Path "$PSScriptRoot\.."
$VenvPython = Join-Path $Root "venv\Scripts\python.exe"

Write-Host "🛡️ Запуск процесса автоматического исправления уязвимостей..." -ForegroundColor Cyan

if (-not (Test-Path $VenvPython)) {
    Write-Host "❌ Виртуальное окружение не найдено. Сначала запустите install.ps1" -ForegroundColor Red
    exit 1
}

# --- Git Branching ---
if (git rev-parse --is-inside-work-tree 2>$null) {
    Write-Host "🌿 Подготовка git-ветки 'security-fix'..." -ForegroundColor Gray
    $branchExists = & git branch --list "security-fix"
    if ($branchExists) {
        & git checkout "security-fix"
    } else {
        & git checkout -b "security-fix"
    }
}

try {
    Write-Host "🔍 Проверка наличия pip-audit..." -ForegroundColor Gray
    & $VenvPython -m pip install pip-audit --quiet

    Write-Host "🛠️ Попытка автоматического исправления (pip-audit --fix)..." -ForegroundColor Yellow
    # --fix обновляет пакеты в текущем окружении до безопасных версий
    & $VenvPython -m pip_audit --fix

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Все возможные исправления применены успешно." -ForegroundColor Green
        
        # Обновляем requirements.txt, чтобы зафиксировать исправленные версии
        Write-Host "📝 Обновление requirements.txt..." -ForegroundColor Gray
        & $VenvPython -m pip freeze > (Join-Path $Root "requirements.txt")
        Write-Host "✅ requirements.txt синхронизирован с исправленным окружением." -ForegroundColor Green

        if (git rev-parse --is-inside-work-tree 2>$null) {
            Write-Host "💾 Создание автоматического коммита..." -ForegroundColor Gray
            git add (Join-Path $Root "requirements.txt")
            git commit -m "security: fix vulnerabilities and update requirements.txt"
            Write-Host "✅ Изменения зафиксированы в ветке 'security-fix'." -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️ Некоторые уязвимости не могут быть исправлены автоматически." -ForegroundColor Yellow
        Write-Host "💡 Требуется ручное обновление мажорных версий или смена библиотек." -ForegroundColor White
    }
} catch {
    Write-Host "❌ Произошла ошибка при попытке исправления: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nРекомендуется запустить .\scripts\Invoke-Qa.ps1 для финальной проверки." -ForegroundColor Cyan
Write-Host "Нажмите любую клавишу для выхода..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
