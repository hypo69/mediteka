# Make-Ico.ps1

Конвертирует PNG-иконки в многоразмерный `.ico`-файл без внешних инструментов.

**Файл:** `install\Make-Ico.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Make-Ico.ps1`

---

## Назначение

Собирает `icon.ico` из трёх PNG-файлов:
- `assets\icons\icon16.png`
- `assets\icons\icon48.png`
- `assets\icons\icon128.png`

Использует `.NET System.Drawing` — Node.js, ImageMagick и другие внешние инструменты не нужны.

---

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `-ProjectRoot` | string | Родительская директория скрипта | Корень проекта |

---

## Примеры

```powershell
# Стандартный запуск из корня проекта
powershell -ExecutionPolicy Bypass -File .\install\Make-Ico.ps1

# Указать корень явно
powershell -ExecutionPolicy Bypass -File .\install\Make-Ico.ps1 -ProjectRoot "D:\project"
```

---

## Функции

### ConvertTo-Ico

Объединяет несколько PNG-файлов в один многоразмерный `.ico`.

**Параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `$PngPaths` | string[] | Упорядоченный список PNG (от маленького к большому) |
| `$OutputPath` | string | Путь к выходному `.ico`-файлу |

**Формат ICO:**
```
6 байт заголовка
+ N × 16 байт записей директории
+ блоки данных изображений (PNG-формат)
```

---

## Результат

```
icon.ico  ← в корне проекта
  ├── 16×16 px
  ├── 48×48 px
  └── 128×128 px
```

Файл используется:
- Ярлыками на рабочем столе (`Install-Shortcuts.ps1`)
- Веб-интерфейсом (`static/interface/index.html`)
- MkDocs (`mkdocs.yml → theme.favicon`)

