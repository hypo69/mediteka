## build_rules_index.py
## Скрипт индексирования модулей промптов в FAISS.
##
## Назначение:
##   Читает все .md и .json файлы из директории prompts/,
##   формирует корпус документов (documents.json),
##   вычисляет эмбеддинги через sentence-transformers,
##   сохраняет FAISS-индекс (rules.index).
##
## Запуск (из корня проекта):
##   python rag/build_rules_index.py
##
## Повторный запуск перестраивает индекс с нуля.

import json
import sys
from pathlib import Path

## src/secrets/ перекрывает stdlib secrets, что ломает huggingface_hub.
## Убираем src/ из sys.path до импорта sentence_transformers/faiss.
_src_path: str = str(Path(__file__).resolve().parent.parent / "src")
if _src_path in sys.path:
    sys.path.remove(_src_path)

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


## Пути
_ROOT: Path = Path(__file__).resolve().parent.parent
_PROMPTS_ROOT: Path = _ROOT / "prompts"
_RAG_DIR: Path = Path(__file__).resolve().parent
_DOCUMENTS_PATH: Path = _RAG_DIR / "documents.json"
_INDEX_PATH: Path = _RAG_DIR / "rules.index"

## Модель эмбеддингов
_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

## Файлы, которые индексируем (порядок влияет на приоритет при равных score)
_TARGET_GLOBS: list[str] = ["**/*.md", "**/*.json"]

## Файлы, которые пропускаем
_EXCLUDE_NAMES: set[str] = {"README.md"}


def _collect_documents() -> list[dict]:
    """
    ## hypo69 docblock
    Собирает корпус документов из директории prompts/.

    Каждый документ — один файл. Текст документа — полное содержимое файла.
    Для JSON-файлов добавляется префикс с именем файла, чтобы модель
    понимала контекст.

    Returns:
        list[dict]: Список документов вида
            {"file": str, "text": str, "path": str}
    """
    documents: list[dict] = []

    for glob in _TARGET_GLOBS:
        for file_path in sorted(_PROMPTS_ROOT.glob(glob)):
            if not file_path.is_file():
                continue
            if file_path.name in _EXCLUDE_NAMES:
                continue

            rel_path: str = str(file_path.relative_to(_PROMPTS_ROOT)).replace("\\", "/")
            raw_text: str = file_path.read_text(encoding="utf-8").strip()

            ## Для JSON добавляем мета-контекст в начало текста
            if file_path.suffix == ".json":
                text: str = f"[Файл: {file_path.name}]\n{raw_text}"
            else:
                text = raw_text

            documents.append({
                "file": file_path.name,
                "path": rel_path,
                "text": text,
            })

    return documents


def _build_index(documents: list[dict], model: SentenceTransformer) -> faiss.IndexFlatL2:
    """
    ## hypo69 docblock
    Создаёт FAISS-индекс из корпуса документов.

    Args:
        documents (list[dict]): Корпус документов.
        model (SentenceTransformer): Модель для вычисления эмбеддингов.

    Returns:
        faiss.IndexFlatL2: Готовый FAISS-индекс.
    """
    texts: list[str] = [doc["text"] for doc in documents]
    print(f"  Вычисляю эмбеддинги для {len(texts)} документов...")

    vectors: np.ndarray = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    dimension: int = vectors.shape[1]
    index: faiss.IndexFlatL2 = faiss.IndexFlatL2(dimension)
    index.add(vectors.astype(np.float32))

    return index


def main() -> None:
    """
    ## hypo69 docblock
    Точка входа: собирает документы, строит индекс, сохраняет файлы.
    """
    sys.stdout.reconfigure(encoding="utf-8")

    print(f"Корень промптов: {_PROMPTS_ROOT}")
    print(f"Индекс будет сохранён в: {_INDEX_PATH}")
    print()

    ## Сбор документов
    print("Шаг 1/3: Сбор документов...")
    documents: list[dict] = _collect_documents()

    if not documents:
        print("ОШИБКА: Документы не найдены. Проверьте путь к prompts/.")
        sys.exit(1)

    print(f"  Найдено документов: {len(documents)}")
    for doc in documents:
        words: int = len(doc["text"].split())
        print(f"    {doc['path']:<50}  {words:>5} слов")

    ## Сохранение корпуса
    print("\nШаг 2/3: Сохранение documents.json...")
    _DOCUMENTS_PATH.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Сохранено: {_DOCUMENTS_PATH}")

    ## Построение индекса
    print("\nШаг 3/3: Построение FAISS-индекса...")
    print(f"  Загрузка модели: {_MODEL_NAME}")
    model: SentenceTransformer = SentenceTransformer(_MODEL_NAME)

    index: faiss.IndexFlatL2 = _build_index(documents, model)

    faiss.write_index(index, str(_INDEX_PATH))
    print(f"  Индекс сохранён: {_INDEX_PATH}")
    print(f"  Размер индекса: {_INDEX_PATH.stat().st_size // 1024} KB")

    print("\nГотово. Индекс построен успешно.")


if __name__ == "__main__":
    main()
