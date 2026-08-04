# Ru

**Файл:** `extensions/browser-extension-summarizer/locales/ru.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `popup` | `dict` | объект: `title`, `loading`, `no_provider`, `provider`, `model` |
| `chat` | `dict` | объект: `title`, `model_label`, `model_loading`, `no_models`, `clear` |
| `settings` | `dict` | объект: `server_url`, `model`, `model_hint`, `load_models`, `load_models_hint` |
| `providers` | `dict` | объект: `title`, `tab_providers`, `tab_summarizer`, `import`, `export` |
| `debug` | `dict` | объект: `title`, `server_url`, `check`, `quick_tests`, `custom_request` |
| `hint` | `dict` | объект: `title`, `desc`, `step1`, `step3`, `step4` |
| `rag` | `dict` | объект: `title`, `empty`, `select_all`, `deselect_all`, `delete_selected` |
| `common` | `dict` | объект: `loading`, `error`, `success`, `cancel`, `close` |

**Полная структура:**

```json
{
  "popup": {
    "title": "🤖 AI Ассистент",
    "loading": "Загрузка…",
    "no_provider": "Провайдер не настроен. Откройте «Провайдеры и модели».",
    "provider": "Провайдер",
    "model": "Модель",
    "open_chat": "💬 Чат",
    "open_providers": "⚙️ Провайдеры и модели",
    "hint": "Правый клик на странице → <strong>Суммаризировать</strong> → выберите режим."
  },
  "chat": {
    "title": "Чат",
    "model_label": "Модель",
    "model_loading": "Загрузка…",
    "no_models": "Модели не настроены",
    "clear": "Очистить чат",
    "send": "Отправить",
    "placeholder": "Введите сообщение…",
    "input_hint": "Enter — отправить · Shift+Enter — новая строка",
    "start_prompt": "Начните разговор",
    "no_model_error": "Сначала выберите модель.",
    "send_to_rag": "📚 В RAG",
    "no_key_error": "Нет API ключа. Выберите настроенную модель."
  },
  "settings": {
    "server_url": "URL сервера",
    "model": "Модель",
    "model_hint": "Префикс: foundry::model-id · hf::model-id · ollama::model-name",
    "load_models": "Загрузить",
    "load_models_hint": "— сначала загрузите модели —",
    "save": "💾 Сохранить",
    "test": "🔍 Проверить подключение",
    "no_url": "Укажите URL сервера"
  },
  "providers": {
    "title": "Провайдеры и модели",
    "tab_providers": "🔑 Провайдеры и модели",
    "tab_summarizer": "🤖 Суммаризатор",
    "import": "📂 Импорт",
    "export": "💾 Экспорт",
    "api_keys": "API ключи",
    "add_key": "+ Добавить ключ",
    "base_url": "Базовый URL",
    "load_models": "Загрузить модели",
    "load_all_models": "Загрузить все модели",
    "set_active": "Сделать активным",
    "active": "✓ Активен",
    "not_active": "Не активен",
    "no_model": "— нет модели —",
    "add_model_placeholder": "Добавить ID модели вручную…",
    "add_model": "Добавить",
    "summary_lang": "🌐 Язык суммаризации",
    "summary_provider": "🤖 Провайдер для суммаризации",
    "summary_provider_hint": "Переопределить активный провайдер для суммаризации",
    "summary_model": "📌 Модель для суммаризации",
    "summary_model_hint": "Переопределить активную модель для суммаризации",
    "use_active_provider": "— использовать активный провайдер —",
    "use_active_model": "— использовать активную модель —",
    "loading_models": "Загрузка…",
    "loading_all_models": "Загрузка всех моделей…",
    "models_loaded": "моделей загружено",
    "no_models_returned": "Модели не получены",
    "load_select_first": "Загрузите модели и выберите одну"
  },
  "debug": {
    "title": "Отладка сервера",
    "server_url": "URL сервера",
    "check": "Проверить подключение",
    "quick_tests": "Быстрые тесты endpoint",
    "custom_request": "Произвольный запрос",
    "chat_test": "Тест чата",
    "model": "Модель",
    "prompt": "Запрос",
    "load_models": "Загрузить модели",
    "send": "Отправить",
    "send_chat": "Отправить чат-запрос",
    "response": "Ответ",
    "response_placeholder": "Ответ появится здесь…",
    "copy": "Копировать",
    "clear": "Очистить"
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
