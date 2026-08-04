# -*- coding: utf-8 -*-
# =============================================================================
# Название: Настройка Git Hooks (Setup-GitHooks)
# =============================================================================
# Описание:
#   Устанавливает pre-commit hook, который запускает Invoke-Qa.ps1 перед коммитом.
# =============================================================================
#
# <#
# .SYNOPSIS
#     Автоматически настраивает локальные Git Hooks для проекта.
# .DESCRIPTION
#     Скрипт проверяет наличие директории .git и создает (или перезаписывает)
#     файл .git/hooks/pre-commit. Этот хук заставляет Git запускать полный
#     цикл QA проверок перед каждым созданием коммита. Если проверки не пройдены,
#     коммит будет отклонен.
# .EXAMPLE
#     .\Setup-GitHooks.ps1
# .NOTES
#     Использует PowerShell для запуска проверок, что гарантирует кроссплатформенность
#     внутри среды Windows/PowerShell Core.
# #>
# =============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$HooksDir = Join-Path $ProjectRoot ".git\hooks"
$PreCommitHook = Join-Path $HooksDir "pre-commit"

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    Write-Host "⚠️  Git не инициализирован. Пропуск установки хуков." -ForegroundColor Yellow
    exit 0
}

# Содержимое хука (вызов Invoke-Qa.ps1)
# Мы используем -SkipCoverageReport, чтобы не открывать браузер при каждом коммите
$HookContent = @"
#!/bin/sh
# AI Assistant Pre-commit Hook
echo "🔍 Running pre-commit QA checks..."
pwsh.exe -ExecutionPolicy Bypass -File ./scripts/Invoke-Qa.ps1 -SkipCoverageReport

RESULT=\$?
if [ \$RESULT -ne 0 ]; then
    echo "❌ QA checks failed. Commit aborted."
    exit 1
fi
exit 0
"@

try {
    $HookContent | Set-Content $PreCommitHook -Encoding utf8NoBOM
    Write-Host "✅ Git pre-commit hook успешно установлен." -ForegroundColor Green
}
catch {
    Write-Host "❌ Не удалось установить Git Hook: $($_.Exception.Message)" -ForegroundColor Red
}
