# 🛡️ Контроль качества (QA)

Раздел описывает инфраструктуру тестирования проекта **AI Assistant (ai_assist)**.

---

## Структура раздела

| Страница | Описание |
|---|---|
| [Стратегия](strategy.md) | Уровни тестирования, инструменты, правила |
| [Запуск тестов](running.md) | Команды, скрипты, CI/CD |
| [Юнит-тесты](unit.md) | Тесты изолированных функций и классов |
| [Интеграционные тесты](integration.md) | Тесты взаимодействия компонентов |
| [Тесты агентов](agents.md) | Тесты AI-агентов с моками |

---

## Быстрый старт

```powershell
# Установка зависимостей QA
venv\Scripts\pip.exe install -r requirements-qa.txt

# Запуск всех тестов
venv\Scripts\pytest.exe

# Полный цикл: линтер + типы + тесты + отчёт покрытия
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-Qa.ps1
```

---

## Структура директории `tests/`

```
tests/
├── unit/
│   └── test_json_utils.py       # Тесты утилит JSON
├── integration/
│   └── test_powershell_mcp.py   # Тесты PowerShell MCP
├── agents/
│   └── test_rag_agent.py        # Тесты RAG-агента
└── reports/
    ├── coverage/                # HTML-отчёт покрытия (генерируется)
    └── junit.xml                # JUnit-отчёт для CI (генерируется)
```

---

## Исключения

Директория `extensions/` исключена из тестирования — браузерные расширения имеют собственный цикл тестирования.

