# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry - Main Installer
# =============================================================================
# Description:
#   Thin installer orchestrator. Implementation blocks live in scripts\Install.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Force
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipRag
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipTesseract
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipLMStudio
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipOllama
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode debug
#
# File: install.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.8.0
# =============================================================================

param(
    [switch]$Force,
    [switch]$SkipRag,
    [switch]$SkipTesseract,
    [switch]$SkipLMStudio,
    [switch]$SkipOllama,
    [switch]$NoGui,
    # prod | debug | qa | qa+debug  (empty = read from MODE file, default prod)
    [string]$Mode = ''
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$InstallRoot = Join-Path $Root 'scripts\Install'
$InstallLogDir = Join-Path $Root 'logs'
$InstallLogFile = Join-Path $InstallLogDir 'aiassistant-install.log'

. (Join-Path $InstallRoot 'Common.ps1')

Write-InstallLog '=== FastAPI Foundry install.ps1 started ==='
Write-InstallLog "Root: $Root"

if (-not $Mode) { $Mode = Get-ModeFromFile -ProjectRoot $Root }
$Mode = Resolve-Mode $Mode # Разрешение режима установки
Write-InstallLog "Selected Mode: $Mode"

Test-PreFlightRequirements -ProjectRoot $Root

. (Get-InstallScriptPath 'Step-PythonEnvironment.ps1') -Root $Root -Force:$Force -SkipRag:$SkipRag # Передача параметра SkipRag
. (Get-InstallScriptPath 'Step-UserInterface.ps1') -Root $Root -Python $python -NoGui:$NoGui
. (Get-InstallScriptPath 'Step-ConfigAndData.ps1') -Root $Root -Python $python -SkipRag:$SkipRag -SkipTesseract:$SkipTesseract
. (Get-InstallScriptPath 'Step-Backends.ps1') -Root $Root -Mode $Mode -SkipLMStudio:$SkipLMStudio -SkipOllama:$SkipOllama
. (Get-InstallScriptPath 'Step-Finalize.ps1') -Root $Root -Python $python -InstallLogFile $InstallLogFile
