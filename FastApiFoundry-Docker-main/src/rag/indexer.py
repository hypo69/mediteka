# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Индексатор RAG для FastAPI Foundry
# =============================================================================
# Описание:
#   Построение индекса FAISS на основе проектной документации.
#   Поддерживает форматы Markdown, HTML, TXT, RST.
#
# Примеры:
#   >>> from src.rag.indexer import RAGIndexer
#   >>> indexer = RAGIndexer(); indexer.load_model()
#   >>> indexer.index_directory(Path("docs")); indexer.save_index(Path("rag_index"))
#
#   CLI:
#   python -m src.rag.indexer --docs-dir docs --output-dir rag_index
#
# File: indexer.py
# Project: Ai Assistant (Docker)
# Version: 0.6.5
# Изменения в 0.6.5:
#   - Полная русификация комментариев и документации
#   - Обновление лицензии на MIT (автор: hypo69)
#   - Строгая типизация возвращаемых значений
#   - Добавление комментариев в стиле "Проверка ..." для условий if
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================
import faiss
import argparse
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    print('Зависимости RAG не установлены: pip install sentence-transformers faiss-cpu')
    raise

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.md', '.txt', '.html', '.rst'}


class RAGIndexer:
    """Класс для индексации документов в системе RAG."""

    def __init__(self, model_name: str = 'sentence-transformers/all-mpnet-base-v2') -> None:
        """Инициализация индексатора.

        Args:
            model_name (str): Имя модели sentence-transformer. По умолчанию 'sentence-transformers/all-mpnet-base-v2'.
        """
        self.model_name = model_name
        self.model = None
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings = None
        self.docs_root: Optional[Path] = None
        self.has_changes: bool = False

    def load_model(self) -> None:
        """Загрузка модели эмбеддингов.

        Raises:
            Exception: Если не удалось загрузить модель (неверное имя или отсутствие связи).
        """
        logger.info(f'Загрузка модели: {self.model_name}')
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info('✅ Модель загружена')
        except Exception as e:
            # Ошибка может возникнуть из-за отсутствия интернета или неверного имени модели
            logger.error(f'❌ Не удалось загрузить модель "{self.model_name}": {e}')
            raise

    def _read_file(self, file_path: Path) -> str:
        """Чтение содержимого файла.

        Args:
            file_path (Path): Путь к файлу.

        Returns:
            str: Текстовое содержимое файла или пустая строка в случае ошибки.
        """
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            # Проверка кодировки: если файл не в UTF-8, он будет пропущен
            logger.warning(f'⚠️ Ошибка кодировки при чтении {file_path}: {e}')
            return ''
        except OSError as e:
            # Проверка доступности: файл может быть занят или отсутствовать права доступа
            logger.warning(f'⚠️ Не удалось прочитать файл {file_path}: {e}')
            return ''

    def _calculate_checksum(self, content: str) -> str:
        """Расчет SHA256 контрольной суммы для содержимого.

        Args:
            content (str): Строковое содержимое.

        Returns:
            str: Хеш-сумма в виде строки.
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 50) -> List[str]:
        """Разбиение текста на перекрывающиеся чанки.

        Args:
            text (str): Исходный текст.
            chunk_size (int): Размер чанка.
            overlap (int): Размер перекрытия.

        Returns:
            List[str]: Список текстовых фрагментов.
        """
        # Проверка длины текста: если он меньше размера чанка, возвращаем целиком
        if len(text) <= chunk_size:
            return [text]
        chunks, start = [], 0
        while start < len(text):
            end = start + chunk_size
            # Проверка выхода за границы текста
            if end < len(text):
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    # Проверка знаков препинания для корректного разрыва
                    if text[i] in '.!?':
                        end = i + 1
                        break
            chunk = text[start:end].strip()
            # Проверка наличия содержимого в чанке
            if chunk:
                chunks.append(chunk)
            start = end - overlap
        return chunks

    def process_markdown(self, content: str, metadata: Dict[str, Any], chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Обработка Markdown с учетом структуры разделов.

        Args:
            content (str): Содержимое файла.
            metadata (Dict[str, Any]): Метаданные файла.
            chunk_size (int): Размер чанка.
            overlap (int): Перекрытие.

        Returns:
            List[Dict[str, Any]]: Список словарей с чанками и метаданными.
        """
        chunks: List[Dict[str, Any]] = []
        current_section = 'Introduction'
        current_lines: List[str] = []

        for line in content.split('\n'):
            line = line.strip()
            # Проверка начала заголовка
            if line.startswith('#'):
                # Проверка наличия накопленных строк перед новым разделом
                if current_lines:
                    text = '\n'.join(current_lines).strip()
                    # Проверка пустоты текста
                    if text:
                        for c in self.chunk_text(text, chunk_size, overlap):
                            chunks.append({**metadata, 'section': current_section, 'text': c, 'char_count': len(c)})
                current_section = line.lstrip('#').strip()
                current_lines = []
            # Проверка наличия текста в строке
            elif line:
                current_lines.append(line)

        # Проверка хвоста после завершения цикла
        if current_lines:
            text = '\n'.join(current_lines).strip()
            # Проверка пустоты текста
            if text:
                for c in self.chunk_text(text, chunk_size, overlap):
                    chunks.append({**metadata, 'section': current_section, 'text': c, 'char_count': len(c)})
        return chunks

    def process_file(self, file_path: Path,
                     chunk_size: int = 1000, overlap: int = 50,
                     content: Optional[str] = None) -> List[Dict[str, Any]]:
        """Обработка одного файла и разбивка на чанки.

        Args:
            file_path (Path): Путь к файлу.
            chunk_size (int): Размер фрагмента.
            overlap (int): Перекрытие.
            content (Optional[str]): Предзагруженное содержимое (если есть).

        Returns:
            List[Dict[str, Any]]: Список обработанных фрагментов.
        """
        # Проверка наличия предзагруженного контента
        if content is None:
            content = self._read_file(file_path)
            
        # Проверка пустоты контента
        if not content:
            return []

        # Проверка наличия корня документов для вычисления относительного пути
        rel_path = str(file_path.relative_to(self.docs_root)) if self.docs_root else file_path.name

        metadata = {
            'source': file_path.name,
            'path': rel_path,
            'checksum': self._calculate_checksum(content),
            'mtime': file_path.stat().st_mtime if file_path.exists() else 0
        }

        # Проверка расширения файла: для Markdown особая обработка
        if file_path.suffix.lower() == '.md':
            return self.process_markdown(content, metadata, chunk_size, overlap)

        return [
            {**metadata, 'section': 'Content', 'text': c, 'char_count': len(c)}
            for c in self.chunk_text(content, chunk_size, overlap)
        ]

    def index_directory(self, docs_dir: Path,
                        chunk_size: int = 1000, overlap: int = 50,
                        existing_chunks: Optional[List[Dict[str, Any]]] = None) -> None:
        """Рекурсивная индексация всех поддерживаемых файлов в директории.

        Args:
            docs_dir (Path): Корневая папка с документами.
            chunk_size (int): Размер фрагмента.
            overlap (int): Перекрытие.
            existing_chunks (Optional[List[Dict[str, Any]]]): Ранее созданные чанки для инкрементальной проверки.
        """
        logger.info(f'Индексация директории: {docs_dir}')
        # Проверка существования директории
        if not docs_dir.exists():
            logger.error(f'❌ Директория документов не найдена: {docs_dir}')
            return

        self.docs_root = docs_dir
        self.has_changes = False
        
        # Подготовка карты существующих файлов
        existing_map: Dict[str, List[Dict[str, Any]]] = {}
        # Проверка наличия существующих чанков для ускорения процесса
        if existing_chunks:
            for i, c in enumerate(existing_chunks):
                path = c.get('path')
                # Проверка наличия пути в метаданных чанка
                if path:
                    chunk_with_idx = c.copy()
                    chunk_with_idx['_old_idx'] = i
                    existing_map.setdefault(path, []).append(chunk_with_idx)

        files_processed = 0
        found_paths = set()

        try:
            for file_path in docs_dir.rglob('*'):
                # Проверка: является ли путь файлом и входит ли расширение в список поддерживаемых
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    rel_path = str(file_path.relative_to(self.docs_root))
                    found_paths.add(rel_path)
                    
                    content = self._read_file(file_path)
                    # Проверка успешности чтения файла
                    if not content:
                        continue
                        
                    checksum = self._calculate_checksum(content)
                    
                    # Проверка изменений: если файл не изменился, используем старые чанки
                    if rel_path in existing_map and existing_map[rel_path][0].get('checksum') == checksum:
                        self.chunks.extend(existing_map[rel_path])
                    else:
                        logger.info(f'Обработка файла: {file_path}')
                        self.chunks.extend(self.process_file(file_path, chunk_size, overlap, content=content))
                        self.has_changes = True
                        files_processed += 1
        except Exception as e:
            logger.error(f'❌ Ошибка при сканировании {docs_dir}: {e}')

        # Проверка на удаление файлов: если изменений еще не зафиксировано, проверяем отсутствие путей
        if existing_map and not self.has_changes:
            if any(p not in found_paths for p in existing_map):
                self.has_changes = True

        logger.info(f'✅ Обработано файлов: {files_processed}, всего фрагментов: {len(self.chunks)}')

    def create_embeddings(self, existing_index: Optional[Any] = None) -> None:
        """Создание векторов эмбеддингов для всех чанков.

        Args:
            existing_index (Optional[Any]): Существующий индекс FAISS для повторного использования векторов.

        Raises:
            ValueError: Если список чанков пуст.
            Exception: При ошибке кодирования (например, OOM).
        """
        # Проверка наличия чанков
        if not self.chunks:
            raise ValueError('Нет фрагментов для эмбеддинга — сначала запустите index_directory()')

        logger.info('Создание эмбеддингов…')

        dimension = self.model.get_sentence_embedding_dimension()
        final_embeddings = np.zeros((len(self.chunks), dimension), dtype='float32')

        to_encode_indices = []
        to_encode_texts = []
        reused_count = 0

        for i, chunk in enumerate(self.chunks):
            old_idx = chunk.get('_old_idx')
            reused = False

            # Проверка возможности повторного использования вектора
            if existing_index is not None and old_idx is not None and old_idx < existing_index.ntotal:
                # Проверка совпадения размерностей
                if existing_index.d == dimension:
                    try:
                        final_embeddings[i] = existing_index.reconstruct(old_idx)
                        reused_count += 1
                        reused = True
                    except Exception:
                        pass  # Возврат к полному кодированию

            # Проверка: если не удалось переиспользовать, добавляем в очередь на кодирование
            if not reused:
                to_encode_indices.append(i)
                to_encode_texts.append(chunk['text'])

        # Проверка необходимости кодирования новых фрагментов
        if to_encode_texts:
            logger.info(f"Кодирование {len(to_encode_texts)} новых/измененных фрагментов...")
            batch_size = 32
            try:
                for start_idx in range(0, len(to_encode_texts), batch_size):
                    end_idx = start_idx + batch_size
                    batch_texts = to_encode_texts[start_idx:end_idx]
                    batch_embeddings = self.model.encode(batch_texts, show_progress_bar=True)

                    for j, emb in enumerate(batch_embeddings):
                        final_embeddings[to_encode_indices[start_idx + j]] = emb
            except Exception as e:
                logger.error(f'❌ Ошибка при создании эмбеддингов: {e}')
                raise

        for chunk in self.chunks:
            chunk.pop('_old_idx', None)

        self.embeddings = final_embeddings
        logger.info(f'✅ Форма эмбеддингов: {self.embeddings.shape} (Переиспользовано: {reused_count})')

    def save_index(self, output_dir: Path) -> None:
        """Сборка индекса FAISS и сохранение всех артефактов.

        Args:
            output_dir (Path): Директория для сохранения.

        Raises:
            Exception: Если не удалось создать индекс.
            OSError: Если не удалось записать файлы на диск.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            faiss.normalize_L2(self.embeddings)
            dimension = self.embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            index.add(self.embeddings)
            logger.info(f'✅ Индекс FAISS: {index.ntotal} векторов')
        except Exception as e:
            # Ошибка возникает, если эмбеддинги отсутствуют или имеют неверный тип данных
            logger.error(f'❌ Не удалось собрать индекс FAISS: {e}')
            raise

        try:
            faiss.write_index(index, str(output_dir / 'faiss.index'))
            logger.info(f'✅ Сохранено: {output_dir / "faiss.index"}')
        except Exception as e:
            # Ошибка записи: диск переполнен или нет прав
            logger.error(f'❌ Ошибка при записи faiss.index: {e}')
            raise

        try:
            (output_dir / 'chunks.json').write_text(
                json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding='utf-8'
            )
            (output_dir / 'index_info.json').write_text(
                json.dumps({
                    'model':        self.model_name,
                    'chunks_count': len(self.chunks),
                    'dimension':    dimension,
                    'created_at':   datetime.now().isoformat(),
                    'version':      '1.0.0',
                }, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
            logger.info(f'✅ Метаданные сохранены в {output_dir}')
        except OSError as e:
            # Ошибка при записи служебных файлов
            logger.error(f'❌ Не удалось сохранить метаданные индекса: {e}')
            raise


def main() -> None:
    """Точка входа CLI для индексации документов."""
    parser = argparse.ArgumentParser(description='RAG Indexer for FastAPI Foundry')
    parser.add_argument('--docs-dir',   required=True,  help='Директория с документами')
    parser.add_argument('--output-dir', default='./rag_index', help='Директория для индекса')
    parser.add_argument('--model',      default='sentence-transformers/all-mpnet-base-v2')
    parser.add_argument('--chunk-size', type=int, default=1000, help='Размер чанка')
    parser.add_argument('--overlap',    type=int, default=50, help='Перекрытие чанков')
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    # Проверка существования исходной директории
    if not docs_dir.exists():
        logger.error(f'Директория не найдена: {docs_dir}')
        return

    indexer = RAGIndexer(model_name=args.model)
    indexer.load_model()
    indexer.index_directory(docs_dir, chunk_size=args.chunk_size, overlap=args.overlap)

    # Проверка наличия найденных документов
    if not indexer.chunks:
        logger.error('Документы не найдены — индексировать нечего')
        return

    indexer.create_embeddings()
    indexer.save_index(Path(args.output_dir))
    logger.info(f'Готово. Всего фрагментов: {len(indexer.chunks)}')


if __name__ == '__main__':
    main()
