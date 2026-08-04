# Ru

**Файл:** `static/interface/locales/ru.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `banner` | `dict` | объект: `no_model` |
| `nav` | `dict` | объект: `connecting`, `connected`, `api_only`, `error` |
| `tabs` | `dict` | объект: `chat`, `models`, `foundry`, `hf`, `llama` |
| `chat` | `dict` | объект: `title`, `clear`, `placeholder`, `send`, `stop` |
| `models` | `dict` | объект: `title`, `available`, `add`, `refresh`, `no_models` |
| `foundry` | `dict` | объект: `service`, `port`, `unknown`, `start`, `stop` |
| `rag` | `dict` | объект: `active_base`, `bases`, `refresh`, `no_bases`, `build_title` |
| `settings` | `dict` | объект: `title`, `system_status`, `export`, `import`, `reload` |
| `editor` | `dict` | объект: `env_title`, `env_subtitle`, `config_title`, `config_subtitle`, `reload` |
| `logs` | `dict` | объект: `title`, `refresh`, `clear`, `filter`, `filter_all` |
| `llama` | `dict` | объект: `gguf_title`, `gguf_what`, `gguf_where_title`, `gguf_hf_title`, `gguf_hf_hint` |
| `agent` | `dict` | объект: `title`, `settings`, `select`, `tools`, `run` |
| `loading` | `dict` | объект: `title`, `init`, `config`, `i18n`, `services` |
| `providers` | `dict` | объект: `local_key_title`, `local_key_hint`, `local_key_current`, `local_key_copy_hint`, `local_key_generate` |
| `hitl` | `dict` | объект: `title`, `message`, `tool`, `arguments`, `allow` |
| `common` | `dict` | объект: `notes`, `loading`, `error`, `success`, `cancel` |

**Полная структура:**

```json
{
  "banner": {
    "no_model": "Модель не загружена"
  },
  "nav": {
    "connecting": "Подключение...",
    "connected": "Подключено",
    "api_only": "Только API",
    "error": "Ошибка"
  },
  "tabs": {
    "chat": "Чат",
    "models": "Модели",
    "foundry": "Foundry",
    "hf": "HuggingFace",
    "llama": "llama.cpp",
    "ollama": "Ollama",
    "rag": "RAG",
    "settings": "Настройки",
    "editor": "Редактор",
    "mcp": "MCP Серверы",
    "agent": "Агент",
    "providers": "API Ключи",
    "support": "Поддержка",
    "logs": "Логи",
    "docs": "Документация API"
  },
  "chat": {
    "title": "AI Чат",
    "clear": "Очистить",
    "placeholder": "Введите сообщение...",
    "send": "Отправить",
    "stop": "Стоп",
    "settings": "Настройки чата",
    "model": "Модель",
    "model_auto": "Авто-выбор",
    "model_hint": "Выбранная модель сохранится как модель по умолчанию",
    "temperature": "Температура",
    "max_tokens": "Макс. токенов",
    "use_rag": "Использовать RAG контекст",
    "start_prompt": "Начните разговор с AI",
    "select_model_warning": "Выберите модель в настройках чата",
    "generating": "Генерация ответа...",
    "how_models_work": "Как работают модели в чате",
    "models_list_hint": "Список показывает модели из локальных кэшей: Foundry из <code>/foundry/models/cached</code>, HuggingFace из <code>/hf/models</code>, llama.cpp из <code>/llama/models</code> (.gguf в <code>~/.models</code>).",
    "models_switch_hint": "При переключении модели выгружаются активные модели (Foundry unload + HF unload) и останавливается llama.cpp, затем загружается выбранная.",
    "models_add_hint": "Для добавления: вкладки <strong>Foundry</strong>, <strong>HuggingFace</strong> или <strong>llama.cpp</strong>. Для llama.cpp скопируйте .gguf в <code>~/.models</code> и нажмите Refresh.",
    "cli_title": "Загрузка через CLI (в обход интерфейса)",
    "hf_via_ui": "Получить HuggingFace модель через интерфейс",
    "hf_step1": "Откройте вкладку <strong>HuggingFace</strong>.",
    "hf_step2": "Для gated моделей задайте токен в <strong>Settings &rarr; HuggingFace</strong> и примите лицензию.",
    "hf_step3": "Введите <code>model_id</code> (например <code>google/gemma-2b</code>) и нажмите <strong>Download</strong>.",
    "hf_step4": "Нажмите Refresh в <strong>Downloaded Locally</strong> — модель появится в списке чата.",
    "tokens": "ток"
  },
  "models": {
    "title": "Активные модели",
    "available": "Доступные модели",
    "add": "Добавить модель",
    "refresh": "Обновить",
    "no_models": "Нет загруженных моделей. Загрузите модель из раздела ниже.",
    "grouped_hint": "Сгруппировано по провайдерам",
    "use_in_chat": "Использовать в чате",
    "unload": "Выгрузить"
  },
  "foundry": {
    "service": "Сервис Foundry",
    "port": "Порт",
    "unknown": "Неизвестно",
    "start": "Запустить Foundry",
    "stop": "Остановить Foundry",
    "check_status": "Проверить статус",
    "status_placeholder": "Статус сервиса отобразится здесь"
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
