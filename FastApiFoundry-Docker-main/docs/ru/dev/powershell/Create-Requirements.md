# Create-Requirements

> Create requirements.txt

## Description

Generates requirements.txt using one of two strategies:
freeze   — full pip freeze snapshot of the active venv
pipreqs  — only packages actually imported in source code (auto-installs pipreqs)
Examples:
.\create_requirements.ps1 -Mode pipreqs
.\create_requirements.ps1 -Mode freeze -ProjectPath . -VenvPath venv
File: scripts/create_requirements.ps1
Project: Ai Assistant (Docker)
Version: 0.6.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
.\create_requirements.ps1 -Mode pipreqs
.\create_requirements.ps1 -Mode freeze -ProjectPath . -VenvPath venv
File: scripts/create_requirements.ps1
Project: Ai Assistant (Docker)
Version: 0.6.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`scripts/Create-Requirements.ps1`

