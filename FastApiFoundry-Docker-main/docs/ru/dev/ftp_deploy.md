# Деплой документации на FTP

Документация FastAPI Foundry может публиковаться на собственный сервер через FTP.
Для этого используется MCP сервер `docs_deploy_mcp.py`.

---

## Структура на сервере

Скрипт загружает содержимое `site/ru/` и `site/en/` напрямую в пути, заданные в `.env`.
Никакой дополнительной вложенности не создаётся.

Пример значений в `.env` и результирующая структура на сервере:

```env
FTP_DOCS_RU=/domains/davidka.net/public_html/ai_assist/site/ru
FTP_DOCS_EN=/domains/davidka.net/public_html/ai_assist/site/en
```

```
/domains/davidka.net/public_html/ai_assist/
└── site/
    ├── ru/     ← сюда заливается site/ru/ (FTP_DOCS_RU)
    └── en/     ← сюда заливается site/en/ (FTP_DOCS_EN)
```

Документация доступна по адресам:

```
http://davidka.net/ai_assist/site/ru/
http://davidka.net/ai_assist/site/en/
```

!!! warning "Пути на сервере"
    `FTP_DOCS_RU` и `FTP_DOCS_EN` — это пути на FTP-сервере, куда будет залито
    содержимое `site/ru/` и `site/en/` соответственно. Значения можно
    задать любые под вашу структуру сервера.

---

## Настройка

### 1. Заполнить `.env`

```env
FTP_HOST=141.136.34.182
FTP_USER=<ваш_логин>
FTP_PASSWORD=<ваш_пароль>
FTP_PORT=21
FTP_DOCS_RU=/domains/davidka.net/public_html/ai_assist/site/ru
FTP_DOCS_EN=/domains/davidka.net/public_html/ai_assist/site/en
```

### 2. Запустить MCP сервер

```bash
POST /api/v1/mcp-powershell/servers/docs-deploy/start
```

Или вручную:

```powershell
python ./mcp/src/servers/docs_deploy_mcp.py
```

---

## Сценарии деплоя

### Загрузить только русскую документацию

```bash
POST /api/v1/mcp-powershell/servers/docs-deploy/start
```

Затем через MCP агента:

```json
POST /api/v1/agent/run
{
  "agent": "mcp",
  "message": "Задеплой русскую документацию на FTP",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

Агент вызовет инструмент `docs_deploy_ru` — загрузит `site/ru/` в `FTP_DOCS_RU`.

### Загрузить только английскую документацию

```json
{
  "agent": "mcp",
  "message": "Задеплой английскую документацию на FTP",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

Агент вызовет `docs_deploy_en` — загрузит `site/en/` в `FTP_DOCS_EN`.

### Собрать и задеплоить всё

```json
{
  "agent": "mcp",
  "message": "Собери документацию mkdocs и задеплой оба языка на FTP",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

Агент вызовет `docs_build_and_deploy` с `lang=all`:
1. `mkdocs build` — собирает `site/`
2. Загружает `site/ru/` → `FTP_DOCS_RU`
3. Загружает `site/en/` → `FTP_DOCS_EN`

### Проверить статус удалённых директорий

```json
{
  "agent": "mcp",
  "message": "Проверь статус документации на FTP",
  "model": "qwen3-0.6b-generic-cpu:4"
}
```

Агент вызовет `docs_status` — покажет количество файлов в каждой директории.

---

## Прямые вызовы API

Без агента — напрямую через MCP API:

```bash
# Запустить сервер
POST /api/v1/mcp-powershell/servers/docs-deploy/start

# Статус сервера
GET /api/v1/mcp-powershell/servers/docs-deploy/status

# Остановить сервер
POST /api/v1/mcp-powershell/servers/docs-deploy/stop
```

---

## Инструменты MCP сервера

| Инструмент | Параметры | Описание |
|---|---|---|
| `docs_deploy_ru` | — | Загрузить `site/ru/` → `FTP_DOCS_RU` |
| `docs_deploy_en` | — | Загрузить `site/en/` → `FTP_DOCS_EN` |
| `docs_deploy_all` | — | Загрузить оба языка |
| `docs_build_and_deploy` | `lang`: `ru`/`en`/`all` | `mkdocs build` + загрузка |
| `docs_status` | — | Проверить удалённые директории |

---

## Workflow: полный цикл публикации

```
1. Редактируем docs/ru/ или docs/en/
        │
        ▼
2. mkdocs build
   (или docs_build_and_deploy сделает это автоматически)
        │
        ▼
3. site/ru/  и  site/en/  готовы
        │
        ├──▶ docs_deploy_ru  →  FTP_DOCS_RU
        └──▶ docs_deploy_en  →  FTP_DOCS_EN
        │
        ▼
4. Документация доступна на сервере
   http://davidka.net/ai_assist/site/ru/
   http://davidka.net/ai_assist/site/en/
```

---

## Переменные окружения

| Переменная | Обязательно | Описание |
|---|---|---|
| `FTP_HOST` | ✅ | Хост FTP сервера |
| `FTP_USER` | ✅ | Логин FTP |
| `FTP_PASSWORD` | ✅ | Пароль FTP |
| `FTP_PORT` | — | Порт (default: `21`) |
| `FTP_DOCS_RU` | ✅ | Удалённый путь для русской документации |
| `FTP_DOCS_EN` | ✅ | Удалённый путь для английской документации |

---

## Файлы

| Файл | Назначение |
|---|---|
| `mcp/src/servers/docs_deploy_mcp.py` | MCP сервер деплоя |
| `mcp/settings.json` → `docs-deploy` | Конфигурация сервера |
| `.env` | Учётные данные FTP и пути |
| `site/` | Собранная документация (после `mkdocs build`) |

---

## Локальная сборка перед деплоем

```powershell
# Собрать документацию
venv\Scripts\python.exe -m mkdocs build

# Проверить что site/ создан
ls site/ru/
ls site/en/

# Задеплоить
python ./mcp/src/servers/docs_deploy_mcp.py
```

!!! warning "Сначала mkdocs build"
    `docs_deploy_ru` и `docs_deploy_en` загружают содержимое `site/ru/` и `site/en/`.
    Если `site/` не существует — деплой завершится ошибкой.
    Используйте `docs_build_and_deploy` чтобы сборка и деплой выполнились за один шаг.
