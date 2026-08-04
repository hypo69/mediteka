# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Ротация лога очистки
# =============================================================================
# Описание:
#   Проверка размера файла logs/cleanup.log. Если размер превышает 10 МБ,
#   файл переименовывается с добавлением метки времени.
#
# File: scripts/Rotate-CleanupLog.ps1
# Project: Ai Assistant
# Version: 1.0.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "cleanup.log"

if (-not (Test-Path $LogFile)) {
    exit 0
}

$fileInfo = Get-Item $LogFile
# 10MB = 10,485,760 bytes
if ($fileInfo.Length -gt 10MB) {
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $ArchiveFile = Join-Path $LogDir "cleanup-$Timestamp.log"
    
    try {
        # Перемещаем текущий лог в архив
        Move-Item -Path $LogFile -Destination $ArchiveFile -Force
        
        # Создаем новый файл с записью о ротации
        $Message = "[$($Timestamp)] Log rotated. Previous size: $([Math]::Round($fileInfo.Length / 1MB, 2)) MB"
        $Message | Set-Content $LogFile -Encoding UTF8
        
        Write-Host "🔄 Лог cleanup.log ротирован (архив: cleanup-$Timestamp.log)" -ForegroundColor Cyan
    } catch {
        Write-Error "❌ Ошибка при ротации лога: $($_.Exception.Message)"
    }
} else {
    Write-Host "✅ Размер лога в норме ($([Math]::Round($fileInfo.Length / 1KB, 2)) KB)." -ForegroundColor Green
}

# --- Очистка архивов старше 30 дней ---
$RetentionDays = 30
$LimitDate = (Get-Date).AddDays(-$RetentionDays)
$OldLogs = Get-ChildItem -Path $LogDir -Filter "cleanup-*.log" | Where-Object { $_.LastWriteTime -lt $LimitDate }

if ($OldLogs) {
    foreach ($oldFile in $OldLogs) {
        Remove-Item $oldFile.FullName -Force
        Write-Host "🗑️ Удален старый архив лога: $($oldFile.Name) (старше $RetentionDays дней)" -ForegroundColor Gray
    }
}

exit 0