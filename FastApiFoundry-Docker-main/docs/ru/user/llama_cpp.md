# llama.cpp — бинарники и утилиты

Директория `bin/` содержит готовые Windows x64 бинарники llama.cpp (сборка от 15.04.2026).
Ниже описано назначение каждого исполняемого файла.

---

## Основные исполняемые файлы

### llama-server.exe (16.9 MB)

**Главный HTTP-сервер** с OpenAI-совместимым API.
Именно его запускает `start.ps1` / `Start-Llama.ps1` для работы с AI Assistant.

```powershell
.\bin\llama-server.exe -m D:\models\qwen2.5-0.5b-q4_k_m.gguf --port 9780 --host 0.0.0.0
```

Эндпоинты: `POST /completion`, `POST /v1/chat/completions`, `GET /health`, `GET /v1/models`.

---

### llama-cli.exe (9.2 MB)

**Интерактивный чат в терминале.** Запускает диалог с моделью прямо в консоли без HTTP-сервера.

```powershell
.\bin\llama-cli.exe -m D:\models\model.gguf -p "Привет!" -n 200
# Флаг -i — интерактивный режим (диалог)
.\bin\llama-cli.exe -m D:\models\model.gguf -i
```

---

### llama-bench.exe (4.1 MB)

**Бенчмарк производительности.** Измеряет скорость генерации (tokens/sec) и скорость обработки промпта (prompt processing).

```powershell
.\bin\llama-bench.exe -m D:\models\model.gguf
# Вывод: pp (prompt processing) и tg (token generation) в t/s
```

---

### llama-batched-bench.exe

**Бенчмарк батчевой обработки.** Тестирует производительность при параллельной обработке нескольких запросов одновременно (batch inference).

```powershell
.\bin\llama-batched-bench.exe -m D:\models\model.gguf -npp 128 -ntg 128 -npl 1,2,4
```

---

## Утилиты для работы с моделями

### llama-quantize.exe (375 KB)

**Квантизация моделей.** Конвертирует GGUF-модель в другой формат квантизации (Q4_K_M, Q5_K_M, Q8_0 и др.) для уменьшения размера или изменения качества.

```powershell
.\bin\llama-quantize.exe input.gguf output-q4km.gguf Q4_K_M
```

| Тип | Размер | Качество |
|---|---|---|
| Q4_K_M | ~4–5 GB | Лучший баланс |
| Q5_K_M | ~5–6 GB | Лучше качество |
| Q8_0 | ~8–9 GB | Максимальное |

---

### llama-gguf-split.exe (63 KB)

**Разбивка и сборка GGUF-файлов.** Разделяет большой GGUF на части (для FAT32 / ограничений файловой системы) или собирает части обратно.

```powershell
# Разбить на части по 4 GB
.\bin\llama-gguf-split.exe --split --split-max-size 4G model.gguf model-part
# Собрать обратно
.\bin\llama-gguf-split.exe --merge model-part-00001-of-00003.gguf model-merged.gguf
```

---

### llama-tokenize.exe (306 KB)

**Токенизация текста.** Показывает как модель разбивает текст на токены — полезно для отладки промптов и подсчёта токенов.

```powershell
.\bin\llama-tokenize.exe -m D:\models\model.gguf -p "Привет, мир!"
# Вывод: список токенов и их ID
```

---

### llama-imatrix.exe (7.2 MB)

**Вычисление importance matrix.** Генерирует матрицу важности весов на основе калибровочного датасета — используется для улучшения качества квантизации.

```powershell
.\bin\llama-imatrix.exe -m model-f16.gguf -f calibration_data.txt -o imatrix.dat
# Затем использовать imatrix.dat при квантизации:
.\bin\llama-quantize.exe --imatrix imatrix.dat model-f16.gguf model-q4km.gguf Q4_K_M
```

---

### llama-perplexity.exe (7.3 MB)

**Измерение перплексии (perplexity).** Оценивает качество модели на тестовом тексте — чем ниже значение, тем лучше модель предсказывает текст.

```powershell
.\bin\llama-perplexity.exe -m D:\models\model.gguf -f test_data.txt
```

---

### llama-results.exe (7.1 MB)

**Просмотр и сравнение результатов бенчмарков.** Читает сохранённые результаты `llama-bench` и выводит сводную таблицу для сравнения разных моделей или конфигураций.

```powershell
.\bin\llama-results.exe results.json
```

---

### llama-fit-params.exe (7.1 MB)

**Подбор параметров сэмплинга.** Автоматически подбирает оптимальные параметры генерации (temperature, top-p, top-k и др.) для достижения целевого качества.

```powershell
.\bin\llama-fit-params.exe -m D:\models\model.gguf -f reference_outputs.txt
```

---

### llama-template-analysis.exe (3.2 MB)

**Анализ chat-шаблонов.** Показывает как модель форматирует системный промпт и историю диалога согласно своему chat template (Jinja2).

```powershell
.\bin\llama-template-analysis.exe -m D:\models\model.gguf
```

---

## Мультимодальные утилиты

### llama-mtmd-cli.exe (7.2 MB)

**Мультимодальный CLI** (изображения + текст). Основной инструмент для работы с vision-моделями (LLaVA, MiniCPM-V, Qwen2-VL и др.).

```powershell
.\bin\llama-mtmd-cli.exe -m D:\models\llava-v1.6.gguf --mmproj mmproj.gguf -p "Что на картинке?" --image photo.jpg
```

---

### llama-mtmd-debug.exe (7.2 MB)

**Отладочная версия мультимодального CLI.** Аналог `llama-mtmd-cli.exe` с расширенным выводом для диагностики проблем с vision-моделями.

---

### llama-llava-cli.exe (27 KB)

**Устаревший CLI для LLaVA.** Тонкая обёртка над `llama-mtmd-cli.exe` для обратной совместимости со старыми скриптами под LLaVA 1.5/1.6.

---

### llama-minicpmv-cli.exe (27 KB)

**Устаревший CLI для MiniCPM-V.** Тонкая обёртка для обратной совместимости со скриптами под MiniCPM-V 2.x.

---

### llama-gemma3-cli.exe (27 KB)

**CLI для Gemma 3.** Специализированная обёртка для мультимодальных моделей Gemma 3 (текст + изображения).

```powershell
.\bin\llama-gemma3-cli.exe -m D:\models\gemma-3-4b-it-q4.gguf -p "Объясни квантовую физику"
```

---

### llama-qwen2vl-cli.exe (27 KB)

**CLI для Qwen2-VL.** Специализированная обёртка для мультимодальных моделей Qwen2 Vision-Language.

```powershell
.\bin\llama-qwen2vl-cli.exe -m D:\models\qwen2-vl-7b-q4.gguf --mmproj mmproj.gguf --image img.jpg -p "Опиши изображение"
```

---

## Специализированные утилиты

### llama-tts.exe (7.3 MB)

**Text-to-Speech.** Генерация речи из текста с помощью TTS-моделей в формате GGUF (например, OuteTTS).

```powershell
.\bin\llama-tts.exe -m D:\models\oute-tts.gguf -p "Привет, это тест синтеза речи" -o output.wav
```

---

### llama-completion.exe (7.2 MB)

**Однократная генерация без сервера.** Выполняет один запрос на completion и выводит результат — удобно для скриптов и пайплайнов.

```powershell
.\bin\llama-completion.exe -m D:\models\model.gguf -p "Напиши функцию на Python для сортировки списка" -n 300
```

---

### rpc-server.exe (103 KB)

**RPC-сервер для распределённого инференса.** Позволяет разнести слои модели по нескольким машинам в сети — один узел запускает `rpc-server.exe`, другой подключается к нему через `llama-server.exe --rpc`.

```powershell
# На удалённой машине:
.\bin\rpc-server.exe --host 0.0.0.0 --port 50052
# На основной машине:
.\bin\llama-server.exe -m model.gguf --rpc 192.168.1.100:50052
```

---

## Библиотеки (DLL)

| Файл | Размер | Назначение |
|---|---|---|
| `llama.dll` | 2.7 MB | Основная библиотека llama.cpp — ядро инференса |
| `mtmd.dll` | 1.1 MB | Мультимодальная библиотека (vision encoder) |

Все `.exe` файлы динамически линкуются с этими DLL — они должны находиться в той же директории.

---

## Сводная таблица

| Файл | Назначение | Используется в AI Assistant |
|---|---|---|
| `llama-server.exe` | HTTP-сервер (OpenAI API) | ✅ Основной |
| `llama-cli.exe` | Интерактивный чат в терминале | — |
| `llama-bench.exe` | Бенчмарк производительности | — |
| `llama-batched-bench.exe` | Бенчмарк батчевой обработки | — |
| `llama-quantize.exe` | Квантизация GGUF | — |
| `llama-gguf-split.exe` | Разбивка/сборка GGUF | — |
| `llama-tokenize.exe` | Токенизация текста | — |
| `llama-imatrix.exe` | Importance matrix для квантизации | — |
| `llama-perplexity.exe` | Оценка качества модели | — |
| `llama-results.exe` | Просмотр результатов бенчмарков | — |
| `llama-fit-params.exe` | Подбор параметров сэмплинга | — |
| `llama-template-analysis.exe` | Анализ chat-шаблонов | — |
| `llama-mtmd-cli.exe` | Мультимодальный CLI (vision) | — |
| `llama-mtmd-debug.exe` | Отладка мультимодальных моделей | — |
| `llama-llava-cli.exe` | LLaVA (legacy обёртка) | — |
| `llama-minicpmv-cli.exe` | MiniCPM-V (legacy обёртка) | — |
| `llama-gemma3-cli.exe` | Gemma 3 vision | — |
| `llama-qwen2vl-cli.exe` | Qwen2-VL vision | — |
| `llama-tts.exe` | Text-to-Speech | — |
| `llama-completion.exe` | Однократная генерация | — |
| `rpc-server.exe` | Распределённый инференс | — |
| `llama.dll` | Ядро llama.cpp | ✅ Зависимость |
| `mtmd.dll` | Vision encoder | ✅ Зависимость |

!!! tip "Какой файл нужен для работы с AI Assistant"
    Для стандартной работы через AI Assistant нужен только **`llama-server.exe`** — он запускается автоматически через `Start-Llama.ps1`. Остальные утилиты предназначены для ручной работы с моделями вне AI Assistant.

!!! warning "Зависимости DLL"
    Все бинарники требуют `llama.dll` в той же директории. Мультимодальные утилиты дополнительно требуют `mtmd.dll`. Не перемещайте `.exe` файлы без DLL.
