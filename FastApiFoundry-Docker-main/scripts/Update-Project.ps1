# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: FastAPI Foundry - Update Checker
# =============================================================================
# Description:
#   Checks GitHub for a newer release tag and offers to update.
#   Compares the current local tag (VERSION file or git describe) against
#   the latest tag on the remote. If a newer tag exists, pulls it and
#   re-runs install.ps1 to refresh dependencies.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Silent
#   powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Force
#
# File: scripts/Update-Project.ps1
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    # Suppress interactive prompts — auto-accept update
    [switch]$Silent,
    # Force update even if already on latest tag
    [switch]$Force
)

$ErrorActionPreference = 'Continue'
$Root = Split-Path $PSScriptRoot -Parent

# --- helpers ---

function Get-LocalVersion {
    <#
    .SYNOPSIS
        Returns the current local version string.
    .DESCRIPTION
        Reads VERSION file first; falls back to `git describe --tags`.
    .OUTPUTS
        [string] Version tag, e.g. "v0.6.0", or $null.
    #>
    $versionFile = Join-Path $Root 'VERSION'
    if (Test-Path $versionFile) {
        $v = (Get-Content $versionFile -Raw).Trim()
        if ($v) { return $v }
    }

    try {
        $v = & git -C $Root describe --tags --abbrev=0 2>$null
        if ($LASTEXITCODE -eq 0 -and $v) { return $v.Trim() }
    } catch { }

    return $null
}

function Get-RemoteLatestTag {
    <#
    .SYNOPSIS
        Fetches tags from origin and returns the latest one by version sort.
    .OUTPUTS
        [string] Latest remote tag, or $null on failure.
    #>
    try {
        # Fetch tags without pulling commits
        & git -C $Root fetch --tags --quiet 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }

        $tag = & git -C $Root tag --sort=-version:refname 2>$null | Select-Object -First 1
        if ($tag) { return $tag.Trim() }
    } catch { }

    return $null
}

function Compare-Versions {
    <#
    .SYNOPSIS
        Returns $true if $Remote is strictly newer than $Local.
    .PARAMETER Local
        Local version string (e.g. "v0.5.5").
    .PARAMETER Remote
        Remote version string (e.g. "v0.6.0").
    .OUTPUTS
        [bool]
    #>
    param([string]$Local, [string]$Remote)

    # Strip leading 'v'
    $l = $Local  -replace '^v', ''
    $r = $Remote -replace '^v', ''

    try {
        return ([version]$r) -gt ([version]$l)
    } catch {
        # Fallback: simple string compare
        return $r -ne $l
    }
}

function Invoke-Update {
    <#
    .SYNOPSIS
        Checks out the latest tag and re-runs install.ps1.
    .PARAMETER Tag
        The remote tag to check out.
    #>
    param([string]$Tag)

    Write-Host "📥 Переключение на $Tag ..." -ForegroundColor Yellow

    & git -C $Root checkout $Tag --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host '❌ git checkout завершился с ошибкой.' -ForegroundColor Red
        return $false
    }

    # Write new version to VERSION file so offline runs know the tag
    $Tag | Set-Content (Join-Path $Root 'VERSION') -Encoding UTF8
    Write-Host "✅ Версия обновлена до $Tag" -ForegroundColor Green

    # Re-run installer to pick up any new dependencies
    $installer = Join-Path $Root 'install.ps1'
    if (Test-Path $installer) {
        Write-Host '📦 Обновление зависимостей (install.ps1)...' -ForegroundColor Yellow
        try {
            & $installer
        } catch {
            Write-Host "⚠️ install.ps1 завершился с ошибкой: $_" -ForegroundColor Yellow
        }
    }

    return $true
}

# --- main ---

Write-Host '🔄 Проверка обновлений...' -ForegroundColor Cyan

# Ensure we are inside a git repo
if (-not (Test-Path (Join-Path $Root '.git'))) {
    Write-Host '⚠️ Не git-репозиторий — проверка обновлений пропущена.' -ForegroundColor Yellow
    exit 0
}

# Ensure git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host '⚠️ git не найден в PATH — проверка обновлений пропущена.' -ForegroundColor Yellow
    exit 0
}

$localTag  = Get-LocalVersion
$remoteTag = Get-RemoteLatestTag

if (-not $remoteTag) {
    Write-Host '⚠️ Не удалось получить теги с remote — пропуск.' -ForegroundColor Yellow
    exit 0
}

Write-Host "   Текущая версия : $( if ($localTag) { $localTag } else { '(неизвестна)' } )" -ForegroundColor Gray
Write-Host "   Последний тег  : $remoteTag" -ForegroundColor Gray

$needsUpdate = $Force -or (-not $localTag) -or (Compare-Versions -Local $localTag -Remote $remoteTag)

if (-not $needsUpdate) {
    Write-Host "✅ Версия актуальна ($remoteTag)" -ForegroundColor Green
    exit 0
}

Write-Host ''
Write-Host "🆕 Доступно обновление: $localTag → $remoteTag" -ForegroundColor Cyan

if ($Silent) {
    $answer = 'y'
} else {
    $answer = Read-Host '   Обновить сейчас? [Y/n]'
}

if ($answer -match '^[Nn]') {
    Write-Host '⏭️  Обновление пропущено.' -ForegroundColor Yellow
    exit 0
}

$ok = Invoke-Update -Tag $remoteTag
if ($ok) {
    Write-Host '✅ Обновление завершено. Перезапустите start.ps1.' -ForegroundColor Green
} else {
    Write-Host '❌ Обновление не удалось.' -ForegroundColor Red
}
