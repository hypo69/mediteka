# Generate-PsDocs

> Generate PowerShell Docs

## Description

Generates Markdown documentation from PowerShell comment-based help
for ALL .ps1 files in the project (root, scripts/, scripts/Install/, mcp/,
check_engine/, src/, tests/, microsoft_sandbox_operations/).
Excludes archived files (~), venv/ and site/.
Used by GitHub Actions deploy-docs.yml workflow and locally.
Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Create-Doc\Generate-PsDocs.ps1
File: Generate-PsDocs.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Scan all project directories, not only mcp/src/servers and scripts/
- Group index page by directory
- Exclude ~, venv/, site/ from scan
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Create-Doc\Generate-PsDocs.ps1
File: Generate-PsDocs.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Scan all project directories, not only mcp/src/servers and scripts/
- Group index page by directory
- Exclude ~, venv/, site/ from scan
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`scripts/Create-Doc/Generate-PsDocs.ps1`

