# Prompts — модульная система промптов

Директория содержит атомарные файлы инструкций для AI-агентов медиатеки.
Вместо одного монолитного промпта используется набор специализированных модулей,
которые собираются в нужную комбинацию через `prompt_loader.py`.

## Структура

```
prompts/
│
├── core/                        — базовые модули (нужны всегда)
│   ├── identity.md              — кто агент и что он делает
│   ├── categories.md            — 11 разрешённых категорий медиа
│   └── output_schema.json       — JSON Schema структуры ответа
│
├── narrator/                    — модули для режима диктора
│   ├── tts_rules.md             — правила TTS: числа словами, только русский
│   └── narrator_style.md        — стиль текста: запрет «это», размеры полей
│
├── chat/                        — модули для режима чата
│   └── chat_rules.md            — правила чат-агента
│
├── examples/                    — примеры заполненных JSON
│   └── series_example.json      — эталонный пример для сериала
│
└── media_organizer/             — точка сборки основного агента
    ├── system_instruction.md    — индекс: ссылки на все модули
    ├── prompt_research.md       — правила для режима исследования
    └── prompt_tts.md            — дополнительные TTS-правила
```

## Какой агент получает какие модули

| Модуль | Chat Agent | Narrator Agent |
|---|:---:|:---:|
| `core/identity.md` | ✓ | ✓ |
| `core/categories.md` | ✓ | ✓ |
| `core/output_schema.json` | ✓ | ✓ |
| `narrator/tts_rules.md` | — | ✓ |
| `narrator/narrator_style.md` | ✓ | ✓ |
| `chat/chat_rules.md` | ✓ | — |
| `examples/series_example.json` | ✓ | ✓ |

## Сборка промптов

Промпты собираются через `src/prompt_loader.py`:

```python
from src.prompt_loader import load_chat_prompt, load_narrator_prompt

chat_prompt = load_chat_prompt()
narrator_prompt = load_narrator_prompt()
```

## Принципы модификации

- Каждый файл отвечает за одну задачу.
- При изменении правил редактируется только соответствующий модуль.
- Новые правила добавляются как новый файл, а не расширяют существующий.
- При добавлении нового файла — обновить эту таблицу и `prompt_loader.py`.
