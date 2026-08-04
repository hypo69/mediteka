# -*- coding: utf-8 -*-
# =============================================================================
# Название: Миграция окружения (Invoke-EnvMigration)
# =============================================================================
# Описание:
#   Сравнивает .env с .env.example и сообщает о недостающих ключах.
# =============================================================================
#
# <#
# .SYNOPSIS
#     Сравнивает текущий файл .env с .env.example и выводит список отсутствующих переменных.
# .DESCRIPTION
#     Этот скрипт помогает поддерживать актуальность файла `.env` пользователя.
#     Он читает ключи переменных из `.env.example` (эталонный файл) и сравнивает их с ключами,
#     присутствующими в `.env`. Если в `.env` отсутствуют какие-либо ключи, имеющиеся в `.env.example`,
#     скрипт выводит их список, предлагая пользователю добавить их вручную.
#     Игнорирует комментарии и пустые строки.
# .EXAMPLE
#     .\Invoke-EnvMigration.ps1
#     Запускает проверку и выводит отсутствующие переменные окружения.
# .OUTPUTS
#     Выводит сообщения о статусе синхронизации `.env` и список отсутствующих ключей, если таковые имеются.
# .NOTES
#     Предполагает, что `.env.example` содержит полный набор необходимых переменных.
#     Не изменяет файлы, только информирует пользователя.
# #>
# =============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot '.env'
$ExampleFile = Join-Path $ProjectRoot '.env.example'

if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ Файл .env отсутствует. Создайте его на основе .env.example." -ForegroundColor Red
    exit 1
}

function Get-EnvKeys {
    <#
    .SYNOPSIS
        Извлекает имена переменных окружения из файла .env или .env.example.
    .DESCRIPTION
        Сканирует указанный файл построчно, извлекая все ключи переменных,
        которые не являются комментариями и имеют формат `КЛЮЧ=ЗНАЧЕНИЕ`.
    .PARAMETER Path
        Полный путь к файлу (.env или .env.example).
    .RETURNS
        Массив строк, содержащих имена переменных окружения.
    .EXAMPLE
        $keys = Get-EnvKeys -Path "C:\project\.env.example"
        # Возвращает ['HF_TOKEN', 'OPENAI_API_KEY', ...]
    #>
    param([string]$Path)
    $content = Get-Content $Path
    $keys = @()
    foreach ($line in $content) {
        if ($line -match '^([^#\s][^=]+)=') {
            $keys += $matches[1].Trim()
        }
    }
    return $keys
}

$CurrentKeys = Get-EnvKeys $EnvFile
$ExampleKeys = Get-EnvKeys $ExampleFile

$MissingKeys = $ExampleKeys | Where-Object { $CurrentKeys -notcontains $_ }

if ($MissingKeys.Count -gt 0) {
    Write-Host "⚠️  В вашем .env отсутствуют следующие ключи из примера:" -ForegroundColor Yellow
    foreach ($key in $MissingKeys) {
        Write-Host "  [ ] $key" -ForegroundColor Gray
    }
    Write-Host "`n💡 Пожалуйста, добавьте их вручную, чтобы обеспечить работу новых функций." -ForegroundColor Cyan
} else {
    Write-Host "✅ Ваш .env файл синхронизирован с .env.example." -ForegroundColor Green
}