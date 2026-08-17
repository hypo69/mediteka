---
languages:
  - id: ru
    name: Русский
    native: Русский
  - id: en
    name: English
    native: English
  - id: he
    name: עברית
    native: Hebrew
---

[Switch language | Переключить язык | החלף שפה 🌐](#language-switch)

<div lang="ru" style="display:none;">

# rag — FAISS-индекс правил и примеров

Директория содержит векторный индекс для RAG-поиска по модулям промптов медиатеки.

## Назначение

Вместо статической загрузки всех файлов промптов,
система выполняет семантический поиск и включает в промпт
только те модули, которые релевантны конкретному запросу.

Это сокращает размер промпта с ~20 000 до ~5 000–8 000 символов.

## Структура

```
rag/
├── build_rules_index.py   — скрипт построения индекса (запускать вручную)
├── rules.index            — FAISS-индекс (генерируется, не коммитить)
├── documents.json         — корпус документов (генерируется, не коммитить)
└── README.md              — этот файл
```

## Как пересобрать индекс

При добавлении или изменении любого файла в `prompts/`
необходимо пересобрать индекс:

```bash
python rag/build_rules_index.py
```

Скрипт:
1. Читает все `.md` и `.json` из `prompts/`
2. Создаёт `documents.json` (корпус)
3. Вычисляет эмбеддинги (`all-MiniLM-L6-v2`)
4. Сохраняет `rules.index`

## Модель

`sentence-transformers/all-MiniLM-L6-v2`

- Размер: ~90 MB
- Кешируется в `~/.cache/huggingface/` после первой загрузки
- Поддерживает многоязычные тексты (русский и английский)

## Использование в коде

```python
from src.prompt_loader import RulesRAG

rag = RulesRAG()
results = rag.search("правила для диктора", top_k=3)
for doc in results:
    print(doc["file"], doc["score"])
```

## .gitignore

Добавить в `.gitignore`:
```
rag/rules.index
rag/documents.json
```

Индекс генерируется локально и не должен попасть в репозиторий.

</div>

<div lang="en">

# rag — FAISS Index of Rules and Examples

Directory contains a vector index for RAG-search across media library prompt modules.

## Purpose

Instead of static loading of all prompt files,
the system performs semantic search and includes in the prompt
only those modules that are relevant to the specific query.

This reduces prompt size from ~20,000 to ~5,000–8,000 characters.

## Structure

```
rag/
├── build_rules_index.py   — index building script (run manually)
├── rules.index            — FAISS index (generated, don't commit)
├── documents.json         — document corpus (generated, don't commit)
└── README.md              — this file
```

## How to Rebuild the Index

When adding or changing any file in `prompts/`,
the index must be rebuilt:

```bash
python rag/build_rules_index.py
```

Script:
1. Reads all `.md` and `.json` from `prompts/`
2. Creates `documents.json` (corpus)
3. Computes embeddings (`all-MiniLM-L6-v2`)
4. Saves `rules.index`

## Model

`sentence-transformers/all-MiniLM-L6-v2`

- Size: ~90 MB
- Cached in `~/.cache/huggingface/` after first download
- Supports multilingual texts (Russian and English)

## Code Usage

```python
from src.prompt_loader import RulesRAG

rag = RulesRAG()
results = rag.search("narrator rules", top_k=3)
for doc in results:
    print(doc["file"], doc["score"])
```

## .gitignore

Add to `.gitignore`:
```
rag/rules.index
rag/documents.json
```

Index is generated locally and should not be committed to the repository.

</div>

<div lang="he" style="display:none;">

# rag — אינדקס FAISS של כללים ודוגמאות

התיקייה מכילה אינדקס וקטורי לחיפוש RAG במודולי פרומפטים של ספריית המדיה.

## מטרה

במקום טעינה סטטית של כל קבצי הפרומפטים,
המערכת מבצעת חיפוש סמנטי ומכללת בפרומפט
רק את המודולים הרלוונטיים לשאילתה הספציפית.

זה מקטין את גודל הפרומפט מ-~20,000 ל-~5,000–8,000 תווים.

## מבנה

```
rag/
├── build_rules_index.py   — סקריפט בניית אינדקס (הרץ ידנית)
├── rules.index            — אינדקס FAISS (נוצר, אל תבצע commit)
├── documents.json         — גוף מסמכים (נוצר, אל תבצע commit)
└── README.md              — קובץ זה
```

## כיצד לבנות מחדש את האינדקס

בעת הוספה או שינוי של קובץ ב-`prompts/`,
יש לבנות מחדש את האינדקס:

```bash
python rag/build_rules_index.py
```

סקריפט:
1. קורא את כל ה-`.md` ו-`.json` מ-`prompts/`
2. יוצר `documents.json` (גוף)
3. מחשב הטמעות (`all-MiniLM-L6-v2`)
4. שומר `rules.index`

## מודל

`sentence-transformers/all-MiniLM-L6-v2`

- גודל: ~90 MB
- נשמר ב-`~/.cache/huggingface/` אחרי ההורדה הראשונה
- תומך בטקסטים רב-לשוניים (רוסית ואנגלית)

## שימוש בקוד

```python
from src.prompt_loader import RulesRAG

rag = RulesRAG()
results = rag.search("כללי קריין", top_k=3)
for doc in results:
    print(doc["file"], doc["score"])
```

## .gitignore

הוסף ל-`.gitignore`:
```
rag/rules.index
rag/documents.json
```

האינדקס נוצר מקומית ולא צריך להיות מתועד במאגר.

</div>

---

## Language Switch / Переключатель языков / החלפת שפה 🌐

<div align="center">

**[Русский 🇷🇺](#language-switch)** | **[English 🇺🇸](#language-switch)** | **[עברית 🇮🇱](#language-switch)**

</div>

**Instructions:** Search for `<div lang="...">` blocks above and toggle `style="display:none;"` to switch language.

**Инструкции:** Найдите блоки `<div lang="...">` выше и переключите `style="display:none;"` для смены языка.

**הוראות:** חפשו בלוקים `<div lang="...">` למעלה והחליפו את `style="display:none;"` להחלפת שפה.

---

## Translation Status / Статус перевода / סטטוס תרגום

| Language | Status |
|----------|--------|
| 🇷🇺 Russian | ✓ Translated |
| 🇺🇸 English | ✓ Default |
| 🇮🇱 Hebrew | ✓ Translated |