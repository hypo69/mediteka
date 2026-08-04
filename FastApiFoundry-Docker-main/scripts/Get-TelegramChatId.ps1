# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Get Telegram Chat ID
# =============================================================================
# Description:
#   Helper for configuring Telegram notifications. Polls the Telegram Bot API
#   to get the chat_id of the last sender.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Get-TelegramChatId.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Get-TelegramChatId.ps1 -Token "YOUR_TOKEN"
#
# File: scripts/Get-TelegramChatId.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Replaced Cyrillic UI strings with English to avoid encoding issues
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$Token
)

if (-not $Token) {
    Write-Host '--- Telegram Setup for AI Assistant ---' -ForegroundColor Cyan
    $Token = Read-Host 'Enter your Telegram Bot Token (from @BotFather)'
}

if (-not $Token) { Write-Error 'Token cannot be empty.'; exit 1 }

Write-Host "`n1. Open Telegram and find your bot." -ForegroundColor Yellow
Write-Host '2. Send the bot any text message (e.g. /start).' -ForegroundColor Yellow
Write-Host '3. Waiting for a message...' -ForegroundColor Cyan

$baseUrl = "https://api.telegram.org/bot$Token/getUpdates"
$chatId  = $null
$attempt = 0

while ($null -eq $chatId -and $attempt -lt 30) {
    try {
        $response = Invoke-RestMethod -Uri $baseUrl -Method Get -ErrorAction Stop
        if ($response.result.Count -gt 0) {
            $lastUpdate = $response.result[-1]
            $chatId     = $lastUpdate.message.chat.id
            $userName   = $lastUpdate.message.from.first_name
        }
    } catch {
        Write-Host "Warning: API error: $($_.Exception.Message)" -ForegroundColor Red
        break
    }

    if ($null -eq $chatId) {
        $attempt++
        Write-Host '.' -NoNewline -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if ($chatId) {
    Write-Host "`n`n✅ Success!" -ForegroundColor Green
    Write-Host "Chat ID  : $chatId" -ForegroundColor White
    Write-Host "Sender   : $userName" -ForegroundColor Gray

    $envFile = Join-Path $PSScriptRoot '..\.env'
    if (Test-Path $envFile) {
        $choice = Read-Host "`nSave to .env? (y/N)"
        if ($choice -eq 'y' -or $choice -eq 'Y') {
            $content = Get-Content $envFile
            $content = $content -replace '^TELEGRAM_BOT_TOKEN=.*', "TELEGRAM_BOT_TOKEN=$Token"
            $content = $content -replace '^TELEGRAM_CHAT_ID=.*',   "TELEGRAM_CHAT_ID=$chatId"
            $content | Set-Content $envFile -Encoding UTF8
            Write-Host '✅ .env updated.' -ForegroundColor Green
        }
    } else {
        Write-Host "`nCopy these values to your .env file:" -ForegroundColor Cyan
        Write-Host "TELEGRAM_BOT_TOKEN=$Token"
        Write-Host "TELEGRAM_CHAT_ID=$chatId"
    }
} else {
    Write-Host "`n`n❌ Timeout or error." -ForegroundColor Red
    Write-Host 'Make sure you sent a message to the bot.' -ForegroundColor Yellow
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
