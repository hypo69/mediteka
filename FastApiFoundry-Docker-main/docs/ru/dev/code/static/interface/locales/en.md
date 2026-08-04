# En

**Файл:** `static/interface/locales/en.json`  
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
| `common` | `dict` | объект: `notes`, `loading`, `error`, `success`, `cancel` |

**Полная структура:**

```json
{
  "banner": {
    "no_model": "No model loaded"
  },
  "nav": {
    "connecting": "Connecting...",
    "connected": "Connected",
    "api_only": "API Only",
    "error": "Error"
  },
  "tabs": {
    "chat": "Chat",
    "models": "Models",
    "foundry": "Foundry",
    "hf": "HuggingFace",
    "llama": "llama.cpp",
    "ollama": "Ollama",
    "rag": "RAG",
    "settings": "Settings",
    "editor": "Editor",
    "mcp": "MCP Servers",
    "agent": "Agent",
    "providers": "API Keys",
    "support": "Support",
    "logs": "Logs",
    "docs": "API Documentation"
  },
  "chat": {
    "title": "AI Chat",
    "clear": "Clear",
    "placeholder": "Type your message...",
    "send": "Send",
    "stop": "Stop",
    "settings": "Chat Settings",
    "model": "Model",
    "model_auto": "Auto-select",
    "model_hint": "Selected model will be saved as default",
    "temperature": "Temperature",
    "max_tokens": "Max Tokens",
    "use_rag": "Use RAG Context",
    "start_prompt": "Start a conversation with AI",
    "select_model_warning": "Please select a model in Chat Settings",
    "generating": "Generating response...",
    "how_models_work": "How models work in chat",
    "models_list_hint": "List shows models from local caches: Foundry from <code>/foundry/models/cached</code>, HuggingFace from <code>/hf/models</code>, llama.cpp from <code>/llama/models</code> (.gguf in <code>~/.models</code>).",
    "models_switch_hint": "On model switch, active models are unloaded (Foundry unload + HF unload) and llama.cpp is stopped if needed, then the selected model is loaded.",
    "models_add_hint": "To add: use <strong>Foundry</strong>, <strong>HuggingFace</strong> or <strong>llama.cpp</strong> tabs. For llama.cpp copy .gguf to <code>~/.models</code> then Refresh.",
    "cli_title": "Load via CLI (bypassing UI)",
    "hf_via_ui": "Get HuggingFace model via UI",
    "hf_step1": "Open <strong>HuggingFace</strong> tab.",
    "hf_step2": "For gated models set token in <strong>Settings &rarr; HuggingFace</strong> and accept license.",
    "hf_step3": "Enter <code>model_id</code> (e.g. <code>google/gemma-2b</code>) and click <strong>Download</strong>.",
    "hf_step4": "Click Refresh in <strong>Downloaded Locally</strong> — model appears in chat list.",
    "tokens": "tok"
  },
  "models": {
    "title": "Active Models",
    "available": "Available Models",
    "add": "Add Model",
    "refresh": "Refresh",
    "no_models": "No models loaded. Load a model from the Available section below.",
    "grouped_hint": "Grouped by provider",
    "use_in_chat": "Use in Chat",
    "unload": "Unload"
  },
  "foundry": {
    "service": "Foundry Service",
    "port": "Port",
    "unknown": "Unknown",
    "start": "Start Foundry",
    "stop": "Stop Foundry",
    "check_status": "Check Status",
    "status_placeholder": "Service status will appear here",
    "logs": "Foundry Logs",
    "logs_clear": "Clear",
    "logs_placeholder": "Foundry logs will appear here",
    "available_models":
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
