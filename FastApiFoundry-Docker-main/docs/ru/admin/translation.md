# Перевод запросов к модели (translate_model_dialog)

Описание механизма автоматического перевода: запрос клиента → английский → модель → язык клиента.

---

## Концепция

Локальные AI модели работают лучше на английском языке. Флаг `translate_model_dialog`
позволяет клиенту (чат, Telegram, внешний скрипт) отправлять запросы на любом языке —
система автоматически переведёт их перед отправкой модели и вернёт ответ на языке клиента.

```
Клиент (ru/he/de/...)
    │
    │  "Объясни квантовую запутанность"
    ▼
translate_model_dialog=true
    │
    ▼
[Translator] → "Explain quantum entanglement"  (→ EN)
    │
    ▼
[AI Model]   → "Quantum entanglement is..."    (EN)
    │
    ▼
[Translator] → "Квантовая запутанность — это..." (→ ru)
    │
    ▼
Клиент получает ответ на своём языке
```

---

## Приоритет активации

```
Запрос содержит translate_model_dialog=true   →  перевод ВКЛ
Запрос содержит translate_model_dialog=false  →  перевод ВЫКЛ
Запрос не содержит translate_model_dialog     →  читается config.json translator.enabled
```

Это правило реализовано в `Translator.should_translate()` (`src/utils/translator.py`)
и применяется одинаково во всех endpoints.

---

## Глобальное включение через config.json

Чтобы перевод работал по умолчанию для всех запросов без явного флага:

```json
{
  "translator": {
    "enabled": true,
    "default_provider": "mymemory"
  }
}
```

!!! warning "Перевод замедляет ответ"
    Каждый запрос с переводом делает 1–2 дополнительных HTTP-вызова к провайдеру перевода.
    Для production рекомендуется включать перевод только per-request, а не глобально.

---

## Использование в API

### POST /api/v1/generate

```json
{
  "prompt": "Объясни квантовую запутанность",
  "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
  "translate_model_dialog": true,
  "user_language": "ru"
}
```

Поля:

| Поле | Тип | Описание |
|---|---|---|
| `translate_model_dialog` | bool | Включить перевод для этого запроса |
| `user_language` | str\|null | Язык клиента (ISO 639-1). `null` = автоопределение |

Ответ содержит дополнительные поля:

```json
{
  "success": true,
  "content": "Квантовая запутанность — это...",
  "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
  "user_language": "ru",
  "translated": true,
  "usage": {...}
}
```

### POST /api/v1/chat/message

```json
{
  "session_id": "uuid",
  "message": "מה זה בינה מלאכותית?",
  "translate_model_dialog": true,
  "user_language": "he"
}
```

### POST /api/v1/chat/stream

```json
{
  "session_id": "uuid",
  "message": "Was ist künstliche Intelligenz?",
  "translate_model_dialog": true,
  "user_language": "de"
}
```

При стриминге после завершения генерации приходит дополнительное SSE-событие:

```
data: {"chunk_translated": "Künstliche Intelligenz ist..."}
```

---

## Примеры запросов

=== "Python"
    ```python
    import requests

    response = requests.post(
        "http://localhost:9696/api/v1/generate",
        json={
            "prompt": "Объясни квантовую запутанность простыми словами",
            "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
            "translate_model_dialog": True,
            "user_language": "ru",
        }
    )
    data = response.json()
    print(data["content"])        # ответ на русском
    print(data["translated"])     # True
    print(data["user_language"])  # "ru"
    ```

=== "PowerShell"
    ```powershell
    $body = @{
        prompt                = "Объясни квантовую запутанность"
        model                 = "hf::Qwen/Qwen2.5-0.5B-Instruct"
        translate_model_dialog = $true
        user_language         = "ru"
    } | ConvertTo-Json

    $r = Invoke-RestMethod -Uri "http://localhost:9696/api/v1/generate" `
        -Method POST -Body $body -ContentType "application/json"
    Write-Host $r.content
    ```

=== "curl"
    ```bash
    curl -X POST http://localhost:9696/api/v1/generate \
      -H "Content-Type: application/json" \
      -d '{
        "prompt": "Объясни квантовую запутанность",
        "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
        "translate_model_dialog": true,
        "user_language": "ru"
      }'
    ```

=== "Go"
    ```go
    body := map[string]any{
        "prompt":                 "Объясни квантовую запутанность",
        "model":                  "hf::Qwen/Qwen2.5-0.5B-Instruct",
        "translate_model_dialog": true,
        "user_language":          "ru",
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
         "translate_model_dialog":true,"user_language":"ru"}
        """;
    HttpRequest req = HttpRequest.newBuilder()
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
        translate_model_dialog = true,
        user_language = "ru"
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
                'prompt'                 => 'Объясни квантовую запутанность',
                'model'                  => 'hf::Qwen/Qwen2.5-0.5B-Instruct',
                'translate_model_dialog' => true,
                'user_language'          => 'ru',
            ]),
        ]])
    );
    ```

---

## Провайдеры перевода

| Провайдер | Ключ в config | Лимит (бесплатно) | API ключ |
|---|---|---|---|
| `mymemory` | `default_provider` | 500 слов/день (анонимно), 50K с email | нет |
| `libretranslate` | `libretranslate_url` | зависит от инстанса | опционально |
| `deepl` | — | 500K символов/месяц | `DEEPL_API_KEY` в `.env` |
| `google` | — | $10 кредит/месяц | `GOOGLE_TRANSLATE_API_KEY` в `.env` |

Настройка провайдера:

```json
{
  "translator": {
    "enabled": false,
    "default_provider": "mymemory",
    "mymemory_email": "your@email.com",
    "request_timeout_sec": 30
  }
}
```

!!! tip "Увеличение лимита MyMemory"
    Укажите `mymemory_email` в `config.json` — лимит вырастет с 500 до 50 000 слов в день.

---

## Автоопределение языка

Если `user_language` не передан, система определяет язык автоматически через MyMemory API:

```python
# Внутри Translator.resolve_user_lang()
det = await translator.detect_language(prompt)
return det.get("language") or "en"
```

Автоопределение работает для всех языков из `LANG_NAMES` в `translator.py`:
`en`, `ru`, `de`, `fr`, `es`, `zh`, `ja`, `ar`, `uk`, `pl`, `it`, `pt`, `nl`, `ko`, `tr`, `he`.

!!! warning "Точность автоопределения"
    Для коротких фраз (< 5 слов) автоопределение может ошибаться.
    Передавайте `user_language` явно для надёжной работы.

---

## Поддерживаемые endpoints

| Endpoint | translate_model_dialog | user_language | Примечание |
|---|---|---|---|
| `POST /api/v1/generate` | ✅ | ✅ | Полная цепочка |
| `POST /api/v1/ai/generate` | ✅ | — | Через глобальный конфиг |
| `POST /api/v1/ai/chat` | ✅ | — | Через глобальный конфиг |
| `POST /api/v1/chat/message` | ✅ | ✅ | Полная цепочка |
| `POST /api/v1/chat/stream` | ✅ | ✅ | Перевод после накопления |

!!! info "Стриминг и перевод"
    При стриминге (`/chat/stream`) токены передаются клиенту на английском по мере генерации.
    После завершения генерации весь накопленный текст переводится и отправляется
    отдельным событием `chunk_translated`.

---

## Где реализовано в коде

| Файл | Роль |
|---|---|
| `src/utils/translator.py` | `Translator.should_translate()`, `resolve_user_lang()`, `translate_for_model()`, `translate_response()` |
| `src/api/endpoints/generate.py` | Применяет перевод в `/generate` |
| `src/api/endpoints/chat_endpoints.py` | Применяет перевод в `/chat/message` и `/chat/stream` |
| `src/api/endpoints/ai_endpoints.py` | Использует глобальный конфиг (без per-request флага) |

---

## Тесты

```powershell
venv\Scripts\python.exe -m pytest tests/unit/test_translation_pipeline.py -v
```

Покрытие:

| Тест | Что проверяет |
|---|---|
| `test_per_request_true_overrides_config` | Флаг `true` включает перевод даже при `config.enabled=false` |
| `test_per_request_false_overrides_config` | Флаг `false` отключает перевод даже при `config.enabled=true` |
| `test_falls_back_to_config_*` | Без флага используется конфиг |
| `test_explicit_lang_returned_as_is` | Явный `user_language` не вызывает автоопределение |
| `test_auto_detect_called_when_no_lang` | Без `user_language` вызывается `detect_language` |
| `test_prompt_translated_to_en_before_model` | Промпт переводится в EN перед роутером |
| `test_no_translation_when_flag_false` | Промпт идёт в модель без изменений |
| `test_english_prompt_not_translated` | EN промпт не переводится повторно |
| `test_translate_for_model_skips_english` | `source_lang=en` → `was_translated=False` |
| `test_translate_response_skips_english_target` | `target_lang=en` → без перевода |

---

## История изменений

| Версия | Изменение |
|---|---|
| 0.8.0 | `should_translate()` и `resolve_user_lang()` вынесены в `Translator` как общие методы |
| 0.8.0 | `chat/message` и `chat/stream` поддерживают `translate_model_dialog` per-request |
| 0.8.0 | `chat/stream` добавляет событие `chunk_translated` после накопления |
| 0.8.0 | Добавлены 16 unit-тестов в `tests/unit/test_translation_pipeline.py` |
| до 0.8.0 | `translate_model_dialog` работал только в `/generate`; chat endpoints использовали только глобальный конфиг |
