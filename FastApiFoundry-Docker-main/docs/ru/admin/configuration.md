# Конфигурация

Подробное описание конфигурации системы для администратора.

Полная справка по всем параметрам: [Конфигурация — справочник](../user/configuration.md)

---

## Главное правило

> **Секреты → `.env`**
> **Всё остальное → `config.json`**

---

## Ключевые настройки для администратора

### Порт и хост

```json
{
  "fastapi_server": {
    "host": "0.0.0.0",
    "port": 9696,
    "mode": "prod"
  }
}
```

- `host: "0.0.0.0"` — доступен из сети (не только localhost)
- `mode: "prod"` — без hot-reload, для production

### Параметры генерации по умолчанию

```json
{
  "defaults": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

Применяются ко всем бэкендам (Foundry, HuggingFace, llama.cpp, Ollama, LM Studio).
Клиент может переопределить их в теле запроса.
Подробнее: [Параметры генерации](generation_defaults.md)

### Автозапуск модели

```json
{
  "foundry_ai": {
    "auto_load_default": true,
    "default_model": "qwen3-0.6b-generic-cpu:4"
  }
}
```

### RAG

```json
{
  "rag_system": {
    "enabled": true,
    "index_dir": "~/.aiassistant/rag/default_index"
  }
}
```

### Перевод запросов к модели

```json
{
  "translator": {
    "enabled": false,
    "default_provider": "mymemory"
  }
}
```

Флаг `translate_model_dialog=true` в запросе включает перевод для отдельного запроса независимо от глобального конфига.
Подробнее: [Перевод запросов](translation.md)

### Безопасность

```json
{
  "security": {
    "api_key": "ваш_секретный_ключ"
  }
}
```

При заданном `api_key` все запросы к API должны содержать заголовок `X-API-Key`.

---

## Редактирование через веб-интерфейс

**Settings** → поля формы → **Save All**

Или прямое редактирование файлов: **Editor** → вкладка `config.json` / `.env`

---

## Резервное копирование

```powershell
Copy-Item config.json config.json.bak
Copy-Item .env .env.bak
```

Или через UI: **Settings** → **Export** (включает все секреты из `.env`).

!!! danger "Файл экспорта содержит секреты"
    Не передавайте файл экспорта третьим лицам и не коммитьте в git.
