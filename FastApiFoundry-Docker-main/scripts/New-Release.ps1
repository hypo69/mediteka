# -*- coding: utf-8 -*-
# =============================================================================
# Название: Создание нового релиза (New-Release)
# =============================================================================
# Описание:
#   Автоматизирует инкремент версии, обновление VERSION и создание Git-тега.
# =============================================================================
#
# <#
# .SYNOPSIS
#     Автоматизирует процесс обновления версии проекта и создания Git-тега.
# .DESCRIPTION
#     Этот скрипт интерактивно запрашивает у пользователя тип обновления версии (patch, minor, major),
#     затем обновляет файл `VERSION` в корне проекта. После обновления версии,
#     скрипт выполняет Git-операции: добавляет измененный файл `VERSION`,
#     создает коммит с сообщением о новой версии и создает аннотированный Git-тег.
#     В конце выводится напоминание о необходимости `git push --tags`.
# .EXAMPLE
#     .\New-Release.ps1
#     Запускает интерактивный процесс создания нового релиза.
# .OUTPUTS
#     Выводит текущую и новую версию, статус Git-операций и напоминания.
# .NOTES
#     Требует инициализированного Git-репозитория.
#     Файл `VERSION` должен существовать в корне проекта.
#     Использует семантическое версионирование.
#     Не выполняет `git push` автоматически, чтобы дать пользователю возможность проверить изменения.
# #>
# =============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VersionFile = Join-Path $ProjectRoot 'VERSION'
$CurrentVersion = (Get-Content $VersionFile -Raw).Trim().Replace('v', '')

$v = [version]$CurrentVersion

Write-Host "🚀 Текущая версия: v$CurrentVersion" -ForegroundColor Cyan
Write-Host "Выберите тип обновления:"
Write-Host "1. Patch (v$($v.Major).$($v.Minor).$($v.Build + 1))"
Write-Host "2. Minor (v$($v.Major).$($v.Minor + 1).0)"
Write-Host "3. Major (v$($v.Major + 1).0.0)"

$choice = Read-Host "Введите номер (1-3)"

switch ($choice) {
    '1' { $NewVersion = "v$($v.Major).$($v.Minor).$($v.Build + 1)" }
    '2' { $NewVersion = "v$($v.Major).$($v.Minor + 1).0" }
    '3' { $NewVersion = "v$($v.Major + 1).0.0" }
    Default { Write-Host "❌ Отмена."; exit }
}

Write-Host "🆕 Новая версия: $NewVersion" -ForegroundColor Green
$Confirm = Read-Host "Подтвердить? (y/n)"
if ($Confirm -ne 'y') { exit }

# Обновление файла
$NewVersion | Set-Content $VersionFile -NoNewline

# Git операции
try {
    git add $VersionFile
    git commit -m "chore: bump version to $NewVersion"
    git tag -a $NewVersion -m "Release $NewVersion"
    Write-Host "✅ Версия обновлена и тег $NewVersion создан локально." -ForegroundColor Green
    Write-Host "💡 Не забудьте выполнить: git push --tags" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️  Git-команды не выполнены (возможно, Git не инициализирован)." -ForegroundColor Yellow
}