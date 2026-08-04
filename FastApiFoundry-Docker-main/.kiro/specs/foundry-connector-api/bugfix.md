# Bugfix Requirements Document

## Introduction

The Foundry connector in `src/api/endpoints/foundry_models.py` uses CLI subprocess calls
and filesystem scanning in several places where the Foundry Local HTTP API should be used
instead. This makes the connector fragile: it breaks whenever Foundry changes its CLI output
format or its on-disk cache layout.

Specifically:

- `list_available_models()` calls `foundry model ls` and parses text output.
- `list_cached_models()` scans `~/.foundry/cache/models/Microsoft/` directly and
  reconstructs model IDs from directory names.
- `load_model()` spawns `subprocess.Popen(["foundry", "model", "load", model_id])`.
- `auto_load_default_model()` also spawns `subprocess.Popen(["foundry", "model", "load", ...])`.

`foundry_client.py` already exposes the correct HTTP API methods (`list_available_models()`,
`load_model()`) that call `GET /v1/models` and `POST /v1/models/{id}/load` respectively.
The fix is to route the four buggy operations through `foundry_client` instead of the CLI
or filesystem. The `download_model()` endpoint and all llama.cpp process management are
correct and must not be changed.

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `GET /api/v1/foundry/models/available` is called THEN the system executes
    `foundry model ls` via subprocess and parses its text output to build the model list,
    breaking if the CLI is absent or its output format changes.

1.2 WHEN `GET /api/v1/foundry/models/cached` is called THEN the system scans the
    `~/.foundry/cache/models/Microsoft/` directory tree directly and reconstructs model IDs
    from directory names, breaking if Foundry changes its cache directory structure.

1.3 WHEN `POST /api/v1/foundry/models/load` is called with a valid `model_id` THEN the
    system spawns `subprocess.Popen(["foundry", "model", "load", model_id])` and returns
    a PID, bypassing the Foundry HTTP API and losing structured error reporting.

1.4 WHEN `POST /api/v1/foundry/models/auto-load-default` is called THEN the system spawns
    `subprocess.Popen(["foundry", "model", "load", model_id])`, bypassing the Foundry HTTP
    API and losing structured error reporting.

### Expected Behavior (Correct)

2.1 WHEN `GET /api/v1/foundry/models/available` is called THEN the system SHALL retrieve
    the model list by calling `foundry_client.list_available_models()` (which uses
    `GET /v1/models`), falling back to the hardcoded `AVAILABLE_MODELS` list only when
    the Foundry service is unreachable.

2.2 WHEN `GET /api/v1/foundry/models/cached` is called THEN the system SHALL retrieve
    the model list by calling `foundry_client.list_available_models()` (which uses
    `GET /v1/models` and returns all models known to Foundry, not just loaded ones),
    falling back to filesystem scanning only when the Foundry service is unreachable.

2.3 WHEN `POST /api/v1/foundry/models/load` is called with a valid `model_id` THEN the
    system SHALL load the model by calling `foundry_client.load_model(model_id)` (which
    uses `POST /v1/models/{id}/load`) and SHALL return a structured success/error response
    without spawning a subprocess.

2.4 WHEN `POST /api/v1/foundry/models/auto-load-default` is called THEN the system SHALL
    load the default model by calling `foundry_client.load_model(model_id)` (which uses
    `POST /v1/models/{id}/load`) and SHALL return a structured success/error response
    without spawning a subprocess.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `POST /api/v1/foundry/models/download` is called with a valid `model_id` THEN
    the system SHALL CONTINUE TO spawn `foundry model download` via subprocess, as no
    HTTP API alternative exists for this operation.

3.2 WHEN any Foundry endpoint is called and the Foundry service is unreachable THEN the
    system SHALL CONTINUE TO return a graceful error response (success=False with an error
    message) without raising an unhandled exception.

3.3 WHEN `GET /api/v1/foundry/models/available` is called and the Foundry service is
    unreachable THEN the system SHALL CONTINUE TO fall back to the hardcoded
    `AVAILABLE_MODELS` list so the UI always has something to display.

3.4 WHEN `GET /api/v1/foundry/models/loaded` is called THEN the system SHALL CONTINUE TO
    return only models currently loaded in the Foundry service (in-memory), unchanged.

3.5 WHEN `POST /api/v1/foundry/models/unload` is called THEN the system SHALL CONTINUE TO
    unload the model via `DELETE /v1/models/{id}` with CLI fallback, unchanged.

3.6 WHEN any llama.cpp endpoint is called THEN the system SHALL CONTINUE TO manage the
    llama.cpp process via subprocess, as llama.cpp has no management HTTP API.

3.7 WHEN the response shape of any existing endpoint is observed by a caller THEN the
    system SHALL CONTINUE TO return the same JSON field names and structure as before the
    fix (same endpoint URLs, same response shapes).

---

## Bug Condition Pseudocode

**Bug Condition Function** — identifies the four operations that use CLI/filesystem
instead of the Foundry HTTP API:

```pascal
FUNCTION isBugCondition(operation)
  INPUT: operation — one of the Foundry endpoint handler calls
  OUTPUT: boolean

  RETURN operation IN {
    list_available_models_via_cli,       // foundry model ls subprocess
    list_cached_models_via_filesystem,   // ~/.foundry/cache scan
    load_model_via_subprocess,           // Popen(["foundry", "model", "load", ...])
    auto_load_default_via_subprocess     // Popen(["foundry", "model", "load", ...])
  }
END FUNCTION
```

**Property: Fix Checking**

```pascal
FOR ALL operation WHERE isBugCondition(operation) DO
  result ← execute_fixed_operation(operation)
  ASSERT result uses foundry_client HTTP API
  AND result does NOT spawn a subprocess for model listing or loading
  AND result contains structured success/error fields
END FOR
```

**Property: Preservation Checking**

```pascal
FOR ALL operation WHERE NOT isBugCondition(operation) DO
  ASSERT F(operation) = F'(operation)
  // download_model, unload_model, list_loaded_models, all llama.cpp ops — unchanged
END FOR
```
