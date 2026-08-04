# Стили и UI

Bootstrap 5 + кастомные компоненты расширения browser-extension-summarizer.

## Файл стилей

`css/theme.css` — единый файл стилей. Подключается через Bootstrap 5 CDN + кастомные переопределения.

## Структура страниц

| Страница | HTML | JS |
|---|---|---|
| Popup | `popup.html` | `popup.js` |
| Чат | `chat.html` | `chat.js` |
| Провайдеры | `providers.html` | `providers-page.js` |
| Отладка | `debug.html` | `debug.js` |

## Создание новой страницы

1. Создать `page.html` с подключением Bootstrap и `css/theme.css`
2. Создать `page.js` с логикой
3. Зарегистрировать страницу в `manifest.json` → `web_accessible_resources` (если нужно)
4. Добавить кнопку открытия через `ui-manager.js`
