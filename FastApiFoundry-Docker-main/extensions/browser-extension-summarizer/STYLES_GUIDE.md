# Руководство по стилям — FastAPI Foundry UI

**Версия:** 0.6.0
**Применяется к:** `static/` (основной интерфейс) и `extensions/browser-extension-summarizer/` (расширение)

---

## 1. Основа — Bootstrap 5

Оба интерфейса построены на **Bootstrap 5.3.0**.

### static/

Bootstrap подключается через `<head>` в `_head.html`:

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
```

Кастомизация — в `static/css/main.css` (сейчас пустой, Bootstrap достаточно).

### extensions/

Bootstrap подключается через `@import` в `css/theme.css`:

```css
@import url("https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css");
@import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css");
```

Все кастомные стили расширения — только в `css/theme.css`.
**Никаких `<style>` блоков в HTML файлах** (кроме page-specific минимума).

---

## 2. Цветовая палитра

Используются стандартные Bootstrap 5 цвета — не переопределяем:

| Назначение | Класс Bootstrap | HEX |
|---|---|---|
| Primary (кнопки, navbar, ссылки) | `btn-primary`, `bg-primary` | `#0d6efd` |
| Success (зелёный) | `btn-success`, `bg-success` | `#198754` |
| Danger (красный) | `btn-danger`, `text-danger` | `#dc3545` |
| Secondary (серый) | `btn-secondary`, `text-muted` | `#6c757d` |
| Light bg (карточки, header) | `bg-light`, `card-header` | `#f8f9fa` |
| Border | `border` | `#dee2e6` |
| Text основной | `text-body` | `#212529` |
| Text приглушённый | `text-muted` | `#6c757d` |
| Text hint | — | `#adb5bd` |

---

## 3. Компоненты Bootstrap — использовать напрямую

Для стандартных элементов **не писать кастомный CSS** — использовать Bootstrap классы:

### Кнопки

```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-success">Success</button>
<button class="btn btn-outline-secondary">Outline</button>
<button class="btn btn-danger">Danger</button>

<!-- Размеры -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- Полная ширина -->
<button class="btn btn-primary w-100">Full width</button>
```

### Карточки

```html
<div class="card mb-3">
    <div class="card-header d-flex align-items-center justify-content-between">
        <h6 class="mb-0">Заголовок</h6>
        <button class="btn btn-sm btn-outline-secondary">Action</button>
    </div>
    <div class="card-body">
        Контент
    </div>
</div>
```

`card-header` автоматически получает `background: #f8f9fa` через `theme.css`.

### Формы

```html
<!-- Input -->
<input type="text" class="form-control form-control-sm" placeholder="...">

<!-- Select -->
<select class="form-select form-select-sm">
    <option value="a">Option A</option>
</select>

<!-- Textarea -->
<textarea class="form-control form-control-sm" rows="3"></textarea>

<!-- Label -->
<label class="form-label small">Подпись</label>

<!-- Input group -->
<div class="input-group input-group-sm">
    <input type="text" class="form-control">
    <button class="btn btn-primary">Go</button>
</div>
```

### Бейджи

```html
<span class="badge bg-primary">Active</span>
<span class="badge bg-success">OK</span>
<span class="badge bg-secondary">Inactive</span>
<span class="badge bg-danger">Error</span>
<span class="badge bg-warning text-dark">Warning</span>
```

### Алерты (информационные блоки)

```html
<!-- Синий — подсказки, инструкции -->
<div class="alert alert-info" style="font-size:.85rem">
    <div class="fw-semibold mb-2">Заголовок</div>
    <p>Текст подсказки</p>
</div>

<!-- Зелёный — успех -->
<div class="alert alert-success">Успешно</div>

<!-- Красный — ошибка -->
<div class="alert alert-danger">Ошибка</div>

<!-- Жёлтый — предупреждение -->
<div class="alert alert-warning">Внимание</div>
```

### Layout

```html
<!-- Flex row с gap -->
<div class="d-flex align-items-center gap-2">
    <span>Item 1</span>
    <span>Item 2</span>
    <span class="ms-auto">Right side</span>  <!-- ms-auto = margin-left: auto -->
</div>

<!-- Grid -->
<div class="row g-3">
    <div class="col-md-6">Left</div>
    <div class="col-md-6">Right</div>
</div>
```

---

## 4. Кастомные компоненты расширения (в theme.css)

Эти классы определены в `css/theme.css` и не входят в Bootstrap.
Использовать только в расширении.

### Navbar расширения

```html
<div class="ext-navbar">
    <div class="brand">🤖 Название страницы</div>

    <!-- Опционально: действия справа -->
    <div class="d-flex gap-2 ms-auto align-items-center">
        <button class="btn btn-sm btn-outline-light">Action</button>

        <!-- Селектор языка — ВСЕГДА в navbar -->
        <select class="lang-select form-select form-select-sm"
                style="width:auto;background:rgba(255,255,255,.15);color:#fff;border-color:rgba(255,255,255,.3)">
            <option value="en">EN</option>
            <option value="ru">RU</option>
            <option value="he">HE</option>
        </select>
    </div>
</div>
```

### Tab bar расширения

```html
<div class="ext-tabs">
    <button class="ext-tab-btn active" data-tab="tab1">Tab 1</button>
    <button class="ext-tab-btn" data-tab="tab2">Tab 2</button>
</div>

<div id="tab-tab1" class="tab-panel">...</div>
<div id="tab-tab2" class="tab-panel" style="display:none">...</div>
```

Переключение вкладок — через `providers-page.js` паттерн:

```js
document.querySelectorAll('.ext-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.ext-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => { p.style.display = 'none'; });
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).style.display = '';
    });
});
```

### Popup info block

```html
<!-- Нормальное состояние -->
<div class="info-block" id="active-info">
    <span class="label">Provider: </span><span class="value">OpenAI</span><br>
    <span class="label">Model: </span><span class="value">gpt-4o</span>
</div>

<!-- Ошибка / не настроено -->
<div class="info-block empty">
    Провайдер не настроен.
</div>
```

### Chat layout (полноэкранный)

```html
<div class="chat-wrap">
    <div class="ext-navbar">...</div>

    <div class="chat-messages-area" id="messages">
        <!-- Empty state -->
        <div class="empty-state" id="empty-state">
            <div class="icon">🤖</div>
            <div>Начните разговор</div>
        </div>

        <!-- Message bubbles -->
        <div class="message user">
            <div class="message-avatar">You</div>
            <div class="message-bubble">Текст пользователя</div>
        </div>
        <div class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble"><p>Ответ ассистента</p></div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-group">
            <textarea class="form-control form-control-sm" rows="1"></textarea>
            <button class="btn btn-primary btn-sm">Send</button>
        </div>
        <div class="input-hint">Enter — отправить · Shift+Enter — новая строка</div>
    </div>
</div>
```

---

## 5. Многоязычность (i18n)

### Подключение в каждом JS файле

```js
import { initI18n, t, applyTranslations } from './js/i18n.js';

async function init() {
    await initI18n();  // загружает локаль, применяет переводы, вешает listener на .lang-select
    // ... остальная инициализация
}
init();
```

### HTML атрибуты

```html
<!-- Текст элемента -->
<h1 data-i18n="section.key">Fallback text</h1>

<!-- Placeholder -->
<input data-i18n-placeholder="section.key" placeholder="Fallback">

<!-- Title/tooltip -->
<button data-i18n-title="section.key" title="Fallback">...</button>
```

### Добавление новых строк

1. Добавить ключ в `locales/en.json`, `locales/ru.json`, `locales/he.json`
2. Структура — вложенный JSON, ключи через точку:

```json
{
  "section": {
    "key": "Translation text"
  }
}
```

3. Использовать в JS через `t('section.key')`
4. Использовать в HTML через `data-i18n="section.key"`

### Переключатель языка

Добавить в navbar — `initI18n()` автоматически вешает обработчик через event delegation:

```html
<select class="lang-select ...">
    <option value="en">EN</option>
    <option value="ru">RU</option>
    <option value="he">HE</option>
</select>
```

Класс `.lang-select` обязателен — по нему работает delegation в `js/i18n.js`.

---

## 6. Создание новой страницы расширения

### Шаблон HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Assistant — Название</title>
    <link rel="stylesheet" href="css/theme.css">
    <!-- Page-specific стили ТОЛЬКО если Bootstrap + theme.css недостаточно -->
    <style>
        /* минимум */
    </style>
</head>
<body>

<!-- 1. Navbar -->
<div class="ext-navbar">
    <div class="brand">🔧 <span data-i18n="page.title">Page Title</span></div>
    <div class="d-flex gap-2 ms-auto align-items-center">
        <select class="lang-select form-select form-select-sm"
                style="width:auto;background:rgba(255,255,255,.15);color:#fff;border-color:rgba(255,255,255,.3)">
            <option value="en">EN</option>
            <option value="ru">RU</option>
            <option value="he">HE</option>
        </select>
    </div>
</div>

<!-- 2. Опционально: tab bar -->
<div class="ext-tabs">
    <button class="ext-tab-btn active" data-tab="main" data-i18n="page.tab_main">Main</button>
</div>

<!-- 3. Контент -->
<div class="container-fluid py-3 px-3" style="max-width:760px">
    <div id="tab-main" class="tab-panel">
        <div class="card mb-3">
            <div class="card-header">
                <h6 class="mb-0" data-i18n="page.section">Section</h6>
            </div>
            <div class="card-body">
                <!-- контент -->
            </div>
        </div>
    </div>
</div>

<script src="page.js" type="module"></script>
</body>
</html>
```

### Шаблон JS

```js
import { initI18n, t } from './js/i18n.js';

async function init() {
    await initI18n();

    // Tab switching (если есть вкладки)
    document.querySelectorAll('.ext-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.ext-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => { p.style.display = 'none'; });
            btn.classList.add('active');
            document.getElementById('tab-' + btn.dataset.tab).style.display = '';
        });
    });

    // ... логика страницы
}

init();
```

### Регистрация в manifest.json

```json
"web_accessible_resources": [
    {
        "resources": ["providers.html", "chat.html", "debug.html", "new-page.html", "locales/*.json"],
        "matches": ["<all_urls>"]
    }
]
```

---

## 7. Правила — что делать и что не делать

| ✅ Делать | ❌ Не делать |
|---|---|
| Использовать Bootstrap классы напрямую | Писать кастомный CSS для стандартных элементов |
| Добавлять стили только в `css/theme.css` | Добавлять `<style>` блоки в HTML |
| Использовать `data-i18n` для всех видимых строк | Хардкодить текст в HTML |
| Использовать `t('key')` в JS для строк | Хардкодить строки в JS |
| Класс `.lang-select` на селекторе языка | Использовать `onchange` inline handler |
| `btn-sm` для кнопок в navbar и card-header | Большие кнопки в компактных зонах |
| `form-control-sm` / `form-select-sm` в плотных UI | Стандартный размер в узких контейнерах |
| `ms-auto` для выравнивания вправо | `float: right` |
| `gap-2`, `gap-3` для отступов в flex | `margin-right` на каждом элементе |

---

## 8. Файловая структура

```
extensions/browser-extension-summarizer/
├── css/
│   └── theme.css          ← ВСЕ кастомные стили здесь
├── js/
│   └── i18n.js            ← i18n модуль (не трогать)
├── locales/
│   ├── en.json            ← английские строки
│   ├── ru.json            ← русские строки
│   └── he.json            ← ивритские строки
├── popup.html / popup.js
├── chat.html / chat.js
├── providers.html / providers-page.js
├── debug.html / debug.js
└── manifest.json
```

```
static/
├── css/
│   └── main.css           ← кастомные стили (сейчас пустой)
├── js/
│   └── i18n.js            ← i18n для основного UI (i18next CDN)
├── locales/
│   ├── en.json
│   ├── ru.json
│   └── he.json
└── index.html             ← Bootstrap подключается в _head.html
```
