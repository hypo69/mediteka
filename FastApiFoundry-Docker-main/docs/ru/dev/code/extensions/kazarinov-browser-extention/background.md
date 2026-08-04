# Background

**Файл:** `extensions/kazarinov-browser-extention/background.js`  
**Тип:** `.js`

---

### `showResultToUser`

Модуль фоновой службы расширения
 * =================================
 * Оркестрация событий и управление основной логикой расширения

### `saveOffer`

Сохранение предложения в storage
 * Функция запрашивает имя у пользователя и сохраняет данные
 * 
 * Args:
 *     tabId (number): ID вкладки
 *     result (Object): Данные предложения

### `isTabAccessible`

Проверка доступности вкладки для работы расширения
 * Функция проверяет URL вкладки на наличие ограниченных протоколов
 * 
 * Args:
 *     tab (Object): Объект вкладки Chrome
 * 
 * Returns:
 *     boolean: true если вкладка доступна, false иначе

### `handleGenerateOffer`

Обработчик установки/обновления расширения

### `handleClearAllComponents`

Обработчик: Удаляет все сохраненные компоненты (ВРЕМЕННО УДАЛЕНА ЛОГИКА ПОДТВЕРЖДЕНИЯ ДЛЯ ТЕСТА)

### `getComponentsForOffer`

Получение компонентов для формирования предложения
 * Функция загружает компоненты из storage
 * 
 * Returns:
 *     Promise<Array>: Массив компонентов

### `getGeminiApiKey`

Получение API ключа Gemini
 * 
 * Returns:
 *     Promise<string>: API ключ

### `getGeminiModel`

Получение модели Gemini
 * 
 * Returns:
 *     Promise<string>: Название модели

### `handleAddComponent`

### `handleDeleteComponent`

### `handleCopyComponent`

### `handleLoadOffer`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
