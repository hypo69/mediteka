# Запуск тестов

---

## Локальный запуск

### Установка зависимостей

```powershell
venv\Scripts\pip.exe install -r requirements-qa.txt
```

### Все тесты

```powershell
venv\Scripts\pytest.exe
```

### Конкретный уровень

```powershell
# Только юнит-тесты
venv\Scripts\pytest.exe tests/unit/

# Только интеграционные
venv\Scripts\pytest.exe tests/integration/

# Только тесты агентов
venv\Scripts\pytest.exe tests/agents/
```

### С отчётом покрытия

```powershell
venv\Scripts\pytest.exe --cov=src --cov-report=html:tests/reports/coverage
# Открыть отчёт
start tests\reports\coverage\index.html
```

---

## Полный QA-цикл (скрипт)

Скрипт `scripts/Invoke-Qa.ps1` выполняет последовательно:

1. Очистку `tests/reports/` через `scripts/clear-reports.ps1`
2. Линтинг — `ruff check src/`
3. Проверку типов — `mypy src/`
4. Тесты с покрытием — `pytest --cov=src --cov-report=html --junitxml`
5. Открытие HTML-отчёта в браузере

```powershell
# Полный цикл с открытием отчёта
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-Qa.ps1

# Без открытия браузера (для CI)
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-Qa.ps1 -SkipCoverageReport
```

### Только очистка отчётов

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\clear-reports.ps1
```

---

## Статический анализ

```powershell
# Линтер
venv\Scripts\ruff.exe check src/

# Автоисправление
venv\Scripts\ruff.exe check src/ --fix

# Проверка типов
venv\Scripts\mypy.exe src/
```

---

## GitHub Actions

Workflow `.github/workflows/dev-qa.yml` запускается автоматически при `push` в ветку `dev`.

**Шаги pipeline:**

1. Checkout репозитория
2. Установка Python 3.11
3. Установка зависимостей (`requirements.txt` + `requirements-qa.txt`)
4. Создание `venv/`
5. Запуск `scripts/Invoke-Qa.ps1 -SkipCoverageReport`
6. Загрузка артефактов (`tests/reports/`) в GitHub Actions

**Триггеры:**

```yaml
on:
  push:
    branches: [dev]
  pull_request:
    branches: [dev]
```

Раннер: `windows-latest` — проект использует PowerShell и Windows-специфичные утилиты.

---

## Артефакты тестирования

После запуска в `tests/reports/` появляются:

| Файл | Описание |
|---|---|
| `coverage/index.html` | HTML-отчёт покрытия кода |
| `junit.xml` | JUnit XML для интеграции с CI |

Содержимое `tests/reports/` исключено из git (`.gitignore`), кроме `README.md`.

