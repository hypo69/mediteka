# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: EXE Wrapper Generator
# =============================================================================
# Description:
#   Compiles tiny C# wrapper programs into .exe files that launch PowerShell
#   scripts when double-clicked. Uses the built-in Windows C# compiler (csc.exe)
#   so no external tools are required.
#   Produces install.exe (wraps install.ps1) and launcher.exe (wraps launcher.ps1).
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\build_exes.ps1
#
# File: scripts/build_exes.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

$ErrorActionPreference = 'Stop'

# Resolve the project root: this script lives in scripts\, so go one level up
$Root = $PSScriptRoot
if ($Root -match 'scripts$') { $Root = Split-Path $Root -Parent }

# -----------------------------------------------------------------------------
# Locate csc.exe — the .NET Framework C# compiler bundled with Windows
# Try 64-bit first, then fall back to 32-bit
# -----------------------------------------------------------------------------
$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) {
    $csc = "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
}

if (-not (Test-Path $csc)) {
    Write-Host "❌ C# Compiler (csc.exe) not found. Cannot build EXE wrappers." -ForegroundColor Red
    exit 1
}

function Build-Wrapper {
    <#
    .SYNOPSIS
        Compiles a minimal C# EXE that launches a PowerShell script.
    .PARAMETER name
        Base name for the output EXE (e.g. "install" → install.exe).
    .PARAMETER scriptName
        Name of the .ps1 file to wrap (must be in the project root).
    .PARAMETER iconPath
        Optional path to a .ico file to embed as the EXE icon.
    .NOTES
        The generated EXE resolves the .ps1 path relative to its own location,
        so it works correctly regardless of the current working directory.
    #>
    param(
        [string]$name,
        [string]$scriptName,
        [string]$iconPath = ""
    )

    Write-Host "Building $name.exe..." -ForegroundColor Yellow

    # Inline C# source: finds the .ps1 next to the EXE and launches it via powershell.exe
    $source = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;

class Program {
    static void Main(string[] args) {
        string root     = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        string psScript = Path.Combine(root, "$scriptName");

        if (!File.Exists(psScript)) {
            Console.WriteLine("Error: " + psScript + " not found.");
            Console.ReadLine();
            return;
        }

        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName  = "powershell.exe";
        // -ExecutionPolicy Bypass allows running the script even if system policy is restricted
        psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + psScript + "\"";
        psi.UseShellExecute = false;

        Process.Start(psi);
    }
}
"@

    $sourcePath = Join-Path $Root "$name.cs"
    $outputPath = Join-Path $Root "$name.exe"

    # Write the C# source to a temporary file
    $source | Out-File -FilePath $sourcePath -Encoding UTF8

    # Build the compiler argument list
    $cmdArgs = @("/out:$outputPath", "/target:exe", $sourcePath)
    if ($iconPath -and (Test-Path $iconPath)) {
        # Embed the icon so the EXE shows a custom icon in Explorer
        $cmdArgs += "/win32icon:$iconPath"
    }

    # Compile — suppress compiler output with Out-Null
    & $csc $cmdArgs | Out-Null

    if (Test-Path $outputPath) {
        Write-Host "✅ Created $outputPath" -ForegroundColor Green
        # Clean up the temporary .cs source file
        Remove-Item $sourcePath
    } else {
        Write-Host "❌ Failed to create $name.exe" -ForegroundColor Red
    }
}

# --- main ---

# Build install.exe — one-click installer for end users
Build-Wrapper -name "install" -scriptName "install.ps1"

# Build launcher.exe — one-click launcher for end users
Build-Wrapper -name "launcher" -scriptName "launcher.ps1"

Write-Host "`n✅ Done! EXE files are in the project root directory." -ForegroundColor Cyan
