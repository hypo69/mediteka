# ReinstallFoundry

> Foundry Local - Reinstall (CI/QA Tool)

## Description

Fully resets and reinstalls Microsoft Foundry Local.
Used in CI pipelines and QA validation runs.
Modes:
- clean uninstall via winget
- reinstall via winget (silent, non-interactive)
- readiness verification (polls /v1/models on auto-detected port)
Examples:
.\scripts\Install\ReinstallFoundry.ps1
.\scripts\Install\ReinstallFoundry.ps1 -TimeoutSec 120
.\scripts\Install\ReinstallFoundry.ps1 -TimeoutSec 30 -Verbose
Exit codes:
0 = success (API ready)
1 = install failed
2 = service not ready within timeout
File: scripts\Install\ReinstallFoundry.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Restored missing code blocks (Uninstall-Foundry, Install-Foundry, Wait-Ready)
- Added full hypo69 header
- Aligned docstrings with project standard (Args/Returns/Exceptions/Examples)
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
.\scripts\Install\ReinstallFoundry.ps1
.\scripts\Install\ReinstallFoundry.ps1 -TimeoutSec 120
.\scripts\Install\ReinstallFoundry.ps1 -TimeoutSec 30 -Verbose
Exit codes:
0 = success (API ready)
1 = install failed
2 = service not ready within timeout
File: scripts\Install\ReinstallFoundry.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Restored missing code blocks (Uninstall-Foundry, Install-Foundry, Wait-Ready)
- Added full hypo69 header
- Aligned docstrings with project standard (Args/Returns/Exceptions/Examples)
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`scripts/Install/ReinstallFoundry.ps1`

