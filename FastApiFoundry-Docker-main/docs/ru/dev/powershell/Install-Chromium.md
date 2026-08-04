# Install-Chromium

> Chromium for Testing Setup

## Description

Downloads Chrome for Testing (stable) via @puppeteer/browsers into bin/chromium/.
After install, writes the chromium executable path to config.json under
browser.chromium_path so the web UI launcher can use it.
Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Chromium.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Chromium.ps1 -Channel canary
File: scripts/Install/Install-Chromium.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Initial implementation
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Chromium.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Chromium.ps1 -Channel canary
File: scripts/Install/Install-Chromium.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Initial implementation
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`scripts/Install/Install-Chromium.ps1`

