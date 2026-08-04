# 🧠 CODE_RULES.RU.v0.3.0

**Проект:** Ai Assistant  
**Версия:** 0.3.0 (WordPress Edition)  
**Автор:** hypo69 / Ai Assistant Team (https://www.Ai Assistant.com)  
**Лицензия:** CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)  
**Дата:** 2025  

---

## 🔧 GUI Configuration Rules

### GUI Configuration File
- **ВСЕГДА** используй имя файла `config.json` для настроек GUI
- **НЕ** используй другие имена типа `gui-config.json`, `settings.json` и т.д.
- Файл `config.json` должен содержать все настройки для GUI лончера
- Структура: JSON с секциями `fastapi_server`, `foundry_ai`, `rag_system`

### Пример структуры config.json:
```json
{
  "fastapi_server": {
    "port": 8002,
    "host": "0.0.0.0",
    "mode": "dev"
  },
  "foundry_ai": {
    "base_url": "http://localhost:50477/v1/"
  }
}
```

---

## ⚙️ 0. Общие сведения

Этот документ определяет **единые стандарты кодирования и документирования** для всех модулей экосистемы **Ai Assistant** 

Инструкция описывает:

- форматы заголовков файлов;
- docstring / docblock для функций и классов;
- принципы именования;
- правила работы с JSON и файлами;
- логирование и обработку ошибок;
- безопасность и WordPress-специфику.

### 🔥 Обязательные шаги для ИИ-модели перед работой с проектом Ai Assistant

Любая модель ИИ (Gemini, OpenAI, локальный LLM и т.д.), использующаяся для работы с кодом проекта **Ai Assistant**, обязана:

1. **Прочитать файл `./DEPLOYMENT-WORKFLOW.md` полностью.**  
   В нём описано:
   - как устроен деплой и окружения;
   - как запускать MCP-серверы;
   - как взаимодействуют агенты Ai Assistant;
   - какие ограничения и требования к автоматизации.

2. **Прочитать актуальные правила кодирования:**
   - `./gemini/CODE_RULES.RU.v0.3.0.md` (или соответствующую локальную копию `CODE_RULES.md`);
   - дополнительные файлы в `./gemini/` при наличии ссылок.

3. **Прочитать основную документацию проекта WordPress:**
   - `./wp-content/docs/index.html`,
   - пройти по всем ссылкам из `index.html` для понимания общей структуры.

4. **Следовать этим правилам дословно.**  
   Если модель не уверена — она должна:
   - либо явно указать на сомнение в сгенерированном ответе,
   - либо запросить уточнение / ссылку на конкретный документ.

⚠️ Любая генерация кода, не соответствующая этим правилам, считается экспериментальной и требует ручной ревизии.

---

## 🔖 1. Общие правила форматирования кода

1. Все файлы кодируются в **UTF-8** без BOM.
2. В коде запрещено использование **глобальных переменных** — они выносятся в класс `Config` (или аналогичный конфигурационный объект).
3. Все импорты выравниваются и упорядочиваются по блокам:

   ```python
   from header import __root__
   from src import gs
   from src.logger import logger
   from src.utils.printer import pprint
   from src.utils.json import j_loads, j_loads_ns, j_dumps, save_text_file, read_text_file
```

4. Все функции объявляют **локальные переменные в начале** тела функции.
5. Проверка условий **всегда** в формате:

   ```python
   if not condition:
       return
   ```

   Вместо:

   ```python
   if condition:
       ...
   ```
6. Для проверки отсутствия данных используется `if not data`, **не** `if data is None`.
7. Строки с `...` являются **маркерами отладки** и  **не изменяются** .
8. **JSON** и файловые операции выполняются только через:

   * `j_loads`, `j_loads_ns` — для чтения;
   * `j_dumps`, `save_text_file` — для записи;
   * `read_text_file` — для чтения текстов.

   Эти функции:

   * логируют ошибки самостоятельно;
   * создают директории при необходимости.
9. Вызовы `j_loads` / `save_text_file` / `read_text_file` требуют  **проверки результата** , но  **не оборачиваются в try/except** :

   ```python
   data = j_loads(path)
   if not data:
       return None
   ```
10. **Логирование** только через `logger` из `src.logger.logger`:

    ```python
    logger.error("Ошибка чтения файла конфигурации", ex, exc_info=True)
    ```
11. **Вывод** в консоль — только через `pprint` из `src.utils.printer`.

    `print()` использовать  **запрещено** .
12. **Timestamp** получаем только через `gs.now` (ни `datetime.now()`, ни `time.time()` напрямую):

    ```python
    current_ts = gs.now()
    ```
13. Для WordPress / Web-файлов можно указывать дополнительный тег-комментарий:

    ```python
    # Platform: WordPress
    ```
14. Комментарии, начинающиеся с `#`, **никогда не изменяются** — это служебные строки (особенно в auto-сгенерированных заголовках).
15. Примеры в docstring должны быть **рабочими и минимальными** — их можно скопировать и запустить.
16. В коде допускаются только **типовые аннотации** Python / PHP / JS.
17. Все модули импортируются  **относительно `__root__`** , который задаётся в `header.py`.
18. **ReStructuredText-блоки запрещены** :

* Нельзя использовать модульные описания `.. module::`, `:platform:`, `:synopsis:` внутри docstring.
* Нельзя оформлять docstring в стиле `Sphinx` или `reST`.
* Нельзя использовать fenced-блоки с языком `rst` (```rst).

  Если такие блоки встречаются в коде — их необходимо **удалить** и заменить на обычные docstring / docblock.

---

## 🧩 2. Шапки файлов (`hypo69 / Ai Assistant header`)

Структура заголовка обязательна для всех файлов проекта.

Она содержит назначение, примеры, а также мета-данные (имя файла, проект, автор, лицензия, год).

---

### 🐍 Python

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: <Название логического процесса или модуля>
# =============================================================================
# Описание:
#   <Подробно опиши назначение модуля, его классов и функций>
#   <Укажи, какие пакеты или API используются>
#
# Примеры:
#   >>> from src.module import ClassName
#   >>> ClassName().execute()
#
# File: <имя_файла.py>
# Project: Ai Assistant
# Package: <PackageName>
# Module: <ModuleName>
# Class: <ClassName>
# Function: <FunctionName>
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

---

### 🧱 PHP

```php
<?php
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: <Название логического процесса или блока логики>
# =============================================================================
# Описание:
#   <Опиши подробно, что делает код, какие хуки, фильтры или функции реализует>
#   <Если файл связан с WordPress — укажи контекст использования>
#
# Примеры:
#   1. Как вызвать функцию:
#        add_action('wp_footer', 'custom_footer_text');
#   2. Как расширить функционал:
#        include_once get_stylesheet_directory() . '/custom-functions.php';
#
# File: <имя_файла.php>
# Project: Ai Assistant
# IF Package - Package: <PackageName>
# IF Module  - Module: <ModuleName>
# IF Class   - Class: <ClassName>
# IF Function- Function: <FunctionName>
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================
```

---

### ⚙️ JavaScript / TypeScript

```javascript
/**
 * =============================================================================
 * Название процесса: <Название логического процесса или скрипта>
 * =============================================================================
 * Описание:
 *   <Опиши подробно назначение кода, ключевые функции, взаимодействие с DOM или API>
 *   <Если код подключается к WordPress, укажи место вызова>
 *
 * Примеры:
 *   document.addEventListener('DOMContentLoaded', () => {
 *       console.log('Script initialized');
 *   });
 *
 * File: <имя_файла.js/ts>
 * Project: Ai Assistant
 * Module: <ModuleName>
 * Class: <ClassName>
 * Function: <FunctionName>
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */
```

---

### 🧩 HTML

```html
<!--
===============================================================================
Название процесса: <Название логического процесса или шаблона>
===============================================================================
Описание:
    <Подробное описание HTML-фрагмента, его назначения и связей с другими файлами>
    <Если используется в WordPress — укажи, какой шаблон вызывает этот блок>

Примеры:
    <header class="site-header">
        <h1><?php bloginfo('name'); ?></h1>
    </header>

File: <имя_файла.html>
Project: Ai Assistant
Module: <ModuleName>
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2026 hypo69
===============================================================================
-->
```

---

### 🎨 CSS / SCSS

```css
/*
===============================================================================
Название процесса: <Название набора стилей или логического блока>
===============================================================================
Описание:
    <Опиши, какие классы и элементы оформляются>
    <Укажи область применения — глобальные стили, компоненты или страницы>

Примеры:
    body {
        background-color: #fafafa;
        color: #333;
    }

File: <имя_файла.css/scss>
Project: Ai Assistant
Module: <ModuleName>
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2026 hypo69
===============================================================================
*/
```

---

## ⚙️ 3. Формат функций и классов (`hypo69 docblock`)

Документация функций и классов оформляется в едином стиле для каждого языка.

Описание начинается с  **назначения** , затем аргументы, возвращаемое значение, исключения и пример.

---

### 🐍 Python

```python
from typing import Optional

def function_name(param: str, param1: Optional[int | dict] = None) -> dict | None:
    """Описание назначения функции

    Args:
        param (str): Основной параметр.
        param1 (Optional[int | dict], optional): Дополнительный параметр. По умолчанию `None`.

    Returns:
        dict | None: Результат выполнения функции или `None` при ошибке/пустых данных.

    Raises:
        SomeError: Если входные данные некорректны.

    Example:
        >>> result = function_name("data", {"opt": 1})
        >>> print(result)
        {'status': 'ok'}
    """
    result: dict = {}

    if not param:
        return None

    ...
    return result
```

---

### ⚙️ JavaScript / TypeScript

```javascript
/**
 * Выполняет основное действие с переданными данными.
 *
 * @param {string} param1 - Основной параметр.
 * @param {number|Object|null} [param2=null] - Дополнительный параметр.
 * @returns {Object|null} Результат выполнения функции.
 * @throws {Error} Если входные данные некорректны.
 *
 * @example
 * const data = processData("text", 42);
 * console.log(data);
 */
function processData(param1, param2 = null) {
    if (!param1) {
        throw new Error("Некорректный параметр");
    }

    const result = {};
    ...
    return result;
}
```

---

### 🧱 PHP

```php
<?php
/**
 * Выполняет основное действие с переданными данными.
 *
 * @param string          $param1 Основной параметр.
 * @param int|array|null  $param2 Дополнительный параметр.
 *
 * @return array|null Результат выполнения функции.
 *
 * @throws InvalidArgumentException Если параметры некорректны.
 *
 * @example
 * $res = process_data("input", [1, 2]);
 * var_dump($res);
 */
function process_data(string $param1, int|array|null $param2 = null): ?array {
    if (!$param1) {
        throw new InvalidArgumentException("param1 не должен быть пустым");
    }

    $result = [];
    ...
    return $result;
}
```

---

### 🧩 Классы

**Python**

```python
class DataProcessor:
    """Класс выполняет обработку данных

    Attributes:
        config (dict): Настройки обработки.
        name (str): Имя объекта.
    """

    def __init__(self, config: dict, name: str) -> None:
        """Инициализация экземпляра класса."""
        self.config: dict = config
        self.name: str = name

    def run(self, data: str) -> bool:
        """Запуск обработки данных.

        Args:
            data (str): Входные данные.

        Returns:
            bool: True при успешной обработке.

        Raises:
            ValueError: Если переданы пустые данные.
        """
        if not data:
            raise ValueError("Пустые данные")

        ...
        return True
```

**JavaScript**

```javascript
class DataProcessor {
    /**
     * @param {Object} config - Конфигурация обработки.
     * @param {string} name - Имя экземпляра.
     */
    constructor(config, name) {
        this.config = config;
        this.name = name;
    }

    /**
     * Запускает обработку данных.
     *
     * @param {string} data - Входные данные.
     * @returns {boolean} Успешность выполнения.
     * @throws {Error} Если данные пустые.
     */
    run(data) {
        if (!data) {
            throw new Error("Пустые данные");
        }

        ...
        return true;
    }
}
```

**PHP**

```php
<?php
class DataProcessor {
    private array $config;
    private string $name;

    public function __construct(array $config, string $name) {
        $this->config = $config;
        $this->name = $name;
    }

    public function run(string $data): bool {
        if (!$data) {
            throw new RuntimeException("Пустые данные");
        }

        ...
        return true;
    }
}
```

---

## 🧩 4. Примеры оформления комментариев

* Комментарий всегда  **перед кодом** , который он описывает.
* Использовать чёткие технические формулировки:
  * ✅ «Проверка наличия файла перед чтением»
  * ❌ «Проверяем файл»
* Строки с `...`  **оставляются без изменений** .

**Python**

```python
# Проверка наличия файла перед обработкой
if not file_path.exists():
    raise FileNotFoundError(f"Файл не найден: {file_path}")
```

**JavaScript**

```javascript
// Проверка наличия элемента перед вызовом метода
if (!element) {
    throw new Error("Элемент не найден");
}
```

**PHP**

```php
// Проверка наличия ключа перед обработкой массива
if (!array_key_exists('key', $data)) {
    throw new InvalidArgumentException("Ключ отсутствует");
}
```

---

## 🚀 6. WordPress-специфичные правила

### 6.1 Общие принципы WordPress разработки

1. **Структура плагинов и тем** :

```text
   plugin-name/
   ├── plugin-name.php          # Главный файл плагина (макс 50 KB)
   ├── README.md                # Документация
   ├── includes/
   │   ├── class-main.php       # Главный класс плагина
   │   ├── class-*.php          # Один класс = один файл
   │   └── functions.php        # Функции helpers
   ├── admin/
   │   ├── admin.php            # Admin страницы и меню
   │   ├── class-settings.php   # Класс настроек
   │   └── assets/
   │       ├── css/
   │       ├── js/
   │       └── images/
   ├── public/
   │   ├── class-frontend.php   # Фронтенд функциональность
   │   └── assets/
   ├── database/
   │   └── schema.sql           # SQL для создания таблиц
   └── index.html               # Документация (HTML)
```

1. **Обязательные проверки** :

```php
   // Всегда в начале файла - проверка доступа
   defined( 'ABSPATH' ) || exit;
```

1. **Версионирование** : X.Y.Z (Major.Minor.Patch)

* X: большие изменения (backward-incompatible);
* Y: новые функции (backward-compatible);
* Z: баг-фиксы.

1. **Локализация** : все строки через `__()` или `_e()`:

```php
   echo esc_html__( 'Привет, мир!', 'plugin-textdomain' );
```

1. **Nonce-проверки** обязательны для всех форм и AJAX:
   ```php
   wp_verify_nonce( $_REQUEST['_wpnonce'], 'action_name' );
   ```
2. **Capability-проверки** :

```php
   if ( ! current_user_can( 'manage_options' ) ) {
       wp_die( 'Недостаточно прав' );
   }
```

---

### 6.2 WordPress PHP файлы (плагины и темы)

#### Заголовок плагина

```php
<?php
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: <Название функциональности плагина>
# =============================================================================
# Описание:
#   <Подробное описание того, что делает плагин или модуль>
#   <Какие хуки, фильтры и функции WordPress используются>
#   <На каких сайтах / в каких сценариях применяется>
#
# Примеры:
#   1. Активация плагина:
#        Перейти в wp-admin/plugins.php и активировать плагин
#   2. Использование функции:
#        do_action('plugin_name_after_post', $post_id);
#   3. Фильтр данных:
#        apply_filters('plugin_name_post_data', $data);
#
# Требования:
#   - WordPress: 5.0+
#   - PHP: 8.1+
#   - Зависимости: (если есть)
#
# File: plugin-name.php
# Project: Ai Assistant
# Package: PluginName
# Class: Plugin_Main_Class
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================
?>
```

#### Структура класса плагина

```php
<?php
defined( 'ABSPATH' ) || exit;

class Plugin_Main_Class {
    /**
     * Singleton экземпляр класса.
     *
     * @var Plugin_Main_Class|null
     */
    private static $instance = null;

    /**
     * Получить singleton экземпляр.
     *
     * @return Plugin_Main_Class Экземпляр класса
     */
    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }

        return self::$instance;
    }

    /**
     * Конструктор класса.
     */
    private function __construct() {
        $this->init_hooks();
    }

    /**
     * Инициализация WordPress хуков.
     */
    private function init_hooks() {
        // Загрузка текстового домена для локализации
        add_action( 'plugins_loaded', [ $this, 'load_textdomain' ] );

        // Активация и деактивация плагина
        register_activation_hook( __FILE__, [ $this, 'activate' ] );
        register_deactivation_hook( __FILE__, [ $this, 'deactivate' ] );

        // Инициализация плагина
        add_action( 'init', [ $this, 'init' ] );

        // Admin хуки
        if ( is_admin() ) {
            add_action( 'admin_menu', [ $this, 'admin_menu' ] );
            add_action( 'admin_init', [ $this, 'admin_init' ] );
        }
    }

    /**
     * Загрузка текстового домена для локализации.
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'plugin-textdomain',
            false,
            dirname( plugin_basename( __FILE__ ) ) . '/languages'
        );
    }

    /**
     * При активации плагина.
     */
    public static function activate() {
        // Создание таблиц БД
        // Установка значений по умолчанию
        // Логирование активации
    }

    /**
     * При деактивации плагина.
     */
    public static function deactivate() {
        // Очистка временных данных
        // Удаление scheduled tasks
    }

    /**
     * Инициализация функциональности плагина.
     */
    public function init() {
        // Регистрация custom post types
        // Регистрация таксономий
        // Регистрация ассетов
    }

    /**
     * Добавление меню в админку.
     */
    public function admin_menu() {
        add_menu_page(
            'Название Плагина',     // page_title
            'Плагин',               // menu_title
            'manage_options',       // capability
            'plugin-slug',          // menu_slug
            [ $this, 'admin_page' ] // function
        );
    }

    /**
     * Страница административной панели.
     */
    public function admin_page() {
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_die( esc_html__( 'Недостаточно прав доступа', 'plugin-textdomain' ) );
        }
        ?>
        <div class="wrap">
            <h1><?php echo esc_html__( 'Настройки плагина', 'plugin-textdomain' ); ?></h1>
            <!-- Контент админ-страницы -->
        </div>
        <?php
    }

    /**
     * Инициализация админ-панели.
     */
    public function admin_init() {
        // Регистрация настроек
        // Добавление полей форм
    }
}

// Инициализация плагина
Plugin_Main_Class::get_instance();
```

---

### 6.3 WordPress функции (helpers)

```php
<?php
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Вспомогательные функции плагина
# =============================================================================
# Описание:
#   Набор функций-помощников для работы с WordPress API
#   Содержит функции для работы с постами, опциями, пользователями и т.д.
#
# File: functions.php
# Project: Ai Assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
?>

<?php
defined( 'ABSPATH' ) || exit;

/**
 * ! Получить значение опции с проверкой и кэшированием.
 *
 * @param string $option    Название опции.
 * @param mixed  $default   Значение по умолчанию.
 * @param bool   $use_cache Использовать кэш (default: true).
 *
 * @return mixed Значение опции или значение по умолчанию.
 *
 * Example:
 *     $settings = plugin_get_option( 'plugin_settings', [], true );
 *     echo esc_html( $settings['key'] ?? 'default' );
 */
function plugin_get_option( string $option, $default = false, bool $use_cache = true ) {
    if ( ! $option ) {
        return $default;
    }

    if ( $use_cache ) {
        $value = wp_cache_get( $option, 'plugin_options' );
        if ( false !== $value ) {
            return $value;
        }
    }

    $value = get_option( $option, $default );

    if ( $use_cache ) {
        wp_cache_set( $option, $value, 'plugin_options', HOUR_IN_SECONDS );
    }

    return $value;
}

/**
 * ! Сохранить опцию с инвалидацией кэша.
 *
 * @param string $option Название опции.
 * @param mixed  $value  Значение опции.
 * @param string $type   Тип хука: 'add' или 'update'.
 *
 * @return bool True если успешно.
 *
 * Example:
 *     plugin_update_option( 'plugin_settings', [ 'key' => 'value' ] );
 */
function plugin_update_option( string $option, $value, string $type = 'update' ): bool {
    if ( ! $option ) {
        return false;
    }

    $result = 'add' === $type
        ? add_option( $option, $value, '', 'no' )
        : update_option( $option, $value );

    // Инвалидация кэша
    wp_cache_delete( $option, 'plugin_options' );

    return (bool) $result;
}

/**
 * ! Логирование в debug.log.
 *
 * @param string $message Сообщение для логирования.
 * @param mixed  $data    Дополнительные данные.
 * @param string $level   Уровень лога: 'error', 'warning', 'info'.
 *
 * Example:
 *     plugin_log( 'Ошибка при обработке поста', $post_id, 'error' );
 */
function plugin_log( string $message, $data = null, string $level = 'info' ) {
    if ( ! WP_DEBUG ) {
        return;
    }

    $output = sprintf(
        '[%s] %s - %s',
        strtoupper( $level ),
        $message,
        is_array( $data ) || is_object( $data ) ? wp_json_encode( $data ) : (string) $data
    );

    error_log( $output );
}
?>
```

---

### 6.4 WordPress HTML шаблоны

#### Заголовок HTML файла в теме

```html
<!--
===============================================================================
Название процесса: <Название шаблона или компонента>
===============================================================================
Описание:
    <Подробное описание, когда и где этот шаблон используется>
    <Какие переменные $available_theme_props и $wp_query доступны>
    <Связь с другими шаблонами (parent template, child blocks)>

Примеры:
    1. Вызов из functions.php:
         get_template_part( 'template-parts/header' );
    2. Использование переменных:
         if ( have_posts() ) {
             while ( have_posts() ) {
                 the_post();
                 echo get_the_title();
             }
         }

Доступные переменные:
    - $post: объект текущего поста
    - $wp_query: объект глобального запроса
    - $post_type: тип поста

File: template-parts/header.php
Project: Ai Assistant Theme
Template: Header Template
Author: hypo69
Copyright: © 2026 hypo69
Copyright: © 2025
===============================================================================
-->

<header class="site-header">
    <!-- Основной контент -->
</header>
```

#### WordPress-специфичный PHP в шаблоне

```php
<?php
/**
 * ! Шаблон для отображения заголовка сайта.
 *
 * Используется на всех страницах через get_header().
 *
 * @package Ai Assistant
 * @subpackage Theme
 * @since 1.0.0
 */

defined( 'ABSPATH' ) || exit;
?>

<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
    <?php wp_body_open(); ?>

    <header class="site-header">
        <div class="site-branding">
            <h1 class="site-title">
                <a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home">
                    <?php bloginfo( 'name' ); ?>
                </a>
            </h1>
            <p class="site-description"><?php bloginfo( 'description' ); ?></p>
        </div>

        <nav class="site-navigation" role="navigation">
            <?php
            wp_nav_menu(
                [
                    'theme_location' => 'primary',
                    'menu_class'     => 'primary-menu',
                    'fallback_cb'    => 'wp_page_menu',
                ]
            );
            ?>
        </nav>
    </header>
```

---

### 6.5 WordPress REST API

```php
<?php
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: REST API endpoints для плагина
# =============================================================================
# Описание:
#   Регистрация и реализация REST API endpoints
#   Для работы с custom post types и данными плагина
#
# File: includes/class-rest-api.php
# Project: Ai Assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
?>

<?php
defined( 'ABSPATH' ) || exit;

class Plugin_REST_API {
    const NAMESPACE  = 'plugin/v1';
    const REST_BASE  = 'data';

    /**
     * ! Регистрация REST API routes.
     *
     * Example:
     *     GET  /wp-json/plugin/v1/data
     *     POST /wp-json/plugin/v1/data
     */
    public static function register_routes() {
        register_rest_route(
            self::NAMESPACE,
            '/' . self::REST_BASE,
            [
                [
                    'methods'             => WP_REST_Server::READABLE,
                    'callback'            => [ __CLASS__, 'get_data' ],
                    'permission_callback' => [ __CLASS__, 'permission_check' ],
                    'args'                => [
                        'page'     => [
                            'type'    => 'integer',
                            'default' => 1,
                            'minimum' => 1,
                        ],
                        'per_page' => [
                            'type'    => 'integer',
                            'default' => 10,
                            'minimum' => 1,
                        ],
                    ],
                ],
                [
                    'methods'             => WP_REST_Server::CREATABLE,
                    'callback'            => [ __CLASS__, 'create_data' ],
                    'permission_callback' => [ __CLASS__, 'permission_check_admin' ],
                ],
            ]
        );
    }

    /**
     * ! Получить данные (GET).
     *
     * @param WP_REST_Request $request Объект запроса.
     * @return WP_REST_Response|WP_Error Ответ или ошибка.
     */
    public static function get_data( WP_REST_Request $request ) {
        $page     = $request->get_param( 'page' );
        $per_page = $request->get_param( 'per_page' );

        if ( ! $page || ! $per_page ) {
            return new WP_Error(
                'invalid_params',
                'Неверные параметры пагинации',
                [ 'status' => 400 ]
            );
        }

        $data = [
            'page'     => $page,
            'per_page' => $per_page,
            'items'    => [],
        ];

        return rest_ensure_response( $data );
    }

    /**
     * ! Создать данные (POST).
     *
     * @param WP_REST_Request $request Объект запроса.
     * @return WP_REST_Response|WP_Error Ответ или ошибка.
     */
    public static function create_data( WP_REST_Request $request ) {
        $body = $request->get_json_params();

        if ( ! $body || empty( $body['title'] ) ) {
            return new WP_Error(
                'invalid_data',
                'Отсутствуют обязательные поля',
                [ 'status' => 400 ]
            );
        }

        // Обработка данных и сохранение...

        return rest_ensure_response(
            [
                'status'  => 'success',
                'message' => 'Данные сохранены',
                'id'      => 123,
            ]
        );
    }

    /**
     * ! Проверка прав доступа (чтение).
     *
     * @return bool True если пользователь авторизован.
     */
    public static function permission_check() {
        return is_user_logged_in();
    }

    /**
     * ! Проверка прав доступа (администратор).
     *
     * @return bool True если пользователь администратор.
     */
    public static function permission_check_admin() {
        return current_user_can( 'manage_options' );
    }
}

// Регистрация routes при инициализации.
add_action( 'rest_api_init', [ 'Plugin_REST_API', 'register_routes' ] );
?>
```

---

### 6.6 WordPress AJAX

```php
<?php
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: AJAX обработчики плагина
# =============================================================================
# Project: Ai Assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

defined( 'ABSPATH' ) || exit;

class Plugin_AJAX {
    /**
     * ! Регистрация AJAX обработчиков.
     */
    public static function register_handlers() {
        add_action( 'wp_ajax_plugin_action', [ __CLASS__, 'handle_action' ] );
        add_action( 'wp_ajax_nopriv_plugin_action', [ __CLASS__, 'handle_action' ] );
    }

    /**
     * ! Обработчик AJAX запроса.
     *
     * JavaScript:
     *     $.post(ajaxurl, {
     *         action: 'plugin_action',
     *         nonce: pluginData.nonce,
     *         data: { key: 'value' }
     *     }, function(response) {
     *         console.log(response);
     *     });
     */
    public static function handle_action() {
        // Проверка nonce
        if ( ! isset( $_POST['nonce'] ) ||
             ! wp_verify_nonce( $_POST['nonce'], 'plugin_nonce' ) ) {
            wp_send_json_error( 'Invalid nonce' );
        }

        // Проверка данных
        if ( ! isset( $_POST['data'] ) ) {
            wp_send_json_error( 'Missing data' );
        }

        $data = sanitize_text_field( $_POST['data'] );

        // Обработка...
        $result = [
            'status'  => 'success',
            'message' => 'Action completed',
            'data'    => $data,
        ];

        wp_send_json_success( $result );
    }
}

add_action( 'wp_loaded', [ 'Plugin_AJAX', 'register_handlers' ] );
?>
```

---

### 6.7 WordPress CSS и JavaScript

#### CSS в теме

```css
/*
===============================================================================
Название процесса: Основные стили темы
===============================================================================
Описание:
    Глобальные стили для всех элементов сайта
    Включает стили для body, headers, footers и основных компонентов

File: style.css
Project: Ai Assistant Theme
Author: hypo69
Copyright: © 2026 hypo69
===============================================================================
*/

/* Переменные CSS */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --text-color: #333;
    --background-color: #fff;
}

/* Глобальные стили */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}

/* Компоненты */
.site-header {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
    padding: 20px;
}

.site-header h1 {
    margin: 0;
    font-size: 28px;
}
```

#### JavaScript для WordPress

```javascript
/**
 * =============================================================================
 * Название процесса: Фронтенд скрипты для темы
 * =============================================================================
 * Описание:
 *   Основной JavaScript файл для интерактивности на фронтенде.
 *   Работает с WordPress AJAX и Gutenberg блоками.
 *
 * File: assets/js/main.js
 * Project: Ai Assistant Theme
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * =============================================================================
 */

(function() {
    'use strict';

    /**
     * ! Инициализация при загрузке DOM.
     */
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Theme initialized');
        initMenuToggle();
        initAjaxForms();
    });

    /**
     * ! Инициализация меню-бургер.
     */
    function initMenuToggle() {
        const menuButton = document.querySelector('.menu-toggle');
        const menu = document.querySelector('.site-navigation');

        if (!menuButton) {
            return;
        }

        menuButton.addEventListener('click', function() {
            menu.classList.toggle('open');
        });
    }

    /**
     * ! AJAX обработчик форм.
     */
    function initAjaxForms() {
        const forms = document.querySelectorAll('.plugin-form');

        forms.forEach((form) => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();

                const formData = new FormData(this);
                formData.append('action', 'plugin_action');
                formData.append('nonce', pluginData.nonce);

                fetch(pluginData.ajaxUrl, {
                    method: 'POST',
                    body: formData,
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.success) {
                            console.log('Success:', data.data);
                        } else {
                            console.error('Error:', data.data);
                        }
                    })
                    .catch((error) => console.error('Fetch error:', error));
            });
        });
    }
})();
```

---

### 6.8 Безопасность в WordPress

```php
<?php
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Функции безопасности плагина
# =============================================================================
# Project: Ai Assistant
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

defined( 'ABSPATH' ) || exit;

/**
 * ! Санитизация текстовых данных.
 *
 * Example:
 *     $safe_text = plugin_sanitize_text( $_POST['input'] );
 *
 * @param mixed $data Входные данные.
 * @return string Очищенная строка.
 */
function plugin_sanitize_text( $data ): string {
    if ( ! $data ) {
        return '';
    }

    return sanitize_text_field( wp_unslash( $data ) );
}

/**
 * ! Экранирование для HTML вывода.
 *
 * Example:
 *     echo plugin_esc_html( get_option( 'option_name' ) );
 *
 * @param mixed $data Входные данные.
 * @return string Экранированная строка.
 */
function plugin_esc_html( $data ): string {
    if ( ! $data ) {
        return '';
    }

    return esc_html( $data );
}

/**
 * ! Экранирование для URL.
 *
 * Example:
 *     echo plugin_esc_url( $user_input_url );
 *
 * @param string|null $url Входной URL.
 * @return string Экранированный URL или пустая строка.
 */
function plugin_esc_url( ?string $url ): string {
    if ( ! $url ) {
        return '';
    }

    return esc_url( $url );
}

/**
 * ! Экранирование для HTML атрибутов.
 *
 * Example:
 *     echo plugin_esc_attr( get_post_meta( $id, 'value', true ) );
 *
 * @param mixed $data Входные данные.
 * @return string Экранированная строка.
 */
function plugin_esc_attr( $data ): string {
    if ( ! $data ) {
        return '';
    }

    return esc_attr( $data );
}

/**
 * ! Безопасный SQL запрос через $wpdb.
 *
 * Example:
 *     $results = plugin_get_posts_secure( $post_id );
 *
 * @param mixed $post_id ID поста.
 * @return array Список постов или пустой массив.
 */
function plugin_get_posts_secure( $post_id ): array {
    global $wpdb;

    if ( ! $post_id || ! is_numeric( $post_id ) ) {
        return [];
    }

    return $wpdb->get_results(
        $wpdb->prepare(
            "SELECT * FROM {$wpdb->posts} WHERE ID = %d LIMIT 1",
            absint( $post_id )
        )
    );
}

/**
 * ! Проверка nonce для формы.
 *
 * Example:
 *     if ( ! plugin_verify_nonce( $_POST, 'action_name' ) ) {
 *         wp_die( 'Security check failed' );
 *     }
 *
 * @param array  $data   Массив данных (обычно $_POST или $_REQUEST).
 * @param string $action Имя действия.
 *
 * @return bool True при валидном nonce.
 */
function plugin_verify_nonce( array $data, string $action ): bool {
    if ( ! isset( $data['_wpnonce'] ) ) {
        return false;
    }

    return wp_verify_nonce( $data['_wpnonce'], $action );
}

/**
 * ! Вывод nonce поля в форме.
 *
 * Example:
 *     plugin_nonce_field( 'action_name' );
 *
 * @param string $action Имя действия.
 */
function plugin_nonce_field( string $action ): void {
    wp_nonce_field( $action, '_wpnonce', false, true );
}

/**
 * ! Проверка возможности пользователя.
 *
 * Example:
 *     if ( plugin_user_can( 'edit_posts' ) ) {
 *         // ...
 *     }
 *
 * @param string $capability Возможность (capability).
 * @return bool True, если есть права.
 */
function plugin_user_can( string $capability ): bool {
    return current_user_can( $capability );
}
?>
```

---


## 🌐 7. Мультиязычность и язык комментариев (HTML, JS, CSS, PHP)

### 7.1 Плейсхолдеры для мультиязычности

Все пользовательские строки в файлах `.html`, `.js`, `.css`, `.php` **обязаны** использовать плейсхолдеры вместо хардкода текста:

- **HTML** — атрибут `data-i18n` или шаблонный тег:
  ```html
  <!-- Use data-i18n attribute for all user-visible text -->
  <button data-i18n="btn.save">Save</button>
  <h1 data-i18n="page.title">Title</h1>
  ```

- **JavaScript** — функция `t()` или `i18n()`:
  ```javascript
  // Use i18n() for all user-facing strings
  showAlert(i18n('error.not_found'));
  el.textContent = i18n('label.model_name');
  ```

- **PHP** — WordPress `__()` / `_e()` обязательны для всех строк:
  ```php
  // Use __() for all translatable strings
  echo esc_html__( 'Settings saved', 'plugin-textdomain' );
  ```

- **CSS** — строки в CSS не локализуются, но `content: "..."` в псевдоэлементах **запрещён** для пользовательского текста.

### 7.2 Язык внутренних комментариев

**ОБЯЗАТЕЛЬНО:** Все inline-комментарии внутри кода файлов `.html`, `.js`, `.css`, `.php` пишутся **только на английском языке**.

```javascript
// ✅ Correct
// Initialize menu toggle on DOM ready
function initMenuToggle() { ... }

// ❌ Wrong
// Инициализация меню при загрузке DOM
function initMenuToggle() { ... }
```

```php
// ✅ Correct
// Verify nonce before processing form data
if ( ! wp_verify_nonce( ... ) ) { ... }

// ❌ Wrong
// Проверка nonce перед обработкой формы
```

```css
/* ✅ Correct */
/* Primary navigation styles */
.site-nav { ... }

/* ❌ Wrong */
/* Стили основной навигации */
```

```html
<!-- ✅ Correct -->
<!-- Main content wrapper -->
<div class="wrap">

<!-- ❌ Wrong -->
<!-- Основной контейнер контента -->
```

> Это правило распространяется на **все** комментарии внутри кода. Заголовки файлов (file header block) могут содержать описание на русском языке.

---

## 🔐 8. Правила экспорта и импорта параметров настроек

### 7.1 Общий принцип

Все параметры конфигурации проекта разделены на два типа:

| Тип | Хранение | Пример |
|-----|----------|--------|
| Публичные настройки | `config.json` | порт, хост, режим, RAG параметры |
| Секретные параметры | `.env` | токены, ключи API, пароли |

### 7.2 Обязательные правила

- **НИКОГДА** не хранить секреты (`TOKEN`, `KEY`, `SECRET`, `PASSWORD`, `PAT`) в `config.json`
- **ВСЕГДА** использовать синтаксис `${VAR_NAME}` в `config.json` для подстановки из `.env`
- **ВСЕГДА** добавлять новый параметр одновременно в три места:
  1. `.env` — реальное значение
  2. `.env.example` — заглушка с описанием
  3. `config.json` — ссылка `${VAR_NAME}` или прямое значение (если не секрет)

### 7.3 Полный список переменных окружения проекта

Все переменные, которые **обязаны** присутствовать в `.env` и `.env.example`:

```env
# GitHub
GITHUB_USER=
GITHUB_PAT=

# FastAPI
API_KEY=
SECRET_KEY=

# Foundry
FOUNDRY_BASE_URL=
FOUNDRY_DYNAMIC_PORT=
FOUNDRY_TIMEOUT=

# HuggingFace — оба варианта обязательны (разные части кода используют разные имена)
HF_TOKEN=
HUGGING_FACE_TOKEN=

# RAG
RAG_INDEX_PATH=

# Logging
LOG_LEVEL=

# Environment
ENVIRONMENT=
DEBUG=
```

### 7.4 Правила при добавлении нового параметра

```
ШАГ 1: Определить тип параметра
  — секрет (токен, ключ, пароль) → только в .env
  — публичная настройка          → в config.json напрямую

ШАГ 2: Добавить в .env
  НОВЫЙ_ПАРАМЕТР=реальное_значение

ШАГ 3: Добавить в .env.example
  НОВЫЙ_ПАРАМЕТР=описание_или_заглушка

ШАГ 4: Если нужен в config.json — добавить ссылку
  "новый_параметр": "${НОВЫЙ_ПАРАМЕТР}"

ШАГ 5: Убедиться что env_processor.py подхватит переменную
  через load_dotenv() → os.getenv('НОВЫЙ_ПАРАМЕТР')
```

### 7.5 Проверка при экспорте / передаче проекта

Перед передачей проекта другому разработчику или деплоем **обязательно** проверить:

- ✅ `.env` добавлен в `.gitignore` — реальные секреты не попадают в git
- ✅ `.env.example` содержит **все** переменные с заглушками
- ✅ `config.json` не содержит реальных токенов и паролей
- ✅ Все `${VAR_NAME}` в `config.json` имеют соответствующую запись в `.env.example`

### 7.6 Пример правильной связки

**.env** (не в git):
```env
HF_TOKEN=hf_реальный_токен
HUGGING_FACE_TOKEN=hf_реальный_токен
```

**.env.example** (в git):
```env
# Токен HuggingFace для закрытых моделей (Gemma, Llama и др.)
# Создать на: https://huggingface.co/settings/tokens
HF_TOKEN=hf_your_token_here
HUGGING_FACE_TOKEN=hf_your_token_here
```

**config.json** (в git):
```json
{
  "huggingface": {
    "token": "${HF_TOKEN}"
  }
}
```

---

## 📦 9. Управление зависимостями

### Синхронизация требований
- **ОБЯЗАТЕЛЬНО:** После любого изменения или пересоздания основного файла `requirements.txt` необходимо обновить частичные файлы зависимостей (`requirements_*.txt`).
- Это гарантирует корректную работу модульных установок и Docker-слоев.

---

## 📦 9. Управление зависимостями

### Синхронизация требований
- **ОБЯЗАТЕЛЬНО:** После любого изменения или пересоздания основного файла `requirements.txt` необходимо обновить частичные файлы зависимостей (`requirements_*.txt`).
- Это гарантирует корректную работу модульных установок (RAG, Extras, Dev) и оптимизацию Docker-слоев.

---

## 🎯 Стиль сообщений и комментариев

### Краткий технический стиль:
- ✅ "Запуск сервера..." вместо "Запускаем сервер..."
- ✅ "Поиск порта..." вместо "Ищем порт..."
- ✅ "Киллинг процессов..." вместо "Убиваем процессы..."
- ✅ "Загрузка модели..." вместо "Загружаем модель..."

### В комментариях:
- ✅ "# Поиск реального порта Foundry"
- ✅ "# Сохранение порта в переменную"
- ✅ "# Запуск FastAPI с передачей порта"

### В docstrings:
- ✅ "Проверка Foundry на порту"
- ✅ "Запуск сервера"




Изучи код.

Всегда делай подробные комментарии в коде, чтобы я понимал почему ты выбрал именно текое решение, а не другое. Это касается и всех последующих действий с кодом. 


В коментариях:
Используй существительные а не глагольные формы в комментариях.
Плохо:
Отправляет, Суммаризирует, Объединяет, ...
Хорошо:
Отправка, Суммаризация, Объединение, ..

Пример кода с комментариами:

```javascript/typescript
// connectors/openai-compat.js
// Универсальный коннектор для провайдеров с OpenAI-совместимым API.
//
// ПОЧЕМУ ОДИН ФАЙЛ ДЛЯ ВСЕХ, А НЕ ОТДЕЛЬНЫЙ ДЛЯ КАЖДОГО:
//   OpenAI, Mistral, Groq, DeepSeek, xAI, NVIDIA, Cohere, Anthropic (через прокси),
//   OpenRouter и custom self-hosted (Ollama, vLLM) — все используют один и тот же
//   формат: POST /v1/chat/completions с { model, messages }.
//   Дублировать один и тот же fetch-код в 8 местах — плохая практика.
//   Разница между провайдерами только в base URL и заголовках — это параметры.
//
// ПОЧЕМУ ОСТАЛСЯ ОТДЕЛЬНЫЙ gemini.js:
//   Gemini использует принципиально другой формат запроса (contents/parts),
//   другой endpoint и ключ в query-параметре. Его нельзя унифицировать.
//
// ПОЧЕМУ ОСТАЛСЯ ОТДЕЛЬНЫЙ openrouter.js:
//   OpenRouter поддерживает поле reasoning: { enabled: true }, которого нет
//   в стандартном OpenAI API. Это специфичная фича, требующая отдельной обработки.

// Base URL для каждого провайдера.
// Вынесено в константу чтобы не хардкодить в каждом вызове и легко менять.
export const PROVIDER_URLS = {
    openai:    'https://api.openai.com/v1/chat/completions',
    mistral:   'https://api.mistral.ai/v1/chat/completions',
    groq:      'https://api.groq.com/openai/v1/chat/completions',
    cohere:    'https://api.cohere.com/v2/chat',           // Cohere v2 chat endpoint
    deepseek:  'https://api.deepseek.com/chat/completions',
    xai:       'https://api.x.ai/v1/chat/completions',
    nvidia:    'https://integrate.api.nvidia.com/v1/chat/completions',
    anthropic: 'https://api.anthropic.com/v1/messages',   // Anthropic отличается форматом ответа
};

/**
 * Формирование заголовков запроса для конкретного провайдера.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic использует x-api-key вместо Authorization и требует
 *   дополнительный заголовок anthropic-version. Остальные — стандартный Bearer.
 *
 * @param {string} provider
 * @param {string} apiKey
 * @returns {object}
 */
function buildHeaders(provider, apiKey) {
    if (provider === 'anthropic') {
        return {
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01', // обязательный заголовок версии API Anthropic
            'Content-Type': 'application/json'
        };
    }
    return {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
    };
}

/**
 * Формирование тела запроса для конкретного провайдера.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic использует формат { model, messages, max_tokens } с обязательным max_tokens.
 *   NVIDIA требует stream: false явно (иначе может стримить).
 *   Остальные — минимальный { model, messages }.
 *
 * @param {string} provider
 * @param {string} model
 * @param {string} prompt
 * @returns {object}
 */
function buildBody(provider, model, prompt) {
    const messages = [{ role: 'user', content: prompt }];

    if (provider === 'anthropic') {
        return { model, messages, max_tokens: 8192 }; // Anthropic требует явный max_tokens
    }
    if (provider === 'nvidia') {
        return { model, messages, temperature: 0.15, top_p: 0.95, max_tokens: 8192, stream: false };
    }
    return { model, messages };
}
```

Не оставляй мертвый код. Удаляй ненужные файлы

В каждой директории должен находиться файл README.md, в котором описано назначение директории и обзор содержащихся файлов в директории





**Последнее обновление:** 2025

**Версия:** 0.3.1 (FastApi Foundry Edition)

**Статус:** ✅ Production Ready (некоммерческое использование, с атрибуцией)
