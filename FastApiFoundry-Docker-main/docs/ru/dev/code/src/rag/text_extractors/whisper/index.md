# whisper

Локальная транскрипция аудиофайлов через [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Работает полностью оффлайн — никаких облачных API не требуется.

## Установка

```bash
pip install faster-whisper
```

## Поддерживаемые форматы

`.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm`

## Использование

```python
from src.rag.text_extractors.whisper import WhisperExtractor

extractor = WhisperExtractor(
    model_size="base",   # tiny | base | small | medium | large-v2 | large-v3
    device="cpu",        # cpu | cuda
    compute_type="int8", # int8 (CPU) | float16 (GPU)
    language=None,       # None = автоопределение, "ru" / "en" = принудительно
)

# Из файла
result = extractor.extract_from_file("interview.mp3")
# {
#   "text": "Полный текст транскрипции...",
#   "filename": "interview.mp3",
#   "language": "ru",
#   "segments": [{"start": 0.0, "end": 3.5, "text": "Первый сегмент"}, ...]
# }

# Из байтов
with open("lecture.wav", "rb") as f:
    result = extractor.extract_from_bytes(f.read(), "lecture.wav")

# Проверка поддержки формата
extractor.is_supported("audio.mp3")   # True
extractor.is_supported("report.pdf")  # False
```

## Модели и требования к железу

| Модель | Размер | RAM | Рекомендация |
|---|---|---|---|
| `tiny` | 75 MB | ~1 GB | Быстрый прототип |
| `base` | 145 MB | ~1 GB | Баланс скорость/качество (по умолчанию) |
| `small` | 465 MB | ~2 GB | Хорошее качество |
| `medium` | 1.5 GB | ~5 GB | Высокое качество |
| `large-v3` | 3 GB | ~10 GB | Максимальное качество |

Модель загружается лениво при первом вызове и кэшируется.
При первом запуске скачивается в `~/.cache/huggingface/hub`.

!!! tip
    Для русскоязычных записей рекомендуется `small` или `medium`.
    Укажите `language="ru"` явно, чтобы избежать ошибок автоопределения.
