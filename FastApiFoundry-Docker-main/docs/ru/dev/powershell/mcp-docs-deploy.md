# docs_deploy_mcp.py

**Файл:** `mcp/src/servers/docs_deploy_mcp.py`  
**Протокол:** MCP STDIO  
**Версия:** 0.6.1

## Назначение

MCP сервер для деплоя MkDocs документации на FTP. Загружает собранные файлы из `site/ru/` и `site/en/` на удалённый сервер.

## Workflow

```
mkdocs build  →  site/ генерируется локально
docs_deploy_ru / docs_deploy_en  →  загрузка на FTP
```

## Инструменты

| Инструмент | Описание |
|---|---|
| `docs_deploy_ru` | Загрузить `site/ru/` на FTP |
| `docs_deploy_en` | Загрузить `site/en/` на FTP |
| `docs_deploy_all` | Загрузить оба языка |
| `docs_build_and_deploy` | Собрать (`mkdocs build`) и загрузить |
| `docs_status` | Проверить состояние удалённых директорий |

## Переменные окружения

| Переменная | Описание |
|---|---|
| `FTP_HOST` | Хост FTP сервера |
| `FTP_USER` | Имя пользователя |
| `FTP_PASSWORD` | Пароль |
| `FTP_PORT` | Порт (по умолчанию: 21) |
| `FTP_DOCS_RU` | Удалённый путь для русской документации |
| `FTP_DOCS_EN` | Удалённый путь для английской документации |

## Запуск

```powershell
venv\Scripts\python.exe mcp/src/servers/docs_deploy_mcp.py
```
