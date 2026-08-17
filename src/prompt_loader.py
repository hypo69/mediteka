## prompt_loader.py
## Сборщик системных промптов из модульных файлов.
##
## Два режима работы:
##   1. Статический (load_chat_prompt_static / load_narrator_prompt_static):
##      загружает все модули напрямую из файлов. Используется как резерв.
##
##   2. RAG (load_chat_prompt / load_narrator_prompt):
##      выполняет семантический поиск по FAISS-индексу и включает
##      только релевантные модули. Требует предварительного запуска
##      rag/build_rules_index.py.
##
## Использование:
##   from src.prompt_loader import load_chat_prompt, load_narrator_prompt
##   system_prompt = load_chat_prompt("Описание сериала про войну")

import json
import sys
from dataclasses import dataclass
from pathlib import Path


## Базовые пути
_PROMPTS_ROOT: Path = Path(__file__).resolve().parent.parent / "prompts"
_RAG_DIR: Path = Path(__file__).resolve().parent.parent / "rag"
_INDEX_PATH: Path = _RAG_DIR / "rules.index"
_DOCUMENTS_PATH: Path = _RAG_DIR / "documents.json"

## Модель эмбеддингов (та же, что в build_rules_index.py)
_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

## Модули, общие для обоих агентов (статический режим)
_CORE_MODULES: list[str] = [
    "core/identity.md",
    "core/categories.md",
]

## Модули только для чат-агента (статический режим)
_CHAT_MODULES: list[str] = [
    "chat/chat_rules.md",
    "narrator/narrator_style.md",
]

## Модули только для агента-диктора (статический режим)
_NARRATOR_MODULES: list[str] = [
    "narrator/tts_rules.md",
    "narrator/narrator_style.md",
]

## Пример (статический режим)
_EXAMPLE_MODULE: str = "examples/series_example.json"

## JSON-схема (статический режим)
_SCHEMA_MODULE: str = "core/output_schema.json"

## Файлы, которые всегда включаются в RAG-промпт (независимо от поиска).
## Только маленькие базовые модули — схема и примеры подтягиваются через FAISS.
_ALWAYS_INCLUDE: list[str] = [
    "identity.md",
    "categories.md",
]


## ---------------------------------------------------------------------------
## Вспомогательные функции
## ---------------------------------------------------------------------------


def _read_file(relative_path: str) -> str:
    """
    ## hypo69 docblock
    Читает файл из директории промптов.

    Args:
        relative_path (str): Путь относительно _PROMPTS_ROOT.

    Returns:
        str: Содержимое файла.

    Raises:
        FileNotFoundError: Если файл не найден.
    """
    full_path: Path = _PROMPTS_ROOT / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Модуль промпта не найден: {full_path}")
    return full_path.read_text(encoding="utf-8")


def _load_modules(module_paths: list[str]) -> str:
    """
    ## hypo69 docblock
    Загружает и конкатенирует несколько модулей промпта.

    Args:
        module_paths (list[str]): Список относительных путей к модулям.

    Returns:
        str: Объединённое содержимое всех модулей.
    """
    parts: list[str] = [_read_file(p).strip() for p in module_paths]
    return "\n\n---\n\n".join(parts)


def _load_schema_block() -> str:
    """
    ## hypo69 docblock
    Загружает JSON-схему и оборачивает в markdown-блок.

    Returns:
        str: Строка с JSON-схемой в markdown-обёртке.
    """
    raw: str = _read_file(_SCHEMA_MODULE)
    parsed: dict = json.loads(raw)
    formatted: str = json.dumps(parsed, ensure_ascii=False, indent=2)
    return f"## JSON Schema ответа\n\n```json\n{formatted}\n```"


def _load_example_block() -> str:
    """
    ## hypo69 docblock
    Загружает пример JSON и оборачивает в markdown-блок.

    Returns:
        str: Строка с примером в markdown-обёртке.
    """
    raw: str = _read_file(_EXAMPLE_MODULE)
    parsed: dict = json.loads(raw)
    formatted: str = json.dumps(parsed, ensure_ascii=False, indent=2)
    return f"## Пример заполненного ответа (сериал)\n\n```json\n{formatted}\n```"


## ---------------------------------------------------------------------------
## RulesRAG — класс семантического поиска
## ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """Результат поиска по индексу."""
    file: str
    path: str
    text: str
    score: float


class RulesRAG:
    """
    ## hypo69 docblock
    Семантический поиск по модулям промптов через FAISS.

    Требует предварительного запуска:
        python rag/build_rules_index.py

    Attributes:
        _index: FAISS-индекс.
        _documents (list[dict]): Корпус документов.
        _model: Модель sentence-transformers.
    """

    def __init__(self) -> None:
        """
        ## hypo69 docblock
        Загружает FAISS-индекс, корпус документов и модель эмбеддингов.

        Raises:
            FileNotFoundError: Если индекс или корпус не найдены.
        """
        import sys as _sys

        ## src/secrets/ перекрывает stdlib secrets, что ломает huggingface_hub.
        ## Временно убираем src/ из путей поиска до импорта тяжёлых библиотек.
        _src_path: str = str(Path(__file__).resolve().parent)
        _removed: bool = _src_path in _sys.path
        if _removed:
            _sys.path.remove(_src_path)

        try:
            import faiss
            import numpy as np
            from sentence_transformers import SentenceTransformer
        finally:
            ## Восстанавливаем путь независимо от результата импорта
            if _removed:
                _sys.path.insert(0, _src_path)

        if not _INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS-индекс не найден: {_INDEX_PATH}\n"
                "Запустите: python rag/build_rules_index.py"
            )
        if not _DOCUMENTS_PATH.exists():
            raise FileNotFoundError(
                f"Корпус не найден: {_DOCUMENTS_PATH}\n"
                "Запустите: python rag/build_rules_index.py"
            )

        self._faiss = faiss
        self._np = np
        self._index = faiss.read_index(str(_INDEX_PATH))
        self._documents: list[dict] = json.loads(
            _DOCUMENTS_PATH.read_text(encoding="utf-8")
        )
        self._model: SentenceTransformer = SentenceTransformer(
            _MODEL_NAME,
            local_files_only=True,
        )

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        """
        ## hypo69 docblock
        Выполняет семантический поиск по корпусу правил.

        Args:
            query (str): Запрос на русском или английском языке.
            top_k (int): Количество возвращаемых результатов. По умолчанию 4.

        Returns:
            list[SearchResult]: Список результатов, отсортированных по релевантности.
        """
        vector = self._model.encode([query], convert_to_numpy=True).astype(self._np.float32)
        distances, indices = self._index.search(vector, top_k)

        results: list[SearchResult] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc: dict = self._documents[idx]
            results.append(SearchResult(
                file=doc["file"],
                path=doc["path"],
                text=doc["text"],
                score=float(dist),
            ))
        return results

    def build_context(self, query: str, top_k: int = 4) -> str:
        """
        ## hypo69 docblock
        Собирает текстовый контекст из найденных документов для вставки в промпт.

        Всегда добавляет обязательные модули (_ALWAYS_INCLUDE) и дополняет
        результатами семантического поиска.

        Args:
            query (str): Запрос пользователя.
            top_k (int): Количество дополнительных результатов из поиска.

        Returns:
            str: Конкатенированный контекст всех релевантных модулей.
        """
        ## Сначала собираем обязательные модули по имени файла
        always_docs: list[str] = []
        for doc in self._documents:
            if doc["file"] in _ALWAYS_INCLUDE:
                always_docs.append(doc["text"].strip())

        ## Семантический поиск — исключаем уже добавленные
        search_results: list[SearchResult] = self.search(query, top_k=top_k)
        search_docs: list[str] = []
        for result in search_results:
            if result.file not in _ALWAYS_INCLUDE:
                search_docs.append(result.text.strip())

        all_parts: list[str] = always_docs + search_docs
        return "\n\n---\n\n".join(all_parts)


## ---------------------------------------------------------------------------
## Публичные функции сборки промптов (RAG-режим)
## ---------------------------------------------------------------------------


def load_chat_prompt(query: str = "Создать описание медиа для чата") -> str:
    """
    ## hypo69 docblock
    Собирает системный промпт для Chat Agent через FAISS-поиск.

    Args:
        query (str): Запрос, по которому выбираются релевантные модули.
                     По умолчанию — универсальный запрос для чат-агента.

    Returns:
        str: Готовый системный промпт для чат-агента (~5 000–8 000 символов).
    """
    rag: RulesRAG = RulesRAG()
    context: str = rag.build_context(query, top_k=4)
    return context


def load_narrator_prompt(query: str = "Подготовить текст для голосового диктора TTS") -> str:
    """
    ## hypo69 docblock
    Собирает системный промпт для Narrator Agent через FAISS-поиск.

    Args:
        query (str): Запрос, по которому выбираются релевантные модули.
                     По умолчанию — запрос для TTS-режима.

    Returns:
        str: Готовый системный промпт для агента-диктора (~5 000–8 000 символов).
    """
    rag: RulesRAG = RulesRAG()
    context: str = rag.build_context(query, top_k=4)
    return context


## ---------------------------------------------------------------------------
## Резервные статические функции (без FAISS)
## ---------------------------------------------------------------------------


def load_chat_prompt_static() -> str:
    """
    ## hypo69 docblock
    Собирает полный промпт для Chat Agent из файлов без FAISS.

    Используется как резерв если индекс не построен.

    Returns:
        str: Полный промпт для чат-агента (~20 000 символов).
    """
    sections: list[str] = [
        _load_modules(_CORE_MODULES),
        _load_schema_block(),
        _load_modules(_CHAT_MODULES),
        _load_example_block(),
    ]
    return "\n\n---\n\n".join(sections)


def load_narrator_prompt_static() -> str:
    """
    ## hypo69 docblock
    Собирает полный промпт для Narrator Agent из файлов без FAISS.

    Используется как резерв если индекс не построен.

    Returns:
        str: Полный промпт для агента-диктора (~20 000 символов).
    """
    sections: list[str] = [
        _load_modules(_CORE_MODULES),
        _load_schema_block(),
        _load_modules(_NARRATOR_MODULES),
        _load_example_block(),
    ]
    return "\n\n---\n\n".join(sections)


## ---------------------------------------------------------------------------
## Точка входа — быстрая проверка
## ---------------------------------------------------------------------------


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== Статический режим ===")
    chat_s: str = load_chat_prompt_static()
    narrator_s: str = load_narrator_prompt_static()
    print(f"Chat (static):     {len(chat_s):>6} символов  |  {len(chat_s.split()):>5} слов")
    print(f"Narrator (static): {len(narrator_s):>6} символов  |  {len(narrator_s.split()):>5} слов")

    print()
    if not _INDEX_PATH.exists():
        print("FAISS-индекс не найден. Запустите: python rag/build_rules_index.py")
        sys.exit(0)

    print("=== RAG-режим ===")
    rag: RulesRAG = RulesRAG()

    test_queries: list[str] = [
        "Описание сериала",
        "Правила для диктора TTS",
        "Категории медиа боевики шпионы",
    ]
    for q in test_queries:
        results = rag.search(q, top_k=3)
        files: list[str] = [r.file for r in results]
        print(f"  '{q}' → {files}")

    print()
    chat_r: str = load_chat_prompt("Описание сериала")
    narrator_r: str = load_narrator_prompt("Текст для диктора")
    print(f"Chat (RAG):        {len(chat_r):>6} символов  |  {len(chat_r.split()):>5} слов")
    print(f"Narrator (RAG):    {len(narrator_r):>6} символов  |  {len(narrator_r.split()):>5} слов")

    reduction: float = (1 - len(chat_r) / len(chat_s)) * 100
    print(f"\nСжатие промпта: {reduction:.0f}%")
