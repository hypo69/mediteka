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
    DEFAULT_CATEGORIES, MEDIA_DB, REPORTS_DIR, OUTPUT_DIR,
    TORRENTS_FILE, DB_FILE, CONFIG_DIR,
    SYSTEM_INSTRUCTION_RESEARCH, SYSTEM_INSTRUCTION_CHAT, SYSTEM_INSTRUCTION_TTS
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

INSTRUCTION = SYSTEM_INSTRUCTION_RESEARCH

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

    def _handle_report(self, message: str) -> str:
        """Формирует отчет по диску из БД."""
        match = re.search(r'(?:диск|disk)\s*(\w+)', message, re.IGNORECASE)
        if not match:
            return "❌ Укажите имя диска (например: 'отчет диск 1')"
        disk_name = _normalize_disk_name(match.group(0))
        db = MediaDatabase(MEDIA_DB)
        export_disk_json(db, disk_name, OUTPUT_DIR)
        report_file = export_disk_md(db, disk_name, OUTPUT_DIR)
        return f"✅ Отчёт сформирован: {report_file}"

    async def _handle_audit(self) -> str:
        """Выполняет ревизию несовпадений и автодополнение метаданных."""
        db = MediaDatabase(MEDIA_DB)
        auditor = MediaAuditor(db, gemini=self.ai)
        issues = await auditor.audit()
        if not issues:
            return "✅ Ревизия завершена: несовпадений не найдено."

        lines = [f"⚠️ Найдено несовпадений: {len(issues)}. Начинаю автоматическое дополнение..."]
        from src.ai import UnifiedChatModel
        api_key_names = getattr(self.ai.gemini_model, 'api_key_names', []) if hasattr(self.ai, 'gemini_model') else []
        foundry_model_id = getattr(self.ai, 'foundry_model_id', '')
        use_foundry = getattr(self.ai, 'use_foundry', False)

        ai_research = UnifiedChatModel(api_key_names=api_key_names, system_instruction=SYSTEM_INSTRUCTION_RESEARCH, foundry_model_id=foundry_model_id, use_foundry=use_foundry)
        ai_chat = UnifiedChatModel(api_key_names=api_key_names, system_instruction=SYSTEM_INSTRUCTION_CHAT, foundry_model_id=foundry_model_id, use_foundry=use_foundry)
        ai_tts = UnifiedChatModel(api_key_names=api_key_names, system_instruction=SYSTEM_INSTRUCTION_TTS, foundry_model_id=foundry_model_id, use_foundry=use_foundry)

        classifier = PersistentGenreClassifier(TMDBClient(os.getenv('TMDB_API_KEY', '')), ai_research, ai_chat, ai_tts, db, "UNKNOWN")

        for iss in issues:
            try:
                lines.append(f"  🔄 Обработка: {iss.get('title', 'Unknown')}")
                if 'path' in iss:
                    await classifier._map_category(
                        iss['title'],
                        [Path(iss['path'])],
                        'series' if 'S0' in iss['title'] or iss['type'] in ['missing_season', 'episodes'] else 'movie',
                        iss['title'],
                        True
                    )
                lines.append("    ✅ Успешно дополнено.")
            except Exception as e:
                lines.append(f"    ❌ Ошибка дополнения: {e}")
                await asyncio.sleep(7)

        return "\n".join(lines)

    def _save_series_seasons_episodes(self, db: MediaDatabase, scanner: MediaScanner, classified_series: dict, disk_name: str) -> tuple[int, int]:
        """Сохраняет детализацию сезонов и эпизодов сериалов в БД."""
        saved_seasons = 0
        saved_episodes = 0
        for series_title, series_data in scanner.series.items():
            series_record = db.find_any_disk(series_title)
            if not series_record:
                continue
            series_id = series_record.get('id', 0)
            classified_item = classified_series.get(series_title, {}) or {}
            episodes_detail = classified_item.get('episodes_detail', []) or []
            seasons = series_data.get('seasons', {})

            for season_num, season_data in seasons.items():
                season_plot = ""
                season_verdict = ""
                if isinstance(episodes_detail, list):
                    for s_det in episodes_detail:
                        if s_det.get('season_number') == season_num:
                            season_plot = s_det.get('summary') or s_det.get('description') or ""
                            season_verdict = s_det.get('final_verdict') or ""
                            break

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

                for ep in season_data.get('episodes', []):
                    ep_num = ep.get('episode', 0)
                    ep_plot = ""
                    ep_verdict = ""
                    if isinstance(episodes_detail, list):
                        for s_det in episodes_detail:
                            if s_det.get('season_number') == season_num:
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

        return saved_seasons, saved_episodes

    async def _handle_scan_disk(self, disk_name: str, disk_paths_filtered: list[Path], fulldata: bool) -> str:
        """Выполняет полный цикл сканирования, классификации и сохранения диска."""
        tmdb_key = os.getenv('TMDB_API_KEY', '')
        if not tmdb_key:
            return "❌ Не найден TMDB_API_KEY в .env"

        original_instruction = self.ai.system_instruction
        self.ai.system_instruction = INSTRUCTION
        try:
            tmdb = TMDBClient(tmdb_key)
            db = MediaDatabase(MEDIA_DB)
            scanner = MediaScanner()

            print(f"\n этап 1/3: Сканирование {disk_name}...")
            scanner.scan_paths(disk_paths_filtered)
            print(f"   Найдено: фильмов — {len(scanner.movies)}, сериалов — {len(scanner.series)}")

            print("\n этап 2/4: Сохранение в БД...")
            from src.ai import UnifiedChatModel
            api_key_names = getattr(self.ai.gemini_model, 'api_key_names', []) if hasattr(self.ai, 'gemini_model') else []
            foundry_model_id = getattr(self.ai, 'foundry_model_id', '')
            use_foundry = getattr(self.ai, 'use_foundry', False)

            ai_research = UnifiedChatModel(api_key_names=api_key_names, system_instruction=SYSTEM_INSTRUCTION_RESEARCH, foundry_model_id=foundry_model_id, use_foundry=use_foundry)
            ai_chat = UnifiedChatModel(api_key_names=api_key_names, system_instruction=SYSTEM_INSTRUCTION_CHAT, foundry_model_id=foundry_model_id, use_foundry=use_foundry)
            ai_tts = UnifiedChatModel(api_key_names=api_key_names, system_instruction=SYSTEM_INSTRUCTION_TTS, foundry_model_id=foundry_model_id, use_foundry=use_foundry)

            classifier = PersistentGenreClassifier(tmdb, ai_research, ai_chat, ai_tts, db, disk_name)
            _, classified_series = await classifier.classify_media(scanner.movies, scanner.series)
            print(f"   Записей сохранено: {len(db.export_disk(disk_name))}")

            print("\n этап 3/4: Поиск дубликатов...")
            dup_count = db.update_duplicates()
            if dup_count > 0:
                print(f"   Найдено {dup_count} уникальных дубликатов между дисками")

            if fulldata:
                print("\n этап 4/4: Глубокое сканирование сериалов...")
                scanner.deep_scan_series()
                saved_s, saved_e = self._save_series_seasons_episodes(db, scanner, classified_series, disk_name)
                print(f"   Сохранено сезонов: {saved_s}, эпизодов: {saved_e}")
            else:
                print("\n Глубокое сканирование сериалов пропущено (--fulldata=n)")

            episodes_list = [r for r in db.export_disk(disk_name) if r.get('parent_id') is not None]
            return (
                f"✅ Сканирование завершено!\n"
                f"   Этап 1: Фильмов — {len(scanner.movies)}, Сериалов — {len(scanner.series)}\n"
                f"   Этап 2: Дубликатов — {dup_count}\n"
                f"   Этап 3: Эпизодов — {len(episodes_list)}\n"
            )
        finally:
            self.ai.system_instruction = original_instruction

    async def _handle(self, message: str, disk_paths: Optional[List[Path]] = None, fulldata: bool = True) -> Optional[str]:
        """Обработка сообщения пользователя (диспетчер режимов)."""
        low = message.lower()
        if not any(t in low for t in TRIGGERS):
            return None

        if any(t in low for t in ('отчет', 'report')):
            return self._handle_report(message)

        if 'rebuild_rag' in low:
            from plugins.media_organizer.core.media_rag import build_media_rag
            api_key = getattr(self.ai, 'api_key', '') or os.getenv('GEMINI_API_KEY', '')
            if not api_key:
                return '❌ GEMINI_API_KEY не найден (требуется для векторизации текста)'
            rag = build_media_rag(api_key)
            return f'✅ RAG-индекс построен: {rag.count()} документов'

        if 'rebuild_db' in low:
            return rebuild_db(MediaDatabase(MEDIA_DB))

        if any(t in low for t in ('rebuild', 'восстанов')):
            return "⚠️  Режим --rebuild удалён. Используйте полное сканирование."

        if any(t in low for t in ('ревизи', 'audit')):
            return await self._handle_audit()

        if not re.search(r'(?:диск|disk)\s*\w+', message, re.IGNORECASE):
            return await self.ai.ask_with_tools(message, [MEDIA_TOOLS], dispatch_tool_call)

        match = re.search(r'(?:диск|disk)\s*(\w+)', message, re.IGNORECASE)
        if not match:
            return "❌ Укажите имя диска (например: 'диск 4')"
        disk_name = _normalize_disk_name(match.group(0))

        paths_to_use = disk_paths if disk_paths else self.media_paths
        if not paths_to_use:
            return "⚠️ Не заданы пути для сканирования."

        disk_paths_filtered = _filter_paths_by_disk(paths_to_use, disk_name)
        if not disk_paths_filtered:
            return f"⚠️ Не найден путь для {disk_name}."

        return await self._handle_scan_disk(disk_name, disk_paths_filtered, fulldata)
