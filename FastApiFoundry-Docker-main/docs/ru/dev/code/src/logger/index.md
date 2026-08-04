# Logging subsystem

The application logging subsystem records only warnings and errors to disk.
Successful HTTP requests such as `200 OK` are intentionally excluded from the
file logs.

## Storage

Runtime logs are stored in the current user's temp directory:

```text
%TEMP%/aissistant
```

The default file pattern is:

```text
aiassistant-YYYY-MM-DD-NNN.log
```

Example:

```text
C:\Users\user\AppData\Local\Temp\aissistant\aiassistant-2026-05-07-001.log
```

## Rotation

Rotation has two limits:

- one logical export per day, by date in the filename
- a maximum number of lines per file

When the current file reaches `max_lines_per_file`, the logger opens the next
file for the same day, for example `aiassistant-2026-05-07-002.log`.

Old daily log files are removed according to `retention_days`.

## Configuration

Settings are read from `config.json` under `logging`:

```json
{
  "logging": {
    "level": "WARNING",
    "log_dir": "",
    "max_lines_per_file": 5000,
    "retention_days": 7
  }
}
```

If `log_dir` is empty, `%TEMP%/aissistant` is used.

`AIASSISTANT_LOG_DIR` can override the default directory. `LOG_LEVEL` can
override the console/root logging level.

## What Is Logged

The file handler records `WARNING`, `ERROR`, and `CRITICAL` records from:

- FastAPI middleware for `4xx` and `5xx` responses
- unhandled FastAPI exceptions with stack traces
- `uvicorn.error` warnings and errors
- model generation failures
- chat and streaming chat exceptions
- RAG warnings that affect generation or chat behavior

The file handler does not write normal success events or successful `200`
requests.

## API

The log viewer uses these endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/logs/files` | List files in the configured log directory |
| `GET` | `/v1/logs` | Read a selected file with filtering and pagination |
| `GET` | `/v1/logs/settings` | Read line-limit and retention settings |
| `POST` | `/v1/logs/settings` | Save line-limit and retention settings |
| `GET` | `/v1/logs/health` | Count warnings/errors for health badges |
| `POST` | `/v1/logs/clear` | Truncate a selected log file |
| `GET` | `/v1/logs/download` | Download a selected log file |

