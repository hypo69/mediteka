# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Watcher для qBittorrent и автосинхронизации БД/RAG
# =============================================================================
# Описание:
#   Фоновый процесс отслеживания завершенных торрентов, автоклассификации
#   и периодической очистки заблокированных файлов.
#
# File: qbittorrent_watcher.py
# Project: gemini-simplechat
# =============================================================================

import os
import sys
import time
import json
import sqlite3
import subprocess
import re
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

import header
from src.logger import logger
from plugins.qbittorrent.qbittorrent import QBittorrentClient, _load_cfg
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_scanner import TMDBClient
from plugins.media_organizer.core.genre_classifier import PersistentGenreClassifier
from plugins.media_organizer.core.media_rag_functions import rebuild_rag_index
from src.secrets.api_key_state import load_api_keys
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core import MEDIA_DB, SYSTEM_INSTRUCTION

load_dotenv()

class QBittorrentWatcher:
    def __init__(self, db_path: Path = MEDIA_DB) -> None:
        self.db_path = db_path
        self.db = MediaDatabase(db_path)
        
        # Загрузка конфигурации qBittorrent
        cfg = _load_cfg()
        self.qbt = QBittorrentClient(
            host=cfg.host,
            port=int(cfg.port),
            username=cfg.username,
            password=cfg.password,
        )
        
        # Инициализация Gemini AI
        _, key_names, _ = load_api_keys()
        if not key_names:
            raise ValueError("Нет доступных Gemini API ключей.")
        self.ai = GoogleGenerativeAI(api_key_names=key_names, system_instruction=SYSTEM_INSTRUCTION)
        
        # Инициализация TMDB
        tmdb_key = os.getenv('TMDB_API_KEY', '')
        if not tmdb_key:
            raise ValueError("Не найден TMDB_API_KEY в .env")
        self.tmdb = TMDBClient(tmdb_key)

    def get_qbittorrent_executable_path(self) -> str:
        """Определяет путь к qbittorrent.exe, если он запущен."""
        try:
            # Используем PowerShell для получения пути исполняемого файла
            cmd = "powershell -Command \"(Get-Process qbittorrent -ErrorAction SilentlyContinue).Path\""
            res = subprocess.check_output(cmd, shell=True, text=True).strip()
            if res:
                return res
        except Exception as e:
            logger.warning(f"Не удалось получить путь к qBittorrent: {e}")
        return ""

    def process_new_files(self) -> None:
        """Синхронизация новых завершенных файлов из qBittorrent."""
        logger.info("Проверка новых завершенных торрентов в qBittorrent...")
        try:
            torrents = self.qbt.torrents()
        except Exception as e:
            logger.error(f"Не удалось подключиться к qBittorrent: {e}")
            return

        db_updated = False
        
        # Получаем информацию обо всех источниках
        torrents_sources = {}
        for t in torrents:
            h = t.get("hash", "")
            if h:
                src = t.get("comment", "")
                if not src:
                    src = t.get("tracker", "")
                torrents_sources[h] = src

        for t in torrents:
            # Обрабатываем только полностью скачанные
            if t.get("progress", 0.0) < 1.0:
                continue

            torrent_hash = t.get("hash", "")
            torrent_name = t.get("name", "")
            save_path = t.get("save_path", "")
            
            if not torrent_hash or not save_path:
                continue

            # Получаем список файлов этого торрента
            try:
                t_files = self.qbt.files(torrent_hash)
            except Exception as e:
                logger.warning(f"Не удалось получить список файлов для торрента {torrent_name}: {e}")
                continue

            for f in t_files:
                file_name = f.get("name", "")
                file_size = f.get("size", 0)
                if not file_name:
                    continue

                full_path = Path(save_path) / file_name
                # Проверяем, есть ли уже этот файл в БД
                record = self.db.get_media_by_path(str(full_path))
                if record:
                    # Если запись есть, но нет torrent_id, обновим его
                    if not record.get("torrent_id"):
                        src = torrents_sources.get(torrent_hash, "")
                        # TODO: Populate download_url properly if possible
                        self.db.update_torrent_id(str(full_path), torrent_hash, src, "")
                        db_updated = True
                    continue

                # Если файла нет в БД, значит это новый файл. Добавим его.
                logger.info(f"Обнаружен новый файл: {full_path}. Начинаем классификацию...")
                
                # Определяем тип: сериал или фильм
                is_series = False
                pattern = re.compile(r'(?i)[Ss]\d{2}|[Ee]\d{2,3}|season|серия')
                if pattern.search(file_name) or pattern.search(torrent_name):
                    is_series = True

                media_type = "series" if is_series else "movie"
                
                # Извлекаем красивое название для поиска
                clean_title = Path(file_name).stem
                # Убираем технические теги
                clean_title = re.sub(r'(?i)\b(1080p|720p|bluray|web-dl|h264|x264|dts|dd5\.1|lostfilm|alexfilm|repack)\b', '', clean_title)
                clean_title = re.sub(r'[\._-]', ' ', clean_title).strip()

                try:
                    # Инициализируем классификатор для конкретной директории
                    disk_name = "QBITTORRENT"
                    classifier = PersistentGenreClassifier(self.tmdb, self.ai, self.db, disk_name)
                    
                    info = classifier._map_category(
                        clean_title,
                        [full_path],
                        media_type,
                        clean_title,
                        is_series
                    )
                    
                    # Добавляем торрент информацию
                    info["torrent_id"] = torrent_hash
                    info["torrent_source"] = torrents_sources.get(torrent_hash, "")
                    info["media_size"] = file_size
                    info["path"] = str(full_path)
                    
                    # Сохраняем в БД
                    self.db.save_media(disk_name, media_type, info)
                    db_updated = True
                    logger.info(f"Файл {file_name} успешно добавлен в базу.")
                except Exception as ex:
                    logger.error(f"Не удалось классифицировать файл {file_name}: {ex}")

        if db_updated:
            logger.info("База данных обновлена. Перестраиваем RAG-индекс...")
            try:
                res = rebuild_rag_index(fresh=False)
                logger.info(f"RAG перестроен: {res}")
            except Exception as e:
                logger.error(f"Не удалось перестроить RAG-индекс: {e}")

    def check_deleted_torrents(self) -> None:
        """Помечает записи как 'deleted', если торрент был удален из qBittorrent."""
        try:
            current_torrents = {t.get("hash", "") for t in self.qbt.torrents() if t.get("hash")}
        except Exception as e:
            logger.error(f"Не удалось подключиться к qBittorrent: {e}")
            return

        # Извлекаем из БД все записи, привязанные к торрентам, которые еще не помечены как удаленные
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT path, torrent_id FROM media WHERE torrent_id IS NOT NULL AND status != 'deleted'"
            ).fetchall()

        for row in rows:
            path_str = row["path"]
            t_id = row["torrent_id"]
            if t_id not in current_torrents:
                logger.info(f"Торрент {t_id} больше не найден в qBittorrent. Помечаем {path_str} как deleted.")
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE media SET status = 'deleted' WHERE path = ?",
                        (path_str,)
                    )

    def run_cleanup_process(self) -> None:
        """Очистка заблокированных файлов с временной остановкой qBittorrent."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            candidates = conn.execute(
                "SELECT id, path FROM media WHERE status = 'delete_candidate'"
            ).fetchall()

        if not candidates:
            return

        logger.info(f"Обнаружено {len(candidates)} кандидатов на физическое удаление. Начинаем очистку...")
        
        # Определяем путь к qBittorrent.exe перед его закрытием
        qbt_path = self.get_qbittorrent_executable_path()
        if not qbt_path:
            # Запасной вариант - попробуем найти стандартный путь
            std_paths = [
                r"C:\Program Files\qBittorrent\qbittorrent.exe",
                r"C:\Program Files (x86)\qBittorrent\qbittorrent.exe",
            ]
            for p in std_paths:
                if Path(p).exists():
                    qbt_path = p
                    break

        # 1. Останавливаем qBittorrent
        logger.info("Остановка процесса qBittorrent...")
        try:
            subprocess.run("taskkill /F /IM qbittorrent.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3) # Даем процессу время полностью закрыться
        except Exception as e:
            logger.error(f"Не удалось остановить qBittorrent: {e}")

        # 2. Удаляем файлы физически
        deleted_ids = []
        for cand in candidates:
            p = Path(cand["path"])
            try:
                if p.exists():
                    if p.is_dir():
                        import shutil
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                    logger.info(f"Физически удален файл/папка: {p}")
                else:
                    logger.info(f"Файл/папка уже отсутствует: {p}")
                deleted_ids.append(cand["id"])
            except Exception as e:
                logger.error(f"Не удалось удалить {p}: {e}")

        # 3. Запускаем qBittorrent обратно
        if qbt_path:
            logger.info(f"Запуск qBittorrent обратно: {qbt_path}")
            try:
                subprocess.Popen([qbt_path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            except Exception as e:
                logger.error(f"Не удалось запустить qBittorrent: {e}")
        else:
            logger.warning("Путь к qBittorrent не определен, автоматический запуск невозможен.")

        # 4. Обновляем статус в БД
        if deleted_ids:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    f"UPDATE media SET status = 'deleted' WHERE id IN ({','.join(map(str, deleted_ids))})"
                )
            logger.info(f"Статус обновлен на 'deleted' для {len(deleted_ids)} записей.")

    def start_loop(self, interval_seconds: int = 300) -> None:
        """Запускает watcher в бесконечном цикле."""
        logger.info(f"Watcher запущен. Интервал проверки: {interval_seconds} секунд.")
        while True:
            try:
                self.process_new_files()
                self.check_deleted_torrents()
                self.run_cleanup_process()
            except Exception as e:
                logger.error(f"Ошибка в цикле watcher-а: {e}")
            time.sleep(interval_seconds)

if __name__ == '__main__':
    watcher = QBittorrentWatcher()
    # Однократный запуск для теста, если запущен напрямую
    watcher.process_new_files()
    watcher.check_deleted_torrents()
    watcher.run_cleanup_process()
