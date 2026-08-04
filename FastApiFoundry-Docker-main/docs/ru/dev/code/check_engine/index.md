# check_engine/ — Диагностика и тесты FastAPI Foundry

Директория содержит скрипты для ручного и автоматического тестирования
компонентов FastAPI Foundry.

**Требование:** сервер должен быть запущен (`python run.py`) перед запуском
большинства тестов, так как они обращаются к живому API на `localhost:9696`.

---

## Запуск

```powershell
# Запуск конкретного теста
venv\Scripts\python.exe check_engine\check_server.py

# Запуск всех endpoints
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py
```

---

## Файлы

### smoke_all_endpoints.py
Комплексное тестирование всех API endpoints.
Требует: запущенный сервер + Foundry + загруженная модель.

```powershell
venv\Scripts\python.exe check_engine\smoke_all_endpoints.py
```

### check_server.py
Быстрая проверка доступности сервера и основных endpoints.
Тестирует: `/`, `/api/v1/health`, `/api/v1/models`, `/docs`.
Не требует запущенного Foundry.

### check_system.py
Комплексная проверка всех компонентов системы.
Тестирует: health, Foundry connection, models, RAG, chat.
Требует: запущенный сервер + Foundry.

### check_foundry_models.py
Прямая проверка подключения к Foundry API.
Тестирует: health check, список моделей.
Не требует запущенного FastAPI — обращается к Foundry напрямую.

### check_rag.py
Тестирование RAG системы: инициализация, поиск по запросам.
Требует: установленные RAG зависимости (`python install_rag_deps.py`).

### check_config.py
Проверка загрузки конфигурации из `config.json`.
Не требует запущенного сервера.

### check_config_editor.py
Тестирование API редактора конфигурации через HTTP.
Тестирует: GET `/api/v1/config`, POST `/api/v1/config`.
Требует: запущенный сервер.

### check_default_model.py
Тестирование сохранения модели по умолчанию через API.
Требует: запущенный сервер + Foundry с загруженными моделями.

### check_chat_implementation.py
Тестирование реализации чата через `enhanced_foundry_client`.
Требует: запущенный Foundry.

### check_simplified.py
Тестирование упрощённых моделей ответов (`api/models.py`).
Не требует запущенного сервера.

### check_port.ps1
PowerShell скрипт для поиска порта Foundry через `Inference.Service.Agent*` процесс.

```powershell
.\check_engine\check_port.ps1
```

---

## Зависимости тестов

| Тест | Сервер | Foundry | RAG deps |
|------|--------|---------|----------|
| check_server.py | ✅ | — | — |
| smoke_all_endpoints.py | ✅ | ✅ | ✅ |
| check_system.py | ✅ | ✅ | — |
| check_foundry_models.py | — | ✅ | — |
| check_rag.py | — | — | ✅ |
| check_config.py | — | — | — |
| check_config_editor.py | ✅ | — | — |
| check_default_model.py | ✅ | ✅ | — |
| check_chat_implementation.py | — | ✅ | — |
| check_simplified.py | — | — | — |
| check_port.ps1 | — | ✅ | — |
