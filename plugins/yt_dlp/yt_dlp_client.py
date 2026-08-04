# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Клиент yt-dlp
# =============================================================================
# Описание:
#   Обёртка над библиотекой yt-dlp для скачивания видео/аудио и получения
#   метаданных. Поддерживает прогресс-коллбэк, форматы видео и аудио,
#   пользовательские куки, прокси и ограничение по размеру файла.
#
# File: yt_dlp_client.py
# Project: mediteka
# Package: plugins.yt_dlp
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from src.logger import logger


class YtDlpClient:
    """Клиент yt-dlp: скачивание видео/аудио и извлечение метаданных."""

    def __init__(self, cfg) -> None:
        """Инициализация клиента по конфигурации из config.json.

        Args:
            cfg: Namespace-объект, возвращаемый j_loads_ns.
        """
        self.cfg = cfg
        self.download_dir = Path(getattr(cfg, "download_dir", "downloads/yt_dlp"))
        self.download_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _base_opts(self, extra: dict | None = None) -> dict:
        """Базовые ydl_opts из конфига, объединённые с extra."""
        opts: dict[str, Any] = {
            "outtmpl": str(self.download_dir / "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        proxy = getattr(self.cfg, "proxy", None)
        if proxy:
            opts["proxy"] = proxy

        cookies_browser = getattr(self.cfg, "cookies_from_browser", None)
        if cookies_browser:
            opts["cookiesfrombrowser"] = (cookies_browser,)

        cookies_file = getattr(self.cfg, "cookies_file", None)
        if cookies_file and Path(cookies_file).exists():
            opts["cookiefile"] = cookies_file

        rate_limit = getattr(self.cfg, "rate_limit", None)
        if rate_limit:
            opts["ratelimit"] = rate_limit

        max_size = getattr(self.cfg, "max_filesize_mb", None)
        if max_size:
            opts["max_filesize"] = int(max_size) * 1024 * 1024

        if extra:
            opts.update(extra)
        return opts

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def get_info(self, url: str) -> dict | None:
        """Возвращает метаданные медиа без скачивания.

        Args:
            url: URL видео или плейлиста.

        Returns:
            Словарь с метаданными или None при ошибке.
        """
        try:
            import yt_dlp
            opts = self._base_opts({"skip_download": True, "noplaylist": True})
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as ex:
            logger.error("[yt_dlp] get_info failed", ex)
            return None

    def download_video(
        self,
        url: str,
        progress_hook: Callable[[dict], None] | None = None,
    ) -> Path | None:
        """Скачивает видео в лучшем доступном качестве.

        Args:
            url: URL видео.
            progress_hook: Коллбэк прогресса yt-dlp (опционально).

        Returns:
            Путь к скачанному файлу или None при ошибке.
        """
        try:
            import yt_dlp
            fmt = getattr(self.cfg, "format",
                          "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best")
            extra: dict[str, Any] = {
                "format": fmt,
                "merge_output_format": "mp4",
                "writethumbnail": getattr(self.cfg, "embed_thumbnail", False),
                "embedthumbnail": getattr(self.cfg, "embed_thumbnail", False),
                "addmetadata": getattr(self.cfg, "add_metadata", True),
                "restrictfilenames": getattr(self.cfg, "restrict_filenames", False),
            }
            if getattr(self.cfg, "subtitles", False):
                extra.update({
                    "writesubtitles": True,
                    "subtitleslangs": getattr(self.cfg, "subtitle_langs", ["ru", "en"]),
                    "embedsubtitles": True,
                })
            if progress_hook:
                extra["progress_hooks"] = [progress_hook]

            opts = self._base_opts(extra)
            downloaded_path: list[str] = []

            def _post_hook(d: dict):
                if d.get("status") == "finished":
                    downloaded_path.append(d.get("filename", ""))

            opts.setdefault("progress_hooks", []).append(_post_hook)

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if downloaded_path:
                return Path(downloaded_path[-1])
            # Fallback: найти последний скачанный файл в директории
            files = sorted(self.download_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            return files[0] if files else None
        except Exception as ex:
            logger.error("[yt_dlp] download_video failed", ex)
            return None

    def download_audio(
        self,
        url: str,
        progress_hook: Callable[[dict], None] | None = None,
    ) -> Path | None:
        """Скачивает только аудио и конвертирует в mp3.

        Args:
            url: URL видео/аудио.
            progress_hook: Коллбэк прогресса yt-dlp (опционально).

        Returns:
            Путь к скачанному аудиофайлу или None при ошибке.
        """
        try:
            import yt_dlp
            audio_fmt = getattr(self.cfg, "audio_format", "mp3")
            audio_q = str(getattr(self.cfg, "audio_quality", "192"))
            extra: dict[str, Any] = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_fmt,
                    "preferredquality": audio_q,
                }],
                "addmetadata": getattr(self.cfg, "add_metadata", True),
                "embedthumbnail": getattr(self.cfg, "embed_thumbnail", False),
                "restrictfilenames": getattr(self.cfg, "restrict_filenames", False),
            }
            if progress_hook:
                extra["progress_hooks"] = [progress_hook]

            downloaded_path: list[str] = []

            def _post_hook(d: dict):
                if d.get("status") == "finished":
                    downloaded_path.append(d.get("filename", ""))

            extra.setdefault("progress_hooks", []).append(_post_hook)

            opts = self._base_opts(extra)
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if downloaded_path:
                # После конвертации расширение меняется
                p = Path(downloaded_path[-1])
                converted = p.with_suffix(f".{audio_fmt}")
                return converted if converted.exists() else p
            files = sorted(
                self.download_dir.glob(f"*.{audio_fmt}"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            return files[0] if files else None
        except Exception as ex:
            logger.error("[yt_dlp] download_audio failed", ex)
            return None

    def get_formats(self, url: str) -> list[dict]:
        """Возвращает список доступных форматов для видео.

        Args:
            url: URL видео.

        Returns:
            Список словарей с описанием форматов.
        """
        info = self.get_info(url)
        if not info:
            return []
        return info.get("formats", [])

    def search_youtube(self, query: str, max_results: int = 5) -> list[dict]:
        """Поиск видео на YouTube через ytsearch.

        Args:
            query: Поисковый запрос.
            max_results: Максимальное количество результатов.

        Returns:
            Список словарей с метаданными найденных видео.
        """
        try:
            import yt_dlp
            search_url = f"ytsearch{max_results}:{query}"
            opts = self._base_opts({
                "skip_download": True,
                "extract_flat": "in_playlist",
                "noplaylist": False,
            })
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_url, download=False)
                entries = info.get("entries", []) if info else []
                return [e for e in entries if e]
        except Exception as ex:
            logger.error("[yt_dlp] search_youtube failed", ex)
            return []

    @staticmethod
    def format_filesize(size_bytes: int | None) -> str:
        """Форматирует размер файла в читаемый вид."""
        if not size_bytes:
            return "неизвестно"
        for unit in ("Б", "КБ", "МБ", "ГБ"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} ТБ"

    @staticmethod
    def format_duration(seconds: int | None) -> str:
        """Форматирует длительность из секунд в MM:SS или HH:MM:SS."""
        if not seconds:
            return "—"
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    @staticmethod
    def is_url(text: str) -> bool:
        """Проверяет, является ли строка URL."""
        return bool(re.match(r"https?://\S+", text.strip()))
