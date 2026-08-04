# Invoke-QaInstall

> QA - Clean Reinstall

## Description

Full QA reinstall pipeline:
1. Stop all services          (calls tests\qa-start.ps1)
2. Remove venv/               (clean pip state)
3. Remove bin\llama-*\        (re-extracted from zip)
4. Run install.ps1 -Force     (clean install)
5. Optional: run smoke tests
Produces a deterministic environment identical to a first-time install.
Use in CI pipelines or before regression test runs.
Examples:
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipRag
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipLMStudio
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipSmoke
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -KeepFoundry
File: tests\qa-install.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipRag
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipLMStudio
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -SkipSmoke
powershell -ExecutionPolicy Bypass -File .\tests\qa-install.ps1 -KeepFoundry
File: tests\qa-install.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`tests/Invoke-QaInstall.ps1`

