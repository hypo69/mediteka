# Update-Project

> FastAPI Foundry - Update Checker

## Description

Checks GitHub for a newer release tag and offers to update.
Compares the current local tag (VERSION file or git describe) against
the latest tag on the remote. If a newer tag exists, pulls it and
re-runs install.ps1 to refresh dependencies.
Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Silent
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Force
File: scripts/Update-Project.ps1
Project: Ai Assistant (Docker)
Version: 0.6.0
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Silent
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Force
File: scripts/Update-Project.ps1
Project: Ai Assistant (Docker)
Version: 0.6.0
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`scripts/Update-Project.ps1`

