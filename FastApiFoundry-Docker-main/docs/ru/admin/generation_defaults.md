# Параметры генерации по умолчанию

Описание механизма глобальных дефолтов `temperature` и `max_tokens`,
их настройки и переопределения на уровне запроса.

---

## Концепция

До версии 0.8.0 параметры `temperature` и `max_tokens` были захардкожены
в каждом endpoint отдельно (`0.7` и `2048`/`1000`).

Начиная с **0.8.0** введён единый блок `defaults` в `config.json`.
Все endpoints и роутер читают значения оттуда, если клиент не передал их явно.

```
Запрос клиента
    │
    ├── передал temperature/max_tokens → используются значения из запроса
    │
    └── не передал → router.py читает config.defaults → применяет глобальный дефолт
```

---

## Настройка в config.json

```json
{
  "defaults": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

| Параметр | Тип | Описание | Диапазон |
|---|---|---|---|
| `temperature` | float | Случайность генерации | 0.0 — 2.0 |
| `max_tokens` | int | Максимум токенов в ответе | 1 — зависит от модели |

!!! tip "Рекомендации по temperature"
    - `0.0–0.3` — детерминированные ответы, код, факты
    - `0.5–0.8` — сбалансированный режим (дефолт)
    - `1.0–1.5` — творческие задачи, генерация текста
    - `> 1.5` — непредсказуемые ответы, не рекомендуется для продакшена

!!! warning "max_tokens и контекстное окно"
    Значение `max_tokens` не должно превышать контекстное окно модели.
    Для большинства локальных моделей безопасный максимум — 4096.

---

## Переопределение на уровне запроса

Любой клиент может передать свои значения в теле запроса.
Они имеют приоритет над глобальными дефолтами.

=== "Python"
    ```python
    import requests

    response = requests.post(
        "http://localhost:9696/api/v1/generate",
        json={
            "prompt": "Объясни квантовую запутанность",
            "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
            "temperature": 0.3,
            "max_tokens": 512,
        }
    )
    print(response.json()["content"])
    ```

=== "PowerShell"
    ```powershell
    $body = @{
        prompt      = "Объясни квантовую запутанность"
        model       = "hf::Qwen/Qwen2.5-0.5B-Instruct"
        temperature = 0.3
        max_tokens  = 512
    } | ConvertTo-Json

    Invoke-RestMethod -Uri "http://localhost:9696/api/v1/generate" `
        -Method POST -Body $body -ContentType "application/json"
    ```

=== "curl"
    ```bash
    curl -X POST http://localhost:9696/api/v1/generate \
      -H "Content-Type: application/json" \
      -d '{
        "prompt": "Объясни квантовую запутанность",
        "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
        "temperature": 0.3,
        "max_tokens": 512
      }'
    ```

=== "Go"
    ```go
    body := map[string]any{
        "prompt":      "Объясни квантовую запутанность",
        "model":       "hf::Qwen/Qwen2.5-0.5B-Instruct",
        "temperature": 0.3,
        "max_tokens":  512,
    }
    data, _ := json.Marshal(body)
    http.Post("http://localhost:9696/api/v1/generate",
        "application/json", bytes.NewReader(data))
    ```

=== "Java"
    ```java
    String body = """
        {"prompt":"Объясни квантовую запутанность",
         "model":"hf::Qwen/Qwen2.5-0.5B-Instruct",
         "temperature":0.3,"max_tokens":512}
        """;
    HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("http://localhost:9696/api/v1/generate"))
        .POST(HttpRequest.BodyPublishers.ofString(body))
        .header("Content-Type", "application/json")
        .build();
    ```

=== "C#"
    ```csharp
    var payload = new {
        prompt = "Объясни квантовую запутанность",
        model = "hf::Qwen/Qwen2.5-0.5B-Instruct",
        temperature = 0.3,
        max_tokens = 512
    };
    var json = JsonSerializer.Serialize(payload);
    await client.PostAsync("http://localhost:9696/api/v1/generate",
        new StringContent(json, Encoding.UTF8, "application/json"));
    ```

=== "PHP"
    ```php
    $response = file_get_contents('http://localhost:9696/api/v1/generate', false,
        stream_context_create(['http' => [
            'method'  => 'POST',
            'header'  => 'Content-Type: application/json',
            'content' => json_encode([
                'prompt'      => 'Объясни квантовую запутанность',
                'model'       => 'hf::Qwen/Qwen2.5-0.5B-Instruct',
                'temperature' => 0.3,
                'max_tokens'  => 512,
            ]),
        ]])
    );
    ```

---

## Приоритет значений

```
Запрос (temperature=0.3)  →  используется 0.3
Запрос (без temperature)  →  config.defaults.temperature (0.7)
config.defaults отсутствует  →  hardcoded fallback (0.7)
```

Это правило применяется одинаково для всех endpoints:

| Endpoint | Поддерживает per-request параметры |
|---|---|
| `POST /api/v1/generate` | ✅ |
| `POST /api/v1/ai/generate` | ✅ |
| `POST /api/v1/ai/generate/stream` | ✅ |
| `POST /api/v1/ai/chat` | ✅ |
| `POST /api/v1/ai/chat/stream` | ✅ |
| `POST /api/v1/chat/message` | ✅ |
| `POST /api/v1/chat/stream` | ✅ |

---

## Где применяется в коде

Логика дефолтов сосредоточена в одном месте — `src/models/router.py`:

```python
def _default_temperature() -> float:
    """Return default temperature from config.defaults, fallback 0.7."""
    from config_manager import config as _cfg
    return _cfg.foundry_temperature  # читает из config.defaults.temperature

def _default_max_tokens() -> int:
    """Return default max_tokens from config.defaults, fallback 2048."""
    from config_manager import config as _cfg
    return _cfg.foundry_max_tokens  # читает из config.defaults.max_tokens
```

Все endpoints передают `temperature=None` / `max_tokens=None` когда клиент
не указал значения. Роутер подставляет дефолты из конфига.

!!! info "Изменение дефолтов без перезапуска"
    Значения читаются из `config_manager.Config` singleton.
    После изменения `config.json` через `PATCH /api/v1/config` или веб-интерфейс
    новые дефолты применяются к следующим запросам без перезапуска сервера.

---

## История изменений

| Версия | Изменение |
|---|---|
| 0.8.0 | Введён блок `defaults` в `config.json`; `temperature`/`max_tokens` вынесены из `foundry_ai` |
| 0.8.0 | `route_generate()` принимает `Optional[float]`/`Optional[int]`, применяет дефолты из конфига |
| 0.8.0 | Все endpoints передают `None` вместо захардкоженных значений |
| до 0.8.0 | `temperature=0.7`, `max_tokens=1000`/`2048` были захардкожены в каждом endpoint |
