# Интеграционные тесты

Файлы: `tests/integration/`

Проверка взаимодействия между компонентами системы.

---

## test_powershell_mcp.py

**Компонент:** PowerShell MCP сервер (`mcp/src/servers/McpSTDIOServer.ps1`)

Проверяет реальное выполнение PowerShell через `subprocess` — без моков интерпретатора.

| Тест | Сценарий |
|---|---|
| `test_execution_simple` | Базовая команда PowerShell, проверка версии ≥ 5 |
| `test_json_rpc_simulation` | Передача JSON через stdin, парсинг `ConvertFrom-Json` |

**Как работает `test_json_rpc_simulation`:**

```
pytest → subprocess.Popen(powershell) → stdin: JSON payload
                                      ← stdout: распарсенное значение
assert "Ai Assistant_QA" in stdout
```

**Пример:**

```python
def test_json_rpc_simulation(self):
    """Simulation of JSON data passing through PowerShell stdin."""
    payload = json.dumps({"params": {"message": "Ai Assistant_QA"}})
    script = "$input | ConvertFrom-Json | ForEach-Object { $_.params.message }"

    proc = subprocess.Popen(
        ["powershell", "-Command", script],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, encoding="utf-8",
    )
    stdout, _ = proc.communicate(input=payload)
    assert "Ai Assistant_QA" in stdout
```

!!! warning "Только Windows"
    Тесты PowerShell выполняются только на Windows. В CI используется раннер `windows-latest`.

**Запуск:**

```powershell
venv\Scripts\pytest.exe tests/integration/test_powershell_mcp.py -v
```

---

## Тестирование FastAPI эндпоинтов

Для тестирования HTTP-эндпоинтов используется `httpx.AsyncClient` с моком внешних сервисов через `respx`.

**Шаблон:**

```python
import pytest
import respx
from httpx import AsyncClient, Response
from src.api.app import create_app

@pytest.mark.asyncio
class TestGenerateEndpoint:
    """Integration tests for /api/v1/generate."""

    @respx.mock
    async def test_generate_success(self):
        """Validation of successful text generation via Foundry."""
        # Mock Foundry response
        respx.post("http://localhost:50477/v1/chat/completions").mock(
            return_value=Response(200, json={
                "choices": [{"message": {"content": "Hello"}}]
            })
        )

        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/generate", json={
                "prompt": "Hi", "model": "foundry::qwen3-0.6b"
            })

        assert response.status_code == 200
        assert response.json()["success"] is True
```

---

## Добавление новых интеграционных тестов

Размещать в `tests/integration/test_<component>.py`.

**Правила:**

- Внешние HTTP-сервисы (Foundry, HuggingFace, Ollama) — всегда через `respx.mock`
- Реальный PowerShell допускается
- Тест не должен требовать запущенного сервера `run.py`
