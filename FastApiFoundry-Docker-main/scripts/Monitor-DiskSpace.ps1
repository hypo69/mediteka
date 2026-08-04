# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Мониторинг свободного места на диске
# =============================================================================
# Описание:
#   Проверяет свободное место на диске C:. Если объем меньше порога,
#   отправляет уведомление в Telegram.
#
# File: scripts/Monitor-DiskSpace.ps1
# Project: Ai Assistant
# Version: 1.0.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

[CmdletBinding()]
param(
    [int]$ThresholdGB = 5,
    [string]$DriveLetter = "C",
    [int]$RetentionDays = 60
)

$Drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$($DriveLetter):'"
if (-not $Drive) {
    Write-Error "❌ Диск $($DriveLetter): не найден."
    exit 1
}

$FreeGB = [Math]::Round($Drive.FreeSpace / 1GB, 2)
$TotalGB = [Math]::Round($Drive.Size / 1GB, 2)
$PercentFree = [Math]::Round(($Drive.FreeSpace / $Drive.Size) * 100, 1)

Write-Host "📊 Диск $($DriveLetter): Свободно $FreeGB ГБ из $TotalGB ГБ ($PercentFree%)" -ForegroundColor Cyan

if ($FreeGB -lt $ThresholdGB) {
    Write-Host "⚠️ ВНИМАНИЕ: Мало места на диске!" -ForegroundColor Red
    
    # Попытка автоматической очистки
    $CleanupScript = Join-Path $PSScriptRoot "Clear-TempFiles.ps1"
    if (Test-Path $CleanupScript) {
        Write-Host "🚀 Попытка автоматической очистки временных файлов..." -ForegroundColor Cyan
        & $CleanupScript -Force -RetentionDays $RetentionDays
        
        # Повторная проверка места
        $Drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$($DriveLetter):'"
        $FreeGB = [Math]::Round($Drive.FreeSpace / 1GB, 2)
        Write-Host "📊 После очистки: $FreeGB ГБ свободно." -ForegroundColor Cyan
        if ($FreeGB -ge $ThresholdGB) { Write-Host "✅ Очистка помогла, уведомление отменено." -ForegroundColor Green; exit 0 }
    }
    
    # Интеграция с Telegram (требует TOKEN и IDS в окружении)
    if ($env:TELEGRAM_ADMIN_TOKEN -and $env:TELEGRAM_ADMIN_IDS) {
        $Hostname = [System.Net.Dns]::GetHostName()
        $Message = "🚨 *AI Assistant: Disk Space Alert*`n" +
                   "🖥 Host: $Hostname`n" +
                   "💽 Drive: $($DriveLetter):`n" +
                   "📉 Free: *$FreeGB GB* (Threshold: $ThresholdGB GB)`n" +
                   "📊 Total: $TotalGB GB ($PercentFree%)`n" +
                   "🕒 Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

        foreach ($ChatId in ($env:TELEGRAM_ADMIN_IDS -split ',')) {
            try {
                $Uri = "https://api.telegram.org/bot$($env:TELEGRAM_ADMIN_TOKEN)/sendMessage"
                $Body = @{ 
                    chat_id = $ChatId.Trim()
                    text = $Message
                    parse_mode = "Markdown"
                }
                Invoke-RestMethod -Uri $Uri -Method Post -Body $Body | Out-Null
                Write-Host "✅ Уведомление отправлено в Telegram (ID: $ChatId)" -ForegroundColor Green
            } catch {
                Write-Host "❌ Ошибка отправки в Telegram: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "💡 Настройки Telegram не найдены (пропуск уведомления)." -ForegroundColor Gray
    }
} else {
    Write-Host "✅ Достаточно свободного места." -ForegroundColor Green
}