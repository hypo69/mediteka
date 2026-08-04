# Сборка документации

> 👉 Исходный код: **https://github.com/hypo69/FastApiFoundry-Docker**
> 📚 Онлайн: **https://davidka.net/ai_assist/site/**

---

## Как устроена документация

Документация проекта — это MkDocs-сайт, который собирается из трёх источников одновременно:

```
src/**/*.py          → mkdocstrings   → Python API Reference
extensions/**/*.js   → TypeDoc        → JS Browser Extension docs
mcp/src/servers/*.ps1 → PlatyPS       → PowerShell MCP docs
docs/ru/**/*.md      → MkDocs         → основной контент
          │
          ▼
      mkdocs build
          │
          ▼
       site/         ← статический HTML
```

Конфигурация сборки: `mkdocs.yml` в корне проекта.
Зависимости: `docs/requirements.txt`.

---

## Мультиязычность

!!! warning "Текущее состояние"
    Основной язык документации — **русский**. Английская версия (`docs/en/`) существует,
    но заполнена частично. Иврит и другие языки в структуре `docs/` отсутствуют.
    Плагин `mkdocs-static-i18n` **не подключён** — языкового переключателя на сайте нет.

Структура директорий:

```
docs/
├── ru/              ← основная документация (docs_dir в mkdocs.yml)
│   ├── index.md
│   ├── about.md
│   ├── user/
│   └── dev/
└── en/              ← английская документация (частично заполнена)
    └── index.md
```

### Как собирается сайт

`mkdocs.yml` настроен на `docs_dir: docs/ru` — весь контент берётся из русской директории.
`theme.language: ru` — интерфейс темы (поиск, кнопки) на русском.

```
mkdocs build
  └─ docs/ru/ → site/   (единственный язык)
```

### Как добавить языковой переключатель

Для полноценной мультиязычности нужно:

1. Установить плагин:
    ```
    pip install mkdocs-static-i18n
    ```
2. Добавить в `mkdocs.yml`:
    ```yaml
    plugins:
      - i18n:
          default_language: ru
          languages:
            en:
              name: English
              build: true
            he:
              name: עברית
              build: true
    ```
3. Создать зеркальные файлы в `docs/en/` и `docs/he/` с той же структурой путей.

!!! note "Fallback"
    Если страница есть в `docs/ru/`, но отсутствует в `docs/en/` — плагин использует
    русскую версию как fallback.

---

## Локальный сервер документации

### Быстрый запуск (рекомендуется)

`doc.ps1` — скрипт в корне проекта. Делает всё сам:

```
doc.ps1
  ├─ читает порт из config.json → docs_server.port (default: 9697)
  ├─ [порт занят] → убивает процесс на порту
  ├─ scripts\Create-Doc\Generate-PsDocs.ps1  (генерирует docs/ru/dev/powershell/)
  ├─ удаляет site/ (пересборка с нуля)
  ├─ mkdocs build  (генерирует site/)
  ├─ mkdocs serve  (запускает сервер в новом окне)
  ├─ ждёт готовности сервера (до 20 сек)
  └─ открывает браузер на http://localhost:9697
```

```powershell
powershell -ExecutionPolicy Bypass -File .\doc.ps1
```

Или через скрипт-обёртку:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart-mkdocs.ps1
```

### Только сервер (без пересборки)

Если нужен только live-preview с hot reload при редактировании `.md` файлов:

```powershell
venv\Scripts\python.exe -m mkdocs serve --dev-addr 0.0.0.0:9697
```

Сервер доступен на `http://localhost:9697`. При сохранении любого `.md` файла
страница автоматически перезагружается в браузере.

### Только сборка (без сервера)

Генерирует статический `site/` без запуска сервера:

```powershell
venv\Scripts\python.exe -m mkdocs build
```

Результат в `site/` — готов к деплою на любой веб-сервер или FTP.

### Порт сервера документации

Порт задаётся в `config.json`:

```json
{
  "docs_server": {
    "enabled": false,
    "port": 9697
  }
}
```

При `enabled: true` сервер документации запускается автоматически вместе с `start.ps1`.

---

## Устройство файла mkdocs.yml

`mkdocs.yml` — центральный файл конфигурации в корне проекта. Содержит восемь главных разделов:

```
mkdocs.yml
  ├─ метаданные сайта   ← site_name, site_url, docs_dir, site_dir
  ├─ theme              ← внешний вид, палитра, навигация
  ├─ plugins            ← расширения MkDocs
  ├─ nav                ← дерево страниц
  ├─ markdown_extensions ← синтаксис Markdown
  ├─ extra_javascript    ← подключение JS
  ├─ extra_css           ← подключение CSS
  └─ extra              ← переменные и соцсети
```

### Метаданные сайта

```yaml
site_name: AI Assistant
site_description: Оркестратор локальных AI моделей с единым REST API
site_author: hypo69
site_url: https://davidka.net/ai_assist/site/
site_dir: site
docs_dir: docs/ru
```

| Параметр | Назначение |
|---|---|
| `site_name` | Заголовок в браузере и шапке сайта |
| `site_url` | Канонический URL — используется в `sitemap.xml` и абсолютных ссылках |
| `docs_dir` | Откуда читаются `.md` файлы. `docs/ru` — выбор основного языка |
| `site_dir` | Куда складывается собранный HTML (`site/`) |

### theme

```yaml
theme:
  name: material
  language: ru
  logo: assets/icons/icon128.png
  favicon: assets/icons/icon48.png
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
```

`palette` — два объекта с `media` — браузер выбирает тему по системным настройкам, `toggle` даёт переключатель.

`features` — включаемые возможности темы:

| Feature | Что даёт |
|---|---|
| `navigation.tabs` | Верхняя панель вкладок (Главная / Пользователь / Разработчик) |
| `navigation.sections` | Группировка пунктов в боковом меню |
| `navigation.top` | Кнопка «наверх» при прокрутке |
| `search.suggest` | Автодополнение в поиске |
| `search.highlight` | Подсветка найденного текста на странице |
| `content.code.copy` | Кнопка копирования у каждого блока кода |

### plugins

```yaml
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [.]
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            members_order: source
            show_if_no_docstring: false
```

- `search` — встроенный полнотекстовый поиск, обязателен
- `mkdocstrings` — читает Python docstrings и вставляет их в страницы через директиву `:::`
  - `paths: [.]` — Python-модули ищутся от корня проекта
  - `docstring_style: google` — формат docstring (Args / Returns / Raises / Example)
  - `show_source: true` — показывать исходный код под документацией

### nav

```yaml
nav:
  - Главная:
    - Обзор: index.md
    - Смысл: about.md
  - Руководство пользователя:
    - Быстрый старт: user/getting_started.md
  - Для разработчиков:
    - Архитектура: dev/architecture.md
    - Code Reference (Python):
      - Foundry Client: dev/code/foundry_client.md
```

Дерево навигации сайта. Правила:

- Верхний уровень (`Главная`, `Руководство`) — вкладки в шапке (из-за `navigation.tabs`)
- Вложенные пункты — боковое меню
- Значение — путь к `.md` файлу **относительно `docs_dir`**
- Если `nav` не указан — MkDocs строит навигацию автоматически по структуре папок, но порядок непредсказуем

### markdown_extensions

```yaml
markdown_extensions:
  - admonition
  - pymdownx.highlight:
      anchor_linenums: true
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
```

Расширения синтаксиса Markdown. Все `pymdownx.*` — пакет PyMdown Extensions:

| Расширение | Что даёт | Пример в `.md` |
|---|---|---|
| `admonition` | Блоки предупреждений | `!!! note "..."` |
| `pymdownx.highlight` | Подсветка кода (PowerShell, JS, Python...) | ` ```powershell ` |
| `pymdownx.inlinehilite` | Подсветка инлайн-кода | `` `#!python x = 1` `` |
| `pymdownx.superfences` | Вложенные блоки, диаграммы Mermaid | ` ```mermaid ` |
| `pymdownx.tabbed` | Вкладки внутри страницы | `=== "Tab 1"` |
| `pymdownx.details` | Сворачиваемые блоки | `??? note "..."` |
| `pymdownx.emoji` | Эмодзи через имя | `:material-home:` |

### extra_javascript / extra_css

```yaml
extra_javascript:
  - javascripts/extra.js

extra_css:
  - stylesheets/extra.css
```

Подключение своих JS и CSS файлов. Пути относительно `docs_dir`.
Файлы лежат в `docs/ru/javascripts/` и `docs/ru/stylesheets/`.

### extra

```yaml
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/hypo69/FastApiFoundry-Docker
  ai_assist_version: "0.7.1"
```

- `social` — иконки соцсетей в футере (Material рендерит автоматически)
- Любые ключи доступны в `.md` через `{{ config.extra.ai_assist_version }}`

---



При каждом пуше в `main` / `master` запускается GitHub Actions workflow
`.github/workflows/deploy-docs.yml`.

```
push → [docs-js]           ──┐
     → [docs-powershell]   ──┼──→ [deploy] → GitHub Pages / FTP
     → (Python inline)     ──┘
```

| Job | Runner | Инструмент | Что генерирует |
|---|---|---|---|
| `docs-js` | ubuntu-latest | TypeDoc + typedoc-plugin-markdown | `docs/ru/dev/js/` из JSDoc |
| `docs-powershell` | windows-latest | PlatyPS | `docs/ru/dev/powershell/` из `.ps1` |
| `deploy` | ubuntu-latest | MkDocs Material + mkdocstrings | весь `site/` |

### Триггеры

Сборка запускается при изменении:

```yaml
paths:
  - 'src/**'
  - 'docs/**'
  - 'mkdocs.yml'
  - 'extensions/**'
  - 'mcp/**'
  - 'scripts/**'
  - 'config.json'
  - 'config_manager.py'
  - 'run.py'
```

---

## Источники документации

### Python — mkdocstrings

Вставка в `.md` файл:

```markdown
::: src.models.foundry_client.FoundryClient
::: src.rag.rag_system
::: config_manager.Config
```

Используется Google-style docstring:

```python
async def health_check(self) -> dict:
    """Проверка состояния Foundry.

    Returns:
        dict: Словарь со статусом, URL и timestamp.

    Example:
        >>> result = await client.health_check()
        >>> print(result["status"])
        healthy
    """
```

### JavaScript — TypeDoc

Конфигурация: `extensions/browser-extension-summarizer/typedoc.json`

Используется JSDoc:

```javascript
/**
 * Суммаризация текста страницы.
 *
 * @param {string} pageText - Текст страницы
 * @param {string} provider - ID провайдера ('gemini', 'foundry', ...)
 * @param {string} apiKey   - API ключ
 * @param {string} model    - Название модели
 * @returns {Promise<string>} Текст суммаризации
 */
export async function summarizePage(pageText, provider, apiKey, model) {
```

Локальная генерация JS docs:

```powershell
cd extensions\browser-extension-summarizer
npx typedoc --plugin typedoc-plugin-markdown
```

### PowerShell — PlatyPS

Используется comment-based help:

```powershell
function Invoke-PowerShellScript {
    <#
    .SYNOPSIS
        Выполняет PowerShell скрипт в изолированном runspace.
    .PARAMETER Script
        PowerShell код для выполнения.
    .PARAMETER TimeoutSeconds
        Таймаут в секундах (default: 300).
    .OUTPUTS
        hashtable — success, output, errors, executionTime
    #>
```

---

## Генерация документации PowerShell

`scripts/Create-Doc/Generate-PsDocs.ps1` — скрипт для генерации Markdown-документации
из comment-based help и файловых заголовков всех `.ps1` файлов проекта.

Запускается автоматически из `doc.ps1` перед сборкой сайта. Можно запустить отдельно:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Create-Doc\Generate-PsDocs.ps1
```

Что делает скрипт:

```
Generate-PsDocs.ps1
  ├─ сканирует *.ps1 в корне проекта
  ├─ сканирует scripts/, mcp/, install/, check_engine/, src/, tests/,
  │  microsoft_sandbox_operations/ (рекурсивно)
  ├─ исключает ~start/ (архив), venv/, site/
  ├─ извлекает .SYNOPSIS / .DESCRIPTION / .EXAMPLE (или заголовок файла)
  ├─ генерирует docs/ru/dev/powershell/<name>.md для каждого скрипта
  └─ создаёт docs/ru/dev/powershell/index.md, сгруппированный по директориям
```

!!! note "Запуск в CI"
    В GitHub Actions скрипт запускается автоматически в job `docs-powershell`
    при каждом пуше в `main`/`master`.

---

## Добавление новых страниц

### Новый Python модуль

1. Создать `docs/ru/dev/code/my_module.md`:
    ```markdown
    # My Module
    ::: src.my_package.my_module
    ```
2. Добавить в `mkdocs.yml` → `nav`:
    ```yaml
    - My Module: dev/code/my_module.md
    ```

### Новый раздел документации

1. Создать `.md` файл в `docs/ru/`
2. Добавить в `mkdocs.yml` → `nav`
3. Создать зеркальный файл в `docs/en/` (или оставить — будет fallback на русский)

---

## Деплой на собственный сервер

Подробнее: [Деплой документации на FTP](ftp_deploy.md)

Краткий вариант через MCP сервер:

```powershell
# Собрать и задеплоить оба языка
venv\Scripts\python.exe mcp/src/servers/docs_deploy_mcp.py
```
