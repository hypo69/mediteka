# List-Models

> Foundry Model List

## Description

Retrieves the list of Foundry models.
In 'available' mode: calls 'foundry model list' to show all downloadable models.
In 'loaded' mode: calls 'foundry service list'; falls back to the HTTP API
at localhost:50477 if the CLI command fails.
Outputs only clean model ID lines, stripping headers and status messages.
Examples:
.\list-models.ps1                    # list all available models
.\list-models.ps1 -Type loaded       # list models currently loaded in memory
File: scripts/list-models.ps1
Project: Ai Assistant (Docker)
Version: 0.4.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
.\list-models.ps1                    # list all available models
.\list-models.ps1 -Type loaded       # list models currently loaded in memory
File: scripts/list-models.ps1
Project: Ai Assistant (Docker)
Version: 0.4.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`scripts/List-Models.ps1`

