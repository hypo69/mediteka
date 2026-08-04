# doc

> Start Documentation Server and Open Browser

## Description

Reads docs_server.port from config.json, generates PowerShell docs
via scripts\Create-Doc\Generate-PsDocs.ps1, rebuilds the MkDocs site,
starts the server and opens the documentation in the default browser.
Examples:
powershell -ExecutionPolicy Bypass -File .\doc.ps1
File: doc.ps1
Project: AI Assistant (ai_assist)
Version: 0.8.0
Changes in 0.8.0:
- Added Generate-FullReference.py step (telegram, js, mcp_servers)
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\doc.ps1
File: doc.ps1
Project: AI Assistant (ai_assist)
Version: 0.8.0
Changes in 0.8.0:
- Added Generate-FullReference.py step (telegram, js, mcp_servers)
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`doc.ps1`

