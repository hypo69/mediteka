# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Управление и структурирование знаний из чатов (Knowledge Manager)
# =============================================================================
# Описание:
#   Скрипт для извлечения, учета и структурирования знаний из диалогов
#   с ИИ-ассистентами в реестр JSON и индекс Markdown.
#
# File: manage_knowledge.py
# Project: gemini-simplechat
# =============================================================================

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import header
from header import __root__
from src.logger.logger import logger
from src.ai import GoogleGenerativeAI
from src.secrets.api_key_state import load_api_keys
from src.utils.jjson import j_loads, j_dumps

REGISTRY_JSON = __root__ / '.ai_instructions' / 'knowledge' / 'codex_registry.json'
REGISTRY_MD = __root__ / '.ai_instructions' / 'knowledge' / 'codex' / 'registry.md'

load_dotenv(__root__ / '.env')


def init_registry() -> bool:
    """Инициализация файлов реестра, если они не существуют.

    Returns:
        bool: True при успешном выполнении, False при ошибке.
    """
    try:
        # Инициализация JSON-реестра
        if not REGISTRY_JSON.exists():
            REGISTRY_JSON.parent.mkdir(parents=True, exist_ok=True)
            j_dumps([], REGISTRY_JSON, ensure_ascii=False)
            print(f"✅ Создан файл JSON реестра: {REGISTRY_JSON}")
        else:
            print(f"ℹ Файл JSON реестра уже существует: {REGISTRY_JSON}")

        # Инициализация Markdown-файла
        if not REGISTRY_MD.exists():
            REGISTRY_MD.parent.mkdir(parents=True, exist_ok=True)
            write_markdown_index([])
            print(f"✅ Создан файл Markdown индекса: {REGISTRY_MD}")
        else:
            print(f"ℹ Файл Markdown индекса уже существует: {REGISTRY_MD}")

        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации реестра знаний: {e}")
        return False


def load_registry_data() -> list:
    """Загрузка данных реестра из JSON файла.

    Returns:
        list: Список записей из реестра.
    """
    if not REGISTRY_JSON.exists():
        return []
    try:
        data = j_loads(REGISTRY_JSON)
        if isinstance(data, list):
            # j_loads может вернуть OrderedDict, преобразуем к обычному list/dict если надо
            # но list OrderedDict вполне устраивает
            return list(data)
        return []
    except Exception as e:
        logger.error(f"Ошибка чтения реестра JSON: {e}")
        return []


def save_registry_data(data: list) -> bool:
    """Сохранение данных реестра в JSON файл.

    Args:
        data (list): Список записей для сохранения.

    Returns:
        bool: True при успехе, False при ошибке.
    """
    try:
        REGISTRY_JSON.parent.mkdir(parents=True, exist_ok=True)
        j_dumps(data, REGISTRY_JSON, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Ошибка записи в реестр JSON: {e}")
        return False


def write_markdown_index(data: list) -> bool:
    """Генерация файла registry.md на основе данных реестра.

    Args:
        data (list): Список записей реестра.

    Returns:
        bool: True при успехе, False при ошибке.
    """
    try:
        lines = [
            "# Реестр знаний проекта (Chat Knowledge Codex)\n",
            "Этот файл содержит упорядоченные знания, полученные в ходе диалогов с ИИ-ассистентами.\n",
            "Реестр автоматически генерируется и обновляется с помощью скрипта `manage_knowledge.py`.\n",
            "| Дата | Тема обсуждения | Краткие выводы / Принятые решения | Затронутые файлы |",
            "| :--- | :--- | :--- | :--- |"
        ]

        # Сортируем записи по дате в обратном порядке (новые сверху)
        sorted_data = sorted(data, key=lambda x: x.get('date', ''), reverse=True)

        for item in sorted_data:
            date = item.get('date', '')
            topic = item.get('topic', '')
            summary = item.get('summary', '')
            decisions = item.get('decisions', [])
            files = item.get('affected_files', [])

            # Форматируем решения
            decisions_str = "<br>".join([f"• {d}" for d in decisions])
            full_desc = f"**{summary}**"
            if decisions_str:
                full_desc += f"<br>{decisions_str}"

            # Форматируем ссылки на файлы
            formatted_files = []
            for filepath in files:
                rel_path = filepath
                if filepath.startswith('.ai_instructions/knowledge/codex/'):
                    rel_path = filepath.replace('.ai_instructions/knowledge/codex/', '')
                elif filepath.startswith('.ai_instructions/knowledge/'):
                    rel_path = filepath.replace('.ai_instructions/knowledge/', '../')
                elif filepath.startswith('.ai_instructions/rules/'):
                    rel_path = filepath.replace('.ai_instructions/rules/', '../rules/')
                elif filepath.startswith('.ai_instructions/'):
                    rel_path = filepath.replace('.ai_instructions/', '../../')
                else:
                    rel_path = "../../../" + filepath

                rel_path = rel_path.replace('\\', '/')
                formatted_files.append(f"[{filepath}](file:///{__root__.as_posix()}/{filepath})")

            files_str = ", ".join(formatted_files)

            # Заменяем перенос строки в markdown таблицах
            topic_clean = topic.replace('|', '\\|')
            full_desc_clean = full_desc.replace('|', '\\|').replace('\n', ' ')

            lines.append(f"| {date} | {topic_clean} | {full_desc_clean} | {files_str} |")

        REGISTRY_MD.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_MD, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        return True
    except Exception as e:
        logger.error(f"Ошибка генерации Markdown индекса: {e}")
        return False


def add_entry(chat_id: str, date: str, topic: str, summary: str, decisions: list, files: list) -> bool:
    """Добавление новой записи в реестр вручную.

    Returns:
        bool: True при успехе, False при ошибке.
    """
    data = load_registry_data()

    # Проверка дубликатов по chat_id
    if len(chat_id) > 0:
        for item in data:
            if item.get('chat_id') == chat_id:
                print(f"ℹ Запись для чата {chat_id} уже присутствует в реестре. Обновление...")
                item['date'] = date
                item['topic'] = topic
                item['summary'] = summary
                item['decisions'] = decisions
                item['affected_files'] = files
                save_registry_data(data)
                write_markdown_index(data)
                return True

    new_item = {
        "chat_id": chat_id,
        "date": date,
        "topic": topic,
        "summary": summary,
        "decisions": decisions,
        "affected_files": files
    }
    data.append(new_item)
    save_registry_data(data)
    write_markdown_index(data)
    print("✅ Новая запись успешно добавлена в реестр и обновлен Markdown-индекс.")
    return True


async def extract_knowledge_from_file(filepath: str) -> bool:
    """Автоматическое извлечение знаний из файла архива чата с помощью Gemini.

    Args:
        filepath (str): Путь к markdown-файлу архива чата.

    Returns:
        bool: True при успехе, False при ошибке.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"❌ Файл архива не найден: {filepath}")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            chat_text = f.read()
    except Exception as e:
        logger.error(f"Не удалось прочитать файл {filepath}: {e}")
        return False

    # Загружаем ключи
    _, key_names, _ = load_api_keys()
    if not key_names:
        print("❌ Ошибка: Отсутствуют активные API ключи Gemini в .env.")
        return False

    print("🤖 Подключение к Gemini для анализа диалога...")
    system_instruction = (
        "Ты — технический аналитик проекта. Твоя задача — проанализировать архив чата "
        "разработчика с ИИ и выдать структурированный JSON-отчет с ключевыми знаниями."
    )
    
    try:
        ai = GoogleGenerativeAI(api_key_names=[key_names[0]], system_instruction=system_instruction)
    except Exception as e:
        logger.error(f"Не удалось инициализировать модель: {e}")
        return False

    prompt = (
        "Проанализируй предоставленный архив чата разработчика с ИИ-ассистентом и "
        "извлеки из него ключевые полученные знания, архитектурные решения и изменения.\n\n"
        "Выдай результат СТРОГО в формате JSON с кодировкой UTF-8 со следующей структурой:\n"
        "{\n"
        "  \"chat_id\": \"идентификатор чата (найди UUID в тексте или оставь пустым)\",\n"
        "  \"date\": \"дата обсуждения в формате YYYY-MM-DD (найди в тексте или укажи текущую)\",\n"
        "  \"topic\": \"тема обсуждения (до 10 слов)\",\n"
        "  \"summary\": \"краткое описание решенной проблемы или задачи (1-2 предложения)\",\n"
        "  \"decisions\": [\"принятое решение 1\", \"принятое решение 2\"],\n"
        "  \"affected_files\": [\"путь/к/файлу1\", \"путь/к/файлу2\"]\n"
        "}\n\n"
        "В поле affected_files указывай относительные пути файлов от корня проекта (например, "
        "'.ai_instructions/knowledge/scripts_tools.md' или 'main.py').\n"
        "Возвращай ТОЛЬКО валидный JSON-объект. Не оборачивай его в markdown блоки (например, ```json).\n\n"
        "Текст чата для анализа:\n"
        f"{chat_text}"
    )

    response = await ai.ask(prompt)
    if not response:
        print("❌ Модель вернула пустой ответ.")
        return False

    # Очищаем ответ от разметки markdown, если она все же вернулась
    cleaned_response = response.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()

    try:
        # Используем j_loads для парсинга ответа модели
        result = j_loads(cleaned_response)
    except Exception as e:
        logger.error(f"Не удалось распарсить JSON модели: {e}. Ответ модели:\n{response}")
        return False

    chat_id = result.get("chat_id", "")
    # Если chat_id пустой, попробуем извлечь его из названия файла
    if len(chat_id) == 0:
        filename = path.stem
        # Поиск UUID в имени файла
        import re
        uuid_match = re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", filename)
        if uuid_match:
            chat_id = uuid_match.group(0)
        else:
            chat_id = filename

    date = result.get("date", datetime.today().strftime('%Y-%m-%d'))
    topic = result.get("topic", "Автоматически извлеченная тема")
    summary = result.get("summary", "Нет описания")
    decisions = result.get("decisions", [])
    files = result.get("affected_files", [])

    add_entry(chat_id, date, topic, summary, decisions, files)
    return True


def main() -> int:
    """Основная функция парсинга аргументов командной строки.

    Returns:
        int: Код завершения.
    """
    parser = argparse.ArgumentParser(
        prog='manage_knowledge.py',
        description='Инструмент ведения и структурирования базы знаний проекта на основе диалогов.'
    )
    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # Команда init
    subparsers.add_parser('init', help='Инициализировать реестр и markdown-файл индекса.')

    # Команда add
    add_parser = subparsers.add_parser('add', help='Вручную добавить запись в реестр знаний.')
    add_parser.add_argument('--chat-id', type=str, default='', help='ID чата.')
    add_parser.add_argument('--date', type=str, default='', help='Дата (YYYY-MM-DD).')
    add_parser.add_argument('--topic', type=str, required=True, help='Тема обсуждения.')
    add_parser.add_argument('--summary', type=str, required=True, help='Краткое описание.')
    add_parser.add_argument('--decision', type=str, action='append', default=[], help='Принятое решение (можно указывать несколько раз).')
    add_parser.add_argument('--file', type=str, action='append', default=[], help='Затронутый файл (можно указывать несколько раз).')

    # Команда extract
    ext_parser = subparsers.add_parser('extract', help='Автоматически извлечь знания из файла архива чата.')
    ext_parser.add_argument('--file', type=str, required=True, help='Путь к markdown файлу архива чата.')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == 'init':
        success = init_registry()
        if success:
            return 0
        return 1

    elif args.command == 'add':
        date_str = args.date
        if len(date_str) == 0:
            date_str = datetime.today().strftime('%Y-%m-%d')
        success = add_entry(args.chat_id, date_str, args.topic, args.summary, args.decision, args.file)
        if success:
            return 0
        return 1

    elif args.command == 'extract':
        success = asyncio.run(extract_knowledge_from_file(args.file))
        if success:
            return 0
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
