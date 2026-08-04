# Пайплайн сборки документации (doc.ps1)

## Что делает doc.ps1

`doc.ps1` — точка входа для полной пересборки документации.
Запускается вручную или из CI. Результат — актуальный `site/` и запущенный MkDocs сервер.

## Порядок обработки

```
doc.ps1
  │
  ├─[1] Остановить предыдущий MkDocs (если занят порт)
  │      └─ Stop-PortProcess -Port <docs_server.port из config.json>
  │
  ├─[2] Генерация документации по PowerShell скриптам
  │      └─ scripts\Create-Doc\Generate-PsDocs.ps1
  │           └─ читает: *.ps1, scripts/**/*.ps1, install/*.ps1, mcp/**/*.ps1, tests/**/*.ps1
  │           └─ пишет:  docs/ru/dev/powershell/*.md
  │
  ├─[3] Генерация Code Reference по Python коду
  │      └─ scripts\Create-Doc\Generate-CodeReference.py
  │           └─ читает: src/**/*.py (docstrings)
  │           └─ пишет:  docs/ru/dev/code/src/**/*.md
  │                      обновляет nav в mkdocs.yml (секция AUTO_GENERATED)
  │
  ├─[4] Генерация полного API Reference
  │      └─ scripts\Create-Doc\Generate-ApiReference.py
  │           └─ читает: src/api/endpoints/*.py
  │           └─ пишет:  docs/ru/dev/api_full.md
  │
  ├─[5] Удалить site/ полностью
  │      └─ Remove-Item site/ -Recurse -Force
  │
  ├─[6] Пересборка MkDocs
  │      └─ python -m mkdocs build -f mkdocs.yml
  │           └─ читает: docs/ru/**/*.md + mkdocs.yml
  │           └─ пишет:  site/**  (статический HTML)
  │
  ├─[7] Запустить MkDocs сервер
  │      └─ python -m mkdocs serve --dev-addr 0.0.0.0:<port>
  │
  └─[8] Открыть браузер
         └─ Start-Process http://localhost:<port>
```

## Источники → выходные файлы

| Источник | Генератор | Выход |
|---|---|---|
| `*.ps1`, `scripts/**/*.ps1`, `install/*.ps1`, `mcp/**/*.ps1`, `tests/**/*.ps1` | `scripts/Create-Doc/Generate-PsDocs.ps1` | `docs/ru/dev/powershell/*.md` |
| `src/**/*.py` (docstrings) | `scripts/Create-Doc/Generate-CodeReference.py` | `docs/ru/dev/code/src/**/*.md` |
| `src/api/endpoints/*.py` | `scripts/Create-Doc/Generate-ApiReference.py` | `docs/ru/dev/api_full.md` |
| `docs/ru/**/*.md` + `mkdocs.yml` | `mkdocs build` | `site/**` (HTML) |

## Конфигурация

Порт сервера документации читается из `config.json`:

```json
{
  "docs_server": {
    "port": 9697
  }
}
```

## Что НЕ трогает скрипт

- Вручную написанные страницы в `docs/ru/` — они только читаются MkDocs, не перезаписываются
- `config.json`, `.env`, исходный код `src/`
- Файлы с суффиксом `~` (помечены как архивные)

## Запуск

```powershell
powershell -ExecutionPolicy Bypass -File .\doc.ps1
```

## Добавление нового параметра (план)

Сейчас скрипт всегда пересобирает всё. Планируемый параметр `-Target`:

| Значение | Что пересобирается |
|---|---|
| `all` | всё (текущее поведение) |
| `ps` | только PowerShell docs → `site/` |
| `code` | только Code Reference → `site/` |
| `site` | только `mkdocs build` без генерации |

!!! note "Текущий статус"
    Параметр `-Target` пока не реализован. Скрипт всегда выполняет полный цикл.
