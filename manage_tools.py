#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Универсальный CLI для управления инструментами проекта
# =============================================================================
# Описание:
#   Единая точка входа для всех служебных скриптов и плагинов:
#   - Управление медиатекой (media) -> plugins.media_organizer.tools
#   - Синхронизация с qBittorrent (torrents) -> plugins.qbittorrent.tools
#   - Обслуживание БД (db) -> plugins.media_organizer.tools
#   - Диагностика (check) -> plugins.media_organizer.tools
#   - Аудит целостности (audit) -> plugins.media_organizer.tools
#   - Управление знаниями и RAG (knowledge, rag) -> plugins.rag.tools
#   - Документация и разработка (docs, dev) -> scripts.dev
#
# File: manage_tools.py
# Project: gemini-simplechat
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

import header
from header import __root__

# Fix Windows console utf-8 output encoding
if sys.platform.startswith('win') and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Загрузка переменных окружения
load_dotenv(__root__ / '.env')


def _run_script(script_rel_path: str, extra_args: list[str] = []) -> int:
    """Запускает Python-скрипт по относительному пути от корня проекта.

    Args:
        script_rel_path (str): Относительный путь к скрипту от корня проекта.
        extra_args (list[str]): Дополнительные аргументы командной строки.

    Returns:
        int: Код возврата процесса (0 - успех, >0 - ошибка).
    """
    target_path = __root__ / script_rel_path
    if not target_path.exists():
        print(f"❌ Ошибка: скрипт не найден: {target_path}")
        return 1

    cmd = [sys.executable, str(target_path)]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, cwd=str(__root__))
    return result.returncode


def run_media_command(args: argparse.Namespace) -> int:
    """Команды управления медиатекой (делегирование в plugins.media_organizer)."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'scan':
        return _run_script('plugins/media_organizer/tools/run_media_organizer.py', extra)
    if sub == 'dry_run':
        return _run_script('plugins/media_organizer/tools/run_dry_run.py', extra)
    if sub == 'complete':
        return _run_script('plugins/media_organizer/tools/fill_missing_metadata.py', extra)
    if sub == 'enrich':
        return _run_script('plugins/media_organizer/tools/enrich_incomplete_records.py', extra)
    if sub == 'card':
        return _run_script('plugins/media_organizer/tools/get_media_card.py', extra)

    print(f"Неизвестная подкоманда media: {sub}")
    return 1


def run_torrents_command(args: argparse.Namespace) -> int:
    """Команды управления торрентами (делегирование в plugins.qbittorrent)."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'assign':
        return _run_script('plugins/qbittorrent/tools/assign_categories_to_torrents.py', extra)
    if sub == 'ids':
        return _run_script('plugins/qbittorrent/tools/assign_torrents_ids.py', extra)
    if sub == 'state':
        return _run_script('plugins/qbittorrent/tools/update_torrent_state.py', extra)
    if sub == 'path':
        return _run_script('plugins/qbittorrent/tools/update_torrents_path.py', extra)
    if sub == 'clear':
        return _run_script('plugins/qbittorrent/tools/clear_torrents_meta.py', extra)
    if sub == 'orchestrator':
        return _run_script('plugins/qbittorrent/tools/orchestrator_torrent.py', extra)

    print(f"Неизвестная подкоманда torrents: {sub}")
    return 1


def run_db_command(args: argparse.Namespace) -> int:
    """Команды обслуживания базы данных медиатеки."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'update':
        return _run_script('plugins/media_organizer/tools/update_db.py', extra)
    if sub == 'sizes':
        return _run_script('plugins/media_organizer/tools/update_media_sizes.py', extra)
    if sub == 'fill':
        return _run_script('plugins/media_organizer/tools/fill_missing_metadata.py', extra)
    if sub == 'migration':
        return _run_script('plugins/media_organizer/tools/perform_migration_safe.py', extra)

    print(f"Неизвестная подкоманда db: {sub}")
    return 1


def run_check_command(args: argparse.Namespace) -> int:
    """Команды базовой диагностики."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'db':
        return _run_script('plugins/media_organizer/tools/check_db.py', extra)
    if sub == 'data':
        return _run_script('plugins/media_organizer/tools/check_db_data.py', extra)
    if sub == 'paths':
        return _run_script('plugins/media_organizer/tools/check_db_paths.py', extra)
    if sub == 'count':
        return _run_script('plugins/media_organizer/tools/count_media_by_category.py', extra)

    print(f"Неизвестная подкоманда check: {sub}")
    return 1


def run_audit_command(args: argparse.Namespace) -> int:
    """Команды аудита целостности дисков и медиафайлов."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'disk':
        return _run_script('plugins/media_organizer/tools/audit_disk.py', extra)
    if sub == 'media':
        return _run_script('plugins/media_organizer/tools/audit_media.py', extra)
    if sub == 'report':
        return _run_script('plugins/media_organizer/tools/generate_audit_report.py', extra)

    print(f"Неизвестная подкоманда audit: {sub}")
    return 1


def run_knowledge_command(args: argparse.Namespace) -> int:
    """Команды управления базой знаний проекта."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub in ('extract', 'add', 'init'):
        cmd_args = [sub] + extra
        return _run_script('plugins/rag/tools/manage_knowledge.py', cmd_args)

    print(f"Неизвестная подкоманда knowledge: {sub}")
    return 1


def run_rag_command(args: argparse.Namespace) -> int:
    """Команды управления RAG-индексами."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'rebuild':
        return _run_script('plugins/rag/tools/rebuild_chat_rag.py', extra)
    if sub == 'reindex':
        return _run_script('plugins/rag/tools/reindex_rag.py', extra)
    if sub == 'validate':
        return _run_script('plugins/rag/tools/validate_rag_files.py', extra)
    if sub == 'status':
        try:
            from plugins.media_organizer.core.media_rag_functions import get_rag_status
            print(get_rag_status())
            return 0
        except Exception as e:
            print(f"Ошибка проверки RAG статуса: {e}")
            return 1

    print(f"Неизвестная подкоманда rag: {sub}")
    return 1


def run_docs_command(args: argparse.Namespace) -> int:
    """Команды управления документацией."""
    sub = args.subcommand
    extra = getattr(args, 'rest', [])

    if sub == 'update':
        return _run_script('scripts/dev/update_docs.py', extra)

    print(f"Неизвестная подкоманда docs: {sub}")
    return 1


def main() -> int:
    """Главная точка входа универсального CLI."""
    parser = argparse.ArgumentParser(
        prog='manage_tools.py',
        description='Универсальный CLI для управления инструментами проекта gemini-simplechat',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  py manage_tools.py media scan                           # полное сканирование медиатеки
  py manage_tools.py media complete --title "The Bear"    # заполнение метаданных
  py manage_tools.py torrents assign                      # сопоставление категорий торрентов
  py manage_tools.py torrents ids                         # привязка торрентов к медиа
  py manage_tools.py db update                            # обновление БД
  py manage_tools.py db sizes E: L:                       # обновление размеров
  py manage_tools.py check db                             # диагностика БД
  py manage_tools.py audit disk "ДИСК 1"                  # аудит диска
  py manage_tools.py rag rebuild                          # перестроение RAG-индекса
  py manage_tools.py knowledge extract --file chat.md     # извлечение знаний
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # --- Media commands ---
    media_parser = subparsers.add_parser('media', help='Управление медиатекой')
    media_subparsers = media_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    media_scan_parser = media_subparsers.add_parser('scan', help='Сканирование медиатеки')
    media_scan_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для run_media_organizer.py')
    media_subparsers.add_parser('dry_run', help='Тестовый прогон сканирования')
    media_complete_parser = media_subparsers.add_parser('complete', help='Заполнение метаданных')
    media_complete_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    media_enrich_parser = media_subparsers.add_parser('enrich', help='Обогащение неполных записей')
    media_enrich_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    media_card_parser = media_subparsers.add_parser('card', help='Генерация карточки медиа')
    media_card_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')

    # --- Torrents commands ---
    torrents_parser = subparsers.add_parser('torrents', help='Управление торрентами')
    torrents_subparsers = torrents_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    torrents_subparsers.add_parser('assign', help='Сопоставление категорий')
    torrents_ids_parser = torrents_subparsers.add_parser('ids', help='Привязка торрентов к медиа')
    torrents_ids_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    torrents_subparsers.add_parser('state', help='Перепроверка торрентов')
    torrents_subparsers.add_parser('path', help='Синхронизация путей')
    torrents_subparsers.add_parser('clear', help='Очистка метаданных')
    torrents_orchestrator = torrents_subparsers.add_parser('orchestrator', help='Оркестратор торрентов')
    torrents_orchestrator.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')

    # --- DB commands ---
    db_parser = subparsers.add_parser('db', help='Обслуживание базы данных')
    db_subparsers = db_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    db_subparsers.add_parser('update', help='Обновление схемы БД')
    db_sizes_parser = db_subparsers.add_parser('sizes', help='Обновление размеров')
    db_sizes_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    db_subparsers.add_parser('fill', help='Заполнение пропущенных метаданных')
    db_subparsers.add_parser('migration', help='Безопасная миграция базы данных')

    # --- Check commands ---
    check_parser = subparsers.add_parser('check', help='Диагностика')
    check_subparsers = check_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    check_subparsers.add_parser('db', help='Диагностика БД')
    check_subparsers.add_parser('data', help='Проверка данных')
    check_subparsers.add_parser('paths', help='Проверка путей')
    check_subparsers.add_parser('count', help='Подсчет медиа по категориям')

    # --- Audit commands ---
    audit_parser = subparsers.add_parser('audit', help='Аудит')
    audit_subparsers = audit_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    audit_disk_parser = audit_subparsers.add_parser('disk', help='Аудит диска')
    audit_disk_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    audit_media_parser = audit_subparsers.add_parser('media', help='Аудит медиа')
    audit_media_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    audit_subparsers.add_parser('report', help='Генерация сводного отчета аудита')

    # --- Knowledge commands ---
    knowledge_parser = subparsers.add_parser('knowledge', help='Управление знаниями')
    knowledge_subparsers = knowledge_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    knowledge_extract = knowledge_subparsers.add_parser('extract', help='Извлечение знаний из чатов')
    knowledge_extract.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    knowledge_add = knowledge_subparsers.add_parser('add', help='Добавить новую запись в знания')
    knowledge_add.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы')
    knowledge_subparsers.add_parser('init', help='Инициализация реестра знаний')

    # --- RAG commands ---
    rag_parser = subparsers.add_parser('rag', help='Управление RAG-индексами')
    rag_subparsers = rag_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    rag_subparsers.add_parser('rebuild', help='Полное перестроение RAG-индекса')
    rag_subparsers.add_parser('reindex', help='Переиндексация базы знаний')
    rag_subparsers.add_parser('validate', help='Валидация файлов базы знаний')
    rag_subparsers.add_parser('status', help='Проверить статус RAG-индекса')

    # --- Docs commands ---
    docs_parser = subparsers.add_parser('docs', help='Управление документацией')
    docs_subparsers = docs_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    docs_subparsers.add_parser('update', help='Проверить и актуализировать документацию')

    args = parser.parse_args()

    if not args.command or not getattr(args, 'subcommand', ''):
        parser.print_help()
        return 0

    dispatch = {
        'media': run_media_command,
        'torrents': run_torrents_command,
        'db': run_db_command,
        'check': run_check_command,
        'audit': run_audit_command,
        'knowledge': run_knowledge_command,
        'rag': run_rag_command,
        'docs': run_docs_command,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == '__main__':
    sys.exit(main())
