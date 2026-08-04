# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Установка ИИ-бэкендов
# =============================================================================
# Описание:
#   Оркестрация установки бэкендов инференса: llama.cpp, Foundry Local, 
#   LM Studio, Ollama и OpenCode в соответствии с режимом установки.
#
# File: scripts/Install/Step-Backends.ps1
# Project: Наш интеллектуальный помощник
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Mode,
    [switch]$SkipLMStudio,
    [switch]$SkipOllama
)

$envFile = Join-Path $Root '.env'

Write-Host "`nllama.cpp..." -ForegroundColor Yellow
Write-InstallLog 'llama.cpp installer step started'
Invoke-OptionalInstallScript `
    -Name 'Install-Llama.ps1' `
    -DisplayName 'llama.cpp' `
    -LogName 'llama.cpp' `
    -UnavailableMessage 'Continuing installation. llama.cpp can be configured later.' `
    -Invoke { param($scriptPath) & $scriptPath -EnvFile $envFile }

Write-Host "`nAI Backend (Foundry Local)..." -ForegroundColor Yellow
Write-InstallLog 'Foundry installer step started'
$foundryScript = Get-InstallScriptPath 'Install-Foundry.ps1'
if (Test-Path $foundryScript) {
    try {
        if ($Mode -eq 'debug') {
            & $foundryScript -DiagnosticsOnly
        } else {
            & $foundryScript -SkipIfExists -SkipServiceStart -SkipModelDownload
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Foundry installer returned exit code $LASTEXITCODE - continuing without Foundry" -ForegroundColor Yellow
                Write-InstallLog "Foundry installer returned exit code $LASTEXITCODE; continuing without Foundry" 'ERROR'
            } else {
                $foundryInstalled = $null -ne (Get-Command foundry -ErrorAction SilentlyContinue)
                if (-not $foundryInstalled) {
                    $wingetOk = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
                    if (-not $wingetOk) {
                        Write-Host '  winget not found - install manually: https://aka.ms/foundry-local' -ForegroundColor Cyan
                        Write-InstallLog 'winget not found; Foundry install skipped' 'WARNING'
                    } else {
                        $answer = Read-Host '  Install Microsoft Foundry Local now? (y/N)'
                        if ($answer -eq 'y' -or $answer -eq 'Y') {
                            & $foundryScript -SkipServiceStart -SkipModelDownload
                            if ($LASTEXITCODE -ne 0) {
                                Write-InstallLog "Foundry installer returned exit code $LASTEXITCODE after user approval; continuing" 'ERROR'
                            }
                        } else {
                            Write-InstallLog 'Foundry install skipped by user' 'WARNING'
                        }
                    }
                }
                Write-InstallLog 'Foundry installer step completed'
            }
        }
    } catch {
        Write-Host "  Foundry installer error: $_" -ForegroundColor Yellow
        Write-Host '  Continuing installation. Foundry can be installed later.' -ForegroundColor Cyan
        Write-InstallLog "Foundry installer error: $_; continuing without Foundry" 'ERROR'
    }
} else {
    Write-Host '  scripts\Install\Install-Foundry.ps1 not found - skipping' -ForegroundColor Yellow
    Write-InstallLog 'scripts\Install\Install-Foundry.ps1 not found; skipping Foundry' 'WARNING'
}

if ($SkipLMStudio) {
    Write-Host "`nLM Studio skipped (-SkipLMStudio)" -ForegroundColor Gray
    Write-InstallLog 'LM Studio skipped (-SkipLMStudio)' 'WARNING'
} else {
    Write-Host "`nLM Studio..." -ForegroundColor Yellow
    Write-InstallLog 'LM Studio installer step started'
    Invoke-OptionalInstallScript `
        -Name 'Install-LMStudio.ps1' `
        -DisplayName 'LM Studio' `
        -UnavailableMessage 'Continuing installation. LM Studio provider will be unavailable until LM Studio is installed.' `
        -Invoke { param($scriptPath) & $scriptPath -DiagnosticsOnly:($Mode -eq 'debug') }
}

if ($SkipOllama) {
    Write-Host "`nOllama skipped (-SkipOllama)" -ForegroundColor Gray
    Write-InstallLog 'Ollama skipped (-SkipOllama)' 'WARNING'
} else {
    Write-Host "`nOllama..." -ForegroundColor Yellow
    Write-InstallLog 'Ollama installer step started'
    Invoke-OptionalInstallScript `
        -Name 'Install-Ollama.ps1' `
        -DisplayName 'Ollama' `
        -UnavailableMessage 'Continuing installation. Ollama provider will be unavailable until Ollama is installed.' `
        -Invoke { param($scriptPath) & $scriptPath -SkipIfExists -DiagnosticsOnly:($Mode -eq 'debug') }
}

Write-Host "`nOpenCode..." -ForegroundColor Yellow
Write-InstallLog 'OpenCode installer step started'
Invoke-OptionalInstallScript `
    -Name 'Install-OpenCode.ps1' `
    -DisplayName 'OpenCode' `
    -UnavailableMessage 'Continuing installation. OpenCode can be installed later with: npm install -g opencode-ai' `
    -Invoke { param($scriptPath) & $scriptPath -DiagnosticsOnly:($Mode -eq 'debug') }
