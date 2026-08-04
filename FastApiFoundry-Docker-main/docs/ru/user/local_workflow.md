# Локальный workflow: от задачи до ответа

Эта страница описывает единый подход к решению повседневных задач с помощью AI Assistant —
без облака, без регистраций, без утечки данных.

Принцип один для всех сценариев:

```
Задача → Подготовить данные → Спросить модель → Получить ответ
```

Всё происходит на вашей машине. Интернет не нужен.

---

## Шаг 1 — Запустить сервер

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

После запуска открывается веб-интерфейс: **http://localhost:9696**

---

## Шаг 2 — Выбрать сценарий

### 💬 Просто спросить

Самый простой случай — задать вопрос напрямую через чат.

**Когда:** нужен совет, объяснение, перевод, черновик текста, помощь с кодом.

**Как:** вкладка **Chat** → выбрать модель → написать вопрос.

```
Вопрос → модель → ответ
```

Примеры:

- «Объясни разницу между TCP и UDP простыми словами»
- «Переведи этот абзац на английский»
- «Найди ошибку в этом Python-коде»
- «Напиши письмо с отказом от встречи — вежливо»

---

### 📄 Работать с документами (RAG)

Когда нужно задавать вопросы по конкретным файлам — договорам, инструкциям,
архивам, книгам.

**Когда:** у вас есть документы, по которым нужно искать информацию.

**Workflow:**

```
Загрузить документы → Построить индекс → Задать вопрос → Получить ответ с цитатой
```

**Как:**

1. Вкладка **RAG** → **Build Index** → указать папку с документами
2. Дождаться построения индекса
3. Вкладка **Chat** → включить **Use RAG** → задать вопрос

Поддерживаемые форматы: PDF, DOCX, XLSX, PPTX, HTML, TXT, изображения (OCR), ZIP, 7z и др.

!!! tip "Профили RAG"
    Можно создать несколько профилей — например, отдельно для рабочих документов
    и отдельно для личной библиотеки. Переключение мгновенное, без перезапуска.

---

### 🔁 Автоматизировать через скрипт

Когда нужно обрабатывать много файлов или встроить AI в существующий процесс.

**Когда:** пакетная обработка, регулярные задачи, интеграция с другими инструментами.

**Workflow:**

```
Скрипт читает файл → отправляет запрос к API → получает ответ → сохраняет результат
```

=== "Python"

    ```python
    import requests
    from pathlib import Path

    text = Path("document.txt").read_text(encoding="utf-8")

    r = requests.post("http://localhost:9696/api/v1/generate", json={
        "prompt": f"Сделай краткое резюме:\n\n{text}",
        "model": "foundry::qwen3-0.6b",
        "max_tokens": 512,
    })
    print(r.json()["content"])
    ```

=== "PowerShell"

    ```powershell
    $text = Get-Content "document.txt" -Raw
    $body = @{
        prompt     = "Сделай краткое резюме:`n`n$text"
        model      = "foundry::qwen3-0.6b"
        max_tokens = 512
    } | ConvertTo-Json

    $r = Invoke-RestMethod -Uri "http://localhost:9696/api/v1/generate" `
        -Method POST -Body $body -ContentType "application/json"
    Write-Host $r.content
    ```

=== "curl"

    ```bash
    TEXT=$(cat document.txt)
    curl -s -X POST http://localhost:9696/api/v1/generate \
      -H "Content-Type: application/json" \
      -d "{\"prompt\": \"Сделай краткое резюме:\n\n$TEXT\", \"model\": \"foundry::qwen3-0.6b\"}"
    ```

---

### 🤖 Запустить агента

Когда задача требует нескольких шагов — поиск информации, выполнение команд,
работа с системой.

**Когда:** нужно не просто ответить, а что-то сделать.

**Workflow:**

```
Запрос → агент выбирает инструменты → выполняет шаги → формирует ответ
```

**Как:** вкладка **Agent** → выбрать агента → описать задачу.

| Агент | Что умеет |
|---|---|
| `powershell` | Выполнять команды в системе |
| `rag` | Искать по базе знаний |
| `windows_os` | Диагностика Windows: процессы, службы, диски |
| `qa` | Запускать тесты, проверять покрытие |
| `google` | Работать с Gmail, Calendar, Sheets |

---

### 📦 Пакетная обработка

Когда нужно обработать много файлов одновременно.

**Workflow:**

```
Список файлов → цикл → POST /api/v1/generate → сохранить результаты
```

=== "Python"

    ```python
    import requests
    from pathlib import Path

    docs = Path("./docs").glob("*.txt")
    results = {}

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        r = requests.post("http://localhost:9696/api/v1/generate", json={
            "prompt": f"Краткое резюме:\n\n{text[:3000]}",
            "model": "foundry::qwen3-0.6b",
        })
        results[doc.name] = r.json().get("content", "")
        print(f"✅ {doc.name}")

    # Сохранить результаты
    import json
    Path("summaries.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2)
    )
    ```

=== "PowerShell"

    ```powershell
    $results = @{}

    Get-ChildItem ".\docs\*.txt" | ForEach-Object {
        $text = Get-Content $_.FullName -Raw
        $body = @{
            prompt = "Краткое резюме:`n`n$($text.Substring(0, [Math]::Min(3000, $text.Length)))"
            model  = "foundry::qwen3-0.6b"
        } | ConvertTo-Json

        $r = Invoke-RestMethod -Uri "http://localhost:9696/api/v1/generate" `
            -Method POST -Body $body -ContentType "application/json"
        $results[$_.Name] = $r.content
        Write-Host "✅ $($_.Name)"
    }

    $results | ConvertTo-Json | Set-Content "summaries.json" -Encoding UTF8
    ```

---

## Выбор модели под задачу

Разные задачи требуют разных моделей. Общее правило:

| Задача | Рекомендуемая модель | Почему |
|---|---|---|
| Быстрый вопрос-ответ | `foundry::qwen3-0.6b` | Малая, быстрая |
| Анализ и рассуждения | `ollama::deepseek-r1:7b` | Цепочки мышления |
| Написание кода | `ollama::codellama:7b` | Специализирована на коде |
| Работа с документами | `llama::~/.models/mistral-7b.gguf` | Длинный контекст |
| Перевод | `hf::facebook/nllb-200-distilled-600M` | Многоязычная |
| Суммаризация | `foundry::phi-3-mini` | Хорошо сжимает текст |

Модель указывается в поле `model` — просто меняете префикс, сервер перезапускать не нужно.

---

## Типичные ошибки и решения

| Проблема | Причина | Решение |
|---|---|---|
| Модель не отвечает | Foundry не запущен | `foundry service start` |
| Медленный ответ | Модель слишком большая для железа | Выбрать модель меньшего размера |
| RAG не находит нужное | Индекс не построен или устарел | Перестроить индекс во вкладке RAG |
| Ответ обрывается | Мало `max_tokens` | Увеличить `max_tokens` в запросе |
| Ошибка 400 | Неверный префикс модели | Проверить формат: `foundry::`, `hf::`, `llama::`, `ollama::` |

---

## Что дальше

- [Работа с моделями](models_guide.md) — подробно о каждом бэкенде
- [Система RAG](../dev/rag_system.md) — как устроен поиск по документам
- [API Reference](../dev/api_reference.md) — все эндпоинты для автоматизации
- [Агенты](../dev/agents.md) — многошаговые задачи
