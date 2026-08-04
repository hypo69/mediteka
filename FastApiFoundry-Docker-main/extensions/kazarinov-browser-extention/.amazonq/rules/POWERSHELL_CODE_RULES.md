# PowerShell Code Style Guide

**Project:** AI Assistant (ai_assist)
**Version:** 0.7.1
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
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
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
    [string]$Mode = ''
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

Use `Verb-Noun` (approved PowerShell verbs: `Get`, `Set`, `New`, `Start`, `Stop`, `Test`, `Enable`, `Ensure`, `Remove`, `Invoke`, `Resolve`):

```powershell
function Test-Virtualization { ... }
function Enable-Feature { ... }
function New-WSBConfig { ... }
function Start-Sandbox { ... }
function Resolve-Mode { ... }
```

### 5.2 Comment-based Help (docstring)

Every function uses the **universal docstring template** — same structure across
Python, JavaScript, TypeScript, PowerShell, PHP.

Use `.SYNOPSIS` for Short Description, `.DESCRIPTION` for everything else,
`.EXAMPLE` for each example.

**Forbidden:** `.PARAMETER`, `.OUTPUTS`, `.NOTES` blocks.
Use `Args:` / `Returns:` / `Exceptions:` inside `.DESCRIPTION` instead.

**Template:**

```
Short Description        <- .SYNOPSIS, one line, no trailing period
Long Description         <- .DESCRIPTION opening paragraph (optional)

Args:
    $ParamName (type) — description, constraints, default if any

Returns:
    type — what is returned and when

Exceptions:
    ErrorType — when it is thrown

Examples:
    Verb-Noun -Param value
    # expected output or side-effect
```

**Rules:**
- Sections `Args:`, `Returns:`, `Exceptions:`, `Examples:` are **required** for every public function
- Omit a section only when genuinely not applicable (no params, no return value, no exceptions)
- Minimum **one example** per public function
- Section order must not change
- `Params:` is **forbidden** — only `Args:`

```powershell
function Test-Virtualization {
    <#
    .SYNOPSIS
        Checks whether hardware virtualization is enabled in firmware.
    .DESCRIPTION
        Returns:
            bool — True if VT-x/AMD-V is enabled in BIOS, False otherwise.
    .EXAMPLE
        Test-Virtualization
        # Returns $true on a machine with VT-x enabled in BIOS
    #>
    ...
}

function Enable-Feature {
    <#
    .SYNOPSIS
        Enables a Windows optional feature if not already active.
    .DESCRIPTION
        Args:
            $Name (string) — name of the Windows optional feature.

        Returns:
            bool — True if the feature was just enabled, False if already active.
    .EXAMPLE
        Enable-Feature -Name 'Containers-DisposableClientVM'
        # Returns $true if the feature was newly enabled
    #>
    param ([string]$Name)
    ...
}

function Ensure-Sandbox {
    <#
    .SYNOPSIS
        Verifies and enables Windows Sandbox and its required dependencies.
    .DESCRIPTION
        Returns:
            bool — True if a system reboot is required, False otherwise.

        Exceptions:
            RuntimeException — thrown if hardware virtualization is disabled in BIOS.
    .EXAMPLE
        $reboot = Ensure-Sandbox
        if ($reboot) { Restart-Computer }
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

## 10. Mode Handling — Resolve-Mode Pattern

Any script that accepts a `-Mode` parameter **must** normalise the value
immediately after `param()`, before any mode-dependent logic.

This prevents failures on `qa+debug`, `debug+qa`, `QA`, `DEBUG+QA`, etc.

```powershell
function Resolve-Mode {
    <#
    .SYNOPSIS
        Normalises a raw mode string to one of the four canonical values.
    .DESCRIPTION
        Canonical values: prod | qa | debug | qa+debug

        Normalisation rules (case-insensitive):
          debug+qa  ->  qa+debug
          qa+debug  ->  qa+debug
          qa        ->  qa
          debug     ->  debug
          prod      ->  prod
          <empty>   ->  prod  (safe default)

        Args:
            $Raw (string) — raw value from -Mode param or MODE file.

        Returns:
            string — one of: prod | qa | debug | qa+debug

        Exceptions:
            RuntimeException — thrown for unrecognised mode strings.

    .EXAMPLE
        Resolve-Mode 'debug+qa'
        # Returns 'qa+debug'
    .EXAMPLE
        Resolve-Mode 'QA'
        # Returns 'qa'
    .EXAMPLE
        Resolve-Mode ''
        # Returns 'prod'
    #>
    param([string]$Raw)

    $n = $Raw.ToLower().Trim()
    switch ($n) {
        ''         { return 'prod' }
        'prod'     { return 'prod' }
        'qa'       { return 'qa' }
        'debug'    { return 'debug' }
        'qa+debug' { return 'qa+debug' }
        'debug+qa' { return 'qa+debug' }
        default    { throw "Unknown mode: '$Raw'. Valid: prod | qa | debug | qa+debug | debug+qa" }
    }
}
```

Call it immediately after `param(...)`:

```powershell
$Mode = Resolve-Mode $Mode
```

---

## 11. Reading Mode from the MODE File

When `-Mode` is not passed explicitly, fall back to the `MODE` file in the project root.

```powershell
function Get-ModeFromFile {
    <#
    .SYNOPSIS
        Reads the active mode from the MODE file in the project root.
    .DESCRIPTION
        Looks for a line matching `mode = <value>` (case-insensitive, whitespace-tolerant).

        Args:
            $ProjectRoot (string) — path to the directory containing the MODE file.

        Returns:
            string — raw mode value, or empty string if file is absent or has no match.

    .EXAMPLE
        $raw  = Get-ModeFromFile -ProjectRoot $PSScriptRoot
        $Mode = Resolve-Mode $raw
        # $Mode is now one of: prod | qa | debug | qa+debug
    .EXAMPLE
        Get-ModeFromFile -ProjectRoot 'D:\repos\FastApiFoundry-Docker'
        # Returns 'qa+debug' when MODE file contains: mode = qa+debug
    #>
    param([string]$ProjectRoot)

    $modeFile = Join-Path $ProjectRoot 'MODE'
    if (-not (Test-Path $modeFile)) { return '' }

    $line = Get-Content $modeFile |
            Where-Object { $_ -match '^\s*mode\s*=' } |
            Select-Object -First 1

    if (-not $line) { return '' }
    return ($line -split '=', 2)[1].Trim()
}
```

Usage pattern in any script that supports the MODE file:

```powershell
param(
    [string]$Mode = ''
)

# Fall back to MODE file when -Mode not supplied on the command line
if (-not $Mode) { $Mode = Get-ModeFromFile -ProjectRoot $PSScriptRoot }
$Mode = Resolve-Mode $Mode
```

---

## 12. Quick Reference

| Rule | Example |
|---|---|
| File header | `# -*- coding: utf-8 -*-` + block |
| Error mode | `$ErrorActionPreference = 'Stop'` |
| Constants | `$UPPER_SNAKE_CASE = 'value'` |
| Function names | `Verb-Noun` |
| Docstring template | `Short / Args: / Returns: / Exceptions: / Examples:` |
| Docstring keywords | `.SYNOPSIS` + `.DESCRIPTION` + `.EXAMPLE` — never `.PARAMETER` / `.OUTPUTS` / `.NOTES` |
| Suppress output | `command \| Out-Null` |
| File write | `Set-Content -Encoding UTF8` |
| Main separator | `# --- main ---` |
| UI output | `Write-Host '🚀 Message'` |
| Guard clause | `if (-not $cond) { throw / return }` |
| Mode normalisation | `$Mode = Resolve-Mode $Mode` immediately after `param()` |
| MODE file fallback | `if (-not $Mode) { $Mode = Get-ModeFromFile $PSScriptRoot }` |
