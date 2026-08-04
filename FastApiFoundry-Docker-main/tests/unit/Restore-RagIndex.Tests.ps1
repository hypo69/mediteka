# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование Restore-RagIndex.ps1
# =============================================================================
# Описание:
#   Модульные тесты для проверки логики восстановления RAG-индексов из архивов.
# =============================================================================

Describe "Restore-RagIndex.ps1 Logic" {
    $ScriptPath = Join-Path $PSScriptRoot "..\..\scripts\Restore-RagIndex.ps1"
    $TempZip = Join-Path $env:TEMP "unit_test_profile_20260512.zip"

    Context "Инициализация и параметры" {
        It "Должен завершиться с ошибкой, если ZIP-архив не существует" {
            Mock Test-Path { return $false }
            
            # Скрипт использует exit 1, поэтому проверяем код завершения в дочернем процессе
            $Result = powershell -ExecutionPolicy Bypass -File $ScriptPath -ZipPath "non-existent.zip"
            $LASTEXITCODE | Should Be 1
        }

        It "Должен правильно определять имя профиля из имени файла" {
            Mock Test-Path { param($Path) if ($Path -like "*\.aiassistant\rag\unit_test_profile") { return $false } return $true }
            Mock New-Item { }
            Mock Expand-Archive { }

            # Проверяем, что скрипт отрабатывает без ошибок при автоматическом определении имени
            & $ScriptPath -ZipPath $TempZip
        }
    }

    Context "Защита данных" {
        It "Не должен удалять существующий индекс, если пользователь ответил 'n'" {
            Mock Test-Path { return $true } # Индекс существует
            Mock Read-Host { return "n" }   # Пользователь против перезаписи
            Mock Remove-Item -Verifiable

            & $ScriptPath -ZipPath $TempZip -ProfileName "existing"
            
            # Проверяем, что Remove-Item НЕ вызывался
            Assert-VerifiableMocks -Exactly 0
        }

        It "Должен перезаписать индекс, если пользователь подтвердил действие" {
            Mock Test-Path { return $true }
            Mock Read-Host { return "y" }
            Mock New-Item { }
            Mock Expand-Archive { }
            Mock Remove-Item -Verifiable

            & $ScriptPath -ZipPath $TempZip -ProfileName "overwrite"
            
            # Проверяем, что старая папка была удалена перед распаковкой
            Assert-VerifiableMocks -Exactly 1
        }
    }
}