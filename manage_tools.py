#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Универсальный CLI для управления инструментами проекта
# =============================================================================
# Описание:
#   Единая точка входа для всех служебных скриптов:
#   - Управление медиатекой (media)
#   - Синхронизация с qBittorrent (torrents)
#   - Обслуживание БД (db)
#   - Диагностика (check)
#   - Управление знаниями (knowledge)
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

# Загрузка переменных окружения
load_dotenv()


def run_media_command(args):
    """Команды управления медиатекой."""
    if args.subcommand == 'scan':
        from run_media_organizer import main as scan_main
        import asyncio
        # Передача аргументов через подмену sys.argv
        old_argv = sys.argv
        try:
            sys.argv = ['run_media_organizer.py'] + args.rest
            asyncio.run(scan_main())
        finally:
            sys.argv = old_argv
    elif args.subcommand == 'complete':
        # Заполнение пропущенных метаданных
        cmd = [sys.executable, 'complete_media_data.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0


def run_torrents_command(args):
    """Команды управления торрентами."""
    if args.subcommand == 'assign':
        from assign_categories_to_torrents import main as assign_main
        assign_main()
    elif args.subcommand == 'ids':
        # Использование assign_torrents_ids.py
        cmd = [sys.executable, 'assign_torrents_ids.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'state':
        cmd = [sys.executable, 'update_torrent_state.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'path':
        cmd = [sys.executable, 'update_torrents_path.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'clear':
        cmd = [sys.executable, 'clear_torrents_meta.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'orchestrator':
        cmd = [sys.executable, 'orchestrator_torrent.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0


def run_db_command(args):
    """Команды обслуживания базы данных."""
    if args.subcommand == 'update':
        cmd = [sys.executable, 'update_db.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'sizes':
        cmd = [sys.executable, 'update_media_sizes.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'fill':
        # Заполнение метаданных через fill_missing_metadata.py
        cmd = [sys.executable, 'fill_missing_metadata.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0


def run_check_command(args):
    """Команды диагностики."""
    if args.subcommand == 'db':
        cmd = [sys.executable, 'check_db.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'data':
        cmd = [sys.executable, 'check_db_data.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'media_type':
        cmd = [sys.executable, 'check_media_type.py']
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'series':
        cmd = [sys.executable, 'check_series.py']
        subprocess.run(cmd, check=True)
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0


def run_audit_command(args):
    """Команды аудита."""
    if args.subcommand == 'disk':
        # Использование audit_disk.py
        cmd = [sys.executable, 'audit_disk.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'media':
        cmd = [sys.executable, 'audit_media.py']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0


def run_knowledge_command(args):
    """Команды управления знаниями."""
    if args.subcommand == 'extract':
        cmd = [sys.executable, 'manage_knowledge.py', 'extract']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'add':
        cmd = [sys.executable, 'manage_knowledge.py', 'add']
        if args.rest:
            cmd.extend(args.rest)
        subprocess.run(cmd, check=True)
    elif args.subcommand == 'init':
        cmd = [sys.executable, 'manage_knowledge.py', 'init']
        subprocess.run(cmd, check=True)
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0


def run_rag_command(args):
    """Команды управления RAG-индексом медиатеки."""
    if args.subcommand == 'rebuild':
        from plugins.media_organizer.core.media_rag_functions import rebuild_rag_index
        print(rebuild_rag_index())
    elif args.subcommand == 'status':
        from plugins.media_organizer.core.media_rag_functions import get_rag_status
        print(get_rag_status())
    else:
        print(f"Неизвестная команда: {args.subcommand}")
        return 1
    return 0



def main():
    parser = argparse.ArgumentParser(
        prog='manage_tools.py',
        description='Универсальный CLI для управления инструментами проекта gemini-simplechat',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  py manage_tools.py media scan                           # полное сканирование
  py manage_tools.py media scan --disk "диск 2" --path "E:"
  py manage_tools.py media complete --title "The Bear"
  py manage_tools.py torrents assign                      # сопоставление категорий
  py manage_tools.py torrents ids                         # привязка торрентов
  py manage_tools.py db update                            # обновление БД
  py manage_tools.py db sizes E: L:                       # обновление размеров
  py manage_tools.py check db                             # диагностика БД
  py manage_tools.py audit disk "ДИСК 1"                  # аудит диска
  py manage_tools.py knowledge extract --file chat.md     # извлечение знаний
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # --- Media commands ---
    media_parser = subparsers.add_parser('media', help='Управление медиатекой')
    media_subparsers = media_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    media_scan_parser = media_subparsers.add_parser('scan', help='Сканирование медиатеки')
    media_scan_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для run_media_organizer.py')
    media_complete_parser = media_subparsers.add_parser('complete', help='Заполнение метаданных')
    media_complete_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для complete_media_data.py')

    # --- Torrents commands ---
    torrents_parser = subparsers.add_parser('torrents', help='Управление торрентами')
    torrents_subparsers = torrents_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    torrents_subparsers.add_parser('assign', help='Сопоставление категорий')
    torrents_ids_parser = torrents_subparsers.add_parser('ids', help='Привязка торрентов к медиа')
    torrents_ids_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для assign_torrents_ids.py')
    torrents_subparsers.add_parser('state', help='Перепроверка торрентов')
    torrents_subparsers.add_parser('path', help='Синхронизация путей')
    torrents_subparsers.add_parser('clear', help='Очистка мета-данных')
    torrents_orchestrator = torrents_subparsers.add_parser('orchestrator', help='Оркестратор торрентов')
    torrents_orchestrator.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для orchestrator_torrent.py')

    # --- DB commands ---
    db_parser = subparsers.add_parser('db', help='Обслуживание базы данных')
    db_subparsers = db_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    db_subparsers.add_parser('update', help='Обновление схемы БД')
    db_sizes_parser = db_subparsers.add_parser('sizes', help='Обновление размеров')
    db_sizes_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для update_media_sizes.py')
    db_subparsers.add_parser('fill', help='Заполнение пропущенных метаданных')

    # --- Check commands ---
    check_parser = subparsers.add_parser('check', help='Диагностика')
    check_subparsers = check_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    check_subparsers.add_parser('db', help='Диагностика БД')
    check_subparsers.add_parser('data', help='Проверка данных')
    check_subparsers.add_parser('media_type', help='Типы медиа')
    check_subparsers.add_parser('series', help='Сериалы')

    # --- Audit commands ---
    audit_parser = subparsers.add_parser('audit', help='Аудит')
    audit_subparsers = audit_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    audit_disk_parser = audit_subparsers.add_parser('disk', help='Аудит диска')
    audit_disk_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для audit_disk.py')
    audit_media_parser = audit_subparsers.add_parser('media', help='Аудит медиа')
    audit_media_parser.add_argument('rest', nargs=argparse.REMAINDER, help='Аргументы для audit_media.py')

    # --- Knowledge commands ---
    knowledge_parser = subparsers.add_parser('knowledge', help='Управление знаниями')
    knowledge_subparsers = knowledge_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    knowledge_subparsers.add_parser('extract', help='Извлечение знаний из чатов')
    knowledge_subparsers.add_parser('add', help='Добавить новую запись в знания')
    knowledge_subparsers.add_parser('init', help='Инициализация реестра знаний')

    # --- RAG commands ---
    rag_parser = subparsers.add_parser('rag', help='Управление RAG-индексом медиатеки')
    rag_subparsers = rag_parser.add_subparsers(dest='subcommand', help='Подкоманды')
    rag_subparsers.add_parser('rebuild', help='Полное перестроение RAG-индекса')
    rag_subparsers.add_parser('status', help='Проверить статус RAG-индекса')


    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Вызов соответствующей функции
    if args.command == 'media':
        return run_media_command(args)
    elif args.command == 'torrents':
        return run_torrents_command(args)
    elif args.command == 'db':
        return run_db_command(args)
    elif args.command == 'check':
        return run_check_command(args)
    elif args.command == 'audit':
        return run_audit_command(args)
    elif args.command == 'knowledge':
        return run_knowledge_command(args)
    elif args.command == 'rag':
        return run_rag_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
