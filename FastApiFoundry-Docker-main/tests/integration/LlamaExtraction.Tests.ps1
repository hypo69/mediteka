# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Интеграционное тестирование распаковки (llama.cpp)
# =============================================================================
# Описание:
#   Проверка корректности работы функции Ensure-LlamaBin при взаимодействии
#   с реальной файловой системой. Тест создает временную структуру папок,
#   генерирует тестовый архив и проверяет его извлечение.
#
# Примеры:
#   Invoke-Pester -Path .\tests\integration\LlamaExtraction.Tests.ps1
#
# File: LlamaExtraction.Tests.ps1
# Project: Ai Assistant
# Package: FastApiFoundry
# Version: 0.1.0
# Author: Gemini Code Assist
# Copyright: © 2024 - 2026 hypo69
# Date: 2025
# =============================================================================

# Определение путей
$OriginalRoot = Resolve-Path "$PSScriptRoot\..\.."
$StartScript = Join-Path $OriginalRoot "start.ps1"
$TestTempPath = Join-Path $env:TEMP "Ai Assistant_IntegrationTests_$(Get-Random)"

# ПОЧЕМУ ИСПОЛЬЗУЕТСЯ ТЕКСТОВАЯ ИНЪЕКЦИЯ:
#   Функция Ensure-LlamaBin использует глобальную переменную $Root.
#   Для изоляции интеграционного теста мы переопределяем $Root на временную папку.
$tokens = $null
$parseErrors = $null
$Ast = [System.Management.Automation.Language.Parser]::ParseFile($StartScript, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) {
    throw "start.ps1 parse errors: $($parseErrors.Message -join '; ')"
}
$Function = $Ast.Find({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Ensure-LlamaBin'
}, $true)
if (-not $Function) { throw "Функция Ensure-LlamaBin не найдена в start.ps1" }
Invoke-Expression $Function.Extent.Text

Describe "Интеграция: Распаковка llama.cpp" {

    BeforeAll {
        # Создание временной структуры проекта
        New-Item -ItemType Directory -Path $TestTempPath -Force | Out-Null
        $script:binDir = New-Item -ItemType Directory -Path (Join-Path $TestTempPath "bin") -Force
        
        # Создание фиктивного config.json
        $DefaultConfig = @{ llama_cpp = @{ bin_version = "none" } }
        $DefaultConfig | ConvertTo-Json | Set-Content (Join-Path $TestTempPath "config.json")

        # Подготовка тестового zip-архива
        # Имитация реального имени файла: llama-<build>-bin-win-x64.zip
        $ZipSourcePath = New-Item -ItemType Directory -Path (Join-Path $TestTempPath "temp_zip_source")
        New-Item -ItemType File -Path (Join-Path $ZipSourcePath "llama-server.exe") -Value "dummy binary content" | Out-Null
        
        $script:FixtureName = "llama-b999-bin-win-x64"
        $script:ZipPath = Join-Path $script:binDir "$script:FixtureName.zip"
        
        # Архивация тестовых данных
        Compress-Archive -Path "$ZipSourcePath\*" -DestinationPath $script:ZipPath -Force
        
        # Переопределение переменной $Root для тестируемой функции
        $script:Root = $TestTempPath
    }

    AfterAll {
        # Очистка временных файлов
        if (Test-Path $TestTempPath) { 
            Remove-Item $TestTempPath -Recurse -Force -ErrorAction SilentlyContinue 
        }
    }

    Context "Выполнение Ensure-LlamaBin" {
        
        It "Успешная распаковка нового архива в поддиректорию" {
            # ПОЧЕМУ МОКИРУЕТСЯ Read-Host:
            #   Если версия в конфиге отличается, скрипт может запросить подтверждение.
            #   Автоматизация требует эмуляции нажатия 'Y'.
            Mock Read-Host { return "Y" }

            $ResultPath = Ensure-LlamaBin

            # Проверка возвращаемого пути
            $ExpectedExe = Join-Path $script:binDir "$script:FixtureName\llama-server.exe"
            $ResultPath | Should Be $ExpectedExe

            # Проверка физического наличия файла
            Test-Path $ResultPath | Should Be $true
        }

        It "Обновление версии в файле config.json" {
            $ConfigPath = Join-Path $script:Root "config.json"
            $UpdatedConfig = Get-Content $ConfigPath | ConvertFrom-Json
            
            # Валидация записи новой версии
            $UpdatedConfig.llama_cpp.bin_version | Should Be $script:FixtureName
        }

        It "Пропуск распаковки, если версия уже актуальна" {
            # Сброс мока для проверки отсутствия вызова Expand-Archive
            Mock Expand-Archive { throw "Распаковка не должна была запускаться!" }
            
            # Повторный вызов функции
            $ResultPath = Ensure-LlamaBin
            
            $ResultPath | Should Not BeNullOrEmpty
            Test-Path $ResultPath | Should Be $true
        }
    }
}
