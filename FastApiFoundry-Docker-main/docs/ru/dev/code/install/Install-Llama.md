# Install-Llama.ps1

Распаковывает Windows-бинарник llama.cpp и прописывает пути в `config.json`.

**Файл:** `install\Install-Llama.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Llama.ps1`

---

## Назначение

1. Читает `directories.models` из `config.json` как директорию моделей по умолчанию
2. Ищет `bin\llama-*-bin-win-*.zip` — берёт последний по имени
3. Распаковывает архив в `bin\<имя архива без .zip>\`
4. Обновляет `config.json`: `llama_cpp.bin_version` и `llama_cpp.model_path`
5. Создаёт директорию моделей если не существует

---

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `-ModelsDir` | string | из `config.json` или `~/.models` | Путь к директории GGUF-моделей |

---

## Примеры

```powershell
# Стандартная настройка
powershell -ExecutionPolicy Bypass -File .\install\Install-Llama.ps1

# Указать другую директорию моделей
powershell -ExecutionPolicy Bypass -File .\install\Install-Llama.ps1 -ModelsDir "D:\models"
```

---

## Результат в config.json

```json
{
  "directories": { "models": "~/.models" },
  "llama_cpp": {
    "bin_version": "llama-b8802-bin-win-cpu-x64",
    "model_path": "C:\\Users\\user\\.models"
  }
}
```

!!! warning "Бинарник в репозитории"
    Архив `bin\llama-*-bin-win-cpu-x64.zip` включён в репозиторий. GPU-версии нужно скачивать отдельно с [github.com/ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/releases).

