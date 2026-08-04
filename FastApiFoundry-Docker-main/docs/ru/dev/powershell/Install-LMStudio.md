# Install-LMStudio

> Установщик LM Studio

## Description

Проверяет наличие LM Studio CLI (`lms`) и при согласии пользователя
устанавливает LM Studio официальной командой:
irm https://lmstudio.ai/install.ps1 | iex
Скрипт защищённо проверяет наличие Invoke-RestMethod / irm и
останавливается с объяснением, если PowerShell не поддерживает этот alias.
Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -SkipIfExists
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -DiagnosticsOnly
File: scripts\Install\Install-LMStudio.ps1
Project: AI Assistant (ai_assist)
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -SkipIfExists
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -DiagnosticsOnly
File: scripts\Install\Install-LMStudio.ps1
Project: AI Assistant (ai_assist)
=============================================================================
```

## Source

`scripts/Install/Install-LMStudio.ps1`

