# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: LM Studio Installer Tests
# =============================================================================
# Description:
#   Static/syntax tests for LM Studio installation scripts.
#
# Examples:
#   Invoke-Pester -Path .\tests\unit\InstallLMStudio.Tests.ps1
#
# File: tests\unit\InstallLMStudio.Tests.ps1
# Project: AI Assistant (ai_assist)
# =============================================================================

$ProjectRoot = Resolve-Path "$PSScriptRoot\..\.."
$MainInstaller = Join-Path $ProjectRoot "install.ps1"
$LMStudioInstaller = Join-Path $ProjectRoot "scripts\Install\Install-LMStudio.ps1"
$InstallerCommon = Join-Path $ProjectRoot "scripts\Install\Common.ps1"
$InstallerBackends = Join-Path $ProjectRoot "scripts\Install\Step-Backends.ps1"
$QaInstaller = Join-Path $ProjectRoot "tests\Invoke-QaInstall.ps1"

Describe "LM Studio installer integration" {
    It "scripts/Install/Install-LMStudio.ps1 has valid PowerShell syntax" {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($LMStudioInstaller, [ref]$tokens, [ref]$errors) | Out-Null
        $errors.Count | Should Be 0
    }

    It "install.ps1 has valid PowerShell syntax after LM Studio integration" {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($MainInstaller, [ref]$tokens, [ref]$errors) | Out-Null
        $errors.Count | Should Be 0
    }

    It "uses the official LM Studio Windows install command" {
        $content = Get-Content $LMStudioInstaller -Raw
        $content | Should Match 'irm\s+https://lmstudio\.ai/install\.ps1\s+\|\s+iex'
    }

    It "stops with an explanation when irm / Invoke-RestMethod is unavailable" {
        $content = Get-Content $LMStudioInstaller -Raw
        $content | Should Match 'Assert-InvokeRestMethodAvailable'
        $content | Should Match 'Get-Command irm'
        $content | Should Match 'Get-Command Invoke-RestMethod'
        $content | Should Match 'irm.*alias.*Invoke-RestMethod'
    }

    It "main install.ps1 calls the specific LM Studio installer script" {
        $content = (Get-Content $MainInstaller -Raw) + "`n" + (Get-Content $InstallerBackends -Raw)
        $content | Should Match 'Install-LMStudio\.ps1'
        $content | Should Match 'Invoke-OptionalInstallScript[\s\S]*Install-LMStudio\.ps1'
        $content | Should Match "-DisplayName 'LM Studio'"
        $content | Should Match 'Continuing installation'
        $content | Should Match 'LM Studio provider will be unavailable'
    }

    It "main install.ps1 exposes SkipLMStudio and keeps config defaults" {
        $content = (Get-Content $MainInstaller -Raw) + "`n" + (Get-Content $InstallerCommon -Raw)
        $content | Should Match '\[switch\]\$SkipLMStudio'
        $content | Should Match 'Ensure-LMStudioConfig'
        $content | Should Match "base_url\s*=\s*'http://localhost:1234'"
        $content | Should Match 'request_timeout_sec\s*=\s*300'
    }

    It "main install.ps1 writes install events to a Logs-tab-visible file" {
        $content = (Get-Content $MainInstaller -Raw) + "`n" + (Get-Content $InstallerCommon -Raw) + "`n" + (Get-Content $InstallerBackends -Raw)
        $content | Should Match 'aiassistant-install\.log'
        $content | Should Match 'function Write-InstallLog'
        $content | Should Match 'Write-InstallLog "\$DisplayName installer error'
    }

    It "QA install script can pass SkipLMStudio through to install.ps1" {
        $content = Get-Content $QaInstaller -Raw
        $content | Should Match '\[switch\]\$SkipLMStudio'
        $content | Should Match "\$installArgs \+= '-SkipLMStudio'"
    }
}

