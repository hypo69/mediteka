# -*- coding: utf-8 -*-
# Модульные тесты для проверки логики start.ps1

$StartScriptPath = Join-Path $PSScriptRoot "..\start.ps1"
$TestEnvPath = Join-Path $PSScriptRoot "test.env"

Describe "Start-Project Logic" {
    Context "Загрузка переменных окружения" {
        BeforeAll {
            "TEST_VAR=hello_world`nSECRET_KEY=12345`n# Comment`nINVALID_LINE" | Set-Content $TestEnvPath -Encoding UTF8
            
            # Динамическая загрузка функции Load-EnvFile из скрипта
            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($StartScriptPath, [ref]$tokens, [ref]$errors)
            $func = $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $args[0].Name -eq "Load-EnvFile" }, $true)
            Invoke-Expression $func.Extent.Text
        }

        AfterAll {
            if (Test-Path $TestEnvPath) { Remove-Item $TestEnvPath }
            [System.Environment]::SetEnvironmentVariable("TEST_VAR", $null)
            [System.Environment]::SetEnvironmentVariable("SECRET_KEY", $null)
        }

        It "Load-EnvFile корректно устанавливает переменные" {
            Load-EnvFile -EnvPath $TestEnvPath
            
            $env:TEST_VAR | Should -Be "hello_world"
            $env:SECRET_KEY | Should -Be "12345"
        }

        It "Игнорирует комментарии и некорректные строки" {
            [System.Environment]::GetEnvironmentVariable("INVALID_LINE") | Should -BeNullOrEmpty
        }
    }
}