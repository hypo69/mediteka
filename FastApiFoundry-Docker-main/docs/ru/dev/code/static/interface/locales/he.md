# He

**Файл:** `static/interface/locales/he.json`  
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
| `loading` | `dict` | объект: `title`, `init`, `config`, `i18n`, `services` |
| `providers` | `dict` | объект: `local_key_title`, `local_key_hint`, `local_key_current`, `local_key_copy_hint`, `local_key_generate` |
| `common` | `dict` | объект: `notes`, `loading`, `error`, `success`, `cancel` |

**Полная структура:**

```json
{
  "banner": {
    "no_model": "אין מודל טעון"
  },
  "nav": {
    "connecting": "מתחבר...",
    "connected": "מחובר",
    "api_only": "API בלבד",
    "error": "שגיאה"
  },
  "tabs": {
    "chat": "צ'אט",
    "models": "מודלים",
    "foundry": "Foundry",
    "hf": "HuggingFace",
    "llama": "llama.cpp",
    "ollama": "Ollama",
    "rag": "RAG",
    "settings": "הגדרות",
    "editor": "עורך",
    "mcp": "שרתי MCP",
    "agent": "סוכן",
    "providers": "מפתחות API",
    "support": "תמיכה",
    "logs": "לוגים",
    "docs": "תיעוד API"
  },
  "chat": {
    "title": "צ'אט AI",
    "clear": "נקה",
    "placeholder": "הקלד הודעה...",
    "send": "שלח",
    "stop": "עצור",
    "settings": "הגדרות צ'אט",
    "model": "מודל",
    "model_auto": "בחירה אוטומטית",
    "model_hint": "המודל הנבחר יישמר כברירת מחדל",
    "temperature": "טמפרטורה",
    "max_tokens": "מקסימום טוקנים",
    "use_rag": "השתמש בהקשר RAG",
    "start_prompt": "התחל שיחה עם AI",
    "select_model_warning": "בחר מודל בהגדרות הצ'אט",
    "generating": "מייצר תשובה...",
    "how_models_work": "כיצד עובדים המודלים בצ'אט",
    "models_list_hint": "הרשימה מציגה מודלים ממטמונים מקומיים: Foundry מ-<code>/foundry/models/cached</code>, HuggingFace מ-<code>/hf/models</code>, llama.cpp מ-<code>/llama/models</code>.",
    "models_switch_hint": "בעת החלפת מודל, המודלים הפעילים מוסרים מהזיכרון ולאחר מכן המודל הנבחר נטען.",
    "models_add_hint": "להוספה: השתמש בלשוניות <strong>Foundry</strong>, <strong>HuggingFace</strong> או <strong>llama.cpp</strong>.",
    "cli_title": "טעינה דרך CLI",
    "hf_via_ui": "קבל מודל HuggingFace דרך הממשק",
    "hf_step1": "פתח את לשונית <strong>HuggingFace</strong>.",
    "hf_step2": "למודלים מוגבלים הגדר טוקן ב-<strong>Settings &rarr; HuggingFace</strong>.",
    "hf_step3": "הזן <code>model_id</code> ולחץ <strong>Download</strong>.",
    "hf_step4": "לחץ Refresh ב-<strong>Downloaded Locally</strong> — המודל יופיע ברשימה.",
    "tokens": "טוק"
  },
  "models": {
    "title": "מודלים מחוברים",
    "available": "מודלים זמינים",
    "add": "הוסף מודל",
    "refresh": "רענן",
    "no_models": "אין מודלים מחוברים. השתמש בלשונית Foundry.",
    "grouped_hint": "מקובץ לפי ספק",
    "use_in_chat": "השתמש בצ'אט",
    "unload": "הסר מהזיכרון"
  },
  "foundry": {
    "service": "שירות Foundry",
    "port": "פורט",
    "unknown": "לא ידוע",
    "start": "הפעל Foundry",
    "stop": "עצור Foundry",
    "check_status": "בדוק סטטוס",
    "status_placeholder": "סטטוס השירות יוצג כאן",
    "logs": "לוגי Foundry",
    "logs_clear": "נקה",
    "logs_placeholder": "לוגי Foundry יופיעו כאן",
    "available_models": "מודלים זמינים",
    "list_models": "רשימת מודלים",
    "list_models_download": "רשימת מודלים להורדה",
    "include_gpu": "כלול מודלי GPU",
    "models_placeholder": "לחץ על \"רשימת מודלים\" לצפייה",
    "downloaded": "מודלים שהורדו",
    "refresh_downloaded": "רענן מורדים",
    "downloaded_hint": "ניתן לטעון רק מודלים שכבר הורדו למטמון המקומי.",
    "downloaded_placeholder": "
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
