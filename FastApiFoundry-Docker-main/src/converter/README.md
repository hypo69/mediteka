# Converter — GGUF → ONNX

Модуль конвертации локальных `.gguf` моделей в формат ONNX с опциональной оптимизацией.

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `gguf_to_onnx.py` | Класс `GGUFConverter` — логика экспорта и оптимизации |
| `__init__.py` | Экспорт `GGUFConverter`, `ConversionResult` |

API endpoint: `src/api/endpoints/converter.py`

---

## Как это работает

```
model.gguf (или HF директория)
        ↓
  ORTModelForCausalLM(export=True)   ← optimum[onnxruntime]
        ↓
  artifacts/onnx/
    ├── model.onnx
    ├── tokenizer.json
    └── config.json
        ↓ (если optimize=True)
  model_optimized.onnx               ← onnxruntime-tools
```

Тяжёлые операции (загрузка модели, экспорт, оптимизация) выполняются в `run_in_executor` — event loop FastAPI не блокируется.

---

## ⚠️ Ограничение: что такое "gguf_path"

`optimum` конвертирует модели через HuggingFace Transformers, а **не** парсит бинарный GGUF напрямую.

Поэтому `gguf_path` должен быть одним из:

| Вариант | Пример |
|---------|--------|
| HuggingFace model id | `google/gemma-2b` |
| Локальная HF директория (с `config.json`) | `./models/gemma-2b-hf/` |

Если у вас только голый `.gguf` файл (например, скачанный с HuggingFace GGUF-репозитория) — его нужно сначала конвертировать в HF формат через `llama.cpp/convert_hf_to_gguf.py` в обратную сторону, либо скачать оригинальную HF версию модели.

---

## API Endpoints

### GET `/v1/converter/status`

Проверить доступность зависимостей.

```json
{
  "success": true,
  "available": true,
  "optimizer_available": true,
  "dependencies": {
    "converter": "optimum[onnxruntime] + transformers",
    "optimizer": "onnxruntime-tools"
  }
}
```

### POST `/v1/converter/convert`

Запустить конвертацию.

**Тело запроса:**

```json
{
  "gguf_path": "google/gemma-2b",
  "output_dir": "./artifacts/onnx",
  "model_type": "gpt2",
  "opset": 17,
  "optimize": true
}
```

| Поле | Тип | По умолчанию | Описание |
|------|-----|-------------|---------|
| `gguf_path` | string | — | HF model id или путь к локальной HF директории |
| `output_dir` | string | `./artifacts/onnx` | Куда сохранить результат |
| `model_type` | string | `gpt2` | Тип для оптимизатора: `gpt2`, `bert`, `bart` |
| `opset` | int | `17` | Версия ONNX opset |
| `optimize` | bool | `true` | Запустить оптимизацию после экспорта |

**Ответ при успехе:**

```json
{
  "success": true,
  "output_dir": "./artifacts/onnx",
  "optimized_path": "./artifacts/onnx/model_optimized.onnx",
  "info": {
    "onnx_files": ["model.onnx"],
    "total_size_mb": 4821.3
  }
}
```

**Ответ при ошибке:**

```json
{
  "success": false,
  "error": "optimum[onnxruntime] не установлен. Выполните: pip install optimum[onnxruntime]"
}
```

---

## Установка зависимостей

```powershell
# Минимум для конвертации
pip install optimum[onnxruntime] onnxruntime

# С оптимизатором
pip install optimum[onnxruntime] onnxruntime onnxruntime-tools

# Или через скрипт проекта
pip install -r requirements.txt
```

Если зависимости не установлены — сервер запускается в штатном режиме, эндпоинт `/converter/status` сообщит о недоступности, `/converter/convert` вернёт `{"success": false, "error": "..."}`.

---

## Примеры использования

### Через curl

```powershell
# Проверить статус
curl http://localhost:9696/v1/converter/status

# Конвертировать модель с HuggingFace
curl -X POST http://localhost:9696/v1/converter/convert `
  -H "Content-Type: application/json" `
  -d '{
    "gguf_path": "google/gemma-2b",
    "output_dir": "./artifacts/onnx",
    "optimize": true
  }'
```

### Через Python

```python
import httpx

response = httpx.post(
    "http://localhost:9696/v1/converter/convert",
    json={
        "gguf_path": "google/gemma-2b",
        "output_dir": "./artifacts/onnx",
        "model_type": "gpt2",
        "opset": 17,
        "optimize": True,
    },
    timeout=600,  # конвертация занимает несколько минут
)
print(response.json())
```

---

## Время и ресурсы

| Модель | RAM | Время конвертации |
|--------|-----|------------------|
| gemma-2b / qwen-0.5b | ~8 GB | 5–15 мин |
| gemma-7b / qwen-7b | ~24 GB | 20–40 мин |

> Конвертация — однократная операция. Результат сохраняется в `output_dir` и используется повторно.
