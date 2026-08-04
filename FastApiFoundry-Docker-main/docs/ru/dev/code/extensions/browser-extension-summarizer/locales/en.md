# En

**Файл:** `extensions/browser-extension-summarizer/locales/en.json`  
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
    "title": "🤖 AI Assistant",
    "loading": "Loading…",
    "no_provider": "No provider configured. Open Providers & Models to set up.",
    "provider": "Provider",
    "model": "Model",
    "open_chat": "💬 Chat",
    "open_providers": "⚙️ Providers & Models",
    "hint": "Right-click any page → <strong>Summarise</strong> → choose mode."
  },
  "chat": {
    "title": "Chat",
    "model_label": "Model",
    "model_loading": "Loading…",
    "no_models": "No models configured",
    "clear": "Clear chat",
    "send": "Send",
    "placeholder": "Type a message…",
    "input_hint": "Enter to send · Shift+Enter for new line",
    "start_prompt": "Start a conversation",
    "no_model_error": "Select a model first.",
    "send_to_rag": "📚 RAG",
    "no_key_error": "No API key. Select a configured model."
  },
  "settings": {
    "server_url": "Server URL",
    "model": "Model",
    "model_hint": "Use prefix: foundry::model-id · hf::model-id · ollama::model-name",
    "load_models": "Load",
    "load_models_hint": "— load models first —",
    "save": "💾 Save",
    "test": "🔍 Test connection",
    "no_url": "Enter server URL first"
  },
  "providers": {
    "title": "Providers & Models",
    "tab_providers": "🔑 Providers & Models",
    "tab_summarizer": "🤖 Summarizer",
    "import": "📂 Import",
    "export": "💾 Export",
    "api_keys": "API Keys",
    "add_key": "+ Add key",
    "base_url": "Base URL",
    "load_models": "Load models",
    "load_all_models": "Load all models",
    "set_active": "Set Active",
    "active": "✓ Active",
    "not_active": "Not active",
    "no_model": "— no model —",
    "add_model_placeholder": "Add model ID manually…",
    "add_model": "Add",
    "summary_lang": "🌐 Summary language",
    "summary_provider": "🤖 Provider for summarization",
    "summary_provider_hint": "Override the active provider specifically for summarization",
    "summary_model": "📌 Model for summarization",
    "summary_model_hint": "Override the active model specifically for summarization",
    "use_active_provider": "— use active provider —",
    "use_active_model": "— use active model —",
    "loading_models": "Loading…",
    "loading_all_models": "Loading all models…",
    "models_loaded": "models loaded",
    "no_models_returned": "No models returned",
    "load_select_first": "Load models and select one first"
  },
  "debug": {
    "title": "Server Debug",
    "server_url": "Server URL",
    "check": "Check connection",
    "quick_tests": "Quick endpoint tests",
    "custom_request": "Custom request",
    "chat_test": "Chat test",
    "model": "Model",
    "prompt": "Prompt",
    "load_models": "Load models",
    "send": "Send",
    "send_chat": "Send chat request",
    "response": "Response",
    "response_placeholder": "Response will appear here…",
    "copy": "Copy",
    "clear": "Clear"
  },
  "hint": {
    "title": "Connect to FastAPI Foundry (local server)",
    "desc": "FastAPI Foundry runs a local OpenAI-compatible API. Add
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
