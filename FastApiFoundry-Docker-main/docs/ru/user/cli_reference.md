# CLI Reference

`cli.ps1` — интерактивный CLI для AI Assistant. Все операции идут через REST API на `http://localhost:9696`.

---

## Запуск

### Интерактивный режим (REPL)

Запустите без аргументов — откроется интерактивная сессия:

```powershell
.\cli.ps1
```

```
  AI Assistant CLI
  http://localhost:9696
  Type /help for commands, /exit or Ctrl+C to quit

  Service: healthy  |  Foundry: healthy  |  llama: running

> /health
> /generate What is RAG?
> /chat
> /exit

✅ Bye!
```

В REPL все команды вводятся с префиксом `/`. Нажмите `Ctrl+C` или введите `/exit` для выхода.

### Одиночная команда

```powershell
.\cli.ps1 <команда> [аргументы] [--опции]
```

### Опции

| Опция | По умолчанию | Описание |
|---|---|---|
| `--model <prefix::id>` | — | Модель для generate/chat |
| `--base-url <url>` | `http://localhost:9696` | URL API сервера |
| `--top-k <n>` | `5` | Количество результатов RAG |
| `--raw` | — | Вывод сырого JSON |

---

## Команды

### health — статус сервиса

=== "REPL"
    ```
    > /health
    Status    : healthy
    Foundry   : healthy
    llama.cpp : running
    RAG       : disabled
    Docs      : stopped
    Models    : 3
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 health
    .\cli.ps1 health --raw
    ```

---

### models — список моделей

=== "REPL"
    ```
    > /models
    ℹ️  Available models (3):
      • qwen3-0.6b-generic-cpu:4 [foundry]
      • llama-server [llama.cpp]
      • mistral:latest [ollama]
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 models
    .\cli.ps1 models --raw
    ```

---

### generate — генерация текста

=== "REPL"
    ```
    > /generate What is FAISS?
    FAISS (Facebook AI Similarity Search) is a library for...

    ℹ️  Model: ollama::llama3  |  Tokens: 142
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 generate "What is FAISS?"
    .\cli.ps1 generate "Explain RAG" --model ollama::llama3
    .\cli.ps1 generate "Hello" --model foundry::qwen3-0.6b
    ```

Префиксы моделей: `foundry::`, `hf::`, `llama::`, `ollama::`.

---

### chat — интерактивный чат

Запускает диалог с историей сессии. Работает одинаково в REPL и одиночном режиме.

=== "REPL"
    ```
    > /chat
    ✅ Chat started (session: a3f1b2c4...)
    ℹ️  Model: default  |  Type 'exit' to end

    You: Привет! Что такое Python?
    AI: Python — высокоуровневый язык программирования...

    You: А чем отличается от Java?
    AI: Основные отличия: Python динамически типизирован...

    You: exit
    ✅ Chat ended.
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 chat
    .\cli.ps1 chat --model foundry::qwen3-0.6b
    .\cli.ps1 chat --model ollama::mistral
    ```

Для выхода из чата: `exit`, `quit`, `/exit` или `Ctrl+C`.

---

### rag — система RAG

#### rag search

=== "REPL"
    ```
    > /rag search vector databases
    ℹ️  Results (3):
    [1] score=0.847
        FAISS is a library for efficient similarity search...
    [2] score=0.731
        Vector databases store embeddings and support...
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 rag search "vector databases"
    .\cli.ps1 rag search "what is FAISS" --top-k 3
    ```

#### rag build

=== "REPL"
    ```
    > /rag build ./docs
    ℹ️  Building RAG index from: ./docs
    ✅ Index rebuilt — 247 chunks
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 rag build ./docs
    .\cli.ps1 rag build D:\my-knowledge-base
    ```

#### rag status

=== "REPL"
    ```
    > /rag status
    Enabled   : True
    Index dir : C:\Users\user\.aiassistant\rag\docs
    Model     : sentence-transformers/all-MiniLM-L6-v2
    Chunks    : 247
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 rag status
    ```

#### rag profiles

=== "REPL"
    ```
    > /rag profiles
    ℹ️  RAG profiles (2):
      ✅ docs
      ⬜ notes
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 rag profiles
    ```

---

### foundry — управление Foundry

#### foundry status

=== "REPL"
    ```
    > /foundry status
    Running : True
    Status  : healthy
    Port    : 52632
    URL     : http://127.0.0.1:52632/v1
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 foundry status
    ```

#### foundry models

=== "REPL"
    ```
    > /foundry models
    ℹ️  Foundry models (2):
      • qwen3-0.6b-generic-cpu:4
      • qwen2.5-1.5b-instruct-generic-cpu:4
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 foundry models
    ```

#### foundry load / unload

=== "REPL"
    ```
    > /foundry load qwen3-0.6b-generic-cpu:4
    ✅ Loaded: qwen3-0.6b-generic-cpu:4

    > /foundry unload qwen3-0.6b-generic-cpu:4
    ✅ Unloaded: qwen3-0.6b-generic-cpu:4
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 foundry load qwen3-0.6b-generic-cpu:4
    .\cli.ps1 foundry unload qwen3-0.6b-generic-cpu:4
    ```

---

### config — конфигурация

#### config get

=== "REPL"
    ```
    > /config get
    {
      "fastapi_server": { "port": 9696, ... },
      "rag_system": { "enabled": false, ... },
      ...
    }
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 config get
    ```

#### config set

Ключи задаются в dot-notation. Значения `true`/`false` конвертируются в bool, числа — в int.

=== "REPL"
    ```
    > /config set rag_system.enabled true
    ✅ Set rag_system.enabled = true

    > /config set fastapi_server.port 9696
    ✅ Set fastapi_server.port = 9696
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 config set rag_system.enabled true
    .\cli.ps1 config set foundry_ai.temperature 0.5
    .\cli.ps1 config set llama_cpp.port 9780
    ```

---

### logs — просмотр логов

=== "REPL"
    ```
    > /logs
    2025-06-10 12:01:03 INFO  ✅ RAG system initialized
    2025-06-10 12:01:05 INFO  🤖 Generating: model=ollama::llama3
    ...

    > /logs 100
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 logs
    .\cli.ps1 logs 100
    ```

---

### restart — перезапуск сервисов

=== "REPL"
    ```
    > /restart foundry
    ✅ Foundry start command sent

    > /restart llama
    ✅ llama.cpp started on port 9780
    ```

=== "Одиночная"
    ```powershell
    .\cli.ps1 restart foundry
    .\cli.ps1 restart llama
    .\cli.ps1 restart docs
    .\cli.ps1 restart rag
    ```

| Сервис | Действие |
|---|---|
| `foundry` | `foundry service start` |
| `llama` | Запуск llama-server с моделью из config |
| `docs` | `mkdocs serve` на порту 9697 |
| `rag` | Перезагрузка FAISS индекса |

---

## Типичные сценарии

### Быстрая проверка системы

```powershell
.\cli.ps1 health
.\cli.ps1 models
```

### Работа с документами

```powershell
# Проиндексировать папку
.\cli.ps1 rag build ./docs

# Проверить индекс
.\cli.ps1 rag status

# Поиск
.\cli.ps1 rag search "как настроить RAG"
```

### Смена модели и генерация

```powershell
.\cli.ps1 foundry load qwen3-0.6b-generic-cpu:4
.\cli.ps1 generate "Объясни FAISS" --model foundry::qwen3-0.6b
```

### Удалённый сервер

```powershell
.\cli.ps1 --base-url http://192.168.1.10:9696 health
.\cli.ps1 --base-url http://192.168.1.10:9696 models
```

### Скрипты и автоматизация

```powershell
# Получить JSON для обработки
$models = .\cli.ps1 models --raw | ConvertFrom-Json
$models.models | Where-Object { $_.provider -eq 'foundry' }

# Проверить здоровье в CI
$h = .\cli.ps1 health --raw | ConvertFrom-Json
if ($h.status -ne 'healthy') { exit 1 }
```

---

## Справочник команд REPL

| Команда | Описание |
|---|---|
| `/health` | Статус сервиса |
| `/models` | Список моделей |
| `/generate <prompt>` | Генерация текста |
| `/chat` | Интерактивный чат |
| `/rag search <query>` | Поиск по RAG |
| `/rag build <dir>` | Построить индекс |
| `/rag status` | Статус RAG |
| `/rag profiles` | Профили RAG |
| `/foundry status` | Статус Foundry |
| `/foundry models` | Модели Foundry |
| `/foundry load <id>` | Загрузить модель |
| `/foundry unload <id>` | Выгрузить модель |
| `/config get` | Показать конфиг |
| `/config set <key> <val>` | Изменить конфиг |
| `/logs [n]` | Последние логи |
| `/restart <service>` | Перезапустить сервис |
| `/help` | Справка |
| `/exit` или `Ctrl+C` | Выход |

---

## Foundry Local CLI

Foundry Local управляется через команду `foundry`. Устанавливается через:

```powershell
winget install Microsoft.FoundryLocal
```

### foundry service

| Команда | Описание |
|---|---|
| `foundry service start` | Запустить сервис в фоне |
| `foundry service stop` | Остановить сервис |
| `foundry service status` | Показать статус, URL и порт |
| `foundry service restart` | Перезапустить сервис |

```powershell
foundry service start
foundry service status
# 🟢 Model management service is running on http://127.0.0.1:52632/openai/status
```

!!! tip "Динамический порт"
    Foundry каждый раз может запускаться на другом порту.
    AI Assistant находит его автоматически через `tasklist` + `netstat`.
    Чтобы зафиксировать порт — задайте `FOUNDRY_BASE_URL` в `.env`.

### foundry model

| Команда | Описание |
|---|---|
| `foundry model list` | Список скачанных моделей |
| `foundry model list-available` | Каталог доступных моделей |
| `foundry model download <id>` | Скачать модель |
| `foundry model load <id>` | Загрузить в память |
| `foundry model unload <id>` | Выгрузить из памяти |
| `foundry model info <id>` | Информация о модели |
| `foundry model remove <id>` | Удалить из кэша |

```powershell
foundry model list-available
foundry model download qwen3-0.6b-generic-cpu:4:4
foundry model load qwen3-0.6b-generic-cpu:4:4
foundry model list
foundry model unload qwen3-0.6b-generic-cpu:4:4
```

### foundry run

Интерактивный чат с моделью прямо в терминале:

```powershell
foundry run qwen3-0.6b-generic-cpu:4:4
```

```
You: Привет! Что такое Python?
Assistant: Python — это высокоуровневый язык программирования...

You: /exit
```

### Рекомендуемые модели Foundry

| Модель | Размер | Описание |
|---|---|---|
| `qwen3-0.6b-generic-cpu:4:4` | 0.8 GB | Самая лёгкая, быстрая |
| `qwen2.5-1.5b-instruct-generic-cpu:4` | 1.78 GB | Хороший баланс |
| `qwen2.5-3b-instruct-generic-cpu:4` | 2.8 GB | Средняя |
| `deepseek-r1-distill-qwen-7b-generic-cpu:3` | 6.43 GB | С цепочками рассуждений |

---

## llama.cpp

Запуск GGUF моделей через `llama-server.exe`. Бинарники в `bin/`.

### Запуск сервера

```powershell
# Через скрипт (читает config.json)
.\scripts\Start-Llama.ps1

# Вручную
.\bin\llama-b8802-bin-win-cpu-x64\llama-server.exe `
  --model ~/.models/qwen2.5-0.5b-q4_k_m.gguf `
  --port 9780 `
  --ctx-size 4096 `
  --threads 8
```

### Проверка

```powershell
curl http://localhost:9780/health
curl http://localhost:9780/v1/models
```

### Скачивание GGUF моделей

```powershell
pip install huggingface_hub
hf auth login

# Q4_K_M — рекомендуется (лучший баланс размер/качество)
hf download bartowski/Qwen2.5-0.5B-Instruct-GGUF `
  --include "*Q4_K_M.gguf" `
  --local-dir ~/.models
```

| Квантование | Размер (7B) | Рекомендация |
|---|---|---|
| `Q4_K_M` | ~4.1 GB | **Рекомендуется** |
| `Q5_K_M` | ~4.8 GB | Если есть запас RAM |
| `Q8_0` | ~7.2 GB | Максимальное качество |

---

## HuggingFace CLI

```powershell
pip install huggingface_hub
hf auth login
hf whoami
hf download <repo_id> --include "*.gguf" --local-dir ~/.models
huggingface-cli scan-cache
```

---

## Диагностика

```powershell
# Проверить окружение
venv\Scripts\python.exe check_env.py

# Полная диагностика
venv\Scripts\python.exe diagnose.py

# Smoke-тесты всех endpoints
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py

# Через CLI
.\cli.ps1 health
.\cli.ps1 models --raw
```
