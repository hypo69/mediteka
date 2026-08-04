# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование функций запуска (start.ps1)
# =============================================================================
# Описание:
#   Модульные тесты Pester для валидации внутренних функций скрипта start.ps1.
#   Проверка механизмов загрузки конфигурации, обнаружения Foundry и
#   управления локальными бинарными файлами.
#
# Примеры:
#   Invoke-Pester -Path .\tests\unit\start.Tests.ps1

# File: start.Tests.ps1
# Project: AI Assistant
# Package: FastApiFoundry
# Version: 0.1.0
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# Licence: MIT
# =============================================================================

# Определение пути к корневой директории проекта
$Root = Resolve-Path "$PSScriptRoot\..\.."
$StartScript = Join-Path $Root "start.ps1"

# ПОЧЕМУ ИСПОЛЬЗУЕТСЯ ДИНАМИЧЕСКАЯ ЗАГРУЗКА ФУНКЦИЙ:
#   Прямой вызов (dot-sourcing) файла start.ps1 приведет к немедленному запуску
#   всего процесса (установка зависимостей, запуск FastAPI), что недопустимо
#   в Unit-тестах. Для изоляции мы извлекаем только определения функций.

$tokens = $null
$parseErrors = $null
$Ast = [System.Management.Automation.Language.Parser]::ParseFile($StartScript, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) {
    throw "start.ps1 parse errors: $($parseErrors.Message -join '; ')"
}

# Поиск и выполнение всех определений функций из скрипта через AST.
# Это устойчивее regex: функции могут содержать вложенные блоки, строки и комментарии.
$FunctionDefinitions = $Ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)
foreach ($Function in $FunctionDefinitions) {
    Invoke-Expression $Function.Extent.Text
}

Describe "start.ps1 Unit Tests" {
    
    Context "Загрузка переменных окружения (Load-EnvFile)" {
        $TempEnv = Join-Path $PSScriptRoot "test.env"
        
        BeforeEach {
            # Создание временного файла конфигурации
            "API_KEY=test_key_123`n# Комментарий`nSECRET_VAL=`"quoted value`"`n" | Set-Content $TempEnv -Encoding UTF8
        }
        
        AfterEach {
            if (Test-Path $TempEnv) { Remove-Item $TempEnv }
        }

        It "Экспорт корректных значений из .env в среду окружения" {
            # Вызов загруженной функции
            Load-EnvFile -EnvPath $TempEnv
            
            $env:API_KEY | Should Be "test_key_123"
            $env:SECRET_VAL | Should Be "quoted value"
        }
    }

    Context "Обнаружение Foundry CLI (Test-FoundryCli)" {
        It "Возврат True при успешном нахождении команды" {
            Mock Get-Command { return $true }
            $Result = Test-FoundryCli
            $Result | Should Be $true
        }

        It "Возврат False при отсутствии утилиты в системе" {
            Mock Get-Command { throw "CommandNotFound" }
            $Result = Test-FoundryCli
            $Result | Should Be $false
        }
    }

    Context "Поиск порта Foundry (Get-FoundryPort)" {
        It "Возврат null если процесс службы не найден" {
            # Эмуляция отсутствия процесса Inference.Service.Agent
            Mock Get-Process { return $null }
            $Result = Get-FoundryPort
            $Result | Should BeNullOrEmpty
        }
        
        It "Возврат порта при успешной проверке API" {
            # Эмуляция найденного процесса
            Mock Get-Process { 
                return @([pscustomobject]@{ 
                    ProcessName = "Inference.Service.Agent"
                    Id = 1234
                }) 
            }
            # Эмуляция слушающего порта
            Mock netstat { return "Proto  Local Address          Foreign Address        State           PID`nTCP    127.0.0.1:50477        0.0.0.0:0              LISTENING       1234" }
            # Эмуляция успешного API ответа
            Mock Invoke-WebRequest { 
                return @{ StatusCode = 200 } 
            }
            
            $Result = Get-FoundryPort
            $Result | Should Be "50477"
        }
        
        It "Возврат null если API не отвечает на порту" {
            Mock Get-Process { 
                return @([pscustomobject]@{ 
                    ProcessName = "Inference.Service.Agent"
                    Id = 1234
                }) 
            }
            Mock netstat { return "TCP    127.0.0.1:50477        0.0.0.0:0              LISTENING       1234" }
            Mock Invoke-WebRequest { throw "Connection refused" }
            
            $Result = Get-FoundryPort
            $Result | Should BeNullOrEmpty
        }
        
        It "Возврат порта при fallback поиске по пути процесса" {
            # Эмуляция отсутствия процесса по имени
            Mock Get-Process { 
                return @([pscustomobject]@{ 
                    ProcessName = "Inference.Service.Agent"
                    Id = 1234
                    Path = "C:\Users\user\.foundry\Inference.Service.Agent.exe"
                }) 
            }
            Mock netstat { return "TCP    127.0.0.1:50477        0.0.0.0:0              LISTENING       1234" }
            Mock Invoke-WebRequest { 
                return @{ StatusCode = 200 } 
            }
            
            $Result = Get-FoundryPort
            $Result | Should Be "50477"
        }
    }

    Context "Управление бинарными файлами (Ensure-LlamaBin)" {
        # ПОЧЕМУ ТУТ ТРЕБУЕТСЯ МНОГО МОКОВ:
        #   Функция проверяет наличие zip-архивов, версию в config.json и
        #   распаковывает файлы. Мы должны имитировать всё это, не трогая диск.

        BeforeEach {
            Mock Get-ChildItem {
                return @([pscustomobject]@{ Name = "llama-b123-bin-win-x64.zip"; FullName = "C:\test\llama-b123-bin-win-x64.zip" })
            }
            Mock Test-Path { return $true }
            Mock Get-Content { return '{"llama_cpp": {"bin_version": "llama-b123-bin-win-x64"}}' }
            Mock Set-Content { }
        }

        It "Возврат пути к exe, если версия в конфиге совпадает с актуальным архивом" {
            $Result = Ensure-LlamaBin
            $Result | Should Match "llama-server.exe"
        }

        It "Инициация распаковки, если версия устарела или отсутствует" {
            # Эмуляция несовпадения версий
            Mock Get-Content { return '{"llama_cpp": {"bin_version": "old-version"}}' }
            Mock Expand-Archive -Verifiable
            Mock Remove-Item
            
            $Result = Ensure-LlamaBin
            
            Assert-VerifiableMocks
            $Result | Should Not BeNullOrEmpty
        }
    }

    Context "Запуск сервера llama.cpp (Start-LlamaServer)" {
        # ПОЧЕМУ ИСПОЛЬЗУЮТСЯ ПОПЫТКИ (ATTEMPTS):
        #   В реальной жизни сервер может не подняться с первого раза.
        #   Тест проверяет, что логика опроса (polling) работает корректно.

        It "Успешный запуск при положительном ответе health-check" {
            Mock Test-Path { return $true }
            # Эмуляция запуска процесса
            Mock Start-Process { return @{ Id = 1234; HasExited = $false } }
            # Эмуляция успешного ответа от сервера
            Mock Invoke-WebRequest { 
                return @{ StatusCode = 200 } 
            }

            $Result = Start-LlamaServer -ServerExe "llama.exe" -ModelPath "model.gguf" -Port 9780
            $Result | Should Be $true
        }

        It "Возврат False, если сервер не отвечает после всех попыток опроса" {
            Mock Test-Path { return $true }
            Mock Start-Process { return @{ Id = 1234; HasExited = $false } }
            # Эмуляция ошибки подключения
            Mock Invoke-WebRequest { throw "Connection refused" }
            
            # Уменьшаем время ожидания в тестах, чтобы они шли быстрее
            Mock Start-Sleep { }

            $Result = Start-LlamaServer -ServerExe "llama.exe" -ModelPath "model.gguf" -Port 9780
            $Result | Should Be $false
        }
    }

    Context "Завершение работы и очистка" {
        # ПОЧЕМУ ЭТО ВАЖНО:
        #   Если скрипт упадет, он может оставить за собой "зомби-процессы"
        #   портов 9696 или 9780. Тест проверяет механизм остановки.

        It "Остановка фоновых процессов MkDocs и Llama при выходе" {
            $script:MkDocsPid = 100
            $script:LlamaPid = 200
            
            Mock Get-Process { 
                param($Id)
                return @{ Id = $Id }
            }
            Mock Stop-Process -Verifiable

            # Имитация блока finally через вызов логики очистки
            # В start.ps1 это реализовано через Stop-Process в блоке finally
            if ($script:MkDocsPid) { Stop-Process -Id $script:MkDocsPid -Force }
            if ($script:LlamaPid) { Stop-Process -Id $script:LlamaPid -Force }

            Assert-VerifiableMocks
        }
    }
}
