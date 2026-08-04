# AI Assistant (ai_assist)

**Оркестратор локальных AI моделей с единым REST API**

![Version](https://img.shields.io/badge/version-0.8.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Docker-informational)
![Docker](https://img.shields.io/badge/Docker-supported-2496ED?logo=docker&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?logo=huggingface&logoColor=black)
![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-8B5CF6)
![Ollama](https://img.shields.io/badge/Ollama-local-black?logo=ollama&logoColor=white)
![Microsoft Foundry](https://img.shields.io/badge/Microsoft_Foundry-Local-0078D4?logo=microsoft&logoColor=white)
![AI](https://img.shields.io/badge/AI-Orchestrator-FF6B35?logo=openai&logoColor=white)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/11ibP2Ys2eIbjb51t6ZXNyL0BKqy8sGQ_)

---

[🚀 О проекте — зачем это нужно и кому полезно](about.md){ .md-button .md-button--primary }

---

## Кто вы?

Выберите раздел, который соответствует вашей роли.

---

## 👤 Пользователь

Вы работаете с системой через веб-интерфейс или API: задаёте вопросы, получаете ответы, выбираете модели, строите базы знаний.

Система уже развёрнута и запущена администратором. Вам не нужно знать про установку, конфигурацию или код.

- [Начало работы](user/start.md) — первый вход, интерфейс, первый запрос
- [Чат с моделью](user/chat.md) — диалог, история, параметры ответа
- [Выбор модели](user/choose_model.md) — какую модель выбрать и зачем
- [База знаний (RAG)](user/rag_user.md) — подключить свои документы, построить индекс
- [Продвинутые возможности](user/advanced.md) — параметры модели, несколько RAG индексов, агенты

---

## 🔧 Администратор

Вы разворачиваете, настраиваете и обслуживаете систему. Устанавливаете зависимости, управляете конфигурацией, следите за работой сервисов.

- [Быстрый старт](admin/getting_started.md) — установка и первый запуск
- [Установка](admin/installation.md) — install.ps1, зависимости, Docker
- [Конфигурация](admin/configuration.md) — config.json, .env, приоритеты
- [Запуск и остановка](admin/run_stop.md) — start.ps1, stop.ps1, автозапуск
- [Модели и бэкенды](admin/backends.md) — Foundry, llama.cpp, HuggingFace, Ollama, LM Studio
- [RAG — индексы и профили](admin/rag_admin.md) — построение, хранение, переключение
- [Мониторинг и логи](admin/monitoring.md) — логи, health check, диагностика
- [Telegram боты](admin/telegram_bots.md) — admin bot, helpdesk bot

---

## 💻 Разработчик

Вы расширяете систему: пишете агентов, MCP серверы, интегрируете через API, работаете с кодом.

- [Архитектура](dev/architecture.md) — структура кода, паттерны, маршрутизация
- [API Reference](dev/api_reference.md) — все REST endpoints
- [Система RAG](dev/rag_system.md) — FAISS, индексация, поиск
- [Агенты](dev/agents.md) — создание AI агентов
- [MCP серверы](dev/mcp_agent.md) — STDIO, HTTPS, PowerShell
- [SDK](dev/sdk.md) — Python SDK для интеграции
- [Утилиты](dev/utils.md) — src/utils, вспомогательные модули
- [CI/CD](dev/cicd_docs.md) — GitHub Actions, MkDocs деплой

---

## 🛡️ QA / Тестирование

Вы тестируете систему: пишете и запускаете тесты, проверяете качество.

- [Стратегия тестирования](qa/strategy.md)
- [Запуск тестов](qa/running.md)
- [Юнит-тесты](qa/unit.md)
- [Интеграционные тесты](qa/integration.md)
- [Тесты агентов](qa/agents.md)
