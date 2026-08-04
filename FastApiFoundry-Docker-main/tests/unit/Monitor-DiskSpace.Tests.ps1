# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование Monitor-DiskSpace.ps1
# =============================================================================
# Описание:
#   Проверка логики мониторинга диска, вызова очистки и Telegram уведомлений.
# =============================================================================

Describe "Monitor-DiskSpace.ps1 Logic" {
    $ScriptPath = Join-Path $PSScriptRoot "..\..\scripts\Monitor-DiskSpace.ps1"
    $CleanupPath = Join-Path $PSScriptRoot "..\..\scripts\Clear-TempFiles.ps1"

    Context "Когда места на диске достаточно" {
        It "Не должен вызывать очистку или уведомления" {
            # Мокаем диск: 50 ГБ свободно (Threshold = 5)
            Mock Get-CimInstance {
                return [pscustomobject]@{
                    DeviceID = "C:"
                    FreeSpace = 50 * 1GB
                    Size = 100 * 1GB
                }
            } -ParameterFilter { $Filter -like "*C:*" }

            Mock Test-Path { return $true }
            Mock Invoke-RestMethod -Verifiable

            # Запуск скрипта
            & $ScriptPath -ThresholdGB 5

            # Проверка, что Telegram не вызывался
            Assert-VerifiableMocks -Exactly 0
        }
    }

    Context "Когда места мало (< Threshold)" {
        BeforeEach {
            # Окружение для Telegram
            $env:TELEGRAM_ADMIN_TOKEN = "test_token"
            $env:TELEGRAM_ADMIN_IDS = "12345"
            
            Mock Test-Path { param($Path) return $true }
        }

        It "Должен запустить Clear-TempFiles.ps1 и отправить уведомление, если не помогло" {
            # Сначала мало места, и после "очистки" все еще мало
            $diskObj = [pscustomobject]@{
                DeviceID = "C:"
                FreeSpace = 2 * 1GB
                Size = 100 * 1GB
            }
            Mock Get-CimInstance { return $diskObj }
            
            Mock Invoke-RestMethod -Verifiable

            & $ScriptPath -ThresholdGB 5

            # Проверка, что уведомление было отправлено
            Assert-VerifiableMocks -Exactly 1
        }

        It "Должен выйти после очистки, если место освободилось" {
            $calls = 0
            Mock Get-CimInstance {
                $calls++
                if ($calls -eq 1) { return [pscustomobject]@{ DeviceID = "C:"; FreeSpace = 2 * 1GB; Size = 100 * 1GB } }
                return [pscustomobject]@{ DeviceID = "C:"; FreeSpace = 10 * 1GB; Size = 100 * 1GB }
            }

            Mock Invoke-RestMethod -Verifiable

            & $ScriptPath -ThresholdGB 5

            # Уведомление НЕ должно быть отправлено (т.к. exit 0 после успеха очистки)
            Assert-VerifiableMocks -Exactly 0
        }
    }
}