# OpenCode 1.15.3 integration

Интеграция добавляет управляемый интерфейс к `opencode serve` и HTTP API OpenCode.
`config.json` остаётся single source of truth: перед запуском FastAPI Foundry
генерирует проектный `opencode.json`, в котором OpenCode получает
OpenAI-compatible provider на `custom.base_url` (обычно `http://localhost:9696/v1`).

Официальная модель OpenCode:

- `opencode serve --port <number> --hostname <string>` запускает headless HTTP server.
- `GET /global/health` возвращает health/version.
- `GET /doc` открывает OpenAPI 3.1 спецификацию.
- `POST /session` создаёт сессию.
- `POST /session/{id}/message` отправляет сообщение и ждёт ответ.

Источники:

- [OpenCode Server docs](https://dev.opencode.ai/docs/server/)
- [OpenCode CLI docs](https://dev.opencode.ai/docs/ru/cli/)

## Configuration

`config.json`:

```json
{
  "opencode": {
    "enabled": true,
    "target_version": "1.15.3",
    "auto_start": true,
    "host": "127.0.0.1",
    "port": 4096,
    "base_url": "http://127.0.0.1:4096",
    "command": "opencode",
    "runtime_config_home": ".opencode-runtime",
    "username": "opencode",
    "password": "",
    "cors": ["http://localhost:9696"]
  }
}
```

`custom.base_url` используется как OpenAI-compatible endpoint для OpenCode:

```json
{
  "custom": {
    "base_url": "http://localhost:9696/v1",
    "api_key": ""
  }
}
```

If `password` is set, FastAPI Foundry sends HTTP Basic Auth to OpenCode.
OpenCode itself also reads:

- `OPENCODE_SERVER_PASSWORD`
- `OPENCODE_SERVER_USERNAME`

## FastAPI endpoints

All endpoints are under `/api/v1/opencode`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/status` | Configured settings + OpenCode health/version |
| `POST` | `/start` | Start `opencode serve` with configured host/port/CORS |
| `POST` | `/stop` | Stop process started by this API |
| `GET` | `/config` | Proxy OpenCode `GET /config` |
| `GET` | `/generated-config` | Show the `opencode.json` generated from `config.json` |
| `PATCH` | `/config` | Proxy OpenCode `PATCH /config` |
| `GET` | `/providers` | Proxy OpenCode provider list |
| `GET` | `/sessions` | Proxy OpenCode session list |
| `POST` | `/sessions` | Create OpenCode session |
| `GET` | `/sessions/{session_id}/messages` | List session messages |
| `POST` | `/message` | Send prompt to a session or create a new one |
| `GET` | `/openapi-url` | Return OpenCode `/doc` URL |

Example:

```bash
curl -X POST http://localhost:9696/api/v1/opencode/message \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Inspect this repository and summarize the API layout"}'
```

## Web UI

The main UI has an **OpenCode** tab:

- health/version badge
- start/stop controls
- OpenAPI `/doc` link
- provider list
- session list
- prompt sender

Settings are in **Settings -> OpenCode**.

## Notes

- FastAPI Foundry also exposes `POST /v1/chat/completions`, so OpenCode can chat
  through the same local orchestrator it uses for `GET /v1/models`.
- On Windows, FastAPI Foundry starts OpenCode with `XDG_CONFIG_HOME` pointing to
  `opencode.runtime_config_home` (default `.opencode-runtime`). This avoids
  OpenCode 1.15.x failing when `%USERPROFILE%\.config\opencode` already exists.
- The generated OpenCode provider uses `@ai-sdk/openai-compatible`,
  `provider.ai_assist.options.baseURL = custom.base_url`, and the default model
  from `foundry_ai.default_model`.
- The API can stop only a process it started itself. If OpenCode was started externally, use your terminal/process manager to stop it.
- For browser access to OpenCode directly, include the FastAPI origin in `opencode.cors`.
- For automation, prefer FastAPI Foundry `/api/v1/opencode/*`; for direct schema inspection, open the OpenCode `/doc` URL.
- `host: "0.0.0.0"` means "listen on all interfaces". Clients should still connect to `127.0.0.1` or a real LAN IP. FastAPI Foundry normalizes `base_url` from `0.0.0.0` to `127.0.0.1`.
- aiohttp errors may include `ssl:default` even for plain `http://` requests; it does not mean HTTPS is enabled.
