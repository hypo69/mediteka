# PowerShell Code Style Guide

**Project:** FastApiFoundry (Docker)
**Version:** 0.4.1
**Based on:** `run-sandbox.ps1`

---

## 1. File Header

Every `.ps1` file starts with this block:

```powershell
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <Short descriptive name of what the script does>
# =============================================================================
# Description:
#   <What the script does, what it checks, what it produces>
#   <Multi-line is fine>
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\script.ps1
#   powershell -ExecutionPolicy Bypass -File .\script.ps1 -SomeFlag
#
# File: script.ps1
# Project: Ai Assistant (Docker)
# Version: 0.4.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

---

## 2. Parameters Block

Immediately after the header, before any code:

```powershell
param (
    [switch]$Silent,
    [string]$Mode = 'default'
)
```

---

## 3. Error Handling

Set at the top of the script body, after `param`:

```powershell
$ErrorActionPreference = 'Stop'
```

---

## 4. Constants / Script-level Variables

Use `UPPER_SNAKE_CASE`. Add a short inline comment explaining the purpose:

```powershell
# Path to the project on the host machine
$PROJECT_PATH = 'D:\repos\project'

# Temporary config file path
$CONFIG_FILE = Join-Path $env:TEMP 'config.wsb'
```

---

## 5. Function Structure

### 5.1 Naming

Use `Verb-Noun` (approved PowerShell verbs: `Get`, `Set`, `New`, `Start`, `Stop`, `Test`, `Enable`, `Ensure`, `Remove`, `Invoke`):

```powershell
function Test-Virtualization { ... }
function Enable-Feature { ... }
function New-WSBConfig { ... }
function Start-Sandbox { ... }
```

### 5.2 Comment-based Help (docstring)

Every function has a `<# ... #>` block with at minimum `.SYNOPSIS`. Add `.PARAMETER`, `.OUTPUTS`, `.NOTES` when relevant:

```powershell
function Test-Virtualization {
    <#
    .SYNOPSIS
        Checks whether hardware virtualization is enabled in firmware.
    .OUTPUTS
        bool — True if virtualization is enabled, False otherwise.
    #>
    ...
}

function Enable-Feature {
    <#
    .SYNOPSIS
        Enables a Windows optional feature if not already enabled.
    .PARAMETER name
        Name of the Windows optional feature.
    .OUTPUTS
        bool — True if the feature was just enabled, False if already active.
    #>
    param ([string]$name)
    ...
}

function Ensure-Sandbox {
    <#
    .SYNOPSIS
        Verifies and enables Windows Sandbox and its required dependencies.
    .OUTPUTS
        bool — True if a system reboot is required, False otherwise.
    .NOTES
        Throws if hardware virtualization is disabled in BIOS.
    #>
    ...
}
```

### 5.3 Early Return Pattern

Prefer early return / guard clauses over deep nesting:

```powershell
if (-not (Test-Virtualization)) {
    throw 'Виртуализация отключена в BIOS'
}
```

### 5.4 Return Values

Functions return `$true`/`$false` for boolean state, objects for data. Never mix output and return value — suppress side-effect output with `| Out-Null`:

```powershell
bcdedit /set hypervisorlaunchtype Auto | Out-Null
return $rebootRequired
```

---

## 6. Inline Comments

- Written in **English** (code comments) or **Russian** (user-facing messages)
- Placed **above** the line they describe
- Explain *why*, not *what*:

```powershell
# Set hypervisor to launch automatically on boot
bcdedit /set hypervisorlaunchtype Auto | Out-Null
```

---

## 7. User-facing Output

Use `Write-Host` with emoji for status messages. Never use `Write-Output` for UI messages:

```powershell
Write-Host '🔍 Проверка окружения...'
Write-Host '⚙️ Генерация конфигурации...'
Write-Host '🚀 Запуск...'
Write-Host '⚠️ Требуется перезагрузка.'
Write-Host '➡️ Включается feature ...'
```

---

## 8. Here-String for Multi-line Content

Use `@" ... "@` for generating file content. Variables expand automatically:

```powershell
$content = @"
<Configuration>
  <Value>$VARIABLE</Value>
</Configuration>
"@

$content | Set-Content -Path $FILE -Encoding UTF8
```

---

## 9. Main Block

Mark the entry point with a `# --- main ---` separator. Keep it flat — call functions, no logic inline:

```powershell
# --- main ---

Write-Host '🔍 Проверка окружения...'

$needsReboot = Ensure-Sandbox

if ($needsReboot) {
    Write-Host '⚠️ Требуется перезагрузка.'
    Restart-Computer
    return
}

New-WSBConfig -silent:$Silent
Start-Sandbox
```

---

## 10. Quick Reference

| Rule | Example |
|---|---|
| File header | `# -*- coding: utf-8 -*-` + block |
| Error mode | `$ErrorActionPreference = 'Stop'` |
| Constants | `$UPPER_SNAKE_CASE = 'value'` |
| Function names | `Verb-Noun` |
| Docstring | `<# .SYNOPSIS ... #>` inside function |
| Suppress output | `command | Out-Null` |
| File write | `Set-Content -Encoding UTF8` |
| Main separator | `# --- main ---` |
| UI output | `Write-Host '🚀 Message'` |
| Guard clause | `if (-not $cond) { throw / return }` |
