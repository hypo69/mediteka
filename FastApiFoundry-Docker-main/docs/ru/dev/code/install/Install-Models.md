# Install-Models.ps1

Загружает модели по умолчанию для Foundry Local, HuggingFace и llama.cpp.

**Файл:** `install\Install-Models.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Models.ps1`

---

## Назначение

Запускается автоматически из `install.ps1` при первой установке или вручную в любое время.

### Foundry Local
Предлагает скачать `qwen3-0.6b-generic-cpu:4` (~300 МБ) через `foundry model download`.

### HuggingFace (RAG)
Предлагает скачать `sentence-transformers/all-MiniLM-L6-v2` (~90 МБ) — модель эмбеддингов для RAG.

### llama.cpp GGUF
- Сканирует директорию моделей (`llama_cpp.models_dir` или `directories.models` из `config.json`)
- Показывает нумерованный список найденных `.gguf`-файлов с размерами
- Позволяет выбрать модель по умолчанию → записывает в `config.json`
- Если моделей нет — показывает инструкцию по скачиванию

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-SkipFoundry` | switch | Пропустить раздел Foundry |
| `-SkipHuggingFace` | switch | Пропустить раздел HuggingFace |
| `-SkipLlama` | switch | Пропустить раздел llama.cpp |

---

## Примеры

```powershell
# Полная загрузка (интерактивно)
powershell -ExecutionPolicy Bypass -File .\install\Install-Models.ps1

# Только llama.cpp
powershell -ExecutionPolicy Bypass -File .\install\Install-Models.ps1 -SkipFoundry -SkipHuggingFace

# Только Foundry
powershell -ExecutionPolicy Bypass -File .\install\Install-Models.ps1 -SkipHuggingFace -SkipLlama
```

---

## Скачивание GGUF-моделей вручную

```powershell
pip install huggingface_hub
huggingface-cli download bartowski/gemma-2-2b-it-GGUF `
    gemma-2-2b-it-Q6_K.gguf --local-dir ~/.models
```

| Квантование | Размер | Рекомендация |
|---|---|---|
| Q4_K_M | ~4–5 ГБ | Лучший баланс |
| Q5_K_M | ~5–6 ГБ | Лучше качество |
| Q8_0 | ~8–9 ГБ | Максимальное качество |

