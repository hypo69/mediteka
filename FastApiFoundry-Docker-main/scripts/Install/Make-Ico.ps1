# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Конвертер PNG в ICO
# =============================================================================
# Description:
#   Конвертирует assets/icons/icon16.png + icon48.png + icon128.png
#   в единый файл icon.ico в корне проекта.
#   Использует .NET System.Drawing — внешние инструменты не нужны.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Make-Ico.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\Install\Make-Ico.ps1 -ProjectRoot "D:\project"
#
# File: scripts\Install\Make-Ico.ps1
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Обновлён заголовок и проект
#   - Комментарии переведены на русский
# Author: hypo69
# Copyright: © 2024 - 2026 hypo69
# License: MIT
# =============================================================================

param (
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'

# --- paths ---

$ICONS_DIR = Join-Path $ProjectRoot 'assets\icons'
$OUT_ICO   = Join-Path $ProjectRoot 'icon.ico'

$PNG_SIZES = @(16, 48, 128)

# --- functions ---

function ConvertTo-Ico {
    <#
    .SYNOPSIS
        Объединяет несколько PNG-файлов в один многоразмерный .ico-файл.
    .DESCRIPTION
        Args:
            $PngPaths (string[]) — упорядоченный список PNG-файлов (от маленького к большому).
            $OutputPath (string) — путь к выходному .ico-файлу.

        Returns:
            void
    .EXAMPLE
        ConvertTo-Ico -PngPaths @('icon16.png','icon48.png','icon128.png') -OutputPath 'icon.ico'
        # Создан icon.ico с тремя размерами
    #>
    param (
        [string[]]$PngPaths,
        [string]$OutputPath
    )

    Add-Type -AssemblyName System.Drawing

    # ICO file format:
    #   6-byte header + N * 16-byte directory entries + image data blobs
    $header    = [System.Collections.Generic.List[byte]]::new()
    $directory = [System.Collections.Generic.List[byte]]::new()
    $imageData = [System.Collections.Generic.List[byte]]::new()

    # ICO header: reserved(2) + type=1(2) + count(2)
    $count = $PngPaths.Count
    $header.AddRange([byte[]](0,0, 1,0, $count,0))

    $dataOffset = 6 + $count * 16   # header + all directory entries

    foreach ($pngPath in $PngPaths) {
        $bmp   = [System.Drawing.Bitmap]::new($pngPath)
        $w     = if ($bmp.Width  -ge 256) { 0 } else { [byte]$bmp.Width  }
        $h     = if ($bmp.Height -ge 256) { 0 } else { [byte]$bmp.Height }

        # Re-encode as PNG into memory stream (ICO supports embedded PNG for sizes >= 32)
        $ms = [System.IO.MemoryStream]::new()
        $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()
        $imgBytes = $ms.ToArray()
        $ms.Dispose()

        $imgSize = $imgBytes.Length

        # Directory entry: width(1) height(1) colorCount(1) reserved(1)
        #                  planes(2) bitCount(2) bytesInRes(4) imageOffset(4)
        $directory.Add($w)
        $directory.Add($h)
        $directory.Add(0)    # colorCount (0 = no palette)
        $directory.Add(0)    # reserved
        $directory.AddRange([byte[]](1,0))   # planes = 1
        $directory.AddRange([byte[]](32,0))  # bitCount = 32
        $directory.AddRange([System.BitConverter]::GetBytes([uint32]$imgSize))
        $directory.AddRange([System.BitConverter]::GetBytes([uint32]$dataOffset))

        $imageData.AddRange($imgBytes)
        $dataOffset += $imgSize
    }

    $allBytes = $header.ToArray() + $directory.ToArray() + $imageData.ToArray()
    [System.IO.File]::WriteAllBytes($OutputPath, $allBytes)
}

# --- main ---

Write-Host '🔍 Checking source PNGs...'

$pngPaths = @()
foreach ($size in $PNG_SIZES) {
    $p = Join-Path $ICONS_DIR "icon${size}.png"
    if (-not (Test-Path $p)) {
        Write-Host "  ⚠️  Missing: $p — skipping size $size" -ForegroundColor Yellow
        continue
    }
    $pngPaths += $p
    Write-Host "  ✅ Found: icon${size}.png"
}

if ($pngPaths.Count -eq 0) {
    Write-Host '❌ No PNG icons found in assets\icons\' -ForegroundColor Red
    exit 1
}

Write-Host "⚙️  Building $OUT_ICO from $($pngPaths.Count) PNG(s)..."
ConvertTo-Ico -PngPaths $pngPaths -OutputPath $OUT_ICO

Write-Host "✅ Created: $OUT_ICO" -ForegroundColor Green
