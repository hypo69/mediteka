# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Плагин Media Organizer для организации медиатеки
# =============================================================================
# Описание:
#   Плагин MediaOrganizerPlugin для интеграции с интеллектуальным помощником.
#   Использует модули: media_scanner, media_auditor, genre_classifier,
#   report_generator, media_rebuild.
#
# File: media_organizer.py
# Project: gemini-simplechat
# Package: plugins.media_organizer.core
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import re
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from plugins.plugin import BasePlugin
from src.logger import logger

from plugins.media_organizer.core import (
    DEFAULT_CATEGORIES, MEDIA_DB, REPORTS_DIR, OUTPUT_DIR, MEDIA_PATHS_FILE,
    INSTRUCTION_FILE, TORRENTS_FILE, PATHS_FILE, DB_FILE, CONFIG_DIR,
    SYSTEM_INSTRUCTION
)
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_tools import MEDIA_TOOLS, dispatch_tool_call
from plugins.media_organizer.core.media_scanner import TMDBClient, MediaScanner
from plugins.media_organizer.core.media_auditor import MediaAuditor
from plugins.media_organizer.core.genre_classifier import PersistentGenreClassifier
from plugins.media_organizer.core.report_generator import export_disk_json, export_disk_md, ReportGenerator
from plugins.media_organizer.core.media_rebuild import rebuild_db
from plugins.media_organizer.core.media_tracker import (
    load_media_paths, _filter_paths_by_disk, _normalize_disk_name
)

INSTRUCTION = SYSTEM_INSTRUCTION

TRIGGERS = ("фильм", "сериал", "кино", "movie", "film", "series", "медиа", "media",
            "скан", "scan", "отчет", "report", "библиотек", "медиатек", "ревизи", "audit",
            "rebuild", "восстанов", "rebuild_db", "rebuild_rag",
            "карточк", "расскаж", "покаж", "что за", "info", "card", "классифицировать")


# =============================================================================
# PLUGIN
# =============================================================================

class MediaOrganizerPlugin(BasePlugin):
    """Плагин для сканирования и классификации медиатеки через TMDB и Gemini.

    Attributes:
        name (str): Имя плагина.
        media_paths (List[Path]): Список путей к медиа.
        report_format (str): Формат отчёта (не используется в текущей версии).
    """

    name = "media_organizer"

    def __init__(self, ai_model) -> None:
        """Инициализация плагина.

        Args:
            ai_model: Экземпляр модели искусственного интеллекта.
        """
        super().__init__(ai_model)
        self.media_paths = load_media_paths()
        self.report_format = 'html'

    async def handle(self, message: str, disk_paths: Optional[List[Path]] = None, fulldata: bool = True) -> Optional[str]:
        """Обработка входящего сообщения с поддержкой явных путей.

        Args:
            message (str): Входящее текстовое сообщение.
            disk_paths (Optional[List[Path]]): Явные пути для сканирования. Если None, используются self.media_paths.
            fulldata (bool): Выполнять глубокое сканирование и сбор данных о сезонах/эпизодах.

        Returns:
            Optional[str]: Ответ плагина или пустая строка если плагин неприменим.
        """
        try:
            return await self._handle(message, disk_paths=disk_paths, fulldata=fulldata) or ''
        except Exception as ex:
            logger.error(f'[{self.name}] Ошибка обработки сообщения', ex)
            return ''

    async def _handle(self, message: str, disk_paths: Optional[List[Path]] = None, fulldata: bool = True) -> Optional[str]:
        """Обработка сообщения пользователя.
        
        Args:
            message (str): Сообщение от пользователя.
            disk_paths (Optional[List[Path]]): Явные пути для сканирования. Если None, используются self.media_paths.
            fulldata (bool): Выполнять глубокое сканирование и сбор данных о сезонах/эпизодах.
        """
        print(f"DEBUG: _handle received message: '{message}', fulldata={fulldata}")
        if not any(t in message.lower() for t in TRIGGERS):
            print(f"DEBUG: Triggers not matched in message.")
            return None

        # Режим генерации отчёта из БД без сканирования
        if any(t in message.lower() for t in ('отчет', 'report')):
            match = re.search(r'(?:диск|disk)\s*(\w+)', message, re.IGNORECASE)
            if not match:
                return "❌ Укажите имя диска (например: 'отчет диск 1')"
            disk_name = _normalize_disk_name(match.group(0))
            db = MediaDatabase(MEDIA_DB)
            export_disk_json(db, disk_name, OUTPUT_DIR)
            report_file = export_disk_md(db, disk_name, OUTPUT_DIR)
            return f"✅ Отчёт сформирован: {report_file}"

        # Режим rebuild_rag — перестройка RAG-индекса
        if 'rebuild_rag' in message.lower():
            from plugins.media_organizer.core.media_rag import build_media_rag
            api_key = os.getenv('GEMINI_API_KEY', '')
            if not api_key:
                return '❌ GEMINI_API_KEY не найден в .env'
            rag = build_media_rag(api_key)
            return f'✅ RAG-индекс построен: {rag.count()} документов'

        # Режим rebuild_db — консолидация дублей в БД
        if 'rebuild_db' in message.lower():
            return rebuild_db(MediaDatabase(MEDIA_DB))

        # Режим rebuild — восстановление БД из JSON
        if any(t in message.lower() for t in ('rebuild', 'восстанов')):
            return "⚠️  Режим --rebuild удалён. Используйте полное сканирование."

        # Режим ревизии
        if any(t in message.lower() for t in ('ревизи', 'audit')):
            db = MediaDatabase(MEDIA_DB)
            auditor = MediaAuditor(db, gemini=self.ai)
            issues = await auditor.audit()
            if not issues:
                return "✅ Ревизия завершена: несовпадений не найдено."
            
            lines = [f"⚠️ Найдено несовпадений: {len(issues)}. Начинаю автоматическое дополнение..."]
            
            # Инициализируем классификатор для дозаполнения
            classifier = PersistentGenreClassifier(TMDBClient(os.getenv('TMDB_API_KEY', '')), self.ai, db, "UNKNOWN")
            
            for iss in issues:
                try:
                    lines.append(f"  🔄 Обработка: {iss.get('title', 'Unknown')}")
                    # Попытка дозаполнить данные
                    # Вызов метода классификации для конкретного пути или тайтла
                    if 'path' in iss:
                        await classifier._map_category(
                            iss['title'], 
                            [Path(iss['path'])], 
                            'series' if 'S0' in iss['title'] or iss['type'] in ['missing_season', 'episodes'] else 'movie', 
                            iss['title'], 
                            True
                        )
                    lines.append(f"    ✅ Успешно дополнено.")
                except Exception as e:
                    lines.append(f"    ❌ Ошибка дополнения: {e}")
                    await asyncio.sleep(7) # Пауза при ошибке

            return "\n".join(lines)

        # Поиск по БД для запросов о конкретном медиа (нет названия/номера диска)
        if not re.search(r'(?:диск|disk)\s*\w+', message, re.IGNORECASE):
            return await self.ai.ask_with_tools(message, [MEDIA_TOOLS], dispatch_tool_call)

        # Check for disk_name in message (e.g., "диск 4")
        match = re.search(r'(?:диск|disk)\s*(\w+)', message, re.IGNORECASE)
        if not match:
            return "❌ Укажите имя диска (например: 'диск 4')"
        disk_name = _normalize_disk_name(match.group(0))

        tmdb_key = os.getenv('TMDB_API_KEY', '')
        if not tmdb_key:
            return "❌ Не найден TMDB_API_KEY в .env"

        if not self.media_paths:
            return f"⚠️ Не заданы пути для сканирования. Добавьте пути в {MEDIA_PATHS_FILE}"

        # Фильтруем пути по disk_name
        paths_to_use = disk_paths if disk_paths else self.media_paths
        if not paths_to_use:
            return f"⚠️ Не заданы пути для сканирования. Добавьте пути в {MEDIA_PATHS_FILE}"

        disk_paths_filtered = _filter_paths_by_disk(paths_to_use, disk_name)
        if not disk_paths_filtered:
            return f"⚠️ Не найден путь для {disk_name}. Проверьте {MEDIA_PATHS_FILE}"

        original_instruction = self.ai.system_instruction
        self.ai.system_instruction = INSTRUCTION
        try:
            # STAGE 1: Setup and Initialization
            tmdb = TMDBClient(tmdb_key)
            db = MediaDatabase(MEDIA_DB)
            scanner = MediaScanner()

            # STAGE 2: Сканирование путей (Этап 1 - базовое)
            print(f"\n этап 1/3: Сканирование {disk_name}...")
            scanner.scan_paths(disk_paths_filtered)
            print(f"   Найдено: фильмов — {len(scanner.movies)}, сериалов — {len(scanner.series)}")

            # STAGE 3: Сохранение базовой информации в БД
            print("\n этап 2/4: Сохранение в БД...")
            classifier = PersistentGenreClassifier(tmdb, self.ai, db, disk_name)
            _, classified_series = await classifier.classify_media(scanner.movies, scanner.series)
            print(f"   Записей сохранено: {len(db.export_disk(disk_name))}")

            # STAGE 4: Поиск дубликатов (Этап 2)
            print("\n этап 3/4: Поиск дубликатов...")
            dup_count = db.update_duplicates()
            if dup_count > 0:
                print(f"   Найдено {dup_count} уникальных дубликатов между дисками")

            # STAGE 5: Глубокое сканирование (Этап 3)
            if fulldata:
                print("\n этап 4/4: Глубокое сканирование сериалов...")
                scanner.deep_scan_series()
                # Сохраняем информацию о сезонах и эпизодах в таблицу media
                saved_seasons = 0
                saved_episodes = 0
                print(f"DEBUG: scanner.series = {list(scanner.series.keys())}")
                for series_title, series_data in scanner.series.items():
                    series_record = db.find_any_disk(series_title)
                    if not series_record:
                        print(f"   ⚠️  Сериал '{series_title}' не найден в БД, пропускаем сохранение сезонов/эпизодов")
                        # Получаем список всех сериалов из базы для диагностики
                        all_series = [r for r in db.export_disk(disk_name) if r.get('num_of_seasons', 0) > 0]
                        print(f"   DEBUG: Сериалов в БД: {[(r.get('title'), r.get('path')) for r in all_series]}")
                        continue
                    series_id = series_record.get('id', 0)

                    # Извлекаем episodes_detail в памяти из результатов классификатора
                    # series_title - это ключ в scanner.series
                    classified_item = classified_series.get(series_title, {}) or {}
                    episodes_detail = classified_item.get('episodes_detail', []) or []

                    # Попробуем распарсить seasons (описания сезонов) из записи сериала
                    # seasons_detail может быть сохранен в БД
                    seasons = series_data.get('seasons', {})
                    for season_num, season_data in seasons.items():
                        # Ищем описание сезона в episodes_detail или в seasons родителя
                        season_plot = ""
                        season_verdict = ""
                        if isinstance(episodes_detail, list):
                            for s_det in episodes_detail:
                                if s_det.get('season_number') == season_num:
                                    # Если в s_det есть общее описание
                                    season_plot = s_det.get('summary') or s_det.get('description') or ""
                                    season_verdict = s_det.get('final_verdict') or ""
                                    break

                        # Сохраняем сезон
                        season_path = season_data.get('path', '')
                        season_record = {
                            'path': season_path,
                            'title': f"{series_title} (сезон {season_num})",
                            'type': 'season',
                            'parent_id': series_id,
                            'year': series_record.get('year', 0),
                            'country': series_record.get('country', ''),
                            'main_category': series_record.get('main_category', ''),
                            'genres': series_record.get('genres', []),
                            'directors': series_record.get('directors', []),
                            'cast': series_record.get('cast', []),
                            'plot': season_plot,
                            'final_verdict': season_verdict,
                            'rating': series_record.get('rating', {}),
                        }
                        db.save_media(disk_name, 'season', season_record)
                        saved_seasons += 1
                        season_id = db.get_media(disk_name, season_record['title']).get('id', 0)

                        # Сохраняем эпизоды
                        for ep in season_data.get('episodes', []):
                            ep_num = ep.get('episode', 0)
                            ep_plot = ""
                            ep_verdict = ""
                            # Ищем описание конкретного эпизода в episodes_detail
                            if isinstance(episodes_detail, list):
                                for s_det in episodes_detail:
                                    if s_det.get('season_number') == season_num:
                                        # В зависимости от уровня детализации (episode или arc)
                                        eps_list = s_det.get('episodes', [])
                                        if isinstance(eps_list, list):
                                            for ep_det in eps_list:
                                                if ep_det.get('episode_number') == ep_num:
                                                    begins = ep_det.get('begins', '')
                                                    ends = ep_det.get('ends', '')
                                                    ep_plot = f"{begins} {ends}".strip()
                                                    ep_verdict = ep_det.get('final_verdict') or ""
                                                    break
                                        break

                            ep_record = {
                                'path': ep.get('path') or ep.get('filepath', ''),
                                'filename': ep.get('filename', ''),
                                'title': f"{series_title} S{season_num:02d}E{ep_num:02d} {ep.get('filename', '')}",
                                'type': 'episode',
                                'parent_id': season_id,
                                'size_mb': round(ep.get('size', 0) / 1024 / 1024, 2),
                                'year': series_record.get('year', 0),
                                'country': series_record.get('country', ''),
                                'main_category': series_record.get('main_category', ''),
                                'genres': series_record.get('genres', []),
                                'directors': series_record.get('directors', []),
                                'cast': series_record.get('cast', []),
                                'plot': ep_plot,
                                'final_verdict': ep_verdict,
                                'rating': series_record.get('rating', {}),
                            }
                            db.save_media(disk_name, 'episode', ep_record)
                            saved_episodes += 1
                print(f"   Сохранено сезонов: {saved_seasons}, эпизодов: {saved_episodes}")
            else:
                print("\n Глубокое сканирование сериалов пропущено (--fulldata=n)")

            # STAGE 6: Report from DB
            print("\nФормирование отчетов пропущено.")
            # export_disk_json(db, disk_name, OUTPUT_DIR)
            # report_file = export_disk_md(db, disk_name, OUTPUT_DIR)

            # STAGE 11: Duplicates Report
            # ...
            # print(f"\n⚠️  Найдено {len(duplicates)} дубликатов. Отчёт: {dup_file}")

            # STAGE 12: Open report
            # try:
            #     webbrowser.open(report_file.as_uri())
            #     print(f"🌐 Файл открыт в браузере: {report_file}")
            # except Exception as e:
            #     print(f"⚠️ Не удалось открыть файл в браузере: {e}")

            # Получаем список эпизодов
            episodes_list = [r for r in db.export_disk(disk_name) if r.get('parent_id') is not None]

            result_msg = (
                f"✅ Сканирование завершено!\n"
                f"   Этап 1: Фильмов — {len(scanner.movies)}, Сериалов — {len(scanner.series)}\n"
                f"   Этап 2: Дубликатов — {dup_count}\n"
                f"   Этап 3: Эпизодов — {len(episodes_list)}\n"
            )
            return result_msg
        finally:
            self.ai.system_instruction = original_instruction
